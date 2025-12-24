
from abc import ABC
from typing import Dict, List, Iterable

from v0.relationalai.debugging import logger
from v0.relationalai.dsl import next_id

from v0.relationalai.experimental.pathfinder.options import DEFAULT_OPTIONS
from v0.relationalai.experimental.pathfinder.rpq import RPQ
from v0.relationalai.experimental.pathfinder.filter import (
    NodeFilter, NodeLabel, EdgeLabel, AnonymousNodeFilter
)
from v0.relationalai.experimental.pathfinder.automaton import prepare_automaton
from v0.relationalai.experimental.pathfinder.transition import EdgeTransition, NodeTransition

from v0.relationalai.experimental.pathfinder.datalog import (
    ConstantEqualityAtom, Rule, RelAtom, AnonymousFilterAtom,
    VariableEqualityAtom, Atom, DatalogProgram
)

# =========================================================================================
# Compiling a pattern into Rel programs
# =========================================================================================
#
# We compile a RPQ pattern into two kinds of programs:
# 1. A program that computes the connectivity relation of the input automaton.
# 2. A program that computes the product graph of the input automaton and a knowledge graph.
#
# We illustrate the compilation process on the following example pattern:
# -----------------------------------------------------------------------------------------
# Running example
# -----------------------------------------------------------------------------------------
# An example of the program generation is presented on the pattern below.
#
# path(Odd, star('-[A]->', Even)) | path('<-[B]-', N)
#
# which is parsed into the following RPQ
#
# ╷ Union
# ├──┐ Concat
# │  ├──╴ Node(Odd)
# │  └──┐ Star
# │     └──┐ Concat
# │        ├──╴ Edge(-[A]→) [pos=1]
# │        └──╴ Node(Even)
# └──┐ Concat
#    ├──╴ Edge(←[B]-) [pos=2]
#    └──╴ Node(N)
#
# The RPQ is compiled into the following automaton (with transitions explicitly labeled):
# * states: 0 1 2
# * init: 0
# * delta:
#    - 0
#       → 1
#         ⊨(Odd)=[-[A]→]=()⇒    (t1)
#       → 2
#         ⊨()=[←[B]-]=()⇒       (t2)
#    - 1
#       → 1
#         ⊨(Even)=[-[A]→]=()⇒   (t3)
# * final:
#    - 0
#       ⊨(Odd)⇒                 (f1)
#    - 1
#       ⊨(Even)⇒                (f2)
#    - 2
#       ⊨(N)⇒                   (f3)
#
# =========================================================================================
# 1. Connectivity Program
# =========================================================================================
# The Rel connectivity program defines a binary relation `pq_conn(x, y)` that selects the
# nodes `y` reachable from `x` with the automaton having an accepting run. The program has
# two independent uses:
# 1. When the RPQ is meant to be evaluated as a connectivity query, the program is used to
#    evaluate the query.
# 2. When the RPQ is meant to produce paths but the user does not specify the source or
#    target nodes to be used during evaluation.
#
# The program consists of binary predicates `pq_conn_from_q(x, y)` that selects the nodes
# `y` reachable from `x` with the automaton having a run from state `q` to an accepting
# state. Note that when the automaton has cycles, the program may be recursive. To make sure
# that each introduced predicate is grounded we may "contract" the final node transitions of
# an accepting state `q` with every incoming transition of `q` (note that the final node
# transitions may be ungrounded). As a consequence, an accepting state `q` that does not
# have any outgoing transitions, called an _exit state_, does not need its own dedicated
# `pq_conn_fom_q` predicate. At this time, we decorate every predicate with `@no_inline`
# attribute to prevent any inlining. Diligent inlining may be beneficial for performance but
# is left for future work.
#
# -----------------------------------------------------------------------------------------
# In the running example, the state 2 is an exit state. Also note that the initial state is
# also a final state, thus the automaton accepts empty paths (consisting of a single node
# with type OddNode). The compiled Rel program follows. (All relations have `@no_inline`
# attribute that we omit here for brevity)
#
# // The main connectivity predicate
# def pq_conn(x0, x1): pq_conn_from_0(x0, x1)
#
# // Accepting empty paths with node transition f1
# def pq_conn(x0, x1): x0 = x1 ∧ Odd(x0)
#
# // Paths from state 0 going through t1 to state 1
# def pq_conn_from_0(x0, x2): A(x0, x1) ∧ Odd(x0) ∧ pq_conn_from_1(x1, x2)
#
# // Paths from state 0 through t1 (to state 1) and terminating with f2
# def pq_conn_from_0(x0, x1): A(x0, x1) ∧ Odd(x0) ∧ Even(x1)
#
# // Paths from state 0 through t2 (to state 1) and terminating with f3
# def pq_conn_from_0(x0, x1): A(x0, x1) ∧ Even(x0) ∧ Even(x1)
#
# // Paths from state 1 through t3 to state 1
# def pq_conn_from_1(x0, x2): A(x0, x1) ∧ Even(x0) ∧ pq_conn_from_1(x1, x2)
#
# // Paths from state 1 through t3 and terminating with f2
# def pq_conn_from_1(x0, x1): A(x0, x1) ∧ Even(x0) ∧ Even(x1)
#
# =========================================================================================
# 2. Product Graph Program
# =========================================================================================
# The Product Graph program defines a relation `pg_graph` of arity 5 that defines the set of
# edges in the product graph: `pg_graph(q, p, a, n, m)` holds iff the product graph has an
# edge from `(q, n)` to `(p, m)` and the hash value of the edge label is `a`. The program
# also defines two unary relations `pg_source(n, q)` and `pg_target(n, q)` that define the
# source and target nodes of the product graph. The computation of the product graph is
# based on the input finite automaton corresponding to the RPQ and additionally two
# relations `source` and `target` with the sets of source and target nodes of the knowledge
# graph.
#
# The program is used to compute the product graph of the automaton and a knowledge graph.
# The program is used when the user specifies the source and target nodes to be used during
# evaluation.
#
# -----------------------------------------------------------------------------------------
# In the running example, the compiled Rel program follows
#
# // Source nodes of the product graph
# def pg_source(x0, x1): source(x0) x1 = 0
#
# // Target nodes of the product graph
# def pg_target(x0, x1): target(x0) ∧ x1 = 0 ∧ Odd(x0)
# def pg_target(x0, x1): target(x0) ∧ x1 = 1 ∧ Even(x0)
# def pg_target(x0, x1): target(x0) ∧ x1 = 2 ∧ N(x0)
#
# // Edges of the product graph
# def pg_graph(x0, x1, x2, x3, x4): x0 = 0 ∧ x1 = 1 ∧ x2 = hash(-[A]→) ∧ A(x3, x4) ∧ Odd(x3)
# def pg_graph(x0, x1, x2, x3, x4): x0 = 0 ∧ x1 = 2 ∧ x2 = hash(←[B]-) ∧ B(x4, x3)
# def pg_graph(x0, x1, x2, x3, x4): x0 = 1 ∧ x1 = 1 ∧ x2 = hash(-[A]→) ∧ A(x3, x4) ∧ Even(x3)
#
# =========================================================================================


