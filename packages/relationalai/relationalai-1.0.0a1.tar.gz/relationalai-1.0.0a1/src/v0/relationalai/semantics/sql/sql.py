"""
A simple metamodel for SQL.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from io import StringIO
from typing import Optional, Union, Tuple, Any, Sequence
from v0.relationalai.semantics.metamodel.util import Printer as BasePrinter
import json

@dataclass(frozen=True)
class Node:
    def __str__(self):
        return to_string(self)

@dataclass(frozen=True)
class Program(Node):
    """ The root node of the SQL program. """
    statements: list[Node]

#-------------------------------------------------
# Table
#-------------------------------------------------

@dataclass(frozen=True)
class Column(Node):
    name: str
    type: str

@dataclass(frozen=True)
class Table(Node):
    name: str
    columns: list[Column]

#-------------------------------------------------
# Statements
#-------------------------------------------------

@dataclass(frozen=True)
class CreateTable(Node):
    table: Table
    if_not_exists: bool = False

@dataclass(frozen=True)
class CreateDynamicTable(Node):
    name: str
    query: Union[list[Select], CTE]
    target_lag: str
    warehouse: str

@dataclass(frozen=True)
class CreateView(Node):
    name: str
    query: Union[list[Select], CTE]

@dataclass(frozen=True)
class CreateFunction(Node):
    name: str
    inputs: list[Column]
    return_type: str
    body: str
    language: str = "PYTHON"
    runtime_version: str = "3.11"
    handler: str = "compute"
    packages: Optional[list[str]] = None

@dataclass(frozen=True)
class Insert(Node):
    table: str
    columns: list[str]
    values: list[Tuple[Any, ...]]
    query: Optional[Union[Select, CTE]] = None

@dataclass(frozen=True)
class Update(Node):
    table: str
    set: list[UpdateSet]
    where: Optional[Where]

@dataclass(frozen=True)
class UpdateSet(Node):
    name: str
    expression: str

@dataclass(frozen=True)
class Select(Node):
    distinct: bool
    vars: Optional[Sequence[Union[VarRef, RowNumberVar, int]]] = None
    froms: Optional[Union[list[From], Select]] = None
    where: Optional[Where] = None
    joins: Optional[list[Join]] = None
    group_by: Optional[list[VarRef]] = None
    order_by: Optional[list[VarRef]] = None
    limit: Optional[int] = None
    is_output: bool = False

@dataclass(frozen=True)
class UnionAllSelect(Node):
    selects: list[Select]

@dataclass(frozen=True)
class VarRef(Node):
    name: str
    column: Optional[str] = None
    alias: Optional[str] = None
    type: Optional[str] = None

@dataclass(frozen=True)
class From(Node):
    table: str
    alias: Optional[str] = None

@dataclass(frozen=True)
class Join(Node):
    table: str
    alias: Optional[str]
    on: Optional[Expr] = None

@dataclass(frozen=True)
class LeftOuterJoin(Join):
    pass

@dataclass(frozen=True)
class FullOuterJoin(Join):
    pass

@dataclass(frozen=True)
class JoinWithoutCondition(Join):
    pass

@dataclass(frozen=True)
class RowNumberVar(Node):
    order_by_vars: list[OrderByVar]
    partition_by_vars: list[str]
    alias: str
    type: Optional[str] = None

@dataclass(frozen=True)
class OrderByVar(Node):
    var: str
    is_ascending: bool

# TODO: consider removing Where and make Select.where: Expr
@dataclass(frozen=True)
class Where(Node):
    expression: Optional[Expr] = None

@dataclass(frozen=True)
class RawSource(Node):
    """ A raw source for SQL, used to represent a raw SQL query or expression. """
    src: str

#-------------------------------------------------
# Clauses
#-------------------------------------------------
# TODO: move clauses from other sections

@dataclass(frozen=True)
class CTE(Node):
    """ Common Table Expressions. """
    recursive: bool
    name: str
    columns: list[str]
    selects: list[Select]
    distinct: bool = False

#-------------------------------------------------
# Expressions
#-------------------------------------------------

@dataclass(frozen=True)
class Expr(Node):
    pass

@dataclass(frozen=True)
class And(Expr):
    expr: list[Expr]

@dataclass(frozen=True)
class Or(Expr):
    expr: list[Expr]

@dataclass(frozen=True)
class Terminal(Expr):
    """ Avoid going deeper in the meta-model, this is an arbitrary terminal expression."""
    expr: str

@dataclass(frozen=True)
class NotNull(Expr):
    var: str

@dataclass(frozen=True)
class NotExists(Expr):
    expr: Select

@dataclass(frozen=True)
class BinaryExpr(Expr):
    left: str
    right: str

@dataclass(frozen=True)
class Like(BinaryExpr):
    pass

@dataclass(frozen=True)
class RegexLike(BinaryExpr):
    pass

#--------------------------------------------------
# Printer
#--------------------------------------------------

def to_string(node) -> str:
    io = StringIO()
    Printer(io).print_node(node, 0)
    return io.getvalue()

@dataclass(frozen=True)
class Printer(BasePrinter):

    _RESERVED_NAMES: frozenset[str] = frozenset({"right", "left", "order", "any", "table"})

    def _is_reserved_name(self, name: str) -> bool:
        return isinstance(name, str) and name.lower() in self._RESERVED_NAMES

    def _join(self, args, sep=', ', indent=0, is_output=False):
        for i, s in enumerate(args):
            if i != 0:
                if indent != 0:
                    self._print(sep.rstrip())
                    self._nl()
                else:
                    self._print(sep)
            self.print_node(s, indent, is_output=is_output)

    def _print_value(self, value, quote_strings:bool = False):
        if isinstance(value, tuple):
            for i, v in enumerate(value):
                if i != 0:
                    self._print(", ")
                self._print_value(v, True)
        elif isinstance(value, str):
            value = 'NULL' if value.lower() == 'none' else value
            value = json.dumps(value) if quote_strings else value
            self._print(value)
        elif isinstance(value, bool):
            self._print(str(value).lower())
        elif isinstance(value, datetime.date):
            self._print(f"'{value}'")
        elif isinstance(value, type(None)):
            self._print("NULL")
        else:
            self._print(str(value))

    def _print_query(self, indent, node, union_type:str = "UNION ALL"):
        queries = node.query if isinstance(node.query, list) else [node.query]
        if len(queries) == 1:
            self.print_node(queries[0], indent, True)
        else:
            for i, s in enumerate(queries):
                self._nl()
                if i != 0:
                    self._indent_print_nl(indent + 2, union_type)
                self.print_node(s, indent + 1, True)
        self._print(";")

    def _get_table_name(self, name: str) -> str:
        return f'"{name}"' if self._is_reserved_name(name) else name

    def print_node(self, node:Node, indent=0, inlined=False, is_output=False) -> None:
        # Table
        if isinstance(node, Program):
            for idx, d in enumerate(node.statements):
                self.print_node(d, indent)
                # Avoid an extra newline at the end of the file.
                if idx != len(node.statements) - 1:
                    self._nl()
        elif isinstance(node, Table):
            self._print(f"{self._get_table_name(node.name)} (")
            self._join(node.columns)
            self._print(")")
        elif isinstance(node, Column):
            self._print(f"{node.name} {node.type}")

        # Statements
        elif isinstance(node, CreateTable):
            clause = "IF NOT EXISTS " if node.if_not_exists else ""
            self._print(f"CREATE TABLE {clause}{node.table};")
        elif isinstance(node, CreateDynamicTable):
            self._print_nl(f"CREATE DYNAMIC TABLE {self._get_table_name(node.name)}")
            self._indent_print_nl(indent+1, f"TARGET_LAG = '{node.target_lag}'")
            self._indent_print_nl(indent+1, f"WAREHOUSE = '{node.warehouse}'")
            self._print("AS ")
            self._print_query(indent, node)
        elif isinstance(node, CreateView):
            self._print(f"CREATE VIEW {self._get_table_name(node.name)} AS ")
            self._print_query(indent, node, "UNION")
        elif isinstance(node, CreateFunction):
            self._print(f"CREATE OR REPLACE FUNCTION {self._get_table_name(node.name)} (")
            self._join(node.inputs)
            self._print_nl(")")
            self._print_nl(f"RETURNS {node.return_type}")
            self._print_nl(f"LANGUAGE {node.language}")
            self._print_nl(f"RUNTIME_VERSION = '{node.runtime_version}'")
            self._print_nl(f"HANDLER = '{node.handler}'")
            if node.packages:
                self._print("PACKAGES = (")
                self._join(node.packages)
                self._print_nl(")")
            self._print_nl("AS ")
            self._print_nl("$$")
            self._print_nl(node.body)
            self._print("$$;")
        elif isinstance(node, Insert):
            self._print(f"INSERT INTO {self._get_table_name(node.table)} ")
            if len(node.columns) > 0:
                self._print("(")
                self._join(node.columns)
                self._print(") ")
            if len(node.values) > 0:
                # We need to use `SELECT` with `UNION ALL` instead of `VALUES` because Snowflake parses and restricts
                #   certain expressions in VALUES(...). Built-in functions like HASH() or MD5() are often rejected unless used in SELECT.
                for i, value in enumerate(node.values):
                    if i != 0:
                        self._print(" UNION ALL ")
                    self._print("SELECT ")
                    self._join(value)
                self._print(";")
            if node.query is not None:
                self._print_query(indent, node)
        elif isinstance(node, Update):
            self._print(f"UPDATE {self._get_table_name(node.table)} SET ")
            self._join(node.set)
            if node.where is not None:
                self.print_node(node.where, indent)
            self._print(";")
        elif isinstance(node, UpdateSet):
            self._print(f"{node.name} = {node.expression}")
        elif isinstance(node, Select):
            self._indent_print(indent, "SELECT ")
            if node.distinct and node.froms:
                self._print("DISTINCT ")
            if node.vars:
                self._join(node.vars, is_output=node.is_output or is_output)
            else:
                self._print("*")
            if node.froms:
                self._print(" FROM ")
                if isinstance(node.froms, Select):
                    # If `froms` is a `Select`, we need to print it inline, and we do not need to indent it
                    self._print("( ")
                    self.print_node(node.froms, 0, True)
                    self._print(" )")
                else:
                    self._join(node.froms)
            if node.joins:
                self._print(" ")
                self._join(node.joins, sep=" ")
            if node.where:
                self.print_node(node.where, indent)
            if node.group_by:
                self._print(" GROUP BY ")
                self._join(node.group_by)
            if node.order_by:
                self._print(" ORDER BY ")
                self._join(node.order_by)
            if node.limit:
                self._print(f" LIMIT {node.limit}")
            if not inlined:
                self._print(";")
        elif isinstance(node, UnionAllSelect):
            if node.selects:
                self._indent_print_nl(indent, "SELECT DISTINCT * FROM (")
                for i, s in enumerate(node.selects):
                    if i != 0:
                        self._nl()
                        self._indent_print_nl(indent + 2, "UNION ALL")
                    self.print_node(s, indent + 1, True)
                self._nl()
                self._print(")")
                if not inlined:
                    self._print(";")
        elif isinstance(node, VarRef):
            # --- Handle column or name ---
            if node.column is None:
                self._print(node.name)
            elif node.column.lower() in ("any", "order"):
                self._print(f'{node.name}."{node.column}"')
            else:
                self._print(f"{node.name}.{node.column}")
            # --- Add CAST if needed ---
            if node.type:
                self._print(f"::{node.type}")
            # --- Handle alias ---
            if node.alias:
                needs_quotes = any(c in node.alias for c in ['-', '?'])
                if is_output:
                    self._print(f' as "{node.alias}"')
                elif node.alias != node.column or node.type or needs_quotes:
                    alias_str = f'"{node.alias}"' if needs_quotes else node.alias
                    self._print(f" as {alias_str}")
        elif isinstance(node, RowNumberVar):
            # --- ROW_NUMBER clause ---
            self._print("ROW_NUMBER() OVER (")
            # --- Partition by (if present) ---
            if node.partition_by_vars:
                self._print(" PARTITION BY ")
                self._join(node.partition_by_vars)
            # --- ORDER BY ---
            self._print(" ORDER BY ")
            self._join(node.order_by_vars)
            self._print(" )")
            # --- Add CAST if needed ---
            if node.type:
                self._print(f"::{node.type}")
            # --- Handle alias ---
            alias_str = f' as "{node.alias}"' if is_output else f' as {node.alias}'
            self._print(alias_str)
        elif isinstance(node, OrderByVar):
            self._print(node.var)
            direction = "ASC" if node.is_ascending else "DESC"
            self._print(f" {direction}")
        elif isinstance(node, From):
            self._print(self._get_table_name(node.table))
            if node.alias:
                self._print(f" AS {node.alias}")
        elif isinstance(node, Join):
            join_type = (
                "LEFT OUTER JOIN" if isinstance(node, LeftOuterJoin)
                else "FULL OUTER JOIN" if isinstance(node, FullOuterJoin)
                else "JOIN"
            )
            self._print(f"{join_type} {self._get_table_name(node.table)}")
            if node.alias is not None:
                self._print(f" AS {node.alias}")
            if not isinstance(node, JoinWithoutCondition):
                self._print(" ON ")
                if node.on is None:
                    self._print("TRUE")
                else:
                    self.print_node(node.on, indent, True)
        elif isinstance(node, Where):
            expr = node.expression if node.expression else 'FALSE'
            self._print(f" WHERE {expr}")
        elif isinstance(node, RawSource):
            self._print(node.src)

        # Clauses
        elif isinstance(node, CTE):
            self._print("WITH ")
            if node.recursive:
                self._print("RECURSIVE ")
            self._print(f"{self._get_table_name(node.name)} (")
            self._join(node.columns)
            self._print_nl(") AS (")
            for i, s in enumerate(node.selects):
                if i != 0:
                    self._nl()
                    self._indent_print_nl(indent + 2, "UNION ALL")
                self.print_node(s, indent + 1, True)
            self._nl()
            self._print(") SELECT")
            if node.distinct:
                self._print(" DISTINCT")
            self._print(f" * FROM {self._get_table_name(node.name)}")
            if not inlined:
                self._print(";")
        # --------------------------------------------------
        # Primitives, Annotations
        # --------------------------------------------------
        elif isinstance(node, (str, int, float, bool, datetime.date, tuple, type(None))):
            self._indent_print(indent, "")
            self._print_value(node)
        # Expressions
        elif isinstance(node, And):
            self._join(node.expr, " AND ", indent)
        elif isinstance(node, Or):
            self._print("( ")
            for i, expr in enumerate(node.expr):
                if i > 0:
                    self._print(" OR ")
                needs_parens = isinstance(expr, And)
                if needs_parens:
                    self._print("( ")
                self.print_node(expr, indent, True)
                if needs_parens:
                    self._print(" )")
            self._print(" )")
        elif isinstance(node, Terminal):
            self._print(node.expr)
        elif isinstance(node, NotNull):
            self._print(f"{node.var} IS NOT NULL")
        elif isinstance(node, NotExists):
            self._print("NOT EXISTS ( ")
            self.print_node(node.expr, indent, True)
            self._print(" )")
        elif isinstance(node, Like):
            self._print(f"{node.left} LIKE {node.right}")
        elif isinstance(node, RegexLike):
            self._print(f"REGEXP_LIKE({node.left}, {node.right})")
        else:
            raise Exception(f"Missing SQL.pprint({type(node)}): {node}")
