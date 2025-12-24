from __future__ import annotations
from typing import Any, Iterable, List, Sequence

import pandas as pd

from v0.relationalai.clients.types import TransactionAsyncResponse
from v0.relationalai.clients.util import IdentityParser, ParseError
from v0.relationalai.dsl import safe_symbol
from v0.relationalai.errors import RAIException, RAIExceptionSet, RelQueryError

#-------------------------------------------------------------------------------
# Emitting
#-------------------------------------------------------------------------------

class Char(str):
    def __new__(cls, value):
        if value is None:
            raise ValueError("Char cannot be None")
        if len(value) != 1:
            raise ValueError("A Char must be a single character")
        return str.__new__(cls, value)

def emit_literal(v: Any):
    """Emit `v` as its equivalent literal representation in rel."""
    if isinstance(v, Char):
        sanitized = v.replace("'", "\\'")
        return f"'{sanitized}'"
    if isinstance(v, str):
        sanitized = v.replace('"', '\\"').replace("%", "\\%")
        return f'"{sanitized}"'
    if isinstance(v, tuple):
        return ", ".join(emit_literal(item) for item in v)
    return v

def emit_nested_relation(prefix: str, obj: dict|None = None, keys: Iterable[str]|None = None, raw = False) -> str:
    """Emit a set of defs encoding `obj` in GNF on `prefix`."""
    obj = obj or {}
    result = ""
    for k in keys or obj.keys():
        v = obj.get(k, None)
        if isinstance(v, dict):
            result += emit_nested_relation(f"{prefix}{safe_symbol(k)}, ", v)
        elif v is not None:
            result += f"def {prefix}{safe_symbol(k)}]: {emit_literal(v) if not raw else v}\n"
    return result

# SEE: REL:      https://docs.relational.ai/rel/ref/lexical-symbols#keywords
#      CORE REL: https://docs.google.com/document/d/12LUQdRed7P5EqQI1D7AYG4Q5gno9uKqy32i3kvAWPCA
RESERVED_WORDS = [
    "and",
    "as",
    "bound",
    "declare",
    "def",
    "else",
    "end",
    "entity",
    "exists",
    "false",
    "for",
    "forall",
    "from",
    "ic",
    "if",
    "iff",
    "implies",
    "in",
    "module",
    "namespace",
    "not",
    "or",
    "requires",
    "then",
    "true",
    "use",
    "where",
    "with",
    "xor"
]

def sanitize_identifier(name: str) -> str:
    """
    Return a string safe to use as a top level identifier in rel, such as a variable or relation name.

    Args:
        name (str): The input identifier string.

    Returns:
        str: The sanitized identifier string.
    """

    if not name:
        return name

    safe_name = ''.join(c if c.isalnum() else '_' for c in name)
    if safe_name[0].isdigit():
        safe_name = '_' + safe_name
    if  safe_name in RESERVED_WORDS:
        safe_name = safe_name + "_" # preferring the pythonic pattern of `from_` vs `_from`
    return safe_name

def to_fqn_relation_name(fqn: str) -> str:
    """
    Wrapper around `sanitize_identifier` which also lowers the string if no double quotes are present
    (for backwards compatibility), otherwise leaves it as is.

    Args:
        fqn (str): The fully qualified name ('db.schema.object').

    Returns:
        str: A string safe to use as a relation name in rel and matching the format in SF NA.
    """
    # In this case we do not want to upper case the non unique/double quoted parts of the identifier
    # This is required currently for for backwards compatibility
    parser = IdentityParser(fqn, force_upper_case = False)
    if not parser.is_complete:
        raise ParseError(f"Failed to parse {fqn}. Incomplete relation identifier. Must be fully qualified e.g. 'db.schema.object'.")
    if not parser.identity:
        raise ParseError(f"Failed to parse {fqn}. Empty identifier.")

    _name = parser.identity if parser.has_double_quoted_identifier else parser.identity.lower()
    return sanitize_identifier(_name)

#-------------------------------------------------------------------------------
# Result Handling
#-------------------------------------------------------------------------------

_known_problems: list[Any] = []
def ignore_known_problems(problems: Sequence[Any]):
    """Filter out issues already in `problems` when checking responses for rel problems."""
    global _known_problems
    _known_problems.clear()
    _known_problems.extend(problems)

def assert_no_problems(res: TransactionAsyncResponse):
    """Throw a vaguely-readable exception if rel problems were reported with the given transaction."""
    new_problems = []
    for problem in res.problems or []:
        if problem not in _known_problems:
            new_problems.append(problem)

    if new_problems:
        errs: List[RAIException] = [RelQueryError(problem) for problem in new_problems]
        if len(errs) > 1:
            raise RAIExceptionSet(errs) from None
        else:
            raise errs[0] from None

def maybe_scalarize(v):
    if getattr(v, "__len__", None) and len(v) == 1:
        return v[0]
    return v

def process_gnf_results(gnf: Sequence, *key_names: str):
    """Process GNF results into a nested object keyed by the key(s) in `key_names`"""
    assert len(key_names) > 0, "Must supply a name for the GNF key(s)"
    key_size = len(key_names)

    obj = {}

    for rel in gnf:
        sig = rel["relationId"].split("/")
        if sig[1] != ":output":
            continue

        table: pd.DataFrame = rel["table"].to_pandas()

        key_cols = table.columns[0:key_size]

        for _, row in table.iterrows():
            raw_keys = tuple(row[col] for col in key_cols)
            keys = maybe_scalarize(raw_keys)
            vals = [row[col] for col in table.columns[key_size:]]

            entry = obj.setdefault(keys, {k: v for k, v in zip(key_names, raw_keys)})

            cur = 4
            field = sig[cur - 2][1:]
            while len(sig) > cur and sig[cur][0] == ":":
                entry = entry.setdefault(field, {})
                field = sig[cur][1:]
                cur += 2
            entry[field] = maybe_scalarize(vals)

    return obj
