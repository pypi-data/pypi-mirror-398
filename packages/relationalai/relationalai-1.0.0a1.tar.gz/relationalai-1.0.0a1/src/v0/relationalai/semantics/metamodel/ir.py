"""
    Intermediate Representation of RelationalAI programs.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from io import StringIO
from itertools import count

from pandas import DataFrame
from more_itertools import peekable
from typing import Any, Iterator, Optional, Tuple, TypeVar, Union as PyUnion, IO, Iterable
from copy import copy
from itertools import islice
from datetime import datetime, date
from decimal import Decimal as PyDecimal
import numpy as np

from .util import FrozenOrderedSet, Printer as BasePrinter, NameCache

import json
import re

#--------------------------------------------------
# IR Nodes
#--------------------------------------------------

_global_id = peekable(count(0))
def next_id():
    return next(_global_id)

def reconstructor(cls):
    """
    A decorator that adds a `reconstruct` method to the class.
    The method reconstructs the object with new values for its fields.
    The `reconstruct` method can take either positional arguments in field order
    (excluding the `id` field) or keyword arguments for specific fields.
    For positional arguments, fields of superclasses precede fields of subclasses.
    If there is no difference between the current values of the fields and the new values,
    `self` is returned, otherwise the object is copied and modified.
    Note that the `id` field is not updated, unlike when creating a new node.
    """
    # Get the names of all fields from the class, except "id".
    fnames = [fname for fname in cls.__dataclass_fields__ if fname != "id"]

    # Add reconstruct method that can handle both positional and keyword arguments
    def reconstruct(self, *args, **kwargs):
        """
        Reconstruct the object with new values for its fields.

        Can be called in two ways:
        1. With positional arguments in the same order as the fields in the class
        2. With keyword arguments for specific fields to update

        It is an error to provide both positional and keyword arguments.
        Returns self if no changes are needed, otherwise returns a new instance.
        """
        # Validate arguments
        if args and kwargs:
            raise ValueError("Cannot provide both positional and keyword arguments")

        # Handle positional arguments
        if args:
            if len(args) != len(fnames):
                raise ValueError(f"Expected {len(fnames)} positional arguments, got {len(args)}")

            # Check if any values differ from current values
            has_changes = False
            for fname, value in zip(fnames, args):
                if getattr(self, fname) is not value:
                    has_changes = True
                    break

            if not has_changes:
                return self

            # Create a new instance with updated values
            new_obj = copy(self)
            for fname, value in zip(fnames, args):
                object.__setattr__(new_obj, fname, value)

            return new_obj

        # Handle keyword arguments
        else:
            # Check if any values differ from current values
            has_changes = False
            for fname, value in kwargs.items():
                if fname not in fnames:
                    raise ValueError(f"Field '{fname}' is not a valid field for this object")
                if getattr(self, fname) is not value:
                    has_changes = True
                    break

            if not has_changes:
                return self

            # Create a new instance with updated values
            new_obj = copy(self)
            for fname, value in kwargs.items():
                if fname in fnames:
                    object.__setattr__(new_obj, fname, value)

            return new_obj

    setattr(cls, "reconstruct", reconstruct)

    # Also add a clone method that will recreate the node with the same data but with a
    # new, distinct node id.
    def clone(self):
        """
        Reconstruct a node with the same values, but it will get a new id.
        """
        args = []
        for fname in fnames:
            args.append(getattr(self, fname))
        return self.__class__(*args)

    setattr(cls, "clone", clone)

    return cls

def acceptor(cls):
    """
    A decorator that adds an `accept` method to the class.
    The `accept` method calls the appropriate handler method
    of a Dispatcher.

    Using a decorator here allows us to compute the handler name once
    for the class rather than each time we dispatch.
    """
    attr_name = f"visit_{cls.__name__.lower()}"
    def accept(self, v, parent=None):
        return getattr(v, attr_name)(self, parent)
    cls.accept = accept
    return cls

def annotations_field() -> FrozenOrderedSet[Annotation]:
    return field(default_factory=lambda: FrozenOrderedSet([]), compare=False, hash=False)

@dataclass(frozen=True)
class Node:
    # A generated id that is not used on comparisons and hashes
    id: int = field(default_factory=next_id, init=False, compare=False, hash=False)

    @property
    def kind(self):
        return self.__class__.__name__.lower()

    def __str__(self):
        return node_to_string(self)

    def accept(self, v, parent=None):
        raise NotImplementedError(f"accept not implemented for {self.kind}")

    def reconstruct(self, *args, **kwargs):
        raise NotImplementedError(f"reconstruct not implemented for {self.kind}")

    def clone(self, *args):
        raise NotImplementedError(f"clone not implemented for {self.kind}")


#-------------------------------------------------
# Public Types - Model
#-------------------------------------------------

@acceptor
@reconstructor
@dataclass(frozen=True)
class Model(Node):
    """Represents the whole universe of elements that make up a program."""
    engines: FrozenOrderedSet["Engine"]
    relations: FrozenOrderedSet["Relation"]
    types: FrozenOrderedSet["Type"]
    root: Task
    annotations:FrozenOrderedSet[Annotation] = annotations_field()


#-------------------------------------------------
# Public Types - Engine
#-------------------------------------------------

@acceptor
@reconstructor
@dataclass(frozen=True)
class Capability(Node):
    """Engine capabilities, such as 'graph algorithms', 'solver', 'constant time count', etc"""
    name: str

@acceptor
@reconstructor
@dataclass(frozen=True)
class Engine(Node):
    """The entity that owns a Task and provides access to certain relations."""
    name: str
    platform: str # SQL, Rel, JS, OpenAI, etc
    info: Any
    capabilities: FrozenOrderedSet[Capability]
    relations: FrozenOrderedSet["Relation"]
    annotations:FrozenOrderedSet[Annotation] = annotations_field()


#-------------------------------------------------
# Public Types - Data Model
#-------------------------------------------------

@acceptor
@reconstructor
@dataclass(frozen=True)
class Type(Node):
    """The type of a field in a relation."""
    pass

@acceptor
@dataclass(frozen=True)
class ScalarType(Type):
    """The named type."""
    name: str
    super_types: FrozenOrderedSet[ScalarType] = field(default_factory=lambda: FrozenOrderedSet([]))
    annotations:FrozenOrderedSet[Annotation] = annotations_field()

    def __eq__(self, other):
        return isinstance(other, ScalarType) and other.id == self.id

    def __hash__(self):
        return hash(self.id)

@acceptor
@dataclass(frozen=True)
class DecimalType(ScalarType):
    precision: int = 38
    scale: int = 14

    def __eq__(self, other):
        # note that we are not checking the name, only precision and scale
        return isinstance(other, DecimalType) and other.precision == self.precision and other.scale == self.scale


@acceptor
@reconstructor
@dataclass(frozen=True)
class ListType(Type):
    """A type that represents a list of elements of some other type."""
    element_type: Type

@acceptor
@reconstructor
@dataclass(frozen=True)
class UnionType(Type):
    """A type that represents either one of a set of types."""
    types: FrozenOrderedSet[Type]

    def __eq__(self, other):
        return isinstance(other, UnionType) and len(self.types) == len(other.types) and self.types.includes(other.types)

@acceptor
@dataclass(frozen=True)
class TupleType(Type):
    """A type that represents a tuple of elements of some other types."""
    types: Tuple[Type, ...]

@acceptor
@reconstructor
@dataclass(frozen=True)
class Field(Node):
    """A named field in a relation."""
    name: str
    type: Type
    input: bool # must be grounded as the relation cannot compute it

    def __eq__(self, other):
        return isinstance(other, Field) and other.id == self.id

    def __hash__(self):
        return hash(self.id)


@acceptor
@reconstructor
@dataclass(frozen=True)
class Relation(Node):
    """A relation represents the schema of a set of tuples."""
    name: str
    fields: Tuple[Field, ...]
    requires: FrozenOrderedSet[Capability]
    annotations:FrozenOrderedSet[Annotation] = annotations_field()
    overloads: FrozenOrderedSet[Relation] = field(default_factory=lambda: FrozenOrderedSet([]))

    def __eq__(self, other):
        return isinstance(other, Relation) and other.id == self.id

    def __hash__(self):
        return hash(self.id)


#-------------------------------------------------
# Public Types - Tasks
#-------------------------------------------------

@acceptor
@reconstructor
@dataclass(frozen=True)
class Task(Node):
    engine: Optional[Engine]

#
# Task composition
#

@acceptor
@reconstructor
@dataclass(frozen=True)
class Logical(Task):
    """Execute sub-tasks up to fix-point."""
    # Executes tasks concurrently. Succeeds if every task succeeds.
    hoisted: Tuple[VarOrDefault, ...]
    body: Tuple[Task, ...]
    annotations:FrozenOrderedSet[Annotation] = annotations_field()

@acceptor
@reconstructor
@dataclass(frozen=True)
class Union(Task):
    """Execute sub-tasks in any order."""
    # Executes tasks concurrently. Succeeds if at least one task succeeds.
    hoisted: Tuple[VarOrDefault, ...]
    tasks: Tuple[Task, ...]
    annotations:FrozenOrderedSet[Annotation] = annotations_field()

@acceptor
@reconstructor
@dataclass(frozen=True)
class Sequence(Task):
    """Execute sub-tasks one at a time, in this order."""
    # Executes tasks in order. Stops when a task fails. Succeeds if all tasks succeed.
    hoisted: Tuple[VarOrDefault, ...]
    tasks: Tuple[Task, ...]
    annotations:FrozenOrderedSet[Annotation] = annotations_field()

@acceptor
@reconstructor
@dataclass(frozen=True)
class Match(Task):
    """Execute sub-tasks in order until the first succeeds."""
    # Executes tasks in order. Stops when a task succeeds. Succeeds if some task succeeds.
    hoisted: Tuple[VarOrDefault, ...]
    tasks: Tuple[Task, ...]
    annotations:FrozenOrderedSet[Annotation] = annotations_field()

@acceptor
@reconstructor
@dataclass(frozen=True)
class Check(Node):
    check: Task
    error: Optional[Task]
    annotations:FrozenOrderedSet[Annotation] = annotations_field()

@acceptor
@reconstructor
@dataclass(frozen=True)
class Require(Task):
    """Execute the domain task and verify the checks. If a check is not satisfied, execute its error task."""
    domain: Task
    checks: Tuple[Check, ...]
    annotations:FrozenOrderedSet[Annotation] = annotations_field()

@acceptor
@reconstructor
@dataclass(frozen=True)
class Until(Task):
    """Execute both `check` and `body` concurrently, until check succeeds."""
    hoisted: Tuple[VarOrDefault, ...]
    check: Task
    body: Task
    annotations:FrozenOrderedSet[Annotation] = annotations_field()

@acceptor
@reconstructor
@dataclass(frozen=True)
class Wait(Task):
    hoisted: Tuple[VarOrDefault, ...]
    check: Task
    annotations:FrozenOrderedSet[Annotation] = annotations_field()

# TODO: DynamicLookup


#
# Logical Quantifiers
#

@acceptor
@reconstructor
@dataclass(frozen=True)
class Not(Task):
    """Logical negation of the sub-task."""
    task: Task
    annotations:FrozenOrderedSet[Annotation] = annotations_field()

@acceptor
@reconstructor
@dataclass(frozen=True)
class Exists(Task):
    """Existential quantification over the sub-task."""
    vars: Tuple[Var, ...]
    task: Task
    annotations:FrozenOrderedSet[Annotation] = annotations_field()

@acceptor
@reconstructor
@dataclass(frozen=True)
class ForAll(Task):
    """Universal quantification over the sub-task."""
    vars: Tuple[Var, ...]
    task: Task
    annotations:FrozenOrderedSet[Annotation] = annotations_field()

#
# Iteration (Loops)
#

# loops body until a break condition is met
@acceptor
@reconstructor
@dataclass(frozen=True)
class Loop(Task):
    """Execute the body in a loop, incrementing the iter variable, until a break sub-task in
    the body succeeds."""
    hoisted: Tuple[VarOrDefault, ...]
    iter: Var
    body: Task
    annotations:FrozenOrderedSet[Annotation] = annotations_field()

@acceptor
@reconstructor
@dataclass(frozen=True)
class Break(Task):
    """Break a surrounding Loop if the `check` succeeds."""
    check: Task
    annotations:FrozenOrderedSet[Annotation] = annotations_field()


#
# Relational Operations
#

@acceptor
@reconstructor
@dataclass(frozen=True)
class Var(Node):
    """A named variable that can point to objects of this type."""
    type: Type
    name: str

    def __eq__(self, other):
        return isinstance(other, Var) and other.id == self.id

    def __hash__(self):
        return hash(self.id)


@acceptor
@reconstructor
@dataclass(frozen=True)
class Default(Node):
    """A variable with a default value. This can be used in 'hoisted' attributes to
    represent the value to assign a variable if the underlying task fails."""
    var: Var
    value: Value

VarOrDefault = PyUnion[Var, Default]

@acceptor
@reconstructor
@dataclass(frozen=True)
class Literal(Node):
    """A literal value with a specific type."""
    type: Type
    value: Any

@acceptor
@reconstructor
@dataclass(frozen=True)
class Data(Task):
    """A table of data"""
    data: DataFrame
    vars: tuple[Var, ...]

    def __eq__(self, other):
        return (
            isinstance(other, Data)
            and self.data is other.data
            and self.vars == other.vars
        )

    def __hash__(self):
        # Use id() to get the reference of the DataFrame
        data_ref_hash = hash(id(self.data))
        vars_hash = hash(self.vars)
        return data_ref_hash ^ vars_hash

    def __len__(self):
        return len(self.data)

    def __iter__(self) -> Iterator[tuple[Any, ...]]:
        return iter(self.data.itertuples(index=True))

PyValue = PyUnion[str, int, float, PyDecimal, bool, date, datetime]
Value = PyUnion[Var, Default, Literal, Type, Relation, None, Tuple["Value", ...], FrozenOrderedSet["Value"]]

@acceptor
@reconstructor
@dataclass(frozen=True)
class Annotation(Node):
    """Meta information that can be attached to Updates."""
    relation: Relation
    args: Tuple[Value, ...]

class Effect(Enum):
    """Possible effects of an Update."""
    derive = "derive"
    insert = "insert"
    delete = "delete"

@acceptor
@reconstructor
@dataclass(frozen=True)
class Update(Task):
    """Updates the relation with these arguments. The update can derive new tuples
    temporarily, can insert new tuples persistently, or delete previously persisted tuples."""
    relation: Relation
    args: Tuple[Value, ...]
    effect: Effect
    annotations:FrozenOrderedSet[Annotation] = annotations_field()

@acceptor
@reconstructor
@dataclass(frozen=True)
class Lookup(Task):
    """Lookup tuples from this relation, filtering with these arguments."""
    relation: Relation
    args: Tuple[Value, ...]
    annotations:FrozenOrderedSet[Annotation] = annotations_field()

@acceptor
@reconstructor
@dataclass(frozen=True)
class Output(Task):
    """Output the value of these vars, giving them these column names."""
    aliases: FrozenOrderedSet[Tuple[str, Value]]
    keys: Optional[FrozenOrderedSet[Var]]
    annotations:FrozenOrderedSet[Annotation] = annotations_field()

@acceptor
@reconstructor
@dataclass(frozen=True)
class Construct(Task):
    """Construct an id from these values, and bind the id to this var."""
    values: Tuple[Value, ...]
    id_var: Var
    annotations:FrozenOrderedSet[Annotation] = annotations_field()

@acceptor
@reconstructor
@dataclass(frozen=True)
class Aggregate(Task):
    """Perform an aggregation with these arguments."""
    aggregation: Relation
    projection: Tuple[Var, ...]
    group: Tuple[Var, ...]
    args: Tuple[Value, ...]
    annotations:FrozenOrderedSet[Annotation] = annotations_field()

@acceptor
@reconstructor
@dataclass(frozen=True)
class Rank(Task):
    """Perform a rank with these arguments."""
    projection: Tuple[Var, ...]
    group: Tuple[Var, ...]
    args: Tuple[Var, ...]
    # True if the argument is ascending, False if descending
    arg_is_ascending: Tuple[bool, ...]
    result: Var
    limit: int = 0
    annotations:FrozenOrderedSet[Annotation] = annotations_field()


#--------------------------------------------------
# Name helpers
#--------------------------------------------------

# TODO - extract the printer from here, and then use the method from helpers
def sanitize(name:str) -> str:
    """ Cleanup the name to make it more palatable to names. """
    x = re.sub(r"[ ,\.\(\)\|]", "_", name)
    return x[0:-1] if x[-1] == "_" else x

#--------------------------------------------------
# Printer
#--------------------------------------------------

infix = ["+", "-", "*", "/", "%", "=", "!=", "<", "<=", ">", ">="]

T = TypeVar('T', bound=Node)
def node_to_string(node:Node|Tuple[T, ...]|FrozenOrderedSet[T], print_ids=False) -> str:
    io = StringIO()
    printer = Printer(io)
    printer.pprint(node, print_ids=print_ids)
    return io.getvalue()

def value_to_string(value:PyUnion[Value, Tuple[Value, ...]]) -> str:
    return Printer().value_to_string(value)

def type_to_string(t:Type) -> str:
    return value_to_string(t).strip()

def types_to_string(ts: Iterable[Type]) -> str:
    """Join a collection of types with commas."""
    return ', '.join(type_to_string(t) for t in ts)

@dataclass(frozen=True)
class Printer(BasePrinter):
    name_cache: NameCache = field(default_factory=NameCache)

    def print_hoisted(self, depth, name, hoisted: Tuple[VarOrDefault, ...]):
        if hoisted:
            self._indent_print_nl(depth, f"{name} ⇑[{', '.join([self.value_to_string(h) for h in hoisted])}]")
        else:
            self._indent_print_nl(depth, name)

    def value_to_string(self, value:PyUnion[PyValue, Value, Tuple[Value, ...]]) -> str:
        """ Return a string representation of the value. """
        if isinstance(value, (int, float, bool)):
            return json.dumps(value)
        if isinstance(value, str):
            return f"\"{value}\""
        if isinstance(value, PyDecimal):
            return str(value)
        if isinstance(value, (date, datetime)):
            return json.dumps(value.isoformat())
        elif value is None:
            return "None"
        elif isinstance(value, Var):
            return f"{self.name_cache.get_name(value.id, sanitize(value.name))}::{self.value_to_string(value.type)}"
        elif isinstance(value, Default):
            return f"{self.name_cache.get_name(value.var.id, sanitize(value.var.name))}={value.value}"
        elif isinstance(value, Literal):
            return f"{self.value_to_string(value.value)}::{self.value_to_string(value.type)}"
        elif isinstance(value, ListType):
            return f"[{self.value_to_string(value.element_type)}]"
        elif isinstance(value, UnionType):
            return f"{{{'; '.join(map(self.value_to_string, value.types))}}}"
        elif isinstance(value, TupleType):
            return f"({', '.join(map(self.value_to_string, value.types))})"
        elif isinstance(value, DecimalType):
            return f"Decimal({value.precision},{value.scale})"
        elif isinstance(value, ScalarType):
            annos_str = "" if not value.annotations else f" {' '.join(f'@{a.relation.name}' for a in value.annotations)}"
            return f"{value.name}{annos_str}"
        elif isinstance(value, Relation):
            return value.name
        elif isinstance(value, Tuple):
            return f"({', '.join(map(self.value_to_string, value))})"
        elif isinstance(value, FrozenOrderedSet):
            return f"{{{', '.join(map(self.value_to_string, value))}}}"
        elif isinstance(value, DataFrame):
            length = len(value)
            vals = islice(value, min(length, 3))
            vals_str = ", ".join([f"({', '.join(map(self.value_to_string, v))})" for v in vals]) # type: ignore
            if length > 3:
                vals_str += f", ... ({length} total)"
            final_str = f"{{{vals_str}}}"
            return final_str
        else:
            raise NotImplementedError(f"value_to_string not implemented for {type(value)}")

    T = TypeVar('T', bound=Node)
    def pprint(self, node:Node|Tuple[T, ...]|FrozenOrderedSet[T], depth=0, print_ids=False) -> None:
        """ Pretty print the node into the io, starting with indentation based on depth. If io is None,
        print into the standard output. """

        if print_ids and not (isinstance(node, Tuple) or isinstance(node, FrozenOrderedSet)):
            self._print(f"|{node.id}|")

        # deal with annotations more generically
        annos = getattr(node, "annotations", [])
        annos_str = "" if not annos else f" {' '.join(f'@{a.relation.name}' for a in annos)}"

        if isinstance(node, Tuple) or isinstance(node, FrozenOrderedSet):
            for n in node:
                self.pprint(n, depth, print_ids=print_ids)
        # model
        elif isinstance(node, Model):
            self._indent_print_nl(depth, f"Model{annos_str}")
            if len(node.engines) > 0:
                self._indent_print_nl(depth + 1, "engines:")
            self.pprint(node.engines, depth + 2, print_ids=print_ids)
            if len(node.relations) > 0:
                self._indent_print_nl(depth + 1, "relations:")
            self.pprint(node.relations, depth + 2, print_ids=print_ids)
            if len(node.types) > 0:
                self._indent_print_nl(depth + 1, "types:")
            self.pprint(node.types, depth + 2, print_ids=print_ids)
            self._indent_print_nl(depth + 1, "root:")
            self.pprint(node.root, depth + 2, print_ids=print_ids)

        # engine
        elif isinstance(node, Capability):
            self._indent_print_nl(depth, node.name)
        elif isinstance(node, Engine):
            self._indent_print_nl(depth, f"Engine ({node.name}, {node.platform}){annos_str}")
            self._indent_print_nl(depth + 1, node.info)
            self._indent_print_nl(depth + 1, ', '.join([c.name for c in node.capabilities]))
            self.pprint(node.relations, depth + 1, print_ids=print_ids)

        # data model
        elif isinstance(node, Type):
            self._indent_print_nl(depth, self.value_to_string(node))
        elif isinstance(node, Field):
            s = f"{node.name}: {self.value_to_string(node.type)}{' (input)' if node.input else ''}"
            self._indent_print_nl(depth, s)
        elif isinstance(node, Relation):
            self._indent_print_nl(depth, node.name)
            for anno in annos:
                self._indent_print(depth + 1, anno)
            self.pprint(node.fields, depth + 1, print_ids=print_ids)
            if len(node.requires) > 0:
                self._indent_print_nl(depth + 1, "requires:")
                self.pprint(node.requires, depth + 2, print_ids=print_ids)

        # tasks

        # Task composition
        elif isinstance(node, Logical):
            self.print_hoisted(depth, f"Logical{annos_str}", node.hoisted)
            self.pprint(node.body, depth + 1, print_ids=print_ids)
        elif isinstance(node, Sequence):
            self.print_hoisted(depth, f"Sequence{annos_str}", node.hoisted)
            self.pprint(node.tasks, depth + 1, print_ids=print_ids)
        elif isinstance(node, Union):
            self.print_hoisted(depth, f"Union{annos_str}", node.hoisted)
            self.pprint(node.tasks, depth + 1, print_ids=print_ids)
        elif isinstance(node, Match):
            self.print_hoisted(depth, f"Match{annos_str}", node.hoisted)
            self.pprint(node.tasks, depth + 1, print_ids=print_ids)
        elif isinstance(node, Until):
            self.print_hoisted(depth, f"Until{annos_str}", node.hoisted)
            self.pprint(node.check, depth + 1, print_ids=print_ids)
            self.pprint(node.body, depth + 1, print_ids=print_ids)
        elif isinstance(node, Wait):
            self.print_hoisted(depth, f"Match{annos_str}", node.hoisted)
            self.pprint(node.check, depth + 1, print_ids=print_ids)
        elif isinstance(node, Require):
            self._indent_print_nl(depth, f"Require{annos_str}")
            self._indent_print_nl(depth + 1, "domain: ")
            self.pprint(node.domain, depth + 2, print_ids=print_ids)
            self._indent_print_nl(depth + 1, "checks: ")
            for check in node.checks:
                self.pprint(check, depth + 2, print_ids=print_ids)
        elif isinstance(node, Check):
            self._indent_print_nl(depth, f"Check{annos_str}")
            self._indent_print_nl(depth + 1, "check: ")
            self.pprint(node.check, depth + 2, print_ids=print_ids)
            self._indent_print_nl(depth + 1, "error: ")
            if node.error:
                self.pprint(node.error, depth + 2, print_ids=print_ids)
            else:
                self._indent_print_nl(depth + 2, "None")

        # Relational Operations
        elif isinstance(node, Var):
            self._indent_print_nl(0, self.value_to_string(node))
        elif isinstance(node, Default):
            self._indent_print_nl(depth, f"{self.value_to_string(node.var)} (default: {self.value_to_string(node.value)})")
        elif isinstance(node, Literal):
            self._indent_print_nl(0, self.value_to_string(node))
        elif isinstance(node, Annotation):
            if node.args:
                self._indent_print_nl(depth, f"@{node.relation.name}{self.value_to_string(node.args)}")
            else:
                self._indent_print_nl(depth, f"@{node.relation.name}")
        elif isinstance(node, Update):
            rel_name = node.relation.name
            self._indent_print_nl(depth, f"→ {node.effect.value} {rel_name}{self.value_to_string(node.args)}{annos_str}")
        elif isinstance(node, Lookup):
            rel_name = node.relation.name
            if rel_name in infix:
                args = [self.value_to_string(arg) for arg in node.args]
                if len(node.args) == 2:
                    self._indent_print_nl(depth, f"{args[0]} {rel_name} {args[1]}{annos_str}")
                elif len(node.args) == 1:
                    self._indent_print_nl(depth, f"{rel_name}{args[0]}{annos_str}")
                elif len(node.args) == 3:
                    self._indent_print_nl(depth, f"{args[2]} = {args[0]} {rel_name} {args[1]}{annos_str}")
            else:
                self._indent_print_nl(depth, f"{rel_name}{self.value_to_string(node.args)}{annos_str}")
        elif isinstance(node, Output):
            keys = []
            if node.keys:
                for k in node.keys:
                    keys.append(self.value_to_string(k))
            args = []
            for k, v in node.aliases:
                ppv = self.value_to_string(v)
                if k != ppv:
                    args.append(f"{ppv} as '{k}'")
                else:
                    args.append(ppv)
            keys_str = f"[{', '.join(keys)}]" if keys else ""
            self._indent_print_nl(depth, f"→ output{keys_str}({', '.join(args)}){annos_str}")
        elif isinstance(node, Construct):
            values = [self.value_to_string(v) for v in node.values]
            self._indent_print_nl(depth, f"construct({', '.join(values)}, {self.value_to_string(node.id_var)}){annos_str}")
        elif isinstance(node, Aggregate):
            projection = ", ".join([self.value_to_string(v) for v in node.projection])
            group = ", ".join([self.value_to_string(v) for v in node.group])
            args = ", ".join([self.value_to_string(v) for v in node.args])
            self._indent_print_nl(depth, f"{node.aggregation.name}([{projection}], [{group}], [{args}]){annos_str}")
        elif isinstance(node, Rank):
            def str_rank_var(v, o):
                up, down = "'↑'", "'↓'"
                return f"{self.value_to_string(v)}{up if o else down}"
            projection = ", ".join([self.value_to_string(v) for v in node.projection])
            group = ", ".join([self.value_to_string(v) for v in node.group])
            assert len(node.args) == len(node.arg_is_ascending)
            args = ", ".join([str_rank_var(v, o) for v, o in zip(node.args, node.arg_is_ascending)])
            result = self.value_to_string(node.result)
            limit = f"[limit={node.limit}]" if node.limit != 0 else ""
            self._indent_print_nl(depth, f"rank{limit}([{projection}], [{group}], [{args}], {result}){annos_str}")
        elif isinstance(node, Data):
            length = len(node)
            vals = islice(node, min(length, 3))
            def unwrap_val(v):
                if isinstance(v, (np.integer, np.floating)):
                    # convert DataFrame number types to native Python types
                    v = v.item()
                return self.value_to_string(v)
            vals_str = ", ".join([f"({', '.join(map(unwrap_val, v))})" for v in vals])
            if length > 3:
                vals_str += f", ... ({length} total)"
            vars_str = ", ".join([self.value_to_string(v) for v in node.vars])
            final_str = f"{{{vals_str}}}({vars_str})"
            self._indent_print_nl(depth, final_str)

        # Logical Quantifiers
        elif isinstance(node, Not):
            self._indent_print_nl(depth, f"Not{annos_str}")
            self.pprint(node.task, depth + 1, print_ids=print_ids)
        elif isinstance(node, Exists):
            self._indent_print_nl(depth, f"Exists({', '.join([self.value_to_string(v) for v in node.vars])}){annos_str}")
            self.pprint(node.task, depth + 1, print_ids=print_ids)
        elif isinstance(node, ForAll):
            self._indent_print_nl(depth, f"ForAll({', '.join([self.value_to_string(v) for v in node.vars])}){annos_str}")
            self.pprint(node.task, depth + 1, print_ids=print_ids)

        # Iteration (Loops)
        elif isinstance(node, Loop):
            self.print_hoisted(depth, f"Loop ⇓[{self.value_to_string(node.iter)}]{annos_str}", node.hoisted)
            self.pprint(node.body, depth + 1, print_ids=print_ids)

        elif isinstance(node, Break):
            self._indent_print_nl(depth, f"Break{annos_str}")
            self.pprint(node.check, depth + 1, print_ids=print_ids)

        elif isinstance(node, Task):
            self._indent_print_nl(depth, "Success")

        else:
            # return
            raise NotImplementedError(f"pprint not implemented for {type(node)}")

def dump_to_string(node: Node|Tuple[T, ...]|FrozenOrderedSet[T], depth=0, io: Optional[IO[str]] = None) -> str:
    """Dump a node to a string."""
    output = StringIO()
    dump(node, depth, output)
    return output.getvalue()


def dump(node: Node|Tuple[T, ...]|FrozenOrderedSet[T], depth=0, io: Optional[IO[str]] = None) -> None:
    """Print complete IR information, including node IDs and all fields."""

    def indent_print(depth, io: Optional[IO[str]], *args) -> None:
        """ Helper to print the arguments into the io with indented based on depth. """
        if io is None:
            print("    " * depth + " ".join(map(str, args)))
        else:
            io.write("    " * depth + " ".join(map(str, args)) + "\n")

    def print_node_header(n: Node, depth: int):
        indent_print(depth, io, f"{n.__class__.__name__} (id={n.id})")

    if isinstance(node, (Tuple, FrozenOrderedSet)):
        for n in node:
            if isinstance(n, Tuple) and len(n) == 2 and isinstance(n[0], str) and isinstance(n[1], Node):
                indent_print(depth, io, f"{n[0]}:")
                dump(n[1], depth + 1, io)
            elif isinstance(n, (Node, Tuple, FrozenOrderedSet)):
                dump(n, depth, io)
            else:
                indent_print(depth, io, f"{value_to_string(n)}")
        return

    if not isinstance(node, Node):
        raise TypeError(f"Expected Node but got {type(node)}")

    print_node_header(node, depth)

    # Print all fields of the dataclass
    for field_name, field_value in node.__dict__.items():
        if field_name == 'id':  # Already printed in header
            continue

        assert not isinstance(field_value, list), f"{node.__class__.__name__}.{field_name} is a {type(field_value)}"
        assert not isinstance(field_value, set), f"{node.__class__.__name__}.{field_name} is a {type(field_value)}"

        if isinstance(field_value, (Node, Tuple, FrozenOrderedSet)) and not isinstance(field_value, Type):
            indent_print(depth + 1, io, f"{field_name}:")
            dump(field_value, depth + 2, io)
        elif isinstance(field_value, Effect):
            indent_print(depth + 1, io, f"{field_name}: {field_value.value}")
        else:
            indent_print(depth + 1, io, f"{field_name}: {value_to_string(field_value)}")
