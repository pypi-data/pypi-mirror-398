from v0.relationalai.early_access.dsl.core.namespaces import Namespace
from v0.relationalai.early_access.dsl.core.relations import RelationSignature, ExternalRelation
from v0.relationalai.early_access.dsl.core.types import Type
from v0.relationalai.early_access.dsl.core.types.standard import DateTime, Date, PositiveInteger, Decimal, String, Symbol, \
    Any, Integer

#=
# StdLib.
#=

standard_relations = {}

parse_date_name = "parse_date"
parse_date = ExternalRelation(Namespace.top, parse_date_name, RelationSignature(String, String, Date))
standard_relations[parse_date_name] = parse_date

parse_datetime_name = "parse_datetime"
parse_datetime = ExternalRelation(Namespace.top, parse_datetime_name, RelationSignature(String, String, DateTime))
standard_relations[parse_datetime_name] = parse_datetime

parse_decimal_name = "parse_decimal"
parse_decimal = ExternalRelation(Namespace.top, parse_decimal_name, RelationSignature(PositiveInteger, PositiveInteger, String, Decimal))
standard_relations[parse_decimal_name] = parse_decimal

power_name = "power"
power = ExternalRelation(Namespace.top, power_name, RelationSignature(Integer, Integer, Integer))
standard_relations[power_name] = power

unpack_name = "unpack"
def unpack(*sig: Type):
    return ExternalRelation(Namespace.top, unpack_name, RelationSignature(*sig))
standard_relations[unpack_name] = unpack

decimal_ctor_name = "decimal"
new_decimal = ExternalRelation(Namespace.top, decimal_ctor_name, RelationSignature(Integer, Integer, Integer, Decimal))
standard_relations[decimal_ctor_name] = new_decimal

#=
# Rel Mirror.
#=

mirror_lower_name = "mirror_lower"
mirror_lower_rel_name = "::std::mirror::lower"
mirror_lower = ExternalRelation(Namespace.top, mirror_lower_rel_name, RelationSignature(Symbol, Any))
standard_relations[mirror_lower_rel_name] = mirror_lower