class RPQCompiler(ABC):
    def __init__(self, pattern: RPQ, options):
        self.a = prepare_automaton(pattern, options)

        self.prog_id = next_id()

        self.rules: List[Rule] = []
        self.rel_attrs: Dict[str, List[str]] = dict()

    def yield_node_filters_atoms(self, filters: Iterable[NodeFilter], x: int):
        for f in filters:
            if isinstance(f, NodeLabel):
                yield RelAtom(f.label, (x,))
            elif isinstance(f, AnonymousNodeFilter):
                yield AnonymousFilterAtom(f._unary_function, (x,))

    def yield_edge_transition_atoms(self, t, x, y):
        edge_label = t.get_label()
        if edge_label.direction == 'forward':
            yield RelAtom(edge_label.label, (x, y))
        else:
            yield RelAtom(edge_label.label, (y, x))

        if t.has_anon_edge_filters():
            for f in t.get_anon_edge_filters():
                yield AnonymousFilterAtom(f.binary_function, (x, y))

        if t.has_src_filters():
            yield from self.yield_node_filters_atoms(t.src_filters, x)

        if t.has_trg_filters():
            yield from self.yield_node_filters_atoms(t.trg_filters, y)

    def add_rule(self, head: RelAtom, body: List[Atom], n=None):
        if n is None:
            var_refs = set(head.vars).union([v for a in body for v in a.vars])
            n = len(var_refs)
        self.rules.append(Rule(head, n, body))
        logger.info(f"Added rule: {self.rules[-1]}")

