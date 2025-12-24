from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
import dataclasses
import datetime
from decimal import Decimal as PyDecimal
from typing import Optional, Union, Tuple
from v0.relationalai import debugging
from v0.relationalai.semantics.metamodel import builtins, helpers, ir, types, visitor, compiler, factory as f
from v0.relationalai.semantics.metamodel.util import OrderedSet, ordered_set
import rich
import sys

#--------------------------------------------------
# Helpers
#--------------------------------------------------

def to_relation(node:ir.Lookup|ir.Update|ir.Aggregate) -> ir.Relation:
    """ Get the relation being referred to by this node. """
    if isinstance(node, ir.Aggregate):
        return node.aggregation
    return node.relation

def to_name(type:ir.Type) -> str:
    """ Get a human-readable name representing a type. """
    if isinstance(type, ir.DecimalType):
        return f"Decimal({type.precision},{type.scale})"
    elif isinstance(type, ir.ScalarType):
        return type.name
    elif isinstance(type, ir.UnionType):
        return '|'.join([to_name(t) for t in type.types])
    elif isinstance(type, ir.ListType):
        return f"[{to_name(type.element_type)}]"
    else:
        raise TypeError(f"Unknown type: {type}")

def check_int64(value: int):
    INT64_MIN = -(2 ** 63)
    INT64_MAX = 2 ** 63 - 1

    if not (INT64_MIN <= value <= INT64_MAX):
        raise OverflowError(f"Value '{value}' does not fit in Int64.")

#--------------------------------------------------
# Constants
#--------------------------------------------------

# map potential type conversions to their cost
# The differences in the costs of converting from one type to another should be
# smaller than the cost of a literal conversion.
# Otherwise, we'll introduce spurious conversions of say Int->Decimal64 plus a cheap literal conversion
# Float->Decimal64, rather than a single literal conversion Int->Float.
# Use a large enough number here so that if all arguments are literals, it's cheaper to convert
# the literals (cost 10) rather than not convert some literals and convert a non-literal instead.
# For instance, for `y=1+x` is should be cheaper to convert 1 to float and not convert x and y, than it would be
# convert both x and y to integer.
# We do however, want to prefer converting to number types lower in the lattice.
# So we make the cost depend only on the result type.
# Making all the costs the same would introduce spurious unions of conversions.

CONVERSION_LATTICE:dict[tuple[ir.Type, ir.Type], int] = {
    # Make the cost depend only on the result type.
    (types.Int64, types.Int128): 1000,
    (types.Int64, types.GenericDecimal): 1002,
    (types.Int64, types.Float): 1004,
    (types.Int128, types.GenericDecimal): 1002,
    (types.GenericDecimal, types.Float): 1003,
    (types.Int128, types.Float): 1004,
    # Int -> Hash (UInt128)
    (types.Int64, types.Hash): 1001,
    (types.Int128, types.Hash): 1001,
    (types.Int128, types.UInt128): 1001,
}

def conversion_lattice_cost(from_type, to_type):
    """
    Lookup the conversion cost in the conversion lattice to convert from_type to to_type.
    Return inf is the conversion is not allowed.
    """
     # the conversion lattice only has generic decimals as placeholders
    if isinstance(from_type, ir.DecimalType):
        from_type = types.GenericDecimal
    if isinstance(to_type, ir.DecimalType):
        to_type = types.GenericDecimal

    if (from_type, to_type) in CONVERSION_LATTICE:
        return CONVERSION_LATTICE[(from_type, to_type)]
    return float("inf")

# list of non-parametric types that are primitives. Avoid using this constant, use
# is_base_primitive instead because it accounts for parametric types like decimals.
_NON_PARAMETRIC_PRIMITIVES = [
    types.Int64,
    types.Int128,
    types.UInt128,
    types.Float,
    types.GenericDecimal,
    types.Bool,
    types.String,
    types.Date,
    types.DateTime,
    types.Hash
]

ENTITY_LIKES = [types.RowId]

# these are relations that try to preserve their input types
# e.g. if you add a USD and a Decimal, the result is still a USD
TYPE_PRESERVERS = [
    *builtins.plus.overloads,
    *builtins.minus.overloads,
    *builtins.mul.overloads,
    *builtins.mod.overloads,
    builtins.trunc_div,
    builtins.concat,
    *builtins.abs.overloads,
    *builtins.sum.overloads,
    *builtins.max.overloads,
    *builtins.min.overloads,
    # Exclude div overloads (like Int/Int -> Float) where the result type is different from the input types
    *(filter(lambda x: x.fields[0].type == x.fields[1].type == x.fields[2].type, builtins.div.overloads)),
    # Exclude avg overloads (avg Int -> Float) where the result type is different from the input types
    *(filter(lambda x: x.fields[0].type == x.fields[1].type, builtins.avg.overloads)),
]

#--------------------------------------------------
# Type helpers
#--------------------------------------------------

def is_abstract(type:ir.Type) -> bool:
    return types.is_abstract_type(type)

def to_type(value: ir.Value|ir.Field) -> ir.Type:
    if isinstance(value, (ir.Var, ir.Field, ir.Literal)):
        return value.type

    if isinstance(value, tuple):
        return types.AnyList

    if isinstance(value, ir.Relation):
        return types.AnyList

    raise TypeError(f"Cannot determine IR type for value: {value} of type {type(value).__name__}")

def type_matches(actual:ir.Type, expected:ir.Type, allow_expected_parents=False) -> bool:
    """
    True iff we can use a value of the actual type when expecting the expected type.

    TODO: document allow_expected_parents (useful for checking that a Person is an Adult)
    """
    # exact match
    if actual == expected:
        return True

    # any matches anything
    if actual == types.Any or expected == types.Any:
        return True

    # any entity matches any entity (surprise surprise!)
    if extends_any_entity(expected) and not is_primitive(actual):
        return True

    # all decimals match across each other
    if types.is_decimal(actual) and types.is_decimal(expected):
        return True

    # scalar matches with super-type handling
    is_scalar = isinstance(actual, ir.ScalarType)
    exp_is_scalar = isinstance(expected, ir.ScalarType)
    if is_scalar and any([type_matches(parent, expected) for parent in actual.super_types]):
        return True
    if allow_expected_parents and exp_is_scalar and any([type_matches(actual, parent, allow_expected_parents) for parent in expected.super_types]):
        return True
    if not is_primitive(expected) and exp_is_scalar and actual in ENTITY_LIKES:
        return True

    # a union type matches if any of its types match the expected type
    if isinstance(actual, ir.UnionType):
        for t in actual.types:
            if type_matches(t, expected):
                return True

    # types that match Number
    if actual == types.Number and types.is_number(expected):
        return True
    if expected == types.Number and types.is_number(actual):
        return True
    return False


