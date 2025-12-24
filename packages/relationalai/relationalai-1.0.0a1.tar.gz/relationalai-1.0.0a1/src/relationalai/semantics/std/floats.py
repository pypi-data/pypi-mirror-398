from . import StringValue
from ..frontend.base import Library, Expression, Field, Value
from ..frontend.core import Float, String, Number
from decimal import Decimal as PyDecimal

# the front-end library object
library = Library("floats")

_parse_float = library.Relation("parse_float", [Field.input("value", String), Field("result", Float)])

def float(value: Value) -> Expression:
    return Float(value)

def parse_float(value: StringValue) -> Expression:
    return _parse_float(value)
