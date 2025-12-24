from __future__ import annotations
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Sequence, cast

from ...util.structures import OrderedSet

from .metamodel import Aggregate, Construct, Field, Logical, Lookup, Model, Node, Relation, Require, ScalarType, Task, TypeNode, Update, Var, Not, Match, Union
from .rewriter import NO_WALK, Walker
from .builtins import builtins as b
from .pprint import pprint as mmpp

#------------------------------------------------------
# Constants
#------------------------------------------------------

NORMAL_ORDER = {
    Lookup: 0,
    Aggregate: 0,
    Union: 0,
    Match: 0,
    Logical: 0,
    Require: 0,
    Not: 1,
    Construct: 2,
    Update: 2,
}

#------------------------------------------------------
# Analysis
#------------------------------------------------------

@dataclass
class Analysis:
    fds: dict[Field, tuple[Field, ...]] = field(default_factory=dict)
    mandatory: set[Relation] = field(default_factory=set)

    def is_property(self, relation: Relation) -> bool:
        return len(self.fds[relation.fields[-1]]) == len(relation.fields) - 1

#------------------------------------------------------
# Analyzer
#------------------------------------------------------

class Analyzer(Walker):

    def analyze(self, model:Model) -> Analysis:
        self.analysis = Analysis()
        self(model.root)
        object.__setattr__(model, "_analysis", self.analysis)
        return self.analysis

    def require(self, node:Require):
        if not isinstance(node.check, Logical):
            return

        for item in node.check.body:
            if not isinstance(item, Lookup):
                continue
            if item.relation is b.constraints.unique_fields:
                self.track_unique(item)
            # elif item.relation == b.core["mandatory"]:
            #     self.track_mandatory(item)

    def track_unique(self, lookup: Lookup):
        args = cast(list[Field], lookup.args[0])
        if not isinstance(args, (list, tuple)) or any(not isinstance(arg, Field) for arg in args):
            return

        rel = args[0]._relation
        determined = [field for field in rel.fields if field not in args]
        if len(determined) == 1:
            self.analysis.fds[determined[0]] = tuple(args)

    def track_mandatory(self, lookup: Lookup):
        pass

#------------------------------------------------------
# Var finder
#------------------------------------------------------

class VarFinder(Walker):
    def find_vars(self, node:Node|Iterable[Node], positive_only=False) -> OrderedSet[Var]:
        self.vars:OrderedSet[Var] = OrderedSet()
        self.positive_only = positive_only
        self(node)
        return self.vars

    def enter_not(self, node:Node):
        if self.positive_only:
            return NO_WALK

    def var(self, node:Var):
        self.vars.add(node)

    def lookup(self, node:Lookup):

        pass

#------------------------------------------------------
# Context
#------------------------------------------------------

class Frame:
    def __init__(self):
        self.nodes:OrderedSet[Task] = OrderedSet()
        self.post_nodes:OrderedSet[Task] = OrderedSet()
        self.indirect_filters:dict[Var, OrderedSet[Task]] = defaultdict(OrderedSet[Task])

class Context:
    def __init__(self):
        self.stack:list[Frame] = [Frame()]

    #------------------------------------------------------
    # subcontext
    #------------------------------------------------------

    def push(self):
        f = Frame()
        self.stack.append(f)
        return f

    def pop(self) -> Frame:
        prev = self.stack.pop()
        return prev

    #------------------------------------------------------
    # Task capture
    #------------------------------------------------------

    def _check_frames(self, node:Task):
        for frame in reversed(self.stack[:-1]):
            if node in frame.nodes:
                return True
        return False

    def add(self, node:Task):
        if self._check_frames(node):
            return
        self.stack[-1].nodes.add(node)

    def extend(self, nodes:Sequence[Task]):
        for node in nodes:
            self.add(node)

    def add_post(self, node:Task):
        if self._check_frames(node):
            return
        self.stack[-1].post_nodes.add(node)

    @property
    def nodes(self):
        return self.stack[-1].nodes

    @property
    def stack_nodes(self) -> Iterator[Task]:
        for frame in self.stack:
            yield from frame.nodes

    @property
    def frame(self) -> Frame:
        return self.stack[-1]

#------------------------------------------------------
# RuleBuilder
#------------------------------------------------------

