from __future__ import annotations
from typing import Optional

from . import metamodel as mm

class Relations:
    """ Container for built-in relations in a library. """
    def __init__(self):
        self.data = dict[str, mm.Relation]()

    def __getattr__(self, attr: str) -> mm.Relation:
        return self.data[attr]

    def __getitem__(self, attr: str) -> mm.Relation|None:
        return self.data.get(attr)

class CoreLibrary:
    """ Declare some core types and relations as class attributes for performant access. """
    # abstract types
    Any: mm.ScalarType
    AnyEntity: mm.ScalarType
    Numeric: mm.ScalarType
    TypeVar: mm.ScalarType
    EntityTypeVar: mm.ScalarType
    Number: mm.ScalarType
    ScaledNumber: mm.ScalarType
    # meta types
    Field: mm.ScalarType
    Relation: mm.ScalarType
    Type: mm.ScalarType
    Enum: mm.ScalarType
    # concrete primitive types
    Boolean: mm.ScalarType
    String: mm.ScalarType
    Date: mm.ScalarType
    DateTime: mm.ScalarType
    Float: mm.ScalarType
    # type aliases
    Integer: mm.NumberType
    DefaultNumber: mm.NumberType
    # binary operators
    plus: mm.Relation
    minus: mm.Relation
    mul: mm.Relation
    div: mm.Relation
    trunc_div: mm.Relation
    power: mm.Relation
    mod: mm.Relation
    # comparison operators
    eq: mm.Relation
    lt: mm.Relation
    lte: mm.Relation
    gt: mm.Relation
    gte: mm.Relation
    neq: mm.Relation
    # typer relations
    cast: mm.Relation

    def __getitem__(self, attr: str) -> mm.Relation:
        if attr in builtins._libraries["core"].data:
            return builtins._libraries["core"].data[attr]
        raise AttributeError(f"No built-in core attribute named '{attr}'.")

    def __iter__(self):
        yield from builtins._libraries["core"].data.values()

class Builtins:
    # Registered libraries by name
    _libraries = dict[str, Relations]()
    # Special case the core library for more performant access
    core = CoreLibrary()

    def register(self, library_name: str, relation: mm.Relation):
        """
            Register a built-in relation under the given library name.
        """
        if library_name not in self._libraries:
            self._libraries[library_name] = Relations()
        self._libraries[library_name].data[relation.name] = relation
        if library_name == "core":
            setattr(CoreLibrary, relation.name, relation)

    # Dynamic access to libraries (e.g., builtins.math.abs)
    def __getattr__(self, attr: str) -> Relations:
        if attr in self._libraries:
            return self._libraries[attr]
        raise AttributeError(f"No built-in library named '{attr}'.")


# Singleton instance of the builtins container
builtins = Builtins()

#------------------------------------------------------
# Helpers
#------------------------------------------------------
def is_function(r: mm.Relation) -> bool:
    """ True if the relation is a function (i.e., it has inputs and has a single output). """
    if len(r.fields) <= 1:
        return False
    # at least 2 fields, only 1 can be output
    output_fields = [f for f in r.fields if not f.input]
    return len(output_fields) == 1

def is_monotyped(r: mm.Relation) -> bool:
    if len(r.fields) == 0:
        return True

    # all types must be the same
    first = r.fields[0].type
    if any(f.type != first for f in r.fields):
        return False

    if r.overloads:
        # every overload must have all fields of the same type
        for overload in r.overloads:
            first = overload.types[0]
            if any(f_type != first for f_type in overload.types):
                return False
    return True

def is_placeholder(relation: mm.Relation) -> bool:
    """ Whether this relation is an unresolved placeholder that needs to be resolved. """
    return isinstance(relation, mm.UnresolvedRelation)

def is_abstract(t: mm.Type) -> bool:
    """ True if the type is abstract, or a collection or union containing an abstract type.
    """
    if isinstance(t, mm.ScalarType):
        return t in [
            builtins.core.Any,
            builtins.core.AnyEntity,
            builtins.core.Number,
            builtins.core.ScaledNumber,
            builtins.core.Numeric,
            builtins.core.TypeVar,
            builtins.core.EntityTypeVar
        ]
    elif isinstance(t, mm.ListType):
        return is_abstract(t.element_type)
    elif isinstance(t, mm.UnionType):
        return any(is_abstract(t) for t in t.types)
    else:
        return False

def is_type_var(t: mm.Type) -> bool:
    return t in [
        builtins.core.TypeVar,
        builtins.core.EntityTypeVar,
    ]

def is_concrete(t: mm.Type) -> bool:
    return not is_abstract(t)

def is_number(t: mm.Type) -> bool:
    """ True if the type is a number type. """
    # note that builtins.core.Number is a ScalarType that represents "any number type",
    # whereas concrete numbers are represented by NumberType instances.
    return isinstance(t, mm.NumberType) or t == builtins.core.Number

def is_numeric(t: mm.Type) -> bool:
    """ True if the type is numeric (Number or Float). """
    # TODO - we could check by supertype instead, but that would be slower
    return t == builtins.core.Numeric or t == builtins.core.Float or is_number(t)

def is_primitive(t: mm.Type) -> bool:
    """
        True if the type is a primitive type (boolean, string, date, datetime, float, number).
    """
    return t in [
        CoreLibrary.Boolean,
        CoreLibrary.String,
        CoreLibrary.Date,
        CoreLibrary.DateTime,
        CoreLibrary.Float
    ] or is_number(t)

def is_value_type(type: mm.Type):
    """ True if the type extends a primitive type (i.e., is a value type). """
    return isinstance(type, mm.ScalarType) and not is_primitive(type) and get_primitive_supertype(type) is not None

def get_primitive_supertype(type: mm.Type) -> Optional[mm.Type]:
    """ Search the type hierarchy for a primitive supertype. """
    if isinstance(type, mm.ScalarType):
        if is_primitive(type):
            return type
        # walk the hierarchy to find a base primitive
        for parent in type.super_types:
            if found := get_primitive_supertype(parent):
                return found
    if isinstance(type, mm.UnionType):
        for t in type.types:
            if found := get_primitive_supertype(t):
                return found
    return None

def get_number_supertype(type: mm.Type) -> Optional[mm.NumberType]:
    x = get_primitive_supertype(type)
    if isinstance(x, mm.NumberType):
        return x
    return None

def extends(type: mm.Type, supertype: mm.Type) -> bool:
    """ True if `type` extends `supertype` in the type hierarchy. """
    if type == supertype:
        return True
    if isinstance(type, mm.ScalarType):
        for parent in type.super_types:
            if extends(parent, supertype):
                return True
    return False
