from __future__ import annotations
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum, EnumMeta
import re
from typing import Any, Optional, Sequence as PySequence, Type, TypedDict, cast
import itertools
import rich
import sys

from pandas import DataFrame
import numpy as np
import pandas as pd
from more_itertools import peekable

from v0.relationalai import debugging, errors
from v0.relationalai.environments.base import find_external_frame
from v0.relationalai.clients.config import Config
from v0.relationalai.util.otel_configuration import configure_otel
from v0.relationalai.clients.result_helpers import Int128Dtype
from v0.relationalai.semantics.metamodel import factory as f, helpers, ir, builtins, types
from v0.relationalai.semantics.metamodel.typer import typer
from v0.relationalai.semantics.metamodel.util import NameCache, OrderedSet, ordered_set, FrozenOrderedSet
from v0.relationalai.semantics.rel.executor import RelExecutor
from v0.relationalai.semantics.lqp.executor import LQPExecutor
from v0.relationalai.semantics.sql.executor import SnowflakeExecutor
from v0.relationalai.environments import runtime_env, SessionEnvironment
from collections import Counter, defaultdict
from snowflake.snowpark import Session, DataFrame as SnowparkDataFrame

from datetime import date, datetime
from decimal import Decimal as PyDecimal

#--------------------------------------------------
# Globals
#--------------------------------------------------

_global_id = peekable(itertools.count(0))

# Single context variable with default values
_overrides = ContextVar("overrides", default = {})
def overrides(key: str, default: bool | str | dict | datetime | None):
    return _overrides.get().get(key, default)

# Flag that users set in the config or directly on the model, but that can still be
# overridden globally. Precedence is overrides > model argument > config.
def overridable_flag(key: str, config: Config, user_pref: bool | None, default: bool):
    if user_pref is not None:
        preferred = cast(bool, user_pref)
    else:
        preferred = cast(bool, config.get(key, default))
    return overrides(key, preferred)

@contextmanager
def with_overrides(**kwargs):
    token = _overrides.set({**_overrides.get(), **kwargs})
    try:
        yield
    finally:
        _overrides.reset(token)

# Intrinsic values to override for stable snapshots.
def get_intrinsic_overrides() -> dict[str, Any]:
    datetime_now = overrides('datetime_now', None)
    if datetime_now is not None:
        return {'datetime_now': datetime_now}
    return {}

#--------------------------------------------------
# Root tracking
#--------------------------------------------------

_track_default = True
_track_roots = ContextVar('track_roots', default=_track_default)
_global_roots = ordered_set()

def _add_root(root):
    if _track_roots.get():
        _global_roots.add(root)

def _remove_roots(items: PySequence[Producer|Fragment]):
    for item in items:
        if hasattr(item, "__hash__") and item.__hash__ and item in _global_roots:
            _global_roots.remove(item)

# decorator
def roots(enabled=_track_default):
    def decorator(func):
        def wrapper(*args, **kwargs):
            token = _track_roots.set(enabled)
            try:
                return func(*args, **kwargs)
            finally:
                _track_roots.reset(token)
        return wrapper
    return decorator

# with root_tracking(enabled=False): ...
@contextmanager
def root_tracking(enabled=_track_default):
    token = _track_roots.set(enabled)
    try:
        yield
    finally:
        _track_roots.reset(token)

#--------------------------------------------------
# Helpers
#--------------------------------------------------

def default_dir(obj):
    """
    This function returns the names of attributes from `__dict__` and relevant
    parent's attributes. It's a simplification of what `dir()` does by default.
    The intention is for `default_dir(obj)` to return what dir(obj) would
    return if `obj.__dir__` was not defined.

    There are some corner cases that are not handled because we don't need them,
    e.g. obj being `None` or a type, or corner cases of `__slots__`.
    """

    attributes = set()

    # Add attributes from the object's __dict__ if it exists
    if hasattr(obj, '__dict__'):
        attributes.update(obj.__dict__.keys())

    # Add attributes from class and base classes
    if hasattr(obj, '__class__'):
        for cls in obj.__class__.__mro__:
            attributes.update(cls.__dict__.keys())

    return attributes


def unwrap_list(item:Any) -> Any:
    if isinstance(item, (list, tuple)) and len(item) == 1:
        return item[0]
    elif isinstance(item, (list, tuple)) and len(item) > 1:
        raise ValueError(f"Expected a single item, got {len(item)}")
    return item

def flatten(items:PySequence[Any], flatten_tuples=False) -> list[Any]:
    flat = []
    for item in items:
        if isinstance(item, (list, tuple)) and (flatten_tuples or not isinstance(item, TupleArg)):
            flat.extend(flatten(item, flatten_tuples=flatten_tuples))
        else:
            flat.append(item)
    return flat

def find_subjects(items: PySequence[Producer]) -> set[Concept|Ref]:
    subjects = set()
    for item in items:
        if isinstance(item, Concept):
            subjects.add(item)
        elif isinstance(item, ConceptExpression):
            subjects.add(item._op)
        elif isinstance(item, Expression):
            subjects.update(find_subjects(item._params))
        elif isinstance(item, Ref):
            subjects.add(item)
        elif isinstance(item, Relationship) and item._parent:
            subjects.update(find_subjects([item._parent]))
    return subjects

def to_type(item: Any) -> Concept|None:
    if isinstance(item, Concept):
        return item
    elif isinstance(item, (Ref, Alias, TypeRef)):
        return to_type(item._thing)
    elif isinstance(item, ConceptExpression):
        return to_type(item._op)
    elif isinstance(item, Expression):
        return to_type(item._params[-1])

def find_local(name:str) -> Any:
    frame = find_external_frame()
    if frame and name in frame.f_locals:
        return frame.f_locals[name]
    return None

def field_to_type(model:Model|None, field: Field) -> Concept:
    if field.type is not None:
        return field.type
    type_str = field.type_str
    if type_str in python_types_str_to_concepts:
        return python_types_str_to_concepts[type_str]
    elif model and type_str in model.concepts:
        concepts = model.concepts[type_str]
        if len(concepts) > 1:
            # this can be expensive, but is only done if the type_str is ambiguous
            found = find_local(type_str)
            if found in set(concepts):
                return found
            if not found:
                raise ValueError(f"Ambiguous reference to Concept '{type_str}'")
            raise ValueError(f"Reference '{type_str}' is not a valid Concept")
        return concepts[0]
    elif type_str in Concept.builtins:
        return Concept.builtins[type_str]
    elif type_str.lower() in Concept.globals:
        return Concept.globals[type_str.lower()]
    elif found := find_local(type_str):
        if isinstance(found, Concept):
            return found
        elif hasattr(found, "_to_type") and callable(found._to_type):
            return cast(Concept, found._to_type())
        raise ValueError(f"Reference '{type_str}' is not a valid Concept")
    elif type_str.startswith("Decimal"):
        return decimal_concept_by_name(type_str)
    else:
        return Concept.builtins["Any"]

def to_name(item:Any) -> str:
    if isinstance(item, Relationship) and isinstance(item._parent, Concept):
        return f"{item._parent._name}_{item._name}"
    elif isinstance(item, (Ref, Alias)):
        return item._name or to_name(item._thing)
    elif isinstance(item, RelationshipRef):
        return item._relationship._name
    elif isinstance(item, ConceptExpression):
        return item._op._name.lower()
    elif isinstance(item, Concept):
        return item._name.lower()
    return getattr(item, "_name", "v")

def find_model(items: Any) -> Model|None:
    if isinstance(items, (list, tuple)):
        for item in items:
            model = find_model(item)
            if model:
                return model
    elif isinstance(items, dict):
        for item in items.values():
            model = find_model(item)
            if model:
                return model
    else:
        if hasattr(items, "_model") and items._model:
            return items._model
    return None

def with_source(item:Any):
    if not hasattr(item, "_source"):
        raise ValueError(f"Item {item} has no source")
    elif item._source is None:
        return {}
    elif debugging.DEBUG:
        source = item._source.to_source_info()
        if source:
            return { "file": source.file, "line": source.line, "source": source.source }
        else:
            return {"file":item._source.file, "line":item._source.line}
    else:
        return {"file":item._source.file, "line":item._source.line}

def has_keys(item: Any) -> bool:
    try:
        return bool(len(find_keys(item)))
    except Exception:
        return False

def find_keys(item: Any, keys:OrderedSet[Any]|None = None) -> OrderedSet[Any]:
    if keys is None:
        keys = ordered_set()

    if isinstance(item, (list, tuple)):
        for it in item:
            find_keys(it, keys)

    elif isinstance(item, (Relationship, RelationshipReading)) and item._parent:
        find_keys(item._parent, keys)
        if item.is_many():
            keys.add(item._field_refs[-1])

    elif isinstance(item, RelationshipRef):
        find_keys(item._parent, keys)
        if item._relationship.is_many():
            keys.add(item._field_refs[-1])

    elif isinstance(item, (Relationship, RelationshipReading, Property)):
        if item.is_many():
            keys.update(item._field_refs)
        else:
            keys.add(item._field_refs[0])

    elif isinstance(item, Concept):
        if not item._is_primitive():
            keys.add(item)

    elif isinstance(item, ConceptExpression):
        for it in item._params[1].values():
            find_keys(it, keys)

    elif isinstance(item, Ref):
        if isinstance(item._thing, Concept):
            if not item._thing._is_primitive():
                keys.add(item)
        else:
            find_keys(item._thing, keys)

    elif isinstance(item, RelationshipFieldRef):
        find_keys(item._relationship, keys)

    elif isinstance(item, ArgumentRef):
        find_keys(item._arg, keys)

    elif isinstance(item, TypeRef):
        find_keys(item._thing, keys)

    elif isinstance(item, Alias):
        find_keys(item._thing, keys)

    elif isinstance(item, Aggregate):
        keys.update(item._group)

    elif isinstance(item, Expression):
        find_keys(item._params, keys)

    elif isinstance(item, Data):
        keys.add(item._row_id)

    elif isinstance(item, DataColumn):
        keys.add(item._data)

    elif isinstance(item, BranchRef):
        find_keys(item._match, keys)

    elif isinstance(item, Match):
        pass
    elif isinstance(item, Distinct):
        pass
    elif isinstance(item, PY_LITERAL_TYPES):
        pass
    elif hasattr(item, "_to_keys"):
        keys.update(item._to_keys())
    else:
        raise ValueError(f"Cannot find keys for {item}")

    return keys


class Key:
    def __init__(self, val:Any, is_group:bool = False):
        self.val = val
        self.is_group = is_group

def find_select_keys(item: Any, keys:OrderedSet[Key]|None = None, enable_primitive_key:bool = False) -> OrderedSet[Key]:
    if keys is None:
        keys = ordered_set()

    if isinstance(item, (list, tuple)):
        for it in item:
            find_select_keys(it, keys, enable_primitive_key=enable_primitive_key)

    elif isinstance(item, (Relationship, RelationshipReading)) and item._parent:
        find_select_keys(item._parent, keys)
        if item.is_many():
            keys.add( Key(item._field_refs[-1]) )

    elif isinstance(item, RelationshipRef):
        find_select_keys(item._parent, keys)
        if item._relationship.is_many():
            keys.add( Key(item._field_refs[-1]) )

    elif isinstance(item, (Relationship, RelationshipReading)):
        if item.is_many():
            for fld in item._field_refs:
                keys.add( Key(fld) )
        else:
            keys.add( Key(item._field_refs[0]) )

    elif isinstance(item, Concept):
        if not item._is_primitive() or enable_primitive_key:
            keys.add( Key(item) )

    elif isinstance(item, ConceptExpression):
        for it in item._params[1].values():
            find_select_keys(it, keys)

    elif isinstance(item, Ref):
        if isinstance(item._thing, Concept):
            if not item._thing._is_primitive() or enable_primitive_key:
                keys.add( Key(item) )
        else:
            find_select_keys(item._thing, keys)

    elif isinstance(item, TypeRef):
        pass

    elif isinstance(item, RelationshipFieldRef):
        find_select_keys(item._relationship, keys)

    elif isinstance(item, ArgumentRef):
        find_select_keys(item._arg, keys)

    elif isinstance(item, Alias):
        find_select_keys(item._thing, keys, enable_primitive_key=enable_primitive_key)

    elif isinstance(item, Aggregate):
        keys.update( Key(k, True) for k in item._group )

    elif isinstance(item, Expression):
        find_select_keys(item._params, keys)

    elif isinstance(item, Data):
        keys.add( Key(item._row_id) )

    elif isinstance(item, DataColumn):
        keys.add( Key(item._data) )

    elif isinstance(item, BranchRef):
        find_select_keys(item._match, keys)

    elif isinstance(item, Match):
        pass
    elif isinstance(item, Distinct):
        pass
    elif isinstance(item, PY_LITERAL_TYPES):
        pass
    elif hasattr(item, "_to_keys"):
        for sub in item._to_keys():
            find_select_keys(sub, keys)
    else:
        raise ValueError(f"Cannot find keys for {item}")

    return keys


#--------------------------------------------------
# Producer
#--------------------------------------------------

