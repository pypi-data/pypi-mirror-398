"""Base frontend classes for RelationalAI semantics API.
"""
from __future__ import annotations

import decimal
import math
import re
import datetime as dt
from typing import TYPE_CHECKING, Any, Generic, Iterable, Iterator, NoReturn, Optional, Sequence, Tuple, Type, TypeGuard, TypeVar, cast
import itertools
from more_itertools import peekable
from pandas import DataFrame
import pandas as pd
from enum import Enum, EnumMeta

from ...util import schema as schema_util
from ...util.structures import KeyedSet
from ...util.naming import Namer, sanitize
from ...util.python import pytype_to_concept_name
from ...util.source import SourcePos
from ...util.tracing import get_tracer
from ...util.error import err, exc, warn, source
from ...util.docutils import include_in_docs
from ..metamodel.builtins import builtins
from ..metamodel.metamodel import Model as mModel

tracer = get_tracer()
tracer.start_program()

#------------------------------------------------------
# Global ID Generator
#------------------------------------------------------

_global_id = peekable(itertools.count(0))

#------------------------------------------------------
# Helpers
#------------------------------------------------------

def _find_field(fields: list[Field], field: str|int|Concept) -> tuple[Field, int]|None:
    resolved = None
    if isinstance(field, int):
        if not (0 <= field < len(fields)):
            raise IndexError(f"Field index {field} out of range for relationship with {len(fields)} fields")
        resolved = fields[field]
    elif isinstance(field, str):
        resolved = next((f for f in fields if f.name == field), None)
    elif isinstance(field, Concept):
        resolved = next((f for f in fields if f.type is field), None)
    if not resolved:
        return None
    return resolved, fields.index(resolved)

def _find_concept(model: Model, passed_type: Any, extra_types: Sequence[Concept] = [], default:Concept|None = None) -> Concept | None:
    if isinstance(passed_type, Concept):
        return passed_type
    if isinstance(passed_type, str):
        for ext_type in extra_types:
            if ext_type._name == passed_type:
                return ext_type
        name = pytype_to_concept_name.get(passed_type, passed_type)
        if name.startswith("Number(") or name.startswith("Decimal("):
            return cast(Any, CoreConcepts["Number"]).parse(name)
        return model._find_concept(name)
    #TODO: try to find a variable in the frame that is a concept with this name
    return default

#------------------------------------------------------
# Primitive
#------------------------------------------------------

Primitive = str|int|float|bool

def is_primitive(value: Any) -> TypeGuard[str | int | float | bool]:
    return isinstance(value, (str, int, float, bool))

#------------------------------------------------------
# DSLBase
#------------------------------------------------------

class DSLBase:
    def __init__(self, model:Model):
        self._model = model
        self._id = next(_global_id)
        self._source = SourcePos.new()

    #------------------------------------------------------
    # Hashing
    #------------------------------------------------------

    def to_dict_key(self) -> int|tuple[int, int]:
        return self._id

    def __hash__(self) -> NoReturn:
        exc("Unhashable type", f"{self.__class__.__name__} objects are unhashable. Use `to_dict_key()` instead.", [source(self)])

#------------------------------------------------------
# DSLDict
#------------------------------------------------------

def dsl_key(obj:Any) -> Any:
    if isinstance(obj, DSLBase):
        return obj.to_dict_key()
    elif isinstance(obj, tuple):
        return tuple(dsl_key(o) for o in obj)
    return obj

#------------------------------------------------------
# Variable
#------------------------------------------------------

class Variable(DSLBase):
    #--------------------------------------------------
    # Infix operator overloads
    #--------------------------------------------------

    def _bin_op(self, op, left, right) -> Expression:
        res = CoreConcepts["Numeric"].ref()
        return Expression(CoreRelationships[op], [left, right, res])

    def __add__(self, other):
        return self._bin_op("+", self, other)
    def __radd__(self, other):
        return self._bin_op("+", other, self)

    def __mul__(self, other):
        return self._bin_op("*", self, other)
    def __rmul__(self, other):
        return self._bin_op("*", other, self)

    def __sub__(self, other):
        return self._bin_op("-", self, other)
    def __rsub__(self, other):
        return self._bin_op("-", other, self)

    def __truediv__(self, other):
        return self._bin_op("/", self, other)
    def __rtruediv__(self, other):
        return self._bin_op("/", other, self)

    def __floordiv__(self, other):
        return self._bin_op("//", self, other)
    def __rfloordiv__(self, other):
        return self._bin_op("//", other, self)

    def __pow__(self, other):
        return self._bin_op("^", self, other)
    def __rpow__(self, other):
        return self._bin_op("^", other, self)

    def __mod__(self, other):
        return self._bin_op("%", self, other)
    def __rmod__(self, other):
        return self._bin_op("%", other, self)

    def __neg__(self):
        return self._bin_op("*", self, -1)

    #--------------------------------------------------
    # Filter overloads
    #--------------------------------------------------

    def _filter(self, op, left, right) -> Expression:
        return Expression(CoreRelationships[op], [left, right])

    def __gt__(self, other):
        return self._filter(">", self, other)
    def __ge__(self, other):
        return self._filter(">=", self, other)
    def __lt__(self, other):
        return self._filter("<", self, other)
    def __le__(self, other):
        return self._filter("<=", self, other)
    def __eq__(self, other) -> Any:
        return self._filter("=", self, other)
    def __ne__(self, other) -> Any:
        return self._filter("!=", self, other)

    #--------------------------------------------------
    # And/Or
    #--------------------------------------------------

    def __or__(self, other) -> Match:
        return Match(self._model, self, other)

    def __and__(self, other) -> Fragment:
        if isinstance(other, Fragment):
            new = other.where()
            new._where.insert(0, self)
            return new
        return self._model.where(self, other)

    #------------------------------------------------------
    # AsBool
    #------------------------------------------------------

    def as_bool(self) -> AsBool:
        return AsBool(self)

    #------------------------------------------------------
    # Alias
    #------------------------------------------------------

    def alias(self, alias: str) -> Alias:
        return Alias(self, alias)

    #--------------------------------------------------
    # in_
    #--------------------------------------------------

    def in_(self, values:Sequence[Value]|Variable):
        if isinstance(values, Variable):
            return self == values
        if all(isinstance(v, (str, int, float, bool)) for v in values):
            data_table = self._model.data([(v,) for v in values])
            return self == data_table[0]
        else:
            return self == self._model.union(*values)

    #--------------------------------------------------
    # Check value
    #--------------------------------------------------

    def _check_value(self) -> bool:
        return True

    def _to_concept(self) -> Concept|None:
        return None

    #------------------------------------------------------
    # Error handling
    #------------------------------------------------------

    def __bool__(self) -> NoReturn:
        cur_source = self._source.block.source or ""
        invalid = next((bool_check for bool_check in ["if ", "while ", " and ", " or "] if bool_check in cur_source), "bool check").strip()
        mapped = {"and": "`&` or `,`", "or": "`|`", "if": "`where`"}
        if m := mapped.get(invalid):
            exc(f"Invalid operator", f"Cannot use python's `{invalid}` in model expressions. Use {m} instead.", [source(self)])
        else:
            exc(f"Invalid operator", f"Cannot use python's `{invalid}` in model expressions.", [source(self)])

    if not TYPE_CHECKING:
        def __iter__(self):
            common_incorrect = ["sum", "min", "max"]
            for agg in common_incorrect:
                if agg in self._source.block.source:
                    exc(f"Invalid built-in", f"The Python built-in `{agg}()` was used instead of the RAI equivalent.", [
                        source(self),
                        f"Use [cyan]`relationalai.semantics.std.aggregates.{agg}`[/cyan] instead.",
                    ])
            exc("Invalid iteration", f"Cannot iterate over {self.__class__.__name__} objects.", [
                source(self)
            ])

        def __len__(self) -> NoReturn:
            exc("Invalid operator", "Cannot use len() on model variables.", [source(self)])

