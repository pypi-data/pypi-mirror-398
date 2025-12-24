from datetime import datetime

from v0.relationalai.semantics.lqp import ir as lqp
from v0.relationalai.semantics.lqp.constructors import mk_abstraction, mk_value, mk_type, mk_primitive
from v0.relationalai.semantics.lqp.utils import lqp_hash

# Constructs a definition of the current datetime.
def mk_intrinsic_datetime_now(dt: datetime) -> lqp.Def:
    """Constructs a definition of the current datetime."""
    id = lqp_hash("__pyrel_lqp_intrinsic_datetime_now")
    out = lqp.Var(name="out", meta=None)
    out_type = mk_type(lqp.TypeName.DATETIME)
    now = mk_value(lqp.DateTimeValue(value=dt, meta=None))
    datetime_now = mk_abstraction(
        [(out, out_type)],
        mk_primitive("rel_primitive_eq", [out, now]),
    )

    return lqp.Def(
        name = lqp.RelationId(id=id, meta=None),
        body = datetime_now,
        attrs = [],
        meta = None,
    )