class Producer:
    def __init__(self, model:Model|None) -> None:
        self._id = next(_global_id)
        self._model = model

    #--------------------------------------------------
    # Infix operator overloads
    #--------------------------------------------------

    def _bin_op(self, op, left, right) -> Expression:
        res = Number.ref("res")
        return Expression(Relationship.builtins[op], left, right, res)

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
        return Expression(Relationship.builtins[op], left, right)

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
        return Match(self, other)

    def __and__(self, other) -> Fragment:
        if isinstance(other, Fragment):
            return other.where(self)
        return where(self, other)

    #--------------------------------------------------
    # in_
    #--------------------------------------------------

    def in_(self, values:list[Any]|Fragment) -> Expression:
        columns = None
        if isinstance(values, Fragment):
            return self == values
        if not isinstance(values[0], tuple):
            values = [tuple([v]) for v in values]
            columns = [f"v{i}" for i in range(len(values[0]))]
        d = data(values, columns)
        return self == d[0]

    #--------------------------------------------------
    # Relationship handling
    #--------------------------------------------------

    def _get_relationship(self, name:str) -> Relationship|RelationshipRef|RelationshipFieldRef:
        root_type:Concept = to_type(self) or Concept.builtins["Any"]
        namer = NameCache()
        cls = Relationship if root_type is Error else Property

        r = cls(
            f"{{{root_type}}} has {{{name}:Any}}",
            parent=self,
            short_name=name,
            model=self._model,
            field_refs=cast(list[Ref], [
                root_type.ref(namer.get_name(1, Relationship._sanitize_field_name(root_type._name))),
                Concept.builtins["Any"].ref(namer.get_name(2, name)),
            ]),
        )
        # if we don't know the root type, then this relationship is unresolved and we're
        # really just handing an anonymous relationship back that we expect to be resolved
        # later
        if root_type is Concept.builtins["Any"]:
            r._unresolved = True
        return r

    #--------------------------------------------------
    # dir and helpers
    #--------------------------------------------------

    def _dir_extras_from_get_relationship(self):
        # Producer._get_relationship() does not distinguish on
        # new/pre-existing, so we return nothing.
        return set()

    def _dir_extras_from_getattr(self):
        """
        Helper function for computing `__dir__`

        See Also
        --------
        :meth:`Producer.__dir__`
        """
        attributes = set()
        relationships = getattr(self, "_relationships", None)
        if relationships is not None and isinstance(relationships, dict):
            attributes.update(relationships.keys())

        attributes.update(self._dir_extras_from_get_relationship())

        return attributes

    def __dir__(self):
        """
        This method provides hints runtime autocompletion in Jupyter, IPython or similar,
        see https://docs.python.org/3/library/functions.html#dir.

        Our implementation works as follows. We get the "hardcoded" attributes using
        `default_dir`. For the dynamic ones, which are provided via `__getattr__`, we implement
        `_dir_extras_from_getattr`, the idea being that the latter returns the set of strings
        that are a "sensible" input to the former. The former often accepts any string, but
        some values would than fail during compilation, so we mimic the behaviour of
        `__getattr__` up to the point where it starts creating new objects. The `__getattr__`
        often calls `_get_relationship`, due to the virtual dispatch of Python that can belong
        to a different static type (parent or child) than the executed `__getattr__`. Hence,
        to closely mimic the behaviour, we also define `_dir_extras_from_get_relationship`
        which again returns the "sensible" inputs to `_get_relationship`.
        """

        return sorted(default_dir(self).union(self._dir_extras_from_getattr()))

    #--------------------------------------------------
    # getattr
    #--------------------------------------------------

    def __getattr__(self, name:str) -> Any:
        if name.startswith("_"):
            raise AttributeError(f"{type(self).__name__} has no attribute {name}")
        if not hasattr(self, "_relationships"):
            return super().__getattribute__(name)

        if isinstance(self, (Concept, ConceptNew)):
            concept = self._op if isinstance(self, ConceptNew) else self
            topmost_parent = concept._get_topmost_parent()
            if (concept is not Concept.builtins['Any'] and
                not concept._is_enum() and
                name not in concept._relationships and
                not concept._has_inherited_relationship(name)):

                if self._model and self._model._strict:
                    raise AttributeError(f"{self._name} has no relationship `{name}`")
                if topmost_parent is not concept and topmost_parent not in Concept.builtin_concepts:
                    topmost_parent._relationships[name] = topmost_parent._get_relationship(name)
                    rich.print(f"[red bold][Implicit Subtype Relationship][/red bold] [yellow]{concept}.{name}[/yellow] appended to topmost parent [yellow]{topmost_parent}[/yellow] instead")

        if name not in self._relationships:
            self._relationships[name] = self._get_relationship(name)
        return self._relationships[name]

    def _has_inherited_relationship(self, name:str) -> bool:
        if isinstance(self, Concept):
            for parent in self._extends:
                if not parent._is_primitive():
                    if parent._has_relationship(name):
                        return True
        return False

    def _has_relationship(self, name:str) -> bool:
        if name in self._relationships:
            return True
        return self._has_inherited_relationship(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
        elif isinstance(value, (Relationship, RelationshipReading)):
            value._parent = self
            if not value._passed_short_name:
                value._passed_short_name = name
            if name in self._relationships:
                raise ValueError(f"Cannot set attribute {name} on {type(self).__name__} a second time. Make sure to set the relationship before any usages occur")
            # update the first reading created implicitly
            if isinstance(value, Relationship):
                value._readings[0]._parent = value._parent
                value._readings[0]._passed_short_name = value._passed_short_name
            self._relationships[name] = value
        else:
            raise AttributeError(f"Cannot set attribute {name} on {type(self).__name__}")

    #--------------------------------------------------
    # ref + alias
    #--------------------------------------------------

    def ref(self, name:str|None=None) -> Ref|RelationshipRef:
        return Ref(self, name=name)

    def alias(self, name:str) -> Alias:
        return Alias(self, name)

    #--------------------------------------------------
    # Find model
    #--------------------------------------------------

    def _find_model(self, items:list[Any]) -> Model|None:
        if self._model:
            return self._model

        for item in items:
            if isinstance(item, (Producer, Fragment)) and item._model:
                self._model = item._model
                return item._model
        return None

    #--------------------------------------------------
    # Hash
    #--------------------------------------------------

    __hash__ = object.__hash__

    #--------------------------------------------------
    # _pprint
    #--------------------------------------------------

    def _pprint(self, indent:int=0) -> str:
        return str(self)

    #--------------------------------------------------
    # Fallbacks
    #--------------------------------------------------

    def select(self, *args: Any):
        raise NotImplementedError(f"`{type(self).__name__}.select` not implemented")

    def where(self, *args: Any):
        raise NotImplementedError(f"`{type(self).__name__}.where` not implemented")

    def require(self, *args: Any):
        raise NotImplementedError(f"`{type(self).__name__}.require` not implemented")

    def define(self, *args: Any):
        raise NotImplementedError(f"`{type(self).__name__}.then` not implemented")

#--------------------------------------------------
# Ref
#--------------------------------------------------

class Ref(Producer):
    def __init__(self, thing:Producer, name:str|None=None):
        super().__init__(thing._model)
        self._thing = thing
        self._name = name
        self._no_lookup = False
        self._relationships = {}

    def _dir_extras_from_get_relationship(self):
        return self._thing._dir_extras_from_getattr()

    def _get_relationship(self, name: str) -> Relationship | RelationshipRef:
        rel = getattr(self._thing, name)
        return RelationshipRef(self, rel)

    def __str__(self) -> str:
        if self._name:
            return f"{self._name}{self._id}"
        return f"{self._thing}{self._id}"

class TypeRef(Producer):
    """ A reference to the type of a Producer. """

    def __init__(self, thing:Producer):
        super().__init__(thing._model)
        self._thing = thing

    def __str__(self) -> str:
        return f"typeof({self._thing})"

class ArgumentRef(Producer):
    """ Represents a reference to an argument of an Expression.
    Useful when you need to reuse arguments in another Expression
    while maintaining a link to the original Expression during compilation.
    """

    def __init__(self, expr:Expression, arg:Producer):
        super().__init__(expr._model)
        self._expr = expr
        self._arg = arg

    def __str__(self) -> str:
        return f"{self._arg}{self._id}"

class RelationshipRef(Producer):
    def __init__(self, parent:Any, relationship:Relationship|RelationshipRef, name:str|None=None):
        super().__init__(find_model([parent, relationship]))
        self._parent = parent
        if isinstance(relationship, RelationshipRef):
            relationship = relationship._relationship
        self._relationship:Relationship = relationship
        self._field_refs = [r.ref() for r in relationship._field_refs]
        if name:
            self._field_refs[-1].name = name
        self._relationships = {}

    def _dir_extras_from_get_relationship(self):
        return self._relationship._dir_extras_from_getattr()

    def _get_relationship(self, name: str) -> Relationship|RelationshipRef|RelationshipFieldRef:
        rel = self._relationship._get_relationship(name)
        if isinstance(rel, Relationship):
            return RelationshipRef(self, rel)
        elif isinstance(rel, RelationshipFieldRef):
            return RelationshipFieldRef(self, rel._relationship, rel._field_ix)
        else:
            return RelationshipRef(self, rel)


    def __call__(self, *args: Any, **kwargs) -> Any:
        if kwargs and args:
            raise ValueError("Cannot use both positional and keyword arguments")
        if kwargs:
            # check that all fields have been provided
            clean_args = []
            for ix, field in enumerate(self._relationship._field_names):
                if field in kwargs:
                    clean_args.append(kwargs.get(field))
                if ix == 0 and self._parent:
                    continue
                if field not in kwargs:
                    raise ValueError(f"Missing argument {field}")
        else:
            clean_args = list(args)
        if len(clean_args) < self._relationship._arity():
            if self._parent:
                clean_args = [self._parent, *clean_args]
        if len(clean_args) != self._relationship._arity():
            raise ValueError(f"Expected {self._relationship._arity()} arguments, got {len(clean_args)}")
        return Expression(self._relationship, *clean_args)

    def __str__(self) -> str:
        return f"{self._parent}.{self._relationship._short_name}"

class RelationshipFieldRef(Producer):
    def __init__(self, parent:Any, relationship:Relationship|RelationshipRef|RelationshipReading, field_ix:int):
        super().__init__(find_model([relationship]))
        self._parent = parent
        if isinstance(relationship, RelationshipRef):
            relationship = relationship._relationship
        self._relationship:Relationship|RelationshipReading = relationship
        self._field_ix = field_ix
        self._relationships = {}

    @property
    def _field_ref(self) -> Ref|RelationshipRef:
        return self._relationship._field_refs[self._field_ix]

    @property
    def _concept(self) -> Concept:
        return field_to_type(self._model, self._relationship._fields[self._field_ix])

    def _dir_extras_from_get_relationship(self):
        return self._field_ref._dir_extras_from_getattr()

    def _get_relationship(self, name: str) -> Relationship | RelationshipRef:
        rel = getattr(self._field_ref, name)
        return RelationshipRef(self, rel)

    def __call__(self, arg: Any) -> Any:
        return self == arg

    def __str__(self) -> str:
        return f"{self._relationship}.{self._field_ref}"


#--------------------------------------------------
# typed dicts for annotating ref scheme hierarchy
#--------------------------------------------------

# We define a hierarchy of two dicts, one allowing its key(s) to be ommitted,
# and another which extends the first with mandatory keys.
# Up until Python 3.10, this is the only way to create a TypedDict
# which contains both mandatory and non-mandatory keys.
# Once we stop supporting Python 3.10, this can
# be simplified by using Required and NotRequired
# https://peps.python.org/pep-0655/#motivation

class RefSchemeHierarchyParentDict(TypedDict, total=False):
    mapping: Relationship
class RefSchemeHierarchyDict(RefSchemeHierarchyParentDict, total=True):
    concept: Concept
    scheme: tuple[Relationship|RelationshipReading, ...]

#--------------------------------------------------
# Concept
#--------------------------------------------------

class Concept(Producer):
    # Concept instances created for metamodel builtin types
    builtin_concepts = set()
    # The concepts from above, indexed by name
    builtins = {}

    globals = {}

    @staticmethod
    def _validate_concept_name(name: str):
        """
        Validate that a concept name matches the expected format:
        - Format A: [a-zA-Z0-9_.]+
        - Format B: [a-zA-Z0-9_.]+\\([0-9]+,[0-9]+\\) (like Decimal(38,14))
        where the leading character(s) are not underscores.
        """
        if name.startswith("_"):
            raise ValueError("Concept names cannot start with '_'")

        # Check if it matches either allowed format
        pattern_a = r'^[a-zA-Z0-9_.]+$'
        pattern_b = r'^[a-zA-Z0-9_.]+\([0-9]+,[0-9]+\)$'

        if not (re.match(pattern_a, name) or re.match(pattern_b, name)):
            raise ValueError(f"Concept name '{name}' contains invalid characters. "
                           f"Names must contain only letters, digits, dots, and underscores, "
                           f"optionally followed by precision/scale in parentheses like 'Decimal(38,14)'")

    def __init__(self, name:str, extends:list[Any] = [], model:Model|None=None, identify_by:dict[str, Any]={}):
        super().__init__(model)

        self._validate_concept_name(name)
        self._name = name
        self._relationships = {}
        self._extends : list[Concept] = []
        self._reference_schemes: list[tuple[Relationship|RelationshipReading, ...]] = []
        self._scheme_mapping:dict[Concept, Relationship] = {}

        for e in extends:
            if isinstance(e, Concept):
                self._extends.append(e)
            elif python_types_to_concepts.get(e):
                self._extends.append(python_types_to_concepts[e])
            else:
                raise ValueError(f"Unknown concept {e} in extends")

        if identify_by:
            scheme = []
            for k, v in identify_by.items():
                if python_types_to_concepts.get(v):
                    v = python_types_to_concepts[v]
                if isinstance(v, Concept):
                    setattr(self, k, Property(f"{{{self._name}}} has {{{k}:{v._name}}}", parent=self, short_name=k, model=self._model))
                elif isinstance(v, type) and issubclass(v, self._model.Enum): #type: ignore
                    setattr(self, k, Property(f"{{{self._name}}} has {{{k}:{v._concept._name}}}", parent=self, short_name=k, model=self._model))
                elif isinstance(v, Relationship):
                    self._validate_identifier_relationship(v)
                    setattr(self, k, v)
                else:
                    raise ValueError(f"identify_by must be either a Concept or Relationship: {k}={v}")
                scheme.append(getattr(self, k))
            self._add_ref_scheme(*tuple(scheme))
        self._annotations = []

    def require(self, *args: Any) -> Fragment:
        return where(self).require(*args)

    def new(self, ident: Any|None=None, **kwargs) -> ConceptNew:
        self._check_ref_scheme(kwargs)
        return ConceptNew(self, ident, kwargs)

    def filter_by(self, args: Any|None=None, **kwargs: Any) -> ConceptFilter:
        return ConceptFilter(self, args, kwargs)

    def to_identity(self, args: Any|None=None, **kwargs: Any) -> ConceptConstruct:
        self._check_ref_scheme(kwargs, shallow=True)
        return ConceptConstruct(self, args, kwargs)

    def annotate(self, *annos:Expression|Relationship|ir.Annotation) -> Concept:
        self._annotations.extend(annos)
        return self

    #--------------------------------------------------
    # Reference schemes
    #--------------------------------------------------

    def identify_by(self, *args: Relationship|RelationshipReading):
        if not args:
            raise ValueError("identify_by requires at least one relationship")
        for rel in args:
            if not isinstance(rel, (Relationship, RelationshipReading)):
                raise ValueError(f"identify_by must be called with a Relationship/RelationshipReading, got {type(rel)}")
            else:
                self._validate_identifier_relationship(rel)
        self._add_ref_scheme(*args)

    def _add_ref_scheme(self, *rels: Relationship|RelationshipReading):
        # thanks to prior validation we we can safely assume that
        # * the input types are correct due to prior validation
        # * all relationships are binary and defined on this concept

        self._reference_schemes.append(rels)

        # for every concept x every field f has at most one value y.
        # f(x,y): x -> y holds
        concept_fields = tuple([rel.__getitem__(0) for rel in rels])
        for field in concept_fields:
            concept_uc = Unique(field, model=self._model)
            require(concept_uc.to_expressions())

        # for any combination of field values there is at most one concept x.
        # f₁(x,y₁) ∧ … ∧ fₙ(x,yₙ): {y₁,…,yₙ} → {x}
        key_fields = tuple([rel.__getitem__(1) for rel in rels])
        key_uc = Unique(*key_fields, model=self._model)
        require(key_uc.to_expressions())

    def _validate_identifier_relationship(self, rel:Relationship|RelationshipReading):
        if rel._arity() != 2:
            raise ValueError("identify_by can only be applied on binary relations")
        if rel._fields[0].type_str != self._name:
            raise ValueError("For identify_by all relationships/readings must be defined on the same Concept")

    def _ref_scheme(self, shallow=False) -> tuple[Relationship, ...] | None:
        ref_schema = []
        if not shallow:
            for parent in self._extends:
                parent_schema = parent._ref_scheme()
                if parent_schema:
                    ref_schema.extend(parent_schema)
                    break
        if self._reference_schemes:
            ref_schema.extend(self._reference_schemes[0])
        return tuple(ref_schema) if ref_schema else None

    def _check_ref_scheme(self, kwargs: dict[str, Any], shallow=False):
        scheme = self._ref_scheme(shallow)
        if not scheme:
            return
        ks = [rel._short_name for rel in scheme]
        for k in ks:
            if k not in kwargs:
                raise ValueError(f"Missing argument {k} for {self._name}")

    def _ref_scheme_hierarchy(self):

        ref_schemes: list[RefSchemeHierarchyDict] = []
        for parent in self._extends:
            parent_schemes = parent._ref_scheme_hierarchy()
            if parent_schemes:
                ref_schemes.extend(parent_schemes)
                break
        if self._reference_schemes:
            ref_schemes.append({"concept": self, "scheme": self._reference_schemes[0]})

        # add mappings
        top_parent_name = ref_schemes[0]["concept"]._name if ref_schemes else None
        for ix, scheme in enumerate(ref_schemes[1:]):
            cur = scheme["concept"]
            parent = ref_schemes[ix]["concept"]
            if not self._scheme_mapping.get(parent):
                self._scheme_mapping[parent] = cur._scheme_mapping.get(parent) or Relationship(
                    f"{{{cur._name}}} to {{{top_parent_name}}}",
                    short_name=f"{cur._name}_to_{parent._name}",
                    model=self._model,
                )
            scheme["mapping"] = self._scheme_mapping[parent]

        return ref_schemes

    #--------------------------------------------------
    # Internals
    #--------------------------------------------------

    def _get_topmost_parent(self) -> Concept:
        if not self._extends:
            return self
        return self._extends[0]._get_topmost_parent()

    def _dir_extras_from_get_relationship(self):
        attributes = set()
        for parent in self._extends:
            attributes.update(parent._relationships.keys())
            attributes.update(parent._dir_extras_from_get_relationship())
        return attributes

    def _get_relationship(self, name: str) -> Relationship | RelationshipRef | RelationshipFieldRef:
        relationship = self._get_parent_relationship(self, name)
        return relationship if relationship else super()._get_relationship(name)

    def _get_parent_relationship(self, root:Concept, name: str) -> Relationship | RelationshipRef | RelationshipFieldRef | None:
        for parent in self._extends:
            if name in parent._relationships:
                return RelationshipRef(root, parent._relationships[name])
            elif not parent._is_primitive():
                return parent._get_parent_relationship(root, name)
        return None

    def _isa(self, other:Concept) -> bool:
        if self is other:
            return True
        for parent in self._extends:
            if parent._isa(other):
                return True
        return False

    def _is_primitive(self) -> bool:
        return self._isa(Primitive)

    def _is_enum(self) -> bool:
        return self._isa(Concept.builtins["Enum"])

    def _is_filter(self) -> bool:
        return False

    def __call__(self, identity:Any=None, **kwargs: Any) -> ConceptMember:
        return ConceptMember(self, identity, kwargs)

    def __str__(self):
        return self._name

#--------------------------------------------------
# ErrorConcept
#--------------------------------------------------

class ErrorConcept(Concept):
    _error_props = OrderedSet()
    _relation = None
    _overloads:dict[Concept, Relationship] = {}

    def __init__(self, name:str, extends:list[Any] = [], model:Model|None=None):
        super().__init__(name, extends, model)

    def new(self, ident: Any|None=None, **kwargs) -> ConceptNew:
        from v0.relationalai.semantics.internal import annotations as annos
        model = kwargs.get("_model") or find_model([ident, kwargs])
        if kwargs.get("_model"):
            del kwargs["_model"]

        if not ErrorConcept._relation:
            # note: explicitly declaring fields to avoid incorrect madlib lookups
            ErrorConcept._relation = Relationship(
                "{Error} has {attribute:String} with {value:Any}",
                short_name="pyrel_error_attrs",
                model=model,
                fields=[
                    Field("error", "Error", Error),
                    Field("attribute", "String", String),
                    Field("value", "Any", Concept.builtins["Any"])
                ]
            ).annotate(annos.external)
            ErrorConcept._relation._unresolved = True
        source = None
        if "_source" in kwargs:
            source = kwargs["_source"]
            del kwargs["_source"]
        else:
            source = runtime_env.get_source_pos()
        # kwargs["severity"] = "error"
        if source:
            source = source.to_source_info()
            source_id = len(errors.ModelError.error_locations)
            errors.ModelError.error_locations[source_id] = source
            kwargs["pyrel_id"] = source_id

        for k, v in kwargs.items():
            v_type = to_type(v) or python_types_to_concepts.get(type(v)) or Concept.builtins["Any"]
            if v_type and v_type not in self._overloads:
                # note: explicitly declaring fields to avoid incorrect madlib lookups
                self._overloads[v_type] = Relationship(
                    f"{{Error}} has {{attribute:String}} with {{value:{v_type._name}}}",
                    short_name="pyrel_error_attrs",
                    model=model,
                    fields=[
                        Field("error", "Error", Error),
                        Field("attribute", "String", String),
                        Field("value", "v_type._name", v_type)
                    ]
                ).annotate(annos.external)
            assert v_type is not None, f"Cannot determine type for {k}={v}"
            overload = self._overloads[v_type]
            if (model, k) not in ErrorConcept._error_props and not k.startswith("_"):
                ErrorConcept._error_props.add((model, k))
                with root_tracking(True):
                    frag = where(getattr(self, k)).define(
                        overload(self, k, getattr(self, k))
                    )
                    frag._model = model

        return super().new(ident, **kwargs)

    def __call__(self, identity: Any = None, **kwargs: Any) -> Any:
        raise ValueError("Errors must always be created with a new identity. Use Error.new(..) instead of Error(..)")

#--------------------------------------------------
# Builtin Concepts
#--------------------------------------------------

Primitive = Concept.builtins["Primitive"] = Concept("Primitive")
Error = Concept.builtins["Error"] = ErrorConcept("Error")

def _register_builtin(name):
    if name == "AnyEntity":
        c = Concept(name)
    else:
        c = Concept(name, extends=[Primitive])
    Concept.builtin_concepts.add(c)
    Concept.builtins[name] = c

# Load builtin types
for builtin in types.builtin_types:
    if isinstance(builtin, ir.ScalarType):
        _register_builtin(builtin.name)

AnyEntity = Concept.builtins["AnyEntity"]
Float = Concept.builtins["Float"]
Number = Concept.builtins["Number"]
Int64 = Concept.builtins["Int64"]
Int128 = Concept.builtins["Int128"]
# Integer aliases to Int128.
Integer = Concept.builtins["Int128"]
Hash = Concept.builtins["Hash"]
String = Concept.builtins["String"]
Bool = Concept.builtins["Bool"]
Date = Concept.builtins["Date"]
DateTime = Concept.builtins["DateTime"]

# The default Decimal type can be retrieved as "Decimal" or "Decimal(38,14)"
Decimal = Concept.builtins["Decimal"] = Concept.builtins[types.Decimal.name]

def decimal_concept(precision: int = 38, scale: int = 14) -> Concept:
    """ Get the Concept for a decimal with this precision and scale. """
    return decimal_concept_by_name(f"Decimal({precision},{scale})")

def decimal_concept_by_name(name: str) -> Concept:
    """ Get the Concept for a decimal with this name, e.g. 'Decimal(38,14)'. """
    if name not in Concept.builtins:
        # cache for reuse
        _register_builtin(name)
    return Concept.builtins[name]

def is_decimal(concept: Concept) -> bool:
    """ Check whether this concept represents a Decimal. """
    return concept._name.startswith("Decimal") and concept in Concept.builtin_concepts

# The following is a workaround for having the builtin "Int"
# but not other the builtin "Integer". The `Relationship`
# class relies upon the builtin "Integer" existing in its
# _build_inspection_fragment() method.
Concept.builtins["Int"] = Concept.builtins["Int128"]
Concept.builtins["Integer"] = Concept.builtins["Int128"]

_np_datetime = np.dtype('datetime64[ns]')
python_types_to_concepts : dict[Any, Concept] = {
    int: Concept.builtins["Int128"],
    float: Concept.builtins["Float"],
    str: Concept.builtins["String"],
    bool: Concept.builtins["Bool"],
    date: Concept.builtins["Date"],
    datetime: Concept.builtins["DateTime"],
    PyDecimal: Decimal,

    Int128Dtype(): Concept.builtins["Int128"],

    # Pandas/NumPy dtype objects
    np.dtype('int64'): Concept.builtins["Int128"],
    np.dtype('int32'): Concept.builtins["Int128"],
    np.dtype('int16'): Concept.builtins["Int128"],
    np.dtype('int8'): Concept.builtins["Int128"],
    np.dtype('uint64'): Concept.builtins["Int128"],
    np.dtype('uint32'): Concept.builtins["Int128"],
    np.dtype('uint16'): Concept.builtins["Int128"],
    np.dtype('uint8'): Concept.builtins["Int128"],
    np.dtype('float64'): Concept.builtins["Float"],
    np.dtype('float32'): Concept.builtins["Float"],
    np.dtype('bool'): Concept.builtins["Bool"],
    np.dtype('object'): Concept.builtins["String"],  # Often strings are stored as object dtype
    _np_datetime: Concept.builtins["DateTime"],

    # Pandas extension dtypes
    pd.Int64Dtype(): Concept.builtins["Int128"],
    pd.Int32Dtype(): Concept.builtins["Int128"],
    pd.Int16Dtype(): Concept.builtins["Int128"],
    pd.Int8Dtype(): Concept.builtins["Int128"],
    pd.UInt64Dtype(): Concept.builtins["Int128"],
    pd.UInt32Dtype(): Concept.builtins["Int128"],
    pd.UInt16Dtype(): Concept.builtins["Int128"],
    pd.UInt8Dtype(): Concept.builtins["Int128"],
    pd.Float64Dtype(): Concept.builtins["Float"],
    pd.Float32Dtype(): Concept.builtins["Float"],
    pd.StringDtype(): Concept.builtins["String"],
    pd.BooleanDtype(): Concept.builtins["Bool"],
}

# this map is required when we need to map standard python type string to a Concept
python_types_str_to_concepts = {
    "int": python_types_to_concepts[int],
    "float": python_types_to_concepts[float],
    "str": python_types_to_concepts[str],
    "bool": python_types_to_concepts[bool],
    "date": python_types_to_concepts[date],
    "datetime": python_types_to_concepts[datetime],
    "decimal": python_types_to_concepts[PyDecimal]
}

#--------------------------------------------------
# Relationship
#--------------------------------------------------

@dataclass()
class Field():
    name:str
    type_str:str
    type:Concept|None = None

    def __str__(self):
        return f"{self.name}:{self.type_str}"

    def __hash__(self) -> int:
        type_str = self.type._name if self.type else self.type_str
        return hash((self.name, type_str))

class Relationship(Producer):
    builtins = {}

    def __init__(self, madlib:str, parent:Producer|None=None, short_name:str="", model:Model|None=None, fields:list[Field]|None=None, field_refs:list[Ref]|None=None, ir_relation:ir.Relation|None=None):
        found_model = model or find_model(parent) or find_model(args)
        super().__init__(found_model)
        self._parent = parent
        self._madlib = madlib
        self._passed_short_name = short_name
        self._relationships = {}
        if fields is not None:
            self._fields:list[Field] = fields
        else:
            self._fields = self._parse_schema_format(madlib)
        if not self._fields and not ir_relation:
            raise ValueError(f"No fields found in relationship {self}")
        if model and model._strict:
            self._validate_fields(self._fields)
        self._ir_relation = ir_relation
        self._unresolved = False
        if field_refs is not None:
            self._field_refs = field_refs
        else:
            self._field_refs = [cast(Ref, field_to_type(found_model, field).ref(field.name)) for field in self._fields]
        for field in self._field_refs:
            field._no_lookup = True
        self._internal_constraints:set[FieldsConstraint] = set()
        self._field_names = [field.name for field in self._fields]
        self._readings = [RelationshipReading(madlib, alt_of=self, short_name=short_name, fields=self._fields, model=found_model, parent=parent)]
        self._annotations = []
        # now that the Relationship is validated, register into the model
        if found_model is not None:
            found_model.relationships.append(self)

    @property
    def _name(self):
        return self._short_name or self._madlib

    @property
    def _short_name(self):
        return self._passed_short_name or _short_name_from_madlib(self._madlib)

    def is_many(self):
        if self._arity() == 1:
            return False
        uc = Unique.to_identity(*(self[i] for i in range(self._arity() - 1)))
        return uc not in self._internal_constraints

    def _is_filter(self) -> bool:
        return self._short_name in [">", "<", "=", "!=", ">=", "<="]

    @staticmethod
    def _sanitize_field_name(name: str) -> str:
        """
        Sanitize a field name by converting to lowercase and replacing
        problematic characters with underscores. Special handling for
        precision/scale format (like Decimal(38,14)) to avoid trailing underscores.

        This ensures consistent field naming between
        relationship parsing and field reference creation.
        """
        lowered = name.lower()

        # Check if this matches the precision/scale format: word(digits,digits)
        import re
        precision_scale_pattern = r'^([a-zA-Z0-9_.]+)\(([0-9]+),([0-9]+)\)$'
        match = re.match(precision_scale_pattern, lowered)

        if match:
            # Format B: Convert Decimal(38,14) -> decimal_38_14 (no trailing underscore)
            base_name, precision, scale = match.groups()
            # First sanitize the base name part
            sanitized_base = re.sub(r"[ ,\.\|]", "_", base_name)
            return f"{sanitized_base}_{precision}_{scale}"
        else:
            # Format A: Regular sanitization, preserve original trailing underscores
            return re.sub(r"[ ,\.\(\)\|]", "_", lowered)

    def _parse_schema_format(self, format_string:str):
        # Pattern to extract fields like {Type} or {name:Type}, where Type can have precision and scale, like Decimal(38,14)
        pattern = r'\{([a-zA-Z0-9_.]+(?:\([0-9]+,[0-9]+\))?)(?::([a-zA-Z0-9_.]+(?:\([0-9]+,[0-9]+\))?))?\}'
        matches = re.findall(pattern, format_string)

        namer = NameCache()
        fields = []
        match_index = 0
        ix = 0
        for field_name, field_type in matches:
            # If no type is specified, use the field name as the type
            if not field_type:
                field_type = field_name
                # in this case, the field_name is based on the type name,
                # so sanitize to avoid, for example, ()s in decimal names,
                # and other problematic special characters.
                field_name = self._sanitize_field_name(field_name)

            ix += 1
            field_name = namer.get_name(ix, field_name)

            fields.append(Field(field_name, field_type))
            match_index +=1

        return fields

    def _dir_extras_from_get_relationship(self) -> Any:
        return self._field_refs[-1]._dir_extras_from_getattr()

    def _get_relationship(self, name: str) -> Relationship | RelationshipRef | RelationshipFieldRef:
        rel:RelationshipRef = getattr(self._field_refs[-1], name)
        return RelationshipRef(self, rel._relationship)

    def _arity(self):
        return len(self._fields)

    def _dir_extras_from_getattr(self) -> Any:
        attributes = set()
        if self._arity() > 2:
            attributes.update(self._field_names)
        attributes.update(super()._dir_extras_from_getattr())
        return attributes

    def __getattr__(self, name: str) -> Any:
        if self._arity() > 2 and name in self._field_names:
            return RelationshipFieldRef(self._parent, self, self._field_names.index(name))
        return super().__getattr__(name)

    def annotate(self, *annos:Expression|Relationship|ir.Annotation) -> Relationship:
        self._annotations.extend(annos)
        return self

    def __getitem__(self, arg:str|int|Concept) -> Any:
        return _get_relationship_item(self, arg)

    def ref(self, name:str|None=None) -> Ref|RelationshipRef:
        return RelationshipRef(self._parent, self, name=name)

    def alt(self, madlib:Any, short_name:str="", reading:RelationshipReading|None = None) -> RelationshipReading:
        if not reading:
            reading = RelationshipReading(madlib, alt_of=self, short_name=short_name, model=self._model)
        self._readings.append(reading)
        where(self(*self._field_refs)).define(
            reading._ignore_root(*reading._field_refs),
        )
        return reading

    def _is_same_relationship(self, rel:Relationship|RelationshipReading) -> bool:
        return self._id == rel._alt_of._id if isinstance(rel, RelationshipReading) else self._id == rel._id

    def _build_inspection_fragment(self):
        """
        Helper function for the inspect() and to_df() methods below,
        that generates a Fragment from the Relationship, inspect()ing
        or to_df()'ing which yields all tuples in the Relationship.
        """
        field_types = [field_to_type(self._model, field) for field in self._fields]
        field_vars = [field_type.ref() for field_type in field_types]
        return where(self(*field_vars)).select(*field_vars)

    def inspect(self):
        return self._build_inspection_fragment().inspect()

    def to_df(self):
        return self._build_inspection_fragment().to_df()

    def _validate_fields(self, fields:list[Field]):
        # Check for multiple occurrences of the same type without explicit role names
        type_occurrences = defaultdict(list)
        for field in fields:
            type_occurrences[field.type_str].append(field.name)

            if (len(type_occurrences[field.type_str]) > 1 and
                    any(name == field.type_str.lower() for name in type_occurrences[field.type_str])):
                raise ValueError(f"The type {field.type_str} occurs multiple times in '{self._madlib}'. Please "
                                 f"disambiguate by providing explicit role names for each occurrence.")

    def __call__(self, *args: Any, **kwargs) -> Any:
        return _relationship_call(self, *args, **kwargs)

    def __str__(self):
        if self._parent and self._short_name:
            return f"{self._parent}.{self._short_name}"
        return self._name

class Property(Relationship):

    def __init__(self, madlib:str, parent:Producer|None=None, short_name:str="", model:Model|None=None, fields:list[Field]|None=None, field_refs:list[Ref]|None=None, ir_relation:ir.Relation|None=None):
        super().__init__(madlib, parent, short_name, model, fields, field_refs, ir_relation)
        # for property should be an implicit unique constraint on the first n-1 fields
        uc = Unique(*(self[i] for i in range(self._arity() - 1)), model=self._model)
        require(uc.to_expressions())


class RelationshipReading(Producer):

    def __init__(self, madlib:str, alt_of:Relationship, short_name:str, fields:list[Field]|None=None, model:Model|None=None, parent:Producer|None=None,):
        found_model = model or find_model(parent)
        super().__init__(found_model)
        self._parent = parent
        self._alt_of = alt_of
        self._madlib = madlib
        self._passed_short_name = short_name
        if fields is not None:
            self._fields:list[Field] = fields
        else:
            self._fields = alt_of._parse_schema_format(madlib)
        if Counter(self._fields) != Counter(alt_of._fields):
            raise ValueError(
                f"Invalid alternative relationship. The alternative group of used fields ({', '.join(str(f) for f in self._fields)}) does not match with the original ({', '.join(str(f) for f in alt_of._fields)})")
        self._field_refs = [alt_of[f.name]._field_ref for f in self._fields]
        self._field_names = [field.name for field in self._fields]
        self._relationships = {}
        self._annotations = []

    def is_many(self):
        if self._arity() == 1:
            return False
        uc = Unique.to_identity(*(self[i] for i in range(self._arity() - 1)))
        return uc not in self._alt_of._internal_constraints

    def _arity(self):
        return len(self._fields)

    def annotate(self, *annos:Expression|Relationship|ir.Annotation) -> RelationshipReading:
        self._annotations.extend(annos)
        return self

    @property
    def _name(self):
        return self._short_name or self._madlib

    @property
    def _short_name(self):
        return self._passed_short_name or _short_name_from_madlib(self._madlib)

    def _ignore_root(self, *args, **kwargs):
        expr = self(*args, **kwargs)
        expr._ignore_root = True
        return expr

    def _dir_extras_from_get_relationship(self) -> Any:
        return self._field_refs[-1]._dir_extras_from_getattr()

    def _get_relationship(self, name: str) -> Relationship | RelationshipRef | RelationshipFieldRef:
        rel:RelationshipRef = getattr(self._field_refs[-1], name)
        return RelationshipRef(self, rel._relationship)

    def _dir_extras_from_getattr(self) -> Any:
        attributes = set()
        if self._arity() > 2:
            attributes.update(self._field_names)
        attributes.update(self._alt_of._relationships.keys())
        attributes.update(self._dir_extras_from_get_relationship())
        return attributes

    def _is_same_relationship(self, rel:Relationship|RelationshipReading) -> bool:
        return self._alt_of._id == rel._alt_of._id if isinstance(rel, RelationshipReading) else self._alt_of._id == rel._id

    def __getattr__(self, name) -> Any:
        if not name.startswith("_"):
            if self._arity() > 2 and name in self._field_names:
                return RelationshipFieldRef(self._parent, self, self._field_names.index(name))
            if name not in self._relationships:
                self._relationships[name] = self._get_relationship(name)
            return self._relationships[name]
        return super().__getattr__(name)

    def __getitem__(self, arg: str | int | Concept) -> Any:
        return _get_relationship_item(self, arg)

    def __call__(self, *args: Any, **kwargs) -> Any:
        return _relationship_call(self, *args, **kwargs)

    def __str__(self):
        if self._parent and self._short_name:
            return f"{self._parent}.{self._short_name}"
        return self._name

def _short_name_from_madlib(madlib:Any) -> str:
    # Replace curly braces, colons, and spaces with underscores.
    # Then strip leading/trailing underscores.
    return re.sub(r"[{}: ]", "_", str(madlib)).strip("_")

def _get_relationship_item(rel:Relationship|RelationshipReading, arg:Any) -> Any:
    if isinstance(arg, int):
        if arg < 0:
            raise ValueError(f"Position should be positive, got {arg}")
        if rel._arity() <= arg:
            raise ValueError(f"Relationship '{rel._name}' has only {rel._arity()} fields")
        return RelationshipFieldRef(rel._parent, rel, arg)
    elif isinstance(arg, str):
        if arg not in rel._field_names:
            raise ValueError(f"Relationship '{rel._name}' has only {rel._field_names} fields")
        return RelationshipFieldRef(rel._parent, rel, rel._field_names.index(arg))
    elif isinstance(arg, Concept):
        return _get_relationship_field_ref(rel, arg)
    elif isinstance(arg, type) and rel._model is not None and issubclass(arg, rel._model.Enum):
        return _get_relationship_field_ref(rel, arg._concept)
    else:
        raise ValueError(f"Unknown argument {arg}")

def _get_relationship_field_ref(rel:Relationship|RelationshipReading, concept:Concept) -> Any:
    result: RelationshipFieldRef | None = None
    for idx, ref in enumerate(rel._field_refs):
        if result is None and ref._thing._id == concept._id:
            result = RelationshipFieldRef(rel._parent, rel, idx)
        else:
            if ref._thing._id == concept._id:
                raise ValueError(
                    f"Ambiguous reference to the field: '{concept._name}' presented in more than one field. Use reference by name or position instead")
    if result is None:
        raise ValueError(f"Relationship '{rel._name}' does not have '{concept._name}' as a field")
    return result

def _relationship_call(rel:Relationship|RelationshipReading, *args: Any, **kwargs) -> Any:
    if kwargs and args:
        raise ValueError("Cannot use both positional and keyword arguments")
    if kwargs:
        # check that all fields have been provided
        clean_args = []
        for ix, field in enumerate(rel._field_names):
            if field in kwargs:
                clean_args.append(kwargs.get(field))
            if ix == 0 and rel._parent:
                continue
            if field not in kwargs:
                raise ValueError(f"Missing argument {field}")
    else:
        clean_args = list(args)
    if len(clean_args) < rel._arity():
        if rel._parent:
            clean_args = [rel._parent, *clean_args]
    if len(clean_args) != rel._arity():
        raise ValueError(f"Expected {rel._arity()} arguments, got {len(clean_args)}: {rel}")
    return Expression(rel, *clean_args)

#--------------------------------------------------
# Builtin Relationships
#--------------------------------------------------

for builtin in builtins.builtin_relations + builtins.builtin_annotations:
    fields = []
    for field in builtin.fields:
        field_type = re.sub(r'[\[\{\(]', '', str(field.type)).strip()
        field_type = str(field.type).strip()
        fields.append(f"{field.name}:{field_type}")
    args = ' '.join([f"{{{f}}}" for f in fields])
    Relationship.builtins[builtin.name] = Relationship(
        f"{builtin.name} {args}",
        parent=None,
        short_name=builtin.name,
        ir_relation=builtin,
    )

RawSource = Relationship.builtins["raw_source"]

#--------------------------------------------------
# Expression
#--------------------------------------------------

infix_ops = ["+", "-", "*", "/", "//", "^", "%", ">", ">=", "<", "<=", "=", "!="]
constraints_ops = [builtins.unique.name, builtins.exclusive.name, builtins.anyof.name]

class Expression(Producer):
    def __init__(self, op:Relationship|RelationshipReading|Concept, *params:Any):
        super().__init__(op._model or find_model(params))
        self._op = op
        self._params = params
        self._ignore_root = False
        self._source = runtime_env.get_source_pos()

    def __str__(self):
        return f"({self._op} {' '.join(map(str, self._params))})"

    def _pprint(self, indent:int=0) -> str:
        if self._op._name in infix_ops:
            a, b = self._params[0], self._params[1]
            return f"{' ' * indent}{a} {self._op} {b}"
        elif self._op._name in constraints_ops:
            args = []
            for param in flatten(self._params, True):
                args.append(f"{param._relationship}[\"{param._field_ref._name}\"]" if isinstance(param, RelationshipFieldRef) else str(param))
            return f"{' ' * indent}{self._op}({', '.join([str(param) for param in args])})"
        return f"{' ' * indent}{self._op}({' '.join(map(str, self._params))})"

    def _dir_extras(self):
        attributes = set()
        last = self._params[-1]
        if isinstance(self._op, (Relationship, RelationshipRef)) and isinstance(last, Concept):
            # lookup the last concept in the relationship, and then lookup the attribute in it
            concept = self._op.__getitem__(last)
            attributes.update(dir(concept))
        return attributes

    def _arg_ref(self, idx:int) -> ArgumentRef:
        if idx < 0:
            raise ValueError(f"Argument index should be positive, got {idx}")
        if len(self._params) <= idx:
            raise ValueError(f"Expression '{self.__str__()}' has only {len(self._params)} arguments")
        param = self._params[idx]
        # if param is an Expression then refer the last param of this expression
        return ArgumentRef(self, param._params[-1] if isinstance(param, Expression) else param)

    def __getattr__(self, name: str):
        last = self._params[-1]
        if isinstance(self._op, (Relationship, RelationshipRef)) and isinstance(last, Concept):
            # lookup the last concept in the relationship, and then lookup the attribute in it
            concept = self._op.__getitem__(last)
            return getattr(concept, name)
        raise AttributeError(f"Expression has no attribute {name}")

class ConceptExpression(Expression):
    def __init__(self, con:Concept, identity:Any, kwargs:dict[str, Any]):
        super().__init__(con, identity, kwargs)
        for k, _ in kwargs.items():
            # make sure to create the properties being referenced
            getattr(self._op, k)
        self._relationships = {}

        _remove_roots([v for v in kwargs.values() if isinstance(v, Producer)])

    def _construct_args(self, scheme=None) -> dict[Relationship|Concept, Any]:
        args = {}
        scheme = scheme or self._op._ref_scheme()
        [ident, kwargs] = self._params
        if scheme:
            for rel in scheme:
                args[rel] = kwargs[rel._short_name]
        else:
            for k, v in kwargs.items():
                atr = getattr(self._op, k)
                if atr:
                    args[atr] = v
            if ident:
                args[self._op] = ident
        return args

    def _dir_extras_from_get_relationship(self):
        return self._op._dir_extras_from_getattr()

    def _get_relationship(self, name: str) -> Relationship|RelationshipRef:
        parent_rel = getattr(self._op, name)
        return RelationshipRef(self, parent_rel)

    def _dir_extras_from_getattr(self):
        return Producer._dir_extras_from_getattr(self)

    def __getattr__(self, name: str):
        return Producer.__getattr__(self, name)

class ConceptMember(ConceptExpression):
    def __init__(self, con:Concept, identity:Any, kwargs:dict[str, Any]):
        super().__init__(con, identity, kwargs)
        if identity is None:
            class_name = con._name
            raise ValueError(f"Adding or looking up an instance of Concept requires an identity. If you want to create a new identity, use {class_name}.new(..)")
        # TODO: when we do reference schemes, the identity might be
        # in a combination of kwargs rather than in the positionals


class ConceptNew(ConceptExpression):
    def __str__(self):
        return f"({self._op}.new {' '.join(map(str, self._params))})"


class ConceptConstruct(ConceptExpression):
    pass

class ConceptFilter(ConceptExpression):
    pass

#--------------------------------------------------
# TupleArg
#--------------------------------------------------

# There are some special relations that require an actual tuple as
# an argument. We want to differentiate that from a case where a user
# _accidentally_ passes a tuple as an argument.

class TupleArg(tuple):
    def _compile_lookup(self, compiler:Compiler, ctx:CompilerContext):
        return TupleArg(flatten([compiler.lookup(item, ctx) for item in self]))

#--------------------------------------------------
# Aggregate
#--------------------------------------------------

class Aggregate(Producer):
    def __init__(self, op:Relationship, *args: Any):
        super().__init__(op._model or find_model(args))
        self._op = op
        self._args = args
        _remove_roots(args)
        self._group = []
        self._where = where()

    def where(self, *args: Any) -> Aggregate:
        new = self.clone()
        if not new._model:
            new._model = find_model(args)
        new._where = new._where.where(*args)
        return new

    def per(self, *args: Any) -> Aggregate:
        new = self.clone()
        if not new._model:
            new._model = find_model(args)
        new._group.extend(args)
        return new

    def clone(self) -> Aggregate:
        clone = Aggregate(self._op, *self._args)
        clone._group = self._group.copy()
        clone._where = self._where
        return clone

    def _dir_extras_from_getattr(self):
        return set()

    def __getattr__(self, name: str):
        raise AttributeError(f"Expression has no attribute {name}")

    def __str__(self):
        args = ', '.join(map(str, self._args))
        group = ', '.join(map(str, self._group))
        where = ""
        if group:
            group = f" (per {group})"
        if self._where._where:
            items = ', '.join(map(str, self._where._where))
            where = f" (where {items})"
        return f"({self._op} {args}{group}{where})"

class Group():
    def __init__(self, *args: Any):
        self._group = args

    def __str__(self):
        args = ', '.join(map(str, self._group))
        return f"(per {args})"

    #--------------------------------------------------
    # Agg funcs
    #--------------------------------------------------

    def count(self, *args: Any) -> Aggregate:
        return count(*args).per(*self._group)

    def sum(self, *args: Any) -> Aggregate:
        return sum(*args).per(*self._group)

    def avg(self, *args: Any) -> Aggregate:
        return avg(*args).per(*self._group)

    def min(self, *args: Any) -> Aggregate:
        return min(*args).per(*self._group)

    def max(self, *args: Any) -> Aggregate:
        return max(*args).per(*self._group)

#--------------------------------------------------
# Aggregate builtins
#--------------------------------------------------

def per(*args: Any) -> Group:
    return Group(*args)

def count(*args: Any) -> Aggregate:
    return Aggregate(Relationship.builtins["count"], *args)

def sum(*args: Any) -> Aggregate:
    return Aggregate(Relationship.builtins["sum"], *args)

def avg(*args: Any) -> Aggregate:
    return Aggregate(Relationship.builtins["avg"], *args)

def min(*args: Any) -> Aggregate:
    return Aggregate(Relationship.builtins["min"], *args)

def max(*args: Any) -> Aggregate:
    return Aggregate(Relationship.builtins["max"], *args)

def experimental_warning(feature: str):
    rich.print(f"[yellow]Warning:[/yellow] Early access feature '[red]{feature}[/red]' is not yet stable.", file=sys.stderr)

class RankOrder():
    ASC = True
    DESC = False

    def __init__(self, is_asc:bool, *args: Any):
        self._is_asc = is_asc
        self._args = args

    def __str__(self):
        return f"({'asc' if self._is_asc else 'desc'} {', '.join(map(str, self._args))})"

def asc(*args: Any):
    experimental_warning("asc")
    return RankOrder(True, *args)

def desc(*args: Any):
    experimental_warning("desc")
    return RankOrder(False, *args)

def rank(*args: Any) -> Aggregate:
    experimental_warning("rank")
    # A relation is needed further down the pipeline, so we create a dummy one here.
    dummy_ir_relation = f.relation("rank", [f.field("result", types.Int128)])
    dummy_relation = Relationship(dummy_ir_relation.name, ir_relation=dummy_ir_relation)
    return Aggregate(dummy_relation, *args)

#--------------------------------------------------
# Alias
#--------------------------------------------------

class Alias(Producer):
    def __init__(self, thing:Producer, name:str):
        super().__init__(thing._model)
        self._thing = thing
        self._name = name
        _remove_roots([thing])

    def __str__(self) -> str:
        return f"{self._thing} as {self._name}"

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            raise AttributeError(f"Cannot set attribute {name} on {type(self).__name__}")

#--------------------------------------------------
# Match
#--------------------------------------------------

class BranchRef(Producer):
    def __init__(self, match:Match, ix:int):
        super().__init__(match._model)
        self._match = match
        self._ix = ix

    def __str__(self):
        return f"{self._match}#{self._ix}"

class Match(Producer):
    def __init__(self, *args: Any):
        super().__init__(find_model(args))
        self._args = list(self._flatten_args(args))
        if any(isinstance(arg, Fragment) and arg._is_effect() for arg in self._args):
            _add_root(self)
        _remove_roots(args)

        # check for validity
        is_select = None
        ret_count = 0
        for arg in self._args:
            if isinstance(arg, Fragment) and arg._is_effect():
                if is_select:
                    raise ValueError("Cannot mix expression and effect clauses in a match")
                is_select = False
            elif isinstance(arg, Fragment) and not arg._is_effect():
                if is_select is False:
                    raise ValueError("Cannot mix effect and expression clauses in a match")
                is_select = True
                if ret_count == 0:
                    ret_count = len(arg._select)
                elif ret_count != len(arg._select):
                    raise ValueError("All clauses must have the same number of return values")
            elif isinstance(arg, PY_LITERAL_TYPES):
                if is_select is False:
                    raise ValueError("Cannot mix then and select clauses in a match")
                is_select = True
                if ret_count == 0:
                    ret_count = 1
                elif ret_count != 1:
                    raise ValueError("All clauses must have the same number of return values")
            elif isinstance(arg, Expression) or isinstance(arg, Aggregate):
                if is_select is None:
                    is_select = True
                    if not arg._op._is_filter():
                        ret_count = 1
            elif isinstance(arg, Relationship) or isinstance(arg, Ref):
                if is_select is None:
                    is_select = True
                    ret_count = 1

        self._is_select = is_select
        self._ret_count = ret_count
        self._source = runtime_env.get_source_pos()

    def _flatten_args(self, args):
        for arg in args:
            if isinstance(arg, Match):
                for sub_arg in arg._args:
                    yield sub_arg
            else:
                yield arg

    def __iter__(self):
        for ix in range(self._ret_count):
            yield BranchRef(self, ix)

    def __str__(self):
        return " | ".join(map(str, self._args))

#--------------------------------------------------
# Union
#--------------------------------------------------

class Union(Match):
    def __str__(self):
        return f"union({', '.join(map(str, self._args))})"

def union(*args: Any) -> Union:
    if len(args) == 1:
        return args[0]
    return Union(*args)

#--------------------------------------------------
# Negation
#--------------------------------------------------

class Not():
    def __init__(self, *args: Any):
        self._args = args
        self._model = find_model(args)
        _remove_roots(args)

    def clone(self) -> Not:
        clone = type(self)(*self._args)
        return clone

    def __or__(self, other) -> Match:
        return Match(self, other)

    def __and__(self, other) -> Fragment:
        if isinstance(other, Fragment):
            return other.where(self)
        return where(self, other)

    def __str__(self):
        args_str = '\n    '.join(map(str, self._args))
        return f"(not {args_str})"

def not_(*args: Any) -> Not:
    return Not(*args)

#--------------------------------------------------
# Distinct
#--------------------------------------------------

class Distinct():
    def __init__(self, *args: Any):
        self._args = args
        self._model = find_model(args)
        _remove_roots(args)

def distinct(*args: Any) -> Distinct:
    return Distinct(*args)

#--------------------------------------------------
# Enum
#--------------------------------------------------

def create_enum_class(model: Model):

    class ModelEnumMeta(EnumMeta):
        _concept: Concept
        def __setattr__(self, name: str, value: Any) -> None:
            if name.startswith("_") or isinstance(value, self):
                super().__setattr__(name, value)
            elif isinstance(value, (Relationship, RelationshipReading)):
                value._parent = self._concept
                if not value._passed_short_name:
                    value._passed_short_name = name
                if name in self._concept._relationships:
                    raise ValueError(
                        f"Cannot set attribute {name} on {type(self).__name__} a second time. Make sure to set the relationship before any usages occur")
                self._concept._relationships[name] = value
            else:
                raise AttributeError(f"Cannot set attribute {name} on {type(self).__name__}")

    class ModelEnum(Enum, metaclass=ModelEnumMeta):
        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)
            # this is voodoo black magic that is doing meta meta programming where
            # we are plugging into anytime a new subtype of this class is created
            # and then creating a concept to represent the enum. This happens both
            # when you do `class Foo(Enum)` and when you do `Enum("Foo", [a, b, c])`
            c = model.Concept(
                cls.__name__,
                extends=[Concept.builtins["Enum"]],
                identify_by={"name": Concept.builtins["String"]}
            )
            cls._concept = model.enum_concept[cls] = c
            model.enums[cls.__name__] = cls
            cls._has_inited_members = False

        # Python 3.10 doesn't correctly populate __members__ by the time it calls
        # __init_subclass__, so we need to initialize the members lazily when we
        # encounter the enum for the first time.
        def _init_members(self):
            if self._has_inited_members:
                return
            cls = self.__class__
            c = cls._concept
            # Add the name and value attributes to the hashes we create for the enum
            members = [
                c.new(name=name, value=value.value)
                for name, value in cls.__members__.items()
            ]
            with root_tracking(True):
                model.define(*members)
            cls._has_inited_members = True

        def _compile_lookup(self, compiler:Compiler, ctx:CompilerContext):
            self._init_members()
            concept = getattr(self.__class__, "_concept")
            return compiler.lookup(concept.new(name=self.name), ctx)

        @classmethod
        def lookup(cls, value:Producer|str):
            concept = cls._concept
            return concept.new(name=value)

    return ModelEnum