#------------------------------------------------------
# Concept
#------------------------------------------------------

class Concept(Variable):
    lookup_by_id: dict[int, Concept] = {}

    def __init__(self, name: str, extends: list[Concept], identify_by: dict[str, Concept], model:Model):
        super().__init__(model)
        Concept.lookup_by_id[self._id] = self
        self._name = name
        clean_extends = []
        for extend in extends:
            if not isinstance(extend, Concept):
                exc("Invalid extend", f"Cannot extend from non-Concept type: {extend}", [source(self)])
            if "Number" in CoreConcepts and extend is CoreConcepts["Number"]:
                clean_extends.append(extend.size(38, 14))
            else:
                clean_extends.append(extend)
        self._extends = clean_extends
        self._annotations: list[Expression|Relationship] = []
        self._relationships = {}
        self._identify_by:list[Relationship] = []
        for id_name, id_val in identify_by.items():
            if not isinstance(id_val, (Concept, Property)):
                exc("Invalid identify_by", f"identify_by values must be Concepts, got: {type(id_val)}", [source(self)])
            id_val = self._dot(id_name, with_type=id_val)
            self._identify_by.append(id_val)

    def __setattr__(self, name: str, value: Any) -> None:
        if isinstance(value, Relationship):
            key = name.lower()
            if self._relationships.get(key) is not None:
                exc("Duplicate relationship", f"Relationship '{name}' is already defined on concept '{self._name}'", [
                    source(self._relationships[key])
                ])
            if not value._short_name:
                value._short_name = name
            self._relationships[key] = value
        else:
            super().__setattr__(name, value)

    def _dot_recur(self, name: str, with_type: Any = None) -> Relationship|None:
        if name.lower() in self._relationships:
            return self._relationships[name.lower()]
        for ext in self._extends:
            rel = ext._dot_recur(name, with_type)
            if rel is not None:
                return rel
        # We should create the relationship on the root type if it's not
        # found anywhere
        if self._model is not CoreLibrary:
            field_type = _find_concept(self._model, with_type, default=CoreConcepts["Any"])
            assert field_type is not None
            rel = self._relationships[name.lower()] = Property(fields=[
                Field(self._name.lower(), self),
                Field(name, field_type)
            ], short_name=name, model=self._model)
            return rel
        return None

    def _dot(self, name: str, with_type: Any = None) -> Relationship:
        if self._model is CoreLibrary:
            exc("Invalid relationship", f"Cannot access relationships on core concept '{self._name}'.", [source(self)])
        if with_type is None:
            with_type = CoreConcepts["Any"]
        rel = self._dot_recur(name, with_type)
        assert rel is not None
        return rel

    def __getattr__(self, item) -> Chain:
        if item.startswith("_"):
            return object.__getattribute__(self, item)
        return Chain(self, self._dot(item))

    def __call__(self, *args: Any, **kwargs: Any) -> Expression:
        return Expression(self, list(args), kwargs)

    def new(self, *args: StatementAndSchema, **kwargs: Any) -> New:
        return New(self, args, kwargs)

    def to_identity(self, *args: Any, **kwargs: Any) -> New:
        return New(self, args, kwargs, identity_only=True)

    def identify_by(self, *properties: Property|Chain) -> Concept:
        for prop in properties:
            if isinstance(prop, Chain):
                prop = prop._next
            if not isinstance(prop, Property) and not (isinstance(prop, Reading) and isinstance(prop._relationship, Property)):
                exc("Invalid identify_by", f"identify_by expects Properties, got: {type(prop).__name__}", [source(self)])
            if prop._fields[0].type is not self:
                exc("Invalid identify_by", f"Property {prop} have the first field be {self._name}", [source(self)])
            self._identify_by.append(prop)
        return self

    def filter_by(self, **kwargs: Any) -> Expression:
        return FilterBy(self, kwargs)

    def require(self, *items: Variable|Fragment) -> Fragment:
        return self._model.where(self).require(*items)

    def ref(self, name="") -> Ref:
        return Ref(self, name)

    def annotate(self, *annos:Expression|Relationship) -> Concept:
        self._annotations.extend(annos)
        return self

    def _to_concept(self) -> Concept:
        return self

    def __dir__(self):
        default = set(super().__dir__())
        return sorted(default.union(self._relationships.keys()))

    def __format__(self, format_spec: str) -> str:
        if not format_spec:
            return f"{{{self._name}#{self._id}}}"
        return f"{{{self._name}#{self._id}:{format_spec.strip()}}}"

#------------------------------------------------------
# NumberConcept
#------------------------------------------------------

class NumberConcept(Concept):
    def __init__(self, name: str, precision: int, scale: int, model: Model):
        super().__init__(name, extends=[CoreConcepts["Numeric"]], identify_by={}, model=model)
        self._precision = precision
        self._scale = scale

#------------------------------------------------------
# Ref
#------------------------------------------------------

class Ref(Variable):
    def __init__(self, concept: Concept, name: str|None = None):
        super().__init__(concept._model)
        self._concept = concept
        self._name = name or ("number" if (isinstance(concept, NumberConcept) or concept is CoreConcepts["Numeric"])
                              else concept._name)

    def __getattr__(self, item):
        if item.startswith("_"):
            return object.__getattribute__(self, item)
        return Chain(self, self._concept._dot(item))

    def _to_concept(self) -> Concept:
        return self._concept

    def FilterBy(self, **kwargs: Any) -> Expression:
        return FilterBy(self, kwargs)

#------------------------------------------------------
# Table
#------------------------------------------------------

