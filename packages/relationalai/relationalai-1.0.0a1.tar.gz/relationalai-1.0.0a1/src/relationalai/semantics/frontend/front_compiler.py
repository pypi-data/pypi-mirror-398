from __future__ import annotations
from contextlib import contextmanager
from enum import Enum
from functools import lru_cache, wraps
from itertools import chain
from re import sub
from typing import Any, Optional, Sequence, cast
from collections.abc import Iterable

from ...util.naming import Namer, sanitize
from ...util.source import SourcePos
from ...util.structures import KeyedDict, KeyedSet, OrderedSet
from .pprint import pprint
from ..metamodel.builtins import builtins as bt
from ..metamodel.pprint import pprint as mmpp, print_tree
from ...util.error import Diagnostic, Part, err, warn, source as err_source, exc

from .base import (
    Alias, AsBool, CoreConcepts, CoreRelationships, DSLBase, Data, DerivedColumn, Distinct, Field, FieldRef, FilterBy, Group, Library, Literal, Model, Fragment, ModelEnum, New, Not, Chain,
    Property, Ref, Relationship, Concept, Expression, Statement, Table, TableSchema, TupleVariable, Value, Variable, Match, Union, dsl_key, is_primitive,
    NumberConcept, Reading, Aggregate, MetaRef
)
from ..metamodel.metamodel import (
    Aggregate as mAggregate, Annotation, Construct, Effect, FieldType, ISeq, ListType, Logical, Node, NoneType, NumberType, Relation, RelationType, Require, ScalarType, Overload,
    Lookup, TupleType, TypeNode, UnresolvedRelation, Var, Task, Literal as mLiteral, Value as mValue, Table as mTable, Update,
    Field as mField, Not as mNot, Reading as mReading, Match as mMatch, Union as mUnion, Data as mData, Model as mModel
)

#------------------------------------------------------
# Memoize
#------------------------------------------------------

def memoize_in_ctx(method):
    """Cache results in ctx.seen using id(node) as the key."""
    @wraps(method)
    def wrapper(self, ctx, node, *args, **kwargs):
        seen = ctx.seen
        key = id(node)
        if key in seen:
            return seen[key]
        seen[key] = result = method(self, ctx, node, *args, **kwargs)
        return result
    return wrapper

#------------------------------------------------------
# Helpers
#------------------------------------------------------

def find_keys(item: Value | Statement, root_only: bool = False) -> list[Value]:
    if isinstance(item, (Concept, Ref)):
        return [item]
    if isinstance(item, Chain):
        keys = []
        if not root_only and not isinstance(item._next, Property) and len(item._next._fields) > 1:
            keys.extend([FieldRef(item, ix + 1, field, ix + 1) for ix, field in enumerate(item._next._fields[1:-1])])
            keys.append(item)
        keys.extend(find_keys(item._start, root_only))
        return keys
    if isinstance(item, Relationship):
        if root_only:
            return [item]
        return list(item._fields[:-1])
    if isinstance(item, FieldRef):
        return find_keys(item._root, root_only)
    if isinstance(item, Expression):
        root = item._root if item._root is not None else item._op
        is_func = isinstance(root, Relationship) and any(field.is_input for field in root._fields)
        if root_only and item._root is not None and not(is_func):
            # We ignore "function-like relationships" (those with inputs) since they are never a root
            if isinstance(item._root, Relationship):
                return [item]
            return find_keys(item._root, root_only=True)
        args = item._args[:-1] if isinstance(item._op, Property) else item._args
        if is_func:
            assert isinstance(root, Relationship)
            args = [item._args[ix] for ix, field in enumerate(root._fields) if field.is_input]
        keys = []
        for arg in args:
            keys.extend(find_keys(arg, root_only))
        return keys
    if isinstance(item, Fragment):
        keys = []
        for subitem in item._select:
            keys.extend(find_keys(subitem, root_only))
        return keys
    if isinstance(item, DerivedColumn):
        return find_keys(item._table, root_only)
    if isinstance(item, Union):
        # Unions should always act as sets and so have no keys
        return []
    if isinstance(item, Match):
        keys = []
        if root_only:
            keys.extend(find_keys(item._items[0], root_only))
        else:
            for subitem in item._items:
                keys.extend(find_keys(subitem, root_only))
        return keys
    if isinstance(item, TupleVariable):
        keys = []
        for subitem in item._items:
            keys.extend(find_keys(subitem, root_only))
        return keys
    return []

def mm_value_type(value: mValue) -> TypeNode:
    if isinstance(value, (Var, mLiteral)):
        return value.type
    elif isinstance(value, TypeNode):
        return value
    elif isinstance(value, Relation):
        return RelationType
    elif isinstance(value, Field):
        return FieldType
    elif isinstance(value, Iterable):
        return TupleType(element_types=tuple(mm_value_type(v) for v in value))
    elif value is None:
        return NoneType
    else:
        raise NotImplementedError(f"mm_value_type not implemented for value type: {type(value)}")

@lru_cache(maxsize=1)
def _get_core():
    from . import core
    return core

@lru_cache(maxsize=1)
def _get_constraints():
    from ..std import constraints
    return constraints

def is_core_concept(concept):
    core = _get_core()
    if concept._model is core.Core:
        return True
    return any(is_core_concept(a) for a in concept._extends)

def concept_var_name(concept: Concept|Relationship) -> str:
    if isinstance(concept, Relationship):
        return sanitize(concept._short_name).lower()
    core = _get_core()
    if isinstance(concept, core.NumberConcept) or concept is core.Numeric:
        return "number"
    return sanitize(concept._name).lower()


#------------------------------------------------------
# Reference scheme handling
#------------------------------------------------------

def report_missing(concept:Concept, missing:OrderedSet[str], required:OrderedSet[str], source, ctx:Context):
    if missing:
        missing_str = ", ".join([f"`{name}`" for name in missing])
        required_str = ", ".join([f"[bold red]{name}[/bold red]" if name in missing else name for name in required])
        message = "values for properties" if len(missing) > 1 else "a value for property"
        ctx.err("Missing identity", f"Missing {message} {missing_str} in concept `{concept._name}`.", [
            err_source(source),
            f"{concept._name} requires {required_str}"
        ])
        return True
    return False