#--------------------------------------------------
# Data
#--------------------------------------------------

class DataColumn(Producer):
    def __init__(self, data:Data, _type, name:str):
        self._data = data
        self._type = _type
        self._name = name if isinstance(name, str) else f"v{name}"
        if pd.api.types.is_datetime64_any_dtype(_type):
            _type = _np_datetime
        # dates are objects in pandas
        elif pd.api.types.is_object_dtype(_type) and self._is_date_column():
            _type = date
        self._ref = python_types_to_concepts[_type].ref(self._name)

    def _is_date_column(self) -> bool:
        sample = self._data._data[self._name].dropna()
        if sample.empty:
            return False
        sample_value = sample.iloc[0]
        return isinstance(sample_value, date) and not isinstance(sample_value, datetime)

    def __str__(self):
        return f"DataColumn({self._name}, {self._type})"

class Data(Producer):
    def __init__(self, data:DataFrame):
        super().__init__(None)
        self._data = data
        self._relationships = {}
        self._cols : list[DataColumn] = []
        self._row_id = Integer.ref("row_id")
        for col in data.columns:
            t = data[col].dtype
            self._cols.append(DataColumn(self, t, col))
            self._relationships[col] = self._cols[-1]

    def into(self, concept:Concept, keys:list[str]=[]):
        if keys:
            new = concept.to_identity(**{k.lower(): getattr(self, k) for k in keys})
        else:
            new = concept.to_identity(self._row_id)
        where(self, new).define(
            concept(new),
            *[getattr(concept, col._name)(new, col) for col in self._cols]
        )

    def __getitem__(self, item: str|int) -> DataColumn:
        if isinstance(item, int):
            return self._cols[item]
        if item in self._relationships:
            return self._relationships[item]
        raise KeyError(f"Data has no column {item}")

    def _dir_extras_from_get_relationship(self):
        return set()

    def _get_relationship(self, name: str) -> Relationship | RelationshipRef | RelationshipFieldRef:
        raise AttributeError(f"Data has no attribute {name}")

    def __str__(self):
        return f"Data({len(self._data)} rows, [{', '.join([str(c) for c in self._cols])}])"

    def __hash__(self):
        return hash(self._id)