class Table(Concept):
    def __init__(self, name:str, schema: dict[str, Concept], model: Model):
        super().__init__(name, [], {}, model)
        self._known_columns = []
        for col_name, col_type in schema.items():
            if isinstance(col_type, Property):
                col_rel = col_type
                setattr(self, col_name, col_rel)
            else:
                col_rel = self._dot(col_name, with_type=col_type)
            self._known_columns.append(col_rel)

    @property
    def _columns(self) -> list[Relationship]:
        if self._known_columns:
            return self._known_columns
        schema = schema_util.fetch(self._name)
        for col_name, col_type_name in schema.items():
            col_type = _find_concept(self._model, col_type_name, default=CoreConcepts["Any"])
            col_rel = self._dot(col_name, with_type=col_type)
            self._known_columns.append(col_rel)
        return self._known_columns

    def __getitem__(self, index: int|str) -> Chain:
        if isinstance(index, int):
            if not (0 <= index < len(self._columns)):
                raise IndexError(f"Column index {index} out of range, there are {len(self._columns)} columns")
            return Chain(self, self._columns[index])
        col = next((c for c in self._columns if c._short_name == index), None)
        if col is None:
            raise KeyError(f"Column name '{index}' not found, columns have names {[c._short_name for c in self._columns]}")
        return Chain(self, col)

    def __iter__(self) -> Iterator[Relationship]:
        return iter(self._columns)

    def new(self, *args:StatementAndSchema, **kwargs: Any) -> NoReturn:
        exc("Invalid new call", "Cannot create new instances of Tables.", [source(self)])

    def to_identity(self, *args: Any, **kwargs: Any) -> NoReturn:
        exc("Invalid identity call", "Cannot create identity instances of Tables.", [source(self)])

    def to_schema(self, *, exclude: list[str] = []) -> TableSchema:
        return TableSchema(self, exclude=exclude)

#------------------------------------------------------
# TableSchema
#------------------------------------------------------

class TableSchema(DSLBase):
    def __init__(self, table: Table, exclude: list[str] = []):
        super().__init__(table._model)
        self._table = table
        self.exclude = set([e.lower() for e in exclude])

    def get_columns(self) -> list[Relationship]:
        return [col for col in self._table._columns if col._short_name.lower() not in self.exclude]

#--------------------------------------------------
# DerivedTable
#--------------------------------------------------

class DerivedTable(Variable):
    def __init__(self, model: Model):
        super().__init__(model)
        self.__cols = []

    @property
    def _columns(self):
        if not self.__cols:
            self.__cols = self._get_cols()
        if not self.__cols:
            raise ValueError(f"Cannot use {self.__class__.__name__} as it has no columns")
        return self.__cols

    def _check_value(self):
        return bool(self._columns)

    def __iter__(self) -> Iterator[DerivedColumn]:
        return iter(self._columns)

    def __getitem__(self, index: int|str) -> DerivedColumn:
        if isinstance(index, int):
            if not (0 <= index < len(self._columns)):
                raise IndexError(f"Column index {index} out of range, there are {len(self._columns)} columns")
            return self._columns[index]
        col = next((c for c in self._columns if c._name == index), None)
        if not col:
            raise KeyError(f"Column name '{index}' not found, columns have names {[c._name for c in self._columns]}")
        return col

    def _get_cols(self):
        raise NotImplementedError()

#--------------------------------------------------
# DerivedColumn
#--------------------------------------------------

class DerivedColumn(Variable):
    def __init__(self, table: DerivedTable, index: int, name: str|None = None, type_: Concept|None = None):
        super().__init__(table._model)
        self._table = table
        self._index = index
        self._name = name
        self._type = type_
        self._relationships = {}

    def _dot(self, name: str) -> Relationship:
        if self._type is not None:
            return self._type._dot(name)
        if name.lower() not in self._relationships:
            self._relationships[name.lower()] = Property(fields=[
                Field("entity", CoreConcepts["Any"]),
                Field(name, CoreConcepts["Any"])
            ], short_name=name, model=self._model)
        return self._relationships[name.lower()]

    def __getattr__(self, item):
        if item.startswith("_"):
            return object.__getattribute__(self, item)
        return Chain(self, self._dot(item))

    @staticmethod
    def from_value(table: DerivedTable, index: int, var: Value) -> DerivedColumn:
        name = None
        if isinstance(var, Alias):
            name = var._alias
        if not isinstance(var, Variable):
            var = Literal(var, table._model)
        return DerivedColumn(table=table, index=index, name=name, type_=var._to_concept())

#------------------------------------------------------
# Field
#------------------------------------------------------

class Field:
    def __init__(self, name: str, type_: Concept, is_input: bool = False, is_list: bool = False, source: SourcePos | None = None):
        self._id = next(_global_id)
        self.name = name
        self.type = type_
        self.is_input = is_input
        self.is_list = is_list
        self._source = source

    @classmethod
    def input(cls, name: str, concept: Concept, is_list: bool = False) -> Field:
        return Field(name, concept, is_input=True, is_list=is_list)

    def _match(self, other: Field) -> bool:
        return self.name == other.name and self.type is other.type

#--------------------------------------------------
# Relationship
#--------------------------------------------------

class Relationship(Variable):
    def __init__(self, model: Model, reading_str:str = "", fields: list[Field] = [], short_name: str = "", allow_no_fields: bool = False, overloads:list[list[Concept]]|None = None, is_unresolved: bool = False):
        super().__init__(model)
        if not reading_str and not fields and not allow_no_fields:
            raise ValueError("Either reading_str or fields must be provided")
        if not reading_str and fields:
            reading_str = " and ".join([f"{{{f.type._name}#{f.type._id}:{f.name}}}" for f in fields[:-1]])
            reading_str = f"{reading_str} has {{{fields[-1].type._name}#{fields[-1].type._id}:{fields[-1].name}}}"
        parts = []
        if not fields:
            (fields, parts) = Reading.parse(model, reading_str, fields, _source=self)
        self._fields = fields
        if not fields and not allow_no_fields:
            exc("Invalid Relationship", "A Relationship must have at least one field.", [source(self)])
        self._readings = [Reading(model, self, reading_str, fields, parts)]
        self._short_name = short_name
        self._relationships = {}
        self._annotations: list[Expression|Relationship] = []
        self._overloads = overloads
        self._is_unresolved = is_unresolved
        for f in self._fields:
            if f._source is None:
                f._source = self._source

    def _dot(self, name: str) -> Relationship:
        field_type = self._fields[-1].type
        if name.lower() in self._relationships:
            return self._relationships[name.lower()]
        if field_type is CoreConcepts["Any"]:
            rel = Property(fields=[
                Field(self._fields[-1].name, field_type),
                Field(name, CoreConcepts["Any"])
            ], short_name=name, model=self._model, is_unresolved=True)
            self._relationships[name.lower()] = rel
            return rel
        return field_type._dot(name)

    def __getattr__(self, item):
        if item.startswith("_"):
            return object.__getattribute__(self, item)
        op = self._fields[-1].type._dot(item)
        return Chain(self, op)

    def __call__(self, *args: Any, **kwargs: Any) -> Expression:
        return Expression(self, list(args), kwargs, root=self)

    def __getitem__(self, field: str|int|Concept) -> FieldRef:
        resolved = _find_field(self._fields, field)
        if not resolved:
            raise KeyError(f"Field {field} not found in relationship with fields {[f.name for f in self._fields]}")
        return FieldRef(self, field, *resolved)

    def alt(self, reading_str: str) -> Reading:
        reading = Reading(self._model, self, reading_str)
        self._readings.append(reading)
        return reading

    def annotate(self, *annos:Expression|Relationship) -> Relationship:
        self._annotations.extend(annos)
        return self

    def _to_concept(self) -> Concept|None:
        return self._fields[-1].type

    def __dir__(self):
        default = set(super().__dir__())
        return sorted(default.union(self._fields[-1].type.__dir__()))

    def to_df(self) -> DataFrame:
        refs = [self[ix] for ix in range(len(self._fields))]
        return self._model.select(*refs).where(self(*refs)).to_df()

    def inspect(self):
        print(self.to_df())

