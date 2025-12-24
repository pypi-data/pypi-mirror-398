"""
    Elementary IR types.
"""
from __future__ import annotations
from . import ir, util
import re
import sys
from typing import cast, Optional
from functools import reduce

# cache of decimal types being used, keyed by their names, e.g. Decimal(38,14)
_decimal_types = dict[str, ir.DecimalType]()

def decimal(precision: int, scale: int):
    """ Lookup or create a decimal with this precision and scale. """
    type_str = f"Decimal({precision},{scale})"
    if type_str not in _decimal_types:
        _decimal_types[type_str] = create_decimal(precision, scale)
    return _decimal_types[type_str]

def decimal_by_type_str(type_str: str):
    """
        Lookup or create a decimal with this type string, which should match
        the pattern Decimal(precision,scale).
     """
    if type_str not in _decimal_types:
        _decimal_types[type_str] = create_decimal_type_by_type_str(type_str)
    return _decimal_types[type_str]

def create_decimal_type_by_type_str(type_str: str) -> ir.DecimalType:
    """
        Create a new decimal type with precision/scale based on parsing the type string as
        a Decimal(precision,scale) pattern.
    """
    pattern = r'^([a-zA-Z0-9_]+)\(\s*([0-9]+)\s*,\s*([0-9]+)\s*\)$'
    match = re.search(pattern, type_str)
    if match:
        _, precision, scale = match.group(1), match.group(2), match.group(3)
        return create_decimal(int(precision), int(scale))
    raise ValueError(f"Invalid decimal type name: {type_str}.")

def create_decimal(precision: int, scale: int) -> ir.DecimalType:
    """ Create a new decimal type with this precision and scale. """
    if precision < 0 or precision > 38 or scale < 0 or scale > 38 or scale > precision:
        raise ValueError(f"Unsupported decimal type with precision {precision}, scale {scale}.")
    return ir.DecimalType(f"Decimal({precision},{scale})", util.frozen(), util.frozen(), precision, scale)

def digits_to_bits(precision)-> int:
    """
    Transform from a number of base 10 digits to the number of bits necessary to represent
    that. If the precision is larger than 38, return None as that is not supported.

    For example, a number with 38 digits requires 128 bits.
    """
    if precision <= 2:
        return 8
    elif precision <= 4:
        return 16
    elif precision <= 9:
        return 32
    elif precision <= 18:
        return 64
    elif precision <= 38:
        return 128
    raise ValueError(f"Invalid numeric precision '{precision}'")

#
# Abstract types
#

# any numeric type
Number = ir.ScalarType("Number", util.frozen())
# parametric type representing any decimal type (i.e. a DecimalType with any precision/scale);
# this should only be used in relation definitions, to represent the fact that it can be
# specialized for any decimal in a monotyped fashion.
GenericDecimal = ir.ScalarType("GenericDecimal", util.frozen())

#
# Basic Types
#
Null = ir.ScalarType("Null", util.frozen())
Any = ir.ScalarType("Any", util.frozen())
AnyEntity = ir.ScalarType("AnyEntity", util.frozen())
Hash = ir.ScalarType("Hash", util.frozen())
String = ir.ScalarType("String", util.frozen())
Int64 = ir.ScalarType("Int64")
Int128 = ir.ScalarType("Int128")
UInt128 = ir.ScalarType("UInt128")
Float = ir.ScalarType("Float", util.frozen())
Decimal = decimal(38, 14)
Bool = ir.ScalarType("Bool", util.frozen())
Binary = ir.ScalarType("Binary", util.frozen()) # 0 or 1
Date = ir.ScalarType("Date", util.frozen())
DateTime = ir.ScalarType("DateTime", util.frozen())
Symbol = ir.ScalarType("Symbol", util.frozen())
Sha1 = ir.ScalarType("SHA1", util.frozen())
RowId = ir.ScalarType("RowId", util.frozen(UInt128))
Enum = ir.ScalarType("Enum", util.frozen())

# a special type that represent an entity that is of a
# single type in a given expression. This allows us to create
# overloads for e.g. Person < Person, but fails Person < Car
EntityTypeVar = ir.ScalarType("EntityTypeVar", util.frozen())