def _to_df(data: DataFrame | list[tuple] | list[dict], columns:list[str]|None) -> DataFrame:
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

def data(data:DataFrame|list[tuple]|list[dict], columns:list[str]|None=None) -> Data:
    return Data(_to_df(data, columns))

#--------------------------------------------------
# Constraints
#--------------------------------------------------
class Constraint:
    """Base class for constraints"""

    def __init__(self, model:Model|None=None):
        self._model = model or find_model(fields)
        if self._model:
            self._model.constraints.add(self)

    @property
    def _id(self):
        """Returns unique id for this constraint"""
        raise NotImplementedError(f"`{type(self).__name__}._id` not implemented")

    @property
    def _relationship(self) -> Relationship:
        """Returns builtin relationship for this constraint"""
        raise NotImplementedError(f"`{type(self).__name__}._relationship` not implemented")

    def to_expressions(self) -> tuple[Expression]:
        """Returns Expressions for this constraint"""
        raise NotImplementedError(f"`{type(self).__name__}.to_expressions` not implemented")

    def __eq__(self, other):
        if isinstance(other, Constraint):
            return self._id == other._id
        return False

    def __hash__(self):
        return hash(self._id)

class FieldsConstraint(Constraint):

    def __init__(self, *fields: RelationshipFieldRef, model:Model|None=None):
        self._init_constraint(*fields)
        super().__init__(model)

    def _init_constraint(self, *fields: RelationshipFieldRef) -> None:
        self._fields = fields
        ids = [field._field_ref._id for field in fields]
        ids.sort()  # ensures order doesn't matter
        self._stable_id = f'{type(self).__name__}:{ids}'

    @property
    def _id(self):
        return self._stable_id

    def _to_field_expressions(self, fields: tuple[RelationshipFieldRef, ...]) -> Expression:
        return Expression(self._relationship, TupleArg(fields))

    @classmethod
    def to_identity(cls, *fields: RelationshipFieldRef):
        obj = cls.__new__(cls)
        obj._init_constraint(*fields)
        return obj