#------------------------------------------------------
# Reading
#------------------------------------------------------

class Reading(Relationship):
    def __init__(self, model: Model, relationship: Relationship, reading_str: str, reading_fields: list[Field] = [], reading_parts: list[str|int] = []):
        Variable.__init__(self, model)
        self._relationship = relationship
        if not reading_fields or not reading_parts:
            parsed_fields, parsed_parts = Reading.parse(model, reading_str, reading_fields, _source=self)
            reading_fields = reading_fields or parsed_fields
            reading_parts = reading_parts or parsed_parts
        # make sure we can find all these fields in the base relationship
        index_map = {}
        matched = []
        for field_i, field in enumerate(reading_fields):
            found = next(((i, f) for i, f in enumerate(relationship._fields) if f._match(field)), None)
            if not found:
                raise ValueError(f"Field {field.name}:{field.type._name} not found in relationship with fields {[f'{f.name}:{f.type._name}' for f in relationship._fields]}")
            matched.append(found[1])
            index_map[field_i] = found[0]
        self._fields = matched
        self._reading = reading_str
        self._short_name = ""
        self._parts:list[str|int] = [index_map.get(p, p) for p in reading_parts]
        self._relationships = {}
        self._annotations: list[Expression|Relationship] = []

    #------------------------------------------------------
    # Parse
    #------------------------------------------------------

    @classmethod
    def parse(cls, model: Model, reading: str, known_fields: list[Field], _source=None) -> Tuple[list[Field], list[str|int]]:
        # match <class 'foo'> which is the serialized form of a python type mistakenly passed instead of a concept
        class_pattern = re.compile(r'<class \'(.*?)\'>')
        match = class_pattern.search(reading)
        if match:
            extra: list = [source(_source)]
            if match.group(1) in pytype_to_concept_name:
                concept = pytype_to_concept_name[match.group(1)]
                extra.append(f" Did you mean to use [cyan]relationalai.semantics.{concept}[/cyan]?")
            exc("Invalid field type", f"The type '{match.group(1)}' is not a valid Concept.", extra)

        # {Type} or {name:Type}, where Type can include Number(38,14)
        pattern = re.compile(r'\{([a-zA-Z0-9_.#]+(?:(?:\([0-9]+,[0-9]+\))(?:[#0-9]+)?)?)(?::\s*([a-zA-Z0-9_.]+(?:\([0-9]+,[0-9]+\))?))?\}')

        namer = Namer()
        fields: list[Field] = []
        parts: list[str|int] = []

        last_end = 0
        is_old_style = True
        for m in pattern.finditer(reading):
            # literal chunk before this match
            parts.append(reading[last_end:m.start()])
            field_name, field_type_name = m.group(1), m.group(2)
            field_type_id = None
            if "#" in field_name:
                temp_name = field_type_name
                field_type_name, field_type_id = field_name.split("#")
                field_name = temp_name or sanitize(field_type_name.lower())
                is_old_style = False

            # if we don't have a type_name, then only a type was provided
            if not field_type_name:
                field_type_name = field_name
                field_name = sanitize(field_name.lower())

            field_name = namer.get_name(field_name)
            field_type = Concept.lookup_by_id.get(int(field_type_id)) \
                            if field_type_id \
                            else _find_concept(model, field_type_name, extra_types=[f.type for f in known_fields])
            if field_type is None:
                exc("Unknown Concept", f"The Concept '{field_type_name}' couldn't be found in the model", [
                    source(_source),
                ])

            fields.append(Field(field_name, field_type))
            parts.append(len(fields) - 1)
            last_end = m.end()

        # trailing literal after the final match
        if(last_end < len(reading)):
            parts.append(reading[last_end:])

        if is_old_style and fields:
            correct = []
            for part in parts:
                if isinstance(part, int):
                    type_name = fields[part].type._name
                    correct_type_name = type_name
                    if isinstance(fields[part].type, NumberConcept):
                        precision = fields[part].type._precision
                        scale = fields[part].type._scale
                        if scale == 0:
                            correct_type_name = f"Integer"
                        else:
                            correct_type_name = f"Number.size({precision},{scale})"
                    if type_name.lower() != fields[part].name and correct_type_name.lower() != fields[part].name:
                        correct.append(f"{{{correct_type_name}:{fields[part].name}}}")
                    else:
                        correct.append(f"{{{correct_type_name}}}")
                else:
                    correct.append(part)
            warn("Deprecated format", "Plain strings for Relationships/Properties is deprecated. Use an f-string instead.", [
                source(_source),
                f'For example: [cyan]f"{"".join(correct)}"',
            ])

        return fields, parts

#------------------------------------------------------
# Property
#------------------------------------------------------

class Property(Relationship):
    pass

#------------------------------------------------------
# Literal
#------------------------------------------------------

class Literal(Variable):
    def __init__(self, value: Any, model:Model, type: Concept|None = None):
        super().__init__(model)
        self._value = value
        self._type = type if type is not None else self._get_type(value)

    def _to_concept(self) -> Concept:
        return self._type

    @staticmethod
    def _get_type(value: Any) -> Concept:
        if type(value) is float and (math.isnan(value) or math.isinf(value)):
            return CoreConcepts["Float"]
        if type(value) is float:
            fractional_digits = 0 if math.isnan(value) else min(len(str(value).split(".")[1]), 14)
            return CoreConcepts["Decimal"].size(38, fractional_digits) # type: ignore
        if type(value) is decimal.Decimal:
            str_value = format(value, 'f')
            if '.' in str_value:
                _, fractional_part = str_value.split('.')
                scale = min(len(fractional_part), 14)
            else:
                scale = 14
            return CoreConcepts["Decimal"].size(38, scale) # type: ignore
        if type(value) in pytype_to_concept_name:
            return CoreConcepts[pytype_to_concept_name[type(value)]]
        else:
            raise NotImplementedError(f"Literal type not implemented for value type: {type(value)}")

#------------------------------------------------------
# Chain
#------------------------------------------------------