def make_construct(compiler:FrontCompiler,ctx:Context, concept:Concept, kwargs:dict[str, Any], ident_args:list[str], target:Var, source:Any=None):
    construct_args:list[mValue] = [
        ctx.to_value(concept._name),
        *[compiler.lookup(ctx, kwargs[ident]) for ident in ident_args]
    ]
    return Construct(tuple(construct_args), target, source=source)

def handle_concept_expression(compiler:FrontCompiler, ctx:Context, expr:Expression) -> Var:
    assert isinstance(expr._op, Concept)
    source = expr._source
    passed_concept = expr._op
    kwargs = {k.lower(): v for k, v in expr._kwargs.items()}

    root_concept = None
    hierarchy:list[Concept] = []
    constructs = KeyedDict[Concept, list[str]](dsl_key)
    required = OrderedSet[str]()
    missing = OrderedSet[str]()

    def walk_extends(c:Concept):
        nonlocal root_concept
        if c in hierarchy:
            return
        for ext in c._extends:
            walk_extends(ext)
        hierarchy.append(c)
        if c._identify_by and root_concept is None:
            root_concept = c
        ident_args = []
        for ident_rel in c._identify_by:
            ident = ident_rel._short_name.lower()
            required.add(ident)
            if ident in kwargs:
                ident_args.append(ident)
            else:
                missing.add(ident)
        constructs[c] = ident_args

    walk_extends(passed_concept)

    if root_concept is None:
        root_concept = hierarchy[0]
        if isinstance(expr, New) and expr._row_ids:
            names = [f"_row_id_{t._name}" for t in expr._row_ids]
            kwargs.update({name: expr._row_ids[ix] for ix, name in enumerate(names)})
            constructs[root_concept] = list(sorted(names))
        else:
            constructs[root_concept] = list(sorted(kwargs.keys()))

    root_id = ctx.to_value(expr)
    assert isinstance(root_id, Var)
    root_args = constructs[root_concept]

    if isinstance(expr, New) and ctx.in_update:
        # New requires that none of the identity args are missing
        if report_missing(passed_concept, missing, required, source, ctx):
            return root_id

        # construct the root identity
        ctx.add(make_construct(compiler, ctx, root_concept, kwargs, root_args, root_id, source=source))
        if expr not in ctx.construct_handled:
            ctx.add_update(passed_concept, [root_id], source=source)

            # Update identity and non-identity attributes
            for k, v in kwargs.items():
                rel = passed_concept._dot(k)
                ctx.add_update(rel, [root_id, compiler.lookup(ctx, v)], source=source)

            ctx.construct_handled.add(expr)

    elif isinstance(expr, New):
        # New requires that none of the identity args are missing
        if report_missing(passed_concept, missing, required, source, ctx):
            return root_id

        # just construct the root identity and then look it up in the subtype
        # population
        ctx.add(make_construct(compiler, ctx, root_concept, kwargs, root_args, root_id, source=source))
        ctx.add_lookup(passed_concept, [root_id], source=source)

        # Any non-identity attributes are filters
        for k, v in kwargs.items():
            if k not in root_args:
                rel = passed_concept._dot(k)
                ctx.add_lookup(rel, [root_id, compiler.lookup(ctx, v)], source=source)

    elif isinstance(expr, FilterBy):
        # check if _any_ concept has all the identity args it needs as a
        if len(root_args) == len(root_concept._identify_by):
            ctx.add(make_construct(compiler, ctx, root_concept, kwargs, root_args, root_id, source=source))
        else:
            # if we don't have all the identity args for the root, we need to look up any partials
            root_args = []

        ctx.add_lookup(passed_concept, [root_id], source=source)
        for k, v in kwargs.items():
            if k not in root_args:
                rel = passed_concept._dot(k)
                ctx.add_lookup(rel, [root_id, compiler.lookup(ctx, v)], source=source)
    else:
        exc("Invalid concept expression", f"Expected a `New` or `FilterBy` expression, got `{type(expr).__name__}`.", [err_source(source)])

    return root_id

#------------------------------------------------------
# Match union branch keys
#------------------------------------------------------

def get_branch_keys(compiler:FrontCompiler, ctx:Context, branch:Match|Union) -> list[tuple[Value, Var]]:
    keys = KeyedSet(dsl_key)
    for item in branch._items:
        if not isinstance(item, Fragment):
            keys.update(find_keys(item))
    branch_keys = []
    seen_keys = set()
    for key in keys:
        k_var = ctx.to_value(key)
        if k_var not in seen_keys and isinstance(k_var, Var) and not ctx.is_var_available(k_var, ignore_current=True):
            seen_keys.add(k_var)
            branch_keys.append((key, k_var))
    return branch_keys

def normalize_branch_keys(compiler:FrontCompiler, ctx:Context, branch_keys:list[tuple[Value, Var]], branch:Statement):
    for key, var in branch_keys:
        if var not in ctx.frame_vars:
            source = branch._source if isinstance(branch, DSLBase) else var.source
            if not isinstance(key, (Concept, Ref)):
                return ctx.err("Invalid branch", "Branch key must be a concept or reference.", [err_source(source)])
            concept = key._to_concept()
            if is_core_concept(concept):
                return ctx.err("Invalid branch", "Branch key must be an entity, not a primitive.", [err_source(source)])
            else:
                ctx.add(Construct((ctx.to_value(concept._name + "_NONE_SENTINEL"),), var, source=key._source))


#------------------------------------------------------
# Context
#------------------------------------------------------

class Frame:
    def __init__(self):
        self.nodes:OrderedSet[Task] = OrderedSet()
        self.in_update = False
        self.used_vars:OrderedSet[Var] = OrderedSet()
        self.seen:dict[Value, mValue] = {}