class Unique(FieldsConstraint):

    def __init__(self, *fields: RelationshipFieldRef, model:Model|None=None):
        first_field_rel = fields[0]._relationship
        self._internal = all(first_field_rel._is_same_relationship(f._relationship) for f in fields[1:])
        super().__init__(*fields, model=model)
        if self._internal:
            relationship = first_field_rel._alt_of if isinstance(first_field_rel, RelationshipReading) else first_field_rel
            relationship._internal_constraints.add(self)

    def internal(self) -> bool:
        return self._internal

    def to_expressions(self) -> tuple[Expression]:
        if self.internal():
            expressions = []
            rel = self._fields[0]._relationship
            relationship = rel._alt_of if isinstance(rel, RelationshipReading) else rel
            # create Expression from the relationship
            expressions.append(self._to_field_expressions(self._find_fields(relationship)))
            # skip the first implicitly created reading and create Expressions for all other readings
            for reading in relationship._readings[1:]:
                expressions.append(self._to_field_expressions(self._find_fields(reading)))
            return tuple(expressions)
        else:
            return (self._to_field_expressions(self._fields),)

    @property
    def _relationship(self) -> Relationship:
        return Relationship.builtins[builtins.unique.name]

    def _find_fields(self, rel:Relationship|RelationshipReading) -> tuple[RelationshipFieldRef]:
        rel_fields = []
        for field in self._fields:
            assert isinstance(field._field_ref, Ref) and isinstance(field._field_ref._name, str)
            rel_fields.append(rel[field._field_ref._name])
        return tuple(rel_fields)

class SubtypeConstraint(Constraint):

    def __init__(self, *concepts: Concept, model:Model|None=None):
        if len(concepts) < 2:
            raise ValueError("Invalid subtype constraint. A constraint should hold at least 2 concepts")
        first = concepts[0]
        first_super_types = [super_type._id for super_type in first._extends]
        for c in concepts:
            if len(c._extends) == 0:
                raise ValueError(f"Invalid subtype constraint. '{c}' is not a subtype")
            c_super_types = [super_type._id for super_type in c._extends]
            if first_super_types != c_super_types:
                raise ValueError(f"Invalid subtype constraint. '{first}' and '{c}' must have the same parents")
        self._concepts = concepts
        ids = [c._id for c in concepts]
        ids.sort()  # ensures order doesn't matter
        self._stable_id = f'{type(self).__name__}:{ids}'
        super().__init__(model)

    @property
    def _id(self):
        return self._stable_id

    def to_expressions(self) -> tuple[Expression]:
        return (Expression(self._relationship, TupleArg(self._concepts)),)

class Exclusive(SubtypeConstraint):

    def __init__(self, *concepts: Concept, model:Model|None=None):
        super().__init__(*concepts, model=model)

    @property
    def _relationship(self) -> Relationship:
        return Relationship.builtins[builtins.exclusive.name]

class Anyof(SubtypeConstraint):

    def __init__(self, *concepts: Concept, model:Model|None=None):
        super().__init__(*concepts, model=model)

    @property
    def _relationship(self) -> Relationship:
        return Relationship.builtins[builtins.anyof.name]

#--------------------------------------------------
# Fragment
#--------------------------------------------------