class Chain(Variable):
    def __init__(self, start: Chain|Concept|Relationship|DerivedColumn|Table|Ref|FieldRef|Expression, next: Relationship, is_ref = False):
        super().__init__(start._model)
        self._start = start
        self._next = next
        self._is_ref = is_ref

    def __getattr__(self, item):
        if item.startswith("_"):
            return object.__getattribute__(self._next, item)
        next_rel = self._next._dot(item)
        return Chain(self, next_rel)

    def __call__(self, *args: Any, **kwargs: Any) -> Expression:
        last = self._next
        assert not isinstance(last, Chain)
        if len(last._fields) > len(args):
            return Expression(last, [self._start, *args], kwargs, root=self)
        return Expression(last, [*args], kwargs, root=self)

    def to_dict_key(self) -> int|tuple:
        if self._is_ref:
            return self._id
        return (self._start.to_dict_key(), self._next.to_dict_key())

    def __getitem__(self, field: str|int|Concept) -> FieldRef:
        resolved = _find_field(self._next._fields, field)
        if not resolved:
            raise KeyError(f"Field {field} not found in relationship with fields {[f.name for f in self._next._fields]}")
        return FieldRef(self, field, *resolved)

    def ref(self) -> Chain:
        return Chain(self._start, self._next, is_ref=True)

    def alt(self, reading_str: str) -> Reading:
        return self._next.alt(reading_str)

    def annotate(self, *annos:Expression|Relationship) -> Relationship:
        return self._next.annotate(*annos)

    def _to_concept(self) -> Concept | None:
        return self._next._to_concept()

#------------------------------------------------------
# Expression
#------------------------------------------------------

class Expression(Variable):
    def __init__(self, op: Relationship|Concept, args: Sequence[Value], kwargs: dict|None = None, root: Chain|Relationship|Concept|None = None):
        super().__init__(op._model)
        self._op = op
        self._has_output = isinstance(op, Concept) or (any(not f.is_input for f in op._fields))
        self._auto_filled = False
        self._root = root

        # clean args
        clean_args = []
        for arg in args:
            if isinstance(arg, (ModelEnum, Field, TupleVariable)):
                pass
            elif isinstance(arg, TableSchema):
                exc("Invalid argument", "Cannot use a schema as an argument to an Expression.", [source(self)])
            elif not isinstance(arg, Variable):
                arg = Literal(arg, self._model)
            elif isinstance(arg, (Match, Fragment)):
                arg._columns
            clean_args.append(arg)
        self._args = clean_args

        self._kwargs = kwargs or {}
        # clean kwargs
        for k, v in self._kwargs.items():
            if not isinstance(v, Variable):
                self._kwargs[k] = Literal(v, self._model)

        if isinstance(op, Relationship):
            op_len = len(op._fields)
            arg_len = len(self._args)
            if op_len - arg_len == 1:
                self._args.append(op._fields[-1].type.ref(name=op._fields[-1].name))
                self._auto_filled = True
            elif op_len != arg_len:
                dir = "Too few" if arg_len < op_len - 1 else "Too many"
                exc(f"{dir} args", f"{op._short_name or 'Relationship'} requires {op_len - 1}-{op_len} arguments but got {arg_len}", [
                    source(self),
                ])

    def __getattr__(self, item):
        if item.startswith("_"):
            return object.__getattribute__(self, item)
        rel = self._op._dot(item)
        return Chain(self, rel)

    def __getitem__(self, field: str|int|Concept) -> FieldRef:
        if not isinstance(self._op, Relationship):
            raise TypeError(f"Cannot index into Expression with non-Relationship: {self._op}")
        resolved = _find_field(self._op._fields, field)
        if not resolved:
            raise KeyError(f"Field {field} not found in relationship with fields {[f.name for f in self._op._fields]}")
        return FieldRef(self, field, *resolved)

    def _to_concept(self) -> Concept | None:
        return self._args[-1]._to_concept() if self._args else self._op._to_concept()

#------------------------------------------------------
# New
#------------------------------------------------------

class New(Expression):
    def __init__(self, concept: Concept, args: Sequence[Any], kwargs: dict[str, Any], identity_only: bool = False):
        clean_args = []
        row_ids = []
        for arg in args:
            if isinstance(arg, TableSchema):
                row_ids.append(arg._table)
                lower_case_kwargs = {k.lower() for k, v in kwargs.items()}
                # add any keyword args that aren't already in kwargs
                for col in arg.get_columns():
                    if col._short_name and col._short_name.lower() not in lower_case_kwargs:
                        kwargs[col._short_name] = col(arg._table)
            else:
                clean_args.append(arg)
        for k in list(kwargs.keys()):
            concept._dot(k)
        super().__init__(concept, clean_args, kwargs)
        self._identity_only = identity_only
        self._row_ids = row_ids

#------------------------------------------------------
# FilterBy
#------------------------------------------------------

class FilterBy(Expression):
    def __init__(self, item: Concept|Ref, kwargs: dict[str, Any]):
        concept = item._concept if isinstance(item, Ref) else item
        super().__init__(concept, [item], kwargs)

#------------------------------------------------------
# FieldRef
#------------------------------------------------------

class FieldRef(Variable):
    def __init__(self, root: Chain|Relationship|Expression, field: str|int|Concept, resolved: Field, resolved_ix:int):
        super().__init__(root._model)
        self._root = root
        self._field = field
        self._resolved = resolved
        self._resolved_ix = resolved_ix

    def _to_concept(self) -> Concept:
        return self._resolved.type

    def __getattr__(self, item):
        if item.startswith("_"):
            return object.__getattribute__(self, item)
        return Chain(self, self._resolved.type._dot(item))

    def to_dict_key(self) -> tuple:
        return (self._root.to_dict_key(), self._resolved._id)


#------------------------------------------------------
# MetaRef
#------------------------------------------------------

class MetaRef(Variable):
    def __init__(self, target: Concept|Relationship|Field):
        model = target._model if isinstance(target, DSLBase) else target.type._model
        super().__init__(model)
        self._target = target

#------------------------------------------------------
# TupleVariable
#------------------------------------------------------

class TupleVariable:
    def __init__(self, items: Sequence[Value|Distinct]):
        self._items = list(items)
        self._source = SourcePos.new()

#------------------------------------------------------
# AsBool
#------------------------------------------------------

class AsBool(Variable):
    def __init__(self, item: Variable):
        super().__init__(item._model)
        self._item = item

    def _to_concept(self) -> Concept:
        return CoreConcepts["Boolean"]

#------------------------------------------------------
# Alias
#------------------------------------------------------

class Alias(Variable):
    def __init__(self, source: Variable, alias: str):
        super().__init__(source._model)
        self._source = source
        self._alias = alias

    def _to_concept(self) -> Concept|None:
        return self._source._to_concept()

    def __format__(self, format_spec: str) -> str:
        if isinstance(self._source, Concept):
            if format_spec:
                exc("Invalid alias", f"Alias already specifies an alias for this concept, you can remove `:{format_spec}`")
            return self._source.__format__(self._alias)
        return super().__format__(format_spec)

#------------------------------------------------------
# Match
#------------------------------------------------------

