from __future__ import annotations
import base64
from enum import Enum
import inspect
from itertools import zip_longest
import re
import struct
import threading
import typing
from typing import Any, Dict, List, Optional, Set, Tuple, Union, get_type_hints
from v0.relationalai.clients.util import IdentityParser, ParseError
from typing_extensions import TypeGuard
import numbers
import os
import datetime
import hashlib
import traceback
import rich
import json
import sys

from pandas import DataFrame

from v0.relationalai.environments import runtime_env, SnowbookEnvironment
from v0.relationalai.tools.constants import QUERY_ATTRIBUTES_HEADER

from .clients.client import Client

from .metamodel import Behavior, Builtins, ActionType, Var, Task, Action, Builder, Type as mType, Property as mProperty
from . import debugging, errors
from .errors import FilterAsValue, Errors, InvalidPropertySetException, MultipleIdentities, NonCallablePropertyException, OutOfContextException, RAIException, ReservedPropertyException, VariableOutOfContextException, handle_missing_integration

#--------------------------------------------------
# Constants
#--------------------------------------------------

RESERVED_PROPS = ["add", "set", "persist", "unpersist"]
MAX_QUERY_ATTRIBUTE_LENGTH = 255

Value = Union[
    "Expression",
    "ContextSelect", # because of union/match
    int,
    float,
    str,
    bool,
    datetime.datetime,
    datetime.date,
]

#--------------------------------------------------
# Helpers
#--------------------------------------------------

# @FIXME: This should only return a Var or None but that's gonna take some doing.
def to_var(x:Any) -> Any:
    if isinstance(x, Var):
        return x
    if getattr(x, "_to_var", None):
        return to_var(x._to_var())
    if isinstance(x, ContextSelect):
        return x._vars[0]
    if isinstance(x, mProperty):
        return Var(value=x)
    if isinstance(x, mType):
        return Var(value=x)
    if isinstance(x, Producer):
        x._use_var()
        return x._var
    if isinstance(x, list) or isinstance(x, tuple):
        return Var(Builtins.Any, value=[v for i in x if (v := to_var(i))])
    if isinstance(x, str):
        return Var(Builtins.String, None, x)
    if isinstance(x, numbers.Number):
        return Var(Builtins.Number, None, x)
    if isinstance(x, datetime.datetime) or isinstance(x, datetime.date):
        return Var(value=x)
    raise Exception(f"Unknown type: {type(x)}\n{x}")

build = Builder(to_var)

def to_list(x:Any):
    if isinstance(x, list):
        return x
    if isinstance(x, tuple):
        return list(x)
    return [x]

def is_static(x:Any):
    if isinstance(x, Var):
        return x.value is not None
    if isinstance(x, Type):
        return True
    if isinstance(x, str):
        return True
    if isinstance(x, Producer):
        return is_static(to_var(x))
    if isinstance(x, numbers.Number):
        return True
    if isinstance(x, list):
        return all(is_static(i) for i in x)
    if isinstance(x, tuple):
        return all(is_static(i) for i in x)
    if isinstance(x, dict):
        return all(is_static(i) for i in x.values())
    return False

def is_collection(x:Any) -> TypeGuard[Union[List, Tuple, Set]]:
    return isinstance(x, list) or isinstance(x, tuple) or isinstance(x, set)

def rel_dict(**kwargs):
    return InlineRelation(get_graph(), [
        (Symbol(k), v) for k, v in kwargs.items()
    ])

#--------------------------------------------------
# Base
#--------------------------------------------------

id = 0
def next_id():
    global id
    id += 1
    return id

#--------------------------------------------------
# Producer
#--------------------------------------------------

attributes_to_skip = {
    "_to_var",
    "__name__",
    "__qualname__",
    "_repr_html_",
    "_supports_binary_op",
}

def is_streamlit_running():
    # First check: Is streamlit imported?
    if 'streamlit' not in sys.modules:
        return False

    # Second check: Try to access session_state
    try:
        import streamlit as st #type: ignore
        _ = st.session_state
        return True
    except RuntimeError:
        return False

def is_called_by_streamlit_write():
    if not is_streamlit_running():
        return False

    stack_frames = inspect.stack()

    for frame in stack_frames[1:]:
        if ("streamlit" in frame.filename and "write" in frame.function):
            return True

    return False

class Producer():
    def __init__(self, graph:'Graph'):
        self._id = next_id()
        self._graph = graph
        self._subs = {}
        self._var = None

    def __iter__(self):
        if is_called_by_streamlit_write():
            return iter([])
        raise Exception("Can't iterate over a producer")

    def __repr__(self):
        if isinstance(runtime_env, SnowbookEnvironment):
            # suppress spurious output in Snowflake notebooks
            # for expressions like p.age > 18
            return ""
        else:
            return super().__repr__()

    def __getattr__(self, name: str) -> Any:
        if is_called_by_streamlit_write():
            return None
        if name in attributes_to_skip:
            return None
        self._subs[name] = self._make_sub(name, self._subs.get(name))
        return self._subs[name]

    def _make_sub(self, name:str, existing:Optional['Producer']=None) -> Any:
        raise Exception("Implement Producer._make_sub")

    def _use_var(self):
        pass

    #--------------------------------------------------
    # Boolean overloads
    #--------------------------------------------------

    def __bool__(self):
        # This doesn't seem to be safe as Python can call bool on Producers in lots of random cases
        # InvalidBoolWarning(Errors.call_source())
        # class_name = self.__class__.__name__
        # TODO: Refactor this to be Exception instead of warning, so we could directly raise it if we bring back this
        # raise TypeError(f"Can't convert an {class_name} to a boolean.")
        return True

    #--------------------------------------------------
    # Math overloads
    #--------------------------------------------------

    def _wrapped_op(self, op, left, right):
        # Check if an active context redefines this binary operator (e.g. for the solvers library).
        for s in self._graph._stack.stack:
            f = getattr(s, "_supports_binary_op", None)
            if f and f(op):
                return s._make_binary_op(op, left, right)
        return Expression(self._graph, op, [left, right])

    def __add__(self, other):
        return self._wrapped_op(Builtins.plus, self, other)
    def __radd__(self, other):
        return self._wrapped_op(Builtins.plus, other, self)

    def __mul__(self, other):
        return self._wrapped_op(Builtins.mult, self, other)
    def __rmul__(self, other):
        return self._wrapped_op(Builtins.mult, other, self)

    def __sub__(self, other):
        return self._wrapped_op(Builtins.minus, self, other)
    def __rsub__(self, other):
        return self._wrapped_op(Builtins.minus, other, self)

    def __truediv__(self, other):
        return self._wrapped_op(Builtins.div, self, other)
    def __rtruediv__(self, other):
        return self._wrapped_op(Builtins.div, other, self)

    def __floordiv__(self, other):
        return self._wrapped_op(Builtins.floor_div, self, other)
    def __rfloordiv__(self, other):
        return self._wrapped_op(Builtins.floor_div, other, self)

    def __pow__(self, other):
        return self._wrapped_op(Builtins.pow, self, other)
    def __rpow__(self, other):
        return self._wrapped_op(Builtins.pow, other, self)

    def __mod__(self, other):
        return self._wrapped_op(Builtins.mod, self, other)
    def __rmod__(self, other):
        return self._wrapped_op(Builtins.mod, other, self)

    def __neg__(self):
        return self._wrapped_op(Builtins.mult, self, -1)

    #--------------------------------------------------
    # Filter overloads
    #--------------------------------------------------

    def __gt__(self, other):
        return self._wrapped_op(Builtins.gt, self, other)
    def __ge__(self, other):
        return self._wrapped_op(Builtins.gte, self, other)
    def __lt__(self, other):
        return self._wrapped_op(Builtins.lt, self, other)
    def __le__(self, other):
        return self._wrapped_op(Builtins.lte, self, other)
    def __eq__(self, other) -> Any:
        return self._wrapped_op(Builtins.approx_eq, self, other)
    def __ne__(self, other) -> Any:
        return self._wrapped_op(Builtins.neq, self, other)

    #--------------------------------------------------
    # Context management
    #--------------------------------------------------

    def __enter__(self):
        self._graph._push(self)

    def __exit__(self, *args):
        self._graph._pop(self)