class Fragment():
    def __init__(self, parent:Fragment|None=None, model:Model|None=None):
        self._id = next(_global_id)
        self._select = []
        self._where = []
        self._require = []
        self._define = []
        self._order_by = []
        self._limit = 0
        self._model = parent._model if parent else model
        self._parent = parent
        self._source = runtime_env.get_source_pos()
        self._is_export = False
        self._meta = {}
        self._annotations = []
        if parent:
            self._select.extend(parent._select)
            self._where.extend(parent._where)
            self._require.extend(parent._require)
            self._define.extend(parent._define)
            self._order_by.extend(parent._order_by)
            self._limit = parent._limit
            self._meta.update(parent._meta)

    def _add_items(self, items:PySequence[Any], to_attr:list[Any]):
        # TODO: ensure that you are _either_ a select, require, or then
        # not a mix of them
        _remove_roots(items)
        to_attr.extend(items)

        if self._define or self._require:
            if self._parent:
                _remove_roots([self._parent])
            _add_root(self)

        if not self._model:
            self._model = find_model(items)
        return self

    def where(self, *args: Any) -> Fragment:
        f = Fragment(parent=self)
        return f._add_items(args, f._where)

    def select(self, *args: Any) -> Fragment:
        # Check for Not instances in select arguments (including nested)
        def _contains_not(item: Any) -> bool:
            if isinstance(item, Not):
                return True
            elif isinstance(item, (Match, Union)):
                return any(_contains_not(arg) for arg in item._args)
            elif isinstance(item, Fragment):
                # Check all fragment components for not_
                return (
                    any(_contains_not(arg) for arg in item._select)
                    or any(_contains_not(arg) for arg in item._require)
                    or any(_contains_not(arg) for arg in item._define)
                    or any(_contains_not(arg) for arg in item._order_by)
                )
            elif isinstance(item, Expression):
                return any(_contains_not(param) for param in item._params)
            elif isinstance(item, Aggregate):
                return (
                    any(_contains_not(arg) for arg in item._args)
                    or any(_contains_not(arg) for arg in item._group)
                    or _contains_not(item._where)
                )
            elif isinstance(item, Group):
                return any(_contains_not(arg) for arg in item._group)
            elif isinstance(item, (list, tuple)):
                return any(_contains_not(subitem) for subitem in item)
            else:
                return False

        for arg in args:
            if _contains_not(arg):
                raise ValueError("`not_` is not allowed in `select` fragments")

        f = Fragment(parent=self)
        return f._add_items(args, f._select)

    def require(self, *args: Any) -> Fragment:
        f = Fragment(parent=self)
        # todo: find a better way to pass multi Expressions to require
        return f._add_items(tuple(flatten(args)), f._require)

    def define(self, *args: Any) -> Fragment:
        f = Fragment(parent=self)
        return f._add_items(args, f._define)

    def order_by(self, *args: Any) -> Fragment:
        experimental_warning("order_by")
        f = Fragment(parent=self)
        return f._add_items(args, f._order_by)

    def limit(self, n:int) -> Fragment:
        experimental_warning("limit")
        f = Fragment(parent=self)
        f._limit = n
        return f

    def meta(self, **kwargs: Any) -> Fragment:
        """Add metadata to the query.

        Metadata can be used for debugging and observability purposes.

        Args:
            **kwargs: Metadata key-value pairs

        Returns:
            Fragment: Returns self for method chaining

        Example:
            select(Person.name).meta(workload_name="test", priority=1, enabled=True)
        """
        if not kwargs:
            raise ValueError("meta() requires at least one argument")

        self._meta.update(kwargs)
        return self


    def annotate(self, *annos:Expression|Relationship|ir.Annotation) -> Fragment:
        self._annotations.extend(annos)
        return self

    #--------------------------------------------------
    # helpers
    #--------------------------------------------------

    def _is_effect(self) -> bool:
        return bool(self._define or self._require or (self._parent and self._parent._is_effect()))

    def _is_where_only(self) -> bool:
        return not self._select and not self._define and not self._require and not self._order_by

    #--------------------------------------------------
    # And/Or
    #--------------------------------------------------

    def __or__(self, other) -> Match:
        return Match(self, other)

    def __and__(self, other) -> Fragment:
        if isinstance(other, Fragment):
            return other.where(self)
        return where(self, other)

    #--------------------------------------------------
    # Stringify
    #--------------------------------------------------

    def __str__(self):
        sections = []
        if self._select:
            select = '\n    '.join(map(str, self._select))
            sections.append(f"(select\n    {select})")
        if self._where:
            where = '\n    '.join(map(str, self._where))
            sections.append(f"(where\n    {where})")
        if self._require:
            require = '\n    '.join(map(str, self._require))
            sections.append(f"(require\n    {require})")
        if self._define:
            effects = '\n    '.join(map(str, self._define))
            sections.append(f"(then\n    {effects})")
        if self._order_by:
            order_by = '\n    '.join(map(str, self._order_by))
            sections.append(f"(order_by\n    {order_by})")
        if self._limit:
            sections.append(f"(limit {self._limit})")

        return "\n".join(sections)

    #--------------------------------------------------
    # Execute
    #--------------------------------------------------

    def __iter__(self):
        # Iterate over the rows of the fragment's results
        return self.to_df().itertuples(index=False).__iter__()

    def inspect(self):
        # @TODO what format? maybe ignore row indices?
        print(self.to_df(in_inspect=True))

    def to_df(self, in_inspect:bool=False):
        """Convert the fragment's results to a pandas DataFrame."""
        # @TODO currently this code assumes a Rel executor; should dispatch based on config

        # If there are no selects, then there are no results to return
        if not self._select:
            return DataFrame()

        qb_model = self._model or Model("anon")
        ir_model = qb_model._to_ir()
        self._source = runtime_env.get_source_pos()
        # @TODO for now we set tag to None but we need to work out how to properly propagate user-provided tag here
        with debugging.span("query", tag=None, dsl=str(self), **with_source(self), meta=self._meta) as query_span:
            query_task = qb_model._compiler.fragment(self)
            results = qb_model._to_executor().execute(ir_model, query_task, meta=self._meta)
            query_span["results"] = results
            # For local debugging mostly
            dry_run = qb_model._dry_run or bool(qb_model._config.get("compiler.dry_run", False))
            inspect_df = bool(qb_model._config.get("compiler.inspect_df", False))
            if not in_inspect and not dry_run and inspect_df:
                print(results)
            return results

    def to_snowpark(self):
        """
            Convert the fragment's results to a snowflake DataFrame.
            `snowflake.snowpark.DataFrame` represents a lazily-evaluated relational dataset.
            The computation is not performed until you call a method that performs an action (e.g. collect(), to_pandas()).
        """
        # If there are no selects, then there are no results to return
        if not self._select:
            return SnowparkDataFrame()

        qb_model = self._model or Model("anon")
        clone = Fragment(parent=self)
        clone._is_export = True
        ir_model = qb_model._to_ir()
        clone._source = runtime_env.get_source_pos()
        # @TODO for now we set tag to None but we need to work out how to properly propagate user-provided tag here
        with debugging.span("query", tag=None, dsl=str(clone), **with_source(clone), meta=clone._meta) as query_span:
            query_task = qb_model._compiler.fragment(clone)
            results = qb_model._to_executor().execute(ir_model, query_task, format="snowpark", meta=clone._meta)
            query_span["alt_format_results"] = results
            return results

    def into(self, table:Any, update:bool=False) -> None:
        from .snowflake import Table
        assert isinstance(table, Table), "Only Snowflake tables are supported for now"

        clone = Fragment(parent=self)
        clone._is_export = True
        qb_model = clone._model or Model("anon")
        ir_model = qb_model._to_ir()
        clone._source = runtime_env.get_source_pos()
        with debugging.span("query", dsl=str(clone), **with_source(clone), meta=clone._meta):
            query_task = qb_model._compiler.fragment(clone)
            qb_model._to_executor().execute(ir_model, query_task, export_to=table, update=update, meta=clone._meta)

#--------------------------------------------------
# Select / Where
#--------------------------------------------------

def select(*args: Any, parent:Fragment|None=None, model:Model|None=None) -> Fragment:
    return Fragment(model=model).select(*args)

def where(*args: Any, parent:Fragment|None=None, model:Model|None=None) -> Fragment:
    return Fragment(model=model).where(*args)

def require(*args: Any, parent:Fragment|None=None, model:Model|None=None) -> Fragment:
    return Fragment(model=model).require(*args)

def define(*args: Any, parent:Fragment|None=None, model:Model|None=None) -> Fragment:
    return Fragment(model=model).define(*args)

#--------------------------------------------------
# Model
#--------------------------------------------------

class Model():
    def __init__(
        self,
        name: str,
        dry_run: bool = False,
        keep_model: bool = True,
        use_lqp: bool | None = None,
        use_sql: bool = False,
        strict: bool = False,
        wide_outputs: bool = False,
        enable_otel_handler: bool | None = None,
        connection: Session | None = None,
        config: Config | None = None,
    ):
        self._id = next(_global_id)
        self.name = f"{name}{overrides('model_suffix', '')}"
        self._dry_run = cast(bool, overrides('dry_run', dry_run))
        self._keep_model = cast(bool, overrides('keep_model', keep_model))
        self._use_sql = cast(bool, overrides('use_sql', use_sql))
        self._wide_outputs = cast(bool, overrides('wide_outputs', wide_outputs))
        self._config = config or Config()
        config_overrides = overrides('config', {})
        for k, v in config_overrides.items():
            self._config.set(k, v)
        self._intrinsic_overrides = get_intrinsic_overrides()
        self._strict = cast(bool, overrides('strict', strict))
        self._use_lqp = overridable_flag('reasoner.rule.use_lqp', self._config, use_lqp, default=not self._use_sql)
        self._enable_otel_handler = overridable_flag('enable_otel_handler', self._config, enable_otel_handler, default=False)
        if isinstance(runtime_env, SessionEnvironment):
            self._connection = runtime_env.configure_session(self._config, connection)
        else:
            self._connection = connection
        self.concepts:dict[str, list[Concept]] = {}
        self.relationships:list[Relationship] = []
        self.enums:dict[str, Type[Enum]] = {}
        self.enum_concept:dict[Type[Enum], Concept] = {}
        self.constraints:set[Constraint] = set()

        # Compiler
        self._compiler = Compiler()
        self._root_version = _global_roots.version()
        self._last_compilation = None

        # Executor
        self._executor = None

        # Enum
        self.Enum = create_enum_class(self)

    def _to_ir(self):
        if not _global_roots.has_changed(self._root_version) and self._last_compilation:
            return self._last_compilation
        self._last_compilation = self._compiler.model(self)
        self._root_version = _global_roots.version()
        return self._last_compilation

    def _to_executor(self):
        if not self._executor:
            if self._use_lqp:
                self._executor = LQPExecutor(
                    self.name,
                    dry_run=self._dry_run,
                    keep_model=self._keep_model,
                    wide_outputs=self._wide_outputs,
                    connection=self._connection,
                    config=self._config,
                    intrinsic_overrides=self._intrinsic_overrides,
                )
            elif self._use_sql:
                self._executor = SnowflakeExecutor(
                    self.name,
                    self.name,
                    dry_run=self._dry_run,
                    config=self._config,
                    skip_denormalization=True,
                    connection=self._connection,
                )
            else:
                self._executor = RelExecutor(
                    self.name,
                    dry_run=self._dry_run,
                    keep_model=self._keep_model,
                    wide_outputs=self._wide_outputs,
                    connection=self._connection,
                    config=self._config,
                )
            configure_otel(self._enable_otel_handler, self._config, self._executor.resources)
        return self._executor

    def Concept(self, name:str, extends:list[Concept|Any]=[], identify_by:dict[str, Any]={}) -> Concept:
        concept = Concept(name, model=self, extends=extends, identify_by=identify_by)
        if name not in self.concepts:
            self.concepts[name] = list()
        self.concepts[name].append(concept)
        return concept

    def Relationship(self, *args, short_name:str="") -> Relationship:
        return Relationship(*args, parent=None, short_name=short_name, model=self)

    def Property(self, *args, short_name:str="") -> Property:
        return Property(*args, parent=None, short_name=short_name, model=self)

    def define(self, *args: Any) -> Fragment:
        return define(*args, model=self)

#--------------------------------------------------
# Compile
#--------------------------------------------------

class CompilerContext():
    def __init__(self, compiler:Compiler, parent:CompilerContext|None=None):
        self.compiler = compiler
        self.parent = parent
        self.value_map:dict[Any, ir.Value|list[ir.Var]] = parent.value_map.copy() if parent else {}
        self.items:OrderedSet[ir.Task] = OrderedSet()
        self.into_vars:list[ir.Var] = parent.into_vars.copy() if parent else []
        self.global_value_map:dict[Any, ir.Value|list[ir.Var]] = parent.global_value_map if parent else {}

    def to_value(self, item:Any, or_value=None, is_global_or_value=True) -> ir.Value|list[ir.Var]:
        if item not in self.value_map:
            if item in self.global_value_map:
                self.value_map[item] = self.global_value_map[item]
            elif or_value is not None:
                if is_global_or_value:
                    # when or_value is global save it in global_value_map as well
                    self.map_var(item, or_value)
                else:
                    self.value_map[item] = or_value
            else:
                name = to_name(item)
                qb_type = to_type(item)
                type = self.compiler.to_type(qb_type) if qb_type else types.Any
                self.map_var(item, f.var(name, type))
        return self.value_map[item]

    def map_var(self, item:Any, value:ir.Value|list[ir.Var]):
        self.global_value_map[item] = value
        self.value_map[item] = value
        return value

    def fetch_var(self, item:Any):
        if item in self.value_map:
            return self.value_map[item]
        elif item in self.global_value_map:
            return self.global_value_map[item]
        return None

    def _has_item(self, item:ir.Task) -> bool:
        return bool(item in self.items or (self.parent and self.parent._has_item(item)))

    def add(self, item:ir.Task):
        if not self._has_item(item):
            self.items.add(item)

    def try_merge_hoists(self, required: PySequence[ir.VarOrDefault], available: PySequence[ir.VarOrDefault]) -> list[ir.VarOrDefault] | None:
        avail_map = {(item.var if isinstance(item, ir.Default) else item): item for item in available}
        result = []
        for req in required:
            var = req.var if isinstance(req, ir.Default) else req
            if var not in avail_map:
                return None
            # prefer the available default as it would've bubbled up and overridden
            # the required one, otherwise take the required
            result.append(avail_map[var] if isinstance(avail_map[var], ir.Default) else req)
        return result

    def safe_wrap(self, required_hoists:PySequence[ir.VarOrDefault]) -> ir.Task:
        first = self.items[0]
        if len(self.items) == 1 and isinstance(first, ir.Logical):
            merged = self.try_merge_hoists(required_hoists, first.hoisted)
            if merged is not None:
                return f.logical(list(first.body), merged)
        return f.logical(list(self.items), required_hoists)

    def is_hoisted(self, var: ir.Var):
        return any(isinstance(i, helpers.COMPOSITES) and var in helpers.hoisted_vars(i.hoisted) for i in self.items)

    def clone(self):
        return CompilerContext(self.compiler, self)


# map literal, python native types to IR types
PY_LITERAL_TYPE_MAPPING = {
    str: types.String,
    bool: types.Bool,
    int: types.Int128,
    float: types.Float,
    PyDecimal: types.Decimal,
    date: types.Date,
    datetime: types.DateTime,
}

PY_LITERAL_TYPES = (str, bool, int, float, date, datetime, PyDecimal)

def literal_value_to_type(value) -> ir.Type:
    literal_type = type(value)
    if literal_type in PY_LITERAL_TYPE_MAPPING:
        return PY_LITERAL_TYPE_MAPPING[literal_type]
    raise TypeError(f"Cannot determine type for value: {value} of type {type(value).__name__}")

