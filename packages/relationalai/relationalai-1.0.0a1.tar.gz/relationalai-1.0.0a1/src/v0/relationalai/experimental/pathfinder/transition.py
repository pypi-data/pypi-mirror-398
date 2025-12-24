
from typing import List, FrozenSet, Union, Iterable
from v0.relationalai.experimental.pathfinder.filter import (
    NodeFilter, EdgeFilter, EdgeLabel, AnonymousEdgeFilter
)

# =========================================================================================
# Transitions
# =========================================================================================
#
# Transitions are the building blocks of automata for paths in a labeled knowledge graph.
# There are two types of transitions: node transitions and edge transitions.
#
# * a _node transition_ `-(ψ₁ ∧ … ∧ ψ ₖ)->` does not advance on the path but only asserts
#   the node filters ψ₁,..., ψ ₖ on the current node.
#
# * an _edge transition_ `-(ψ₁ ∧ … ∧ ψₖ)-[φ₁ ∧ … ∧ φₙ]-(ρ₁ ∧ … ρₘ)->` that asserts the
#   source node filters ψ₁, ..., ψₖ on the current node, traverses an edge satisfying the
#   edge filters φ₁, ..., φₙ, and asserts the node filters ρ₁, ..., ρₘ on the arriving node.
#   NOTE: We only use edge transitions that have at least one edge label.
#
# A transition `t` is _trivial_ if it has no filters. A transition is _grounded_ if it
# contains a grounded filter (a label). Note that an edge transition is always grounded
# since it contains at least one edge label filter (that is grounded).
#
# Two transitions t₁ and t₂ can be _composed_ `t₁ * t₂` with the multiplication operator:
# 1. two node transitions can be composed by taking the union of their filters.
# 2. an node transition can be composed with and edge transition on the left or right by
#    adding its filters to the source or destination node filters of the edge transition.
# 3. Two edge-transitions CANNOT be composed!
#
# To ensure rudimentary equality and hashing, the collection of filters are stored as
# immutable frozen sets; A transition once created must not have its filters modified in any
# way.
#
# For the purposes of automata simplification, we define a simulation relation between
# transitions: `t₁ simulates t₂` if any path fragment that matches t₂ also matches t₁.
# =========================================================================================

class NodeTransition:
    def __init__(self, filters: Iterable[NodeFilter] = set()):
        self._filters: FrozenSet = frozenset(filters)

    @property
    def filters(self) -> FrozenSet[NodeFilter]:
        return self._filters

    def is_trivial(self):
        return len(self._filters) == 0

    def is_grounded(self):
        return any(f.is_grounded() for f in self._filters)

    def __repr__(self):
        return f"⊨⸨{' ∧ '.join(map(str, self._filters))}⸩⇒"

    def to_dict(self) -> dict:
        d = {"type": "NodeTransition"}
        if self._filters:
            d["filters"] = [f.to_dict() for f in self._filters] # type: ignore
        return d

    def __eq__(self, other):
        if isinstance(other, NodeTransition):
            return self._filters == other._filters
        else:
            return NotImplemented

    def __hash__(self):
        return hash(self._filters)

    def __mul__(self, other: 'NodeTransition') -> 'NodeTransition':
        if isinstance(other, NodeTransition):
            return NodeTransition(self._filters | other._filters)
        else:
            return NotImplemented

    # if `t₁ simulates t₂`, then any node on a path that matches t₂ also matches t₁
    def simulates(self, other: 'NodeTransition') -> bool:
        if isinstance(other, NodeTransition):
            return self._filters <= other._filters
        else:
            return NotImplemented

