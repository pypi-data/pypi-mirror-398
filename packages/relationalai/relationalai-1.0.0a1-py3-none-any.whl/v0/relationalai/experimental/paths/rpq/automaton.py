from typing import List, Dict, Set, Tuple
from v0.relationalai.debugging import warn

from .filter import EdgeLabel
from .transition import (
    EdgeTransition, NodeTransition, simulate
)

# =========================================================================================
# Finite Automaton
# =========================================================================================
#
# An NFA consists of:
# - states -- a finite set of states (integers)
# - init ⊆ states -- a set of initial states
# - delta: states → states → {EdgeTransition} -- transition function
# - final: states → {NodeTransition} -- final states function
#
# We introduce the NFA because a number of simplification manipulations are easier to
# perform on an NFA than on a Glushkov outline. The NFA is obtained from the Glushkov
# outline simply by adding a distinguished initial state 0 and using first transitions and
# last transitions to extend the transition function and final states. The simplification
# operations only remove unnecessary states and transitions; and their main purpose is to
# remove simple cases of non-determinism due to the use of the repetition `[n:m]` in RPQs.
# We do not perform more sophisticated operations such as determinization as those may lead
# to introduction of new states and loss of correspondence between states and the positions
# in the original RPQ.
#
# ------------------------------------------------------------------------------------------
# Example
# ------------------------------------------------------------------------------------------
# Recall the RPQ `path(OddNode, star('-[A]->', EvenNode) | path('<-[B]-', Node)` and its
# Glushkov automaton outline:
#
#  * epsilon:
#    ⋅ ⊨⸨OddNode⸩⇒
#  * positions (label):
#      1 -⟨A⟩→
#      2 ←⟨B⟩-
#  * first:
#      → 1:
#        ⋅ ⊨⸨OddNode⸩=⟦-⟨A⟩→⟧=⸨⸩⇒
#      → 2:
#        ⋅ ⊨⸨⸩=⟦←⟨B⟩-⟧=⸨⸩⇒
#  * follows:
#     - 1
#       → 1:
#         ⋅ ⊨⸨EvenNode⸩=⟦-⟨A⟩→⟧=⸨⸩⇒
#  * last:
#     - 1:
#       ⋅ ⊨⸨EvenNode⸩⇒
#     - 2:
#       ⋅ ⊨⸨Node⸩⇒
#
# The corresponding (reduced) finite automaton follows:
#
# * states: 0 1 2
# * init: 0
# * delta:
#    - 0
#       → 1
#         ⋅ ⊨⸨OddNode⸩=⟦-⟨A⟩→⟧=⸨⸩⇒
#       → 2
#         ⋅ ⊨⸨⸩=⟦←⟨B⟩-⟧=⸨⸩⇒
#    - 1
#       → 1
#         ⋅ ⊨⸨EvenNode⸩=⟦-⟨A⟩→⟧=⸨⸩⇒
# * final:
#    - 0
#       ⋅ ⊨⸨OddNode⸩⇒
#    - 1
#       ⋅ ⊨⸨EvenNode⸩⇒
#    - 2
#       ⋅ ⊨⸨Node⸩⇒
# =========================================================================================