class Compiler():
    def __init__(self):
        self.types:dict[Concept, ir.ScalarType] = {}
        self.name_to_type:dict[str, ir.Type] = {}
        self.relations:dict[Relationship|Concept|ConceptMember|RelationshipRef|RelationshipReading|ir.Relation, ir.Relation] = {}
        # cache box_type relations
        self.box_type_relations:dict[tuple[ir.Type, ir.Type], ir.Relation] = {}

    #--------------------------------------------------
    # Type/Relation conversion
    #--------------------------------------------------

    def to_annos(self, item:Concept|Relationship|RelationshipReading|Fragment) -> list[ir.Annotation]:
        annos = []
        items = item._annotations
        for item in items:
            if isinstance(item, Expression):
                ctx = CompilerContext(self)
                annos.append(f.annotation(self.to_relation(item._op), flatten([self.lookup(p, ctx) for p in item._params])))
            elif isinstance(item, Relationship):
                annos.append(f.annotation(self.to_relation(item), []))
            elif isinstance(item, ir.Annotation):
                annos.append(item)
            else:
                raise ValueError(f"Cannot convert {type(item).__name__} to annotation")
        return annos

    def to_type(self, concept:Concept) -> ir.ScalarType:
        if concept not in self.types:
            if is_decimal(concept):
                self.types[concept] = types.decimal_by_type_str(concept._name)
            elif concept in Concept.builtin_concepts:
                self.types[concept] = types.builtin_scalar_types_by_name[concept._name]
            else:
                parent_types = [self.to_type(parent) for parent in concept._extends]
                self.types[concept] = f.scalar_type(concept._name, parent_types, annos=self.to_annos(concept))
            self.name_to_type[concept._name] = self.types[concept]
        return self.types[concept]

    def to_relation(self, item:Concept|Relationship|RelationshipReading|RelationshipRef|ir.Relation) -> ir.Relation:
        if item not in self.relations:
            if isinstance(item, Concept):
                fields = [f.field(item._name.lower(), self.to_type(item))]
                annos = self.to_annos(item)
                builtins.builtin_annotations_by_name
                annos.append(builtins.concept_relation_annotation)
                relation = f.relation(item._name, fields, annos=annos)
            elif isinstance(item, Relationship):
                if item._ir_relation:
                    relation = item._ir_relation
                    for overload in relation.overloads:
                        self.to_relation(overload)
                else:
                    fields = []
                    for cur in item._field_refs:
                        assert isinstance(cur._thing, Concept)
                        fields.append(f.field(to_name(cur), self.to_type(cur._thing)))
                    overloads = []
                    if item._unresolved:
                        overloads = [v for k, v in self.relations.items()
                                     if isinstance(k, Relationship)
                                        and not k._unresolved
                                        and k._name == item._name]
                    relation = f.relation(item._name, fields, annos=self.to_annos(item), overloads=overloads)
                # skip the first reading since it's the same as the Relationship
                for red in item._readings[1:]:
                    self.to_relation(red)
            elif isinstance(item, RelationshipReading):
                fields = []
                for cur in item._field_refs:
                    assert isinstance(cur._thing, Concept)
                    fields.append(f.field(to_name(cur), self.to_type(cur._thing)))
                # todo: should we look for overloads in case alt_of Relationship is unresolved?
                relation = f.relation(item._name, fields, annos=self.to_annos(item))
            elif isinstance(item, RelationshipRef):
                relation = self.to_relation(item._relationship)
            elif isinstance(item, ir.Relation):
                for overload in item.overloads:
                    self.to_relation(overload)
                relation = item
            self.relations[item] = relation
            return relation
        else:
            return self.relations[item]

    #--------------------------------------------------
    # Model
    #--------------------------------------------------

    @roots(enabled=False)
    def model(self, model:Model) -> ir.Model:
        rules = []
        for concepts in model.concepts.values():
            for concept in concepts:
                if concept not in self.types:
                    self.to_type(concept)
                    self.to_relation(concept)
                rule = self.concept_inheritance_rule(concept)
                if rule:
                    rules.append(rule)
        unresolved = []
        for relationship in model.relationships:
            if relationship not in self.relations:
                if relationship._unresolved:
                    unresolved.append(relationship)
                else:
                    self.to_relation(relationship)
        for relationship in unresolved:
            self.to_relation(relationship)
        with debugging.span("rule_batch"):
            for idx, rule in enumerate(_global_roots):
                if not rule._model or rule._model == model:
                    meta = rule._meta if isinstance(rule, Fragment) else {}
                    with debugging.span("rule", name=f"rule{idx}", dsl=str(rule), **with_source(rule), meta=meta) as rule_span:
                        rule_ir = self.compile_task(rule)
                        rules.append(rule_ir)
                        rule_span["metamodel"] = str(rule_ir)
        root = f.logical(rules)
        engines = ordered_set()
        relations = OrderedSet.from_iterable(self.relations.values())
        types = OrderedSet.from_iterable(self.types.values())
        return f.model(engines, relations, types, root)

    #--------------------------------------------------
    # Compile
    #--------------------------------------------------

    @roots(enabled=False)
    def compile_task(self, thing:Expression|Fragment) -> ir.Task:
        if isinstance(thing, (Expression, Match, Union)):
            return self.root_expression(thing)
        elif isinstance(thing, Fragment):
            return self.fragment(thing)

    #--------------------------------------------------
    # Root expression
    #--------------------------------------------------

    @roots(enabled=False)
    def root_expression(self, item:Expression) -> ir.Task:
        ctx = CompilerContext(self)
        self.update(item, ctx)
        return f.logical(list(ctx.items))

    #--------------------------------------------------
    # Fragment
    #--------------------------------------------------

    def _is_rank(self, item) -> bool:
        return isinstance(item, Aggregate) and item._op._name == "rank"

    def _process_rank(self, items:PySequence[Expression], rank_ctx:CompilerContext):
        args_to_process = ordered_set()
        arg_is_ascending = []
        for item in items:
            if isinstance(item, RankOrder):
                args_to_process.update(item._args)
                arg_is_ascending.extend([item._is_asc] * len(item._args))
            else:
                args_to_process.add(item)
                arg_is_ascending.append(RankOrder.ASC)

        keys = ordered_set()
        for arg in args_to_process:
            if isinstance(arg, Distinct):
                continue
            keys.update(find_keys(arg))
        # Expressions go into the rank args if asked directly.
        # Otherwise they go into the projection if they are keys.
        projection = OrderedSet.from_iterable(
            flatten([self.lookup(key, rank_ctx) for key in keys], flatten_tuples=True)
        )
        args = OrderedSet.from_iterable(
            flatten([self.lookup(arg, rank_ctx) for arg in args_to_process], flatten_tuples=True)
        )
        return projection, args, arg_is_ascending

    @roots(enabled=False)
    def fragment(self, fragment:Fragment, parent_ctx:CompilerContext|None=None, into_vars:list[ir.Var] = []) -> ir.Task:
        ctx = CompilerContext(self, parent_ctx)
        if fragment._require:
            self.require(fragment, fragment._require, ctx)
        else:
            rank_var = self.order_by_or_limit(fragment, ctx)
            self.where(fragment, fragment._where, ctx)
            self.define(fragment, fragment._define, ctx)
            self.select(fragment, fragment._select, ctx, rank_var)
        return f.logical(list(ctx.items), ctx.into_vars, annos=self.to_annos(fragment))

    def order_by_or_limit(self, fragment:Fragment, ctx:CompilerContext):
        if fragment._limit == 0 and not fragment._order_by:
            return None
        if fragment._define:
            raise NotImplementedError("Order_by and/or limit are not supported on define")

        limit_ctx = ctx.clone()
        inner_ctx = limit_ctx.clone()

        # If there is an order-by, then the limit is applied on the fields there. Otherwise,
        # the limit is applied on the fields in the select (with a default ranking order).
        items = fragment._order_by if fragment._order_by else fragment._select

        projection, args, arg_is_ascending = self._process_rank(items, inner_ctx)

        limit_ctx.add(inner_ctx.safe_wrap([]))

        rank_var = f.var("v", types.Int128)
        limit_ctx.add(f.rank(list(projection), [], list(args), arg_is_ascending, rank_var, fragment._limit))
        ctx.add(f.logical(list(limit_ctx.items), [rank_var]))
        return rank_var

    def where(self, fragment:Fragment, items:PySequence[Expression], ctx:CompilerContext):
        for item in items:
            self.lookup(item, ctx)

    def select(self, fragment:Fragment, items:PySequence[Expression], ctx:CompilerContext, rank_var:ir.Var|None=None):
        if not items:
            return

        namer = NameCache(use_underscore=False)
        aggregate_keys:OrderedSet[ir.Var] = OrderedSet()
        out_var_to_keys = {}
        fields = []
        if rank_var:
            fields.append((namer.get_name(len(fields), "rank"), rank_var))
        keys_present = has_keys(items)
        for ix, item in enumerate(items):
            # allow primitive to be a key when at least one key is present and primitive is not the last item
            # this is needed to avoid cross products in output
            enable_primitive_key = ix != len(items) - 1 if keys_present else False
            keys = find_select_keys(item, enable_primitive_key=enable_primitive_key)

            key_vars:list[ir.Var] = []
            for idx, key in enumerate(keys):
                # don't add lookups for the keys played by Concepts if they are not on the first position
                if idx > 0 and isinstance(key.val, Concept):
                    key_var = ctx.to_value(key.val)
                else:
                    key_var = self.lookup(key.val, ctx)
                assert isinstance(key_var, ir.Var)
                key_vars.append(key_var)
                if key.is_group:
                    aggregate_keys.add(key_var)

            sub_ctx = ctx.clone()
            result_vars = []
            # If we lookup a property or a relationship, without a parent (a bare one)
            # don't assume some value can be None. Add the lookup directly to the parent ctx
            if isinstance(item, RelationshipRef) and isinstance(item._parent, Property) and not item._parent._parent:
                self.lookup(item._parent, ctx)
                result = self.lookup(item, sub_ctx)
            elif isinstance(item, (Property, Relationship, RelationshipFieldRef)) and not item._parent:
                result = self.lookup(item, ctx)
            else:
                result = self.lookup(item, sub_ctx)
            if isinstance(result, list):
                assert all(isinstance(v, ir.Var) for v in result)
                result_vars.extend(result)
            else:
                result_vars.append(result)

            # normalize result vars through fetch_var if available
            result_vars = [
                fetched if isinstance(fetched := ctx.fetch_var(v), ir.Var) else v
                for v in result_vars
            ]

            extra_nullable_keys: OrderedSet[ir.Var] = OrderedSet()
            # check if whether we actually added a lookup resulting in the key, in the sub-context
            # the lookup might have already existed in the parent context, in which case the key is not nullable.
            # E.g.,
            # attends(course)
            # course = ..
            # Logical ^[..]
            #
            # vs
            #
            # Logical ^[.., course=None]
            #    attends(course)
            for it in sub_ctx.items:
                if isinstance(it, ir.Lookup):
                    vars = helpers.vars(it.args)
                    if vars[-1] in key_vars:
                        extra_nullable_keys.add(vars[-1])

            if len(sub_ctx.items) > 0:
                args = list(result_vars)
                for k in extra_nullable_keys:
                    if k not in args:
                        args.append(k)
                hoisted:list[ir.VarOrDefault] = [ir.Default(v, None) for v in args if isinstance(v, ir.Var)]
                ctx.add(sub_ctx.safe_wrap(hoisted))

            for v in result_vars:
                name = "v"
                if isinstance(item, Alias):
                    name = item._name
                elif isinstance(v, ir.Var):
                    name = v.name
                out_var_to_keys[v] = key_vars

                # if this is a nested select that is populating variables rather
                # than outputting
                if ctx.into_vars:
                    relation = self.to_relation(builtins.eq)
                    ctx.add(f.lookup(relation, [ctx.into_vars[ix], v]))
                else:
                    fields.append((namer.get_name(len(fields), name), v))

        if fields:
            annos = fragment._annotations
            if fragment._is_export:
                annos += [builtins.export_annotation]

            # If one of the vars in our output is itself a key, and it's the key of an
            # aggregation, then we should ignore its keys. This fixes the case where we
            # return the group of an aggregate and should ignore the keys of the group variables.
            final_keys = ordered_set()
            for v, keys in out_var_to_keys.items():
                if v in aggregate_keys:
                    final_keys.add(v)
                else:
                    final_keys.update(keys)

            # If we are exporting into a table, we need to add a key to the output
            # We hash all the values to create a key
            if not final_keys and fragment._is_export:
                tmp_var = ctx.to_value(self)
                assert isinstance(tmp_var, ir.Var)
                key_var = f.var(tmp_var.name, types.Hash)
                assert isinstance(key_var, ir.Var)
                final_keys.add(key_var)
                values = [ir.Literal(types.String, "NO_KEYS")]
                for fld in fields:
                    values.append(fld[1])
                con = ir.Construct(None, tuple(values), key_var, FrozenOrderedSet([]))
                ctx.add(con)

            ctx.add(f.output(fields, keys=list(final_keys), annos=annos))

    def require(self, fragment:Fragment, items:PySequence[Expression], ctx:CompilerContext):
        domain_ctx = ctx.clone()
        self.where(fragment, fragment._where, domain_ctx)
        domain_vars = OrderedSet.from_iterable(flatten(list(domain_ctx.value_map.values()), flatten_tuples=True))
        to_hoist = OrderedSet()
        checks = []
        for item in items:
            if isinstance(item, Expression) and item._op is Relationship.builtins[builtins.anyof.name] and not domain_vars:
                raise ValueError("'anyof' and 'oneof' are not allowed without a domain")

            req_ctx = domain_ctx.clone()
            self.lookup(item, req_ctx)
            req_body = f.logical(list(req_ctx.items))

            err_ctx = domain_ctx.clone()
            item_str = item._pprint() if isinstance(item, Producer) else str(item)
            keys = {to_name(k): k for k in find_keys(item)}
            source = item._source if hasattr(item, "_source") else fragment._source
            e = Error.new(message=f"Requirement not met: {item_str}", **keys, _source=source, _model=fragment._model)
            self.update(e, err_ctx)
            err_body = f.logical(list(err_ctx.items))
            checks.append(f.check(req_body, err_body))

            # find vars that overlap between domain and check/error and hoist them
            all_values = flatten(list(req_ctx.value_map.values()) + list(err_ctx.value_map.values()))
            to_hoist.update(domain_vars & OrderedSet.from_iterable(all_values))

        domain = f.logical(list(domain_ctx.items), list(to_hoist))
        req = f.require(domain, checks)
        ctx.add(req)

    def define(self, fragment:Fragment, items:PySequence[Expression], ctx:CompilerContext):
        def _check_item(item: Expression):
            if isinstance(item, ConceptFilter):
                raise ValueError("'filter_by' is not allowed in definitions")

        if len(items) == 1:
            item = items[0]
            _check_item(item)
            self.update(item, ctx)
            return

        for item in items:
            _check_item(item)
            sub_ctx = ctx.clone()
            self.update(item, sub_ctx)
            if len(sub_ctx.items) > 1:
                ctx.add(f.logical(list(sub_ctx.items)))
            elif len(sub_ctx.items) == 1:
                ctx.add(sub_ctx.items[0])

    #--------------------------------------------------
    # Reference schemes and concept inheritance
    #--------------------------------------------------

    def concept_inheritance_rule(self, concept:Concept) -> Optional[ir.Task]:
        """
        If the concept extends non-primitive concepts, generate a rule where the body is a
        lookup for this concept and the head are derives into all non-primitive direct super
        types.
        """
        # filter extends to get only non-primitive parents
        parents = []
        for parent in concept._extends:
            if not parent._is_primitive() and parent is not AnyEntity:
                parents.append(parent)
        # always extend AnyEntity for non-primitive types that are not built-in
        if not concept._is_primitive() and concept not in Concept.builtin_concepts:
            parents.append(AnyEntity)
        # only extends primitive types, no need for inheritance rules
        if not parents:
            return None
        # generate the rule
        ctx = CompilerContext(self)
        var = self.lookup(concept, ctx)
        assert isinstance(var, ir.Var)
        return f.logical([
            *list(ctx.items),
            *[f.derive(self.to_relation(parent), [var]) for parent in parents]
        ])

    def concept_any_entity_rule(self, entities:list[Concept]):
        """
        Generate an inheritance rule for all these entities to AnyEntity.
        """
        any_entity_relation = self.to_relation(AnyEntity)
        var = f.var("v", types.Any)
        return f.logical([
            f.union([f.lookup(self.to_relation(e), [var]) for e in entities]),
            f.derive(any_entity_relation, [var])
        ])

    def relation_dict(self, items:dict[Relationship|Concept, Producer], ctx:CompilerContext) -> dict[ir.Relation, list[ir.Var]]:
        return {self.to_relation(k): unwrap_list(self.lookup(v, ctx)) for k, v in items.items()}

    def construct_relation_dict(self, items: dict[Relationship | Concept, Producer], ctx: CompilerContext) -> dict[ir.Relation, list[ir.Var]]:
        result = {}
        for k, v in items.items():
            relation = self.to_relation(k)
            value = unwrap_list(self.lookup(v, ctx))

            # We are able to check types for the `construct` only when we are using binary relations
            #     in the other case we just pass the original value
            if len(relation.fields) == 2:
                field = relation.fields[-1]
                if field and field.type != types.Any and types.is_value_type(field.type):
                    field_base = typer.to_base_primitive(field.type)
                    value_base = typer.to_base_primitive(value.type)

                    if field_base != value_base:
                        # cast to expected field type
                        new_out = f.var(helpers.sanitize(to_name(k)), field.type)
                        ctx.add(f.lookup(builtins.cast, [field.type, value, new_out]))
                        result[relation] = new_out
                        self.relations[relation] = builtins.cast
                        continue

            result[relation] = value

        return result

    def explode_ref_schemes(self, item:ConceptExpression, ctx:CompilerContext, update=False):
        hierarchy = item._op._ref_scheme_hierarchy()
        if not hierarchy:
            out = ctx.to_value(item)
            assert isinstance(out, ir.Var)
            ctx.add(f.construct(out, self.construct_relation_dict(item._construct_args(), ctx)))
            return out

        # if we're just doing a lookup, then we only need the last reference scheme
        if not update:
            hierarchy = hierarchy[-1:]

        out = None
        for ix, info in enumerate(hierarchy):
            concept = info["concept"]
            scheme = info["scheme"]
            # the "out" variable, which is constructed for the top-most concept in the
            # hierarchy and is used to key the generated derives, should be typed with the
            # most specific type, i.e. the type of the concept expression.
            # so if this is the top most (out is None) we set or_value_type to the type of
            # the item instead of the concept.
            if out is None:
                x = to_type(item)
                or_value_type = self.to_type(x) if x else self.to_type(concept)
            else:
                or_value_type = self.to_type(concept)

            or_value = f.var(to_name(concept), or_value_type)
            # or_value is global only when it's the last Concept in hierarchy
            is_global_or_value = ix == len(hierarchy) - 1
            cur = ctx.to_value(concept, or_value, is_global_or_value) if isinstance(item, ConceptFilter) \
                else ctx.to_value((item, ix), or_value, is_global_or_value)
            assert isinstance(cur, ir.Var)
            ctx.add(f.construct(cur, self.construct_relation_dict(item._construct_args(scheme), ctx), prefix=[self.to_type(concept)]))
            if not out:
                out = cur
            if r := info.get("mapping"):
                rel = self.to_relation(r)
                if out is cur:
                    out = ctx.to_value(item, f.var(to_name(concept), self.to_type(concept)))
                    assert isinstance(out, ir.Var)
                if update:
                    ctx.add(f.derive(rel, [cur, out]))
                else:
                    ctx.add(f.lookup(rel, [cur, out]))

        assert out is not None
        return out

    #--------------------------------------------------
    # Lookup
    #--------------------------------------------------

    def lookup(self, item:Any, ctx:CompilerContext) -> ir.Value|list[ir.Var]:
        if isinstance(item, ConceptExpression):
            assert isinstance(item._op, Concept)
            concept = item._op
            relation = self.to_relation(concept)
            (ident, kwargs) = item._params

            # If this is a member lookup, check that the identity is a member
            # and add all the kwargs as lookups
            if isinstance(item, ConceptMember):
                out = self.lookup(ident, ctx)
                if isinstance(out, PY_LITERAL_TYPES):
                    out = f.literal(out, self.to_type(concept))
                assert isinstance(out, (ir.Var, ir.Literal))
                if not concept._is_primitive():
                    ctx.add(f.lookup(relation, [out]))
                rels = {self.to_relation(getattr(concept, k)): unwrap_list(self.lookup(v, ctx))
                        for k, v in kwargs.items()}
                for k, v in rels.items():
                    assert not isinstance(v, list)
                    ctx.add(f.lookup(k, [out, v]))

                # Boxing operation on value types
                # E.g., SSN(str_var), box a String to an SSN in the IR
                op_type = self.to_type(concept)
                if types.is_value_type(op_type):
                    inner_type = out.type
                    if inner_type == op_type:
                        return out

                    # immediately transform string literals in symbol literals if necessary
                    if isinstance(out, ir.Literal) and inner_type == types.String and op_type == types.Symbol:
                        return f.literal(out.value, types.Symbol)

                    if ctx.fetch_var(item):
                        new_out = ctx.fetch_var(item)
                        assert not isinstance(new_out, list)
                    else:
                        new_out = f.var(helpers.sanitize(to_name(concept)), op_type)
                        ctx.map_var(item, new_out)

                    ctx.add(f.lookup(builtins.cast, [op_type, out, new_out]))
                    self.relations[item] = builtins.cast
                    out = new_out

                return out

            # There are 3 types of kwargs usage:
            #   1. Only ref schema attributes - generate construct + population relation
            #   2. Ref schema attributes + some other relations - generate construct + population relation + lookups
            #   3. Not full ref schema or any other relation - generate set of lookups
            if isinstance(item, ConceptFilter):
                scheme = concept._ref_scheme()

                out = None
                args = kwargs

                if scheme:
                    # Collect expected keys from the reference scheme
                    ks = [rel._short_name for rel in scheme]

                    # Check if all scheme keys are present in kwargs
                    full_ref_scheme_present = all(k in kwargs for k in ks)

                    if full_ref_scheme_present:
                        # Explode full reference scheme
                        out = self.explode_ref_schemes(item, ctx, update=False)
                        if not concept._is_primitive():
                            ctx.add(f.lookup(relation, [out]))

                        # Remove scheme keys from arguments
                        args = {k: v for k, v in args.items() if k not in ks}

                        # If nothing left, return early
                        if not args:
                            return out

                # Fallback: simple lookup if no scheme matched
                if out is None:
                    out = self.lookup(concept, ctx)

                assert isinstance(out, ir.Var)

                # Generate relation lookups for remaining args
                rels = {self.to_relation(getattr(concept, k)): unwrap_list(self.lookup(v, ctx))
                        for k, v in args.items()}

                for k, v in rels.items():
                    assert not isinstance(v, list)
                    ctx.add(f.lookup(k, [out, v]))

                return out

            # otherwise we have to construct one
            out = self.explode_ref_schemes(item, ctx, update=False)
            return out

        elif isinstance(item, Expression):
            params = [self.lookup(p, ctx) for p in item._params]
            relation = self.to_relation(item._op)
            ctx.add(f.lookup(relation, flatten(params)))
            return params[-1]

        elif isinstance(item, Concept):
            v = ctx.to_value(item)
            if not item._isa(Primitive):
                assert isinstance(v, ir.Var)
                relation = self.to_relation(item)
                ctx.add(f.lookup(relation, [v]))
            return v

        elif isinstance(item, (Relationship, RelationshipRef, RelationshipReading)):
            params = item._field_refs
            if item._parent:
                params = [item._parent] + params[1:]
            return self.lookup(item(*params), ctx)

        elif isinstance(item, RelationshipFieldRef):
            rel = item._relationship
            params = list(rel._field_refs)
            if item._parent:
                params = [item._parent] + params[1:]
            self.lookup(rel(*params), ctx)
            return self.lookup(params[item._field_ix], ctx)

        elif isinstance(item, Ref):
            if item._no_lookup:
                return ctx.to_value(item)

            root = item._thing
            prev_mapping = ctx.to_value(root)
            out = ctx.to_value(item)
            ctx.map_var(root, out)
            self.lookup(root, ctx)
            ctx.map_var(root, prev_mapping)
            return out

        elif isinstance(item, TypeRef):
            if isinstance(item._thing, Relationship):
                return self.to_relation(item._thing)
            concept = to_type(item)
            if not concept:
                raise ValueError(f"Cannot find concept for {item}, {type(item)}")
            return self.to_type(concept)

        elif isinstance(item, ArgumentRef):
            self.lookup(item._expr, ctx)
            return ctx.to_value(item._arg)

        elif isinstance(item, Alias):
            return self.lookup(item._thing, ctx)

        elif isinstance(item, Aggregate):
            relation = self.to_relation(item._op)

            group = [self.lookup(g, ctx) for g in item._group]
            group = [item for item in flatten(group, flatten_tuples=True) if isinstance(item, ir.Var)]

            agg_ctx = ctx.clone()

            # additional wheres
            self.where(item._where, item._where._where, agg_ctx)

            if self._is_rank(item):
                # The rank output is always an int
                out = agg_ctx.to_value(item, f.var(to_name(item), types.Int128))
                assert isinstance(out, ir.Var)

                projection, args, arg_is_ascending = self._process_rank(item._args, agg_ctx)
                internal_vars = ordered_set()

                ir_node = f.rank(projection.get_list(), group, args.get_list(), arg_is_ascending, out)

            else:
                out = agg_ctx.to_value(item)
                assert isinstance(out, ir.Var)
                arg_count = len(relation.fields) - 1 # skip the result
                raw_args = flatten([self.lookup(a, agg_ctx) for a in item._args])

                # the projection includes all keys for the args
                projection = [self.lookup(key, agg_ctx) for key in find_keys(item._args)]
                # the projection is also all raw_args that aren't consumed by the agg
                projection += raw_args[:-arg_count] if arg_count else raw_args
                projection = flatten(projection, flatten_tuples=True)
                projection = list(dict.fromkeys([item for item in projection if isinstance(item, ir.Var)]))

                # agg args + result var
                args = raw_args[-arg_count:] if arg_count else []
                args.append(out)

                internal_vars = set(flatten(raw_args + projection, flatten_tuples=True))
                ir_node = f.aggregate(relation, projection, group, args)

            final_ctx = ctx.clone()
            if agg_ctx.items:
                internal = internal_vars - set(flatten(list(ctx.value_map.values()), flatten_tuples=True))
                hoisted = [ir.Default(v, None) for v in internal if isinstance(v, ir.Var)]
                hoisted.sort(key=lambda x: x.var.name)
                final_ctx.add(f.logical(list(agg_ctx.items), list(hoisted)))
            final_ctx.add(ir_node)
            ctx.add(f.logical(list(final_ctx.items), [out]))
            return out

        elif isinstance(item, Not):
            not_ctx = ctx.clone()
            for a in item._args:
                self.lookup(a, not_ctx)
            ctx.add(f.not_(f.logical(list(not_ctx.items))))

        elif isinstance(item, Fragment):
            if item._is_where_only():
                for where in item._where:
                    self.lookup(where, ctx)
                return None

            sub_ctx = ctx.clone()

            # if we encounter a select and we aren't already trying to write
            # it into vars, add some
            into_vars = ctx.into_vars
            if not len(into_vars) and item._select:
                into_vars = sub_ctx.into_vars = flatten([ctx.to_value(s) for s in item._select])

            ctx.add(self.fragment(item, sub_ctx))
            out = None
            if len(into_vars) == 1:
                out = into_vars[0]
            elif len(into_vars) > 1:
                out = into_vars
            elif len(item._select) == 1:
                out = sub_ctx.to_value(item._select[0])
            elif len(item._select) > 1:
                out = flatten([sub_ctx.to_value(s) for s in item._select])

            return out

        elif isinstance(item, (Match, Union)):
            branches = []
            vars = []
            if item._is_select:
                vars = ctx.fetch_var(item)
                if isinstance(vars, ir.Var):
                    vars = [vars]
                elif not vars:
                    vars = [f.var(f"v{i}") for i in range(item._ret_count)]
                    ctx.map_var(item, vars)
                assert isinstance(vars, list)
                for branch in item._args:
                    branch_ctx = ctx.clone()
                    branch_ctx.into_vars = vars
                    v = self.lookup(branch, branch_ctx)
                    if not isinstance(v, list):
                        v = [v]
                    for var, ret in zip(vars, v):
                        if var is not ret:
                            relation = self.to_relation(builtins.eq)
                            branch_ctx.add(f.lookup(relation, [var, ret]))
                            # map in parent context the union/match branch var to an original var
                            ctx.map_var(ret, var)
                    branches.append(branch_ctx.safe_wrap(vars))
            elif all(isinstance(branch, Concept) or isinstance(branch, PY_LITERAL_TYPES) for branch in item._args):
                vars = [f.var(to_name(item), types.Any)]
                for branch in item._args:
                    branch_ctx = ctx.clone()
                    v = self.lookup(branch, branch_ctx)
                    assert isinstance(v, (ir.Var, ir.Literal))
                    branch_ctx.add(f.lookup(builtins.eq, [vars[0], v]))
                    branches.append(branch_ctx.safe_wrap(vars))
            else:
                for branch in item._args:
                    branch_ctx = ctx.clone()
                    self.update(branch, branch_ctx)
                    branches.append(branch_ctx.safe_wrap([]))
            if isinstance(item, Union):
                ctx.add(f.union(branches, vars))
            else:
                ctx.add(f.match(branches, vars))

            return vars or None

        elif isinstance(item, BranchRef):
            vars = ctx.value_map.get(item._match)
            if not vars:
                self.lookup(item._match, ctx)
                vars = ctx.fetch_var(item._match)
            assert isinstance(vars, list)
            return vars[item._ix]

        elif isinstance(item, Group):
            for g in item._group:
                self.lookup(g, ctx)

        elif isinstance(item, Distinct):
            vs = [self.lookup(v, ctx) for v in item._args]
            return flatten(vs)

        elif isinstance(item, Data):
            refs = [item._row_id] + [i._ref for i in item._cols]
            vars = flatten([self.lookup(v, ctx) for v in refs])
            ctx.add(f.data(item._data, vars))
            return vars[0]

        elif isinstance(item, DataColumn):
            self.lookup(item._data, ctx)
            return ctx.to_value(item._ref)

        elif isinstance(item, PY_LITERAL_TYPES):
            return f.literal(item, literal_value_to_type(item))

        elif item is None:
            return None

        elif isinstance(item, (ir.Var, ir.Literal)):
            return item

        elif hasattr(item, "_compile_lookup"):
            return item._compile_lookup(self, ctx)

        else:
            raise ValueError(f"Cannot lookup {item}, {type(item)}")

    #--------------------------------------------------
    # Update
    #--------------------------------------------------

    def update(self, item:Expression|Match|Union, ctx:CompilerContext) -> ir.Value|list[ir.Var]:
        if isinstance(item, ConceptExpression):
            assert isinstance(item._op, Concept)
            relation = self.to_relation(item._op)
            (ident, kwargs) = item._params
            out = ctx.to_value(item)
            assert isinstance(out, ir.Var)

            # if this is a member lookup, then our out var is just the identity passed in
            if isinstance(item, ConceptMember):
                out = self.lookup(ident, ctx)
                assert not isinstance(out, list)
            # otherwise we have to construct one
            else:
                out = self.explode_ref_schemes(item, ctx, update=True)

            ctx.add(f.derive(relation, [out]))
            # derive the membership and all the relationships
            rels = self.relation_dict({attr: v for k, v in kwargs.items() if (attr := getattr(item._op, k, None)) is not None}, ctx)
            for k, v in rels.items():
                assert not isinstance(v, list)
                ctx.add(f.derive(k, [out, v]))
            return out

        elif isinstance(item, Expression) and item._op is Relationship.builtins["="]:
            if isinstance(item._params[0], (Relationship, RelationshipRef)):
                return self.update(item._params[0](item._params[1]), ctx)
            elif isinstance(item._params[1], (Relationship, RelationshipRef)):
                return self.update(item._params[1](item._params[0]), ctx)
            elif isinstance(item._params[0], RelationshipFieldRef) or isinstance(item._params[1], RelationshipFieldRef):
                raise ValueError("Cannot set fields of a multi-field relationship individually")
            else:
                raise ValueError("Cannot set a non-relationship via ==")

        elif isinstance(item, Expression):
            op = item._op
            params = flatten([self.lookup(p, ctx) for p in item._params])
            # the case when root a relationship populated thought a reading
            if isinstance(op, RelationshipReading) and not item._ignore_root:
                op = item._op._alt_of
                # reuse params for the root relationship
                ref_2_param = {ref: param for ref, param in zip(item._op._field_refs, params)}
                params = flatten([ref_2_param[ref] for ref in op._field_refs])
            relation = self.to_relation(op)
            ctx.add(f.derive(relation, params))
            return params[-1]

        elif isinstance(item, Relationship) and item._arity() == 1:
            # implicit update of unary relationships
            params = flatten([self.lookup(item._parent, ctx)])
            # normalize parameters through fetch_var if available
            params = [
                fetched if isinstance(fetched := ctx.fetch_var(p), ir.Var) else p
                for p in params
            ]
            relation = self.to_relation(item)
            ctx.add(f.derive(relation, params))
            return params[-1]

        elif isinstance(item, Fragment):
            self.lookup(item, ctx)

        elif isinstance(item, (Match, Union)):
            self.lookup(item, ctx)

        elif hasattr(item, "_compile_update"):
            return item._compile_update(self, ctx)

        else:
            raise ValueError(f"Cannot update {item}")