AnyList = ir.ListType(Any)

def is_builtin(t: ir.Type):
    return t in builtin_types

def _compute_builtin_types() -> list[ir.Type]:
    module = sys.modules[__name__]
    types = []
    for name in dir(module):
        builtin = getattr(module, name)
        if isinstance(builtin, ir.Type):
            types.append(builtin)
    return types

builtin_types = _compute_builtin_types()
builtin_scalar_types_by_name = dict((t.name, t) for t in cast(list[ir.ScalarType], util.filter_by_type(builtin_types, ir.ScalarType)))

def is_any(t: ir.Type) -> bool:
    return t == Any

def is_value_base_type(t: ir.Type) -> bool:
    return isinstance(t, ir.DecimalType) or (isinstance(t, ir.ScalarType) and t in [Hash, String, Number, Int64, Int128, Float, Bool, Binary, Symbol, Sha1, Date, DateTime])

def is_value_type(t: ir.Type) -> bool:
    if is_value_base_type(t):
        return True
    if isinstance(t, ir.ScalarType):
        t = cast(ir.ScalarType, t)
        if len(t.super_types) == 1:
            # Not sure why we need this cast, but it does shut up the type checker.
            s = cast(ir.Type, t.super_types[0])
            if is_value_type(s):
                return True
    return False

def is_entity_type(t: ir.Type) -> bool:
    return isinstance(t, ir.ScalarType) and not is_value_type(t)

def is_null(t: ir.Type) -> bool:
    return t == Null

def is_abstract_type(t: ir.Type) -> bool:
    if isinstance(t, ir.ScalarType):
        return t in [Any, AnyEntity, Number, GenericDecimal]
    elif isinstance(t, ir.ListType):
        return is_abstract_type(t.element_type)
    elif isinstance(t, ir.TupleType):
        return any(is_abstract_type(t) for t in t.types)
    elif isinstance(t, ir.UnionType):
        return any(is_abstract_type(t) for t in t.types)
    else:
        return False

def is_decimal(t: ir.Type) -> bool:
    """ True if the type is some specific decimal or the abstract decimal. """
    return isinstance(t, ir.DecimalType) or t == GenericDecimal

def is_number(t: ir.Type) -> bool:
    return t in (Int64, Int128, Float) or is_decimal(t)


def union(*types: ir.Type) -> ir.Type:
    if len(types) == 0:
        return Null
    elif len(types) == 1:
        return types[0]

    if any(isinstance(t, ir.UnionType) for t in types):
        def _union_elements(t: ir.Type) -> util.FrozenOrderedSet[ir.Type]:
            if isinstance(t, ir.UnionType):
                return t.types
            else:
                return util.ordered_set(t).frozen()
        types = tuple([u for t in types for u in _union_elements(t) if not is_null(u)])

    # Remove types subsumed by other types.
    types = tuple([t for t in types if not any(is_proper_subtype(t, s) for s in types)])

    # Check again for the simple cases.
    if len(types) == 0:
        return Null
    elif len(types) == 1:
        return types[0]

    return ir.UnionType(util.ordered_set(*types).frozen())

def intersect(*types: ir.Type) -> ir.Type:
    """
    Intersect a list of types.
    """
    return reduce(intersect_binary, types, Any)

def intersect_binary(t1: ir.Type, t2: ir.Type) -> ir.Type:
    if is_null(t1) or is_null(t2):
        return Null
    elif is_any(t1):
        return t2
    elif is_any(t2):
        return t1
    elif is_subtype(t1, t2):
        return t1
    elif is_subtype(t2, t1):
        return t2
    elif isinstance(t1, ir.UnionType):
        return union(*[intersect_binary(s1, t2) for s1 in t1.types])
    elif isinstance(t2, ir.UnionType):
        return union(*[intersect_binary(t1, s2) for s2 in t2.types])
    elif isinstance(t1, ir.ListType) and isinstance(t2, ir.ListType):
        return ir.ListType(intersect_binary(t1.element_type, t2.element_type))
    elif isinstance(t1, ir.TupleType) and isinstance(t2, ir.TupleType):
        if len(t1.types) != len(t2.types):
            return Null
        else:
            return ir.TupleType(tuple([intersect(s1, s2) for s1, s2 in zip(t1.types, t2.types)]))
    else:
        return Null