def conversion_allowed(arg:ir.Value, actual:ir.Type, expected:ir.Type, arg_types:set[ir.Type]=set()) -> bool:
    return conversion_cost(arg, actual, expected, arg_types) < float("inf")

def literal_conversion_allowed(actual:ir.Type, expected:ir.Type) -> bool:
    if actual in (types.Int64, types.Int128) and (expected == types.Hash or types.is_number(expected)):
        return True
    elif types.is_decimal(actual) and expected == types.Float:
        return True
    elif types.is_decimal(actual) and types.is_decimal(expected):
        return True
    return False

def conversion_cost(arg: ir.Value, actual:ir.Type, expected:ir.Type, arg_types:set[ir.Type]) -> float:
    if type_matches(actual, expected):
        return 0

    # if we have a type variable and all the types in the expression
    # match, then there's no promotion needed and this is a valid overload
    if expected is types.EntityTypeVar and not is_primitive(actual) and len(arg_types) == 1:
        return 0

    # Literal numbers can be converted to other number types (but not to value types).
    if isinstance(arg, ir.Literal):
        if literal_conversion_allowed(actual, expected):
            return 50

    # Value types that don't match
    if is_value_type(actual) and is_value_type(expected):
        return float("inf")

    base_actual = to_base_primitive(actual)
    base_expected = to_base_primitive(expected)

    if not base_actual or not base_expected:
        return float("inf")

    if type_matches(base_actual, base_expected):
        return 0

    return conversion_lattice_cost(base_actual, base_expected)


def merge_types(type1: ir.Type, type2: ir.Type, is_literal1:bool, is_literal2:bool) -> ir.Type:
    if type1 == type2:
        return type1

    # give precedence to nominal types (e.g. merging USD(decimal) with decimal gives USD(decimal))
    base_primitive_type1 = to_base_primitive(type1)
    base_primitive_type2 = to_base_primitive(type2)
    if base_primitive_type1 == base_primitive_type2:
        if is_base_primitive(type1):
            return type2
        elif is_base_primitive(type2):
            return type1

    combined = ordered_set()
    types_to_process = [type1, type2]

    # Iterative flattening of union types
    while types_to_process:
        t = types_to_process.pop()
        if isinstance(t, ir.UnionType):
            types_to_process.extend(t.types)
        else:
            combined.add(t)

    # If we have multiple types and Any is one of them, remove Any
    if len(combined) > 1 and types.Any in combined:
        combined.remove(types.Any)

    # If we have multiple types and one is a literal and the other is not,
    # we can try to convert the literal to the other type.
    if len(combined) > 1:
        if is_literal1 and not is_literal2 and literal_conversion_allowed(type1, type2):
            return type2
        if is_literal2 and not is_literal1 and literal_conversion_allowed(type2, type1):
            return type1

    # Return single type or create a union
    return next(iter(combined)) if len(combined) == 1 else f.union_type(list(combined))

def to_base_primitive(type:ir.Type) -> Optional[ir.Type]:
    if isinstance(type, ir.ScalarType):
        if is_base_primitive(type):
            return type
        # walk the hierarchy to find a base primitive
        for parent in type.super_types:
            if found := to_base_primitive(parent):
                return found
    if isinstance(type, ir.UnionType):
        for t in type.types:
            if found := to_base_primitive(t):
                return found
    return None

def is_value_type(type:ir.Type):
    return isinstance(type, ir.ScalarType) and is_primitive(type) and not is_base_primitive(type)

def is_base_primitive(type:ir.Type) -> bool:
    return type in _NON_PARAMETRIC_PRIMITIVES or types.is_decimal(type)

def is_primitive(type:ir.Type) -> bool:
    return to_base_primitive(type) is not None

def extends_any_entity(type:ir.Type) -> bool:
    if type == types.AnyEntity:
        return True
    if isinstance(type, ir.ScalarType):
        for parent in type.super_types:
            if extends_any_entity(parent):
                return True
    return False

def invalid_type(type:ir.Type) -> bool:
    if isinstance(type, ir.UnionType):
        # if there are multiple primitives, or a primtive and a non-primitive
        # then we have an invalid type
        if len(type.types) > 1:
            return any([is_primitive(t) for t in type.types])
    return False

def try_preserve_type(types:set[ir.Type]) -> Optional[ir.Type]:
    # we keep the input type as the output type if either all inputs
    # are the exact same type or there's one nominal and its base primitive
    # type, e.g. USD + Decimal
    if len(types) == 1:
        return next(iter(types))
    if len(types) == 2:
        t1, t2 = types
        # type preservation is not applicable to decimal types
        if isinstance(t1, ir.DecimalType) and isinstance(t2, ir.DecimalType):
            return None
        base_equivalent = type_matches(t1, t2, allow_expected_parents=True)
        if base_equivalent:
            # as long as one of the types is a base primitive, we can use the
            # other type as final preserved type
            if is_base_primitive(t1):
                return t2
            elif is_base_primitive(t2):
                return t1
    return None

# Was this variable created for a shared literal?
def var_is_from_literal(var: ir.Var) -> bool:
    return var.name.startswith("__literal__")

#--------------------------------------------------
# Type Errors
#--------------------------------------------------

@dataclass
class TyperError():
    node: ir.Node

@dataclass
class TypeMismatch(TyperError):
    expected: ir.Type
    actual: ir.Type
    def __str__(self):
        return f"[red bold][Type Mismatch][/red bold] expected [yellow]{to_name(self.expected)}[/yellow], got [red]{to_name(self.actual)}[/red]: [white]{str(self.node).strip()}[/white]"

@dataclass
class InvalidType(TyperError):
    type: ir.Type
    def __str__(self):
        return f"[red bold][Invalid Type][/red bold] incompatible types [red]{to_name(self.type)}[/red]: [white]{str(self.node).strip()}[/white]"

@dataclass
class UnresolvedOverload(TyperError):
    arg_types: list[ir.Type]
    def __str__(self):
        assert isinstance(self.node, (ir.Lookup, ir.Update, ir.Aggregate))
        rel = to_relation(self.node)
        types = ', '.join([to_name(t) for t in self.arg_types])
        return f"[red bold][Unresolved Overload][/red bold] [yellow]{rel.name}({types})[/yellow]: [white]{str(self.node).strip()}[/white]"

@dataclass
class UnresolvedType(TyperError):
    def __str__(self):
        return f"[red bold][Unresolved Type][/red bold] [white]{str(self.node).strip()}[/white]"
    pass