class Context:
    def __init__(self, compiler:FrontCompiler):
        self.compiler = compiler
        self.stack:list[Frame] = [Frame()]
        self.value_map:KeyedDict[Value|tuple[Value, Value], mValue] = KeyedDict(dsl_key)
        self.has_error = False
        self._in_update = False
        self.construct_handled:KeyedSet[New] = KeyedSet(dsl_key)

    #------------------------------------------------------
    # subcontext
    #------------------------------------------------------

    @contextmanager
    def subcontext(self):
        self.stack.append(Frame())
        try:
            yield
        finally:
            prev = self.stack.pop()
            self.stack[-1].used_vars.update(prev.used_vars)

    #------------------------------------------------------
    # in_update
    #------------------------------------------------------

    @contextmanager
    def updating(self):
        prev = self.in_update
        self._in_update = True
        try:
            yield
        finally:
            self._in_update = prev
            if not self._in_update:
                self.construct_handled.clear()

    @property
    def in_update(self) -> bool:
        return self._in_update

    #------------------------------------------------------
    # Errors/warnings
    #------------------------------------------------------

    def err(self, name: str, message: str, parts: Optional[list[Part]] = None) -> Diagnostic:
        self.has_error = True
        return err(name, message, parts)

    def warn(self, name: str, message: str, parts: Optional[list[Part]] = None) -> Diagnostic:
        self.has_error = True
        return warn(name, message, parts)

    #------------------------------------------------------
    # Task capture
    #------------------------------------------------------

    def _check_frames(self, node:Task):
        for frame in reversed(self.stack[:-1]):
            if node in frame.nodes:
                return True
        return False

    def add(self, node:Task):
        if self._check_frames(node):
            return
        self.stack[-1].nodes.add(node)

    def extend(self, nodes:Sequence[Task]):
        for node in nodes:
            self.add(node)

    def add_lookup(self, relationship:Relationship|Concept, args:Sequence[mValue], source:Any=None):
        op = self.compiler.to_relation(relationship)
        hint = None
        if isinstance(relationship, Reading):
            hint = self.compiler.find_reading(relationship)
            # reorder the args to match the correct ordering
            new_args:list[Any] = [None] * len(hint.field_order)
            for cur, new in enumerate(hint.field_order):
                new_args[new] = args[cur]
            args = new_args
        self.add(Lookup(op, tuple(args), reading_hint=hint, source=source))

    def add_update(self, relationship:Relationship|Concept, args:Sequence[mValue], effect=Effect.derive, source:Any=None):
        op = self.compiler.to_relation(relationship)
        hint = None
        if isinstance(relationship, Reading):
            hint = self.compiler.reading_map[relationship]
            # reorder the args to match the correct ordering
            new_args:list[Any] = [None] * len(hint.field_order)
            for cur, new in enumerate(hint.field_order):
                new_args[new] = args[cur]
            args = new_args
        self.add(Update(op, tuple(args), effect=effect, reading_hint=hint, source=source))

    def add_eq(self, left:mValue, right:mValue, source:Any=None):
        self.add(Lookup(getattr(bt.core, "="), (left, right), source=source))

    @property
    def nodes(self):
        return self.stack[-1].nodes

    #------------------------------------------------------
    # Value mapping
    #------------------------------------------------------

    def to_value(self, value:Value, source:Optional[Value]=None) -> mValue:
        key = (source, value) if source is not None else value
        if res := self.value_map.get(key):
            if isinstance(res, Var):
                self.stack[-1].used_vars.add(res)
            return res

        node = None
        if isinstance(value, Concept):
            value_type = self.compiler.to_type(value)
            node = Var(value_type, concept_var_name(value), source=value._source)
        elif isinstance(value, Chain):
            node = self.to_value(value._next._fields[-1], value)
        elif isinstance(value, Ref):
            value_type = self.compiler.to_type(value._concept)
            name = sanitize(value._name).lower() if value._name else f"{concept_var_name(value._concept)}{value._id}"
            node = Var(value_type, name, source=value._source)
        elif isinstance(value, Field):
            value_type = self.compiler.to_type(value.type)
            node = Var(value_type, sanitize(value.name).lower())
        elif isinstance(value, New):
            value_type = self.compiler.to_type(value._op)
            node = Var(value_type, f"{concept_var_name(value._op)}", source=value._source)
        elif isinstance(value, FieldRef):
            node = self.to_value(value._resolved, source=value._root)
        elif isinstance(value, Expression):
            node = self.to_value(value._args[-1])
        elif isinstance(value, Aggregate):
            node = self.to_value(value._args[-1])
        elif isinstance(value, DerivedColumn):
            value_type = self.compiler.to_type(value._type) if value._type is not None else bt.core.Any
            node = Var(value_type, f"v", source=value._source)
        elif isinstance(value, Literal):
            value_type = self.compiler.to_type(value._type)
            node = mLiteral(type=value_type, value=value._value, source=value._source)
        elif isinstance(value, AsBool):
            node = Var(bt.core.Boolean, f"v", source=value._source)
        elif isinstance(value, MetaRef):
            if isinstance(value._target, Concept):
                node = self.compiler.to_type(value._target)
            elif isinstance(value._target, Relationship):
                node = self.compiler.to_relation(value._target)
            elif isinstance(value._target, Field):
                node = self.compiler.to_field(value._target)
            else:
                node = self.to_value(value._target)
        elif is_primitive(value):
            type_ = self.compiler.to_type(Literal._get_type(value))
            node = mLiteral(type=type_, value=value)
        else:
            raise NotImplementedError(f"to_value not implemented for value type: {type(value)}")

        if isinstance(node, Var):
            self.stack[-1].used_vars.add(node)
        self.value_map[key] = node
        return node

    @property
    def frame_vars(self) -> OrderedSet[Var]:
        return self.stack[-1].used_vars

    def is_var_available(self, var:Var, ignore_current=False) -> bool:
        stack = self.stack[:-1] if ignore_current else self.stack
        for frame in reversed(stack):
            if var in frame.used_vars:
                return True
        return False

    @property
    def seen(self) -> dict[Value, mValue]:
        return self.stack[-1].seen

#------------------------------------------------------
# Compiler
#------------------------------------------------------

