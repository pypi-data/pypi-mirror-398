from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from sqlglot import exp, select

from ....util.structures import OrderedSet
from ...metamodel.metamodel import Aggregate, Logical, Lookup, Model, Node, Relation, Task, Update, Var, Value
from ...metamodel.pprint import pprint as mmpp
from ...metamodel.rewriter import Rewriter, Walker
from ...metamodel.metamodel_analyzer import Analyzer as MMAnalyzer

from rich import print as rp

#------------------------------------------------------
# Simple flatten
#------------------------------------------------------

class SimpleFlattener(Walker):
    def flatten(self, node: Node) -> list[Task]:
        self.rules: list[Task] = []
        self.stack: list[Task] = []
        self(node)
        return self.rules

    def enter_logical(self, logical: Logical):
        self.stack.append(logical)

    def logical(self, logical: Logical):
        self.stack.pop()

    def update(self, update: Update):
        # build a rule for just this update
        body = OrderedSet()
        for frame in self.stack:
            if isinstance(frame, Logical):
                for task in frame.body:
                    if not isinstance(task, (Logical, Update)):
                        body.add(task)
        body.add(update)
        self.rules.append(Logical(body=tuple(body)))

#------------------------------------------------------
# SourceWalker
#------------------------------------------------------

class SourceWalker(Walker):
    def capture_sources(self, node: Task, analysis:SQLAnalysis):
        self.stack = [OrderedSet()]
        self.root = node
        self.analysis = analysis
        self(node)

    def enter_logical(self, logical: Logical):
        self.stack.append(OrderedSet())

    def logical(self, logical: Logical):
        self.stack.pop()

    def lookup(self, lookup: Lookup):
        self.analysis.get(lookup.relation)
        self.stack[-1].add(lookup.relation)

    def update(self, update: Update):
        info = self.analysis.get(update.relation)
        info.sources.add(self.root)
        for frame in self.stack:
            for dep in frame:
                info.edges.add(dep)
                self.analysis.get(dep)

#------------------------------------------------------
# RecursionWalker
#------------------------------------------------------

class RecursionWalker(Walker):
    def is_simple(self, node: Task, analysis: SQLAnalysis) -> bool:
        self._recursive_count = 0
        self._has_agg = False
        self.analysis = analysis
        self(node)
        if not self._has_agg and self._recursive_count <= 1:
            return True
        return False

    def aggregate(self, aggregate: Aggregate):
        self._has_agg = True

    def lookup(self, lookup: Lookup):
        if self.analysis.get(lookup.relation).recursive:
            self._recursive_count += 1

#------------------------------------------------------
# VarMapper
#------------------------------------------------------

class VarMapper(Rewriter):
    def map_vars(self, mapping: dict[Var, Value], node: Node):
        self.mapping = mapping
        return self(node)

    def var(self, var: Var):
        if var in self.mapping:
            return self.mapping[var]
        return var

#------------------------------------------------------
# Analysis
#------------------------------------------------------

mapper = VarMapper()

@dataclass
class RelationInfo:
    relation: Relation
    sources: OrderedSet[Task] = field(default_factory=OrderedSet[Task])
    edges: OrderedSet[Relation] = field(default_factory=OrderedSet[Relation])

    head_vars: list[Var] = field(default_factory=list)
    body: OrderedSet[Task] = field(default_factory=OrderedSet[Task])

    recursive: bool = field(default=False)

    def map_lookup(self, lookup: Lookup):
        mapping = {self.head_vars[i]: lookup.args[i] for i in range(len(self.head_vars))}
        mapped = []
        for task in self.body:
            mapped.append(mapper.map_vars(mapping, task))
        return mapped

@dataclass
class SQLAnalysis:
    relations: dict[Relation, RelationInfo] = field(default_factory=dict)
    source_walker = SourceWalker()

    def get(self, relation: Relation) -> RelationInfo:
        if relation not in self.relations:
            self.relations[relation] = RelationInfo(relation=relation)
        return self.relations[relation]

    def analyze(self, task:Task):
        self.source_walker.capture_sources(task, self)

    def construct_sccs(self):
        sccs = find_sccs(self.relations)
        self.sccs = sccs
        for info in self.relations.values():
            info.recursive = False
        for scc in sccs:
            for relation in scc.relations:
                self.get(relation).recursive = scc.recursive

        scc_order = scc_toposort(sccs, self.relations)
        self.scc_order = scc_order

#------------------------------------------------------
# SCCs
#------------------------------------------------------

@dataclass
class SCC:
    relations: list[Relation]
    recursive: bool

    def strategy(self, analysis:SQLAnalysis) -> str:
        if not self.recursive:
            return "NORMAL"
        relations = self.relations
        if len(relations) == 1:
            rel = relations[0]
            sources = analysis.get(rel).sources
            if all(RecursionWalker().is_simple(source, analysis) for source in sources):
                return "CTE"
        return "SEMI_NAIVE"