# Prepares (decorates) relations and gathers their definitions.
class ConnCompiler(RPQCompiler):
    def __init__(self, pattern: RPQ, options):
        super().__init__(pattern, options)

        self.edge_transition_id = dict()
        self.final_transition_id = dict()

        self.rules: List[Rule] = []
        self.rel_attrs: Dict[str, List[str]] = dict()

        # self.main_conn_rel is the name of the binary connectivity relation `pq_conn` such
        # that `pq_conn(x, y)` holds iff there is a path from x to y with the automaton
        # having an accepting run (from an initial state to a final state).
        self.main_conn_rel = f'pq_{self.prog_id}_conn'

        # maps state q to the name of a binary connectivity relation `pg_conn_from_q` such
        # that `pg_conn_from_q(x, y)` holds iff there is a path from x to y with the
        # automaton having an accepting run when starting in state q.
        self.conn_rel: Dict[int, str] = dict()

        logger.debug("Initializing PyRel Connectivity Predicate emitter")
        logger.debug(self.a)

        self.prepare_relations()


    # -------------------------------------------------------------------------------------
    # Prepare relations for states, transitions, and final states with necessary decorators
    # -------------------------------------------------------------------------------------
    def prepare_relations(self):
        self.rel_attrs[self.main_conn_rel] = ['@track', '@no_inline']

        for q in self.a.states:
            self.prepare_state_conn_relation(q)

    def prepare_state_conn_relation(self, q):
        if self.a.is_exit(q):
            # the state does not outgoing edge-transitions but only ungrounded final node
            # transitions: we will not create an ungrounded  connectivity relation for it
            # but instead we will always contract it with the preceding transition.
            return

        self.conn_rel[q] = f'pq_{self.prog_id}_conn_from_{q}'
        self.rel_attrs[self.conn_rel[q]] = ['@no_inline']

    # -------------------------------------------------------------------------------------
    # Create rules from the automaton
    # -------------------------------------------------------------------------------------
    def make_rules(self):
        self.make_main_conn_rule()

        for q in self.a.delta:
            for p in self.a.delta[q]:
                for t in self.a.delta[q][p]:
                    self.make_edge_rules(q, p, t)

    def make_main_conn_rule(self):
        q_0 = self.a.get_initial_state()
        if not self.a.is_exit(q_0):
            init_conn_rel = self.conn_rel[q_0]
            self.add_rule(
                head = RelAtom(self.main_conn_rel, (0, 1)),
                body = [RelAtom(init_conn_rel, (0, 1))]
            )
        if q_0 in self.a.final:
            for e in self.a.final[q_0]:
                self.add_rule(
                    head = RelAtom(self.main_conn_rel, (0, 1)),
                    body = [
                        VariableEqualityAtom((0, 1)),
                        *self.yield_node_filters_atoms(e.filters, 0)
                    ]
                )

    def make_edge_rules(self, q, p, t: EdgeTransition):
        if not self.a.is_exit(p):
            self.make_transition_rule(q, p, t)

        if p in self.a.final:
            for e in self.a.final[p]:
                self.make_transition_final_rule(q, t, e)

    def make_transition_rule(self, q, p, t: EdgeTransition):
        assert not self.a.is_exit(p)

        conn_q_rel = self.conn_rel[q]
        conn_p_rel = self.conn_rel[p]

        self.add_rule(
            head = RelAtom(conn_q_rel, (0, 2)),
            body = [
                *self.yield_edge_transition_atoms(t, 0, 1),
                RelAtom(conn_p_rel, (1, 2))
            ]
        )

    def make_transition_final_rule(self, q, t: EdgeTransition, e: NodeTransition):
        conn_q_rel = self.conn_rel[q]

        self.add_rule(
            head = RelAtom(conn_q_rel, (0, 1)),
            body = [
                *self.yield_edge_transition_atoms(t, 0, 1),
                *self.yield_node_filters_atoms(e._filters, 1)
            ]
        )

def compile_conn(pattern, options=DEFAULT_OPTIONS) -> DatalogProgram:
    compiler = ConnCompiler(pattern, options)
    compiler.make_rules()

    program = DatalogProgram(
        root_rel = {'conn_rel': compiler.main_conn_rel},
        rel_attrs = compiler.rel_attrs,
        rules = compiler.rules,
        edge_label_map = None
    )

    return program