#--------------------------------------------------
# Context
#--------------------------------------------------

class TaskExecType(Enum):
    Query = 1
    Rule = 2
    Procedure = 3
    Export = 4

class ContextSelect(Producer):
    def __init__(self, context:'Context'):
        super().__init__(context.graph)
        self._context = context
        self._select_len = None
        self._insts = []
        self._vars = []
        self._props = {}

    def _assign_vars(self):
        task = self._context._task
        if not len(self._vars) and self._select_len:
            self._insts = to_list(Vars(self._select_len))
            self._vars = [to_var(v) for v in self._insts]
            task.properties = [Builtins.Relation.properties[i] for i in range(self._select_len)]
            task.bindings.update({Builtins.Relation.properties[i]: v for i, v in enumerate(self._vars)})

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            return None
        if name in self._props:
            return Instance(self._context.graph, ActionType.Get, [], {}, var=to_var(self._props[name]))
        else:
            return getattr(Instance(self._context.graph, ActionType.Get, [], {}, var=to_var(self._vars[0])), name)

    #--------------------------------------------------
    # Return handling
    #--------------------------------------------------

    def _do_return(self, args, distinct=False):
        graph = self._context.graph
        task = self._context._task
        if task.behavior == Behavior.Query \
            and self._context._exec_type in [TaskExecType.Query, TaskExecType.Procedure]:
            if isinstance(args[0], tuple):
                args = args[0]
            export = self._context._format == "snowpark"
            graph._action(build.return_(list(args), export=export, distinct=distinct))
        else:
            #TODO: good error message depending on the type of task we're dealing with
            raise Exception("Can't select in a non-query")
        return self._context

    def __call__(self, *args: Any) -> Any:
        if self._context._done:
            raise errors.SelectOutOfContext()
        return self._do_return(args)

    def distinct(self, *args:Any) -> Any:
        if self._context._done:
            raise errors.SelectOutOfContext()
        return self._do_return(args, distinct=True)

    #--------------------------------------------------
    # Add for `model.match() as m`
    #--------------------------------------------------

    def add(self, item, **kwargs):
        arg_len = len(kwargs) + 1
        if self._select_len is not None and arg_len != self._select_len:
            raise Exception("Add must be provided the same arguments in each branch")
        self._select_len = arg_len
        self._assign_vars()
        if len(self._props) and set(self._props.keys()) != set(kwargs.keys()):
            raise Exception("Add must be provided the same properties in each branch")
        elif len(self._props) == 0:
            for k, v in zip(kwargs.keys(), self._vars[1:]):
                v.name = k
                self._props[k] = v

        graph = self._context.graph
        graph._action(build.relation_action(ActionType.Bind, self._context._task, [item, *[kwargs[k] for k in self._props.keys()]]))

class Context():
    def __init__(self, graph:'Graph', *args, behavior=Behavior.Query, op=None,
                 exec_type=TaskExecType.Rule, dynamic=False, format="default",
                 props=None, engine=None, tag=None, globalize=False, source=None,
                 attributes=None, read_only=False, skip_invalid_data=False):
        self._id = next_id()
        self.results = DataFrame()
        self.graph = graph
        self._task = Task(behavior=behavior)
        self._globalize = globalize
        self._op = op
        self._args = list(args)
        self._exec_type = exec_type
        self._select_len = None
        self._dynamic = dynamic or any([item._dynamic for item in self.graph._stack.stack if isinstance(item, Context)])
        self._props = props or {}
        self._engine= engine
        self._tag = tag # for benchmark reporting
        self._format = self._resolve_format(format)
        self._done = False
        self._source = source
        self._read_only:bool = read_only
        self._skip_invalid_data:bool = skip_invalid_data

        self._validate_attributes(attributes)
        self._attributes = attributes

    def _validate_attributes(self, attributes):
        if attributes is None:
            return True

        for key, value in attributes.items():
            self._validate_attribute_item(key)
            self._validate_attribute_item(value)

    def _validate_attribute_item(self, item):
        assert isinstance(item, str), f"'{item}' must be a string"
        assert len(item) <= MAX_QUERY_ATTRIBUTE_LENGTH, f"'{item}' exceeds the maximum length of {MAX_QUERY_ATTRIBUTE_LENGTH} characters."
        assert re.match(r'^[a-zA-Z0-9_-]+$', item), f"'{item}' must contain only alphanumeric characters, underscores, or hyphens."

    def _resolve_format(self, format):
        if format == "default":
            if self.graph._format != "default":
                return self.graph._format
            if self.graph._config.get("platform") == "snowflake":
                # In the future we may want to default to snowpark
                return "pandas"
            return "pandas"
        return format

    def __enter__(self):
        debugging.set_source(self._task, self._source)
        self.graph._push(self)
        return ContextSelect(self)

    def __exit__(self, *args):
        self._done = True
        # If no exception info has been passed to args,
        # then proceed with the normal exit process.
        # Otherwise, return False to propagate the exception.
        if args[0] is None:
            if not self._dynamic:
                debugging.check_errors(self._task)
            try:
                self.graph._pop(self, globalize=self._globalize)
            except KeyboardInterrupt as e:
                print("Canceling transactions...")
                self.graph.resources.cancel_pending_transactions()
                raise e
            except RAIException as e:
                handle_missing_integration(e)
                raise e.clone(self.graph._config) from None
        else:
            self.graph._pop(self, exec=False)
            if isinstance(args[1], RAIException):
                raise args[1].clone(self.graph._config) from None
        return False

    def __iter__(self):
        if self._exec_type != TaskExecType.Query:
            raise Exception("Can't iterate over a non-query task")
        else:
            return self.results.itertuples(index=False)

    def _repr_html_(self):
        if self._exec_type == TaskExecType.Query:
            if isinstance(self.results, DataFrame):
                return self.results.to_html(index=False)
            elif getattr(self.results, "_repr_html_", None):
                return self.results._repr_html_()
            elif getattr(self.results, "show"):
                self.results.show()
                return ""
            else:
                return str(self.results)

    def __str__(self):
        if self._exec_type == TaskExecType.Query:
            if isinstance(self.results, DataFrame):
                return self.results.to_string(index=False)
            else:
                return str(self.results)
        return super().__str__()