class Match(DerivedTable):
    def __init__(self, model:Model, *items: Statement):
        super().__init__(model)
        t = type(self)
        self._items = [
            x
            for item in items
            for x in (item._items if (type(item) is t and isinstance(item, Match)) else (item,))
        ] # flatten nested Matches/Unions

    def _get_cols(self) -> list[DerivedColumn]:
        return [DerivedColumn(self, i) for i in range(self._arg_count())]

    def _arg_count(self) -> int:
        counts = []
        for item in self._items:
            if isinstance(item, DerivedTable):
                try:
                    counts.append(len(item._columns))
                except ValueError:
                    counts.append(0)
            else:
                # Expressions with no output and Not are filters, do not count as returning values
                is_filter = isinstance(item, Not) or (isinstance(item, Expression) and not item._has_output)
                counts.append(0 if is_filter else 1)
        if not counts:
            return 0
        first = counts[0]
        if any(c != first for c in counts[1:]):
            exc("Inconsistent branches",
                f"All branches in a {self.__class__.__name__} must have the same number of returned values",
                [source(self)])
        return first

    def __getattr__(self, item) -> Chain:
        if item.startswith("_"):
            return object.__getattribute__(self, item)
        return getattr(self._columns[-1], item)

#------------------------------------------------------
# Union
#------------------------------------------------------

class Union(Match):
    def __init__(self, model:Model, *items: Value):
        super().__init__(model, *items)

#------------------------------------------------------
# Not
#------------------------------------------------------

class Not(DSLBase):
    def __init__(self, *items: Value, model:Model):
        super().__init__(model)
        self._items = items

    def __or__(self, other) -> Match:
        return Match(self._model, self, other)

    def __and__(self, other) -> Fragment:
        if isinstance(other, Fragment):
            new = other.where()
            new._where.insert(0, self)
            return new
        return self._model.where(self, other)

#------------------------------------------------------
# Distinct
#------------------------------------------------------

class Distinct(DSLBase):
    def __init__(self, *items: Value, model:Model):
        super().__init__(model)
        self._items = items

#------------------------------------------------------
# Aggregate
#------------------------------------------------------

class Group(DSLBase):
    def __init__(self, *args: Value):
        model = [arg._model for arg in args if isinstance(arg, Variable)][0] if args else None
        super().__init__(model) # type: ignore
        self._args = list(args)

    def _extend(self, args: Sequence[Value]) -> Group:
        new = Group(*self._args)
        new._args.extend(args)
        return new

    def _clone(self):
        return Group(*self._args)

class Aggregate(Variable):
    def __init__(self, op: Relationship, *args: Value|Distinct, check_args: bool = True, distinct: bool = False):
        model = self._find_model(args) or op._model
        super().__init__(model)
        self._op = op
        self._where = Fragment(model)
        self._group = Group()
        self._args: list[Value] = []
        self._projection_args: list[Value] = []
        self._distinct = distinct
        if check_args:
            # unwrap distinct if present
            if any(isinstance(arg, Distinct) for arg in args):
                if len(args) != 1:
                    exc("Invalid distinct", "Distinct must be applied to all arguments", [source(self)])
                assert isinstance(args[0], Distinct)
                args = args[0]._items
                self._distinct = True

            args = cast(tuple[Value], args)

            num_inputs = sum(f.is_input for f in op._fields)
            if len(args) < num_inputs:
                need = [f.name for f in op._fields if f.is_input][len(args):]
                exc("Missing argument",
                    f"`{op._short_name or 'Relationship'}(..)` is missing: {', '.join(need)}",
                    [source(self)])

            self._projection_args = list(args[:-num_inputs] if num_inputs else args)
            supplied = iter(args[-num_inputs:] if num_inputs else [])

            self._args = [
                (next(supplied) if f.is_input else f.type.ref(f.name))
                for f in op._fields
            ]

    def _find_model(self, args: Sequence[Value|Distinct|TupleVariable]) -> Model|None:
        for arg in args:
            if isinstance(arg, (Variable, Distinct)):
                return arg._model
            elif isinstance(arg, TupleVariable):
                for item in arg._items:
                    if isinstance(item, (Variable, Distinct)):
                        return item._model
        return None


    def where(self, *args: Value) -> Aggregate:
        new = self._clone()
        new._where = new._where.where(*args)
        return new

    def per(self, *args: Value) -> Aggregate:
        new = self._clone()
        new._group = new._group._extend(args)
        return new

    def _clone(self):
        agg = Aggregate(self._op, check_args=False)
        agg._args = self._args
        agg._projection_args = self._projection_args
        agg._where = self._where
        agg._group = self._group
        agg._distinct = self._distinct
        return agg

#------------------------------------------------------
# Data
#------------------------------------------------------

class Data(Table):
    def __init__(self, df:DataFrame, model:Model):
        schema = {}
        for col in df.columns:
            _type = df[col].dtype
            if pd.api.types.is_datetime64_any_dtype(_type):
                col_type = "DateTime"
            elif pd.api.types.is_object_dtype(_type) and self._is_date_column(df[col]):
                col_type = "Date"
            else:
                col_type = pytype_to_concept_name.get(_type, "Any")
            if isinstance(col, int):
                col = f"col{col}"
            schema[col] = CoreConcepts[col_type]
        super().__init__("Data", schema, model)
        self._data = df

    def _is_date_column(self, col) -> bool:
        sample = col.dropna()
        if sample.empty:
            return False
        sample_value = sample.iloc[0]
        return isinstance(sample_value, dt.date) and not isinstance(sample_value, dt.datetime)

    @staticmethod
    def raw_to_df(data: DataFrame | list[tuple] | list[dict], columns:list[str]|None) -> DataFrame:
        if isinstance(data, DataFrame):
            return data
        if not data:
            return DataFrame()
        if isinstance(data, list):
            if isinstance(data[0], tuple):
                # Named tuple check
                if hasattr(data[0], '_fields'):
                    return DataFrame([t._asdict() for t in data]) #type: ignore
                return DataFrame(data, columns=columns)
            elif isinstance(data[0], dict):
                return DataFrame(data)
        raise TypeError(f"Cannot convert {type(data)} to DataFrame. Use DataFrame, list of tuples, or list of dicts.")

#------------------------------------------------------
# Enum
#------------------------------------------------------

class ModelEnumMeta(EnumMeta):
    _concept: Concept
    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_") or isinstance(value, self):
            super().__setattr__(name, value)
        elif isinstance(value, (Relationship, Reading)):
            setattr(self._concept, name, value)
        else:
            raise AttributeError(f"Cannot set attribute {name} on {type(self).__name__}")

    def __format__(self, format_spec: str) -> str:
        return format(self._concept, format_spec)