class ProductGraphCompiler(RPQCompiler):
    def __init__(self, pattern: RPQ, source_rel: str, target_rel: str, options):
        super().__init__(pattern, options)

        self.source_rel = source_rel
        self.target_rel = target_rel

        # The name of the relation with the edges in the product graph of the knowledge
        # graph and the input automaton. The relation has arity `5` and contains a tuple
        # `(q, p, a, n, m)` iff the product graph has an edge from `(q, n)` to `(p, m)` and
        # the hash value of the edge label is `a`.
        self.pg_graph_rel = f'pg_{self.prog_id}_graph'

        # The relation names of the source and target nodes of the product graph; arity 2,
        # each contains pairs `(n, q)`, where `n` is the node of the knowledge graph and `q`
        # is a state of the automaton.
        self.pg_source_rel = f'pg_{self.prog_id}_source'
        self.pg_target_rel = f'pg_{self.prog_id}_target'

        self.rel_attrs[self.pg_graph_rel] = ['@pipeline']
        self.rel_attrs[self.pg_source_rel] = ['@pipeline']
        self.rel_attrs[self.pg_target_rel] = ['@pipeline']

        # maps hashes of edge labels to edge labels
        self.pg_edge_label_map: Dict[int, EdgeLabel] = {
            hash(lab): lab for lab in self.a.alphabet
        }

        logger.info("Initializing PyRel Product Graph emitter")
        logger.info(self.a)


    # -------------------------------------------------------------------------------------
    # Prepare definitions of the 3 main relations
    # -------------------------------------------------------------------------------------

    def make_rules(self):
        self.make_pg_source_rules()
        self.make_pg_graph_rules()
        self.make_pg_target_rules()

    def make_pg_source_rules(self):
        for q in self.a.init:
            # pg_source(n, x) ← source_rel(n) ∧ x = q
            self.add_rule(
                head = RelAtom(self.pg_source_rel, (0, 1)),
                body = [
                    RelAtom(self.source_rel, (0,)),
                    ConstantEqualityAtom((1, q))
                ]
            )

    def make_pg_target_rules(self):
        for q in self.a.final:
            for e in self.a.final[q]:
                # pg_target(n, x) ← target_rel(n) ∧ x = q ∧ e(n)
                self.add_rule(
                    head = RelAtom(self.pg_target_rel, (0, 1)),
                    body = [
                        RelAtom(self.target_rel, (0,)),
                        ConstantEqualityAtom((1, q)),
                        *self.yield_node_filters_atoms(e.filters, 0)
                    ]
                )

    def make_pg_graph_rules(self):
        for q in self.a.delta:
            for p in self.a.delta[q]:
                for t in self.a.delta[q][p]:
                    # pg_edge(x, y, a, n, m) ← q = x ∧ p = y ∧ a = #label(t) ∧ t(n, m)
                    self.add_rule(
                        head = RelAtom(self.pg_graph_rel, (0, 1, 2, 3, 4)),
                        body = [
                            ConstantEqualityAtom((0, q)),
                            ConstantEqualityAtom((1, p)),
                            ConstantEqualityAtom((2, hash(t.get_label()))),
                            *self.yield_edge_transition_atoms(t, 3, 4)
                        ]
                    )


def compile_product_graph(pattern: RPQ, source_rel: str, target_rel: str, options=DEFAULT_OPTIONS) -> DatalogProgram:
    compiler = ProductGraphCompiler(pattern, source_rel, target_rel, options)
    compiler.make_rules()

    logger.info('Mapping edge labels:')
    for pq_edge_label in compiler.pg_edge_label_map:
            logger.info(f" * {pq_edge_label} is {compiler.pg_edge_label_map[pq_edge_label]}")

    program = DatalogProgram(
        root_rel = {
            'pg_graph_rel': compiler.pg_graph_rel,
            'pg_source_rel': compiler.pg_source_rel,
            'pg_target_rel': compiler.pg_target_rel
        },
        rel_attrs = compiler.rel_attrs,
        rules = compiler.rules,
        edge_label_map = compiler.pg_edge_label_map
    )

    return program