#--------------------------------------------------
# Type
#--------------------------------------------------

def hash_values_sha256_truncated(args):
    combined = ''.join(map(str, args))
    combined_bytes = combined.encode('utf-8')
    hasher = hashlib.sha256()
    hasher.update(combined_bytes)
    hash_128_bit = hasher.digest()[:16]
    return hash_128_bit

# @NOTE: `omit_intrinsic_type_in_hash` exists to keep node hashes (which are namespaced by their graph) stable
#        when new nodes are directly created via `Node.add(x = ..)` instead of marking existing entities as
#        nodes. Possible hash collisions between types happen to be okay in this case because of the access
#        paths, but it's _not_ generally safe to use it otherwise.
class Type(Producer):
    def __init__(self, graph:'Graph', name:str, builtins:List[str] = [], scope:str="", omit_intrinsic_type_in_hash = False):
        super().__init__(graph)
        self._type = mType(scope+name)
        self._scope = scope
        self._omit_intrinsic_type_in_hash = omit_intrinsic_type_in_hash
        if graph._config.get("compiler.use_value_types", False):
            self._type.parents.append(Builtins.ValueType)
        install = build.install(self._type)
        self._graph._action(install)
        debugging.set_source(install)

    def __call__(self, *args, **kwargs):
        return Instance(self._graph, ActionType.Get, [self, *args], kwargs, name=self._type.name.lower(), scope=self._scope)

    def add(self, *args, **kwargs):
        inst = Instance(self._graph, ActionType.Bind, [self, *args], kwargs, name=self._type.name.lower(), is_add=True, scope=self._scope)
        if inst._action.entity.value is not None:
            pass
        elif is_static(args) and is_static(kwargs):
            params = [Var(value=t.name) for t in inst._action.types]
            if self._omit_intrinsic_type_in_hash:
                params.pop(0)
            params.extend(inst._action.bindings.values())
            inst._action.entity.value = hash_values_sha256_truncated(params)
        elif all([isinstance(a, Type) for a in args]):
            self._graph._action(build.ident(inst._action, self._omit_intrinsic_type_in_hash))
        inst._add_to_graph()
        return inst

    def persist(self, *args, **kwargs):
        inst = Instance(self._graph, ActionType.Persist, [self, *args], kwargs, name=self._type.name.lower(), is_add=True, scope=self._scope)
        if inst._action.entity.value is not None:
            pass
        elif is_static(args) and is_static(kwargs):
            params = [Var(value=t.name) for t in inst._action.types]
            params.extend(inst._action.bindings.values())
            inst._action.entity.value = hash_values_sha256_truncated(params)
        elif all([isinstance(a, Type) for a in args]):
            self._graph._action(build.ident(inst._action, self._omit_intrinsic_type_in_hash))
        inst._add_to_graph()
        return inst

    def extend(self, *args, **kwargs):
        for arg in args:
            if not isinstance(arg, Type):
                raise Exception("Can only extend a type with another type")
            with self._graph.rule(dynamic=True):
                a = arg()
                a.set(self)
            with self._graph.rule(dynamic=True):
                a = arg()
                neue = self(a)
                for k, v in kwargs.items():
                    if isinstance(v, Property):
                        v = getattr(a, v._prop.name)
                    neue.set(**{k:v})

    def define(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, tuple):
                (other_type, left, right) = v
                with self._graph.rule():
                    inst = other_type()
                    me = self()
                    getattr(inst, right) == getattr(me, left) # type: ignore
                    if getattr(self, k).is_multi_valued:
                        getattr(me, k).add(inst)
                    else:
                        me.set(**{k: inst})
            else:
                raise Exception("Define requires a tuple of (Type, left, right)")
        return self

    def keyed(self, **kwargs):
        return KeyedType(self, kwargs)

    def __or__(self, __value: Any) -> TypeUnion:
        if isinstance(__value, Type) or isinstance(__value, TypeIntersection):
            return TypeUnion(self._graph, [self, __value])
        if isinstance(__value, TypeUnion):
            return TypeUnion(self._graph, [self, *__value._types])
        raise Exception("Can't or a type with a non-type")

    def __and__(self, __value: Any) -> TypeIntersection:
        if isinstance(__value, Type) or isinstance(__value, TypeUnion):
            return TypeIntersection(self._graph, [self, __value])
        if isinstance(__value, TypeIntersection):
            return TypeIntersection(self._graph, [self, *__value._types])
        raise Exception("Can't & a type with a non-type")

    def _make_sub(self, name: str, existing=None):
        if existing is not None:
            return existing
        return Property(self._graph, name, [self._type], self, scope=self._scope)

    def known_properties(self):
        return [p.name.removeprefix(self._scope) for p in self._type.properties]

#--------------------------------------------------
# KeyedType
#--------------------------------------------------

class KeyedType(Producer):
    def __init__(self, type:Type, keys:Dict[str,Type]):
        super().__init__(type._graph)
        self._type = type
        self._relation = RawRelation(self._graph, type._type.name, len(keys))
        self._key_info = keys
        self._key_order = list(keys.keys())
        self._props = {}

        # declare the relation
        install = build.install(self._relation._type)
        self._graph._action(install)
        debugging.set_source(install)

    def _prop(self, name:str):
        if name not in self._props:
            self._props[name] = RawRelation(self._graph, f"{self._relation._name}_{name}", len(self._key_info)+1)
        return self._props[name]

    def extend(self, *args, **kwargs):
        raise errors.KeyedCantBeExtended()

    def _collect_keys(self, args:List[Any], kwargs:Dict[str,Any]):
        ks = self._key_info.keys()
        all_args = dict(zip(ks, args))
        all_args.update(kwargs)
        props = set(all_args.keys()) - set(ks)
        return all_args, {k: all_args.get(k) for k in ks if k in all_args}, {k: all_args[k] for k in props}

    def add(self, *args:Any, **kwargs):
        all_args, keys, props = self._collect_keys(list(args), kwargs)
        if len(keys) != len(self._key_info):
            raise errors.KeyedWrongArity(self._type._type.name, list(self._key_info.keys()), len(keys))
        self._relation.add(*keys.values())
        for k, v in props.items():
            self._prop(k).add(*keys, v)
        return KeyedInstance(self, list(keys), {})

    def __call__(self, *args, **kwargs):
        all_args, keys, props = self._collect_keys(list(args), kwargs)
        ks = self._key_info.keys()
        keys = [all_args.get(k, Vars(1)) for k in ks]
        self._relation(*keys)
        return KeyedInstance(self, keys, props)

    def __getattr__(self, name: str) -> Any:
        return self._props[name]

