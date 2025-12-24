from typing import Dict, Set, Optional

from v0.relationalai.experimental.pathfinder.transition import (
    NodeTransition, NodeFilter, EdgeTransition, EdgeFilter, EdgeLabel
)
from v0.relationalai.experimental.pathfinder.automaton import Automaton

# =========================================================================================
# Glushkov Construction
# =========================================================================================
#
# The Glushkov construction [1] allows to construct an automaton from a given regular
# expression in a manner such that every (non-initial) state of the automaton corresponds to
# a position of a specific edge label in the input expression.  This is an important
# property, maintained throughout the whole integration, because it allows to provide
# actionable diagnostic information to the user composing their queries.
#
# Strictly speaking, the construction does not construct a finite automata but its analogue
# that we refer to as an _outline_.  The main difference is the lack of an initial state.
# Outlines are, however, closed under the standard operations of regular expressions, such
# as union, concatenation, and Kleene closure.  They allow to construct the final outline by
# traversing the input regular expression in a bottom-up fashion.  The final outline is then
# equipped with a single initial state.  The Glushkov construction is commonly used to
# identify the class of Deterministic Regular Expressions, that yield a Deterministic Finite
# Automata [2, 3].  We use it to check the determinism of the automaton representing the
# input RPQ, which is essential for the correctness of Pathfinder execution.  More
# importantly, the correspondence between the automaton states and positions of the Regular
# Path Query shall allows to provide actionable diagnostic messages to the user composing
# their queries [4].
#
# A Glushkov outline consist of a set of _positions_, each corresponding to a specific
# occurrence of an edge label in the regular path query.  The transitions between the two
# positions are encoded with edge transitions stored in the _follow_ relation.  An outline
# does not have initial states: their role is played by the set of _first_ positions with
# incoming edge transitions.  The essential property is  that an edge transition arriving in
# a position has the same edge label as the position.  The final states are represented with
# sets of _last_ positions with outgoing node transition that verifies any additional
# conditions on the last node in a path that must be satisfied.  Finally, for completeness
# an outline also has an _epsilon_ set of node transitions that allow to recognize empty
# paths, consisting of a single node, which do not advance on any edge transition.
#
# -----------------------------------------------------------------------------------------
# Glushkov automaton outline
# -----------------------------------------------------------------------------------------
# A Glushkov outline consists of:
# - epsilon: {NodeTransition} -- epsilon transitions that allow to accept empty paths
# - pos: {int} -- set of positions of the original regular path expression
# - label: pos -> EdgeLabel -- edge labels of positions (edge labels of incoming transitions)
# - first: pos -> {EdgeTransition} -- first positions with incoming edge-transitions
# - follow: pos -> pos -> {EdgeTransition} -- follow transitions between positions
# - last: pos -> {NodeTransition} -- last positions with outgoing ε-transitions
#
# In our constructions, we represent above functions with dicts. For simplicity, we
# manipulate on _complete_ Glushkov outlines i.e., having all dicts total, possibly mapping
# to a (vacuous) empty sets of transitions. These are removed in the final stage of
# trimming.
#
# -----------------------------------------------------------------------------------------
# Example
# -----------------------------------------------------------------------------------------
# We present an example of the Glushkov automaton outline for the following pattern
#
# path(Odd, star('-[A]->', Even)) | path('<-[B]-', N)
#
# which is parsed into the following RPQ (with 2 positions)
#
# ╷ Union
# ├──┐ Concat
# │  ├──╴ Node(Odd)
# │  └──┐ Star
# │     └──┐ Concat
# │        ├──╴ Edge(-⟨A⟩→) pos=1
# │        └──╴ Node(Even)
# └──┐ Concat
#    ├──╴ Edge(←⟨B⟩-) pos=2
#    └──╴ Node(N)
#
# The Glushkov automaton outline follows (vacuous elements omitted):
#  * epsilon:
#    ⋅ ⊨⸨Odd⸩⇒
#  * positions (label):
#      1 -⟨A⟩→
#      2 ←⟨B⟩-
#  * first:
#      → 1:
#        ⋅ ⊨⸨Odd⸩=⟦-⟨A⟩→⟧=⸨⸩⇒
#      → 2:
#        ⋅ ⊨⸨⸩=⟦←⟨B⟩-⟧=⸨⸩⇒
#  * follows:
#     - 1
#       → 1:
#         ⋅ ⊨⸨Even⸩=⟦-⟨A⟩→⟧=⸨⸩⇒
#  * last:
#     - 1:
#       ⋅ ⊨⸨Even⸩⇒
#     - 2:
#       ⋅ ⊨⸨N⸩⇒
# -----------------------------------------------------------------------------------------
#
# References:
# [1] Glushkov Automaton: https://en.wikipedia.org/wiki/Glushkov%27s_construction_algorithm
# [2] Finite Automata: https://en.wikipedia.org/wiki/Nondeterministic_finite_automaton
# [3] Deterministic FA: https://en.wikipedia.org/wiki/Deterministic_finite_automaton
# [4] RPQs in Rel: https://docs.google.com/document/d/1GW71mJTCkCo8wPvOjGIKalUApPOZzKV-L7xHoD8Cel8
# =========================================================================================


