from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing_extensions import Self
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    TypeVar,
    Union as _Union,
)
import itertools
import datetime as _dt
from ...util.source import SourcePos

from pandas import DataFrame

if TYPE_CHECKING:
    from .metamodel_analyzer import Analysis

#------------------------------------------------------
# Immutable Sequence (ISeq)
#------------------------------------------------------

T = TypeVar("T")
ISeq = tuple[T, ...]

#-----------------------------------------------------------------------------
# ID / Base Node
#-----------------------------------------------------------------------------

_id_counter = itertools.count(1)

def _next_id() -> int:
    return next(_id_counter)

@dataclass(repr=False, frozen=True, slots=True)
class Node():
    id: int = field(default_factory=_next_id, compare=False, hash=False, kw_only=True)
    source: SourcePos|None = field(default=None, compare=False, hash=False, kw_only=True)
    annotations: tuple[Annotation,...] = field(default=(), compare=False, hash=False, kw_only=True)

    def __str__(self) -> str:
        try:
            from .pprint import format
            return format(self)
        except Exception as e:
            print(e)
            return object.__repr__(self)

    __repr__ = __str__

    def mut(self: Self, **changes) -> Self:
        """Convenience to return a modified copy, but keeping the id."""
        changes["id"] = self.id
        return replace(self, **changes)

#-----------------------------------------------------------------------------
# Capabilities, Reasoners
#-----------------------------------------------------------------------------

@dataclass(repr=False, frozen=True, slots=True)
class Capability(Node):
    name: str = ""

@dataclass(repr=False, frozen=True, slots=True)
class Reasoner(Node):
    type: str = ""  # e.g., "SQL", "Logic", "ML", "MathOpt"
    info: Any = None
    capabilities: ISeq[Capability] = field(default=())
    relations: ISeq[Relation] = field(default=())

# -----------------------------------------------------------------------------
# Relation
# -----------------------------------------------------------------------------

@dataclass(repr=False, frozen=True, slots=True)
class Field(Node):
    name: str = ""
    type: Type = field(default_factory=lambda:None) #type: ignore
    input: bool = False  # True if value must be supplied (e.g., parameter/input)
    _relation : Relation = field(default=None, compare=False, hash=False, kw_only=True) #type: ignore

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Field):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

@dataclass(repr=False, frozen=True, slots=True)
class Reading(Node):
    name: str = field(default="")
    # for a reading like "{Foo} has {bar:int} and {baz}",
    # parts would be [0, " has ", 1, " and ", 2]
    parts: ISeq[str|int] = field(default=())

    @property
    def field_order(self) -> list[int]:
        return [p for p in self.parts if isinstance(p, int)]

@dataclass(repr=False, frozen=True, slots=True)
class Overload(Node):
    types: ISeq[Type] = field(default=())

@dataclass(repr=False, frozen=True, slots=True)
class Relation(Node):
    name: str = ""
    fields: ISeq[Field] = field(default=())
    requires: ISeq[Capability] = field(default=())
    readings: ISeq[Reading] = field(default=())
    overloads: ISeq[Overload] = field(default=())

    def __post_init__(self):
        # back-reference fields to this relation
        for f in self.fields:
            object.__setattr__(f, '_relation', self)

    def _dangerous_set_readings(self, readings: ISeq[Reading]) -> None:
        object.__setattr__(self, 'readings', readings)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Relation):
            return False
        return self.id == other.id

@dataclass(repr=False, frozen=True, slots=True)
class UnresolvedRelation(Relation):
    """A placeholder for a relation that could not be resolved during compilation."""
    pass

#------------------------------------------------------
# Annotation
#------------------------------------------------------

@dataclass(repr=False, frozen=True, slots=True)
class Annotation(Node):
    relation: Relation = field(default_factory=Relation)
    args: ISeq[Value] = field(default=())

#-----------------------------------------------------------------------------
# Types
#-----------------------------------------------------------------------------

