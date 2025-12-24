from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
import json
import re
import textwrap
from v0.relationalai.clients.util import IdentityParser
from v0.relationalai.semantics.metamodel import types
from v0.relationalai.semantics.metamodel.util import OrderedSet, ordered_set
from v0.relationalai.semantics.rel.rel_utils import sanitize_identifier
from . import internal as b, annotations as anns
from v0.relationalai import debugging
from v0.relationalai.errors import UnsupportedColumnTypesWarning
from snowflake.snowpark.context import get_active_session
from typing import ClassVar, Optional

#--------------------------------------------------
# Iceberg Configuration
#--------------------------------------------------
@dataclass
class IcebergConfig:
    """Configuration for exporting to Iceberg tables."""
    external_volume: str | None = None
    default: ClassVar[Optional["IcebergConfig"]]

IcebergConfig.default = IcebergConfig()
#--------------------------------------------------
# Helpers
#--------------------------------------------------

def schema_dict_to_fields(schema: dict[str, str|b.Concept]) -> list[b.Field]:
    fields = []
    for name, type in schema.items():
        if isinstance(type, str):
            fields.append(b.Field(name=name, type_str=type))
        elif isinstance(type, b.Concept):
            fields.append(b.Field(name=name, type_str=type._name, type=type))
    return fields

#--------------------------------------------------
# Constants
#--------------------------------------------------

# List of supported Snowflake column types. In V0 this comes from the app.get_supported_column_types() function.
# We can't use that function in V1 since it would add a dependency on the app, so we hardcode the list here.
SUPPORTED_SNOWFLAKE_TYPES = [
    'CHAR', 'STRING', 'VARCHAR', 'BINARY', 'NUMBER', 'FLOAT', 'REAL',
    'BOOLEAN', 'DATE', 'FIXED', 'TEXT', 'TIME', 'TIMESTAMP_LTZ',
    'TIMESTAMP_NTZ', 'TIMESTAMP_TZ'
]

#--------------------------------------------------
# Globals
#--------------------------------------------------

_session = None
def get_session():
    global _session
    if not _session:
        try:
            _session = get_active_session()
        except Exception:
            from v0.relationalai import Resources
            from v0.relationalai.clients.snowflake import Resources as SnowflakeResources
            # TODO: we need a better way to handle global config

            # using the resource constructor to differentiate between direct access and
            # regular resource as this impacts the construction of the session.
            resources = Resources()
            assert isinstance(resources, SnowflakeResources), "Can only retrieve session from Snowflake resources"
            _session = resources.get_sf_session()
    return _session

def is_direct_access_enabled():
    from v0.relationalai import Resources
    resources = Resources()
    if hasattr(resources, "is_direct_access_enabled"):
        return resources.is_direct_access_enabled()
    return False


#--------------------------------------------------
# Snowflake sources
#--------------------------------------------------

SFTypes = {
    "TEXT": "String",
    "FIXED": "Number",
    "DATE": "Date",
    "TIME": "DateTime",
    "TIMESTAMP": "DateTime",
    "TIMESTAMP_LTZ": "DateTime",
    "TIMESTAMP_TZ": "DateTime",
    "TIMESTAMP_NTZ": "DateTime",
    "FLOAT": "Float",
    "REAL": "Float",
    "BOOLEAN": "Bool",
}

SF_ID_REGEX = re.compile(r'^[A-Za-z_][A-Za-z0-9_$]*$')
def quoted(ident:str):
    if SF_ID_REGEX.match(ident) or ident[0] == '"':
        return ident
    return f'"{ident}"'

@dataclass
class TableInfo:
    source:Table|None
    fields:list[b.Field]
    raw_columns:list[dict]