class KeyedInstance(Producer):
    def __init__(self, keyed_type:KeyedType, keys:List[Any], kwargs:dict={}):
        self._keys = keys
        self._type = keyed_type
        for k, v in kwargs.items():
            self._type._prop(k)(*keys, v)

    def __getattr__(self, name:str):
        if name in self._type._key_order:
            return self._keys[self._type._key_order.index(name)]
        v = Vars(1)
        self._type._prop(name)(*self._keys, v)
        return v

    def set(self, **kwargs):
        for k, v in kwargs.items():
            self._type._prop(k).add(*self._keys, v)
        return self

    def __iter__(self):
        return iter(self._keys)

    def _to_var(self):
        raise Exception("KeyedTypes can't be returned directly, you can only reference properties")

#--------------------------------------------------
# TypeUnion
#--------------------------------------------------

class TypeUnion(Producer):
    def __init__(self, graph:'Graph', types:List[Type|TypeIntersection]):
        super().__init__(graph)
        self._types = types

    def __call__(self, *args, **kwargs) -> 'ContextSelect':
        if not len(self._graph._stack.stack):
            raise Exception("Can't create an instance outside of a context")
        graph = self._graph
        with graph.union(dynamic=True) as union:
            for t in self._types:
                with graph.scope():
                    union.add(t(*args, **kwargs))
        return union

    def known_properties(self):
        props = []
        for t in self._types:
            for prop in t.known_properties():
                if prop not in props:
                    props.append(prop)
        return props

    def __or__(self, __value: Any) -> 'TypeUnion':
        if isinstance(__value, Type):
            return TypeUnion(self._graph, [*self._types, __value])
        if isinstance(__value, TypeUnion):
            return TypeUnion(self._graph, [*self._types, *__value._types])
        raise Exception("Can't or a type with a non-type")

    def _make_sub(self, name: str, existing=None):
        if existing is not None:
            return existing
        return Property(self._graph, name, [t._type for t in self._types], self)

#--------------------------------------------------
# TypeIntersection
#--------------------------------------------------

class TypeIntersection(Producer):
    def __init__(self, graph:'Graph', types:List[Type|TypeUnion]):
        super().__init__(graph)
        self._types = types

    def __call__(self, *args, **kwargs) -> Producer:
        if not len(self._graph._stack.stack):
            raise Exception("Can't create an instance outside of a context")
        return self._types[0](*self._types[1:], *args, **kwargs)

    def known_properties(self):
        props = []
        for t in self._types:
            for prop in t.known_properties():
                if prop not in props:
                    props.append(prop)
        return props

    def __and__(self, __value: Any) -> TypeIntersection:
        if isinstance(__value, Type):
            return TypeIntersection(self._graph, [*self._types, __value])
        if isinstance(__value, TypeIntersection):
            return TypeIntersection(self._graph, [*self._types, *__value._types])
        raise Exception("Can't & a type with a non-type")

    def _make_sub(self, name: str, existing=None):
        if existing is not None:
            return existing
        return Property(self._graph, name, [t._type for t in self._types], self)

#--------------------------------------------------
# Property
#--------------------------------------------------

class Property(Producer):
    def __init__(self, graph:'Graph', name:str, types:List[mType], provider:Type|TypeUnion|TypeIntersection, scope:str=""):
        super().__init__(graph)
        self._name = name
        self._type = types[0]
        self._scope = scope
        self._provider = provider
        self._prop = build.property_named(scope+name, types)

    def __call__(self, key:Any, value:Any):
        action = build.relation_action(ActionType.Get, self._prop, [key, value])
        self._graph._action(action)

    def _use_var(self):
        raise Exception("Support properties being used as vars")

    def _make_sub(self, name: str, existing=None):
        raise Exception("Support properties on properties?")

    def to_property(self):
        return self._prop

    def declare(self):
        self._graph._action(build.install(self._prop))

    def has_many(self):
        self.declare()
        self._graph._check_property(self._prop, multi_valued=True)

    @property
    def is_multi_valued(self):
        return self._graph._prop_is_multi.get(self._name)

#--------------------------------------------------
# Instance
#--------------------------------------------------

class Instance(Producer):
    def __init__(self, graph:'Graph', action_type:ActionType, positionals:List[Any], named:Dict[str,Any], var:Var|None=None, name=None, is_add=False, scope:str=""):
        super().__init__(graph)
        self._action = Action(action_type, to_var(var) if var else Var(name=name))
        self._actions = [self._action]
        self._sets = {}
        self._context = graph._stack.active()
        self._scope = scope
        available_types = []
        last_pos_var = None

        #--------------------------------------------------
        # Positionals
        #--------------------------------------------------
        has_ident = False
        for pos in positionals:
            if isinstance(pos, Type):
                self._action.append(pos._type)
            elif isinstance(pos, Instance):
                if has_ident:
                    raise MultipleIdentities()
                has_ident = True
                self._action.append(to_var(pos))
                available_types.extend(pos._action.types)
                if last_pos_var:
                    self._graph._action(build.eq(last_pos_var, self._action.entity))
                last_pos_var = self._action.entity
            elif isinstance(pos, TypeUnion) or isinstance(pos, TypeIntersection):
                self._action.append(to_var(pos()))
                available_types.extend([t._type for t in pos._types])
                if last_pos_var:
                    self._graph._action(build.eq(last_pos_var, self._action.entity))
                last_pos_var = self._action.entity
            elif isinstance(pos, Producer):
                if has_ident:
                    raise MultipleIdentities()
                has_ident = True
                self._action.append(to_var(pos))
                if last_pos_var:
                    self._graph._action(build.eq(last_pos_var, self._action.entity))
                last_pos_var = self._action.entity
            elif isinstance(pos, (str, int)):
                if has_ident:
                    raise MultipleIdentities()
                has_ident = True
                if isinstance(pos, str):
                    try:
                        decoded = base64.b64decode(pos + "==")
                        if len(decoded) == 16:
                            first_int = decoded[:8]
                            second_int = decoded[8:]
                            pos = struct.pack('<Q', struct.unpack('>Q', second_int)[0]) + \
                                      struct.pack('<Q', struct.unpack('>Q', first_int)[0])
                    except Exception:
                        pass
                self._action.append(Var(value=pos))
                last_pos_var = self._action.entity
            else:
                raise Exception(f"Unknown input type: {pos}")
        available_types.extend(self._action.types)
        if scope:
            available_types = [t for t in available_types if t.name.startswith(scope)]

        #--------------------------------------------------
        # Handle properties
        #--------------------------------------------------
        for name, val in named.items():
            prop = build.property_named(scope+name, available_types)

            if val is None:
                raise Exception(f"{prop}'s value is None, please provide a value for the property")

            if isinstance(val, int) and action_type == ActionType.Get:
                orig = val
                val = Vars(1)
                self._actions.append(build.eq(val, orig, approx=True))

            prop_var = to_var(val)

            if prop_var.isa(Builtins.ExternalInput):
                orig = prop_var
                prop_var = to_var(Vars(1))
                self._actions.append(build.eq(prop_var, orig, approx=True))

            if is_collection(prop_var.value):
                raise Exception("Can't set a property to a collection")

            if not prop_var.name:
                prop_var.name = prop.name
            if action_type.is_effect():
                self._graph._check_property(prop)
            else:
                self._graph._check_property(prop, unknown_cardinality=True)
            self._action.append(prop, prop_var)

        #--------------------------------------------------
        # Entities
        #--------------------------------------------------
        self._var = self._action.entity
        if self._var.type == Builtins.Unknown and len(self._action.types):
            self._var.type = self._action.types[0]
        if not is_add and (self._action.types or self._action.bindings):
            self._add_to_graph()

    def _to_var(self):
        if not self._graph._stack.contains(self._context):
            exception = VariableOutOfContextException(Errors.call_source(), self._var.name)
            raise exception from None
        return self._var

    def _add_to_graph(self):
        for action in self._actions:
            self._graph._action(action)

    def __call__(self, *args, **kwargs):
        pass

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            return super().__setattr__(name, value)
        exception = InvalidPropertySetException(Errors.call_source(3))
        raise exception from None

    def _make_sub(self, name: str, existing=None):
        if self._sets.get(name) is not None:
            return self._sets[name]
        if existing is not None:
            inst = InstanceProperty(self._graph, self, name, var=existing._var, scope=self._scope)
            inst._subs = existing._subs
            return inst
        prop = build.property_named(self._scope+name, self._action.types)
        if self._action.bindings.get(prop):
            return InstanceProperty(self._graph, self, name, var=self._action.bindings[prop], scope=self._scope)
        return InstanceProperty(self._graph, self, name, scope=self._scope)

    def set(self, *args, **kwargs):
        if self._graph._stack.active() is self._context:
            self._sets.update(kwargs)
        Instance(self._graph, ActionType.Bind, [self, *args], kwargs, var=self._var, scope=self._scope)
        return self

    def persist(self, *args, **kwargs):
        Instance(self._graph, ActionType.Persist, [self, *args], kwargs, var=self._var, scope=self._scope)
        return self

    def unpersist(self, *args, **kwargs):
        Instance(self._graph, ActionType.Unpersist, [self, *args], kwargs, var=self._var, scope=self._scope)
        return self

    def has_value(self):
        return self != rel.Missing # type:ignore