class FrontCompiler:
    def __init__(self, model: Model):
        self.model = model
        self.relations:KeyedDict[DSLBase, Relation] = KeyedDict(dsl_key)
        self.fields:KeyedDict[Field, mField] = KeyedDict(dsl_key)
        self.reading_map: KeyedDict[Reading, mReading] = KeyedDict(dsl_key)
        self.imported_libraries: set[Model] = set()
        self.relation_constraints: OrderedSet[Lookup] = OrderedSet()
        self.global_namer = Namer()

    #------------------------------------------------------
    # Library handling
    #------------------------------------------------------

    def check_import(self, node: Any):
        if not isinstance(node, DSLBase):
            return
        if isinstance(node, Aggregate):
            self.check_import(node._op)
        model = node._model
        if model and model != self.model and model not in self.imported_libraries:
            if model not in self.model.libraries:
                self.model.libraries.append(model)
            self.imported_libraries.add(model)
            self.relations.update(model._compiler.relations)
            self.relation_constraints.update(model._compiler.relation_constraints)
            return True

    #------------------------------------------------------
    # Model elements
    #------------------------------------------------------

    def find_reading(self, reading:Reading) -> mReading:
        if found := self.reading_map.get(reading):
            return found
        # It's possible that readings were added after the first time we encounter
        # the relationship, so we need to re-create them here and update the relationship
        root = reading._relationship
        rel = self.to_relation(root)
        readings = self.to_readings(root, start=len(rel.readings))
        rel._dangerous_set_readings(rel.readings + readings)
        return self.reading_map[reading]

    def to_readings(self, relationship: Relationship, start=0) -> tuple[mReading, ...]:
        readings = tuple(mReading(name=reading._short_name, parts=tuple(reading._parts), source=reading._source) for reading in relationship._readings[start:])
        self.reading_map.update((reading, mreading) for reading, mreading in zip(relationship._readings[start:], readings))
        return readings

    def to_annotation(self, node: Expression | Relationship) -> Annotation:
        if isinstance(node, Expression):
            args = []
            for arg in node._args:
                if isinstance(arg, Literal):
                    args.append(mLiteral(type=self.to_type(arg._type), value=arg._value, source=arg._source))
                elif isinstance(arg, Concept) or isinstance(arg, Relationship):
                    args.append(self.to_relation(arg))
                elif isinstance(arg, Chain):
                    args.append(self.to_relation(arg._next))
                else:
                    exc("Invalid annotation", f"Invalid annotation argument type: {type(arg).__name__}", [
                        err_source(arg._source),
                        "Only Concepts, Relationships, and Literals are allowed as annotation arguments."
                    ])
            return Annotation(relation=self.to_relation(node._op), args=tuple(args), source=node._source)
        elif isinstance(node, Relationship):
            return Annotation(relation=self.to_relation(node), args=(), source=node._source)
        else:
            raise ValueError(f"Unknown annotation type: {type(node)} - {node}")

    def to_field(self, node: Field) -> mField:
        if res := self.fields.get(node):
            return res
        field_type = self.to_type(node.type)
        if node.is_list:
            field_type = ListType(element_type=field_type)
        field = mField(name=node.name, type=field_type, input=node.is_input, source=node._source)
        self.fields[node] = field
        return field

    def to_relation(self, node: Any) -> Relation:
        if res := self.relations.get(node):
            return res
        elif self.check_import(node) and (res := self.relations.get(node)):
            return res

        rel = None
        if isinstance(node, Reading):
            rel = self.to_relation(node._relationship)
        elif isinstance(node, Relationship):
            annos = tuple(self.to_annotation(anno) for anno in node._annotations)
            readings = self.to_readings(node)
            fields = [self.to_field(field) for field in node._fields]
            if node._short_name == '':
                name = self.global_namer.get_name(sub(r"[{}: ]", "_", str(node._readings[0]._reading)).strip("_"))
            else:
                name = node._short_name
            overloads = []
            if node._overloads:
                for overload in node._overloads:
                    overload_types = tuple(self.to_type(concept) for concept in overload)
                    overloads.append(Overload(overload_types))
            if node._is_unresolved:
                rel = UnresolvedRelation(name=name, fields=tuple(fields), source=node._source, readings=readings, annotations=annos, overloads=tuple(overloads))
            else:
                rel = Relation(name=name, fields=tuple(fields), source=node._source, readings=readings, annotations=annos, overloads=tuple(overloads))
            if isinstance(node, Property):
                # Add a uniqueness constraint for properties
                _get_constraints()
                self.relation_constraints.add(Lookup(bt.constraints.unique_fields, (tuple(fields[:-1]),)))
        elif isinstance(node, Data):
            rel = mData(name=f"Data{node._id}", data=node._data, source=node._source)
            self.relations[node] = rel
            rel._force_columns(tuple(self.to_relation(col) for col in node._columns))
        elif isinstance(node, Table):
            rel = mTable(name=node._name, source=node._source)
            self.relations[node] = rel
            rel._force_columns(tuple(self.to_relation(col) for col in node._columns))
        elif isinstance(node, NumberConcept):
            super_types=tuple(self.to_type(ancestor) for ancestor in node._extends)
            rel = NumberType(name=node._name, precision=node._precision, scale=node._scale, source=node._source, super_types=super_types)
        elif isinstance(node, Concept):
            annos = tuple(self.to_annotation(anno) for anno in node._annotations)
            super_types=tuple(self.to_type(ancestor) for ancestor in node._extends)
            rel = ScalarType(name=node._name, annotations=annos, source=node._source, super_types=super_types)
            self.relations[node] = rel
            identify_by_rels = tuple(self.to_relation(rel) for rel in node._identify_by)
            rel._force_identify_by(identify_by_rels)
        else:
            raise ValueError(f"Unknown node type: {type(node)} - {node}")
        self.relations[node] = rel
        return rel

    def to_type(self, node: Any) -> ScalarType:
        rel = self.to_relation(node)
        if not isinstance(rel, ScalarType):
            raise ValueError(f"Node is not a ScalarType: {node}")
        return rel

    #------------------------------------------------------
    # Compile
    #------------------------------------------------------

    def compile(self, fragment: Fragment) -> Task|list[Task]:
        ctx = Context(self)
        # pprint(fragment)
        return self.fragment(ctx, fragment)

    def compile_model(self, model: Model) -> mModel:
        def as_seq(x):
            return x if isinstance(x, (list, tuple)) else (x,)

        # init enums
        for enum in model.enums:
            enum._init_members()

        self.check_invariants(model)

        for concept in model.concepts:
            self.to_relation(concept)
        for relationship in model.relationships:
            self.to_relation(relationship)
        for table in model.tables:
            self.to_relation(table)

        # compile + flatten defines/requires in one pass
        compiled:list[Task] = []
        compiled.extend(chain.from_iterable(
            as_seq(self.compile(item)) for item in chain(model.defines, model.requires)
        ))
        # partition relation values into types vs non-types
        rel_vals = list(self.relations.values())
        types = tuple(r for r in rel_vals if isinstance(r, TypeNode))
        relations = tuple(r for r in rel_vals if not isinstance(r, TypeNode))

        compiled.insert(0, Require(check=Logical(tuple(self.relation_constraints), source=model._source)))

        source = model._source
        root = Logical(tuple(compiled), source=source)

        return mModel(
            reasoners=(),
            relations=relations,
            types=types,
            root=root,
            source=source,
        )

    #------------------------------------------------------
    # Invariants
    #------------------------------------------------------

    def check_invariants(self, model: Model):
        # Ensure that all concepts with identify_by have at least one relationship
        has_errors = False
        for concept in model.concepts:
            for k, v in concept._relationships.items():
                for ext in concept._extends:
                    if k in ext._relationships:
                        kind = "Property" if isinstance(v, Property) else "Relationship"
                        parent_kind = "property" if isinstance(ext._relationships[k], Property) else "relationship"
                        err(f"{kind} conflict",
                            f"{kind} `{k}` in concept `{concept._name}` conflicts with {parent_kind} in parent concept `{ext._name}`.",
                            [
                                f"Parent {parent_kind}",
                                err_source(ext._relationships[k]),
                                f"Child {kind.lower()}",
                                err_source(v)
                            ])
                        has_errors = True

        if has_errors:
            exc("Invalid model", "Model has invariant violations, see errors for details.")

    #------------------------------------------------------
    # Fragment
    #------------------------------------------------------

    def fragment(self, ctx: Context, fragment: Fragment):
        if fragment._require:
            return self.require(ctx, fragment, scope=True)
        else:
            annos = tuple(self.to_annotation(anno) for anno in fragment._annotations)
            self.where(ctx, fragment, fragment._where)
            self.select(ctx, fragment, fragment._select)
            self.define(ctx, fragment, fragment._define)
            return Logical(tuple(ctx.nodes), scope=True, annotations=annos, source=fragment._source)

    #------------------------------------------------------
    # Where
    #------------------------------------------------------

    def where(self, ctx: Context, fragment:Fragment, exprs: list[Value]):
        for expr in exprs:
            self.lookup(ctx, expr)

    #------------------------------------------------------
    # Select
    #------------------------------------------------------

    def select(self, ctx: Context, fragment:Fragment, exprs: Sequence[Value]):
        if not exprs:
            return

        source = fragment._source
        output_name = f"output{fragment._id}"

        uri = f"dataframe://{output_name}" if fragment._into is None else f"table://{fragment._into._name}"
        table = mTable(name=f"Output{fragment._id}", uri=uri, source=source)
        table_var = Var(type=table, name=output_name, source=source)

        keys:KeyedSet[Value] = KeyedSet(dsl_key)
        items:list[Task] = []

        # Unwrap distinct if present
        is_distinct = any(isinstance(expr, Distinct) for expr in exprs)
        if is_distinct:
            if len(exprs) != 1 or not isinstance(exprs[0], Distinct):
                return ctx.err("Invalid distinct", "Distinct must be applied to the entire select.", [
                    err_source(source)
                ])
            exprs = exprs[0]._items

        # Build out the table columns
        # v0, v1, etc, for generic elements like literals or the unnamed result of union/matches
        range_namer = Namer(range=True)
        # v, v_2, v_3, etc, for elements where we want to preserve the original name if there
        # are no collisions, like chain expressions, aggregates, etc
        namer = Namer()

        # we have to first find all the roots, the roots need to be looked up in the outer scope
        # we then need to find the keys for each expr, any keys that aren't roots need to be added
        # to the column relation
        roots = KeyedSet(dsl_key)
        for expr in exprs:
            if is_distinct:
                roots.add(expr)
            else:
                roots.update(find_keys(expr, root_only=True))

        # look the roots up in the outer scope
        root_vars:OrderedSet[mValue] = OrderedSet()
        for root in roots:
            root_v = self.lookup(ctx, root)
            # For top-level relationships, the fields of the relationship are
            # the root vars, since all of them behave like keys. For Properties,
            # we ignore the last field since it's functionally determined by the others.
            # Expressions use their args
            if isinstance(root, Property):
                root_vars.update(ctx.to_value(field) for field in root._fields[:-1])
            elif isinstance(root, Relationship):
                root_vars.update(ctx.to_value(field) for field in root._fields)
            elif isinstance(root, Expression):
                root_vars.update(ctx.to_value(arg) for arg in root._args)
            else:
                root_vars.add(root_v)

        # handle order_by/limit
        if fragment._order_by or fragment._limit != 0:
            from ..std.aggregates import _sort_agg
            args = fragment._order_by if fragment._order_by else fragment._select
            sort_agg = _sort_agg(fragment._limit, *args)
            self.lookup(ctx, sort_agg)

        # build columns
        table_cols = []
        for expr in exprs:
            expr_keys = [expr] if is_distinct else find_keys(expr)

            with ctx.subcontext():
                col = self.lookup(ctx, expr)
                # Columns may need their own keys beyond the roots to guarantee that multiple values end up
                # available for the same root. E.g. people having multiple pets
                maybe_col_keys = [ctx.to_value(col_key) for col_key in expr_keys]
                col_keys = [col_key for col_key in maybe_col_keys
                            if isinstance(col_key, Var) and col_key != col and col_key not in root_vars]
                col_key_fields = [mField(name=key.name, type=key.type) for key in col_keys]

                # build the relation
                col_name = (expr._alias if isinstance(expr, Alias) else
                            range_namer.get_name(col.name) if isinstance(col, Var) and isinstance(expr, (Union, Match)) else
                            namer.get_name(self.to_relation(expr._op).name) if isinstance(expr, Aggregate) else
                            namer.get_name(col.name) if isinstance(col, Var) else
                            range_namer.get_name("v"))
                col_type = mm_value_type(col)
                col_relation = Relation(col_name, (
                    mField(name="table", type=table),
                    *col_key_fields,
                    mField(name=col_name, type=col_type)
                ), source=source)
                table_cols.append(col_relation)

                # The shim needs a hint that this output is both a key and a value
                annos = ()
                if col in maybe_col_keys and col not in root_vars:
                    annos = (Annotation(relation=bt.core["output_value_is_key"], args=(), source=source),)
                ctx.add(Update(col_relation, args=tuple([table_var, *col_keys, col]), annotations=annos, source=source))

                optional = True
                # rank and limit should always just get pushed to the root - they can never be null
                if isinstance(expr, Aggregate):
                    op = self.to_relation(expr._op)
                    optional = not (op is bt.aggregates.rank or op is bt.aggregates.limit)

                node_tuple = tuple(ctx.nodes)
                if len(ctx.nodes) == 1:
                    items.append(node_tuple[0])
                else:
                    items.append(Logical(node_tuple, source=source, optional=optional))

        # add the columns to the output table
        table._force_columns(tuple(table_cols))

        # Construct followed by adding the row to the table and then each column
        ctx.add(Construct(tuple(root_vars), table_var, source=source))
        ctx.add(Update(table, tuple([table_var]), source=source))
        ctx.extend(items)

    #------------------------------------------------------
    # Define
    #------------------------------------------------------

    def define(self, ctx: Context, fragment:Fragment, exprs: list[Value]):
        with ctx.updating():
            for expr in exprs:
                source = expr._source if isinstance(expr, DSLBase) else fragment._source
                with ctx.subcontext():
                    self.update(ctx, expr, root_source=fragment._source)
                    nodes = tuple(ctx.nodes)
                ctx.add(Logical(nodes, source=source, optional=True))

    #------------------------------------------------------
    # Require
    #------------------------------------------------------

    def require(self, ctx: Context, fragment:Fragment, scope:bool=False):
        source = fragment._source
        reqs = []
        annos = tuple(self.to_annotation(anno) for anno in fragment._annotations)
        with ctx.subcontext():
            self.where(ctx, fragment, fragment._where)
            domain_body = tuple(ctx.nodes)
            domain_vars = ctx.frame_vars
            for expr in fragment._require:
                with ctx.subcontext():
                    self.lookup(ctx, expr)
                    check = Logical(tuple(ctx.nodes), source=source)
                    hoisted = tuple(v for v in ctx.frame_vars if v in domain_vars)
                    reqs.append(Require(Logical(domain_body, source=source), check, scope=scope, annotations=annos, source=source))
        if len(reqs) == 1:
            return reqs[0]
        return reqs

    #------------------------------------------------------
    # Lookup
    #------------------------------------------------------

    # @memoize_in_ctx
    def lookup(self, ctx: Context, node: Any) -> mValue:
        source = node._source if not is_primitive(node) else None
        self.check_import(node)

        #------------------------------------------------------
        # Concept / Concept expressions (includes Data and Table)
        #------------------------------------------------------

        if isinstance(node, Concept):
            final_var = ctx.to_value(node)
            if not is_core_concept(node):
                ctx.add_lookup(node, [final_var], source=source)
            return final_var

        elif isinstance(node, Ref):
            final_var = ctx.to_value(node)
            if not is_core_concept(node._concept):
                ctx.add_lookup(node._concept, [final_var], source=source)
            return final_var

        elif isinstance(node, New):
            # If we encounter a New nested inside of an update, we want to treat this
            # new as an update as well so that you can write Person.new(.., pet=Pet.new(..))
            if ctx.in_update and not node._identity_only:
                return self.update(ctx, node, root_source=node._source)

            # Otherwise we're just checking this exists
            return handle_concept_expression(self, ctx, node)

        elif isinstance(node, FilterBy):
            return handle_concept_expression(self, ctx, node)

        #------------------------------------------------------
        # Relationship
        #------------------------------------------------------

        elif isinstance(node, Relationship):
            # we need vars for each field, but how do we store them?
            args = [ctx.to_value(field) for field in node._fields]
            ctx.add_lookup(node, args, source=source)
            return args[-1]

        elif isinstance(node, FieldRef):
            self.lookup(ctx, node._root)
            # If the source of the field ref is an expression, this is an ArgumentRef, so
            # return the expression var directly
            if isinstance(node._root, Expression):
                return self.lookup(ctx, node._root._args[node._resolved_ix])
            # If this is a reference to the relationship itself, then we want that to
            # unify with any other references to the given field. If it's through a chain
            # or expression, then it should be sourced from there.
            field_source = node._root if not isinstance(node._root, Relationship) else None
            return ctx.to_value(node._resolved, source=field_source)

        #------------------------------------------------------
        # Expressions
        #------------------------------------------------------

        elif isinstance(node, Expression):
            # For auto-filled expressions, there's no reason to lookup the last ref and
            # do a population check
            if node._auto_filled:
                args = [self.lookup(ctx, arg) for arg in node._args[:-1]] + [ctx.to_value(node._args[-1])]
                ctx.add_lookup(node._op, args, source=source)
                return args[-1]
            # if we are casting e.g. with something like `Discount(0.6)` we should return a literal with that
            # type
            elif isinstance(node._op, Concept) and is_core_concept(node._op):
                if isinstance(node._args[0], Literal):
                    return mLiteral(type=self.to_type(node._op), value=node._args[0]._value, source=source)
                else:
                    cur = self.lookup(ctx, node._args[-1])
                    ret = ctx.to_value(node._op, source=node)
                    ctx.add_lookup(CoreRelationships["cast"], [self.to_type(node._op), cur, ret], source=source)
                    return ret
            # Normal expression
            else:
                args = [self.lookup(ctx, a) for a in node._args]
                ctx.add_lookup(node._op, args, source=source)
                return args[-1]

        elif isinstance(node, Chain):
            start = self.lookup(ctx, node._start)
            final_var = ctx.to_value(node)
            # Unaries are special, the chain's var is just the start var
            if len(node._next._fields) == 1:
                ctx.add_lookup(node._next, [start], source=source)
                return start
            else:
                # If the relation has more than 2 fields, we need to create vars for the
                # unreferrenced ones in the middle
                middle_args = [ctx.to_value(field, source=node) for field in node._next._fields[1:-1]]
                args = [start, *middle_args, final_var]
                ctx.add_lookup(node._next, args, source=source)
            return final_var

        #------------------------------------------------------
        # Aggregates
        #------------------------------------------------------

        elif isinstance(node, Aggregate):
            agg = self.to_relation(node._op)
            input_args = [arg for ix, arg in enumerate(node._args) if agg.fields[ix].input]

            proj_set:KeyedSet[Value] = KeyedSet(dsl_key)
            if not node._distinct:
                for item in [*node._projection_args, *input_args]:
                    proj_set.update(find_keys(item))
            proj_set.update(node._projection_args)
            proj = cast(OrderedSet[Var], OrderedSet([ctx.to_value(p) for p in proj_set]))
            group = cast(list[Var], [self.lookup(ctx, arg) for arg in node._group._args])

            if agg is bt.aggregates.rank:
                assert isinstance(node._args[0], TupleVariable)
                for arg in node._args[0]._items:
                    self.lookup(ctx, arg)
            elif agg is bt.aggregates.limit:
                assert isinstance(node._args[1], TupleVariable)
                for arg in node._args[1]._items:
                    self.lookup(ctx, arg)

            with ctx.subcontext():
                for item in node._where._where:
                    self.lookup(ctx, item)
                for projected in proj_set:
                    self.lookup(ctx, projected)
                args = cast(list[Var], [self.lookup(ctx, arg) for arg in node._args])
                where = Logical(tuple(ctx.nodes), source=source)

            ctx.add(mAggregate(agg, tuple(proj), tuple(group), tuple(args), where, source=source))
            return args[-1] if not isinstance(args[-1], tuple) else None

        elif isinstance(node, Group):
            for arg in node._args:
                self.lookup(ctx, arg)
            return

        #------------------------------------------------------
        # Quantifiers
        #------------------------------------------------------

        elif isinstance(node, Not):
            with ctx.subcontext():
                for item in node._items:
                    self.lookup(ctx, item)
                not_ = mNot(Logical(tuple(ctx.nodes)), source=source)
            ctx.add(not_)
            return

        #------------------------------------------------------
        # Nested fragment
        #------------------------------------------------------

        elif isinstance(node, Fragment):
            if node._require or node._define:
                ctx.err("Invalid subquery", "Nested queries with `require` or `define` are not supported.", [
                    err_source(source)
                ])
            if node._select:
                with ctx.subcontext():
                    for where in node._where:
                        self.lookup(ctx, where)
                    # cols = cast(ISeq[Var], tuple(ctx.to_value(col) for col in node._columns))
                    vals = [self.lookup(ctx, sel) for sel in node._select]
                    ctx.value_map.update(zip(node._columns, vals))
                    # for col, val in zip(cols, vals):
                    #     ctx.add_eq(col, val, source=source)
                    nodes = tuple(ctx.nodes)
                ctx.add(Logical(nodes, source=source))
                return vals[-1]
            else:
                for where in node._where:
                    self.lookup(ctx, where)
                return None

        #------------------------------------------------------
        # Match / Union
        #------------------------------------------------------

        elif isinstance(node, (Match, Union)):
            branches = []
            outputs = cast(ISeq[Var], tuple(ctx.to_value(col) for col in node._columns) if node._arg_count() > 0 else tuple())
            branch_keys = get_branch_keys(self, ctx, node)
            for item in node._items:
                item_source = item._source if isinstance(item, Variable) else source
                if isinstance(item, Fragment):
                    if item._select:
                        # map the select columns to the match/union outputs
                        for ix, col in enumerate(item._columns):
                            ctx.value_map[col] = outputs[ix]
                        with ctx.subcontext():
                            self.lookup(ctx, item)
                            # unwrap the nested logical
                            wrapper = ctx.nodes[0]
                            assert isinstance(wrapper, Logical)
                            for subnode in wrapper.body:
                                ctx.add(subnode)

                            normalize_branch_keys(self, ctx, branch_keys, item)
                            # add the output column equalities
                            for ix, col in enumerate(item._columns):
                                ctx.add_eq(outputs[ix], ctx.to_value(col), source=item_source)
                            branches.append(Logical(tuple(ctx.nodes)[1:], source=item_source))
                    else:
                        with ctx.subcontext():
                            for where in item._where:
                                self.lookup(ctx, where)
                            branches.append(Logical(tuple(ctx.nodes), source=item_source))
                else:
                    with ctx.subcontext():
                        res = self.lookup(ctx, item)
                        normalize_branch_keys(self, ctx, branch_keys, item)
                        if outputs:
                            ctx.add_eq(outputs[0], res, source=item_source)
                        branches.append(Logical(tuple(ctx.nodes), source=item_source))

            if isinstance(node, Union):
                ctx.add(mUnion(tuple(branches), source=source))
            else:
                ctx.add(mMatch(tuple(branches), source=source))

            return outputs[-1] if outputs else None

        #------------------------------------------------------
        # Value-likes
        #------------------------------------------------------

        elif isinstance(node, (Field, MetaRef)):
            return ctx.to_value(node)

        elif isinstance(node, TupleVariable):
            # exc("TupleVariable unsupported", "TupleVariable is not supported yet.", [err_source(source)])
            items = [self.lookup(ctx, item) for item in node._items]
            return tuple(items)

        elif isinstance(node, TableSchema):
            exc("Invalid value", "A schema cannot be used as a value outside of a `.new(..)` or `.select(..)` call.", [err_source(source)])
            return None

        elif is_primitive(node):
            type_ = self.to_type(Literal._get_type(node))
            return mLiteral(type_, node)

        elif isinstance(node, DerivedColumn):
            self.lookup(ctx, node._table)
            return ctx.to_value(node)

        elif isinstance(node, Literal):
            return mLiteral(type=self.to_type(node._type), value=node._value, source=source)

        elif isinstance(node, ModelEnum):
            return self.lookup(ctx, node._compile_lookup())

        elif isinstance(node, Alias):
            return self.lookup(ctx, node._source)

        elif isinstance(node, AsBool):
            # we need to create a match with two branches that returns true/false
            out = ctx.to_value(node)
            assert isinstance(out, Var)
            with ctx.subcontext():
                self.lookup(ctx, node._item)
                ctx.add_eq(out, mLiteral(bt.core.Boolean, True), source=node._source)
                true_branch = Logical(tuple(ctx.nodes), source=source)
            with ctx.subcontext():
                ctx.add_eq(out, mLiteral(bt.core.Boolean, False), source=node._source)
                false_branch = Logical(tuple(ctx.nodes), source=source)
            ctx.add(mMatch((true_branch, false_branch), source=source))
            return out

        #------------------------------------------------------
        # Invalid nodes
        #------------------------------------------------------

        elif isinstance(node, Distinct):
            ctx.err("Invalid distinct", "Distinct can only be used in `select(distinct(..))` or aggregates like `count(distinct(..))`.", [
                err_source(source)
            ])
            return None

        else:
            raise NotImplementedError(f"Lookup not implemented for node type: {type(node)}")

    #------------------------------------------------------
    # Update
    #------------------------------------------------------

    def update(self, ctx: Context, node: Any, root_source:SourcePos) -> mValue:
        source = node._source if not is_primitive(node) else root_source
        self.check_import(node)

        #------------------------------------------------------
        # Concept / Concept expressions (includes Data and Table)
        #------------------------------------------------------

        if isinstance(node, Concept):
            final_var = ctx.to_value(node)
            ctx.add_update(node, [final_var], source=source)
            return final_var

        elif isinstance(node, New):
            if node._identity_only:
                ctx.err("Invalid define", "Cannot define just an identity.", [
                    err_source(source),
                    "Did you mean to use `.new(..)`?"
                ])
                return
            return handle_concept_expression(self, ctx, node)

        #------------------------------------------------------
        # Relationship
        #------------------------------------------------------

        elif isinstance(node, Relationship):
            ctx.err("Invalid define", "Cannot define a relationship without values for its fields.", [
                err_source(root_source),
            ])

        #------------------------------------------------------
        # Expressions
        #------------------------------------------------------

        elif isinstance(node, Expression):
            if node._auto_filled or len(node._args) == 0:
                field_name = node._op._fields[-1].name if isinstance(node._op, Relationship) else node._op._name.lower()
                ctx.err("Invalid define", f"Define requires that all args be provided, but the value for the `{field_name}` field is missing.", [
                    err_source(source),
                ])
                return
            args = [self.lookup(ctx, arg) for arg in node._args]
            if node._op is CoreRelationships["="]:
                if isinstance(node._args[0], (Relationship, Chain)):
                    return self.update(ctx, node._args[0](node._args[1]), root_source=source)
                elif isinstance(node._args[1], (Relationship, Chain)):
                    return self.update(ctx, node._args[1](node._args[0]), root_source=source)
                else:
                    ctx.err("Invalid define", "Cannot set a non-relationship via `=` in a define.", [
                        err_source(source),
                    ])
            else:
                if isinstance(node._op, Concept) and is_core_concept(node._op):
                    return self.lookup(ctx, node)
                ctx.add_update(node._op, args, source=source)
                return args[-1]

        elif isinstance(node, Chain):
            # all fields have to be specified for a define, so a chain only works
            # if the relationship is unary
            if len(node._next._fields) > 1:
                ctx.err("Invalid define", "All fields must have a value when defining a relationship.", [
                    err_source(source),
                    f"You need something like [cyan]`.{node._next._short_name}(" + ", ".join([field.name for field in node._next._fields[1:]]) + ")`"
                ])
                return

            start = self.lookup(ctx, node._start)
            ctx.add_update(node._next, [start], source=source)
            return start

        #------------------------------------------------------
        # Invalids
        #------------------------------------------------------

        elif is_primitive(node):
            ctx.err("Invalid define", "Cannot define a primitive value.", [
                err_source(source)
            ])
            return

        elif isinstance(node, (FilterBy, Ref, FieldRef, Aggregate, Group, Not, Fragment, Match, Field, DerivedColumn, Literal, Alias, Distinct)):
            ctx.err("Invalid define", f"Cannot define a value of type `{type(node).__name__}`.", [
                err_source(node._source)
            ])
            return

        else:
            raise NotImplementedError(f"Lookup not implemented for node type: {type(node)}")



#------------------------------------------------------
# TODO
#------------------------------------------------------
"""
- vars shared between columns need to end up as column keys
- check sub-selects now that we went back to optional logicals
- roots for union/matches/fragments
- ref scheme mappings
- what do we want to do about Error/require errors?
- None columns in selects

x Concept
x DerivedColumn
x Field
x Relationship
x Reading
x Property
x Literal
x Chain
x Expression
x FieldRef
x Alias
x Match / Union
x Not
x Distinct
x nested Fragments
x New
x Concept expression with kwargs
x select
x where
x Data
x Table
x Group
x Aggregate
x defining an expression allows you to have one fewer var than you should
x define
x require
x distinct for aggregates
x don't do pop checks on primitives
x handle library imports
x nested news
x bool handling (as_bool, select(x > y))
x generate constraints for Property?
x wrong arg count in an update isn't providing an error
"""