class RuleBuilder(Walker):
    var_finder = VarFinder()

    def __init__(self, unnest: bool = True):
        super().__init__()
        self.unnest = unnest

    def build(self, ctx: Context, node:Node|Iterable[Node], root_frame:Frame) -> list[Task]:
        self.ctx = ctx
        self.node_stack = []
        self.root_frame = root_frame
        self.ctx.push()
        self.rules = []
        self(node)
        final = self.ctx.pop()
        if not self.unnest:
            self.rules.extend(final.nodes)
        return self.rules

    #------------------------------------------------------
    # Context handling
    #------------------------------------------------------

    def push(self, node:Node):
        self.node_stack.append(node)
        return self.ctx.push()

    def pop(self):
        self.node_stack.pop()
        return self.ctx.pop()

    def cur_node(self) -> Node|None:
        if len(self.node_stack) < 1:
            return None
        return self.node_stack[-1]

    def satisfy_indirects(self):
        for node in reversed(self.node_stack):
            # We should never push indirect filters into Nots as it
            # changes the actual logic of the query
            if isinstance(node, (Not)):
                return
        f = self.ctx.frame
        handled = set()
        if f.indirect_filters:
            for var in self.var_finder.find_vars(f.nodes):
                tasks = f.indirect_filters.get(var, ())
                for task in tasks:
                    if task not in handled and task not in self.node_stack:
                        handled.add(task)
                        self(task)

    #------------------------------------------------------
    # Relation ops
    #------------------------------------------------------

    def lookup(self, node:Lookup):
        self.ctx.add(node)

    def construct(self, node:Construct):
        self.ctx.add(node)

    def enter_aggregate(self, node:Aggregate):
        self.push(node)

    def aggregate(self, node:Aggregate):
        collected = self.pop()
        self.ctx.add(node.mut(body=collected.nodes[0]))

    def update(self, update: Update):
        if self.unnest:
            # build a rule for just this update
            body = (*self.ctx.stack_nodes, update)
            self.rules.append(Logical(body=body, scope=True, source=update.source))
        else:
            self.ctx.add(update)

    #------------------------------------------------------
    # Logical
    #------------------------------------------------------

    def enter_logical(self, logical:Logical):
        # Nested logicals that aren't optional and aren't a scope should just be inlined
        if not logical.optional and not logical.scope and isinstance(self.cur_node(), Logical):
            return

        f = self.push(logical)
        f.indirect_filters = self.root_frame.indirect_filters

        # TODO: we should actually toposort this based on var dependencies
        # normalize the body order so that nots come after most ops, followed by constructs
        # and updates
        def sort_key(x):
            order = NORMAL_ORDER.get(type(x), len(NORMAL_ORDER))
            if isinstance(x, Lookup) and isinstance(x.relation, ScalarType):
                order = -1
            if isinstance(x, Logical) and x.optional:
                order = len(NORMAL_ORDER) + 1
            return (order, x.id)
        ordered_body = sorted(logical.body, key=sort_key)
        updates = []
        for item in ordered_body:
            if not isinstance(item, Update):
                self(item)
            else:
                updates.append(item)
        self.satisfy_indirects()
        for u in updates:
            self(u)
        f = self.pop()
        optional = False
        if not self.unnest:
            optional = logical.optional
        self.ctx.add(Logical(tuple(f.nodes), scope=logical.scope, source=logical.source, optional=optional))
        return NO_WALK

    #------------------------------------------------------
    # Passthrough Containers
    #------------------------------------------------------

    def enter_not(self, node:Not):
        self.push(node)

    def not_(self, node:Not):
        cur = self.pop()
        self.ctx.add(node.mut(task=cur.nodes[0], source=node.source))

    def enter_match(self, match:Match):
        self.push(match)

    def match(self, match:Match):
        cur = self.pop()
        self.ctx.add(match.mut(tasks=tuple(cur.nodes), source=match.source))

    def enter_union(self, union:Union):
        self.push(union)

    def union(self, union:Union):
        cur = self.pop()
        self.ctx.add(union.mut(tasks=tuple(cur.nodes), source=union.source))

    def enter_require(self, require:Require):
        self.push(require)

        self.ctx.push()
        self(require.domain)
        domain = self.ctx.pop().nodes[0]

        self.ctx.push()
        self(require.check)
        check = self.ctx.pop().nodes[0]

        self.pop()
        self.ctx.add(require.mut(domain=domain, check=check, source=require.source))
        return NO_WALK


#------------------------------------------------------
# Normalize
#------------------------------------------------------

