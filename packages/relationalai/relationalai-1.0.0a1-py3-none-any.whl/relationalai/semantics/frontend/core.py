from __future__ import annotations

import re
from .base import CoreLibrary as Core, Concept, NumberConcept, Field as dslField, Relationship
from ..metamodel.builtins import builtins as b
from ..metamodel import metamodel as mm
from typing import cast


#------------------------------------------------------
# Helpers
#------------------------------------------------------
def make_overloads(types: list[Concept], arity: int) -> list[list[Concept]]:
    """ Helper to create a list of overloads with this arity, for each of these types. """
    return list(map(lambda x: [x] * arity, types))

def register_core_alias(name: str, concept: Concept|Relationship):
    """ Register the relation compiled from this concept in buitins.core with a name that is
    different from its concept name. This is useful for operators whose name is not a valid
    python identifier (e.g. "+", "-", etc) so that we can use b.core.plus instead. Also used
    for type aliases like Integer for Number(38,0).
    """
    b.core.__setattr__(name, Core._compiler.to_relation(concept))

#------------------------------------------------------
# Abstract Types
#------------------------------------------------------

class AnyNumber(Concept):
    """Abstract Number concept that can produce concrete NumberConcepts
       with specific precision and scale."""

    # cache the concrete number concepts created for reuse
    _concrete_numbers = dict[str, NumberConcept]()

    def __init__(self, super_type: Concept):
        super().__init__("Number", extends=[super_type], identify_by={}, model=Core)
        AnyNumber._register(self)

    def size(self, precision:int, scale:int) -> NumberConcept:
        """ Get or create a NumberConcept type with the given precision and scale. """
        key = f"{precision},{scale}"
        if key not in self._concrete_numbers:
            nc = NumberConcept(f"Number({precision},{scale})", precision, scale, model=self._model)
            AnyNumber._register(nc)
            self._concrete_numbers[key] = nc
        return self._concrete_numbers[key]

    def parse(self, type_str: str) -> NumberConcept:
        """
            Get or create a new number type with precision/scale based on parsing the type
            string as a Number(precision,scale) pattern.
        """
        pattern = r'^(?:Number|Decimal)\(\s*([0-9]+)\s*,\s*([0-9]+)\s*\)$'
        match = re.search(pattern, type_str)
        if match:
            precision, scale = match.group(1), match.group(2)
            return self.size(int(precision), int(scale))
        raise ValueError(f"Invalid Number type name: {type_str}.")

    @classmethod
    def _register(cls, concept: Concept):
        """ Register the concept in the core library and as a builtin. """
        Core.concepts.append(concept)
        Core.concept_index[concept._name] = concept
        Core._register_builtin(concept)

# Any type at all
Any = Core.Type("Any")
# Any minus value types (aka nominal types)
AnyEntity = Core.Type("AnyEntity")
# Any numeric type (Number or Float)
Numeric = Core.Type("Numeric")
# Singleton instance of the AnyNumber concept
Number = AnyNumber(Numeric)
# Represents a number whose exact type will be scaled depending on the input types.
ScaledNumber = Core.Type("ScaledNumber", super_types=[Number])

# A generic type variable that represents any type in a relation, as long as it is consitent
# across all uses within that relation. This allows us to create monotyped overloads, e.g.
# Person < Person and number < number are ok, but Person < Car or number < float are not.
TypeVar = Core.Type("TypeVar")
# Same as TypeVar, but only for entity types (i.e. not value types).
EntityTypeVar = Core.Type("EntityTypeVar")


#------------------------------------------------------
# Meta Types
#------------------------------------------------------
Field = Core.Type("Field")
Relation = Core.Type("Relation")
Type = Core.Type("Type", super_types=[Relation])
Enum = Core.Type("Enum")

#------------------------------------------------------
# Concrete Primitive Types
#------------------------------------------------------
Boolean = Core.Type("Boolean")
String = Core.Type("String")
Date = Core.Type("Date")
DateTime = Core.Type("DateTime")
Float = Core.Type("Float", super_types=[Numeric])
Hash = Core.Type("Hash") # TODO: we shouldn't really need this?

#------------------------------------------------------
# Aliases for Types
#------------------------------------------------------
DefaultNumber = Number.size(38, 14) # register default Number type
register_core_alias("DefaultNumber", DefaultNumber)
Core.concept_index["DefaultNumber"] = DefaultNumber

Integer = Number.size(38, 0)
register_core_alias("Integer", Integer)
Core.concept_index["Integer"] = Integer

Int = Integer
Core.concept_index["Int"] = Int
Int64 = Integer
Core.concept_index["Int64"] = Int64
Int128 = Integer
Core.concept_index["Int128"] = Int128
Decimal = Number
Core.concept_index["Decimal"] = Decimal
Bool = Boolean
Core.concept_index["Bool"] = Bool

#------------------------------------------------------
# Binary Operators
#------------------------------------------------------
def make_bin_op(name: str, alias: str, overloads=None) -> Relationship:
    """ Helper to create a binary operator relation in the core library. """
    relationship = Core.Relation(name,
        [dslField.input("x", Numeric), dslField.input("y", Numeric), dslField("result", Numeric)],
        overloads=make_overloads([Number, Float], 3) if overloads is None else overloads)
    register_core_alias(alias, relationship)
    return relationship

plus = make_bin_op("+", "plus")
minus = make_bin_op("-", "minus")
mul = make_bin_op("*", "mul", overloads=([Number, Number, ScaledNumber], [Float, Float, Float]))
div = make_bin_op("/", "div", overloads=([Number, Number, ScaledNumber], [Float, Float, Float]))
trunc_div = make_bin_op("//", "trunc_div")
power = make_bin_op("^", "power")
mod = make_bin_op("%", "mod")

#------------------------------------------------------
# Comparison Operators
#------------------------------------------------------
def make_compare_op(name: str, alias: str) -> Relationship:
    """ Helper to create a comparison operator relation in the core library. """
    relationship = Core.Relation(name, [dslField.input("left", TypeVar), dslField.input("right", TypeVar)])
        # overloads=make_overloads([Number, Float, Boolean, String, Date, DateTime], 2))
    register_core_alias(alias, relationship)
    return relationship

eq = make_compare_op("=", "eq")
lt = make_compare_op("<", "lt")
lte = make_compare_op("<=", "lte")
gt = make_compare_op(">", "gt")
gte = make_compare_op(">=", "gte")
neq = make_compare_op("!=", "neq")

#------------------------------------------------------
# Typer-related Relations
#------------------------------------------------------
cast = Core.Relation("cast", [dslField.input("to_type", Type), dslField.input("source", Any), dslField("target", Any)])

#------------------------------------------------------
# Constraint Relations
#------------------------------------------------------

Core.Relation("unique", [dslField.input("fields", Any, is_list=True)])


#------------------------------------------------------
# Downstream annotations
#------------------------------------------------------

Core.Relation("output_value_is_key", [dslField.input("is_key", Integer)])