class Automaton:
    def __init__(self,
                 states: Set[int],
                 init:Set[int],
                 delta: Dict[int, Dict[int, Set[EdgeTransition]]],
                 final: Dict[int, Set[NodeTransition]]):
        self.states = states
        self.init = init
        self.delta = delta
        self.final = final

    def __repr__(self) -> str:
        res = "Automaton:\n"
        res += "* states: " + ' '.join([str(s) for s in sorted(self.states)]) + "\n"
        res += "* init: " + ' '.join([str(s) for s in sorted(self.init)]) + "\n"
        res += "* delta:\n"
        for q in sorted(self.delta):
            res += f"   - {q}\n"
            for p in sorted(self.delta[q]):
                res += f"      → {p}\n"
                for t in self.delta[q][p]:
                    res += f"        ⋅ {t}\n"
        res += "* final: \n"
        for q in sorted(self.final):
            res += f"   - {q}\n"
            for t in self.final[q]:
                res += f"      ⋅ {t}\n"
        return res[:-1]

    def __len__(self) -> int:
        return len(self.states)

    def to_dict(self) -> dict:
        return {
            "type": "Automaton",
            "states": list(sorted(self.states)),
            "init": list(sorted(self.init)),
            "delta": {
                q: {
                    p: [t.to_dict() for t in self.delta[q][p]]
                    for p in self.delta[q]
                }
                for q in self.delta
            },
            "final": {
                q: [t.to_dict() for t in self.final[q]]
                for q in self.final
            }
        }

    @property
    def alphabet(self) -> Set[EdgeLabel]:
        res = set()
        for q in self.delta:
            for p in self.delta[q]:
                for t in self.delta[q][p]:
                    res.add(t.get_label())
        return res

    # Methods to query the automaton regardless of whether it is complete or not
    def get_edge_transitions(self, q: int, p: int) -> Set[EdgeTransition]:
        return self.delta.get(q, dict()).get(p, set())

    def get_edge_labels(self, q: int, p: int) -> Set[EdgeLabel]:
        return {t.get_label() for t in self.get_edge_transitions(q, p)}

    def has_edge_transitions(self, q: int, p: int) -> bool:
        return len(self.get_edge_transitions(q, p)) > 0

    def get_outbound_states(self, q: int) -> Set[int]:
        return {p for p in self.states if self.has_edge_transitions(q, p)}

    def get_inbound_states(self, p: int) -> Set[int]:
        return {q for q in self.states if self.has_edge_transitions(q, p)}

    def get_initial_state(self) -> int:
        assert len(self.init) == 1, "Automaton is non-deterministic: multiple initial states"
        return next(iter(self.init))

    def get_final_states(self) -> Set[int]:
        return {q for q in self.states if self.is_final(q)}

    def is_final(self, q: int) -> bool:
        return len(self.get_final_transitions(q)) > 0

    def is_exit(self, q: int) -> bool:
        return self.is_final(q) and len(self.get_outbound_states(q)) == 0

    def get_final_transitions(self, q: int) -> Set[NodeTransition]:
        return self.final.get(q, set())

    # Returns a list of strings explaining causes of non-determinism
    def determinism_report(self) -> List[str]:
        report = []

        # this won't be happening if we work with Glushkov automata from RPQ
        if len(self.init) > 1:
            report.append(f"Multiple initial states: {', '.join(map(str, self.init))}")

        def complain(q: int, lab: EdgeLabel, T: Set[Tuple[EdgeTransition, int]]) -> str:
            if q == 0:
                complaint = f"Ambiguous initial transitions for label {lab}:\n"
            else:
                complaint = f"Ambiguous transitions from {q} with label {lab}:\n"
            for (t, p) in T:
                complaint += f"  -> to position {p} (with transition {t})\n"
            return complaint

        for q in self.states:
            q_labels: Dict[EdgeLabel, Set[Tuple[EdgeTransition, int]]] = dict()
            for p in self.get_outbound_states(q):
                for t in self.delta[q][p]:
                    lab = t.get_label()
                    if lab not in q_labels:
                        q_labels[lab] = set()
                    q_labels[lab].add((t, p))

            for lab in q_labels:
                if len(q_labels[lab]) > 1:
                    report.append(complain(q, lab, q_labels[lab]))

        return report

    def is_deterministic(self) -> bool:
        return len(self.determinism_report()) == 0

    # Checks if the automaton has no reachable final states i.e. empty language.
    def is_void(self) -> bool:
        reachable: Set[int] = set()
        frontier: Set[int] = self.init.copy()
        while len(frontier) > 0:
            q = frontier.pop()
            if q in reachable:
                continue
            reachable.add(q)
            for p in self.get_outbound_states(q):
                if p in reachable | frontier:
                    continue
                frontier.add(p)

        return len(reachable & self.get_final_states()) == 0

    # Checks whether the automaton is grounded, i.e., it accepts only a finite number of
    # paths in given a finite graph. An automaton can accept an infinite number of
    # single-node paths if the initial state is accepting with an final ε-transition that
    # does not check for node label.
    def is_grounded(self) -> bool:
        return all(t.is_grounded() for q in self.init for t in self.get_final_transitions(q))

    # ----------------------------------------------------------------------------
    # Reduction
    # ----------------------------------------------------------------------------

    # Simplifies the automaton by removing unnecessary states and transitions.
    def reduce(self, prune_states_only=False):
        while True:
            pruned = False

            # logger.debug("Pruning iteration for")
            # logger.debug(self)

            pruned |= self.prune_unreachable_states()
            pruned |= self.prune_unproductive_states()

            if not prune_states_only:
                pruned |= self.prune_redundant_transitions()

            if not pruned:
                break

        # logger.debug("Final automaton after reduction:")
        # logger.debug(self)

    # Prunes unreachable states: returns True if any states were pruned.
    def prune_unreachable_states(self) -> bool:
        reachable: Set[int] = set()
        frontier: Set[int] = self.init.copy()
        while len(frontier) > 0:
            q = frontier.pop()
            if q in reachable:
                continue
            reachable.add(q)
            for p in self.get_outbound_states(q):
                if p in reachable | frontier:
                    continue
                frontier.add(p)

        unreachable = self.states - reachable

        # logger.debug('Unreachable states:')
        # logger.debug(list(sorted(unreachable)))

        self.prune(redundant_states=unreachable)

        return len(unreachable) > 0

    # Prunes unproductive states: returns True if any states were pruned.
    def prune_unproductive_states(self, debug: bool=True) -> bool:
        productive: Set[int] = set()
        frontier = {q for q in self.states if self.is_final(q)}
        while len(frontier) > 0:
            q = frontier.pop()
            if q in productive:
                continue
            productive.add(q)
            for p in self.get_inbound_states(q):
                if p in productive | frontier:
                    continue
                frontier.add(p)

        unproductive = self.states - productive

        # logger.debug('Unproductive states:')
        # logger.debug(list(sorted(unproductive)))

        self.prune(redundant_states=unproductive)

        return len(unproductive) > 0

    # Uses simulation relation on states to identify and prune redundant transitions.
    # Returns True if any transitions were pruned.
    def prune_redundant_transitions(self, debug: bool=True) -> bool:
        # The simulation relation:
        #
        # p _simulates_ q, in code `(p,q) in simulates`, iff
        # 1) for every transition t from q to q' there is a transition t' from p to p' such
        #    that t' simulates t and p' simulates q'.
        # 2) for every final transition t from q there is a final transition t' from p such
        #    that t' simulates t.
        #
        # Property: if p simulates q, then any path accepted from q is also accepted from p.
        #           The converse does not need to hold.
        #
        # The simulation relation is reflexive and transitive but not necessarily symmetric.

        # We begin with the Cartesian product of states and iteratively remove pairs
        # whenever an argument against simulation is found.
        simulates = {(p, q) for p in self.states for q in self.states}

        # logger.debug("Initial simulation:")
        # logger.debug(simulation_to_dict(simulates))

        # First, we remove pairs where acceptance of empty paths is not simulated
        remove_pairs = set()
        for p in self.states:
            for q in self.get_final_states():
                if not simulate(self.get_final_transitions(p), self.get_final_transitions(q)):
                    remove_pairs.add((p, q))

        simulates -= remove_pairs

        # logger.debug("Pairs removed due to final state simulation:")
        # logger.debug(list(sorted(remove_pairs)))
        # logger.debug("Simulation pairs after final state check:")
        # logger.debug(simulation_to_dict(simulates))

        # Next, we inspect the transitions between positions
        while True:
            remove_pairs = set()
            for (p, q) in simulates:
                for next_q in self.get_outbound_states(q):
                    for t_q in self.get_edge_transitions(q, next_q):
                        t_p_found = False
                        for next_p in self.get_outbound_states(p):
                            if (next_p, next_q) not in simulates:
                                continue
                            for t_p in self.get_edge_transitions(p, next_p):
                                if t_p.simulates(t_q):
                                    t_p_found = True
                        if not t_p_found:
                            remove_pairs.add((p, q))

            # logger.debug("Pairs removed in transition check iteration:")
            # logger.debug(list(sorted(remove_pairs)))
            # logger.debug("Simulation pairs after transition check iteration:")
            # logger.debug(simulation_to_dict(simulates))

            if len(remove_pairs) == 0:
                break

            simulates -= remove_pairs


        # At this point, the simulation relation is in `simulates`

        # We identify redundant transitions using the simulation relation.

        # A final node transition t1 from q is _redundant_ if there is a final node
        # transition t2 != t1 from q such that t2 simulates t1. For final transitions, we do
        # not need to worry about cycles because if t1 is redundant due to t2 and t2 is
        # redundant due to t1, then t1 == t2.

        redundant_final_transitions: Dict[int, Set[NodeTransition]] = dict()
        for q in self.get_final_states():
            for t in self.get_final_transitions(q):
                for t2 in self.get_final_transitions(q):
                    if t == t2:
                        continue
                    if t2.simulates(t):
                        # logger.debug(f"Final transition {t} from {q} is redundant because simulated by {t2}")
                        if q not in redundant_final_transitions:
                            redundant_final_transitions[q] = set()
                        redundant_final_transitions[q].add(t)

        # logger.debug("Redundant final transitions:")
        # logger.debug(final_transitions_to_dict(redundant_final_transitions))

        # Detecting redundant edge transitions is more subtle because cycles are possible.

        # An edge-transition t1 from p to q1 _subsumes_ (is more general than) a
        # edge-transition t2 from p to q2 if t1 simulates t2, q1 simulates q2, and q1 != q2.
        # In code `(t1, q1) in subsumes[p][(t2, q2)]`.

        subsumes: Dict[int, Dict[Tuple[EdgeTransition, int], Set[Tuple[EdgeTransition, int]]]] = {
            p: dict() for p in self.states
        }

        for q in self.states:
            for q1 in self.get_outbound_states(q):
                for t1 in self.get_edge_transitions(q, q1):
                    for q2 in self.get_outbound_states(q):
                        for t2 in self.get_edge_transitions(q, q2):
                            if t1.simulates(t2) and (q1, q2) in simulates and q1 != q2:
                                if (t2, q2) not in subsumes[q]:
                                    subsumes[q][(t2, q2)] = set()
                                subsumes[q][(t2, q2)].add((t1, q1))
        # logger.debug("Subsumption:")
        # logger.debug(subsumption_to_dict(subsumes))

        # An edge-transition t2 from p to q2 is _redundant_ if
        # 1) there is an edge-transition t1 from p such that t1 subsumes t2 but t2 does not
        #    subsume t1.
        # 2) there is an edge-transition t1 from p to q1 such that t1 subsumes t2 and t2
        #    subsumes t1, but q1 > q2. (breaking subsumption cycles)
        redundant_edge_transitions: Dict[Tuple[int,int], Set[EdgeTransition]]= dict()
        for q in subsumes:
            for (t2, q2) in subsumes[q]:
                for (t1, q1) in subsumes[q][(t2, q2)]:
                    if (t2, q2) not in subsumes[q].get((t1, q1), set()) or q1 > q2:
                        if (q, q2) not in redundant_edge_transitions:
                            redundant_edge_transitions[(q, q2)] = set()
                        redundant_edge_transitions[(q, q2)].add(t2)

        # logger.debug("Redundant edge transitions:")
        # logger.debug(edge_transitions_to_dict(redundant_edge_transitions))

        self.prune(redundant_edge_transitions=redundant_edge_transitions,
                   redundant_final_transitions=redundant_final_transitions)

        return len(redundant_edge_transitions) > 0 or len(redundant_final_transitions) > 0

    # Trims the automaton by removing redundant states and transitions
    def prune(self,
              redundant_states: Set[int] = set(),
              redundant_edge_transitions: Dict[Tuple[int,int], Set[EdgeTransition]] = dict(),
              redundant_final_transitions: Dict[int, Set[NodeTransition]] = dict()):

        states = self.states - redundant_states
        init = self.init & states
        delta = dict()
        final = dict()

        for q in states:
            for p in states:
                T = self.get_edge_transitions(q, p)
                T = T - redundant_edge_transitions.get((q, p), set())
                if len(T) > 0:
                    if q not in delta:
                        delta[q] = dict()
                    delta[q][p] = T

        for q in states:
            T = self.get_final_transitions(q)
            T = T - redundant_final_transitions.get(q, set())
            if len(T) > 0:
                final[q] = T

        self.states = states
        self.init = init
        self.delta = delta
        self.final = final