class SchemaInfo:
    def __init__(self, database:str, schema:str) -> None:
        self.database = database
        self.schema = schema
        self.tables = defaultdict(lambda: TableInfo(None, [], []))
        self.fetched = set()

    def fetch(self):
        session = get_session()
        table_names = [name for name in self.tables.keys() if name.upper() not in self.fetched]
        self.fetched.update([x.upper() for x in table_names])
        name_lookup = {x.upper(): x for x in table_names}
        tables = ", ".join([f"'{x.upper()}', '{x}'" for x in table_names])
        supported_types_list = ", ".join([f"'{t}'" for t in SUPPORTED_SNOWFLAKE_TYPES])

        query = textwrap.dedent(f"""
            begin
                SHOW COLUMNS IN SCHEMA {quoted(self.database)}.{quoted(self.schema)};
                let r resultset := (select "table_name", "column_name", "data_type",
                                    CASE
                                        WHEN PARSE_JSON("data_type"):"type" in ({supported_types_list}) THEN TRUE
                                        ELSE FALSE
                                    END as "supported_type"
                                    from table(result_scan(-1)) as t
                                    where "table_name" in ({tables}));
                return table(r);
            end;
        """)
        with debugging.span("fetch_schema", sql=query):
            columns = session.sql(query).collect()

        # Collect unsupported columns for warning
        unsupported_columns = {}

        for row in columns:
            table_name, column_name, data_type, supported_type = row
            table_name = name_lookup.get(table_name, table_name)

            # Skip columns with unsupported types
            if not supported_type:
                if table_name not in unsupported_columns:
                    unsupported_columns[table_name] = {}
                unsupported_columns[table_name][column_name] = data_type
                continue

            info = self.tables[table_name]
            sf_type_info = json.loads(data_type)
            typ = sf_type_info.get("type")
            if typ in SUPPORTED_SNOWFLAKE_TYPES:
                if typ == "FIXED":
                    type_str = self.sf_numeric_to_type_str(column_name, sf_type_info)
                else:
                    type_str = SFTypes[typ]
                info.fields.append(b.Field(name=column_name, type_str=type_str))
                info.raw_columns.append(row.as_dict())
            else:
                # TODO - raise a warning
                pass

        # Show warning for unsupported columns
        if unsupported_columns:
            UnsupportedColumnTypesWarning(unsupported_columns)

    def sf_numeric_to_type_str(self, column_name, sf_type_info):
        """
        Computes the appropriate type to use for this column. This code reflects exactly
        the logic currently used by RAI's CDC implementation to ensure we map to the exact
        same number types.
        """
        if "scale" not in sf_type_info or "precision" not in sf_type_info:
            raise ValueError(f"Invalid definition for column '{column_name}': 'scale' or 'precision' missing")

        precision = sf_type_info.get("precision")
        scale = sf_type_info.get("scale")

        if scale > precision or scale < 0 or scale > 37:
            raise ValueError(f"Invalid numeric scale '{scale}' for column '{column_name}'")

        if scale == 0:
            # Integers (load_csv only supports these two (and not 8/16/32 bit ints)
            # RAI int sizes are 8, 16, 32, 64, or 128; 64 by default
            # SF precision is expressed in base 10 digits, max 38
            # Max positive int value: 127, 32767, 2147483647, 9223372036854775807, 170141183460469231731687303715884105727
            # Base 10 digits fully covered: 2, 4, 9, 18, 38
            bits = types.digits_to_bits(precision)
            return "Int128" if bits == 128 else "Int64"
        else:
            return f"Decimal({precision},{scale})"