class TyperContextEnricher(visitor.Visitor):
    def __init__(self):
        super().__init__()
        # store mapping from the concept population relation var id to a concept population type
        self.concept_population_types:dict[int, ir.Type] = {}

    def visit_lookup(self, node: ir.Lookup, parent: Optional[ir.Node]):
        rel = to_relation(node)
        if helpers.is_concept_lookup(rel):
            for arg, field in zip(node.args, rel.fields):
                if isinstance(arg, ir.Var):
                    arg_type = arg.type
                    field_type = field.type
                    # When the rule declares something like `Adult(v::Person)`, we must record that `v` is actually of type
                    #   `Adult` so this refined type is remembered for later checks.
                    if field_type != arg_type and type_matches(arg_type, field_type, True):
                        self.concept_population_types[arg.id] = field_type

#--------------------------------------------------
# Propagation Network
#--------------------------------------------------

# The core idea of the typer is to build a propagation network where nodes are vars, fields,
# or overloaded lookups/updates/aggregates. The intuition is that _all_ types in the IR
# ultimately flow from relation fields, so if we figure those out we just need to propagate
# their types to unknown vars, which may then flow into other fields and so on.
#
# This means the network only needs to contain nodes that either directly flow into
# an abstract node or are themselves abstract. We need to track overloads because
# their arguments effectively act like abstract vars until we've resolved the final types.

Node = Union[ir.Var, ir.Field, ir.Lookup, ir.Update, ir.Aggregate, ir.Literal]