def find_sccs(relations: dict[Relation, RelationInfo]) -> list[SCC]:
    # find sccs using Tarjan's algorithm
    index = 0
    stack: list[Relation] = []
    onstack: set[Relation] = set()
    ix: dict[Relation, int] = {}
    low: dict[Relation, int] = {}
    results: list[SCC] = []

    def strongconnect(v: Relation):
        nonlocal index
        ix[v] = low[v] = index
        index += 1
        stack.append(v)
        onstack.add(v)

        info = relations.get(v)
        edges = info.edges if info else ()
        for w in edges:
            if w not in ix:
                strongconnect(w)
                low[v] = low[v] if low[v] < low[w] else low[w]
            elif w in onstack:
                low[v] = low[v] if low[v] < ix[w] else ix[w]

        if low[v] == ix[v]:
            comp: list[Relation] = []
            while True:
                w = stack.pop()
                onstack.discard(w)
                comp.append(w)
                if w == v:
                    break
            # size > 1 or a singleton with self-loop
            comp_info = relations.get(comp[0])
            comp_edges = comp_info.edges if comp_info else ()
            recursive = (len(comp) > 1) or (comp[0] in comp_edges)
            results.append(SCC(comp, recursive))

    # visit all vertices, including isolated
    nodes = set(relations.keys()) | {w for info in relations.values() for w in info.edges}
    for v in nodes:
        if v not in ix:
            strongconnect(v)

    return results

def scc_toposort(components: list[SCC], relations: dict[Relation, RelationInfo]) -> list[SCC]:
    comp_id = {v: i for i, comp in enumerate(components) for v in comp.relations}
    n = len(components)

    # Build reversed condensed DAG: dep_comp -> rel_comp
    adj: list[set[int]] = [set() for _ in range(n)]
    indeg: list[int] = [0] * n

    for rel, info in relations.items():
        cr = comp_id[rel]
        for dep in info.edges:
            cd = comp_id.get(dep)
            if cd is None:
                continue
            if cr == cd:
                continue
            # edge: dependency SCC -> relation SCC
            if cr not in adj[cd]:
                adj[cd].add(cr)
                indeg[cr] += 1

    # Kahn’s algorithm
    q: deque[int] = deque(i for i, d in enumerate(indeg) if d == 0)
    order: list[SCC] = []
    while q:
        i = q.popleft()
        order.append(components[i])
        for j in adj[i]:
            indeg[j] -= 1
            if indeg[j] == 0:
                q.append(j)

    assert len(order) == n, "SCC DAG unexpectedly cyclic"
    return order

#------------------------------------------------------
# Context
#------------------------------------------------------

class Frame:
    pass

class Context:
    pass

#------------------------------------------------------
# Compiler
#------------------------------------------------------

class SQLCompiler:

    def compile(self, model:Model):
        MMAnalyzer().analyze(model)
        analysis = SQLAnalysis()

        rules = []
        flattener = SimpleFlattener()
        # mmpp(model)

        assert isinstance(model.root, Logical)
        for sub_task in model.root.body:
            flat_rules = flattener.flatten(sub_task)
            rules.extend(flat_rules)
            for rule in flat_rules:
                analysis.analyze(rule)

        analysis.construct_sccs()
        sccs = analysis.sccs

        # print("\nStrongly Connected Components:")
        # for i, scc in enumerate(sccs, start=1):
        #     tag = f" (recursive {scc.strategy(analysis)})" if scc.recursive else ""
        #     print(f"  SCC {i}:{tag}")
        #     for r in scc.relations:
        #         print(f"    - {r}")

        # # ---- Topological order of SCCs (evaluation phases) ----
        # ordered_sccs = analysis.scc_order

        # # TODO: handle relations that didn't end up in any SCC?

        # # walk the ordered components forward collapsing as we go
        # print("\nSCC evaluation order (topologically sorted):")
        # for phase_idx, scc in enumerate(ordered_sccs, start=1):
        #     tag = f" (recursive {scc.strategy(analysis)})" if scc.recursive else ""
        #     rp(f"[yellow bold]  Phase {phase_idx}:{tag}")
        #     rp("[yellow bold]------------------------------------------------------------")
        #     for relation in scc.relations:
        #         info = analysis.get(relation)
        #         rp(f"[cyan bold]  {relation}")
        #         # print("  Head Vars:")
        #         # for hv in info.head_vars:
        #         #     print(f"    - {hv}")
        #         # print("  Body:")
        #         # for task in info.body:
        #         #     print(f"    - {task}")
        #         print("    Sources:")
        #         for source in info.sources:
        #             # print(f"        - {source}")
        #             mmpp(source, indent=2)
        #         print("    Edges:")
        #         for edge in info.edges:
        #             print(f"        - {edge}")
        #     print("\n")


