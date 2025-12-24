from __future__ import annotations

from . import StringValue, IntegerValue, DateValue, DateTimeValue, math
from ..frontend.base import Aggregate, Library, Concept, NumberConcept, Expression, Field, Literal, TupleVariable, Variable, Value
from ..frontend.core import Any, Int128, Number, String, Integer, Date, DateTime, Hash

from typing import Union, Literal
import datetime as dt

# the front-end library object
library = Library("common")


_range = library.Relation("range", [Field.input("start", Integer), Field.input("stop", Integer), Field.input("step", Integer), Field("value", Integer)])

def range(*args: IntegerValue) -> Expression:
    """ Generate a range of integers.

    Supports range(stop), range(start, stop), range(start, stop, step).

    Start is inclusive and defaults to 0.
    Stop is exclusive.
    Step defaults to 1.
    """
    if len(args) == 1:
        start, stop, step = 0, args[0], 1
    elif len(args) == 2:
        start, stop, step = args[0], args[1], 1
    elif len(args) == 3:
        start, stop, step = args
    else:
        raise ValueError(f"range expects 1, 2, or 3 arguments, got {len(args)}")

    return _range(start, stop, step)

_hash = library.Relation("hash", [Field.input("args", Any, is_list=True), Field("hash", Hash)])
def hash(*args: Value) -> Expression:
    """ Compute a hash value for the given arguments. """
    return _hash(TupleVariable(args))

_uuid_to_string = library.Relation("uuid_to_string", [Field.input("uuid", Hash), Field("str", String)])
def uuid_to_string(uuid: Value) -> Expression:
    """ Convert a UUID (Hash) to its string representation. """
    return _uuid_to_string(uuid)