#
# Private functions for logging only
#

#
# `logger` treats any dictionary as an event. To enable logging of arbitrary data
# structures we convert them to dictionary but need to encapsulate them in a class that
# implements `to_dict` method that ensures that the dictionary is not treated as an
# event but emitted as a json fragment
#
class DictEncapsulation:
    def __init__(self, d):
        self.d = d

    def to_dict(self):
        return self.d

    def __repr__(self):
        return str(self.d)

def simulation_to_dict(simulates: Set[Tuple[int, int]]):
    d = dict()
    for (p, q) in simulates:
        if p not in d:
            d[p] = list()
        d[p].append(q)
    for p in d:
        d[p].sort()
    return DictEncapsulation(d)

def final_transitions_to_dict(final_transitions: Dict[int, Set[NodeTransition]]):
    d = dict()
    for q in final_transitions:
        if len(final_transitions[q]) == 0:
            continue
        d[q] = [t.to_dict() for t in final_transitions[q]]
    return DictEncapsulation(d)

def subsumption_to_dict(subsumes: Dict[int, Dict[Tuple[EdgeTransition, int], Set[Tuple[EdgeTransition, int]]]]):
    d = dict() # p -> [{'transition': t, 'to': q, 'subsumes': [{'transition': t0, 'to': q0}]}]

    for p in subsumes:
        if len(subsumes[p]) == 0:
            continue
        if p not in d:
            d[p] = list()
        for (t, q) in subsumes[p]:
            for (t0, q0) in subsumes[p][(t, q)]:
                d[p].append({
                    'transition': t.to_dict(),
                    'to': q,
                    'subsumes': {
                        'transition': t0.to_dict(),
                        'to': q0
                    }
                })

    return DictEncapsulation(d)


