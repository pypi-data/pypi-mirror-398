from decimal import Decimal as PyDecimal
import datetime as dt
from typing import Any, Union

from v0.relationalai.semantics.internal import internal as b

_String = Union[b.Producer, str]
_Integer = Union[b.Producer, int]
_Date = Union[b.Producer, dt.date]
_DateTime = Union[b.Producer, dt.datetime]
_Number = Union[b.Producer, float, int, PyDecimal]

def _make_expr(op: str, *args: Any) -> b.Expression:
    return b.Expression(b.Relationship.builtins[op], *args)