class TypeNode(Relation):
    """Marker base class for all type nodes."""

    def __post_init__(self):
        if not self.fields:
            object.__setattr__(self, 'fields', (Field(name=self.name, type=self),))
        super().__post_init__()

@dataclass(repr=False, frozen=True, slots=True)
class ScalarType(TypeNode):
    super_types: ISeq[ScalarType] = field(default=())
    identify_by: ISeq[Relation] = field(default=())

    def _force_identify_by(self, identify_by: ISeq[Relation]) -> None:
        object.__setattr__(self, 'identify_by', tuple(identify_by))

    def __hash__(self) -> int:
        return hash(self.id)

@dataclass(repr=False, frozen=True, slots=True)
class NumberType(ScalarType):
    precision: int = 38
    scale: int = 14

    def __hash__(self) -> int:
        return hash(self.id)

@dataclass(repr=False, frozen=True, slots=True)
class UnionType(TypeNode):
    types: ISeq[TypeNode] = field(default=())

    def __hash__(self) -> int:
        return hash(self.id)

@dataclass(repr=False, frozen=True, slots=True)
class ListType(TypeNode):
    element_type: TypeNode = field(default_factory=TypeNode)

    def __hash__(self) -> int:
        return hash(self.id)

@dataclass(repr=False, frozen=True, slots=True)
class TupleType(TypeNode):
    element_types: ISeq[TypeNode] = field(default=())

    def __hash__(self) -> int:
        return hash(self.id)

# Type alias to mirror the spec's union
Type = TypeNode
RelationType = ScalarType(name="Relation")
FieldType = ScalarType(name="Field")
NoneType = ScalarType(name="None")

#------------------------------------------------------
# Table
#------------------------------------------------------

@dataclass(repr=False, frozen=True, slots=True)
class Table(ScalarType):
    columns: ISeq[Relation] = field(default=())
    uri: str = ""

    def __hash__(self) -> int:
        return hash(self.id)

    def _force_columns(self, columns: ISeq[Relation]) -> None:
        object.__setattr__(self, 'columns', tuple(columns))

#------------------------------------------------------
# Data
#------------------------------------------------------

@dataclass(repr=False, frozen=True, slots=True)
class Data(Table):
    """A table of data"""
    data: DataFrame = field(default_factory=lambda: DataFrame([]))
    uri: str = "dataframe://in-memory"

    def __hash__(self) -> int:
        return hash(id(self.data))

# -----------------------------------------------------------------------------
# Values
# -----------------------------------------------------------------------------

Primitive = _Union[str, int, float, bool, _dt.datetime, None]

@dataclass(repr=False, frozen=True, slots=True)
class Var(Node):
    type: Type = field(default_factory=TypeNode)
    name: str = ""

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Var):
            return False
        return self.id == other.id

@dataclass(repr=False, frozen=True, slots=True)
class Literal(Node):
    type: Type = field(default_factory=TypeNode)
    value: Primitive = None


# Value is recursive; allow nested lists of Value
Value = _Union[Var, Literal, Type, Relation, Field, ISeq["Value"], None]

# -----------------------------------------------------------------------------
# Tasks (process algebra)
# -----------------------------------------------------------------------------

@dataclass(repr=False, frozen=True, kw_only=True)
class Task(Node):
    reasoner: Optional[Reasoner] = None

@dataclass(repr=False, frozen=True, slots=True, kw_only=True)
class Container(Task):
    optional:bool = field(default=False)
    scope:bool = field(default=False)

# -----------------------------
# Control Flow
# -----------------------------

@dataclass(repr=False, frozen=True, slots=True)
class Logical(Container):
    body: ISeq[Task] = field(default=())

@dataclass(repr=False, frozen=True, slots=True)
class Sequence(Container):
    tasks: ISeq[Task] = field(default=())

@dataclass(repr=False, frozen=True, slots=True)
class Union(Container):
    tasks: ISeq[Task] = field(default=())