class PropagationNetwork():
    def __init__(self):

        # track the set of nodes that represent entry points into the network
        self.roots = ordered_set()
        # we separately want to track nodes that were loaded from a previous run
        # so that even if we have edges to them, we _still_ consider them roots
        # and properly propagate types from them at the beginning
        self.loaded_roots = set()
        self.edges:dict[Node, dict[int, Node]] = defaultdict(dict)
        self.has_incoming = set()
        self.type_requirements:dict[Node, OrderedSet[ir.Field]] = defaultdict(lambda: ordered_set())

        self.errors:list[TyperError] = []
        # all fields for which types were resolved
        self.fields = set()
        self.resolved_types:dict[int, ir.Type] = {}
        # overloads resolved for a lookup/update/aggregate, by node id
        self.resolved_overloads:dict[int, list[ir.Relation]] = {}
        # if the node resolves to an overload the uses GenericDecimal, the concrete
        # DecimalType to be used (assumes there's a single overload with decimals for a node)
        self.resolved_overload_decimal:dict[int, ir.DecimalType] = {}
        self.node_is_literal:dict[int, bool] = {}

    #--------------------------------------------------
    # Mismatches
    #--------------------------------------------------

    def mismatch(self, node:Node, expected:ir.Type, actual:ir.Type):
        self.errors.append(TypeMismatch(node, expected, actual))

    def invalid_type(self, node:Node, type:ir.Type):
        self.errors.append(InvalidType(node, type))

    def unresolved_overload(self, node:ir.Lookup|ir.Update|ir.Aggregate):
        self.errors.append(UnresolvedOverload(node, [self.resolve(a) for a in node.args]))

    def unresolved_type(self, node:Node):
        self.errors.append(UnresolvedType(node))

    def has_errors(self, node:Node) -> bool:
        for mismatch in self.errors:
            if mismatch.node == node:
                return True
        return False

    #--------------------------------------------------
    # Types and Edges
    #--------------------------------------------------

    def add_edge(self, source:Node, target:Node):
        if target not in self.loaded_roots:
            self.roots.remove(target)
        if source not in self.has_incoming:
            self.roots.add(source)
        self.edges[source][target.id] = target
        self.has_incoming.add(target)

    def add_type(self, node:Node, type:ir.Type, is_literal:bool):
        if isinstance(node, ir.Field):
            self.fields.add(node)

        if node.id in self.resolved_types:
            if isinstance(node, ir.Literal) and self.resolved_types[node.id] == node.type:
                # if the previous "resolved type" was just the literal type itself, we can
                # replace it; this is safe because literals are only part of one task
                self.resolved_types[node.id] = type
            else:
                self.resolved_types[node.id] = merge_types(self.resolved_types[node.id], type, self.node_is_literal[node.id], is_literal)
        else:
            self.resolved_types[node.id] = type

        if node.id in self.node_is_literal:
            is_literal &= self.node_is_literal[node.id]
        self.node_is_literal[node.id] = is_literal

    def add_type_requirement(self, source:Node, field:ir.Field):
        self.type_requirements[source].add(field)

    #--------------------------------------------------
    # Load previous types
    #--------------------------------------------------

    def load_types(self, type_dict:dict[ir.Field, ir.Type]):
        for node, type in type_dict.items():
            self.add_type(node, type, False)
            self.loaded_roots.add(node)
            self.roots.add(node)

    #--------------------------------------------------
    # Resolve
    #--------------------------------------------------

    def resolve(self, value:Node|ir.Value) -> ir.Type:
        if isinstance(value, (ir.Var, ir.Field)):
            return self.resolved_types.get(value.id) or to_type(value)
        assert not isinstance(value, (ir.Lookup, ir.Update, ir.Aggregate)), "Should never try to resolve a task"
        return to_type(value)

    #--------------------------------------------------
    # Overloads
    #--------------------------------------------------

    def resolve_overload_deps(self, op:ir.Lookup|ir.Update|ir.Aggregate, keep_known=False):
        # We need to find which args flow into this task, which flow out, and
        # if some are inputs, then they are required before we can resolve
        incoming:list[Node] = []
        outgoing:list[Node] = []
        required:list[Node] = []
        relation = to_relation(op)
        field_args = zip(relation.fields, [self.resolve(a) for a in op.args], op.args)
        has_inputs = any([field.input for field in relation.fields])
        for field, arg_type, arg in field_args:
            if not isinstance(arg, (ir.Var, ir.Literal)):
                continue
            arg_is_abstract = is_abstract(arg_type)
            if not arg_is_abstract and not keep_known:
                continue
            elif field.input or not arg_is_abstract:
                incoming.append(arg)
                required.append(arg)
            elif not has_inputs:
                incoming.append(arg)
                outgoing.append(arg)
            else:
                outgoing.append(arg)

        # check if the overloads of this relation are fully resolved, if any aren't
        # then their fields are incoming edges to this node
        for overload in relation.overloads:
            for field in overload.fields:
                resolved_type = self.resolve(field)
                if resolved_type != types.GenericDecimal and is_abstract(resolved_type):
                    incoming.append(field)
                    required.append(field)

        return incoming, outgoing, required

    def resolve_overload(self, op:ir.Lookup|ir.Update|ir.Aggregate) -> Optional[list[ir.Relation]]:
        # check if we have any unresolved args that are required, if all of our args
        # are unresolved (len(incoming) == len(relation.fields)) then we have no information
        # to try and resolve the overloads with
        incoming, outgoing, required = self.resolve_overload_deps(op)
        relation = to_relation(op)
        if required or len(incoming) == len(relation.fields):
            return

        overloads = relation.overloads
        if not overloads:
            overloads = [relation]

        # otherwise we compute the cost of each overload and return the set of relations
        # that have the lowest cost. This can be multiple in e.g. the Person.pets.name
        # case where Cat_name and Dog_name are equally valid
        inf = float("inf")
        min_cost = inf
        matches = []
        for overload in overloads:
            arg_types = set(self.resolve(arg) for arg, field in zip(op.args, overload.fields) if field.input)
            total = 0
            for arg, field in zip(op.args, overload.fields):
                arg_type = self.resolve(arg)
                field_type = self.resolve(field)
                total += conversion_cost(arg, arg_type, field_type, arg_types)
                if total == inf:
                    break
            if total != inf and total <= min_cost:
                if total < min_cost:
                    min_cost = total
                    matches.clear()
                matches.append(overload)
        return matches

    #--------------------------------------------------
    # Propagation
    #--------------------------------------------------

    def propagate(self):
        edges = self.edges
        work_list = []

        # go through all the roots and find any that are not abstract, they'll
        # be the first nodes to push types through the network
        unhandled = ordered_set()
        for node in self.roots:
            if not isinstance(node, (ir.Var, ir.Field, ir.Literal)):
                continue
            node_type = self.resolve(node)
            if not is_abstract(node_type):
                is_literal = isinstance(node, ir.Literal) or (isinstance(node, ir.Var) and var_is_from_literal(node))
                self.add_type(node, node_type, is_literal)
                work_list.append(node)
            else:
                unhandled.add(node)

        # We need to visit nodes in topological order; that is we need to visit all predecessors
        # of a node before the node itself.

        # push known type nodes through the edges
        while work_list:
            source = work_list.pop(0)
            unhandled.remove(source)
            source_type = self.resolve(source)
            is_literal = self.node_is_literal.get(source.id, False)
            # check to see if the source has ended up with a set of types that
            # aren't valid, e.g. a union of primitives
            if invalid_type(source_type):
                self.invalid_type(source, source_type)

            # propagate our type to each outgoing edge
            for out in edges.get(source, {}).values():
                # if this is an overload then we need to try and resolve it
                if isinstance(out, (ir.Update, ir.Lookup, ir.Aggregate)):
                    found = self.resolve_overload(out)
                    if found is not None:
                        start_arg_types = [self.resolve(arg) for arg in out.args]
                        self.propagate_overloads(out, found)
                        final_arg_types = [self.resolve(arg) for arg in out.args]
                        for arg, start, final in zip(out.args, start_arg_types, final_arg_types):
                            if start != final:
                                work_list.append(arg)
                # otherwise, we just add to the outgoing node's type and if it
                # changes we add it to the work list
                elif start := self.resolve(out):
                    self.add_type(out, source_type, is_literal)
                    if start != self.resolve(out) or out in unhandled:
                        work_list.append(out)

        for source in unhandled:
            self.unresolved_type(source)

        # now that we've pushed all the types through the network, we need to validate
        # that all type requirements of those nodes are met
        for node, fields in self.type_requirements.items():
            node_type = self.resolve(node)
            for field in fields:
                field_type = self.resolve(field)
                if not type_matches(node_type, field_type):
                    node_base = to_base_primitive(node_type)
                    field_base = to_base_primitive(field_type)
                    if conversion_lattice_cost(node_base, field_base) == float("inf"):
                        self.mismatch(node, field_type, node_type)

        # return the resolved type for fields only
        field_types = {}
        for field in self.fields:
            if field.id in self.resolved_types:
                field_types[field] = self.resolved_types[field.id]
        return field_types


    def propagate_overloads(self, node:ir.Lookup|ir.Update|ir.Aggregate, overloads:list[ir.Relation]):
        if not overloads:
            return self.unresolved_overload(node)

        # we've resolved the overloads, so store that
        self.resolved_overloads[node.id] = overloads

        # we need to determine the final types of our args but taking all the overloads
        # and adding the type of their fields back to the args.
        resolved_args = [self.resolve(a) for a in node.args]
        for overload in overloads:
            resolved_fields = [self.resolve(f) for f in overload.fields]
            if types.GenericDecimal in resolved_fields:
                # this overload contains generic decimals, so find which specific type of
                # decimal to use given the arguments being passed
                decimal, resolved_fields = self.specialize_decimal_overload(resolved_fields, resolved_args)
                self.resolved_overload_decimal[node.id] = decimal

            # if our overload preserves types, we check to see if there's a preserved
            # output type given the inputs and if so, shadow the field's type with the
            # preserved type
            if overload in TYPE_PRESERVERS:
                input_types = set([arg_type for field, arg_type
                                    in zip(overload.fields, resolved_args)
                                    if field.input])
                if out_type := try_preserve_type(input_types):
                    resolved_fields = [field_type if field.input else out_type
                                        for field, field_type in zip(overload.fields, resolved_fields)]

            for field_type, arg_type, arg in zip(resolved_fields, resolved_args, node.args):
                if isinstance(arg, ir.Var) and is_abstract(arg_type):
                    is_literal = var_is_from_literal(arg)
                    self.add_type(arg, field_type, is_literal)
                elif isinstance(arg, ir.Literal) and arg_type != field_type:
                    self.add_type(arg, field_type, True)

        return None

    def specialize_decimal_overload(self, field_types:list[ir.Type], arg_types:list[ir.Type]) -> Tuple[ir.DecimalType, list[ir.Type]]:
        """
        Find the decimal type to use for an overload that has GenericDecimals in its field_types,
        and which is being referred to with these arg_types.

        Return a tuple where the first element is the specialized decimal type, and the second
        element is a new list that contains the same types as field_types but with
        GenericDecimal replaced by this specialized decimal.
        """
        decimal = None
        for arg_type in arg_types:
            x = types.decimal_supertype(arg_type)
            if isinstance(x, ir.DecimalType):
                # the current specialization policy is to select the decimal with largest
                # scale and, if there multiple with the largest scale, the one with the
                # largest precision. This is safe because when converting a decimal to the
                # specialized decimal, we never truncate fractional digits (because we
                # selected the largest scale) and, if the non-fractional digits are too
                # large to fit the specialized decimal, we will have a runtime overflow,
                # which should alert the user of the problem.
                #
                # In the future we can implement more complex policies. For example,
                # snowflake has well documented behavior for how the output of operations
                # behave in face of different decimal types, and we may use that:
                # https://docs.snowflake.com/en/sql-reference/operators-arithmetic#scale-and-precision-in-arithmetic-operations
                if decimal is None or x.scale > decimal.scale or (x.scale == decimal.scale and x.precision > decimal.precision):
                    decimal = x
        assert(isinstance(decimal, ir.DecimalType))
        return decimal, [decimal if field_type == types.GenericDecimal else field_type
                for field_type in field_types]


    #--------------------------------------------------
    # Display
    #--------------------------------------------------

    # draw the network as a mermaid graph for the debugger
    def to_mermaid(self, max_edges=500) -> str:
        resolved = self.resolved_types
        nodes = ordered_set()
        link_strs = []
        for src, dsts in self.edges.items():
            nodes.add(src)
            for dst in dsts.values():
                if len(link_strs) > max_edges:
                    break
                nodes.add(dst)
                link_strs.append(f"n{src.id} --> n{dst.id}")
            if len(link_strs) > max_edges:
                break

        for src, dsts in self.type_requirements.items():
            nodes.add(src)
            for dst in dsts:
                if len(link_strs) > max_edges:
                    break
                nodes.add(dst)
                link_strs.append(f"n{src.id} --> n{dst.id}")
            if len(link_strs) > max_edges:
                break

        def type_span(t:ir.Type) -> str:
            type_str = t.name if isinstance(t, ir.ScalarType) else str(t)
            return f"<span style='color:cyan;'>{type_str.strip()}</span>"

        def overload_span(rel:ir.Relation, arg_types:list[ir.Type]) -> str:
            args = []
            for field, arg_type in zip(rel.fields, arg_types):
                field_type = self.resolve(field)
                if not type_matches(arg_type, field_type) and field_type != types.EntityTypeVar:
                    args.append(f"<span style='color:yellow;'>{str(arg_type).strip()} -> {str(field_type).strip()}</span>")
                elif isinstance(arg_type, ir.UnionType):
                    args.append(type_span(field_type))
                else:
                    args.append(type_span(arg_type))
            return f'{rel.name}({", ".join(args)})'

        node_strs = []
        for node in nodes:
            klass = ""
            if isinstance(node, ir.Var):
                ir_type = resolved.get(node.id) or self.resolve(node)
                type_str = type_span(ir_type)
                # if this is one of our vars that is a placeholder for a literal, just use the type
                if isinstance(ir_type, ir.ScalarType) and var_is_from_literal(node):
                    label = f'(["Literal {type_str}"])'
                else:
                    label = f'(["{node.name}: {type_str}"])'
            elif isinstance(node, ir.Literal):
                ir_type = resolved.get(node.id) or self.resolve(node)
                type_str = type_span(ir_type)
                label = f'(["Literal {type_str}"])'
            elif isinstance(node, ir.Field):
                ir_type = resolved.get(node.id) or self.resolve(node)
                type_str = type_span(ir_type)
                klass = ":::field"
                label = f"{{{{\"{node.name}: {type_str}\"}}}}"
            elif isinstance(node, (ir.Lookup, ir.Update, ir.Aggregate)):
                arg_types = [self.resolve(arg) for arg in node.args]
                if node.id in self.resolved_overloads:
                    overloads = self.resolved_overloads[node.id]
                    content = "<br/>".join([overload_span(o, arg_types) for o in overloads])
                else:
                    content = overload_span(to_relation(node), arg_types)
                label = f'[/"{content}"/]'
            else:
                raise NotImplementedError(f"Unknown node type: {type(node)}")
            if self.has_errors(node):
                klass = ":::error"
            node_strs.append(f"n{node.id}{label}{klass}")

        node_str = "\n                ".join(node_strs)
        link_str = "\n                ".join(link_strs)
        template = f"""
            %%{{init: {{'theme':'dark', 'flowchart':{{'useMaxWidth':false, 'htmlLabels': true}}}}}}%%
            flowchart TD
                linkStyle default stroke:#666
                classDef field fill:#245,stroke:#478
                classDef error fill:#624,stroke:#945,color:#f9a
                classDef default stroke:#444,stroke-width:2px, font-size:12px

                %% nodes
                {node_str}

                %% edges
                {link_str}
        """
        return template

    # simplified, less verbose (compared to mermaid) output for snapshot testing
    def to_fish(self) -> str:
        resolved = self.resolved_types
        nodes = ordered_set()
        for src, dsts in self.edges.items():
            nodes.add(src)
            nodes.update(dsts.values())
        for src, dsts in self.type_requirements.items():
            nodes.add(src)
            nodes.update(dsts)

        def type_to_str(t:ir.Type) -> str:
            type_str = t.name if isinstance(t, ir.ScalarType) else str(t)
            return type_str.strip()

        def overload_str(rel:ir.Relation, arg_types:list[ir.Type]) -> str:
            args = []
            for field, arg_type in zip(rel.fields, arg_types):
                field_type = self.resolve(field)
                if not type_matches(arg_type, field_type):
                    args.append(f"{str(arg_type).strip()} -?> {str(field_type).strip()}")
                elif isinstance(arg_type, ir.UnionType):
                    args.append(type_to_str(field_type))
                else:
                    args.append(type_to_str(arg_type))
            return f'{rel.name}({", ".join(args)})'

        def node_kind(node:ir.Node) -> str:
            if isinstance(node, (ir.Lookup, ir.Update, ir.Aggregate)):
                return "overload"
            return type(node).__name__.lower()

        def error_info(err:TyperError) -> str:
            if isinstance(err, TypeMismatch):
                return f'Type Mismatch|expected {to_name(err.expected)}, got {to_name(err.actual)}'
            return f'{type(err).__name__}'

        nl = "\n"
        node_strs = []
        for node in nodes:
            info = ""
            if isinstance(node, ir.Var):
                ir_type = resolved.get(node.id) or self.resolve(node)
                if not(isinstance(ir_type, ir.ScalarType) and var_is_from_literal(node)):
                    info = f'{node.name}|{type_to_str(ir_type)}'
            elif isinstance(node, ir.Literal):
                ir_type = resolved.get(node.id) or self.resolve(node)
                if not(isinstance(ir_type, ir.ScalarType)):
                    info = f'Literal|{type_to_str(ir_type)}'
            elif isinstance(node, ir.Field):
                ir_type = resolved.get(node.id) or self.resolve(node)
                info = f'{node.name}|{type_to_str(ir_type)}'
            elif isinstance(node, (ir.Lookup, ir.Update, ir.Aggregate)):
                arg_types = [self.resolve(arg) for arg in node.args]
                if node.id in self.resolved_overloads:
                    overloads = self.resolved_overloads[node.id]
                    content = nl.join([overload_str(o, arg_types) for o in overloads])
                else:
                    content = overload_str(to_relation(node), arg_types)
                info = f'{content}'
            else:
                raise NotImplementedError(f"Unknown node type: {type(node)}")

            if info:
                error_suffix = " !" if self.has_errors(node) else ""
                node_strs.append(f'{node_kind(node)}|{info}{error_suffix}')

        node_strs.sort()
        if self.errors:
            node_strs.append("---ERRORS---")
            for err in self.errors:
                node_strs.append(f'{error_info(err)} ({str(err.node).strip()})')

        return f"""{nl.join(node_strs)}"""