#--------------------------------------------------
# InstanceProperty
#--------------------------------------------------

class InstanceProperty(Producer):
    def __init__(self, graph:'Graph', instance:Instance, name:str, var=None, scope:str=""):
        super().__init__(graph)
        self._instance = instance

        self._prop = build.property_named(scope+name, instance._action.types)
        self._var = var or Var(self._prop.type, name=name)
        self._check_context()
        self._scope = scope
        new = Instance(self._graph, ActionType.Get, [instance], {name: self._var}, scope=self._scope)
        self._action = new._action

    def _check_context(self):
        if not self._graph._stack.contains(self._instance._context):
            name = f"{self._instance._var.name}.{self._var.name}"
            exception = VariableOutOfContextException(Errors.call_source(), name, is_property=True)
            raise exception from None

    def __call__(self, *args, **kwargs):
        name = f"{self._instance._var.name}.{self._var.name}"
        exception = NonCallablePropertyException(Errors.call_source(), name)
        raise exception from None

    def _make_sub(self, name: str, existing=None):
        if existing is not None and self._graph._stack.is_active(existing._instance._context):
            return existing
        return getattr(Instance(self._graph, ActionType.Get, [self], {}), name)

    def _to_var(self):
        self._check_context()
        return self._var

    def or_(self, other):
        self._graph._remove_action(self._action)
        default = build.call(Builtins.Default, [self._prop, other, self._instance, self])
        self._graph._action(default)
        return self

    def in_(self, others):
        other_rel = InlineRelation(self._graph, [(x,) for x in others])
        return self == other_rel

    def has_value(self):
        return self != rel.Missing # type:ignore

    def _remove_if_unused(self):
        # When calling append/extend we aren't necessarily doing a get on the property,
        # but we will already have added one. If we're the only thing using this get,
        # we remove it so that it doesn't unnecessarily constrain the query.
        remove = False
        for item in reversed(self._graph._stack.items):
            if item is self._action:
                remove = True
                break
            elif isinstance(item, Action):
                if self._var in item.vars():
                    remove = False
                    break
        if remove:
            self._graph._remove_action(self._action)

    def set(self, *args, **kwargs):
        return Instance(self._graph, ActionType.Get, [self], {}).set(*args, **kwargs)

    def add(self, other):
        self._remove_if_unused()
        self._graph._check_property(self._prop, multi_valued=True)
        rel = Action(ActionType.Bind, to_var(self._instance), [], {self._prop: to_var(other)})
        self._graph._action(rel)

    def extend(self, others):
        self._remove_if_unused()
        self._graph._check_property(self._prop, True)
        for other in others:
            rel = Action(ActionType.Bind, to_var(self._instance), [], {self._prop: to_var(other)})
            self._graph._action(rel)

    def choose(self, num, unique=True):
        if num < 1:
            raise ValueError("Must choose a positive number of items")
        self._remove_if_unused()
        items = [getattr(Instance(self._graph, ActionType.Get, [self._instance], {}), self._prop.name) for ix in range(num)]
        if unique:
            for ix in range(num-1):
                items[ix] < items[ix+1]
        return items

#--------------------------------------------------
# Expression
#--------------------------------------------------

class Expression(Producer):
    def __init__(self, graph:'Graph', op:mType|Task, args:List[Any]):

        super().__init__(graph)
        self._var = None
        self._context = graph._stack.active()

        # For calls to tasks with known signatures, normalize their arguments by
        # throwing on missing inputs or constructing vars for missing outputs
        if op.properties and not op.isa(Builtins.Anonymous):
            for prop, arg in zip_longest(op.properties, args):
                if arg is None:
                    if prop.is_input:
                        raise TypeError(f"{op.name} is missing a required argument: '{prop.name}'")
                    else:
                        args.append(Var(prop.type, name=prop.name))

            # Expose the last output as the result, to ensure we don't double-create it in _use_var.
            # @NOTE: Literal values like 1 show up here from calls like `rel.range(0, len(df), 1)`
            if not op.properties[-1].is_input and isinstance(args[-1], Var):
                self._var = args[-1]

        self._expr = build.call(op, args)
        self._graph._action(self._expr)

    def __call__(self, *args, **kwargs):
        raise Exception("Expressions can't be called")

    def _use_var(self):
        if self._expr.entity.isa(Builtins.Filter):
            if isinstance(runtime_env, SnowbookEnvironment):
                return
            raise FilterAsValue(Errors.call_source())
        elif not self._var:
            self._var = Var(Builtins.Unknown)
            prop = build.property_named("result", self._expr.types)
            self._expr.append(prop, self._var)

        if not self._graph._stack.contains(self._context):
            exception = VariableOutOfContextException(Errors.call_source(), self._var.name or "a result")
            raise exception from None

    def _make_sub(self, name: str, existing=None):
        if existing is not None and existing._instance._context is self._graph._stack.active():
            return existing
        return getattr(Instance(self._graph, ActionType.Get, [self], {}), name)

    def has_value(self):
        return self != rel.Missing # type:ignore