class Normalize(Walker):
    var_finder = VarFinder()
    rule_builder = RuleBuilder(unnest=False)

    def normalize(self, node: Task) -> Task:
        self.ctx = Context()
        self(node)
        return self.ctx.nodes[0]

    #------------------------------------------------------
    # Logical
    #------------------------------------------------------

    def enter_logical(self, logical: Logical):
        if logical.optional:
            self.ctx.add_post(logical)
            return NO_WALK
        self.ctx.push()

    def logical(self, logical: Logical):
        cur = self.ctx.pop()
        parent = self.ctx.frame

        # We need to build our nodes only in the context of our parent frame
        cleaned = self.rule_builder.build(self.ctx, Logical(tuple(cur.nodes)), parent)
        cleaned_nodes = []
        if cleaned:
            assert isinstance(cleaned[0], Logical)
            cleaned_nodes.extend(cleaned[0].body)


        # we want to build the post nodes in the context of the current frame, so
        # we temporarily push it back on the stack
        self.ctx.push()
        for cleaned_node in cleaned_nodes:
            self.ctx.add(cleaned_node)
        if logical.scope:
            for node in cur.post_nodes:
                cleaned_nodes.extend(self.rule_builder.build(self.ctx, node, cur))

        # make sure the frame is gone
        self.ctx.pop()
        self.ctx.add(Logical(tuple(cleaned_nodes), scope=logical.scope, annotations=logical.annotations, source=logical.source))

    #------------------------------------------------------
    # Require
    #------------------------------------------------------

    def enter_require(self, node: Require):
        self.ctx.push()

    def require(self, node: Require):
        cur = self.ctx.pop()
        self.ctx.extend(self.rule_builder.build(self.ctx, node, cur))

    #------------------------------------------------------
    # Relation ops
    #------------------------------------------------------

    def lookup(self, node:Lookup):
        self.ctx.add(node)

    def construct(self, node:Construct):
        self.ctx.add(node)

    def enter_aggregate(self, node:Aggregate):
        self.ctx.add(node)
        return NO_WALK

    def update(self, update: Update):
        self.ctx.add_post(update)

    #------------------------------------------------------
    # Indirect filters
    #------------------------------------------------------

    def enter_not(self, node:Not):
        self.ctx.add(node)
        vs = self.var_finder.find_vars(node.task)
        for v in vs:
            self.ctx.frame.indirect_filters[v].add(node)
        return NO_WALK

    def enter_match(self, match:Match):
        self.ctx.add(match)
        return NO_WALK

    def enter_union(self, union:Union):
        self.ctx.add(union)
        return NO_WALK

#------------------------------------------------------
# SplittingNormalize
#------------------------------------------------------

class SplittingNormalize(Walker):
    var_finder = VarFinder()
    rule_builder = RuleBuilder()

    def flatten(self, node: Node) -> list[Task]:
        self.ctx = Context()
        self.rules: list[Task] = []
        self(node)
        return self.rules

    def enter_logical(self, logical: Logical):
        if logical.optional:
            self.ctx.add_post(logical)
            return NO_WALK
        self.ctx.push()

    def logical(self, logical: Logical):
        if logical.scope:
            cur = self.ctx.pop()
            if len(cur.post_nodes) > 1:
                self._split_rules(cur, logical)
            else:
                post = cur.post_nodes
                first = next(iter(post), None)
                if isinstance(first, Logical):
                    post = first.body
                cur_nodes = (*cur.nodes, *post)
                self.rules.extend(self.rule_builder.build(self.ctx, Logical(cur_nodes), cur))

    def _split_rules(self, cur:Frame, logical:Logical):
        # determine vars that cross the shared root boundary
        vs = self.var_finder.find_vars(list(cur.nodes), positive_only=True)
        needed = OrderedSet[Var]()
        for item in cur.post_nodes:
            item_vars = self.var_finder.find_vars(item)
            for v in item_vars:
                if v in vs:
                    needed.add(v)

        # generate an intermediate to carry the needed vars
        intermediate = Relation("temp", tuple(Field(f.name, f.type) for f in needed), source=logical.source)

        # add the trunk rule
        cur_nodes = (*cur.nodes, Update(intermediate, tuple(needed)))
        base = self.rule_builder.build(self.ctx, Logical(cur_nodes, source=logical.source), cur)
        self.rules.extend(base)
        print("-------------------------------------------------")

        # add the child rules
        self.ctx.push()
        self.ctx.add(Lookup(intermediate, tuple(needed)))

        for node in cur.post_nodes:
            self.rules.extend(self.rule_builder.build(self.ctx, node, cur))

        self.ctx.pop()


    #------------------------------------------------------
    # Relation ops
    #------------------------------------------------------

    def lookup(self, node:Lookup):
        self.ctx.add(node)

    def construct(self, node:Construct):
        self.ctx.add(node)

    def enter_aggregate(self, node:Aggregate):
        self.ctx.add(node)
        return NO_WALK

    def update(self, update: Update):
        self.ctx.add_post(update)

    #------------------------------------------------------
    # Indirect filters
    #------------------------------------------------------

    def enter_not(self, node:Not):
        self.ctx.add(node)
        vs = self.var_finder.find_vars(node.task)
        for v in vs:
            self.ctx.frame.indirect_filters[v].add(node)
        return NO_WALK

    def enter_match(self, match:Match):
        self.ctx.add(match)
        vs = self.var_finder.find_vars(match.tasks)
        for v in vs:
            self.ctx.frame.indirect_filters[v].add(match)
        return NO_WALK

    def exists(self, node):
        print("EXISTS")