class EdgeTransition:
    def __init__(self,
                 src_filters: Iterable[NodeFilter],
                 edge_filters: Iterable[EdgeFilter],
                 trg_filters: Iterable[NodeFilter]):
        assert any(isinstance(f, EdgeLabel) for f in edge_filters), "An edge transition must have at least one edge label"
        self._src_filters: FrozenSet[NodeFilter] = frozenset(src_filters)
        self._edge_filters: FrozenSet[EdgeFilter] = frozenset(edge_filters)
        self._trg_filters: FrozenSet[NodeFilter] = frozenset(trg_filters)

    @property
    def src_filters(self) -> FrozenSet[NodeFilter]:
        return self._src_filters

    @property
    def edge_filters(self) -> FrozenSet[EdgeFilter]:
        return self._edge_filters

    @property
    def trg_filters(self) -> FrozenSet[NodeFilter]:
        return self._trg_filters

    def __repr__(self):
        res = f"⊨⸨{' ∧ '.join(map(str, self._src_filters))}⸩"
        res += f"═⟦{' ∧ '.join(map(str, self._edge_filters))}⟧═"
        res += f"⸨{' ∧ '.join(map(str, self._trg_filters))}⸩⇒"
        return res

    def to_dict(self):
        d = {"type": "EdgeTransition"}
        if self._src_filters:
            d["src_filters"] = [f.to_dict() for f in self._src_filters] # type: ignore
        d["edge_filters"] = [f.to_dict() for f in self._edge_filters]   # type: ignore
        if self._trg_filters:
            d["trg_filters"] = [f.to_dict() for f in self._trg_filters] # type: ignore
        return d

    def has_src_filters(self):
        return len(self._src_filters) > 0

    def has_trg_filters(self):
        return len(self._trg_filters) > 0

    def has_grounded_trg_filters(self):
        return any(f.is_grounded() for f in self._trg_filters)

    def has_grounded_src_filters(self):
        return any(f.is_grounded() for f in self._src_filters)

    def has_anon_edge_filters(self):
        return any(not f.is_grounded() for f in self._edge_filters)

    def get_label(self) -> EdgeLabel:
        for f in self._edge_filters:
            if isinstance(f, EdgeLabel):
                return f
        raise ValueError("No edge label filter in the transition")

    def get_anon_edge_filters(self) -> List[AnonymousEdgeFilter]:
        return [f for f in self._edge_filters if isinstance(f, AnonymousEdgeFilter)]

    def __eq__(self, other):
        if isinstance(other, EdgeTransition):
            return (self._src_filters == other._src_filters and
                    self._edge_filters == other._edge_filters and
                    self._trg_filters == other._trg_filters)
        else:
            return NotImplemented

    # If `t₁ simulates t₂`, then then any edge on a path that matches t₂ also matches t₁.
    def simulates(self, other: 'EdgeTransition') -> bool:
        if isinstance(other, EdgeTransition):
            return (self._src_filters <= other._src_filters and
                    self._edge_filters <= other._edge_filters and
                    self._trg_filters <= other._trg_filters)
        else:
            return NotImplemented

    def __hash__(self):
        return hash((hash(self._src_filters),
                     hash(self._edge_filters),
                     hash(self._trg_filters)))

    def __mul__(self, other: 'NodeTransition') -> 'EdgeTransition':
        if isinstance(other, NodeTransition):
            return EdgeTransition(
                self._src_filters,
                self._edge_filters,
                self._trg_filters | other._filters
            )
        else:
            return NotImplemented

    def __rmul__(self, other: 'NodeTransition') -> 'EdgeTransition':
        if isinstance(other, NodeTransition):
            return EdgeTransition(
                self._src_filters | other._filters,
                self._edge_filters,
                self._trg_filters
            )
        else:
            return NotImplemented

# -----------------------------------------------------------------------------------------
# Function on sets of transitions
# -----------------------------------------------------------------------------------------

# T₁ _simulate_ T₂, if for any t₂ in T₂ there is t₁ in T₁ such that t₁ simulates t₂.
# When T₁ _simulate_ T₂ a path fragment that matches all of T₂ also matches all of T₁.
def simulate(T1: Union[Iterable[EdgeTransition], Iterable[NodeTransition]],
             T2: Union[Iterable[EdgeTransition], Iterable[NodeTransition]]) -> bool:
    return all(any(t1.simulates(t2) for t1 in T1) for t2 in T2) # type: ignore

# Gets the list of all labels from a collection of edge transitions (with repetitions)
def labels(T: Iterable[EdgeTransition]) -> List[EdgeLabel]:
    return [t.get_label() for t in T]