#--------------------------------------------------
# RelationNS
#--------------------------------------------------

unsafe_symbol_pattern = re.compile(r"[^a-zA-Z0-9_]", re.UNICODE)
def safe_symbol(name: str):
    return f':"{name}"' if unsafe_symbol_pattern.search(name) else f":{name}"

class RelationNS():
    def __init__(self, ns:List[str], name:str, use_rel_namespaces=False, tags:List[mType]=[]):
        if name == "getdoc":
            rich.print("[red bold]GETDOC CALLED")
            traceback.print_stack()
            return
        self._name = name
        self._ns = ns
        self._subs = {}
        self._use_rel_namespaces = use_rel_namespaces
        self._rel = self._build_rel()
        self._tags = tags

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        op = self._rel
        for t in self._tags:
            tag(self, t)
        self._ensure_args(len(args))
        return Expression(get_graph(), op, list(args))

    def __getattr__(self, name: str) -> RelationNS:
        self._subs[name] = self._make_sub(name, self._subs.get(name))
        return self._subs[name]

    def _make_sub(self, name: str, existing=None):
        if existing is not None:
            return existing
        ns = self._ns[:]
        if self._name:
            ns.append(self._name)
        return self.__class__(ns, name, use_rel_namespaces=self._use_rel_namespaces, tags=self._tags)

    def _build_rel(self, arg_count = 0):
        fqn_parts = self._ns + [self._name]
        if self._use_rel_namespaces:
            return build.relation('::'+'::'.join(fqn_parts), arg_count)
        if len(fqn_parts) == 1:
            return build.relation(fqn_parts[0], arg_count)
        else:
            return build.relation(f"{fqn_parts[0]}[{', '.join(safe_symbol(part) for part in fqn_parts[1:])}]", arg_count)

    def _ensure_args(self, arg_count):
        if len(self._rel.properties) <= arg_count:
            self._rel.properties = [Builtins.Relation.properties[i] for i in range(arg_count)]

    def add(self, *args):
        op = self._rel
        self._ensure_args(len(args))
        get_graph()._action(build.relation_action(ActionType.Bind, op, list(args)))

    def _to_var(self):
        return Var(Builtins.Relation, value=self._build_rel())

    def _tagged(self, *tags: mType):
        return self.__class__(self._ns, self._name, use_rel_namespaces=self._use_rel_namespaces, tags=list(tags))

#--------------------------------------------------
# RawRelation
#--------------------------------------------------

class RawRelation(Producer):
    def __init__(self, graph:'Graph', name:str, arity:int):
        super().__init__(graph)
        self._name = name
        self._arity = arity
        self._type = build.relation(self._name, self._arity)

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return Expression(self._graph, self._type, list(args))

    def add(self, *args):
        self._graph._action(build.relation_action(ActionType.Bind, self._type, list(args)))

    def _make_sub(self, name: str, existing=None):
        return existing

    def _to_var(self):
        return Var(Builtins.Relation, value=self._type)

#--------------------------------------------------
# InlineRelation
#--------------------------------------------------

class InlineRelation():
    def __init__(self, graph:'Graph', data:List[Tuple]):
        self._var = Var(type=Builtins.InlineRawData)
        self._graph = graph
        cols = [[] for _ in range(len(data[0]))]
        for row in data:
            for i, val in enumerate(row):
                cols[i].append(to_var(val))

        params = [Var(value=col) for col in cols]
        params.append(self._var)
        q = build.relation_action(ActionType.Get, Builtins.InlineRawData, params)
        self._graph._action(q)

    def _to_var(self):
        return self._var

#--------------------------------------------------
# Rows
#--------------------------------------------------

class Rows():
    def __init__(self, graph:'Graph', data:List[Any]):
        self._graph = graph

        col_names = []
        data_cols = []

        size = len(data)
        warning_size = 1000
        error_size = 10000
        if size > error_size:
            raise errors.RowLiteralTooLarge(size, max_size=error_size)
        elif size > warning_size:
            errors.RowLiteralTooLargeWarning(size, max_size=warning_size)

        first = data[0]
        if isinstance(first, dict):
            col_names = list(first.keys())
            data_cols = [[] for _ in range(len(col_names))]
            for row in data:
                for ix, col in enumerate(col_names):
                    if col not in row:
                        raise errors.RowLiteralMismatch("keys")
                    data_cols[ix].append(row[col])
        elif isinstance(first, tuple):
            data_cols = [[] for _ in range(len(first))]
            for row in data:
                if len(row) != len(first):
                    raise errors.RowLiteralMismatch("length")
                for ix, col in enumerate(row):
                    data_cols[ix].append(col)
        elif isinstance(first, list):
            data_cols = [data]
        else:
            raise Exception("Unsupported data type: must be a list")

        data_vars = [Var(value=col) for col in data_cols]
        if col_names:
            vars = [Var(name=name) for name in col_names]
        else:
            vars = [Var() for _ in range(len(data_vars))]

        self._fetch = build.relation_action(ActionType.Get, Builtins.RawData, [*data_vars, *vars])
        self._var = vars[-1]
        self._vars = vars
        self._columns = col_names

    def _add_to_graph(self):
        if not self._graph._in_rule():
            raise errors.OutOfContextException()
        self._graph._action(self._fetch, dedupe=True)

    def _to_var(self):
        self._add_to_graph()
        return self._var

    def __getitem__(self, index):
        self._add_to_graph()
        if isinstance(index, str):
            return getattr(self, index)
        return self._vars[index]

    def __getattr__(self, name):
        if name in self._columns:
            self._add_to_graph()
            return self._vars[self._columns.index(name)]
        raise AttributeError(f"Set has no attribute '{name}'")

#--------------------------------------------------
# Symbol
#--------------------------------------------------

class Symbol():
    def __init__(self, name:str):
        self._var = Var(Builtins.Symbol, value=name)

    def _to_var(self):
        return self._var

#--------------------------------------------------
# RelationRef
#--------------------------------------------------

class RelationRef(Producer):
    def __init__(self, graph:'Graph', rel:Task|mType, args:List[Var]):
        super().__init__(graph)
        self._rel = rel
        self._args = args
        self._var = args[-1]
        self._action = build.relation_action(ActionType.Get, self._rel, self._args)

    def _use_var(self):
        self._graph._action(self._action)

    def _make_sub(self, name: str, existing=None):
        return getattr(Instance(self._graph, ActionType.Get, [self], {}), name)

    def __enter__(self):
        super().__enter__()
        self._use_var()
        Instance(self._graph, ActionType.Get, [self], {}).has_value()

#--------------------------------------------------
# Export
#--------------------------------------------------

allowed_export_types = [Type, str, numbers.Number, datetime.datetime, datetime.date, bool]

def check_type(name, type):
    if not any(isinstance(type, t) or (inspect.isclass(type) and issubclass(type, t))
                for t in allowed_export_types):
        raise TypeError(f"Argument '{name}' is an unsupported type: {type}")

