from v0.relationalai.early_access.dsl.core.types.constrained.subtype import ValueSubtype
from v0.relationalai.early_access.dsl.core.types.unconstrained import UnconstrainedValueType, UnconstrainedNumericType

standard_value_types = {}

# Hash types
Hash = UnconstrainedValueType('Hash')
standard_value_types[Hash.display()] = Hash

# Boolean types
Boolean = UnconstrainedNumericType('Boolean')
standard_value_types[Boolean.display()] = Boolean

# Decimal types
#
Decimal = UnconstrainedNumericType('Decimal')
standard_value_types[Decimal.display()] = Decimal

UnsignedDecimal = ValueSubtype('UnsignedDecimal')
standard_value_types[UnsignedDecimal.display()] = UnsignedDecimal
with UnsignedDecimal:
    x = Decimal()
    x >= 0

PositiveDecimal = ValueSubtype('PositiveDecimal')
standard_value_types[PositiveDecimal.display()] = PositiveDecimal
with PositiveDecimal:
    x = UnsignedDecimal()
    x != 0

# Floating-point types
#
Float = UnconstrainedNumericType('Float')
standard_value_types[Float.display()] = Float
Double = UnconstrainedNumericType('Double')  # A float64 in Rel
standard_value_types[Double.display()] = Double

# Integer types
#
BigInteger = UnconstrainedNumericType('BigInteger')  # 128-bit integer
standard_value_types[BigInteger.display()] = BigInteger

BigUnsignedInteger = ValueSubtype('BigUnsignedInteger')
standard_value_types[BigUnsignedInteger.display()] = BigUnsignedInteger
with BigUnsignedInteger:
    x = BigInteger()
    x >= 0

BigPositiveInteger = ValueSubtype('BigPositiveInteger')
standard_value_types[BigPositiveInteger.display()] = BigPositiveInteger
with BigPositiveInteger:
    x = BigUnsignedInteger()
    x != 0

Integer = UnconstrainedNumericType('Integer')
standard_value_types[Integer.display()] = Integer

UnsignedInteger = ValueSubtype('UnsignedInteger')
standard_value_types[UnsignedInteger.display()] = UnsignedInteger
with UnsignedInteger:
    x = Integer()
    x >= 0

PositiveInteger = ValueSubtype('PositiveInteger')
standard_value_types[PositiveInteger.display()] = PositiveInteger
with PositiveInteger:
    x = UnsignedInteger()
    x != 0

# Date types
#
Date = UnconstrainedValueType('Date')
standard_value_types[Date.display()] = Date

# DateTime types
#
DateTime = UnconstrainedValueType('DateTime')
standard_value_types[DateTime.display()] = DateTime

RowId = UnconstrainedNumericType('RowId')
standard_value_types[RowId.display()] = RowId

# String types
#
String = UnconstrainedValueType('String')
standard_value_types[String.display()] = String

Any = UnconstrainedValueType('Any')
standard_value_types[Any.display()] = Any

Symbol = UnconstrainedValueType('Symbol')
standard_value_types[Symbol.display()] = Symbol