class ModelEnum(Enum, metaclass=ModelEnumMeta):
    _model:Model

    def __init__(self, *args) -> None:
        super().__init__(*args)
        self._source = SourcePos.new()

    def _compile_lookup(self):
        concept = getattr(self.__class__, "_concept")
        return concept.to_identity(name=self.name)

    @classmethod
    def lookup(cls, value:Variable|str):
        concept = cls._concept
        return concept.to_identity(name=value)

    # Python 3.10 doesn't correctly populate __members__ by the time it calls
    # __init_subclass__, so we need to initialize the members lazily when we
    # encounter the enum for the first time.
    @classmethod
    def _init_members(cls):
        if cls._has_inited_members:
            return
        c = cls._concept
        # Add the name and value attributes to the hashes we create for the enum
        members = [
            c.new(name=name, value=value.value)
            for name, value in cls.__members__.items()
        ]
        cls._model.define(*members)
        cls._has_inited_members = True

    def __format__(self, format_spec: str) -> str:
        return format(self._concept, format_spec)

def create_enum_class(model: Model):
    class AttachedModelEnum(ModelEnum):
        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)
            # this is voodoo black magic that is doing meta meta programming where
            # we are plugging into anytime a new subtype of this class is created
            # and then creating a concept to represent the enum. This happens both
            # when you do `class Foo(Enum)` and when you do `Enum("Foo", [a, b, c])`
            cls._model = model
            c = model.Concept(
                cls.__name__,
                extends=[CoreConcepts["Enum"]],
                identify_by={"name": CoreConcepts["String"]}
            )
            model.enums.append(cls)
            model.enums_index[cls.__name__] = cls
            cls._has_inited_members = False
            cls._concept = c

    return AttachedModelEnum

#------------------------------------------------------
# Value
#------------------------------------------------------

Value = Variable|Primitive|Field|TupleVariable

#------------------------------------------------------
# Statement
#------------------------------------------------------

Statement = Value | Group | Not | Distinct | Aggregate
"""Union of statement types."""

StatementAndSchema = Statement | TableSchema

#------------------------------------------------------
# Fragment
#------------------------------------------------------

@include_in_docs
class Fragment(DerivedTable):
    """Composable chunk of a query with select/where/define state.

    Parameters
    ----------
    model : Model
        The semantic model that provides type information and stores any
        definitions produced by this fragment.
    parent : Fragment, optional
        An existing fragment to inherit selection and filter state from when
        building chained queries.
    """

    def __init__(self, model:Model, parent:Fragment|None=None):
        super().__init__(model)
        self._id = next(_global_id)
        self._select = []
        self._where = []
        self._require = []
        self._define = []
        self._order_by = []
        self._limit = 0
        self._model = model
        self._into:Optional[Table] = None
        self._is_into_update = False
        self._has_executed = False
        assert self._model, "Fragment must have a model"

        self._parent = parent
        # self._source = runtime_env.get_source_pos()
        self._meta = {}
        self._annotations = []
        if parent is not None:
            self._select.extend(parent._select)
            self._where.extend(parent._where)
            self._require.extend(parent._require)
            self._define.extend(parent._define)
            self._order_by.extend(parent._order_by)
            self._limit = parent._limit


    def _add_items(self, items:Sequence[Statement], to_attr:list[Statement]):
        # TODO: ensure that you are _either_ a select, require, or then
        # not a mix of them
        model = self._model

        # remove any existing rules that this consumes
        for item in itertools.chain(items, [self._parent]):
            if isinstance(item, Fragment) and item._is_effect():
                model._remove_rule(item)

        to_attr.extend(items)
        if self._is_effect():
            model._add_rule(self)

        return self

    #------------------------------------------------------
    # Select arg handling
    #------------------------------------------------------

    def _check_select_args(self, args:Sequence[StatementAndSchema]) -> Sequence[Statement]:
        clean_args = []
        for arg in args:
            # If you select x > y, treat that as AsBool(x > y)
            if isinstance(arg, Expression) and not arg._has_output:
                clean_args.append(AsBool(arg))
            elif isinstance(arg, TableSchema):
                for col in arg.get_columns():
                    clean_args.append(col(arg._table))
            else:
                clean_args.append(arg)
        return clean_args

    #------------------------------------------------------
    # Core API
    #------------------------------------------------------

    def where(self, *args: Statement) -> Fragment:
        f = Fragment(self._model, parent=self)
        return f._add_items(args, f._where)

    def select(self, *args: StatementAndSchema) -> Fragment:
        f = Fragment(self._model, parent=self)
        return f._add_items(self._check_select_args(args), f._select)

    def require(self, *args: Statement) -> Fragment:
        f = Fragment(self._model, parent=self)
        return f._add_items(args, f._require)

    def define(self, *args: Statement) -> Fragment:
        f = Fragment(self._model, parent=self)
        return f._add_items(args, f._define)

    if not TYPE_CHECKING:
        def order_by(self, *args: Any) -> Fragment:
            exc("Feature unavailable", "The 'order_by' method is not yet available when querying RAI directly.", [
                source(self),
                "You can use [cyan]`relationalai.semantics.std.aggregates.rank`[/cyan] and select it as the first column as a temporary substitute.",
            ])
            f = Fragment(self._model, parent=self)
            return f._add_items(args, f._order_by)

        def limit(self, n:int) -> Fragment:
            exc("Feature unavailable", "The 'order_by' method is not yet available when querying RAI directly.", [
                source(self),
                "You can use [cyan]`relationalai.semantics.std.aggregates.limit`[/cyan] in a where clause as a temporary substitute.",
            ])
            f = Fragment(self._model, parent=self)
            f._limit = n
            return f

    # def meta(self, **kwargs: Any) -> Fragment:
    #     self._meta.update(kwargs)
    #     return self

    def annotate(self, *annos:Expression|Relationship) -> Fragment:
        self._annotations.extend(annos)
        return self

    #------------------------------------------------------
    # into
    #------------------------------------------------------

    def into(self, table: Table, update=False) -> Fragment:
        f = Fragment(self._model, parent=self)
        f._into = table
        f._is_into_update = update
        self._model.exports.add(f)
        return f

    #------------------------------------------------------
    # Execution
    #------------------------------------------------------

    def exec(self):
        if self._has_executed:
            return
        if self._into is None:
            exc("Cannot execute", "Query must have an 'into' table specified to execute.", [source(self)])
        from relationalai.shims.executor import execute
        self._has_executed = True
        return execute(self, self._model, export_to=self._into._name, update=self._is_into_update)

    def to_df(self):
        from relationalai.shims.executor import execute
        return execute(self, self._model)

    def inspect(self):
        print(self.to_df())

    #------------------------------------------------------
    # helpers
    #------------------------------------------------------

    def _is_effect(self) -> bool:
        return bool(self._define or self._require)

    def _is_where_only(self) -> bool:
        return not self._select and not self._define and not self._require and not self._order_by

    #------------------------------------------------------
    # And/Or
    #------------------------------------------------------

    def __or__(self, other) -> Match:
        return Match(self._model, self, other)

    def __and__(self, other) -> Fragment:
        if not isinstance(other, Fragment):
            other = Fragment(self._model).where(other)
        if self._is_where_only() and other._is_where_only():
            return self.where(*other._where)
        elif self._is_where_only():
            return other.where(*self._where)
        elif other._is_where_only():
            return self.where(*other._where)
        else:
            raise Exception("Cannot AND two non-where-only fragments")

    #------------------------------------------------------
    # DerivedTable cols
    #------------------------------------------------------

    def _get_cols(self):
        return [DerivedColumn.from_value(self, i, col) for i, col in enumerate(self._select)]

    #------------------------------------------------------
    # Marterialize
    #------------------------------------------------------

    def to_metamodel(self):
        m = self._model
        return m._compiler.compile(self)