__all__ = ["select", "where", "require", "define", "distinct", "per", "count", "sum", "min", "max", "avg"]

#--------------------------------------------------
# Todo
#--------------------------------------------------
"""
- Syntax
    ✔ construct
    ✔ static data handling
    ✔ Fix fragments to not be chained
    ✔ Extends
    ✔  Quantifiers
        ✔ not
        ✔ exists
        ✔ forall
    ✔ Aggregates
    ✔ Require
    ✘ Multi-step chaining
    ✔ ref
    ✔ alias
    ✔ match
    ✔ union
    ✔ capture all rules
    ✔ implement aliasing
    ✔ support defining relationships via madlibs Relationship("{Person} was born on {birthday:Date}")
    ✔ distinct
    ☐ nested fragments
    ✔  handle relationships with multiple name fields being accessed via prop:
        Package.shipment = Relationship("{Package} in {Shipment} on {Date}")
        Package.shipment.date, Package.shipment.shipment, Package.shipment.package
    ☐  sources
        ☐  table
        ☐  csv

- Compilation
    ✔ simple expressions
    ✔ select
    ✔ then
    ✔ Quantifiers
        ✔ exists
        ✔ forall
        ✔ not
    ✔ Aggregates
        ✔ Determine agg keys from inputs
        ✔ Group
    ✔ Require
    ✔ Alias
    ✔ Ref
    ✔ Match
    ✔ Union
    ✔ whole model
    ✔ distinct
    ✔ add Else to hoists
    ✔ where(..).define(Person.coolness == 10)
    ☐ extends
        ☐ nominals
    ✔ have require find keys and return the keys in the error
    ☐ Match/union with multiple branch refs in a select, duplicates the whole match
    ☐ nested fragments

☐ Execution
    ✔ basic queries
    ✔ query when iterating over a select
    ☐ debugger hookup
    ☐ table sources
    ☐ graph index
    ☐ exports
    ☐ config overhaul

"""