class Table():
    _schemas:dict[tuple[str, str], SchemaInfo] = {}
    _used_sources:OrderedSet[Table] = ordered_set()

    def __init__(self, fqn:str, cols:list[str]|None=None, schema:dict[str, str|b.Concept]|None=None, config: IcebergConfig|None=None) -> None:
        self._fqn = fqn
        parser = IdentityParser(fqn, require_all_parts=True)
        self._database, self._schema, self._table, self._fqn = parser.to_list()
        self._inited = False
        self._concept = b.Concept(self._fqn, extends=[b.Concept.builtins["RowId"]])
        b.Concept.globals[self._fqn.lower()] = self._concept
        self._ref = self._concept.ref("row_id")
        self._cols = {}
        self._col_names = cols
        self._iceberg_config = config
        self._is_iceberg = config is not None
        info = self._schemas.get((self._database, self._schema))
        if not info:
            info = self._schemas[(self._database, self._schema)] = SchemaInfo(self._database, self._schema)
        if schema:
            info.fetched.add(self._table)
            info.tables[self._table] = TableInfo(self, schema_dict_to_fields(schema), [])
        info.tables[self._table].source = self

    def _lazy_init(self):
        if self._inited:
            return
        self._inited = True
        schema_info = self._schemas[(self._database, self._schema)]
        if self._table not in schema_info.fetched:
            schema_info.fetch()
        table_info = schema_info.tables[self._table]
        self._rel = b.Relationship(self._fqn, fields=[b.Field(name="RowId", type_str=self._fqn, type=self._concept)] + table_info.fields)
        self._rel.annotate(anns.external).annotate(anns.from_cdc)

    def __getattr__(self, name: str):
        if name.startswith("_"):
            return super().__getattribute__(name)
        if self._col_names is not None and name not in self._col_names:
            raise ValueError(f"Column {name} not found in {self._fqn}")
        if name.lower() not in self._cols:
            self._cols[name.lower()] = Column(self, name)
        return self._cols[name.lower()]

    def into(self, concept:b.Concept, keys:list[Column]=[]):
        self._lazy_init()
        key_dict = {sanitize_identifier(k._column_name.lower()): k for k in keys}

        # if no keys are defined but the concept has a reference scheme, try to match
        # reference schemes with column fields by name
        if not keys and concept._reference_schemes:
            # do not modify the default argument, create a new array
            keys = []
            sanitized_fields = [sanitize_identifier(n.lower()) for n in self._rel._field_names]
            for scheme in concept._reference_schemes:
                # if all keys in a scheme map to columns, then use it
                if all(k._name in sanitized_fields for k in scheme):
                    for k in scheme:
                        key = Column(self, k._name)
                        keys.append(key)
                        key_dict[k._name] = key
                    break
        # TODO: this is correct, but the rel backend does the wrong thing with it
        # me = concept.new(**key_dict)
        # items = [me]
        # for field in self._rel._fields[1:]:
        #     field_rel = getattr(concept, field.name.lower())
        #     if sanitize_identifier(field.name.lower()) not in key_dict:
        #         items.append(field_rel(me, getattr(self, field.name)))
        # b.where(me).define(*items)

        # this is much less efficient than above

        if keys:
            me = concept.new(**key_dict)
            b.define(me)
        else:
            me = self._rel._field_refs[0]
            b.where(self).define(concept(me))
        # All the fields are treated as properties
        for field in self._rel._fields[1:]:
            field_name = sanitize_identifier(field.name.lower())
            if field_name not in key_dict:
                r = b.Property(
                    f"{{{concept}}} has {{{field_name}:{field.type_str}}}",
                    parent=concept,
                    short_name=field_name,
                    model=self._rel._model
                )
                setattr(concept, field_name, r)
                relationship = getattr(concept, field_name)
                table_name = getattr(self, field.name)
                update = relationship(me, table_name)
                b.define(update)

    def _to_type(self) -> b.Concept:
        return self._concept

    def _to_keys(self) -> list[b.Ref]:
        self._lazy_init()
        return [self._rel._field_refs[0]]

    def _compile_lookup(self, compiler:b.Compiler, ctx:b.CompilerContext):
        self._lazy_init()
        Table._used_sources.add(self)
        compiler.lookup(self._rel, ctx)
        return compiler.lookup(b.RelationshipFieldRef(None, self._rel, 0), ctx)

class Column(b.Producer):
    def __init__(self, source:Table, column_name:str) -> None:
        super().__init__(None)
        self._column_name = column_name
        self._source = source

    def _to_keys(self) -> list[b.Ref]:
        return self._source._to_keys()

    def _compile_lookup(self, compiler:b.Compiler, ctx:b.CompilerContext):
        compiler.lookup(self._source, ctx)
        for ix, field in enumerate(self._source._rel._field_refs):
            assert field._name is not None
            if field._name.lower() == self._column_name.lower():
                return compiler.lookup(b.RelationshipFieldRef(None, self._source._rel, ix), ctx)
        raise ValueError(f"Column {self._column_name} not found in {self._source._fqn}")