#--------------------------------------------------
# Analyzer
#--------------------------------------------------

class Analyzer(visitor.Visitor):
    def __init__(self):
        super().__init__()
        self.net = PropagationNetwork()
        self.context_enricher = TyperContextEnricher()

        # this is a map of literal types to a var representing that literal in
        # the graph. This allows us to collapse all literals into a single node
        # and avoids exploding node count if lots of data gets added directly
        self.shared_literal_vars:dict[ir.Type, ir.Var] = {
            t: f.var(f"__literal__{t.name}", t)
            for t in types.builtin_types
            if isinstance(t, ir.ScalarType)
        }

    #--------------------------------------------------
    # Literal types
    #--------------------------------------------------

    # given a literal type, lookup or create a var for it
    def shared_literal_var(self, node:ir.Type) -> ir.Var:
        assert isinstance(node, ir.ScalarType)
        if node not in self.shared_literal_vars:
            self.shared_literal_vars[node] = f.var(node.name, node)
        return self.shared_literal_vars[node]

    #--------------------------------------------------
    # Lookups + Aggregates
    #--------------------------------------------------

    def visit_lookup(self, node: ir.Lookup, parent: Optional[ir.Node]):
        self.visit_rel_op(node, parent)

    def visit_aggregate(self, node: ir.Aggregate, parent: ir.Node | None):
        self.visit_rel_op(node, parent)

    def visit_rel_op(self, node: ir.Lookup|ir.Aggregate, parent: Optional[ir.Node]):
        rel = to_relation(node)
        if isinstance(node, ir.Lookup) and builtins.is_eq(rel):
            return self.visit_eq(node, parent)
        if isinstance(node, ir.Lookup) and rel == builtins.cast:
            return self.visit_cast(node, parent)

        if rel.overloads:
            return self.visit_overloaded(node, parent)

        # if this is a population check, then it's fine to pass a subtype in to do the check
        # e.g. Employee(Person) is a valid way to check if a person is an employee
        is_concept_lookup = helpers.is_concept_lookup(rel)
        arg_types = set(self.net.resolve(arg) for arg, field in zip(node.args, rel.fields) if field.input)
        for arg, field in zip(node.args, rel.fields):
            field_type = field.type
            arg_type = self.net.resolve(arg)
            is_var = isinstance(arg, ir.Var)
            if not type_matches(arg_type, field_type, is_concept_lookup or is_abstract(arg_type)):
                # If the rule explicitly specifies a refined type, e.g. `Adult(v::Person)`,
                #   then `v` should be treated as `Adult` (not just `Person`).
                # In that case, check the declared population type first before checking conversions.
                if is_var and self.context_enricher.concept_population_types.get(arg.id, arg_type) == field_type:
                    continue
                # Do not complain if we can convert the arg to the field type.
                if not conversion_allowed(arg, arg_type, field_type, arg_types):
                    self.net.mismatch(node, field_type, arg_type)
                    continue
            # if we have an abstract var then this field will ultimately propagate to that
            # var's type
            elif is_var and is_abstract(arg_type) and not field.input:
                self.net.add_edge(field, arg)
                continue

        return None

    #--------------------------------------------------
    # Overloads
    #--------------------------------------------------

    def visit_overloaded(self, node: ir.Lookup|ir.Update|ir.Aggregate, parent: Optional[ir.Node]):
        incoming, outgoing, required = self.net.resolve_overload_deps(node, keep_known=True)
        for arg in incoming:
            self.net.add_edge(arg, node)
        for arg in outgoing:
            self.net.add_edge(node, arg)

    #--------------------------------------------------
    # Eq
    #--------------------------------------------------

    def visit_eq(self, node: ir.Lookup, parent: Optional[ir.Node]):
        (left, right) = node.args
        left_type = self.net.resolve(left)
        right_type = self.net.resolve(right)
        if is_abstract(left_type) and is_abstract(right_type):
            assert isinstance(left, ir.Var) and isinstance(right, ir.Var)
            # if both sides are abstract, then whatever we find out about
            # either should propagate to the other
            self.net.add_edge(left, right)
            self.net.add_edge(right, left)
        elif is_abstract(left_type):
            assert isinstance(left, ir.Var)
            if isinstance(right, ir.Var):
                self.net.add_edge(right, left)
            else:
                literal_var = self.shared_literal_var(right_type)
                self.net.add_edge(literal_var, left)
        elif is_abstract(right_type):
            assert isinstance(right, ir.Var)
            if isinstance(left, ir.Var):
                self.net.add_edge(left, right)
            else:
                literal_var = self.shared_literal_var(left_type)
                self.net.add_edge(literal_var, right)
        elif not type_matches(left_type, right_type):
            if not conversion_allowed(left, left_type, right_type) and not conversion_allowed(right, right_type, left_type):
                self.net.mismatch(node, left_type, right_type)

    #--------------------------------------------------
    # Cast
    #--------------------------------------------------

    def visit_cast(self, node: ir.Lookup, parent: Optional[ir.Node]):
        # Cast has fields: to_type (input), source (input), target (output)
        assert len(node.args) == 3, f"Expected 3 arguments for cast builtin, but got: {node.args}"
        (to_type, source, target) = node.args
        assert isinstance(to_type, ir.Type), f"Invalid target type for cast: {to_type}"
        assert isinstance(target, ir.Var), f"Invalid target variable for cast: {target}"

        if not is_abstract(to_type):
            # If target is abstract, it should get the type from to_type
            target_type = self.net.resolve(target)
            if is_abstract(target_type) and isinstance(target, ir.Var):
                self.net.add_type(target, to_type, False)

    #--------------------------------------------------
    # Update
    #--------------------------------------------------

    def visit_update(self, node: ir.Update, parent: Optional[ir.Node]):
        rel = node.relation
        # if this is a population check, then it's fine to pass a subtype in to do the population
        # e.g. Employee(Person) should be a valid way to populate a person
        allow_any_parents = helpers.is_concept_lookup(rel)
        for arg, field in zip(node.args, rel.fields):
            field_type = field.type
            arg_type = self.net.resolve(arg)
            is_var = isinstance(arg, ir.Var)

            # if the arg is abstract, but the field isn't, then we need to make
            # sure that once the arg is resolved we check that it matches the field
            # type
            if is_var and is_abstract(arg_type) and not is_abstract(field_type):
                self.net.add_type_requirement(arg, field)

            # if the field is abstract, then eventually this var will help determine
            # the field's type
            elif is_abstract(field_type):
                source = self.shared_literal_var(arg_type) if not is_var else arg
                self.net.add_edge(source, field)

            elif not type_matches(arg_type, field_type, allow_expected_parents=allow_any_parents):
                # If the rule explicitly specifies a refined type, e.g. `Adult(v::Person)`,
                #   then `v` should be treated as `Adult` (not just `Person`).
                # In that case, check the declared population type first before checking conversions.
                if is_var and self.context_enricher.concept_population_types.get(arg.id, arg_type) == field_type:
                    continue
                if not conversion_allowed(arg, arg_type, field_type):
                    self.net.mismatch(node, field_type, arg_type)