class Glushkov:
    def __init__(self,
                 epsilon:  Set[NodeTransition],
                 position: Set[int],
                 label:    Dict[int, EdgeLabel],
                 first:    Dict[int, Set[EdgeTransition]],
                 follow:   Dict[int, Dict[int, Set[EdgeTransition]]],
                 last:     Dict[int, Set[NodeTransition]]):

        self.epsilon = epsilon
        self.position = position
        self.label = label
        self.first = first
        self.follow = follow
        self.last = last

        self.check_consistency()
        self.check_completeness()

    def check_consistency(self):
        for pos in self.position:
            assert pos in self.label, f"Position {pos} is missing a label"

        for pos in self.label:
            assert pos in self.position, f"Illegal position {pos} in label with {self.label[pos]}"

        for pos in self.first:
            assert pos in self.position, f"Illegal first position {pos}"
        for pos in self.first:
            for t in self.first[pos]:
                fl = self.label[pos]
                assert fl in t._edge_filters, f"Missing edge label filter {fl} in the transition {t} to the first position {pos}"
                for f in t._edge_filters:
                    if isinstance(f, EdgeLabel):
                        assert f == fl, f"Edge label filter {f} of the transition {t} does not match the label {fl} of first postion {pos}"

        for pos in self.follow:
            assert pos in self.position, f"Illegal follow position {pos}"
            for next_pos in self.follow[pos]:
                assert next_pos in self.position, f"Illegal position {next_pos} following {pos}"
                tl = self.label[next_pos]
                for t in self.follow[pos][next_pos]:
                    assert tl in t._edge_filters, f"Missing edge label filter {tl} in the transition {t} from {pos} to {next_pos}"
                    for f in t._edge_filters:
                        if isinstance(f, EdgeLabel):
                            assert f == tl, f"Edge label {f} of the transition {t} from {pos} to {next_pos} does not match the label {tl}"
        for pos in self.last:
            assert pos in self.position, f"Illegal last position {pos} "

    def check_completeness(self):
        for pos in self.position:
            assert pos in self.first, f"Missing first position {pos}"
            assert pos in self.last, f"Missing last position {pos}"
            assert pos in self.follow, f"Missing follow position {pos}"
            for next_pos in self.position:
                assert next_pos in self.follow[pos], f"Missing follow transition from {pos} to {next_pos}"

    # Output a human-readable representation of the Glushkov outline.  Because Glushkov
    # outlines uses complete dicts, we omit any empty elements that would otherwise create
    # noise in the output.
    def __repr__(self) -> str:
        s = "Glushkov"
        s += ":\n"

        s += " * epsilon:\n"
        for t in self.epsilon:
            s += f"   ⋅ {t}\n"

        s += " * positions (label): \n"
        for pos in sorted(self.position):
            s += f"     {pos} {self.label[pos]}\n"

        s += " * first:\n"
        for pos in sorted(self.first):
            if len(self.first[pos]) == 0:
                continue
            s += f"     → {pos}: \n"
            for t in self.first[pos]:
                s += f"       ⋅ {t}\n"

        s += " * follows: \n"
        for pos in sorted(self.follow):
            pos_printed = False
            for next_pos in sorted(self.follow[pos]):
                if len(self.follow[pos][next_pos]) == 0:
                    continue
                if not pos_printed:
                    s += f"    - {pos}\n"
                    pos_printed = True

                s += f"      → {next_pos}:\n"
                for t in self.follow[pos][next_pos]:
                    s += f"        ⋅ {t}\n"

        s += " * last: \n"
        for pos in sorted(self.last):
            if len(self.last[pos]) == 0:
                continue
            s += f"    - {pos}: \n"
            for t in self.last[pos]:
                s += f"      ⋅ {t}\n"

        return s

    def to_dict(self) -> dict:
        return {
            "type": "Glushkov",
            "epsilon": [t.to_dict() for t in self.epsilon],
            "position": list(sorted(self.position)),
            "label": {pos: self.label[pos].to_dict() for pos in self.label},
            "first": {pos: [t.to_dict() for t in self.first[pos]]
                           for pos in self.first if len(self.first[pos]) > 0},
            "follow": {pos: {next_pos: [t.to_dict() for t in self.follow[pos][next_pos]
                                                    if len(self.follow[pos][next_pos]) > 0]
                                       for next_pos in self.follow[pos]
                                       if len(self.follow[pos][next_pos]) > 0}
                            for pos in self.follow
                            if any(len(self.follow[pos][next_pos]) > 0
                                   for next_pos in self.follow[pos])},
            "last": {pos: [t.to_dict() for t in self.last[pos]]
                          for pos in self.last
                          if len(self.last[pos]) > 0}
        }

    # Copy of the Glushkov outline up to transition sets (which are assumed immutable).
    def copy(self) -> 'Glushkov':
        epsilon = self.epsilon.copy()
        position = self.position.copy()
        label = self.label.copy()
        first = {pos: self.first[pos].copy() for pos in self.first}
        follow = {pos: {next_pos: self.follow[pos][next_pos].copy() for next_pos in self.follow[pos]} for pos in self.follow}
        last = {pos: self.last[pos].copy() for pos in self.last}

        return Glushkov(epsilon, position, label, first, follow, last)

    # Constructs the Automaton from the Glushkov outline.
    def automaton(self) -> Automaton:
        states = self.position | {0}
        init = {0}
        delta = self.follow | {0: {p : self.first[p] for p in self.first}}
        final = self.last
        if len(self.epsilon) > 0:
            final[0] = self.epsilon
        return Automaton(states, init, delta, final)


    # ------------------------------------------------------------------------
    # Mutable operations used to build a new Glushkov automaton outline
    # ------------------------------------------------------------------------

    # adds a single epsilon transition
    def _add_epsilon_transition(self, t: NodeTransition) -> None:
        self.epsilon.add(t)

    # adds all epsilon transitions from another Glushkov automaton outline
    def _add_all_epsilon_transitions(self, other: 'Glushkov') -> None:
        for t in other.epsilon:
            self._add_epsilon_transition(t)

    # adds a single position
    def _add_position(self, pos: int, label: EdgeLabel) -> None:
        assert pos not in self.position, f"Position {pos} already exists"
        self.position.add(pos)
        self.label[pos] = label
        self.first[pos] = set()
        self.follow[pos] = {next_pos: set() for next_pos in self.position}
        for p in self.position:
            if pos not in self.follow[p]:
                self.follow[p][pos] = set()
        self.last[pos] = set()

    # add all positions from another Glushkov automaton
    def _add_all_positions(self, other: 'Glushkov') -> None:
        for pos in other.position:
            self._add_position(pos, other.label[pos])

    # adds a single first transition
    def _add_first_transition(self, pos: int, t: EdgeTransition) -> None:
        assert pos in self.position, f"Position {pos} missing"
        assert self.label[pos] in t._edge_filters, f"Missing edge label filter {self.label[pos]} in the transition {t} to the first position {pos}"
        self.first[pos].add(t)

    # adds all first transitions from another Glushkov automaton outline
    def _add_all_first_transitions(self, other: 'Glushkov') -> None:
        for pos in other.first:
            for t in other.first[pos]:
                self._add_first_transition(pos, t)

    # mutable operation
    def _add_follow_transition(self, pos: int, next_pos: int, t: EdgeTransition) -> None:
        assert pos in self.position, f"Source position {pos} missing"
        assert next_pos in self.position, f"Target position {next_pos} missing"
        assert self.label[next_pos] in t._edge_filters, f"Missing edge label filter {self.label[next_pos]} in the transition {t} from {pos} to {next_pos}"
        self.follow[pos][next_pos].add(t)

    # adds all follow transitions from another Glushkov automaton outline
    def _add_all_follow_transitions(self, other: 'Glushkov') -> None:
        for pos in other.follow:
            for next_pos in other.follow[pos]:
                for t in other.follow[pos][next_pos]:
                    self._add_follow_transition(pos, next_pos, t)

    # adds a single last transition
    def _add_last_transition(self, pos: int, t: NodeTransition) -> None:
        assert pos in self.position, f"Position {pos} missing"
        self.last[pos].add(t)

    # adds all last transitions from another Glushkov automaton outline
    def _add_all_last_transitions(self, other: 'Glushkov') -> None:
        for pos in other.last:
            for t in other.last[pos]:
                self._add_last_transition(pos, t)

    # -------------------------------------------------------------------------------------
    # Operations to build a Glushkov automata using base cases and RegEx operators.
    # -------------------------------------------------------------------------------------

    # The void language, empty set, `L(∅)`.
    @staticmethod
    def void() -> 'Glushkov':
        return Glushkov(
            epsilon = set(),
            position = set(),
            label = dict(),
            first = dict(),
            follow = dict(),
            last = dict()
        )

    # The set of empty paths with single node satisfying given filters, L(ε(filter)),
    @staticmethod
    def node_transition(*filters: NodeFilter) -> 'Glushkov':
        g = Glushkov.void()
        g._add_epsilon_transition(NodeTransition(set(filters)))

        return g

    # The set of paths with a single edge satisfying given filters, L({()-[R(filter)]->()})
    @staticmethod
    def edge_transition(pos: int, edge_label: EdgeLabel, edge_filter: Optional[EdgeFilter]=None) -> 'Glushkov':
        filters: Set[EdgeFilter] = {edge_label}
        if edge_filter is not None:
            filters.add(edge_filter)

        g = Glushkov.void()
        g._add_position(pos, edge_label)
        g._add_first_transition(pos, EdgeTransition(set(), filters, set()))
        g._add_last_transition(pos, NodeTransition())

        return g

    # `A |= B` recognizes the union `L(A|B) = L(A) ∪ L(B)`.
    def __ior__(self, other):
        self._add_all_epsilon_transitions(other)
        self._add_all_positions(other)
        self._add_all_first_transitions(other)
        self._add_all_follow_transitions(other)
        self._add_all_last_transitions(other)

        return self

    # `A *= B` recognizes the concatenation `L(A⋅B) = L(A)⋅L(B)`.
    def __mul__(self, other: 'Glushkov') -> 'Glushkov':
        # epsilon transitions are obtained by composing the epsilon transitions of A and B
        _epsilon = self.epsilon.copy()
        _last = self.last.copy()
        self.epsilon.clear()
        self.last = {pos: set() for pos in self.position}

        # epsilon transitions
        for e1 in _epsilon:
            for e2 in other.epsilon:
                self._add_epsilon_transition(e1 * e2)

        # positions
        self._add_all_positions(other)

        # first transitions
        # combine epsilon transitions of A with the first transitions of B
        for last_pos in other.first:
            for t in other.first[last_pos]:
                for e in _epsilon:
                    self._add_first_transition(last_pos, e * t)

        # follow transitions
        self._add_all_follow_transitions(other)
        # combine last transitions of A with first transitions of B
        for last_pos in _last:
            for e in _last[last_pos]:
                for first_pos in other.first:
                    for t in other.first[first_pos]:
                        self._add_follow_transition(last_pos, first_pos, e * t) # type: ignore

        # last transitions
        self._add_all_last_transitions(other)
        # combine last transitions of A with epsilon transitions of B
        for last_pos in _last:
            for t in _last[last_pos]:
                for e in other.epsilon:
                    self._add_last_transition(last_pos, t * e)

        return self

    # `A.optional()` recognizes `L(A)? = L(A) ∪ L(ε)`.
    def optional(self) -> 'Glushkov':
        self._add_epsilon_transition(NodeTransition())

        return self

    # `A.plus()` recognizes Kleene's plus `L(A)+ = L(A) ∪ L(A)⋅L(A) ∪ L(A)⋅L(A)⋅L(A) ∪ …`.
    def plus(self) -> 'Glushkov':
        # combine last transitions with first transitions
        for last_pos in self.last:
            for first_pos in self.first:
                for last_t in self.last[last_pos]:
                    for first_t in self.first[first_pos]:
                        self._add_follow_transition(last_pos, first_pos, last_t * first_t)

        # Is seems unnecessary to combine first and lasts with epsilons.
        #
        # Thm. For any set of paths L and any set of empty paths E the following holds:
        # >     (L ∪ Ε)+ = L+ ∪ E
        #
        # Proof:
        # * the ⊇ direction is trivial
        # * the ⊆ direction is easily proven by removing of E from the path derivation. □

        return self

    # `A.star()` recognizes Kleene's star `L(A)* = L(A)+ ∪ {ε}`.
    def star(self) -> 'Glushkov':
        return self.plus().optional()