def edge_transitions_to_dict(edge_transitions: Dict[Tuple[int,int], Set[EdgeTransition]]):
    d = dict() # p -> q -> [t]

    for (p, q) in edge_transitions:
        if p not in d:
            d[p] = dict()

        if q not in d[p]:
            d[p][q] = list()

        for t in edge_transitions[(p, q)]:
            d[p][q].append(t.to_dict())

    return DictEncapsulation(d)

def prepare_automaton(pattern, options) -> Automaton:
    from .diagnostics import (
        PathfinderSizeWarning,
        PathfinderNonDeterminismWarning,
        PathfinderVoidPatternError,
        PathfinderUngroundedPatternError
    )

    force_transition_pruning = options.get('force_transition_pruning', False)

    # logger.debug("Emitting PyRel for RPQ")
    # logger.debug(pattern)

    # Pattern compilation
    g = pattern.glushkov()

    # logger.debug(g)

    a = g.automaton()

    # logger.debug("Before reduction")
    # logger.debug(a)
    # logger.debug(f"Size: {len(a)}")
    # logger.debug(f"Automaton is deterministic: {a.is_deterministic()}")

    prune_states_only = len(pattern) >= 50
    if force_transition_pruning:
        prune_states_only = False
    if len(pattern) >= 50:
        warn(PathfinderSizeWarning(pattern, prune_states_only))

    # Automaton reduction
    # logger.debug(f"Prune states only: {prune_states_only}")
    a.reduce(prune_states_only=prune_states_only)

    # logger.debug("After reduction")
    # logger.debug(a)
    # logger.debug(f"Size: {len(a)}")
    # logger.debug(f"Automaton is deterministic: {a.is_deterministic()}")

    if not a.is_deterministic():
        warn(PathfinderNonDeterminismWarning(pattern, a, prune_states_only))

    if a.is_void():
        raise PathfinderVoidPatternError(pattern)

    if not options['suppress_groundedness_test'] and not a.is_grounded():
        raise PathfinderUngroundedPatternError(pattern)

    return a
