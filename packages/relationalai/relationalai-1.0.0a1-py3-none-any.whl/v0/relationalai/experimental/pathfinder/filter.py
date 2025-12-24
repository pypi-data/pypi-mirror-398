import re
from abc import ABC, abstractmethod
from v0.relationalai.experimental.pathfinder.utils import get_lambda_str

# =========================================================================================
# Filters, and Labels
# =========================================================================================
#
# Filters are building blocks of Regular Path Queries, in a analogous way to characters used
# in a regular expression.  They specify constraints on nodes and edges on a path.
# Consequently, they are also used in the transitions of automata that correspond to the
# regular path patterns.
#
# Filter expressions are functions that filter nodes and edges of paths:
#
# _Node filter_ `ψ(x)` is a unary function `lambda x: test(x)` that takes a variable bounded
# to a node and expresses assertions about the node.
#
# _Edge filter_ `φ(x, y)` is a binary function `lambda x, y: test(x,y)` that takes two
# variables bound to endpoints of an edge, and expresses assertions about the nodes at the
# endpoints.
#
# Their principal role of filters is to represent PyRel/Rel conditions that capture the
# semantics of the filter. We distinguish two types of filters:
#
# * _Labels_ that specify a label (of a node or edge), and hence can ensure that the
#   corresponding Rel filtering predicate is grounded. Consequently, they are also
#   considered as _grounded filters_.
# * _Anonymous filters_ that are anonymous lambda functions. Even though they may ground the
#   corresponding Rel filtering predicate, it is impossible to verify this statically, and
#   consequently they are not considered as grounded filters.
#
# We work with sets of filters and to avoid duplicates, we introduce rudimentary equality
# and hashing functions. They are precise for labels, but for anonymous filters, they only
# check for pointer equality. Also, we take rudimentary precautions to endure that the data
# structures used to represent filters are treated as immutable.
# =========================================================================================


# -----------------------------------------------------------------------------------------
# Abstract classes for Node and Edge filters
# -----------------------------------------------------------------------------------------
class NodeFilter(ABC):
    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @abstractmethod
    def is_grounded(self) -> bool:
        pass

class EdgeFilter(ABC):
    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @abstractmethod
    def is_grounded(self) -> bool:
        pass

# -----------------------------------------------------------------------------------------
# Edge and Node labels
# -----------------------------------------------------------------------------------------
class NodeLabel(NodeFilter):
    def __init__(self, label: str):
        self._label = label

    @property
    def label(self):
        return self._label

    def __repr__(self) -> str:
        return f'{self.label}'

    def to_dict(self) -> dict:
        return {
            "type": "NodeLabel",
            "label": self.label
        }

    def __eq__(self, other):
        return isinstance(other, NodeLabel) and self.label == other.label

    def __hash__(self):
        return hash(self.label)

    def is_grounded(self) -> bool:
        return True

class EdgeLabel(EdgeFilter):
    def __init__(self, label: str, direction: str):
        self._label = label
        assert direction in ["forward", "backward"], f"Invalid direction: {direction}"
        self._direction = direction

    @property
    def label(self) -> str:
        return self._label

    @property
    def direction(self) -> str:
        return self._direction

    # when printing edge labels we avoid using `[...]` which tend to be interpreted as
    # a control sequence when printing warnings by PyRel
    def __str__(self) -> str:
        if self.direction == "forward":
            return f"-⟨{self.label}⟩→"
        else:
            return f"←⟨{self.label}⟩-"

    def __repr__(self) -> str:
        if self.direction == "forward":
            return f"-[{self.label}]→"
        else:
            return f"←[{self.label}]-"

    def to_dict(self) -> dict:
        return {
            "type": "EdgeLabel",
            "label": self.label,
            "direction": self.direction
        }

    def is_grounded(self) -> bool:
        return True

    def __eq__(self, other):
        if isinstance(other, EdgeLabel):
            return self.label == other.label and self.direction == other.direction
        else:
            return NotImplemented

    def __hash__(self):
        return hash((self.label, self.direction))

REGEX_FORWARD_EDGE = re.compile(r'^-\[([a-zA-Z_][a-zA-Z0-9_]*?)\]->$')
REGEX_BACKWARD_EDGE = re.compile(r'^<-\[([a-zA-Z_][a-zA-Z0-9_]*?)\]-$')
REGEX_NODE = re.compile(r'^([a-zA-Z_][a-zA-Z0-9_]*?)$')

#
# Parses a string specification of a node or edge label:
#
# parse_label('N') = NodeLabel('N')
# parse_label('-[R]->') = EdgeLabel('R', 'forward')
# parse_label('<-[R]-') = EdgeLabel('R', 'backward')
#
def parse_label(lab: str):
    from v0.relationalai.experimental.pathfinder.filter import NodeLabel, EdgeLabel
    match_forward = REGEX_FORWARD_EDGE.search(lab)
    if match_forward:
        return EdgeLabel(match_forward.group(1), 'forward')

    match_backward = REGEX_BACKWARD_EDGE.search(lab)
    if match_backward:
        return EdgeLabel(match_backward.group(1), 'backward')


    match_node = REGEX_NODE.search(lab)
    if match_node:
        return NodeLabel(match_node.group(1))

    raise Exception(f"Couldn't parse label '{lab}'")


# -----------------------------------------------------------------------------------------
# Anonymous node and edge filters
# -----------------------------------------------------------------------------------------
class AnonymousNodeFilter(NodeFilter):
    def __init__(self, unary_function):
        self._unary_function = unary_function

    @property
    def unary_function(self):
        return self._unary_function

    def __call__(self, x):
        return self._unary_function(x)

    def __eq__(self, other):
        if isinstance(other, AnonymousNodeFilter):
            return self._unary_function == other._unary_function
        else:
            return NotImplemented

    def __hash__(self):
        return hash(self._unary_function)

    def __repr__(self) -> str:
        return get_lambda_str(self._unary_function)

    def to_dict(self) -> dict:
        return {
            "type": "AnonymousNodeFilter",
            "function": get_lambda_str(self._unary_function)
        }

    def is_grounded(self) -> bool:
        return False

class AnonymousEdgeFilter(EdgeFilter):
    def __init__(self, binary_function):
        self._binary_function = binary_function

    @property
    def binary_function(self):
        return self._binary_function

    def __call__(self, x, y):
        return self._binary_function(x, y)

    def __eq__(self, other):
        return isinstance(other, AnonymousEdgeFilter) and self._binary_function == other._binary_function

    def __hash__(self):
        return hash(self._binary_function)

    def __repr__(self) -> str:
        return get_lambda_str(self._binary_function)

    def to_dict(self) -> dict:
        return {
            "type": "AnonymousEdgeFilter",
            "function": get_lambda_str(self._binary_function)
        }

    def is_grounded(self) -> bool:
        return False
