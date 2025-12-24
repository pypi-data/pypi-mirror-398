from __future__ import annotations
import csv
from datetime import date, datetime
from typing import Any, cast

import numpy
import pandas

from v0.relationalai.clients.types import ImportSource, ImportSourceFile
from v0.relationalai.clients.client import ResourcesBase
from v0.relationalai.dsl import Graph, RelationRef, build, tag
from v0.relationalai.loaders.loader import TYPE_TO_REL_SCHEMA, Loader, compute_file_hash, compute_str_hash
from v0.relationalai.rel_utils import Char, assert_no_problems, emit_nested_relation
from v0.relationalai.loaders.types import Schema, Syntax
from v0.relationalai.metamodel import ActionType, Builtins, Var
from v0.relationalai.rel_emitter import sanitize
from v0.relationalai.std import rel


def df_type(df_type_name):
    if df_type_name == "bool":
        type = Builtins.Bool
    elif df_type_name == "int64":
        type = Builtins.Number
    elif df_type_name == "float64":
        type = Builtins.Number
    else:
        type = Builtins.String
    return type

class ExternalRow:
    def __init__(self, data, columns):
        self._data = data
        self._columns = columns

    def __getitem__(self, index):
        if isinstance(index, str):
            return getattr(self, index)
        return self._data[index]

    def __getattr__(self, name):
        if name in self._columns:
            return self._data[self._columns.index(name)]
        return object.__getattribute__(self, name)

# See https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
# for keyword arg docs.
def load_file(graph:Graph, csv_file, **kwargs):
    df = pandas.read_csv(csv_file, **kwargs)

    # create subqueries for each column that consist of a data object
    # and a bind for the column relation, also create a data ref
    # add a range for the id
    # when a dataref is used, it should add a get for the column relation
    # the rest just works?

    index = getattr(rel, sanitize(csv_file))
    tag(index, Builtins.Type)

    with graph.scope():
        index.add(rel.range(0, len(df), 1))

    id = Var(type=Builtins.Number)
    items = []
    for col in df.columns:
        sub = df[[col]]
        col_type = df_type(df[col].dtype)
        with graph.scope(dynamic=True):
            # By setting Builtins.RawData on the task, we're telling the denester to not
            # put a reference to the parent scope in this one
            graph._stack.active()._task.parents.append(Builtins.RawData)
            v1 = []
            v2 = []
            for (i, v) in sub.itertuples():
                if v is not None and v != "" and v is not False and (isinstance(v,str) or isinstance(v, date) or isinstance(v, datetime) or not numpy.isnan(v)):
                    v1.append(i)
                    v2.append(v)

            v1_var = Var(type=Builtins.Number)
            v2_var = Var(name=col, type=col_type)
            graph._action(
                build.relation_action(ActionType.Get, Builtins.RawData, [Var(value=v1), Var(value=v2), v1_var, v2_var])
            )
            temp = build.relation(sanitize(csv_file) + "_" + col, 2)
            temp.parents.append(Builtins.Property)
            graph._action(
                build.relation_action(ActionType.Bind, temp, [v1_var, v2_var])
            )
            usage_var = Var(name=col, type=col_type)
            items.append(RelationRef(graph, temp, [id, usage_var]))
    graph._action(
        build.relation_action(ActionType.Get, index._rel, [id])
    )
    return ExternalRow(items, [c for c in df.columns])

class CSVLoader(Loader):
    """Load CSV files and URLs in RAI DB using `load_csv`."""
    type = "csv"

    def load(self, provider: ResourcesBase, model: str, source: ImportSource, *, schema: Schema|None = None, syntax: Syntax|None = None, integration: dict|None = None):
        from railib import api
        assert isinstance(source, ImportSourceFile), "CSV Loader can only load from files and URLs, not {type(source).__name__}"
        schema = schema or {}
        syntax = syntax or {}

        id = compute_str_hash(source.raw_path)
        prefix = f"""def config[:path]: raw"{source.raw_path}" """
        inputs = None

        if not source.is_url():
            with open(source.raw_path, "r") as csv_file:
                data = csv_file.read()

            id = compute_file_hash(source.raw_path)
            prefix = "def config[:data]: data"
            inputs = {"data": data}

        relation = sanitize(source.name)

        for key in ["delim", "quotechar", "escapechar"]:
            if syntax.get(key, None) and not isinstance(syntax[key], Char):
                syntax[key] = Char(syntax[key])

        q = f"""
        declare {relation}
        def delete[:{relation}]: {relation}
        def delete[:__resource, k, "{relation}"]: __resource[k, "{relation}"]

        {prefix}
        {emit_nested_relation("config[:syntax, ", cast(dict, syntax), api._syntax_options)}
        {emit_nested_relation("config[:schema, ", {col: TYPE_TO_REL_SCHEMA.get(type, "string") for col, type in schema.items()})}
        {emit_nested_relation("config[:integration, ", integration) if integration else ""}
        {emit_nested_relation("insert[:__resource, ", {
        "id": (relation, id),
        "type": (relation, self.type),
        "name": (relation, source.name)
        })}
        def insert[:__resource, :schema]: ("{relation}", config[:schema])
        def insert[:{relation}]: load_csv[config]
        """
        q = "\n".join(line.strip() for line in q.splitlines())
        res = provider.exec_raw(model, provider.get_default_engine_name(), q, readonly=False, inputs=inputs)
        assert_no_problems(res)

    SAMPLE_LINES_COUNT = 100

    @classmethod
    def guess_syntax(cls, path: str) -> Syntax:
        sample_lines = []
        with open(path, "r") as file:
            try:
                for _ in range(cls.SAMPLE_LINES_COUNT):
                    sample_lines.append(next(file))
            except StopIteration:
                pass

        sample = "".join(sample_lines)
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample)

        # Unused but available: quoting, doublequote, lineterminator, skipinitialspace,
        return {
            "delim": dialect.delimiter,
            "quotechar": dialect.quotechar,
            "escapechar": dialect.escapechar,
            "header_row": 1 if sniffer.has_header(sample) else -1
        }

    @classmethod
    def guess_schema(cls, path: str, syntax: Syntax) -> tuple[Schema, pandas.DataFrame]:
        """Guess the schema by reading a chunk of the file."""
        # @TODO: pick an appropriate magic number of rows to consider for type information.

        pandas_syntax_args:dict[str, Any] = {
            "delimiter": syntax.get("delim", None),
            "quotechar": syntax.get("quotechar", None),
            "escapechar": syntax.get("escapechar", None),

            # @NOTE: For some reason the sniffer always wants \r\n even when its only \n, and pandas (like rel) requires single char line terminators
            # "lineterminator": dialect.lineterminator,
            # @NOTE: These can't be passed to load_csv so there's not much point helping pandas with them.
            # "doublequote": dialect.doublequote,
            # "quoting": dialect.quoting,
            # "skipinitialspace": dialect.skipinitialspace,
        }

        chunk = pandas.read_csv(path, nrows=cls.SAMPLE_LINES_COUNT, **pandas_syntax_args)
        chunk = chunk.rename(columns={k: k.strip() for k in chunk.columns})
        inferred_schema = Schema()
        for col in chunk.columns:
            inferred_schema[col] = df_type(chunk[col].dtype)

        return (inferred_schema, chunk)

CSVLoader.register_for_extensions(".csv", ".tsv")
