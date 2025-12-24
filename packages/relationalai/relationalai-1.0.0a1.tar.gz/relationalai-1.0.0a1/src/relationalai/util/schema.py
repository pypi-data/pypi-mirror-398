from collections import defaultdict
from functools import lru_cache
import json
from pathlib import Path
import re
import textwrap

from relationalai.util.error import warn
from ..config import Config
from ..config.connections.snowflake import SnowflakeConnection

# config = Config()
# conn = config.get_connection(SnowflakeConnection, name="snowflake")

# print(conn.get_session().sql("SELECT CURRENT_VERSION()").collect())

#------------------------------------------------------
# General
#------------------------------------------------------

CACHE_PATH = Path("build/cache/schemas.json")
CACHE = {}

def fetch(fqn: str) -> dict[str, str]:
    """
    Fetch Concept metadata for a fully-qualified table name.

    - Cache file may or may not exist.
    - Cache structure is assumed to be { "<db>.<schema>.<table>": { ...Concepts... } }
    - If the requested FQN is missing from the cache, fetch_snowflake is called and
      the result is stored back into the cache.
    """
    global CACHE
    database, schema, table = fqn.split(".")

    # Load or initialize cache
    if not CACHE and CACHE_PATH.exists():
        with CACHE_PATH.open("r", encoding="utf-8") as f:
            str_cache: dict[str, dict[str, str]] = json.load(f)
            CACHE = {k: {ck: cv for ck, cv in v.items()} for k, v in str_cache.items()}

    # If already cached, return it
    if fqn in CACHE:
        return CACHE[fqn]

    # Not in cache → fetch from Snowflake
    result = fetch_snowflake(database, schema, [table])
    if table not in result:
        return {}

    CACHE[fqn] = result[table]

    # Write updated cache
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_PATH.open("w", encoding="utf-8") as f:
        str_cache = {k: {ck: cv for ck, cv in v.items()} for k, v in CACHE.items()}
        json.dump(str_cache, f, indent=2)

    return CACHE[fqn]

#------------------------------------------------------
# Snowflake
#------------------------------------------------------

SUPPORTED_SNOWFLAKE_TYPES = [
    'CHAR', 'STRING', 'VARCHAR', 'BINARY', 'NUMBER', 'FLOAT', 'REAL',
    'BOOLEAN', 'DATE', 'FIXED', 'TEXT', 'TIME', 'TIMESTAMP_LTZ',
    'TIMESTAMP_NTZ', 'TIMESTAMP_TZ'
]

SFTypes = {
    "TEXT": "String",
    "FIXED": "Decimal",
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

def quoted(ident: str) -> str:
    return ident if SF_ID_REGEX.match(ident) or ident.startswith('"') else f'"{ident}"'

@lru_cache()
def get_provider():
    from ..shims.executor import get_provider
    return get_provider()

def fetch_snowflake(database:str, schema:str, table_names:list[str]) -> dict[str, dict[str, str]]:
    name_lookup = {name.upper(): name for name in table_names}

    tables = ", ".join(f"'{name.upper()}', '{name}'" for name in table_names)

    query = textwrap.dedent(f"""
        begin
            SHOW COLUMNS IN SCHEMA {quoted(database)}.{quoted(schema)};
            let r resultset := (
                select "table_name", "column_name", "data_type"
                from table(result_scan(-1)) as t
                where "table_name" in ({tables})
            );
            return table(r);
        end;
    """)

    # with debugging.span("fetch_schema", sql=query):
    try:
        columns = get_provider().sql(query)
    except Exception as e:
        columns = []
    assert isinstance(columns, list)

    unsupported_columns: dict[str, dict[str, str]] = defaultdict(dict)

    schemas: dict[str, dict[str, str]] = defaultdict(dict)
    for row in columns:
        table_name, column_name, data_type = row
        table_name = name_lookup.get(table_name, table_name)
        assert table_name is not None

        sf_type_info = json.loads(data_type)
        typ = sf_type_info.get("type")

        if typ not in SUPPORTED_SNOWFLAKE_TYPES:
            unsupported_columns[table_name][column_name] = typ
            continue

        if typ == "FIXED":
            concept_name = sf_numeric_to_type_str(column_name, sf_type_info)
        else:
            concept_name = SFTypes[typ]
        schemas[table_name][column_name] = concept_name

    for table_name, cols in unsupported_columns.items():
        col_str = ", ".join(f"{col}({typ})" for col, typ in cols.items())
        warn("Unsupported Column",
            f"The following columns in '{database}.{schema}.{table_name}' have unsupported types: {col_str}",
            [
                "These columns will not be accessible in your model.",
                "For the list of supported column types see: https://docs.relational.ai/api/cli/imports/stream/#supported-column-types"
            ])

    return schemas


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

def sf_numeric_to_type_str(column_name: str, sf_type_info: dict) -> str:
    """
    Computes the appropriate type to use for this column. This code reflects exactly
    the logic currently used by RAI's CDC implementation to ensure we map to the exact
    same number types.
    """
    if "scale" not in sf_type_info or "precision" not in sf_type_info:
        raise ValueError(
            f"Invalid definition for column '{column_name}': "
            "'scale' or 'precision' missing"
        )

    precision = sf_type_info["precision"]
    scale = sf_type_info["scale"]

    if scale > precision or scale < 0 or scale > 37:
        raise ValueError(
            f"Invalid numeric scale '{scale}' for column '{column_name}'"
        )

    if scale == 0:
        # Integers (load_csv only supports these two (and not 8/16/32 bit ints)
        bits = digits_to_bits(precision)
        # return Int128 if bits == 128 else Int64
        return f"Decimal(38,0)" if bits == 128 else f"Decimal(18,0)"

    return f"Decimal({precision},{scale})"
