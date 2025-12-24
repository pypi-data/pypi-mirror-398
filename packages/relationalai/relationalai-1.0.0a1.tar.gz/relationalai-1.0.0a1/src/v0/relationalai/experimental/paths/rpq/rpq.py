from abc import ABC, abstractmethod
import typing
from .glushkov import Glushkov
from .filter import (
    NodeFilter, NodeLabel, AnonymousNodeFilter, EdgeLabel, AnonymousEdgeFilter,
    parse_label
)
from v0.relationalai.semantics import Concept

# =========================================================================================
# Regular Path Queries (RPQs) with local filters
# =========================================================================================
#
# Regular Path Queries with local filters are represented as ASTs defined with this grammar.
#
# expr ::= Node([NodeLabel], [AnonymousNodeFilter])
#        | Edge(EdgeLabel, [AnonymousEdgeFilter])
#        | Concat(expr₁, expr₂)
#        | Union(expr₁, expr₂)
#        | Star(expr)
#        | Plus(expr)
#        | Optional(expr)
#        | Void
#
# Every Edge leaf of an RPQ is automatically assigned a unique position `pos` value i.e.,
# the `Edge` constructor uses a class variable `_id_counter` to generate a fresh value for
# each new instance of `Edge`. The positions are used to provide the user with clear
# feedback (error and warnings) that refers to specific places in the input RPQ.
#
# An important requirement is that an RPQ does not use two Edge leaves with the same
# position.  With a natural use of the RPQ constructors, this requirement is not violated
# unless a subexpression is reused. Consequently, the `clone` method is provided to create a
# copy of an RPQ subexpression with fresh edge positions. For further safety, we ensure that
# no two Edges with the same position are present, by constructing the set of positions of
# an expression. If during the construction of a complex RPQ (`Concat` or `Union`) we find
# repeating positions, we clone one of the expressions to ensure that the positions are
# unique in the whole RPQ.
# =========================================================================================

#------------------------------------------------------------------------------------------
# Auxiliary function for repeating `expr{n:m}` used to implement slicing operator of RPQ
#------------------------------------------------------------------------------------------


#-----------------------------------------------------------------------------
# Parsing RPQ elements specified with strings (node and edge labels).
#-----------------------------------------------------------------------------


class RPQ(ABC):
    _id_counter = 0

    @classmethod
    def next_id(cls) -> int:
        cls._id_counter += 1
        return cls._id_counter

    def __init__(self, positions: typing.FrozenSet[int] = frozenset()):
        self._positions = positions

    @property
    def positions(self) -> typing.FrozenSet[int]:
        return self._positions

    @abstractmethod
    def clone(self) -> 'RPQ':
        pass

    @abstractmethod
    def glushkov(self) -> Glushkov:
        pass

    @abstractmethod
    def pprint(self, ind) -> str:
        pass

    def __str__(self):
        return self.pprint("")

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    def __len__(self) -> int:
        return len(self.positions)

    # expr[n:m]
    def __getitem__(self, key):
        if isinstance(key, int):
            return _repeat(self, key, key)
        elif isinstance(key, slice):
            return _repeat(self, key.start, key.stop)
        else:
            return NotImplemented

    # expr₁ | expr₂
    def __or__(self, other):
        if isinstance(self, Void):
            return other
        elif isinstance(other, Void):
            return self
        else:
            return Union(self, other)

    # expr₁ ⋅ expr₂
    def __mul__(self, other):
        return Concat(self, other)

# ∅
class Void(RPQ):
    def __init__(self):
        super().__init__()

    def clone(self):
        return Void()

    def glushkov(self):
        return Glushkov.void()

    def pprint(self, ind):
        return ind + "⋅ ∅"

    def to_dict(self):
        return {"type": "Void"}

# ε(label {filter})
class Node(RPQ):
    def __init__(self,
                 label: typing.Optional[NodeLabel]=None,
                 filter: typing.Optional[AnonymousNodeFilter]=None):
        super().__init__()
        self.label = label
        self.filter = filter

    def clone(self):
        return Node(self.label, self.filter)

    def glushkov(self):
        filters: typing.List[NodeFilter] = []
        if self.label is not None:
            filters.append(self.label)
        if self.filter is not None:
            filters.append(self.filter)
        return Glushkov.node_transition(*filters)

    def pprint(self, ind):
        res = ind + "⋅ Node("
        if self.label is not None:
            res += f"{self.label}"
        if self.filter is not None:
            res += " {" if self.label is not None else "{"
            res += f"{self.filter}"
            res += "}"
        res += ")"
        return res

    def to_dict(self) -> dict:
        d = {"type": "Node"}
        if self.label is not None:
            d["label"] = self.label.to_dict() # type: ignore
        if self.filter is not None:
            d["filter"] = self.filter.to_dict() # type: ignore
        return d

# -[label {filter}]->
class Edge(RPQ):
    def __init__(self,
                 label: EdgeLabel,
                 filter: typing.Optional[AnonymousEdgeFilter] = None):
        self.pos = self.next_id()
        super().__init__(frozenset([self.pos]))
        self.label = label
        self.filter = filter

    def clone(self):
        return Edge(self.label, self.filter)

    def glushkov(self):
        return Glushkov.edge_transition(self.pos, self.label, self.filter)

    # we avoid using `[...]` which can be mistaken for control sequence by rich-text loggers
    def pprint(self, ind):
        res = ind + "⋅ "
        filter_str = ""
        if self.filter is not None:
            filter_str += f" {{ {self.filter} }}"
        if self.label.direction == "forward":
            res += f"-⟨{self.label.label}{filter_str}⟩→"
        else:
            res += f"←⟨{self.label.label}{filter_str}⟩-"
        res += f" pos={self.pos} "
        return res

    def to_dict(self) -> dict:
        return {
            "type": "Edge",
            "pos": self.pos,
            "label": self.label.to_dict() # type: ignore
        }