#--------------------------------------------------
# Replacer
#--------------------------------------------------

# Once we've pushed all the types through the network, we need to replace the types of
# fields and vars that we may have discovered. We also need to replace overloaded lookups
# with the choosen overloads and do any conversions that are needed.
@dataclass
class Replacer(visitor.Rewriter):
    net: PropagationNetwork = dataclasses.field(init=True)
    new_relations:OrderedSet[ir.Relation] = dataclasses.field(default_factory=OrderedSet[ir.Relation])

    def handle_model(self, model: ir.Model, parent: None):
        model = super().handle_model(model, parent)
        return model.reconstruct(
            relations=model.relations | self.new_relations
        )

    def handle_field(self, node: ir.Field, parent: ir.Node):
        if node.id in self.net.resolved_types:
            return f.field(node.name, self.net.resolved_types[node.id], node.input)
        return node

    def handle_var(self, node: ir.Var, parent: ir.Node):
        if node.id in self.net.resolved_types:
            return f.var(node.name, self.net.resolved_types[node.id])
        return node

    def handle_literal(self, node: ir.Literal, parent: ir.Node):
        # Up until now, we allow literals to have a non-builtin types. This code converts the value
        # to a builtin Python type and lifts the literal to that supertype.
        t = self.net.resolved_types[node.id] if node.id in self.net.resolved_types else node.type
        v, t = self.convert_literal_value(node.value, t)
        return node.reconstruct(value=v, type=t)

    def handle_update(self, node: ir.Update, parent: ir.Node):
        node = super().handle_update(node, parent)

        # we may do conversions, so we can end up with multiple tasks
        # in this branch and we need to track what the final args are
        tasks = []
        final_args = []
        for arg, field in zip(node.args, node.relation.fields):
            arg_type = to_type(arg)
            field_type = to_type(field)
            # the typer previously made sure that this should be valid so
            # a type mismatch means we need to convert as long as this isn't
            # a type variable
            if field_type != types.EntityTypeVar and not type_matches(arg_type, field_type):
                arg_base = to_base_primitive(arg_type)
                field_base = to_base_primitive(field_type)
                if arg_base is not None and field_base is not None and conversion_allowed(arg, arg_base, field_base):
                    new_arg = self.convert(arg, arg_base, field_base, tasks)
                    final_args.append(new_arg)
                else:
                    final_args.append(arg)
            else:
                final_args.append(arg)
        tasks.append(node.reconstruct(args=tuple(final_args)))

        if len(tasks) == 1:
            return tasks[0]
        else:
            return f.logical(tasks, [])

    def handle_aggregate(self, node: ir.Aggregate, parent: ir.Node):
        node = super().handle_aggregate(node, parent)
        lookup_args = list(node.args)
        hoists = helpers.get_agg_outputs(node)

        if len(node.aggregation.fields) == len(lookup_args):
            tasks = []
            for i in range(len(lookup_args)):
                if not conversion_allowed(lookup_args[i], to_type(lookup_args[i]), node.aggregation.fields[i].type):
                    self.net.mismatch(node, node.aggregation.fields[i].type, to_type(lookup_args[i]))
                elif not type_matches(to_type(lookup_args[i]), node.aggregation.fields[i].type):
                    lookup_args[i] = self.convert(lookup_args[i], to_type(lookup_args[i]), node.aggregation.fields[i].type, tasks)
            tasks.append(node.reconstruct(args=tuple(lookup_args)))
            if len(tasks) == 1:
                return tasks[0]
            else:
                return f.logical(tasks, hoists)

        return node

    def handle_lookup(self, node: ir.Lookup, parent: ir.Node):
        node = super().handle_lookup(node, parent)
        lookup_args = node.args

        # we can resolve to multiple overloads, that we'd need to union
        # so we'll need to hoist all the vars being output to make sure
        # everything joins correctly
        hoists = helpers.get_outputs(node)
        branches:list[ir.Logical] = []

        # Special case this solver primitive because the type system cannot handle what it
        # needs, which is an input field types as List[Union[Int64,Float64,String,Hash]].
        # So this code makes sure that any in128 that flows into the second argument, which
        # is represented as a tuple, is converted into an int64, which is lossy but should
        # work for most cases
        if node.relation == builtins.rel_primitive_solverlib_fo_appl and len(node.relation.fields) == 3 and len(lookup_args) == 3:
            tasks = []
            # Make lookup_args mutable.
            lookup_args = list(lookup_args)

            # Convert the first and third arguments to the field types.
            for i in [0, 2]:
                if not conversion_allowed(lookup_args[i], to_type(lookup_args[i]), node.relation.fields[i].type):
                    self.net.mismatch(node, node.relation.fields[i].type, to_type(lookup_args[i]))
                elif not type_matches(to_type(lookup_args[i]), node.relation.fields[i].type):
                    lookup_args[i] = self.convert(lookup_args[i], to_type(lookup_args[i]), node.relation.fields[i].type, tasks)

            varargs = lookup_args[1]
            final_varargs = []
            assert isinstance(varargs, tuple)
            for arg in varargs:
                t = to_type(arg)
                if t == types.Int128:
                    final_varargs.append(self.convert(arg, t, types.Int64, tasks))
                else:
                    final_varargs.append(arg)
            lookup_args[1] = tuple(final_varargs)
            tasks.append(node.reconstruct(args=tuple(lookup_args)))
            branches.append(f.logical(tasks, hoists))

        elif builtins.is_eq(node.relation):
            tasks = []

            # We need to handle eq specially because its arguments can be converted symmetrically
            (left, right) = lookup_args
            left_type = to_type(left)
            right_type = to_type(right)
            mismatch = False
            if not type_matches(left_type, right_type):
                if conversion_allowed(left, left_type, right_type):
                    new_left = self.convert(left, left_type, right_type, tasks)
                    final_args = [new_left, right]
                elif conversion_allowed(right, right_type, left_type):
                    new_right = self.convert(right, right_type, left_type, tasks)
                    final_args = [left, new_right]
                else:
                    self.net.mismatch(node, left_type, right_type)
                    final_args = [left, right]
                    mismatch = True
            else:
                final_args = [left, right]

            if not mismatch:
                min_cost = float('inf')
                arg_types = set(to_type(arg) for arg in final_args)
                resolved = []
                for o in node.relation.overloads:
                    total = 0
                    for arg, field in zip(final_args, o.fields):
                        arg_type = to_type(arg)
                        field_type = to_type(field)
                        total += conversion_cost(arg, arg_type, field_type, arg_types)
                    if total <= min_cost:
                        if total < min_cost:
                            resolved.clear()
                            min_cost = total
                        resolved.append(o)

                if len(resolved) == 1:
                    tasks.append(f.lookup(resolved[0], final_args))
                else:
                    # If we cannot resolve the overload, just leave it.
                    self.net.unresolved_overload(node)
                    tasks.append(f.lookup(node.relation, final_args))
            else:
                # If there's a mismatch, just leave the original relation.
                tasks.append(f.lookup(node.relation, final_args))

            branches.append(f.logical(tasks, hoists))
        elif node.relation == builtins.cast:
            assert len(node.args) == 3, f"Invalid number of arguments for cast: {node.args}"
            (tgt_type, src, tgt) = node.args
            assert isinstance(tgt_type, ir.Type), f"Invalid target type for cast: {tgt_type}"
            src_type = to_type(src)

            # if we are casting a literal into a var, we can just set the var to a new literal
            # with the same value but with the same type as the variable
            if isinstance(src, ir.Literal) and literal_conversion_allowed(src_type, tgt_type):
                annos = node.annotations
                return f.lookup(builtins.eq, (ir.Literal(tgt_type, src.value), tgt), annos=(list(annos) + [builtins.from_cast_annotation]))

            src_base = to_base_primitive(src_type)
            tgt_base = to_base_primitive(tgt_type)

            if src_base and tgt_base and src_base == tgt_base:
                annos = node.annotations
                return f.lookup(builtins.eq, (src, tgt), annos=(list(annos) + [builtins.from_cast_annotation]))

            if conversion_allowed(node.args[0], src_type, tgt_type):
                if tgt_base:
                    return node.reconstruct(args=(tgt_base, src, tgt))
                else:
                    return node
            else:
                # TODO: we are simply ignoring this, assuming there's some way to cast it
                # self.net.mismatch(node, src_type, tgt_type)
                return node
        else:
            if node.id in self.net.resolved_overloads:
                resolved = self.net.resolved_overloads[node.id]
            else:
                resolved = [node.relation]
            decimal_type = self.net.resolved_overload_decimal.get(node.id)

            for overload in resolved:
                # we may do conversions, so we can end up with multiple tasks
                # in this branch and we need to track what the final args are
                tasks = []
                final_args = []

                for arg, field in zip(lookup_args, overload.fields):
                    arg_type = to_type(arg)
                    field_type = to_type(field)
                    # the typer previously made sure that this should be valid so
                    # a type mismatch means we need to convert as long as this isn't
                    # a type variable
                    if field_type == types.GenericDecimal or (field_type != types.EntityTypeVar and not arg_type == field_type):
                        arg_base = to_base_primitive(arg_type)
                        field_base = to_base_primitive(field_type)
                        if field_base == types.GenericDecimal:
                            field_base = decimal_type
                        if arg_base is not None and field_base is not None and conversion_allowed(arg, arg_base, field_base):
                            new_arg = self.convert(arg, arg_base, field_base, tasks)
                            final_args.append(new_arg)
                        else:
                            final_args.append(arg)
                    else:
                        final_args.append(arg)
                tasks.append(f.lookup(overload, final_args))
                branches.append(f.logical(tasks, hoists))
        # unwrap if we don't actually need a union
        if len(branches) == 1:
            if len(branches[0].body) == 1:
                return branches[0].body[0]
            else:
                return branches[0]
        else:
            return f.union(branches, hoists)

    def convert(self, arg:ir.Value, actual:ir.Type, expected:ir.Type, tasks:list[ir.Task]) -> ir.Value:
        if actual == expected:
            return arg
        value = None
        if isinstance(arg, ir.Literal):
            value = arg.value
        elif isinstance(arg, (int, float, PyDecimal)):
            value = arg
        if value is not None:
            if isinstance(value, int) and expected in (types.Int64, types.Int128):
                if expected == types.Int64:
                    check_int64(value)
                return f.literal(value, expected)
            if isinstance(value, (int, float, PyDecimal)) and expected == types.Float:
                return f.literal(float(value), expected)
            if isinstance(value, (int, float, PyDecimal)) and types.is_decimal(expected):
                # Converting str(value) rather than value avoids precision loss with Float->Decimal conversion.
                return f.literal(PyDecimal(str(value)), expected)

        name = helpers.sanitize(arg.name + "_" + to_name(expected) if isinstance(arg, ir.Var) else f"v{to_name(expected)}")
        expected_base = to_base_primitive(expected) or expected
        new_arg = f.var(name, expected_base)
        self.new_relations.add(builtins.cast)
        tasks.append(f.lookup(builtins.cast, (expected_base, arg, new_arg)))
        self.new_relations.add(builtins.cast)
        return new_arg

    @staticmethod
    def convert_literal_value(value, t: ir.Type):
        if types.is_subtype(t, types.String):
            return value, types.String
        if isinstance(value, str) and types.is_subtype(t, types.DateTime):
            return datetime.datetime.fromisoformat(value), types.DateTime
        if isinstance(value, str) and types.is_subtype(t, types.Date):
            return datetime.date.fromisoformat(value), types.Date
        if isinstance(value, int) and types.is_subtype(t, types.Int64):
            check_int64(value)
            return value, types.Int64
        if isinstance(value, int) and types.is_subtype(t, types.Int128):
            return value, types.Int128
        if isinstance(value, (int, float, PyDecimal)) and types.is_subtype(t, types.Float):
            return float(value), types.Float
        if isinstance(value, (int, float, PyDecimal)) and types.is_decimal_subtype(t):
            return PyDecimal(str(value)), types.decimal_supertype(t)
        return value, t

#--------------------------------------------------
# Typer pass
#--------------------------------------------------

class InferTypes(compiler.Pass):
    def __init__(self):
        super().__init__()
        self.historical = {}

    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        w = Analyzer()
        w.net.load_types(self.historical)

        # collect some type info before analyzing it
        with debugging.span("type.collect"):
            model.root.accept(w.context_enricher, model)

        # build the propagation network
        with debugging.span("type.analyze"):
            model.root.accept(w, model)

        # propagate the types through the network
        with debugging.span("type.propagate") as end_span:
            field_types = w.net.propagate()
            self.historical.update(field_types)
            end_span["type_graph"] = w.net.to_mermaid()
            end_span["type_report"] = w.net.to_fish()

        # replace the fields in the model with the new types
        with debugging.span("type.replace"):
            final = Replacer(w.net).walk(model)

        for err in w.net.errors:
            rich.print(str(err), file=sys.stderr)

        return final