#------------------------------------------------------
# Model
#------------------------------------------------------

@include_in_docs
class Model:
    """Class representing a semantic model.

    Parameters
    ----------
    name : str, optional
        Name of the model.
    exclude_core : bool, optional
        If True, the core library will not be included by default.
    is_library : bool, optional
        If True, this model is a library and will not be added to the global
        list of models.

    Examples
    --------
    Create a model object:

    >>> from relationalai.semantics import Model
    >>> model = Model(name="MyModel")
    """
    all_models:list[Model] = []

    def __init__(self, name: str = "", exclude_core: bool = False, is_library: bool = False):
        self.name = name
        self.defines:KeyedSet[Fragment] = KeyedSet(dsl_key)
        self.requires:KeyedSet[Fragment] = KeyedSet(dsl_key)
        self.exports:KeyedSet[Fragment] = KeyedSet(dsl_key)
        self.libraries = []
        self.concepts: list[Concept] = []
        self.tables: list[Table] = []
        self.relationships: list[Relationship] = []
        self.enums: list[Type[ModelEnum]] = []
        self.concept_index: dict[str, Concept] = {}
        self.table_index: dict[str, Table] = {}
        self.relationship_index: dict[str, Relationship] = {}
        self.enums_index: dict[str, Type[ModelEnum]] = {}
        self._source = SourcePos.new()

        self.Enum = create_enum_class(self)

        if not is_library:
            Model.all_models.append(self)

        self.__compiler = None
        if not exclude_core:
            self.libraries.append(CoreLibrary)

    #------------------------------------------------------
    # Internal
    #------------------------------------------------------

    @property
    def _compiler(self):
        if not self.__compiler:
            from .front_compiler import FrontCompiler
            self.__compiler = FrontCompiler(self)
        return self.__compiler

    def _find_concept(self, name: str) -> Concept|None:
        if name in self.concept_index:
            return self.concept_index[name]
        if name in self.table_index:
            return self.table_index[name]
        for lib in self.libraries:
            found = lib._find_concept(name)
            if found is not None:
                return found

    def _remove_rule(self, fragment: Fragment) -> None:
        if fragment._define and fragment in self.defines:
            self.defines.remove(fragment)
        elif fragment._require and fragment in self.requires:
            self.requires.remove(fragment)
        else:
            raise ValueError("Fragment must have either define or require clauses to be removed as a rule")

    def _add_rule(self, fragment: Fragment) -> None:
        if fragment._define and fragment not in self.defines:
            self.defines.add(fragment)
        elif fragment._require and fragment not in self.requires:
            self.requires.add(fragment)
        else:
            raise ValueError("Fragment must have either define or require clauses to be added as a rule")

    #------------------------------------------------------
    # Primary API
    #------------------------------------------------------

    def Concept(self, name: str, extends: list[Concept] = [], identify_by: dict[str, Property|Concept] = {}) -> Concept:
        c = Concept(name, extends=extends, identify_by=identify_by, model=self)
        self.concepts.append(c)
        self.concept_index[name] = c
        return c

    def Table(self, path: str, schema: dict[str, Concept] = {}) -> Table:
        t = Table(path, schema=schema, model=self)
        self.tables.append(t)
        self.table_index[path] = t
        return t

    def Relationship(self, reading: str = "", fields: list[Field] = [], short_name: str = "") -> Relationship:
        r = Relationship(self, reading, fields, short_name)
        self.relationships.append(r)
        self.relationship_index[short_name] = r
        return r

    def Property(self, reading: str = "", fields: list[Field] = [], short_name: str = "") -> Property:
        p = Property(self, reading, fields, short_name)
        self.relationships.append(p)
        self.relationship_index[short_name] = p
        return p

    def select(self, *args: StatementAndSchema) -> Fragment:
        f = Fragment(self)
        return f.select(*args)

    def where(self, *args: Statement) -> Fragment:
        f = Fragment(self)
        return f.where(*args)

    def require(self, *args: Statement) -> Fragment:
        f = Fragment(self)
        return f.require(*args)

    def define(self, *args: Statement) -> Fragment:
        f = Fragment(self)
        return f.define(*args)

    def union(self, *items: Value) -> Union:
        return Union(self, *items)

    def data(self, data: DataFrame | list[tuple] | list[dict], columns: list[str]|None = None) -> Data:
        df = Data.raw_to_df(data, columns)
        return Data(df, self)

    def not_(self, *items: Value) -> Not:
        return Not(*items, model=self)

    def distinct(self, *items: Value) -> Distinct:
        return Distinct(*items, model=self)

    #------------------------------------------------------
    # Meta
    #------------------------------------------------------

    def to_metamodel(self) -> mModel:
        return self._compiler.compile_model(self)

#------------------------------------------------------
# Library
#------------------------------------------------------

class Library(Model):
    def __init__(self, name: str, exclude_core: bool = False):
        super().__init__(name=name, exclude_core=exclude_core, is_library=True)

    def Type(self, name: str, super_types: list[Concept] = []) -> Concept:
        c = self.Concept(name, extends=super_types)
        self._register_builtin(c)
        return c

    def Relation(self, name: str, fields: list[Field], overloads: list[list[Concept]]|None = None, annotations: list[Any]|None = None) -> Relationship:
        r = Relationship(self, "", fields, name, allow_no_fields=True, overloads=overloads)
        self.relationships.append(r)
        self.relationship_index[name] = r
        self._register_builtin(r)
        # TODO - deal with annotations
        return r

    def _register_builtin(self, builtin: Concept|Relationship) -> None:
        """ Register a builtin concept or relationship in the global builtins registry. """
        builtins.register(self.name, self._compiler.to_relation(builtin))


#------------------------------------------------------
# Core Library
#------------------------------------------------------

# Library is populated when relationalai.semantics.frontend.core is imported
CoreLibrary: Library = Library("core", exclude_core=True)
CoreRelationships = CoreLibrary.relationship_index
CoreConcepts = CoreLibrary.concept_index


#------------------------------------------------------
# todo
#------------------------------------------------------

"""
x new/to_identity/filter_by
x capture all defines/requires
x identify_by
x figure out Table/DerivedTable
x data node
x in_
x error on invalid iteration/sum/min/max
x Aggregates
x fill in std.agg functions when Thiago's lib stuff lands
- Error?
x rank stuff
- validation checks for identify_by
- unique
- Enum?
"""