def export(model, schema, kwargs):
    try:
        parser = IdentityParser(schema)
    except ParseError as e:
        raise Exception(f"Not able to parse provided schema '{schema}'. {e}")

    def decorator(func):
        # Get type hints of the function
        hints = get_type_hints(func)
        input_types = [hints[name] for name in hints if name != 'return']
        arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
        for name in arg_names:
            if name not in hints:
                raise TypeError(f"Argument '{name}' must have a type hint")
            check_type(name, hints[name])

        output_types = []
        has_return_hint = 'return' in hints
        if has_return_hint:
            ret = hints.get('return')
            if typing.get_origin(ret) is tuple:
                for t in typing.get_args(ret):
                    check_type("return", t)
                    output_types.append(t)
            else:
                check_type("return", ret)
                output_types.append(ret)
        name = f"{schema}.{func.__name__}" if schema else func.__name__
        props = {
            "name": name if parser.entity is None else parser.identity,
            "outputs": output_types if has_return_hint else None,
        }

        ctx = Context(model, exec_type=TaskExecType.Procedure, props=props, format="snowpark", **kwargs)
        with ctx as ret:
            inputs = to_list(Vars(len(arg_names)))
            for i in inputs:
                i._var.type = Builtins.ExternalInput
            props["inputs"] = list(zip(arg_names, [to_var(i) for i in inputs], input_types))
            outs = to_list(func(*inputs))
            if has_return_hint and len(outs) != len(output_types):
                raise TypeError(f"Function '{func.__name__}' must return {len(output_types)} values according to the type hints")
            ret(*outs)

        def wrapper():
            raise Exception("Exports can't be called directly. They are exported to the underlying platform")

        return wrapper
    return decorator

#--------------------------------------------------
# RuleStack
#--------------------------------------------------

class RuleStack():
    def __init__(self, graph:'Graph'):
        self.items = []
        self.stack = []
        self._graph = graph

    def push(self, item):
        self.stack.append(item)
        self.items.append(("push", item))

    def pop(self, item, globalize=False):
        self.stack.pop()
        self.items.append(("pop", item))
        if len(self.stack) == 0:
            compacted = self.compact()
            self.items.clear()
            if len(compacted.items):
                return compacted
        elif globalize:
            ix = self.items.index(("push", item))
            temp_items = self.items[0:ix]
            self.items = self.items[ix:]
            compacted = self.compact()
            self.items = temp_items
            if len(compacted.items):
                return compacted

    def push_item(self, item):
        if not len(self.stack):
            raise Exception("Can't push a non-context item onto an empty stack")
        self.items.append(item)

    def contains(self, item):
        for i in self.stack:
            if i is item:
                return True

    def is_active(self, item):
        if isinstance(item, Context) and item._task.behavior != Behavior.Query:
            return False
        return item is self.active()

    def in_context(self, item):
        if isinstance(item, Context) and item._task.behavior != Behavior.Query:
            return False
        return self.contains(item)

    def active(self):
        try:
            cur = self.stack[-1]
            if cur is self._graph._temp_rule:
                exception = OutOfContextException(Errors.call_source())
                raise exception from None
            return cur
        except IndexError:
            exception = OutOfContextException(Errors.call_source())
            raise exception from None

    def _expression_start(self, buffer, single_use_vars):
        consume_from = -1
        if not len(buffer):
            return consume_from
        # we can only pull vars if their only use is for this condition
        used_vars = set(buffer[-1].requires_provides()[0] & single_use_vars)
        # walk buffer in reverse collecting vars in the action until we get one
        # that doesn't provide a var we care about
        for action in reversed(buffer[:-1]):
            if not isinstance(action, Action):
                break
            req, provs, _ = action.requires_provides()
            # don't pull in vars the represent root entities even though they're provided
            # by gets. This prevents scenarios where p = Person() would get pulled in if you
            # did with p.age > 10:
            provs = provs - {action.entity}
            if len(used_vars.intersection(provs)):
                used_vars.update(req & single_use_vars)
                consume_from -= 1
            else:
                break
        return consume_from

    def compact(self) -> Task:
        stack:List[Task] = []
        buffer = []

        var_uses = {}
        for item in self.items:
            if isinstance(item, Action):
                if item.action == ActionType.Get:
                    for var in item.vars():
                        var_uses[var] = var_uses.get(var, 0) + 1
                else:
                    for var in item.vars():
                        var_uses[var] = var_uses.get(var, 0) - 1

        # check for 2 refs - one create and one use
        single_use_vars = set([var for var, uses in var_uses.items() if uses >= 0])

        for item in self.items:
            if not isinstance(item, tuple):
                buffer.append(item)
                continue

            op, value = item
            if op == "push":
                if isinstance(value, Context):
                    if len(buffer):
                        stack[-1].items.extend(buffer)
                        buffer.clear()
                    task = value._task
                elif isinstance(value, RelationRef):
                    if len(buffer):
                        stack[-1].items.extend(buffer)
                        buffer.clear()
                    task = Task()

                elif isinstance(value, Producer):
                    consume_from = self._expression_start(buffer, single_use_vars)
                    stack[-1].items.extend(buffer[:consume_from])
                    buffer = buffer[consume_from:]
                    task = Task()
                else:
                    raise Exception(f"Unknown push type: {type(value)}")

                stack.append(task)

            elif op == "pop":
                cur = stack.pop()
                cur.items.extend(buffer)
                buffer.clear()
                if not len(stack):
                    return cur
                if isinstance(value, Context) and value._op:
                    stack[-1].items.append(build.call(value._op, [Var(value=value._args), Var(Builtins.Task, value=cur)]))
                else:
                    stack[-1].items.append(build.call(cur, list(cur.bindings.values())))

        raise Exception("No task found")

#--------------------------------------------------
# Graph
#--------------------------------------------------

locals = threading.local()
locals.graph_stack = []

def get_graph() -> 'Graph':
    _ensure_stack()
    if not len(locals.graph_stack):
        raise Exception("Outside of a model context")
    return locals.graph_stack[-1]

def _ensure_stack():
    if not hasattr(locals, "graph_stack"):
        locals.graph_stack = []
    return locals.graph_stack

rel = RelationNS([], "")
global_ns = RelationNS([], "", use_rel_namespaces=True)

def alias(ref:Any, name:str):
    var = to_var(ref)
    var.name = name
    return var

def tag(ref:Any, tag:mType):
    if isinstance(ref, RelationNS):
        parents = ref._rel.parents
    elif isinstance(ref, Type):
        parents = ref._type.parents
    elif isinstance(ref, Property):
        parents = ref._type.parents
    else:
        return
    if tag not in parents:
        parents.append(tag)

def create_var() -> Instance:
    return Instance(get_graph(), ActionType.Get, [], {}, Var(Builtins.Unknown))

def create_vars(count: int) -> List[Instance]:
    return [create_var() for _ in range(count)]

def Vars(count: int):
    if count == 1:
        return create_var()
    return create_vars(count)