@dataclass(repr=False, frozen=True, slots=True)
class Match(Container):
    tasks: ISeq[Task] = field(default=())

@dataclass(repr=False, frozen=True, slots=True)
class Until(Container):
    check: Task = field(default_factory=Logical)
    body: Task = field(default_factory=Logical)

@dataclass(repr=False, frozen=True, slots=True)
class Wait(Container):
    check: Task = field(default_factory=Logical)

@dataclass(repr=False, frozen=True, slots=True)
class Loop(Container):
    over: ISeq[Var] = field(default=())
    body: Task = field(default_factory=Logical)
    concurrency: int = 1

@dataclass(repr=False, frozen=True, slots=True)
class Break(Task):
    check: Task = field(default_factory=Logical)

# -----------------------------
# Constraints
# -----------------------------

@dataclass(repr=False, frozen=True, slots=True)
class Require(Container):
    domain: Task = field(default_factory=Logical)
    check: Task = field(default_factory=Logical)
    error: Optional[Task] = None

# -----------------------------
# Quantifiers
# -----------------------------

@dataclass(repr=False, frozen=True, slots=True)
class Not(Container):
    task: Task = field(default_factory=Logical)

@dataclass(repr=False, frozen=True, slots=True)
class Exists(Container):
    vars: ISeq[Var] = field(default=())
    task: Task = field(default_factory=Logical)

# -----------------------------
# Relation Ops
# -----------------------------

class Effect(str, Enum):
    derive = "derive"
    insert = "insert"
    delete = "delete"

@dataclass(repr=False, frozen=True, slots=True)
class Lookup(Task):
    relation: Relation = field(default_factory=Relation)
    args: ISeq[Value] = field(default=())
    reading_hint: Optional[Reading] = None

@dataclass(repr=False, frozen=True, slots=True)
class Update(Task):
    relation: Relation = field(default_factory=Relation)
    args: ISeq[Value] = field(default=())
    effect: Effect = Effect.derive
    reading_hint: Optional[Reading] = None

@dataclass(repr=False, frozen=True, slots=True)
class Aggregate(Task):
    aggregation: Relation = field(default_factory=Relation)
    projection: ISeq[Var] = field(default=())
    group: ISeq[Var] = field(default=())
    args: ISeq[Value] = field(default=())
    body: Task = field(default_factory=Logical)

@dataclass(repr=False, frozen=True, slots=True)
class Construct(Task):
    values: ISeq[Value] = field(default=())
    id_var: Var = field(default_factory=Var)


# -----------------------------------------------------------------------------
# Model
# -----------------------------------------------------------------------------

@dataclass(repr=False, frozen=True, slots=True)
class Model(Node):
    reasoners: ISeq[Reasoner] = field(default=())
    relations: ISeq[Relation] = field(default=())
    types: ISeq[Type] = field(default=())
    root: Task = field(default_factory=Logical)
    _analysis: Analysis = None # type: ignore - will be set by Analyzer

# -----------------------------------------------------------------------------
# Public exports
# -----------------------------------------------------------------------------

__all__ = [
    # Base
    "Node",
    # Capabilities / Reasoners
    "Capability",
    "Reasoner",
    # Types
    "TypeNode",
    "ScalarType",
    "NumberType",
    "UnionType",
    "ListType",
    "Type",
    # Relations
    "Field",
    "Reading",
    "Relation",
    "Annotation",
    # Values
    "Primitive",
    "Var",
    "Literal",
    "Value",
    "Var",
    # Tasks
    "Task",
    # Control flow
    "Container",
    "Logical",
    "Sequence",
    "Union",
    "Match",
    "Until",
    "Wait",
    "Loop",
    "Break",
    # Constraints
    "Require",
    # Quantifiers
    "Not",
    "Exists",
    # Relation ops
    "Effect",
    "Lookup",
    "Update",
    "Aggregate",
    "Construct",
    "Data",
    # Model
    "Model",
]