# expr₁ ⋅ expr₂
class Concat(RPQ):
    def __init__(self, expr1:RPQ, expr2:RPQ):
        if not expr1.positions.isdisjoint(expr2.positions):
            expr2 = expr2.clone()
        super().__init__(expr1.positions | expr2.positions)
        self.expr1 = expr1
        self.expr2 = expr2

    def clone(self):
        return Concat(self.expr1.clone(), self.expr2.clone())

    def glushkov(self):
        g = self.expr1.glushkov()
        g *= self.expr2.glushkov()
        return g

    def pprint(self, ind):
        res = ind + "⋅ Concat\n"
        res += self.expr1.pprint(ind + "   ") + "\n"
        res += self.expr2.pprint(ind + "   ")
        return res

    def to_dict(self) -> dict:
        return {
            "type": "Concat",
            "expr1": self.expr1.to_dict(), # type: ignore
            "expr2": self.expr2.to_dict()  # type: ignore
        }

# expr ₁ | expr₂
class Union(RPQ):
    def __init__(self, expr1:RPQ, expr2:RPQ):
        if not expr1.positions.isdisjoint(expr2.positions):
            expr2 = expr2.clone()
        super().__init__(expr1.positions | expr2.positions)
        self.expr1 = expr1
        self.expr2 = expr2

    def clone(self):
        return Union(self.expr1.clone(), self.expr2.clone())

    def glushkov(self):
        g = self.expr1.glushkov()
        g |= self.expr2.glushkov()
        return g

    def pprint(self, ind):
        res = ind + "⋅ Union\n"
        res += self.expr1.pprint(ind + "   ") + "\n"
        res += self.expr2.pprint(ind + "   ")
        return res

    def to_dict(self) -> dict:
        return {
            "type": "Union",
            "expr1": self.expr1.to_dict(), # type: ignore
            "expr2": self.expr2.to_dict()  # type: ignore
        }

# expr*
class Star(RPQ):
    def __init__(self, expr:RPQ):
        super().__init__(expr.positions)
        self.expr = expr

    def clone(self):
        return Star(self.expr.clone())

    def glushkov(self):
        return self.expr.glushkov().star()

    def pprint(self, ind):
        return ind + "⋅ Star\n" + self.expr.pprint(ind + '   ')

    def to_dict(self) -> dict:
        return {
            "type": "Star",
            "expr": self.expr.to_dict() # type: ignore
        }

# expr+
class Plus(RPQ):
    def __init__(self, expr:RPQ):
        super().__init__(expr.positions)
        self.expr = expr

    def clone(self):
        return Plus(self.expr.clone())

    def glushkov(self):
        return self.expr.glushkov().plus()

    def pprint(self, ind):
        return ind + "⋅ Plus\n" + self.expr.pprint(ind + '   ')

    def to_dict(self) -> dict:
        return {
            "type": "Plus",
            "expr": self.expr.to_dict() # type: ignore
        }

# expr?
class Optional(RPQ):
    def __init__(self, expr:RPQ):
        super().__init__(expr.positions)
        self.expr = expr

    def clone(self):
        return Optional(self.expr.clone())

    def glushkov(self):
        return self.expr.glushkov().optional()

    def pprint(self, ind):
        return ind + "⋅ Optional\n" + self.expr.pprint(ind + '   ')

    def to_dict(self) -> dict:
        return {
            "type": "Optional",
            "expr": self.expr.to_dict() # type: ignore
        }



# allowed types for segments in RPQ constructors:
Segment = typing.Union[str, Concept, RPQ]


def _process_segment(s: Segment) -> RPQ:

    if isinstance(s, str):
        label = parse_label(s)
        if isinstance(label, NodeLabel):
            return Node(label)
        else:
            return Edge(label)
    elif isinstance(s, Concept):
        return Node(NodeLabel(s._name))
    elif isinstance(s, RPQ):
        return s
    else:
        raise Exception(f"Incorrect type `{type(s)}` of segment `{s}`")


def _repeat(pattern: 'RPQ', n:typing.Union[int,None], m:typing.Union[int,None]) -> 'RPQ':
    n = n if n is not None else 0
    assert n >= 0, f"Negative start range [{n}:{m}]"
    assert (m is None or m >= n), f"Invalid repeat range [{n}:{m}]"
    if m is None:
        if n == 0:
            return Star(pattern)
        elif n == 1:
            return Plus(pattern)
        else:
            result = pattern.clone()
            for _ in range(n-2):
                result = Concat(result, pattern.clone())
            return Concat(result, Plus(pattern))
    else:
        if n == 0:
            if m == 0:
                return Node()
            else:
                result = Optional(pattern)
                for _ in range(m-1):
                    result = Concat(result, Optional(pattern.clone()))
                return result
        else:
            result = pattern
            for _ in range(n-1):
                result = Concat(result, pattern.clone())
            for _ in range(m-n):
                result = Concat(result, Optional(pattern.clone()))
            return result

# Explicitly export RPQ and other relevant classes
__all__ = ["RPQ", "Node", "Edge", "Concat", "Union", "Star"]