class Graph:
    def __init__(self, client:Client, name:str, format:str="default"):
        self.name = name
        self._executed = []
        self._client = client
        self._config = client.resources.config
        self.resources = client.resources
        self._prop_is_multi:Dict[str, bool] = {}
        self._format = format
        self._stack = RuleStack(self)
        self._restore_temp()

        self._Error = Type(self, "Error", scope="pyrel_error_")
        self._error_props = set()


    #--------------------------------------------------
    # Rule stack
    #--------------------------------------------------

    def _flush_temp(self):
        if self._temp_rule:
            self._pop(self._temp_rule, is_temp=True)
            if not len(_ensure_stack()):
                _ensure_stack().append(self)
            self._temp_rule = None

    def _restore_temp(self):
        self._temp_rule = Context(self)
        _ensure_stack().append(self)
        self._stack.push(self._temp_rule)

    def _temp_is_active(self):
        return self._temp_rule and len(self._stack.items) > 1

    def _in_rule(self):
        return not self._temp_rule

    def _push(self, item):
        _ensure_stack().append(self)
        self._flush_temp()
        self._stack.push(item)

    def _pop(self, item, exec=True, is_temp=False, globalize=False):
        _ensure_stack().pop()
        task = self._stack.pop(item, globalize=globalize)
        try:
            if exec and task:
                self._exec(item, task)
        finally:
            if not is_temp and not len(self._stack.stack):
                self._restore_temp()

    def _action(self, action:Action|List[Action], dedupe=False):
        if isinstance(action, list):
            for a in action:
                self._action(a, dedupe=dedupe)
            return
        if dedupe and self._stack.contains(action):
            return
        self._stack.push_item(action)

    def _remove_action(self, action):
        self._stack.items.remove(action)

    def _exec(self, context:Context, task):
        props = context._props
        if context._exec_type == TaskExecType.Rule:
            self._client.install(f"rule{len(self._executed)}", context._task)
        elif context._exec_type == TaskExecType.Query:
            headers = {QUERY_ATTRIBUTES_HEADER: json.dumps(context._attributes)} if context._attributes else {}
            context.results = self._client.query(context._task, tag=context._tag, format=context._format, headers=headers, read_only=context._read_only, skip_invalid_data=context._skip_invalid_data)
        elif context._exec_type == TaskExecType.Procedure:
            self._client.export_udf(props["name"], props["inputs"], props["outputs"], context._task, props.get("engine"), skip_invalid_data=context._skip_invalid_data)
        elif context._exec_type == TaskExecType.Export:
            self._client.export_table(props["name"], props["rel"], props["columns"], context._task, engine=props.get("engine"), refresh=props.get("refresh"))
        self._executed.append(context)

    #--------------------------------------------------
    # Property handling
    #--------------------------------------------------

    def _check_property(self, prop:mProperty, multi_valued=False, unknown_cardinality=False):
        name = prop.name
        if name in RESERVED_PROPS:
            exception = ReservedPropertyException(Errors.call_source(), name)
            raise exception from None

        if unknown_cardinality:
            if name in self._prop_is_multi and self._prop_is_multi[name] and Builtins.MultiValued not in prop.parents:
                prop.parents.append(Builtins.MultiValued)
            return

        if name in self._prop_is_multi:
            if self._prop_is_multi[name] != multi_valued:
                raise Exception(
                    f"Trying to use a property `{name}` as both singular and multi-valued. "
                    "This often happens when multiple types have a property with the same name, but one is single-valued and the other is multi-valued. "
                    "Consider using a plural name for the multi-valued property. "
                    "See https://relational.ai/docs/develop/core-concepts#setting-object-properties for more information."
                )
            elif self._prop_is_multi[name] and Builtins.MultiValued not in prop.parents:
                prop.parents.append(Builtins.MultiValued)
        else:
            self._prop_is_multi[name] = multi_valued

        if not multi_valued and Builtins.FunctionAnnotation not in prop.parents:
            prop.parents.append(Builtins.FunctionAnnotation)
        elif multi_valued and Builtins.MultiValued not in prop.parents:
            prop.parents.append(Builtins.MultiValued)

    #--------------------------------------------------
    # Public API
    #--------------------------------------------------

    def Type(self, name:str, source=None):
        if source:
            return self.resources.to_model_type(self, name, source)
        return Type(self, name)

    def _error_like(self, message:str, kwargs:Dict[str, Any], is_error:bool):
        kwargs["message"] = message
        kwargs["severity"] = "error" if is_error else "warning"
        source = Errors.call_source()
        id = 0
        if source:
            id = len(errors.ModelError.error_locations)
            errors.ModelError.error_locations[id] = source
            kwargs["pyrel_id"] = id
        for k, v in kwargs.items():
            if k not in self._error_props:
                self._error_props.add(k)
                with self.rule():
                    e = self._Error()
                    rel.output.pyrel_error.add(e, k, getattr(e, k))
        if is_error:
            with self.case():
                self._Error(pyrel_id=id)
                rel.abort.add()
        return self._Error.add(**kwargs)

    def error(self, message:str, **kwargs):
        return self._error_like(message, kwargs, is_error=True)

    def warn(self, message:str, **kwargs):
        return self._error_like(message, kwargs, is_error=False)

    def rule(self, **kwargs):
        return Context(self, **kwargs)

    def scope(self, **kwargs):
        return Context(self, **kwargs)

    def case(self, **kwargs):
        return Context(self, **kwargs)

    def match(self, multiple=False, **kwargs):
        if not multiple:
            return Context(self, behavior=Behavior.OrderedChoice, **kwargs)
        else:
            return Context(self, behavior=Behavior.Union, **kwargs)

    def query(self, **kwargs):
        return Context(self, exec_type=TaskExecType.Query, **kwargs)

    def export(self, object:str = "", **kwargs):
        return export(self, object, kwargs)

    def found(self, **kwargs):
        return Context(self, op=Builtins.Exists, **kwargs)

    def not_found(self, **kwargs):
        return Context(self, op=Builtins.Not, **kwargs)

    def union(self, **kwargs):
        return Context(self, behavior=Behavior.Union, **kwargs)

    def ordered_choice(self, **kwargs):
        return Context(self, behavior=Behavior.OrderedChoice, **kwargs)

    def read(self, name:str, **kwargs):
        from v0.relationalai.loaders.loader import read_resource_context # We do the late import to break an dependency cycle
        return read_resource_context(self, name, **kwargs)

    def load_raw(self, path:str):
        if os.path.isfile(path):
            if path.endswith('.rel'):
                self._client.load_raw_file(path)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith('.rel'):
                        file_path = os.path.join(root, file)
                        self._client.load_raw_file(file_path)

    def exec_raw(self, code:str, readonly=False, raw_results=True, abort_on_error=True, inputs={}, query_timeout_mins: Optional[int]=None):
        try:
            return self._client.exec_raw(code, readonly=readonly, raw_results=raw_results, inputs=inputs, abort_on_error=abort_on_error, query_timeout_mins=query_timeout_mins)
        except KeyboardInterrupt as e:
            print("Canceling transactions...")
            self.resources.cancel_pending_transactions()
            raise e
        except RAIException as e:
            raise e.clone(self._config) from None

    def install_raw(self, code:str, name:str|None = None, overwrite=False):
        self._client.install_raw(code, name, overwrite)