def matches(t1: ir.Type, t2: ir.Type) -> bool:
    return is_subtype(t1, t2) or is_subtype(t2, t1)

def is_proper_subtype(t1: ir.Type, t2: ir.Type) -> bool:
    return t1 != t2 and is_subtype(t1, t2)

def is_subtype(t1: ir.Type, t2: ir.Type) -> bool:
    """
    Check if t1 is a subtype of t2.
    """
    if isinstance(t1, ir.ScalarType) and t2 == Any:
        # Any is the universal supertype of all scalar types.
        return True
    elif t1 == Null and isinstance(t2, ir.ScalarType):
        # Null is the universal subtype of all scalar types.
        return True
    elif isinstance(t1, ir.ScalarType) and isinstance(t2, ir.ScalarType):
        return t1 == t2 or any(is_subtype(s1, t2) for s1 in t1.super_types)
    elif isinstance(t1, ir.ListType) and isinstance(t2, ir.ListType):
        # Lists are covariant.
        return is_subtype(t1.element_type, t2.element_type)
    elif isinstance(t1, ir.TupleType) and isinstance(t2, ir.TupleType):
        # Tuples are covariant.
        return all(is_subtype(a1, a2) for a1, a2 in zip(t1.types, t2.types))
    elif isinstance(t1, ir.ScalarType) and isinstance(t2, ir.ListType):
        return is_subtype(t1, t2.element_type)
    elif isinstance(t1, ir.TupleType) and isinstance(t2, ir.ListType):
        # list[t] is a supertype of tuple types (t, ...).
        return all(is_subtype(a1, t2.element_type) for a1 in t1.types)
    elif isinstance(t1, ir.UnionType):
        # (t1 | ... | tn) <: t if ti <: t for all i.
        return all(is_subtype(a1, t2) for a1 in t1.types)
    elif isinstance(t2, ir.UnionType):
        # t <: (t1 | ... | tn) if t <: ti for some i.
        return any(is_subtype(t1, a2) for a2 in t2.types)
    else:
        return False


def is_decimal_subtype(t: ir.Type) -> bool:
    """ True if the type is a subtype of any decimal type. """
    if isinstance(t, ir.ScalarType):
        return is_decimal(t) or any(is_decimal_subtype(s) for s in t.super_types)
    return False


def decimal_supertype(t: ir.Type) -> Optional[ir.Type]:
    """ This t is a subtype of a decimal, lookup that decimal. """
    if isinstance(t, ir.ScalarType):
        if is_decimal(t):
            return t
        for s in t.super_types:
            x = decimal_supertype(s)
            if x:
                return x
    return None

def compute_highest_bound(bound: util.OrderedSet[ir.Type]) -> Optional[ir.Type]:
    """
    Compute the highest bound from a set of types.
    The highest bound is the union of all types that have no proper supertype in the bound.
    """
    if len(bound) == 1:
        return bound[0]
    if len(bound) == 0:
        return None

    # Include only the types that have no proper supertype in the bound.
    ts = []
    for t in bound:
        if not any(is_proper_subtype(t, t2) for t2 in bound):
            ts.append(t)

    if len(ts) == 0:
        return None
    elif len(ts) == 1:
        return ts[0]
    else:
        return ir.UnionType(util.ordered_set(*ts).frozen())

def compute_lowest_bound(bound: util.OrderedSet[ir.Type]) -> Optional[ir.Type]:
    """
    Compute the lowest bound from a set of types.
    The lowest bound is the union of all types that have no proper subtype in the bound.
    """
    if len(bound) == 1:
        return bound[0]
    if len(bound) == 0:
        return None

    # Include only the types that have no proper subtype in the bound.
    ts = []
    for t in bound:
        if not any(is_proper_subtype(t2, t) for t2 in bound):
            ts.append(t)

    if len(ts) == 0:
        return None
    elif len(ts) == 1:
        return ts[0]
    else:
        return ir.UnionType(util.ordered_set(*ts).frozen())
