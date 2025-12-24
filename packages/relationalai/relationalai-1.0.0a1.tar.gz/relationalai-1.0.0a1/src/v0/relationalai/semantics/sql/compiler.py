from __future__ import annotations

import datetime
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from functools import partial
from itertools import chain
from typing import Tuple, cast, Optional, Union
from decimal import Decimal as PyDecimal

import math

from v0.relationalai.semantics.metamodel.rewrite import (Flatten, ExtractNestedLogicals, DNFUnionSplitter,
                                                      DischargeConstraints)
from v0.relationalai.semantics.metamodel.visitor import ReadWriteVisitor
from v0.relationalai.util.graph import topological_sort
from v0.relationalai.semantics.metamodel import ir, compiler as c, visitor as v, builtins, types, helpers
from v0.relationalai.semantics.metamodel.typer import Checker, InferTypes, typer
from v0.relationalai.semantics.metamodel.builtins import from_cdc_annotation, concept_relation_annotation
from v0.relationalai.semantics.metamodel.types import (Hash, String, Number, Int64, Int128, Bool, Date, DateTime, Float,
                                                    RowId, UInt128)
from v0.relationalai.semantics.metamodel.util import (FrozenOrderedSet, OrderedSet, frozen, ordered_set, filter_by_type,
                                                   NameCache)
from v0.relationalai.semantics.sql import sql, rewrite


class Compiler(c.Compiler):
    def __init__(self, skip_denormalization:bool=False):
        rewrites = [
            DischargeConstraints(),
            Checker(),
            ExtractNestedLogicals(),  # before InferTypes to avoid extracting casts
            InferTypes(),
            DNFUnionSplitter(),
            Flatten(handle_outputs=False),
            rewrite.RecursiveUnion(),
            rewrite.DoubleNegation(),
            rewrite.SortOutputQuery()
        ]
        if not skip_denormalization:
            # group updates, compute SCCs, use Sequence to denote their order
            rewrites.append(rewrite.Denormalize())
        super().__init__(rewrites)
        self.model_to_sql = ModelToSQL()

    def do_compile(self, model: ir.Model, options:dict={}) -> tuple[str, ir.Model]:
        """
        Compile the rewritten model into a SQL string. Returns the SQL string together
        with the rewritten model (after the rewrite passes, before translating to sql).
        """
        return str(self.model_to_sql.to_sql(model, options)), model

@dataclass(frozen=True)
class OutputVar:
    value: ir.Value
    alias: Optional[str] = None
    value_type: Optional[str] = None
    task: Optional[ir.Task] = None

@dataclass
class RelationInfo:
    used: bool = False
    view_selects: list[sql.Select] = field(default_factory=list)
    table_selects: list[sql.Select] = field(default_factory=list)
    dynamic_table_selects: list[sql.Select] = field(default_factory=list)

@dataclass
class ImportSpec:
    value: str
    module: Optional[str] = None  # e.g., "scipy.special"

    def render(self) -> str:
        return f"from {self.module} import {self.value}" if self.module else f"import {self.value}"


@dataclass
class UDFConfig:
    handler: str
    code: str
    imports: list[ImportSpec] = field(default_factory=list)
    packages: list[str] = field(default_factory=list)

@dataclass
class ModelToSQL:
    """ Generates SQL from an IR Model, assuming the compiler rewrites were done. """

    _is_duck_db: bool = False
    _warehouse: str = 'MAIN_WH'
    _query_compilation: bool = False
    _default_dynamic_table_target_lag: str = '5 minutes'
    relation_name_cache: NameCache = field(default_factory=NameCache)
    relation_arg_name_cache: NameCache = field(default_factory=NameCache)
    relation_infos: dict[ir.Relation, RelationInfo] = field(default_factory=dict)
    _error_relation_names: set[str] = field(default_factory=lambda: {'Error', 'pyrel_error_attrs'})

    def to_sql(self, model: ir.Model, options:dict) -> sql.Program:
        self.relation_infos.clear()
        self._is_duck_db = options.get("is_duck_db", False)
        self._warehouse = options.get("warehouse") or self._warehouse
        self._query_compilation = options.get("query_compilation", False)
        self._default_dynamic_table_target_lag = (options.get("default_dynamic_table_target_lag") or
                                                  self._default_dynamic_table_target_lag)
        return sql.Program(self._sort_dependencies(self._union_output_selects(self._generate_statements(model))))

    def _generate_statements(self, model: ir.Model) -> list[sql.Node]:
        table_relations, used_builtins = self._get_relations(model)

        self._register_relation_args(table_relations)
        self._register_external_relations(model)

        statements: list[sql.Node] = []
        # 1. Process root logical body
        root = cast(ir.Logical, model.root)
        for child in root.body:
            if isinstance(child, ir.Logical):
                statements.extend(self._create_statement(cast(ir.Logical, child)))
            elif isinstance(child, ir.Union):
                statements.append(self._create_recursive_view(cast(ir.Union, child)))

        relation_selects = {
            relation: info.dynamic_table_selects + info.view_selects + info.table_selects
            for relation, info in self.relation_infos.items()
            if info.dynamic_table_selects or info.view_selects or info.table_selects
        }

        # 3. Handle each relation with proper priority
        for relation, selects in relation_selects.items():
            table_name = self._relation_name(relation)

            info = self._get_relation_info(relation)
            if info.table_selects:
                # Relation is a table → insert into it
                columns = [self._var_name(relation.id, f) for f in relation.fields]
                if len(selects) == 1:
                    statements.append(sql.Insert(table_name, columns, [], selects[0]))
                else:
                    statements.append(sql.Insert(table_name, columns, [],
                                                 sql.CTE(False, f"{table_name}_cte", columns, selects, True)))
            elif info.view_selects:
                statements.append(sql.CreateView(table_name, selects))
            else:
                # Snowflake currently has issues when using DISTINCT together with UNION in a Dynamic Table.
                # As a workaround, we generate a CTE without DISTINCT, using UNION ALL.
                # Then, we create a dynamic table with `SELECT DISTINCT * FROM CTE` to remove duplicates.
                columns = [self._var_name(relation.id, f) for f in relation.fields]
                statements.append(
                    sql.CreateDynamicTable(
                        table_name,
                        sql.CTE(False, f"{table_name}_cte", columns, selects, True),
                        self._default_dynamic_table_target_lag,
                        self._warehouse
                    )
                )

        # 4. Create physical tables for explicitly declared table relations
        for relation in table_relations:
            info = self.relation_infos.get(relation)
            if info is None or info.table_selects:
                statements.append(self._create_table(relation))

        #5. Create Snowflake user-defined functions
        if not self._is_duck_db:
            statements.extend(self._create_user_defined_functions(used_builtins))

        return statements

    #--------------------------------------------------
    # SQL Generation
    #--------------------------------------------------
    def _create_table(self, r: ir.Relation) -> sql.Node:
        return sql.CreateTable(
            sql.Table(self._relation_name(r),
                list(map(lambda f: sql.Column(self._var_name(r.id, f), self._convert_type(f.type)), r.fields))
            ), self._query_compilation)

    def _create_recursive_view(self, union: ir.Union) -> sql.Node:
        assert len(union.tasks) >= 2, f"Recursive CTE requires at least 2 tasks (anchor + recursive), but got {len(union.tasks)}."
        assert all(isinstance(task, ir.Logical) for task in union.tasks), (
            "All tasks in a recursive CTE must be of type `ir.Logical`. "
            f"Invalid types: {[type(task).__name__ for task in union.tasks if not isinstance(task, ir.Logical)]}"
        )

        def make_case_select(logical: ir.Logical):
            # TODO - assuming a single update per case
            update = v.collect_by_type(ir.Update, logical).some()

            # Rewrite relation references for recursive lookups
            old_relation = update.relation
            new_relation = ir.Relation(f"{old_relation.name}_rec", old_relation.fields, frozen(), frozen())
            rlr = RecursiveLookupsRewriter(old_relation, new_relation)
            result = rlr.walk(logical)

            # TODO - improve the typing info to avoid these casts
            nots = cast(list[ir.Not], filter_by_type(result.body, ir.Not))
            unions = cast(list[ir.Union], filter_by_type(result.body, ir.Union))
            lookups = cast(list[ir.Lookup], filter_by_type(result.body, ir.Lookup))
            constructs = cast(list[ir.Construct], filter_by_type(result.body, ir.Construct))

            aliases = []
            for i, arg in enumerate(update.args):
                relation_field = old_relation.fields[i]
                field_type = self._convert_type(relation_field.type)
                aliases.append(OutputVar(arg, self._var_name(old_relation.id, relation_field), value_type=field_type))

            return self._make_select(lookups, aliases, nots, unions, constructs)

        # get a representative update
        update = v.collect_by_type(ir.Update, union).some()

        relation = update.relation
        self.mark_used(relation)
        return sql.CreateView(
            self._relation_name(relation),
            sql.CTE(
                True,
                f"{self._relation_name(relation)}_rec",
                [self._var_name(relation.id, field) for field in update.relation.fields],
                [
                    make_case_select(cast(ir.Logical, task))
                    for task in union.tasks
                ]
            )
        )

    def _create_user_defined_functions(self, relations: list[ir.Relation]) -> list[sql.CreateFunction]:
        # Central UDF metadata configuration
        udf_relations: dict[str, UDFConfig] = {
            builtins.acot.name: UDFConfig(
                handler="compute",
                imports=[ImportSpec("math")],
                code="""def compute(x): return math.atan(1 / x) if x != 0 else math.copysign(math.pi / 2, x)"""
            ),
            builtins.erf.name: UDFConfig(
                handler="compute",
                imports=[ImportSpec("math")],
                code="""def compute(x): return math.erf(x)"""
            ),
            builtins.erfinv.name: UDFConfig(
                handler="compute",
                imports=[ImportSpec("erfinv", module="scipy.special")],
                packages=["'scipy'"],
                code="""def compute(x): return erfinv(x)"""
            )
        }

        statements: list[sql.CreateFunction] = []

        for r in relations:
            meta = udf_relations.get(r.name)
            if not meta:
                continue

            # Split relation fields into inputs and return type
            # We expect a single return argument per builtin relation
            return_type = None
            input_columns: list[sql.Column] = []
            for f in r.fields:
                if f.input:
                    input_columns.append(sql.Column(self._var_name(r.id, f), self._convert_type(f.type)))
                else:
                    return_type = self._convert_type(f.type)

            # Build a full code block (imports + code)
            imports_code = "\n".join(imp.render() for imp in meta.imports)
            python_block = "\n".join(part for part in (imports_code, meta.code) if part)

            assert return_type, f"No return type found for relation '{r.name}'"
            statements.append(
                sql.CreateFunction(
                    name=r.name,
                    inputs=input_columns,
                    return_type=return_type,
                    handler=meta.handler,
                    body=python_block,
                    packages=meta.packages
                )
            )

        return statements

    def _create_statement(self, task: ir.Logical):

        # TODO - improve the typing info to avoid these casts
        nots = cast(list[ir.Not], filter_by_type(task.body, ir.Not))
        lookups = cast(list[ir.Lookup], filter_by_type(task.body, ir.Lookup))
        updates = cast(list[ir.Update], filter_by_type(task.body, ir.Update))
        outputs = cast(list[ir.Output], filter_by_type(task.body, ir.Output))
        logicals = cast(list[ir.Logical], filter_by_type(task.body, ir.Logical))
        constructs = cast(list[ir.Construct], filter_by_type(task.body, ir.Construct))
        ranks = cast(list[ir.Rank], filter_by_type(task.body, ir.Rank))
        aggs = cast(list[ir.Aggregate], filter_by_type(task.body, ir.Aggregate))
        unions = cast(list[ir.Union], filter_by_type(task.body, ir.Union))

        var_to_construct = {c.id_var: c for c in constructs} if constructs else {}

        statements = []
        if updates and not lookups and not nots and not aggs and not logicals and not unions:
            for u in updates:
                r = u.relation
                if r == builtins.raw_source:
                    lang, src = u.args[0], u.args[1]
                    if not (isinstance(lang, str) and lang.lower() == "sql"):
                        logging.warning(f"Unsupported language for RawSource: {lang}")
                        continue
                    if not isinstance(src, str):
                        raise Exception(f"Expected SQL source to be a string, got: {type(src).__name__}")
                    statements.append(sql.RawSource(src))
                else:
                    # Generate select with static values: SELECT hash(V1, ...), V2, V3
                    #   We need to use `SELECT` instead of `VALUES` because Snowflake parses and restricts certain expressions in VALUES(...).
                    #       Built-in functions like HASH() or MD5() are often rejected unless used in SELECT.
                    for values in self._get_tuples(task, u):
                        output_vars = [
                            sql.VarRef(str(value), alias=self._var_name(r.id, f))
                            for f, value in zip(r.fields, values)
                        ]
                        self.add_table_select(r, sql.Select(False, output_vars))
        elif lookups or outputs or nots or aggs or updates:
            # Some of the lookup relations we wrap into logical and we need to get them out for the SQL compilation.
            #    For example QB `decimal(0)` in IR will look like this:
            #        Logical ^[res]
            #           Exists(vDecimal128)
            #               Logical
            #                   cast(Decimal128, 0, vDecimal128)
            #                   decimal128(vDecimal128, res)
            unions = self._extract_all_of_type_from_logical(task, ir.Union) if logicals else unions
            all_lookups = self._extract_all_of_type_from_logical(task, ir.Lookup) if logicals else lookups

            var_to_union = {
                a: u
                for u in unions
                for t in u.tasks
                if isinstance(t, ir.Lookup)
                for a in t.args
                if isinstance(a, ir.Var)
            } if unions else {}

            if updates:
                # insert values that match a query: INSERT INTO ... SELECT ... FROM ... WHERE ...
                for u in updates:
                    r = u.relation
                    if self._is_error_relation(r):
                        # TODO: revisit this during `RAI-39124`. For now we filter out all error relations.
                        continue
                    # We shouldn’t create or populate tables for value types that can be directly sourced from existing Snowflake tables.
                    if not self._is_value_type_population_relation(r):
                        if all_lookups and all(builtins.is_builtin(lookup.relation) for lookup in all_lookups):
                            # Assuming static values insert when you have only builtin lookups (like `cast`, etc.) and you do not have table lookups.
                            aliases = self._get_update_aliases(u, var_to_construct, var_to_union, True)
                            select = self._make_select(all_lookups, aliases, nots, unions, constructs)
                            self.add_table_select(r, select)
                        else:
                            select = None
                            drv = DerivedRelationsVisitor()
                            task.accept(drv)
                            if aggs:
                                # After flatten it can be only one aggregation per rule.
                                select = self._make_agg_select(u, all_lookups, aggs[0], nots, unions, constructs)
                            elif ranks:
                                # After flatten it can be only one rank per rule.
                                select = self._make_rank_select(u, all_lookups, ranks[0], nots, unions, constructs)
                            else:
                                # Snowflake currently has issues when using DISTINCT together with UNION in a Dynamic Table.
                                # That is why we generate statements without DISTINCT, and we remove duplicates later
                                #   by using CTE + DISTINCT to declare the Dynamic Tables
                                distinct = True if self._is_duck_db or not drv.is_derived() else False
                                aliases = self._get_update_aliases(u, var_to_construct, var_to_union)

                                if not unions:
                                    select = self._make_select(all_lookups, aliases, nots, unions, constructs, distinct)
                                elif lookups:
                                    select = self._make_match_select(all_lookups, aliases, unions, nots, constructs, distinct)
                                else:
                                    select = self._make_full_outer_join_select(aliases, unions, constructs, distinct)

                            if drv.is_derived() and not self._is_duck_db:
                                self.add_dynamic_table_select(r, select)
                            else:
                                self.add_view_select(r, select)
            elif outputs:
                # output a query: SELECT ... FROM ... WHERE ...
                aliases = []
                distinct = False
                for output in outputs:
                    distinct = distinct or output.keys is None
                    for key, arg in output.aliases:
                        aliases.append(self._get_alias(key, arg, None, var_to_construct, var_to_union))

                if not unions:
                    if all(builtins.is_builtin(lookup.relation) for lookup in all_lookups):
                        # Example:
                        #   QB: select(1).where(Foo(1) == Bar(1))
                        #   IR:
                        #       Logical
                        #           1::Foo = 1::Bar
                        #           -> output(1 as 'v')
                        select = self._make_select(all_lookups, aliases, nots, unions, constructs, distinct, True)
                    else:
                        select = self._make_left_outer_join_select(task, all_lookups, aliases, nots, constructs, distinct)
                elif lookups:
                    select = self._make_match_select(all_lookups, aliases, unions, nots, constructs, distinct, True)
                else:
                    select = self._make_full_outer_join_select(aliases, unions, constructs, distinct, True)

                statements.append(select)
        elif logicals:
            for logical in logicals:
                statements.extend(self._create_statement(logical))
        elif not updates and not outputs:
            # Example:
            #   QB:
            #       (
            #         where(Person.age >= 65).define(Senior(Person)) |
            #         where(Person.age >= 18).define(Adult(Person)) |
            #         define(Child(Person))
            #       )
            #   After `flatten` IR will look like this:
            #       Logical
            #           Union
            #               _match_7(person_7)
            #               _match_8(person_7)
            #               _match_9(person_7)
            #
            # Nothing to query or define, we need to skip this task.
            return statements
        else:
            raise Exception(f"Cannot create SQL statement for:\n{task}")
        return statements

    def _make_agg_select(self, update: ir.Update, lookups: list[ir.Lookup], agg: ir.Aggregate,
                         nots: Optional[list[ir.Not]] = None, unions: Optional[list[ir.Union]] = None,
                         constructs: Optional[list[ir.Construct]] = None) -> sql.Select:

        """
        Generate a SQL SELECT for an aggregation using a DISTINCT subquery.

        Example output:
            SELECT
                department, count(v) AS v
            FROM (
                SELECT DISTINCT
                    v0.department, v0.employees AS v
                FROM
                    department_employees AS v0,
                    Department AS v1
                WHERE
                    v0.department = v1.department
            ) GROUP BY department;

        Rationale:
        In the IR, it’s not always explicit whether aggregation should be applied over distinct rows.
        By wrapping the aggregation in a DISTINCT subquery, we ensure correctness regardless of whether
        the original query used `count(...)` or `count(distinct ...)`.

        Compare:

        QB: select(count(Person.name))
        IR:
            Logical
                Logical ^[name=None, person_4=None]
                    Person(person_4)
                    name(person_4, name)
                count([person_4, name], [], [v])
                -> derive _aggregate_1(v)

        QB: select(count(distinct Person.name))
        IR:
            Logical
                Logical ^[name=None]
                    Person(person_4)
                    name(person_4, name)
                count([name], [], [v])
                -> derive _aggregate_1(v)

        Note:
        The key difference is that in the `distinct` case, the grouping variable `person_4` is absent from the projection.
        The subquery pattern unifies both cases by projecting all aggregation arguments, ensuring correctness.
        """

        seen_args = set()
        outputs: list[Union[sql.VarRef, sql.RowNumberVar, int]] = []
        sub_query_outputs: list[OutputVar] = []

        relation = update.relation
        agg_var = agg.args[0] if agg.aggregation == builtins.count else agg.args[1]
        # Group across all non-aggregated variables.
        group_by: list[sql.VarRef] = []

        for i, arg in enumerate(update.args):
            if arg not in seen_args:
                relation_field = relation.fields[i]
                field_type = self._convert_type(relation_field.type)
                field_name = self._var_name(relation.id, relation_field)
                if isinstance(arg, ir.Var) and arg == agg_var:
                    outputs.append(sql.VarRef(f"{agg.aggregation.name}({field_name})", alias=field_name, type=field_type))
                    sub_query_outputs.append(OutputVar(arg, field_name, task=agg))
                else:
                    group_by.append(sql.VarRef(field_name))
                    outputs.append(sql.VarRef(field_name, alias=field_name, type=field_type))
                    sub_query_outputs.append(OutputVar(arg, field_name))
                seen_args.add(arg)

        for arg in agg.projection:
            if arg not in seen_args:
                if agg.aggregation == builtins.count and arg == agg.projection[-1]:
                    continue
                sub_query_outputs.append(OutputVar(value=arg))
                seen_args.add(arg)

        sub_select = self._make_select(lookups, sub_query_outputs, nots, unions, constructs, True)

        return sql.Select(False, outputs, sub_select, group_by=group_by)

    def _make_rank_select(self, update: ir.Update, lookups: list[ir.Lookup], rank: ir.Rank,
                         nots: Optional[list[ir.Not]] = None, unions: Optional[list[ir.Union]] = None,
                         constructs: Optional[list[ir.Construct]] = None):

        """
        Generate a SQL SELECT for a rank using a DISTINCT subquery.

        Example output:
            SELECT
                cat, name, ROW_NUMBER() OVER ( ORDER BY name ASC ) as v
            FROM (
                SELECT DISTINCT
                    v0.cat, v1.name
                FROM
                    Cat AS v0, cat_name AS v1
                WHERE
                    v0.cat = v1.cat
            ) ORDER BY v LIMIT 10;

        Rationale:
        In the IR, it’s not always explicit whether rank should be applied over distinct rows.
        By wrapping the rank in a DISTINCT subquery, we ensure correctness regardless of whether
        the original query used `rank(...)` or `rank(distinct ...)`.

        Compare:

        QB: select(rank(Cat.name))
        IR:
            Logical
                Cat(cat_5)
                name(cat_5, name)
                rank([cat_5], [], [name'↑'], v)
                -> derive _rank_1(cat_5, name, v)

        QB: select(rank(distinct(Cat.name)))
        IR:
            Logical
                Cat(cat_5)
                name(cat_5, name)
                rank([], [], [name'↑'], v)
                -> derive _rank_1(name, v)

        Note:
        The key difference is that in the `distinct` case, the grouping variable `cat_5` is absent from the projection.
        The subquery pattern unifies both cases by projecting all rank arguments, ensuring correctness.
        """

        seen_args = set()
        outputs: list[Union[sql.VarRef, sql.RowNumberVar, int]] = []
        sub_query_outputs: list[OutputVar] = []

        order_by_vars = []
        for arg, is_ascending in zip(rank.args, rank.arg_is_ascending):
            order_by_vars.append(sql.OrderByVar(arg.name, is_ascending))
        partition_by_vars = [arg.name for arg in rank.group] if rank.group else []

        relation = update.relation

        rank_result_field_name = None
        for i, arg in enumerate(update.args):
            if arg not in seen_args:
                relation_field = relation.fields[i]
                field_type = self._convert_type(relation_field.type)
                field_name = self._var_name(relation.id, relation_field)
                if isinstance(arg, ir.Var) and arg == rank.result:
                    rank_result_field_name = field_name
                    outputs.append(sql.RowNumberVar(order_by_vars, partition_by_vars, field_name, field_type))
                else:
                    outputs.append(sql.VarRef(field_name, alias=field_name, type=field_type))
                sub_query_outputs.append(OutputVar(arg, field_name))
                seen_args.add(arg)

        for arg in rank.projection:
            if arg not in seen_args:
                sub_query_outputs.append(OutputVar(value=arg))
                seen_args.add(arg)

        sub_select = self._make_select(lookups, sub_query_outputs, nots, unions, constructs, True)

        assert rank_result_field_name is not None, "Rank result variable not found in update.args."
        return sql.Select(False, outputs, sub_select, order_by=[sql.VarRef(rank_result_field_name)], limit=rank.limit)

    def _make_match_select(self, lookups: list[ir.Lookup], outputs: list[OutputVar], unions: list[ir.Union],
                           nots: Optional[list[ir.Not]] = None, constructs: Optional[list[ir.Construct]] = None,
                           distinct: bool = False, is_output: bool = False):

        """
        Generate a SQL SELECT statement representing a match operation.

        Example output:
            SELECT
                COALESCE(v2.v0, v3.v0) as v0, v0.name, COALESCE(v4.v0, v5.v0) as v02
            FROM
                person_name AS v0
                JOIN Person AS v1 ON v0.person = v1.person
                LEFT OUTER JOIN _match_3 AS v2 ON v1.person = v2.person
                LEFT OUTER JOIN _match_4 AS v3 ON v1.person = v3.person
                LEFT OUTER JOIN _match_5 AS v4 ON v1.person = v4.person
                LEFT OUTER JOIN _match_6 AS v5 ON v1.person = v5.person
            WHERE
                ( v2.person IS NOT NULL OR v3.person IS NOT NULL ) AND
                ( v4.person IS NOT NULL OR v5.person IS NOT NULL );

        Explanation:
            This query performs a series of joins to gather matching records based on shared keys (`person`).
            - INNER JOINs are used for mandatory relations (e.g. `Person`, `person_name`).
            - LEFT OUTER JOINs are used to include optional match sets from auxiliary `_match_*` tables.
            - `COALESCE(expr1, expr2, ...)` is used to merge values from multiple sources,
                returning the first non-null value among the arguments (or NULL if all are null).
            This is particularly useful for flattening results from union-style matches and preserving partial matches
                in a single SELECT clause.
        """

        var_to_construct = {c.id_var: c for c in constructs} if constructs else {}

        union_lookups: dict[ir.Union, OrderedSet[ir.Lookup]] = self._extract_all_lookups_per_union(unions)

        table_lookups = OrderedSet.from_iterable(t for t in lookups if not builtins.is_builtin(t.relation))
        froms, joins, wheres, sql_vars, var_column, var_lookups = self._extract_match_lookups_metadata(table_lookups, union_lookups)

        builtin_lookups = OrderedSet.from_iterable(t for t in lookups if builtins.is_builtin(t.relation))
        builtin_vars, builtin_wheres, builtin_table_expressions = (
            self._resolve_builtins(builtin_lookups, var_lookups, var_column, sql_vars, var_to_construct, outputs))

        froms.extend(self._process_builtin_table_expressions(builtin_table_expressions))

        wheres.extend(builtin_wheres)

        construct_wheres = self._process_constructs(table_lookups, var_lookups, var_column, sql_vars, builtin_vars,
                                                    var_to_construct)
        wheres.extend(construct_wheres)

        not_null_vars, vars = self._generate_select_output(outputs, builtin_vars, sql_vars, var_column, var_lookups,
                                                           var_to_construct)

        if not_null_vars:
            wheres.extend(sql.NotNull(var) for var in not_null_vars)

        not_exists, _ = self._generate_select_nots(nots, var_lookups, sql_vars, var_column, len(sql_vars))
        wheres.extend(not_exists)

        where = self._process_wheres_clauses(wheres)

        return sql.Select(distinct, vars, froms, where, joins, is_output=is_output)

    def _make_full_outer_join_select(self, outputs: list[OutputVar], unions: list[ir.Union],
                                     constructs: Optional[list[ir.Construct]] = None, distinct: bool = False,
                                     is_output: bool = False):

        """
        Generate a SQL SELECT statement representing a match operation that combines multiple sets of data
        (using FULL OUTER JOINs), without additional lookup filtering.

        This method is used when the input IR (Intermediate Representation) does not contain table lookups
        but consists of `Union` operations grouped under a `Logical` node. The goal is to preserve all values
        from each union input while aligning their corresponding fields via outer joins.

        IR Example:
            Logical
                Logical ^[v0=None]
                    Union ^[v0]
                        _match_10(v0)
                        _match_11(v0)
                Logical ^[v0_2=None]
                    Union ^[v0_2]
                        _match_12(v0_2)
                        _match_13(v0_2)
                -> output(v0, v0_2 as 'v02')

        This corresponds to an output schema with two final fields:
        - `v0`, derived from `_match_10` and `_match_11`
        - `v02`, derived from `_match_12` and `_match_13`

        Example output:
            SELECT DISTINCT
                COALESCE(v0.v0, v1.v0) as v0, COALESCE(v2.v0, v3.v0) as v02
            FROM
                _match_10 AS v0
                FULL OUTER JOIN _match_11 AS v1 ON TRUE
                FULL OUTER JOIN _match_12 AS v2 ON TRUE
                FULL OUTER JOIN _match_13 AS v3 ON TRUE;

        Explanation:
            - Each `Union` is compiled into one or more subqueries (e.g. `_match_10`, `_match_11`) that may represent
              disjoint subsets of data.
            - These are combined using `FULL OUTER JOIN` to retain all possible values from each side, including `NULL`s.
            - `COALESCE()` is used to merge values from the joined tables into a single column per output field.
            - This strategy ensures completeness when different subsets may contain different keys or match results.
        """

        var_to_construct = {c.id_var: c for c in constructs} if constructs else {}

        union_lookups: dict[ir.Union, OrderedSet[ir.Lookup]] = self._extract_all_lookups_per_union(unions)
        froms, joins, wheres, sql_vars, var_column, var_lookups = self._extract_union_lookups_metadata(union_lookups)

        not_null_vars, vars = self._generate_select_output(outputs, {}, sql_vars, var_column, var_lookups,
                                                           var_to_construct)

        if not_null_vars:
            wheres.extend(sql.NotNull(var) for var in not_null_vars)

        where = self._process_wheres_clauses(wheres)

        return sql.Select(distinct, vars, froms, where, joins, is_output=is_output)

    def _make_left_outer_join_select(self, task: ir.Logical, lookups: list[ir.Lookup], outputs: list[OutputVar],
                                     nots: Optional[list[ir.Not]] = None, constructs: Optional[list[ir.Construct]] = None,
                                     distinct: bool = False) -> sql.Select:

        """
        Generate a SQL SELECT statement from an output query by combining INNER JOIN and LEFT OUTER JOIN clauses
        based on the IR structure.

        ### JOIN Rules:

        1. **Top-level lookups** (direct children of the root `Logical`) always use **INNER JOIN**.

        2. **LEFT OUTER JOIN** is used for a lookup if:
           - It appears inside a nested `Logical`, and
           - The corresponding variable is hoisted with a `None` value in that `Logical`.
           - Example: `id(student, id)` is translated as a LEFT OUTER JOIN if the `Logical` hoists `id=None`.

        3. If a variable is hoisted with `None` in one `Logical`, but used in another lookup that is hoisted without `None`,
            the corresponding join becomes **INNER JOIN**.
           - This resolves ambiguity when a lookup's output variable is reused meaningfully elsewhere.

        ---

        ### IR Example 1 (with LEFT OUTER JOIN):

        IR:
            Logical
                Logical
                    Student(student)
                    goes_at(student, school)
                    subject(school, subject)
                    desc(subject, desc)
                    desc = "English"
                    Logical ^[id=None]
                        id(student, id)
                    Logical ^[name=None, course=None]
                        attends(student, course)
                        instructor(course, instructor)
                        name(instructor, name)
                    -> output[student, course, subject](id, name, desc)

        SQL Output:
            SELECT
                v0.id, v3.name, v7.desc
            FROM
                Student AS v4
                JOIN student_goes_at AS v5 ON v4.student = v5.student
                JOIN school_subject AS v6 ON v5.school = v6.school
                JOIN subject_desc AS v7 ON v6.subject = v7.subject
                LEFT OUTER JOIN student_id AS v0 ON v5.student = v0.student
                LEFT OUTER JOIN student_attends AS v1 ON v5.student = v1.student
                LEFT OUTER JOIN course_instructor AS v2 ON v1.course = v2.course
                LEFT OUTER JOIN instructor_name AS v3 ON v2.instructor = v3.instructor
            WHERE
                v7.desc = 'English';

        ---

        ### IR Example 2 (with NOT EXISTS):

        IR:
            Logical
                Not
                    Logical
                        Logical ^[person, age]
                            _union_1(person, age)
                Person(person)
                Logical ^[name=None]
                    name(person, name)
                Logical ^[age=None]
                    age(person, age)
                -> output[person](name, age)

        Note: Even though `age` is hoisted with `None`, it is also used in `_union_1` which is hoisted without `None`
        (i.e., `^[person, age]`). Therefore, `age(person, age)` is compiled as an INNER JOIN.

        SQL Output:
            SELECT
                v0.name,
                v1.age
            FROM
                Person AS v2
                JOIN person_name AS v0 ON v2.person = v0.person
                JOIN person_age AS v1 ON v2.person = v1.person
            WHERE
                NOT EXISTS ( SELECT 1 FROM _union_1 AS v3 WHERE v3.person = v0.person AND v3.age = v1.age );

        ---
        """

        var_to_construct = {c.id_var: c for c in constructs} if constructs else {}

        table_lookups = OrderedSet.from_iterable(t for t in lookups if not builtins.is_builtin(t.relation))
        froms, joins, wheres, sql_vars, var_column, var_lookups = (
            self._extract_left_outer_joins_lookups_metadata(task, table_lookups, nots))

        builtin_lookups = OrderedSet.from_iterable(t for t in lookups if builtins.is_builtin(t.relation))
        builtin_vars, builtin_wheres, builtin_table_expressions = (
            self._resolve_builtins(builtin_lookups, var_lookups, var_column, sql_vars, var_to_construct, outputs))

        # SF in case of `LEFT OUTER JOIN` and `ARRAY_GENERATE_RANGE` doesn't allow usage of `ON TRUE` but
        #   for DuckDB this is mandatory that is why we have 2 different join classes.
        make_join = (lambda e, a: sql.Join(e, a)) if self._is_duck_db else (lambda e, a: sql.JoinWithoutCondition(e, a))
        joins.extend(make_join(expr, alias) for alias, expr in builtin_table_expressions.items())

        wheres.extend(builtin_wheres)

        construct_wheres = self._process_constructs(table_lookups, var_lookups, var_column, sql_vars, builtin_vars,
                                                    var_to_construct)
        wheres.extend(construct_wheres)

        _, vars = self._generate_select_output(outputs, builtin_vars, sql_vars, var_column, var_lookups, var_to_construct)

        not_exists, _ = self._generate_select_nots(nots, var_lookups, sql_vars, var_column, len(sql_vars))
        wheres.extend(not_exists)

        where = self._process_wheres_clauses(wheres)

        return sql.Select(distinct, vars, froms, where, joins, is_output=True)

    def _make_select(self, lookups: list[ir.Lookup], outputs: list[OutputVar], nots: Optional[list[ir.Not]] = None,
                     unions: Optional[list[ir.Union]] = None, constructs: Optional[list[ir.Construct]] = None,
                     distinct: bool = False, is_output: bool = False) -> sql.Select:

        var_to_construct = {c.id_var: c for c in constructs} if constructs else {}

        union_lookups: dict[ir.Union, OrderedSet[ir.Lookup]] = self._extract_all_lookups_per_union(unions)
        all_lookups = lookups + list(chain.from_iterable(union_lookups.values()))

        table_lookups = OrderedSet.from_iterable(t for t in all_lookups if not builtins.is_builtin(t.relation))
        froms, wheres, sql_vars, var_column, var_lookups = self._extract_lookups_metadata(table_lookups)

        builtin_lookups = OrderedSet.from_iterable(t for t in all_lookups if builtins.is_builtin(t.relation))
        builtin_vars, builtin_wheres, builtin_table_expressions = (
            self._resolve_builtins(builtin_lookups, var_lookups, var_column, sql_vars, var_to_construct, outputs))

        froms.extend(self._process_builtin_table_expressions(builtin_table_expressions))

        wheres.extend(builtin_wheres)

        construct_wheres = self._process_constructs(table_lookups, var_lookups, var_column, sql_vars, builtin_vars,
                                                    var_to_construct)
        wheres.extend(construct_wheres)

        wheres.extend(self._generate_where_clauses(var_lookups, var_column, sql_vars, union_lookups))

        not_null_vars, vars = self._generate_select_output(outputs, builtin_vars, sql_vars, var_column,
                                                                  var_lookups, var_to_construct)

        if not_null_vars:
            wheres.extend(sql.NotNull(var) for var in not_null_vars)

        not_exists, _ = self._generate_select_nots(nots, var_lookups, sql_vars, var_column, len(sql_vars))
        wheres.extend(not_exists)

        where = self._process_wheres_clauses(wheres)

        return sql.Select(distinct, vars, froms, where, is_output=is_output)

    def _extract_lookups_metadata(self, lookups: OrderedSet[ir.Lookup], start_index: int = 0):
        froms: list[sql.From] = []
        wheres: list[sql.Expr] = []
        sql_vars: dict[ir.Lookup, str] = dict()  # one var per table lookup
        var_column: dict[Tuple[ir.Var, ir.Lookup], ir.Field] = dict()
        var_lookups: dict[ir.Var, OrderedSet[ir.Lookup]] = defaultdict(OrderedSet)
        i = start_index

        for lookup in lookups:
            varname = f"v{i}"
            froms.append(sql.From(self._relation_name(lookup.relation), varname))
            sql_vars[lookup] = varname
            self._process_lookup_args(lookup, sql_vars, var_column, var_lookups, wheres)
            i += 1

        return froms, wheres, sql_vars, var_column, var_lookups

    def _extract_match_lookups_metadata(self, lookups: OrderedSet[ir.Lookup],
                                         union_lookups: dict[ir.Union, OrderedSet[ir.Lookup]], start_index: int = 0):
        wheres: list[sql.Expr] = []
        sql_vars: dict[ir.Lookup, str] = dict()  # one var per table lookup
        var_column: dict[Tuple[ir.Var, ir.Lookup], ir.Field] = dict()
        var_lookups: dict[ir.Var, OrderedSet[ir.Lookup]] = defaultdict(OrderedSet)
        i = start_index

        def process_lookups(lookup_set: OrderedSet[ir.Lookup]):
            nonlocal i
            for lookup in lookup_set:
                sql_vars[lookup] = f"v{i}"
                self._process_lookup_args(lookup, sql_vars, var_column, var_lookups, wheres)
                i += 1

        # Step 1: assign aliases and populate helper mappings
        process_lookups(lookups)
        for values in union_lookups.values():
            process_lookups(values)

        # Step 2: build joins
        used_lookups = ordered_set()
        first_lookup = next(iter(lookups))
        used_lookups.add(first_lookup)
        froms: list[sql.From] = []
        joins: list[sql.Join] = []

        # Start with the first table as the root FROM
        froms.append(sql.From(self._relation_name(first_lookup.relation), sql_vars[first_lookup]))

        def _process_joins(lookup: ir.Lookup, is_left_join: bool = False):
            # Try to find a shared variable with any *latest* used lookup
            join_conditions = []
            lookup_not_null_conditions = []

            for arg in lookup.args:
                if isinstance(arg, ir.Var) and arg in var_lookups:
                    for other_lookup in reversed(list(used_lookups)):  # reversed: prioritize most recent join
                        if other_lookup in var_lookups[arg]:
                            left_alias = sql_vars[other_lookup]
                            right_alias = sql_vars[lookup]

                            left_field = self._var_name(other_lookup.relation.id, var_column[(arg, other_lookup)])
                            right_field = self._var_name(lookup.relation.id, var_column[(arg, lookup)])

                            left_var = f"{left_alias}.{left_field}"
                            right_var = f"{right_alias}.{right_field}"

                            join_conditions.append(sql.Terminal(f"{left_var} = {right_var}"))

                            if is_left_join:
                                lookup_not_null_conditions.append(sql.NotNull(right_var))

                            break  # stop on first recent match

            if join_conditions:
                on = sql.And(join_conditions) if len(join_conditions) > 1 else join_conditions[0]
                join = sql.LeftOuterJoin(self._relation_name(lookup.relation), sql_vars[lookup], on) if is_left_join \
                    else sql.Join(self._relation_name(lookup.relation), sql_vars[lookup], on)
                joins.append(join)

                if is_left_join:
                    return sql.And(lookup_not_null_conditions) if len(lookup_not_null_conditions) > 1 else lookup_not_null_conditions[0]
                else:
                    used_lookups.add(lookup)
                    return None
            else:
                raise ValueError(f"No join condition found for lookup: {lookup}")

        # Add JOINs based on shared variables
        for lookup in lookups:
            if lookup not in used_lookups:
                _process_joins(lookup)

        # Add LEFT JOINs based on shared variables
        for values in union_lookups.values():
            not_null_conditions = []
            for lookup in values:
                if lookup not in used_lookups:
                    lookup_condition = _process_joins(lookup, is_left_join=True)
                    not_null_conditions.append(lookup_condition)

            if not_null_conditions:
                wheres.append(sql.Or(not_null_conditions))

        return froms, joins, wheres, sql_vars, var_column, var_lookups

    def _extract_union_lookups_metadata(self, lookups: dict[ir.Union, OrderedSet[ir.Lookup]], start_index: int = 0):
        wheres: list[sql.Expr] = []
        sql_vars: dict[ir.Lookup, str] = {}
        var_column: dict[Tuple[ir.Var, ir.Lookup], ir.Field] = {}
        var_lookups: dict[ir.Var, OrderedSet[ir.Lookup]] = defaultdict(OrderedSet)
        froms: list[sql.From] = []
        joins: list[sql.Join] = []
        used_lookups = ordered_set()

        i = start_index
        first_lookup_handled = False

        for values in lookups.values():
            for lookup in values:
                sql_vars[lookup] = f"v{i}"
                self._process_lookup_args(lookup, sql_vars, var_column, var_lookups, wheres)
                i += 1

                if not first_lookup_handled:
                    # Use this as the base FROM
                    froms.append(sql.From(self._relation_name(lookup.relation), sql_vars[lookup]))
                    used_lookups.add(lookup)
                    first_lookup_handled = True
                else:
                    # Join the rest
                    joins.append(sql.FullOuterJoin(self._relation_name(lookup.relation), sql_vars[lookup]))

        return froms, joins, wheres, sql_vars, var_column, var_lookups

    def _extract_left_outer_joins_lookups_metadata(self, task: ir.Logical, lookups: OrderedSet[ir.Lookup],
                                                   nots: Optional[list[ir.Not]] = None, start_index: int = 0):
        wheres: list[sql.Expr] = []
        sql_vars: dict[ir.Lookup, str] = dict()  # one var per table lookup
        var_column: dict[Tuple[ir.Var, ir.Lookup], ir.Field] = dict()
        var_lookups: dict[ir.Var, OrderedSet[ir.Lookup]] = defaultdict(OrderedSet)

        # Step 1: assign aliases and populate helper mappings
        i = start_index
        for lookup in lookups:
            sql_vars[lookup] = f"v{i}"
            self._process_lookup_args(lookup, sql_vars, var_column, var_lookups, wheres)
            i += 1

        froms: list[sql.From] = []
        joins: list[sql.Join] = []
        full_context = ordered_set()

        # Choose a root FROM table
        first_lookup = next(iter(lookups))
        froms.append(sql.From(self._relation_name(first_lookup.relation), sql_vars[first_lookup]))
        full_context.add(first_lookup)

        @dataclass(frozen=True)
        class JoinMetadata:
            on: Optional[sql.Expr] = None
            inner_join: bool = False

        joins_metadata: dict[ir.Lookup, JoinMetadata] = {}
        not_null_vars: set[ir.Var] = self._extract_all_not_null_vars_from_nots(nots)

        def _process_joins(lookup: ir.Lookup, context: OrderedSet[ir.Lookup], inner_join: bool = True):
            join_conditions = []
            seen_pairs = set()

            # We want most recent joins first from context, then from full_context
            search_context = list(reversed(context)) + [
                lk for lk in reversed(full_context) if lk not in context
            ]

            for arg in lookup.args:
                inner_join = arg in not_null_vars or inner_join
                if isinstance(arg, ir.Var) and arg in var_lookups:
                    for other_lookup in search_context:
                        if other_lookup in var_lookups[arg]:
                            right_alias = sql_vars[lookup]
                            left_alias = sql_vars[other_lookup]

                            right_field = self._var_name(lookup.relation.id, var_column[(arg, lookup)])
                            left_field = self._var_name(other_lookup.relation.id, var_column[(arg, other_lookup)])

                            pair = (left_alias, left_field, right_alias, right_field)
                            if pair not in seen_pairs:
                                seen_pairs.add(pair)
                                join_conditions.append(sql.Terminal(f"{left_alias}.{left_field} = {right_alias}.{right_field}"))
                            break  # stop at first matching lookup

            on = None
            if join_conditions:
                on = sql.And(join_conditions) if len(join_conditions) > 1 else join_conditions[0]

            join_metadata = joins_metadata.get(lookup)

            if join_metadata:
                # Upgrade to inner join only if previously marked as left outer join
                if inner_join and not join_metadata.inner_join:
                    joins_metadata[lookup] = JoinMetadata(on, inner_join)
            else:
                joins_metadata[lookup] = JoinMetadata(on, inner_join)

        def _process_logical(logical: ir.Logical, parent_context: Optional[OrderedSet[ir.Lookup]] = None):
            # Step 1: Prepare null variables from hoisted defaults
            null_vars = {
                v.var for v in (logical.hoisted or [])
                if isinstance(v, ir.Default) and v.value is None
            }

            # Step 2: Create a working context from parent_context
            context = OrderedSet.from_iterable(parent_context) if parent_context else ordered_set()

            # Step 3: Process all sub-tasks
            for sub_task in logical.body:
                if isinstance(sub_task, ir.Logical):
                    _process_logical(sub_task, context)
                elif isinstance(sub_task, ir.Lookup):
                    lookup = cast(ir.Lookup, sub_task)
                    if lookup != first_lookup and not builtins.is_builtin(lookup.relation):
                        inner_join = False if null_vars else True
                        _process_joins(lookup, context, inner_join)
                        context.add(lookup)
                        full_context.add(lookup)

        _process_logical(task, full_context)

        for lookup, metadata in joins_metadata.items():
            if metadata.inner_join:
                joins.append(sql.Join(self._relation_name(lookup.relation), sql_vars[lookup], metadata.on))
            else:
                joins.append(sql.LeftOuterJoin(self._relation_name(lookup.relation), sql_vars[lookup], metadata.on))

        return froms, joins, wheres, sql_vars, var_column, var_lookups

    def _process_lookup_args(self, lookup: ir.Lookup, sql_vars: dict[ir.Lookup, str],
                             var_column: dict[Tuple[ir.Var, ir.Lookup], ir.Field],
                             var_lookups: dict[ir.Var, OrderedSet[ir.Lookup]], wheres: list[sql.Expr]):
        relation = lookup.relation
        for j, arg in enumerate(lookup.args):
            rel_field = relation.fields[j]
            if isinstance(arg, ir.Var):
                var_column[arg, lookup] = rel_field
                var_lookups[arg].add(lookup)
            # case when Literal is used as a relation argument: `test(1, x)`
            elif isinstance(arg, (int, str, float, bool, ir.Literal)):
                ref = f"{sql_vars[lookup]}.{self._var_name(relation.id, rel_field)}"
                wheres.append(sql.Terminal(f"{ref} = {self._convert_value(arg)}"))

    def _var_reference(self, var_lookups: dict[ir.Var, OrderedSet[ir.Lookup]], sql_vars: dict[ir.Lookup, str],
                       var_column: dict[Tuple[ir.Var, ir.Lookup], ir.Field], v):
        if isinstance(v, ir.Var):
            # TODO - assuming the built-in reference was grounded elsewhere
            lookup = var_lookups[v].some()
            return f"{sql_vars[lookup]}.{self._var_name(lookup.relation.id, var_column[(v, lookup)])}"
        return f"'{v}'" if isinstance(v, str) else str(v)

    def _resolve_builtin_var(self, builtin_vars: dict[ir.Var, ir.Value|str|int], var):
        # We need recursive lookup because it maybe a case when we need to join more than 2 lookups.
        #    For example QB `a != decimal(0)` in IR will look like this:
        #        Logical ^[res]
        #           Exists(vDecimal128)
        #               Logical
        #                   cast(Decimal128, 0, vDecimal128)
        #                   decimal128(vDecimal128, res)
        #        a != res
        #    But we need to convert it to `a != 0` in SQL.
        if isinstance(var, ir.Var) and var in builtin_vars:
            val = builtin_vars[var]
            return self._resolve_builtin_var(builtin_vars, val) if isinstance(val, ir.Var) else val
        return var

    def _build_hash_expression(self, reference, resolve_builtin_var, var_to_construct, values):
        """Generate hash expression like hash(`x`, `y`, TABLE_ALIAS.COLUMN_NAME)."""
        elements = []
        for val in values:
            resolved_val = resolve_builtin_var(val)
            if val != resolved_val and isinstance(resolved_val, str):
                # In case we parsed builtin into some expression, we may add it as an element.
                # For example, `TO_DATE('1990-1-1', 'Y-m-d')` or `(v1.value + 5)`.
                elements.append(f"{resolved_val}")
                continue
            if isinstance(resolved_val, ir.Var):
                if resolved_val in var_to_construct:
                    elements.append(self._resolve_construct_var(reference, resolve_builtin_var, var_to_construct, var_to_construct[resolved_val]))
                else:
                    elements.append(reference(resolved_val))
            else:
                elements.append(str(self._convert_value(resolved_val)))
        return f"hash({', '.join(elements)})"

    def _resolve_construct_var(self, reference, resolve_builtin_var, var_to_construct, construct: ir.Construct):
        return self._build_hash_expression(reference, resolve_builtin_var, var_to_construct, construct.values)

    def _resolve_hash_var(self, reference, resolve_builtin_var, var_to_construct, arg: Union[ir.ListType, ir.Value]):
        if isinstance(arg, Tuple):
            return self._build_hash_expression(reference, resolve_builtin_var, var_to_construct, arg)
        return self._build_hash_expression(reference, resolve_builtin_var, var_to_construct, [arg])

    def _resolve_builtins(self, builtin_lookups: OrderedSet[ir.Lookup], var_lookups: dict[ir.Var, OrderedSet[ir.Lookup]],
                          var_column: dict[Tuple[ir.Var, ir.Lookup], ir.Field], sql_vars: dict[ir.Lookup, str],
                          var_to_construct: dict[ir.Var, ir.Construct],
                          outputs: Optional[list[OutputVar]] = None):

        wheres: list[sql.Expr] = []
        # We need to maintain a mapping of these builtin expressions because they generate a new table, which must be
        #   referenced in the FROM clause as part of a JOIN. Structure is `SQL table variable` -> `generated expression`
        table_expressions: dict[str, str] = {}
        builtin_vars: dict[ir.Var, ir.Value|str|int] = {}
        # TODO: remove this when we introduce date periods in builtins
        date_period_var_type: dict[ir.Var, str] = {}

        output_vars = {
            output.value
            for output in outputs or []
            if isinstance(output.value, ir.Var)
        }

        intermediate_builtin_vars: set[ir.Var] = {
            arg for lookup in builtin_lookups
            for arg in lookup.args
            if isinstance(arg, ir.Var) and arg not in var_lookups
        }

        reference = partial(self._var_reference, var_lookups, sql_vars, var_column)
        resolve_builtin_var = partial(self._resolve_builtin_var, builtin_vars)

        for lookup in self._sort_builtin_lookups(list(builtin_lookups), output_vars):
            args = lookup.args
            relation = lookup.relation
            relation_name = self._relation_name(relation)

            if relation == builtins.substring:
                assert len(args) == 4, f"Expected 4 args for `strings.substring`, got {len(args)}: {args}"

                # Unpack and process arguments
                lhs_raw, from_idx_raw, to_idx_raw, output = args
                assert isinstance(output, ir.Var), "Fourth argument (output) must be a variable"
                from_idx = self._convert_value(from_idx_raw)
                to_idx = self._convert_value(to_idx_raw)

                # Resolve the left-hand side expression
                left = self._var_to_expr(lhs_raw, reference, resolve_builtin_var, var_to_construct)

                # Calculate substring length: SQL is 1-based and end-inclusive
                substring_len = int(to_idx) - int(from_idx) + 1
                assert substring_len >= 0, f"Invalid substring range: from {from_idx} to {to_idx}"

                expr = f"substring({left}, {from_idx}, {substring_len})"
                builtin_vars[output] = expr
            elif relation == builtins.replace:
                assert len(args) == 4, f"Expected 4 args for `replace`, got {len(args)}: {args}"
                subject_raw, pattern_raw, replacement_raw, output = args
                subject = self._var_to_expr(subject_raw, reference, resolve_builtin_var, var_to_construct)
                pattern = self._var_to_expr(pattern_raw, reference, resolve_builtin_var, var_to_construct)
                replacement = self._var_to_expr(replacement_raw, reference, resolve_builtin_var, var_to_construct)
                assert isinstance(output, ir.Var), "Fourth argument (output) must be a variable"
                builtin_vars[output] = f"replace({subject}, {pattern}, {replacement})"
            elif relation == builtins.split_part:
                assert len(args) == 4, f"Expected 4 args for `split_part`, got {len(args)}: {args}"
                separator_raw, s_raw, idx_raw, output = args
                separator = self._var_to_expr(separator_raw, reference, resolve_builtin_var, var_to_construct)
                s = self._var_to_expr(s_raw, reference, resolve_builtin_var, var_to_construct)
                idx = self._var_to_expr(idx_raw, reference, resolve_builtin_var, var_to_construct)
                assert isinstance(output, ir.Var)
                builtin_vars[output] = f"split_part({s}, {separator}, {idx})"
            elif relation == builtins.split:
                assert len(args) == 4, f"Expected 4 args for `split`, got {len(args)}: {args}"
                separator_raw, value_raw, index, part = args
                value = self._var_to_expr(value_raw, reference, resolve_builtin_var, var_to_construct)
                separator = self._var_to_expr(separator_raw, reference, resolve_builtin_var, var_to_construct)
                table_sql_var = f"v{len(sql_vars)}"
                sql_vars[lookup] = table_sql_var
                if self._is_duck_db:
                    table_alias = f"{table_sql_var}(data)"
                    table_expressions[table_alias] = f"VALUES(string_split({value}, {separator}))"

                    part_expr = f"unnest({table_sql_var}.data)"
                    index_expr = f"generate_subscripts({table_sql_var}.data, 1)"
                else:
                    table_expressions[table_sql_var] = f"LATERAL FLATTEN(input => SPLIT({value}, {separator}))"

                    # SF returns values in `""` and to avoid this, we need to cast it to `TEXT` type
                    part_expr = f"cast({table_sql_var}.value as TEXT)"
                    index_expr = f"({table_sql_var}.index + 1)" # SF is 0-based internally, adjust to it back
                assert isinstance(index, ir.Var) and isinstance(part, ir.Var), "Third and fourth arguments (index, part) must be variables"
                builtin_vars[part] = part_expr
                builtin_vars[index] = index_expr
            elif relation == builtins.range:
                assert len(args) == 4, f"Expected 4 args for `range`, got {len(args)}: {args}"
                start_raw, stop_raw, step_raw, result = args
                start = self._var_to_expr(start_raw, reference, resolve_builtin_var, var_to_construct)
                stop = self._var_to_expr(stop_raw, reference, resolve_builtin_var, var_to_construct)
                step = self._var_to_expr(step_raw, reference, resolve_builtin_var, var_to_construct)
                table_sql_var = f"v{len(sql_vars)}"
                sql_vars[lookup] = table_sql_var
                # In SQL range is 1...stop exclusive, and because we did `-1` in PyRel v1 we need to return it here
                if self._is_duck_db:
                    table_expr = f"LATERAL range(cast({start} as bigint), cast(({stop} + 1) as bigint), cast({step} as bigint))"
                    expr = f"{table_sql_var}.range"
                else:
                    table_expr = f"LATERAL FLATTEN(input => ARRAY_GENERATE_RANGE({start}, ({stop} + 1), {step}))"
                    expr = f"{table_sql_var}.value"
                table_expressions[table_sql_var] = table_expr
                assert isinstance(result, ir.Var), "Fourth argument (result) must be a variable"
                builtin_vars[result] = f"{expr}"
            elif relation == builtins.cast:
                assert len(args) == 3, f"Expected 3 args for `cast`, got {len(args)}: {args}"

                _, original_raw, result = args
                assert isinstance(result, ir.Var), "Third argument (result) must be a variable"

                builtin_vars[result] = original_raw
            elif relation in {builtins.isnan, builtins.isinf}:
                arg_expr = self._var_to_expr(args[0], reference, resolve_builtin_var, var_to_construct)
                expr = "cast('NaN' AS DOUBLE)" if relation == builtins.isnan else "cast('Infinity' AS DOUBLE)"
                wheres.append(sql.Terminal(f"{arg_expr} = {expr}"))
            elif relation == builtins.construct_date:
                assert len(args) == 4, f"Expected 4 args for `construct_date`, got {len(args)}: {args}"
                year_raw, month_raw, day_raw, result = args
                year = self._var_to_expr(year_raw, reference, resolve_builtin_var, var_to_construct)
                month = self._var_to_expr(month_raw, reference, resolve_builtin_var, var_to_construct)
                day = self._var_to_expr(day_raw, reference, resolve_builtin_var, var_to_construct)

                assert isinstance(result, ir.Var), "Fourth argument (result) must be a variable."
                if self._is_duck_db:
                    expr = f"make_date(cast({year} as bigint), cast({month} as bigint), cast({day} as bigint))"
                else:
                    expr = f"date_from_parts({year}, {month}, {day})"
                builtin_vars[result] = expr
            elif relation == builtins.construct_datetime_ms_tz:
                assert len(args) == 9, f"Expected 9 args for `construct_datetime_ms_tz`, got {len(args)}: {args}"

                year_raw, month_raw, day_raw, hour_raw, minute_raw, second_raw, millisecond_raw, tz_raw, result = args
                assert isinstance(result, ir.Var), "Ninth argument (result) must be a variable."

                year = self._var_to_expr(year_raw, reference, resolve_builtin_var, var_to_construct)
                month = self._var_to_expr(month_raw, reference, resolve_builtin_var, var_to_construct)
                day = self._var_to_expr(day_raw, reference, resolve_builtin_var, var_to_construct)
                hour = self._var_to_expr(hour_raw, reference, resolve_builtin_var, var_to_construct)
                minute = self._var_to_expr(minute_raw, reference, resolve_builtin_var, var_to_construct)
                second = self._var_to_expr(second_raw, reference, resolve_builtin_var, var_to_construct)
                millisecond = self._var_to_expr(millisecond_raw, reference, resolve_builtin_var, var_to_construct)
                tz = self._var_to_expr(tz_raw, reference, resolve_builtin_var, var_to_construct)

                if self._is_duck_db:
                    sub_expr = (f"make_timestamp(cast({year} as bigint), cast({month} as bigint), cast({day} as bigint), "
                                f"cast({hour} as bigint), cast({minute} as bigint), cast({second} as bigint) + {millisecond}/1000.0)")
                    if tz.lower() != "'utc'":
                        sub_expr = f"(({sub_expr} at time zone {tz}) at time zone 'UTC')"
                else:
                    sub_expr = (f"to_timestamp_ntz(lpad({year}, 4, '0') || '-' || lpad({month}, 2, '0') || '-' || "
                                f"lpad({day}, 2, '0') || ' ' || lpad({hour}, 2, '0') || ':' || "
                                f"lpad({minute}, 2, '0') || ':' || lpad({second}, 2, '0') || '.' || "
                                f"lpad({millisecond}, 3, '0'), 'YYYY-MM-DD HH24:MI:SS.FF3')")
                    if tz.lower() != "'utc'":
                        sub_expr = f"convert_timezone({tz}, 'UTC', {sub_expr})"
                builtin_vars[result] = f"cast({sub_expr} as DATETIME)"
            elif relation == builtins.infomap:
                raise NotImplementedError("`infomap` is not supported in SQL")
            elif relation == builtins.louvain:
                raise NotImplementedError("`louvain` is not supported in SQL")
            elif relation == builtins.label_propagation:
                raise NotImplementedError("`label_propagation` is not supported in SQL")
            else:
                # Assuming infix binary or ternary operators here
                lhs, rhs = args[0], args[1]
                if relation in builtins.string_binary_builtins:
                    left = self._var_to_expr(lhs, reference, resolve_builtin_var, var_to_construct)
                    if relation == builtins.num_chars and isinstance(rhs, ir.Var):
                        builtin_vars[rhs] = f"length({left})"
                    elif relation == builtins.lower and isinstance(rhs, ir.Var):
                        builtin_vars[rhs] = f"lower({left})"
                    elif relation == builtins.upper and isinstance(rhs, ir.Var):
                        builtin_vars[rhs] = f"upper({left})"
                    elif relation == builtins.strip and isinstance(rhs, ir.Var):
                        builtin_vars[rhs] = f"trim({left})"
                    elif relation == builtins.regex_match:
                        right = self._var_to_expr(rhs, reference, resolve_builtin_var, var_to_construct)
                        # swap left and right for SQL
                        wheres.append(sql.RegexLike(right, left))
                    else:
                        right = self._var_to_expr(rhs, reference, resolve_builtin_var, var_to_construct, False)
                        if relation == builtins.starts_with:
                            expr = f"concat({right}, '%')" if isinstance(rhs, ir.Var) else f"'{right}%'"
                        elif relation == builtins.ends_with:
                            expr = f"concat('%', {right})" if isinstance(rhs, ir.Var) else f"'%{right}'"
                        elif relation == builtins.like_match:
                            expr = right if isinstance(rhs, ir.Var) else f"'{right}'"
                        elif relation == builtins.contains:
                            expr = f"concat('%', {right}, '%')" if isinstance(rhs, ir.Var) else f"'%{right}%'"
                        else:
                            raise Exception(f"Unsupported string builtin relation: {relation}")
                        wheres.append(sql.Like(left, expr))
                elif relation == builtins.levenshtein:
                    assert len(args) == 3, f"Expected 3 args for `levenshtein`, got {len(args)}: {args}"
                    left = self._var_to_expr(lhs, reference, resolve_builtin_var, var_to_construct)
                    right = self._var_to_expr(rhs, reference, resolve_builtin_var, var_to_construct)
                    function = "levenshtein" if self._is_duck_db else "editdistance"
                    assert isinstance(args[2], ir.Var)
                    builtin_vars[args[2]] = f"{function}({left}, {right})"
                elif relation == builtins.concat:
                    assert len(args) == 3, f"Expected 3 args for `concat`, got {len(args)}: {args}"
                    left = self._var_to_expr(lhs, reference, resolve_builtin_var, var_to_construct)
                    right = self._var_to_expr(rhs, reference, resolve_builtin_var, var_to_construct)
                    assert isinstance(args[2], ir.Var)
                    builtin_vars[args[2]] = f"concat({left}, {right})"
                elif relation == builtins.join:
                    assert len(args) == 3, f"Expected 3 args for `join`, got {len(args)}: {args}"
                    assert isinstance(lhs, tuple)
                    f_args = [
                        self._var_to_expr(item, reference, resolve_builtin_var, var_to_construct)
                        for item in lhs
                    ]
                    right = self._var_to_expr(rhs, reference, resolve_builtin_var, var_to_construct)
                    assert isinstance(args[2], ir.Var)
                    builtin_vars[args[2]] = f"concat_ws({right}, {', '.join(f_args)})"
                elif relation == builtins.hash and isinstance(rhs, ir.Var):
                    builtin_vars[rhs] = self._resolve_hash_var(reference, resolve_builtin_var, var_to_construct, lhs)
                elif relation == builtins.string and isinstance(rhs, ir.Var):
                    if isinstance(lhs, ir.Var) and typer.to_base_primitive(lhs.type) == DateTime:
                        lhs = self._var_to_expr(lhs, reference, resolve_builtin_var, var_to_construct)
                        # Convert DateTime to string in the ISO 8601 format.
                        if self._is_duck_db:
                            builtin_vars[rhs] = f"""strftime({lhs}, '%Y-%m-%dT%H:%M:%S.%f')"""
                        else:
                            builtin_vars[rhs] = f"""to_varchar({lhs}, 'YYYY-MM-DD"T"HH24:MI:SS.FF3')"""
                    else:
                        builtin_vars[rhs] = lhs
                elif relation == builtins.parse_float and isinstance(rhs, ir.Var):
                    left = self._var_to_expr(lhs, reference, resolve_builtin_var, var_to_construct)
                    builtin_vars[rhs] = f"cast({left} AS DOUBLE)"
                elif relation == builtins.parse_date:
                    if self._is_duck_db:
                        raise Exception("DuckDB: unsupported builtin relation 'parse_date'.")
                    assert len(args) == 3, f"Expected 3 args for `parse_date`, got {len(args)}: {args}"
                    left = self._var_to_expr(lhs, reference, resolve_builtin_var, var_to_construct)
                    right = self._var_to_expr(rhs, reference, resolve_builtin_var, var_to_construct)
                    assert isinstance(args[2], ir.Var)
                    builtin_vars[args[2]] = f"to_date({left}, {right})"
                elif relation == builtins.parse_datetime:
                    assert len(args) == 3, f"Expected 3 args for `parse_datetime`, got {len(args)}: {args}"
                    left = self._var_to_expr(lhs, reference, resolve_builtin_var, var_to_construct)
                    right = self._var_to_expr(rhs, reference, resolve_builtin_var, var_to_construct)
                    sub_expr = left
                    if 'z' in right:  # this means that out datetime formatter includes timezone, and we need to convert first.
                        if self._is_duck_db:
                            sub_expr = f"({left} AT TIME ZONE 'UTC')"
                        else:
                            sub_expr = f"convert_timezone('UTC', to_timestamp_tz({left}))"
                    assert isinstance(args[2], ir.Var)
                    builtin_vars[args[2]] = f"cast({sub_expr} as DATETIME)"
                elif relation in builtins.date_periods and isinstance(rhs, ir.Var):
                    builtin_vars[rhs] = lhs
                    date_period_var_type[rhs] = relation.name
                elif relation in builtins.date_builtins:
                    if relation in {builtins.date_add, builtins.date_subtract, builtins.datetime_add,
                                    builtins.datetime_subtract}:
                        assert len(args) == 3, f"Expected 3 args for {relation}, got {len(args)}: {args}"
                        assert isinstance(rhs, ir.Var), f"Period variable must be `ir.Var`, got: {rhs}"
                        period = date_period_var_type[rhs]
                        period_val = self._var_to_expr(rhs, reference, resolve_builtin_var, var_to_construct)

                        left = self._var_to_expr(lhs, reference, resolve_builtin_var, var_to_construct)

                        if self._is_duck_db:
                            op = "+" if relation in {builtins.date_add, builtins.datetime_add} else "-"
                            expr = f"({left} {op} {period_val} * interval 1 {period})"
                        else:
                            sign = 1 if relation in {builtins.date_add, builtins.datetime_add} else -1
                            expr = f"dateadd({period}, ({sign} * {period_val}), {left})"

                        result_var = args[2]
                        assert isinstance(result_var, ir.Var), (
                            f"Expected `ir.Var` type for the result of `{relation}`, "
                            f"but got `{type(result_var).__name__}`: {result_var}"
                        )
                        builtin_vars[result_var] = expr
                    # handle binary cases
                    elif len(args) == 2:
                        assert isinstance(rhs, ir.Var), f"Resulting variable must be `ir.Var`, got: {rhs}"
                        expr_map = {
                            builtins.date_year: "year",
                            builtins.date_quarter: "quarter",
                            builtins.date_month: "month",
                            builtins.date_week: "week",
                            builtins.date_day: "day",
                            builtins.date_dayofyear: "dayofyear",
                            builtins.date_weekday: "isodow" if self._is_duck_db else "dayofweekiso",
                            builtins.datetime_second: "second",
                        }
                        expr = expr_map.get(relation)
                        lhs = self._var_to_expr(lhs, reference, resolve_builtin_var, var_to_construct)
                        builtin_vars[rhs] = f"{expr}({lhs})"
                    elif len(args) == 3:
                        result_var = args[2]
                        assert isinstance(result_var, ir.Var), f"Resulting variable must be `ir.Var`, got: {result_var}"
                        expr_map = {
                            builtins.datetime_year: "year",
                            builtins.datetime_quarter: "quarter",
                            builtins.datetime_month: "month",
                            builtins.datetime_week: "week",
                            builtins.datetime_day: "day",
                            builtins.datetime_dayofyear: "dayofyear",
                            builtins.datetime_hour: "hour",
                            builtins.datetime_minute: "minute",
                            builtins.datetime_weekday: "isodow" if self._is_duck_db else "dayofweekiso",
                            builtins.dates_period_days: "date_diff" if self._is_duck_db else "datediff",
                            builtins.datetimes_period_milliseconds: "date_diff" if self._is_duck_db else "datediff"
                        }
                        expr = expr_map.get(relation)
                        lhs = self._var_to_expr(lhs, reference, resolve_builtin_var, var_to_construct)
                        rhs = self._var_to_expr(rhs, reference, resolve_builtin_var, var_to_construct)
                        if relation == builtins.dates_period_days:
                            sub_expr = f"'day', {lhs}, {rhs}" if self._is_duck_db else f"day, {lhs}, {rhs}"
                        elif relation == builtins.datetimes_period_milliseconds:
                            sub_expr = f"'millisecond', {lhs}, {rhs}" if self._is_duck_db else f"millisecond, {lhs}, {rhs}"
                        else:
                            sub_expr = self._convert_timezone(lhs, rhs)
                        builtin_vars[result_var] = f"{expr}({sub_expr})"
                    else:
                        raise NotImplementedError("Unsupported number of arguments for date builtin (3+).")
                elif relation == builtins.construct_date_from_datetime:
                    assert len(args) == 3, f"Expected 3 args for `construct_date_from_datetime`, got {len(args)}: {args}"
                    dt_raw, tz, result = args
                    tz = self._convert_value(tz)

                    assert isinstance(tz, str), "Timezone argument (tz) must be a string."
                    assert isinstance(result, ir.Var), "Third argument (result) must be a variable."

                    # Note that the order of utc and dt is swapped in construct_date_from_datetime and construct_datetime,
                    # because datetime->date (this case) ensures "the datetime is converted to the specified
                    # timezone or offset string before extracting the date", while date->datetime (next case below)
                    # ensures "the datetime is converted to UTC from the specified timezone or offset string."
                    # (quotes are from pyrel0 docs for fromdate and fromdatetime).
                    dt = self._var_to_expr(dt_raw, reference, resolve_builtin_var, var_to_construct)
                    sub_expr = self._convert_timezone(dt, tz)
                    sub_expr = f"cast({sub_expr} AS DATE)"
                    builtin_vars[result] = sub_expr
                elif relation in builtins.math_builtins:
                    result_var = rhs
                    rel_name = relation.name
                    left = self._var_to_expr(lhs, reference, resolve_builtin_var, var_to_construct)
                    if relation in builtins.math_unary_builtins:
                        method = "ln" if rel_name == builtins.natural_log.name else rel_name
                        sub_expr = left
                        if rel_name == builtins.factorial.name and self._is_duck_db:
                            # Factorial requires an integer operand in DuckDB
                            sub_expr = f"{left}::INTEGER"
                        elif rel_name == builtins.log10.name:
                            # log10 is not supported, so we use log with base 10
                            sub_expr = f"10, {left}"
                            method = "log"
                        expr = f"{method}({sub_expr})"
                    elif rel_name in {builtins.minimum.name, builtins.maximum.name, builtins.trunc_div.name,
                                      builtins.power.name, builtins.mod.name, builtins.pow.name,
                                      builtins.log.name}:
                        assert len(args) == 3, f"Expected 3 args for {relation}, got {len(args)}: {args}"

                        result_var = args[2]
                        right = self._var_to_expr(rhs, reference, resolve_builtin_var, var_to_construct)

                        if rel_name == builtins.minimum.name:
                            expr = f"least({left}, {right})"
                        elif rel_name == builtins.maximum.name:
                            expr = f"greatest({left}, {right})"
                        elif rel_name == builtins.trunc_div.name:
                            expr = f"trunc({left} / {right})"
                        elif rel_name == builtins.power.name or rel_name == builtins.pow.name:
                            expr = f"power({left}, {right})"
                        elif rel_name == builtins.log.name:
                            expr = f"log({left}, {right})"
                        else:
                            expr = f"mod({left}, {right})"
                    else:
                        raise Exception(f"Unsupported math builtin relation: {relation}")
                    assert isinstance(result_var, ir.Var), (
                        f"Expected `ir.Var` type for the result of `{relation}`, "
                        f"but got `{type(result_var).__name__}`: {result_var}"
                    )
                    builtin_vars[result_var] = expr
                elif relation in {builtins.parse_int64, builtins.parse_int128} and isinstance(rhs, ir.Var):
                    builtin_vars[rhs] = self._var_to_expr(lhs, reference, resolve_builtin_var, var_to_construct, False)
                elif helpers.is_from_cast(lookup) and isinstance(rhs, ir.Var):
                    # For the `from cast` relations we keep the raw var, and we will ground it later.
                    builtin_vars[rhs] = lhs
                elif isinstance(lhs, ir.Var) and lhs in intermediate_builtin_vars and lhs not in (builtin_vars | var_to_construct):
                    # Example IR:
                    #   Logical
                    #       Logical ^[v0]
                    #           int = 2
                    #           Logical ^[res=None]
                    #               Logical ^[res]
                    #                   cast(Float, int, int_Float)
                    #                   res = 2.1 * int_Float
                    #           v0 = res
                    #       -> derive _match_1(v0)
                    #
                    # In this example, the `int` variable is an intermediate result produced by the `=` (assignment) builtin.
                    # We must retain this value in the `builtin_vars` mapping so it can be used when compiling the `cast`.
                    # Ultimately, this allows us to fully resolve the final expression: `v0 = 2.1 * 2`.
                    builtin_vars[lhs] = self._var_to_expr(rhs, reference, resolve_builtin_var, var_to_construct)
                elif isinstance(rhs, ir.Var) and rhs in intermediate_builtin_vars and rhs not in (builtin_vars | var_to_construct):
                    # Please see the example above but in this case it will be `2 = int` builtin lookup instead of `int = 2`.
                    builtin_vars[rhs] = self._var_to_expr(lhs, reference, resolve_builtin_var, var_to_construct)
                else:
                    left = self._var_to_expr(lhs, reference, resolve_builtin_var, var_to_construct)
                    right = self._var_to_expr(rhs, reference, resolve_builtin_var, var_to_construct)

                    if len(args) == 3:
                        out_var = args[2]
                        if isinstance(out_var, ir.Var):
                            out_var = resolve_builtin_var(out_var)
                            expr = f"({left} {relation_name} {right})"
                            if isinstance(out_var, ir.Var):
                                # For example, when this is an intermediate result
                                # example: c = a - b in the IR is (a - b = d) and (d = c)
                                builtin_vars[out_var] = expr
                            else:
                                # This means that var was already grounded, and we can add a WHERE clause.
                                wheres.append(sql.Terminal(f"{expr} = {out_var}"))
                        else:
                            raise Exception(
                                f"Expected `ir.Var` type for the relation `{relation}` output but got `{type(out_var).__name__}`: {out_var}"
                            )
                    else:
                        # Replace intermediate vars with disjoined expressions
                        expr = f"{left} {relation_name} {right}"
                        wheres.append(sql.Terminal(expr))

        # After handling all builtins we need to generate where statements for args with single lookup.
        for arg, lookup_set in var_lookups.items():
            if len(lookup_set) == 1:
                lookup = lookup_set[0]
                column = var_column[cast(ir.Var, arg), lookup]
                column_name = self._var_name(lookup.relation.id, column)
                ref = f"{sql_vars[lookup]}.{column_name}"
                # case when we have a builtin operation as a relation argument
                #   example: `test(a - 1, b)` and we are handling here `a - 1` arg.
                if arg in builtin_vars:
                    rhs_ref = resolve_builtin_var(arg)
                    if isinstance(rhs_ref, ir.Var):
                        rhs = reference(rhs_ref) if rhs_ref in var_lookups else rhs_ref.name
                    elif isinstance(rhs_ref, ir.Literal):
                        rhs = self._convert_value(rhs_ref.value)
                    else:
                        rhs = str(rhs_ref)
                    wheres.append(sql.Terminal(f"{ref} = {rhs}"))

        return builtin_vars, wheres, table_expressions

    def _convert_timezone(self, dt: str, tz: str) -> str:
        if tz.lower() != "'utc'":
            if self._is_duck_db:
                return f"({dt} at time zone 'UTC') at time zone {tz}"
            else:
                return f"convert_timezone('UTC', {tz}, {dt})"
        return dt

    def _process_builtin_table_expressions(self, builtin_table_expressions: dict[str, str]):
        """Convert builtin table expressions into SQL FROM clauses."""
        return [
            sql.From(expr, alias)
            for alias, expr in builtin_table_expressions.items()
        ]

    def _process_constructs(self, lookups: OrderedSet[ir.Lookup], var_lookups: dict[ir.Var, OrderedSet[ir.Lookup]],
                            var_column: dict[Tuple[ir.Var, ir.Lookup], ir.Field], sql_vars: dict[ir.Lookup, str],
                            builtin_vars: dict[ir.Var, ir.Value|str|int], var_to_construct: dict[ir.Var, ir.Construct]) -> list[sql.Expr]:
        """
        Handles `filter_by` constructs that require generating SQL `WHERE` conditions.

        Example:

            QB:
                Name = m.Concept('Name', extends=[str])
                Bank = m.Concept('Bank', identify_by={'name': Name})

                where(Bank.filter_by(name="Chase")).select(Bank)

            IR:
                construct(Bank, "name"::String, "Chase"::String, bank::Bank)
                Bank(bank::Bank)

            SQL:
                ... FROM Bank v0
                WHERE v0.bank = hash('Bank', 'name', 'Chase')
        """

        wheres: list[sql.Expr] = []

        reference = partial(self._var_reference, var_lookups, sql_vars, var_column)
        resolve_builtin_var = partial(self._resolve_builtin_var, builtin_vars)

        seen_vars: set[ir.Var] = set()

        for lookup in lookups:
            relation = lookup.relation
            for j, arg in enumerate(lookup.args):
                if isinstance(arg, ir.Var) and arg in var_to_construct and arg not in seen_vars:
                    seen_vars.add(arg)

                    rel_field = relation.fields[j]
                    ref = f"{sql_vars[lookup]}.{self._var_name(relation.id, rel_field)}"

                    construct = var_to_construct[arg]
                    construct_expr = self._resolve_construct_var(
                        reference, resolve_builtin_var, var_to_construct, construct
                    )

                    wheres.append(sql.Terminal(f"{ref} = {construct_expr}"))

        return wheres

    def _generate_where_clauses(self, var_lookups: dict[ir.Var, OrderedSet[ir.Lookup]],
                                var_column: dict[Tuple[ir.Var, ir.Lookup], ir.Field], sql_vars: dict[ir.Lookup, str],
                                union_lookups: dict[ir.Union, OrderedSet[ir.Lookup]]):
        # Reverse mapping: lookup -> union
        lookup_to_union: dict[ir.Lookup, ir.Union] = {}
        for union, lookups in union_lookups.items():
            for lu in lookups:
                lookup_to_union[lu] = union

        wheres: list[sql.Expr] = []
        plain_refs_by_var: dict[ir.Var, list[str]] = defaultdict(list)
        all_union_members: dict[str, dict[ir.Var, str]] = defaultdict(dict)
        for arg, lookup_set in var_lookups.items():
            # if there are 2 lookups for the same variable, we need a join
            if len(lookup_set) > 1:
                # Step 1: Collect all lookups by union member or plain
                for lu in lookup_set:
                    col = var_column[arg, lu]
                    col_name = self._var_name(lu.relation.id, col)

                    matched_union = lookup_to_union.get(lu)
                    if matched_union:
                        for u_lu in union_lookups[matched_union]:
                            u_ref = f"{sql_vars[u_lu]}.{col_name}"
                            all_union_members[sql_vars[u_lu]][arg] = u_ref
                    else:
                        ref = f"{sql_vars[lu]}.{col_name}"
                        plain_refs_by_var[arg].append(ref)

        # Step 2: Build AND chain of plain lookups
        and_clauses = []
        for refs in plain_refs_by_var.values():
            # join variable references pairwise (e.g. "x.id = y.id AND y.id = z.id")
            for lhs, rhs in zip(refs, refs[1:]):
                and_clauses.append(sql.Terminal(f"{lhs} = {rhs}"))

        # Step 3: Build one OR clause across union members
        or_groups: list[sql.Expr] = []
        for member_ref_map in all_union_members.values():
            expressions = []
            for arg_var, rhs in member_ref_map.items():
                plain_refs = plain_refs_by_var.get(arg_var)
                if plain_refs:
                    lhs = plain_refs[-1]  # last plain ref for that var
                    expressions.append(sql.Terminal(f"{lhs} = {rhs}"))
            if expressions:
                or_groups.append(sql.And(expressions) if len(expressions) > 1 else expressions[0])

        wheres.extend(and_clauses)
        if or_groups:
            wheres.append(sql.Or(or_groups))

        return wheres

    def _process_wheres_clauses(self, wheres: list[sql.Expr]) -> Optional[sql.Where]:
        # conjunction of not_wheres
        if len(wheres) == 0:
            where = None
        elif len(wheres) == 1:
            where = sql.Where(wheres[0])
        else:
            where = sql.Where(sql.And(wheres))
        return where

    def _generate_select_output(self, outputs: list[OutputVar], builtin_vars: dict[ir.Var, ir.Value|str|int],
                                sql_vars: dict[ir.Lookup, str], var_column: dict[Tuple[ir.Var, ir.Lookup], ir.Field],
                                var_lookups: dict[ir.Var, OrderedSet[ir.Lookup]],
                                var_to_construct: dict[ir.Var, ir.Construct]):

        reference = partial(self._var_reference, var_lookups, sql_vars, var_column)
        resolve_builtin_var = partial(self._resolve_builtin_var, builtin_vars)

        def handle_lookup_var(var, var_type, alias):
            lookup = var_lookups[var].some()
            relation = lookup.relation
            var_name = sql_vars[lookup]
            column_name = self._var_name(relation.id, var_column[var, lookup])
            vars.append(sql.VarRef(var_name, column_name, alias, var_type))
            if from_cdc_annotation in relation.annotations:
                not_null_vars.add(f"{var_name}.{column_name}")

        def handle_construct(construct):
            # Generate constructions like hash(`x`, `y`, TABLE_ALIAS.COLUMN_NAME)
            elements = []
            for val in construct.values:
                if val in builtin_vars:
                    val = resolve_builtin_var(val)
                    if isinstance(val, str):
                        # In case we parsed builtin into some expression, we may add it as an element.
                        # For example, `TO_DATE('1990-1-1', 'Y-m-d')` or `(v1.value + 5)`.
                        elements.append(f"{val}")
                        continue
                if isinstance(val, ir.Var):
                    if val in var_to_construct:
                        elements.append(handle_construct(var_to_construct[val]))
                    else:
                        lookup = var_lookups[val].some()
                        column_name = self._var_name(lookup.relation.id, var_column[val, lookup])
                        lookup_var = f"{sql_vars[lookup]}.{column_name}"
                        elements.append(lookup_var)
                        if from_cdc_annotation in lookup.relation.annotations:
                            not_null_vars.add(lookup_var)
                else:
                    elements.append(str(self._convert_value(val)))
            return f"hash({', '.join(elements)})"

        # finally, compute what the select will return
        vars = []
        not_null_vars = ordered_set()
        for output in outputs:
            alias, var, var_type, task = output.alias, output.value, output.value_type, output.task
            if isinstance(var, ir.Var):
                if var in var_lookups and not task:
                    handle_lookup_var(var, var_type, alias)
                elif var in builtin_vars:
                    var_ref = resolve_builtin_var(var)
                    if var_ref in var_lookups:
                        # Case: result of `cast` variable
                        handle_lookup_var(var_ref, var_type, alias)
                    elif isinstance(var_ref, ir.Literal):
                        # Case: literal value from `cast` relation, e.g. `decimal(0)`
                        vars.append(sql.VarRef(str(self._convert_value(var_ref.value)), alias=alias, type=var_type))
                    else:
                        # Example: We may have `decimal(0)` in QB which turns in IR into:
                        #   (cast(Decimal128, 0, vDecimal128) and decimal128(vDecimal128, res_3))
                        #   and we need to make it `0` in SQL.
                        var_ref = var_ref.name if isinstance(var_ref, ir.Var) else str(var_ref)
                        vars.append(sql.VarRef(var_ref, alias=alias, type=var_type))
                elif task:
                    if isinstance(task, ir.Construct):
                        # Generate constructions like hash(`x`, `y`, TABLE_ALIAS.COLUMN_NAME) as `alias`
                        vars.append(sql.VarRef(handle_construct(task), alias=alias, type=var_type))
                    elif isinstance(task, ir.Aggregate):
                        result_arg = task.projection[-1] if task.aggregation == builtins.count else task.args[0]
                        result_arg = resolve_builtin_var(result_arg)
                        ref = reference(result_arg) if isinstance(result_arg, ir.Var) else str(result_arg)
                        vars.append(sql.VarRef(str(ref), alias=alias, type=var_type))
                    elif isinstance(task, ir.Union):
                        # Handle `COALESCE` of all lookups of this var from the union
                        lookups = self._extract_all_lookups_from_union(task)
                        elements = []

                        for lu in lookups:
                            if any(isinstance(arg, ir.Var) and arg == var for arg in lu.args):
                                column_name = self._var_name(lu.relation.id, var_column[var, lu])
                                elements.append(f"{sql_vars[lu]}.{column_name}")

                        expr = "COALESCE(" + ", ".join(elements) + ")"
                        vars.append(sql.VarRef(expr, alias=alias, type=var_type))
            else:
                # TODO - abusing even more here, because var is a value!
                vars.append(sql.VarRef(str(self._convert_value(var)), alias=alias, type=var_type))
        return not_null_vars, vars

    def _generate_select_nots(self, nots: Optional[list[ir.Not]], var_lookups: dict[ir.Var, OrderedSet[ir.Lookup]],
                              sql_vars: dict[ir.Lookup, str], var_column:dict[Tuple[ir.Var, ir.Lookup], ir.Field],
                              index: int) -> tuple[list[sql.NotExists], int]:
        not_exists = []
        if nots:
            for not_expr in nots:
                unions = []
                inner_nots = []
                constructs = []
                if isinstance(not_expr.task, ir.Lookup):
                    all_lookups = [not_expr.task]
                else:
                    logical = cast(ir.Logical, not_expr.task)
                    all_lookups = cast(list[ir.Lookup], filter_by_type(logical.body, ir.Lookup))
                    logicals = cast(list[ir.Logical], filter_by_type(logical.body, ir.Logical))
                    inner_nots = cast(list[ir.Not], filter_by_type(logical.body, ir.Not))
                    unions = cast(list[ir.Union], filter_by_type(logical.body, ir.Union))
                    constructs = cast(list[ir.Construct], filter_by_type(logical.body, ir.Construct))

                    # Some of the lookup relations we wrap into logical and we need to get them out for the SQL compilation.
                    #    For example QB `decimal(0)` in IR will look like this:
                    #        Logical ^[res]
                    #           Exists(vDecimal128)
                    #               Logical
                    #                   cast(Decimal128, 0, vDecimal128)
                    #                   decimal128(vDecimal128, res)
                    if logicals:
                        unions = self._extract_all_of_type_from_logicals(logicals, ir.Union) + unions
                        all_lookups = self._extract_all_of_type_from_logicals(logicals, ir.Lookup) + all_lookups

                union_lookups: dict[ir.Union, OrderedSet[ir.Lookup]] = self._extract_all_lookups_per_union(unions)
                all_lookups.extend(list(chain.from_iterable(union_lookups.values())))

                lookups = OrderedSet.from_iterable(t for t in all_lookups if not builtins.is_builtin(t.relation))
                froms, wheres, not_sql_vars, not_var_column, not_var_lookups = self._extract_lookups_metadata(lookups, index)
                index += len(not_sql_vars)

                all_sql_vars = {**sql_vars, **not_sql_vars}
                all_var_column = {**var_column, **not_var_column}
                all_var_lookups = {**var_lookups, **not_var_lookups}

                var_to_construct = {c.id_var: c for c in constructs} if constructs else {}
                builtin_lookups = OrderedSet.from_iterable(t for t in all_lookups if builtins.is_builtin(t.relation))
                builtin_vars, builtin_wheres, builtin_table_expressions = (
                    self._resolve_builtins(builtin_lookups, all_var_lookups, all_var_column, all_sql_vars, var_to_construct))

                froms.extend(self._process_builtin_table_expressions(builtin_table_expressions))

                wheres.extend(builtin_wheres)

                construct_wheres = self._process_constructs(lookups, var_lookups, var_column, sql_vars, builtin_vars,
                                                            var_to_construct)
                wheres.extend(construct_wheres)

                # We need to join the not exists select with the outside select query context
                for arg, lookup_set in not_var_lookups.items():
                    if len(lookup_set) > 0:
                        lu = lookup_set[0]
                        column = not_var_column[cast(ir.Var, arg), lu]
                        column_name = self._var_name(lu.relation.id, column)
                        lhs = f"{not_sql_vars[lu]}.{column_name}"

                        # lookup the same var from the outside context to make the join
                        matching_lookup = next(
                            (lookup for (var, lookup) in var_column if var == arg),
                            None
                        )

                        if matching_lookup is not None:
                            matching_column = var_column[(arg, matching_lookup)]
                            matching_column_name = self._var_name(matching_lookup.relation.id, matching_column)
                            rhs = f"{sql_vars[matching_lookup]}.{matching_column_name}"
                            wheres.append(sql.Terminal(f"{lhs} = {rhs}"))

                wheres.extend(self._generate_where_clauses(not_var_lookups, not_var_column, not_sql_vars, union_lookups))

                inner_not_exists, index = self._generate_select_nots(inner_nots, not_var_lookups, not_sql_vars, not_var_column, index)
                wheres.extend(inner_not_exists)

                where = self._process_wheres_clauses(wheres)
                not_exists.append(sql.NotExists(sql.Select(False, [1], froms, where)))

        return not_exists, index

    def _extract_all_of_type_from_logical(self, task: ir.Logical, target_type: type) -> list:
        """Recursively extract all instances of `target_type` from a Logical task."""
        return self._extract_all_of_type_from_logicals([task], target_type)

    def _extract_all_of_type_from_logicals(self, logicals: list[ir.Logical], target_type: type) -> list:
        """Recursively extract all instances of `target_type` from a list of Logical tasks."""
        result = ordered_set()

        def visit(logical: ir.Logical):
            for expr in logical.body:
                if isinstance(expr, ir.Logical):
                    visit(expr)
                elif isinstance(expr, target_type):
                    result.add(expr)

        for logical in logicals or []:
            visit(logical)

        return result.list if result.list else []

    def _extract_all_lookups_per_union(self, unions: Optional[list[ir.Union]]) -> dict[ir.Union, OrderedSet[ir.Lookup]]:
        return {
            union: self._extract_all_lookups_from_union(union)
            for union in unions or []
        }

    def _extract_all_lookups_from_union(self, union: ir.Union) -> OrderedSet[ir.Lookup]:
        lookups: OrderedSet[ir.Lookup] = OrderedSet()
        for task in union.tasks:
            if isinstance(task, ir.Logical):
                lookups.update(self._extract_all_of_type_from_logicals([task], ir.Lookup))
            elif isinstance(task, ir.Lookup):
                lookups.add(cast(ir.Lookup, task))
        return lookups

    def _extract_all_not_null_vars_from_nots(self, nots: Optional[list[ir.Not]]) -> set[ir.Var]:
        vars: set[ir.Var] = set()
        null_vars: set[ir.Var] = set()

        def visit(task):
            if isinstance(task, ir.Not):
                visit(task.task)
            elif isinstance(task, ir.Logical):
                for var in task.hoisted:
                    if isinstance(var, ir.Var):
                        vars.add(var)
                    elif isinstance(var, ir.Default):
                        (vars if var.value is not None else null_vars).add(var.var)
                for subtask in task.body:
                    visit(subtask)
            elif isinstance(task, ir.Lookup):
                vars.update(arg for arg in task.args if isinstance(arg, ir.Var))

        for not_task in nots or []:
            visit(not_task)

        return vars - null_vars

    def _var_to_expr(self, var, reference, resolve_builtin_var, var_to_construct: dict[ir.Var, ir.Construct],
                     quote_strings: bool = True):
        """
        Convert a variable to an expression string.
        """
        if isinstance(var, ir.Var) and var in var_to_construct:
            return self._resolve_construct_var(reference, resolve_builtin_var, var_to_construct, var_to_construct[var])
        resolved = resolve_builtin_var(var)
        if isinstance(resolved, ir.Var):
            return reference(resolved)
        elif isinstance(resolved, ir.Literal):
            return str(self._convert_value(resolved, quote_strings=quote_strings))
        elif isinstance(resolved, int):
            return str(resolved)
        else:
            return str(resolved) if isinstance(var, ir.Var) or not quote_strings else f"'{resolved}'"

    def _get_update_aliases(self, update: ir.Update, var_to_construct, var_to_union, skip_type:bool=False):
        relation = update.relation
        return [
            self._get_alias(
                self._var_name(relation.id, f),
                arg,
                self._convert_type(f.type) if not skip_type else None,
                var_to_construct,
                var_to_union,
            )
            for f, arg in zip(relation.fields, update.args)
        ]

    def _get_alias(self, key, arg, arg_type, var_to_construct, var_to_union):
        if not isinstance(arg, ir.Var):
            return OutputVar(arg, key, arg_type)

        return OutputVar(arg, key, arg_type, var_to_construct.get(arg) or var_to_union.get(arg))

    def _get_tuples(self, logical: ir.Logical, u: ir.Update):
        """
        Get a list of tuples to perform this update.

        This function traverses the update args, assuming they contain only static values or
        variables bound to a construct task, and generates a list of tuples to insert. There
        may be multiple tuples because arguments can be lists of values bound to a field
        whose role is multi.
        """
        # TODO - this only works if the variable is bound to a Construct task, we need a more general approach.

        def find_construct(var):
            for stmt in logical.body:
                if isinstance(stmt, ir.Construct) and stmt.id_var == var:
                    return stmt
            return None

        def resolve_value(arg):
            if isinstance(arg, ir.Var):
                construct = find_construct(arg)
                if not construct:
                    return self._convert_value(arg)

                resolved = []
                for val in construct.values:
                    if isinstance(val, ir.Var):
                        inner_construct = find_construct(val)
                        if inner_construct:
                            nested = [str(self._convert_value(x)) for x in inner_construct.values]
                            resolved.append(f"hash({', '.join(nested)})")
                        else:
                            resolved.append(str(self._convert_value(val)))
                    else:
                        resolved.append(str(self._convert_value(val)))

                return f"hash({', '.join(resolved)})"
            elif isinstance(arg, FrozenOrderedSet):
                return frozen(*[self._convert_value(v) for v in arg])
            else:
                return self._convert_value(arg)

        values = [resolve_value(a) for a in u.args]
        return self._product(values)

    def _product(self, values):
        """ Compute a cartesian product of values when the value is a FrozenOrderedSet. """
        # TODO - some pass needs to check that this is correct, i.e. that we are using a
        # FrozenOrderedSet only if the field is of role multi.
        tuples = [[]]
        for value in values:
            if isinstance(value, FrozenOrderedSet):
                tuples = [prev + [element] for prev in tuples for element in value]
            else:
                tuples = [prev + [value] for prev in tuples]
        return [tuple(t) for t in tuples]

    def _convert_value(self, v, quote_strings:bool=True) -> str|int:
        """ Convert the literal value in v to a SQL value."""
        if isinstance(v, str):
            return f"'{v}'" if quote_strings else v
        if isinstance(v, PyDecimal):
            return str(v)
        if isinstance(v, ir.ScalarType):
            return f"'{v.name}'"
        if isinstance(v, ir.Literal):
            if v.type == types.Date:
                return f"cast('{v.value}' as date)"
            if v.type == types.DateTime:
                return f"cast('{v.value}' as datetime)"
            return self._convert_value(v.value, quote_strings)
        if isinstance(v, float):
            if math.isnan(v):
                return "cast('NaN' as DOUBLE)"
            elif v == float("inf"):
                return "cast('Infinity' as DOUBLE)"
            elif v == float("-inf"):
                return "cast('-Infinity' as DOUBLE)"
            return str(v)
        if isinstance(v, datetime.datetime):
            return f"cast('{v}' as datetime)"
        if isinstance(v, datetime.date):
            return f"cast('{v}' as date)"
        if isinstance(v, bool):
            return str(v).lower()
        if isinstance(v, int):
            return v
        return str(v)

    COMMON_CONVERSION = {
        Hash: "DECIMAL(38, 0)",
        String: "TEXT",
        Number: "DOUBLE",
        Bool: "BOOLEAN",
        Date: "DATE",
        DateTime: "DATETIME",
        Float: "FLOAT(53)",
        RowId: "NUMBER(38, 0)", # NUMBER(38,0) cannot hold the full UInt128 range — it can only go up to about 2¹²⁶. We need to find something better.
        UInt128: "NUMBER(38, 0)" # NUMBER(38,0) cannot hold the full UInt128 range — it can only go up to about 2¹²⁶. We need to find something better.
    }
    SNOWFLAKE_OVERRIDES = {
        Int64: "NUMBER(19, 0)",
        Int128: "NUMBER(38, 0)",
    }
    DUCKDB_OVERRIDES = {
        Int64: "BIGINT",
        Int128: "HUGEINT",
    }
    SF_BUILTIN_CONVERSION = {**COMMON_CONVERSION, **SNOWFLAKE_OVERRIDES}
    DUCKDB_BUILTIN_CONVERSION = {**COMMON_CONVERSION, **DUCKDB_OVERRIDES}
    def _convert_type(self, t: ir.Type) -> str:
        """ Convert the type t into the equivalent SQL type."""
        # entities become DECIMAL(38, 0)
        if not types.is_builtin(t) and not types.is_value_type(t):
            return "DECIMAL(38, 0)"

        # convert known builtins
        base_type = typer.to_base_primitive(t)
        if isinstance(base_type, ir.ScalarType):
            if self._is_duck_db and base_type in self.DUCKDB_BUILTIN_CONVERSION:
                return self.DUCKDB_BUILTIN_CONVERSION[base_type]
            elif base_type in self.SF_BUILTIN_CONVERSION:
                return self.SF_BUILTIN_CONVERSION[base_type]
        if isinstance(base_type, ir.DecimalType):
            return f"DECIMAL({base_type.precision},{base_type.scale})"
        raise Exception(f"Unknown built-in type: {t}")

    def _get_relations(self, model: ir.Model) -> Tuple[list[ir.Relation], list[ir.Relation]]:
        rw = ReadWriteVisitor()
        model.accept(rw)

        root = cast(ir.Logical, model.root)

        # For query compilation exclude read-only tables because we do not need to declare `CREATE TABLE` statements
        used_relations = rw.writes(root) if self._query_compilation else rw.writes(root) | rw.reads(root)

        # Filter only relations that require table creation
        table_relations = [
            r for r in used_relations
            if self._is_table_creation_required(r)
        ]

        used_builtins = [
            r for r in rw.reads(root)
            if builtins.is_builtin(r)
        ]

        return table_relations, used_builtins

    def _is_table_creation_required(self, r: ir.Relation) -> bool:
        """
        Determine whether the given relation should result in a SQL table creation.

        Skips creation for:
        - Built-in relations or annotations
        - CDC relations
        - Boxed types or special "rank" name
        - Relations with unresolved field types (types.Any)
        - ValueType population relations
        """
        if (
            builtins.is_builtin(r) or
            builtins.is_annotation(r) or
            from_cdc_annotation in r.annotations or
            r.name == "rank" or
            # TODO: revisit this during `RAI-39124`. For now we filter out all error relations.
            self._is_error_relation(r)
        ):
            return False

        if any(relation_field.type == types.Any for relation_field in r.fields):
            if not r.overloads:
                raise ValueError(f"Relation '{r.name}' has unresolved field types (`types.Any`) and no overloads.")
            return False

        return not self._is_value_type_population_relation(r)

    def _is_error_relation(self, r: ir.Relation) -> bool:
        return r.name in self._error_relation_names or self._relation_name(r).startswith('error_')

    @staticmethod
    def _is_value_type_population_relation(r: ir.Relation) -> bool:
        """
        Check if the relation is a ValueType population relation:
        - Has exactly one field
        - Field type is a value type
        - Annotated with concept_relation_annotation
        """
        if not r.fields or len(r.fields) != 1:
            return False
        return types.is_value_type(r.fields[0].type) and concept_relation_annotation in r.annotations

    def _relation_name(self, relation: ir.Relation):
        if helpers.is_external(relation) or helpers.builtins.is_builtin(relation):
            return relation.name
        return self.relation_name_cache.get_name(relation.id, helpers.sanitize(relation.name), helpers.relation_name_prefix(relation))

    def _register_external_relations(self, model: ir.Model):
        # force all external relations to get a name in the cache, so that internal relations
        # cannot use those names in _relation_name
        for r in model.relations:
            if helpers.is_external(r):
                self.relation_name_cache.get_name(r.id, r.name)

    def _get_relation_info(self, relation: ir.Relation) -> RelationInfo:
        if relation not in self.relation_infos:
            self.relation_infos[relation] = RelationInfo()
        return self.relation_infos[relation]

    def mark_used(self, relation: ir.Relation):
        self._get_relation_info(relation).used = True

    def add_table_select(self, relation: ir.Relation, select: sql.Select):
        self._get_relation_info(relation).table_selects.append(select)

    def add_view_select(self, relation: ir.Relation, select: sql.Select):
        self._get_relation_info(relation).view_selects.append(select)

    def add_dynamic_table_select(self, relation: ir.Relation, select: sql.Select):
        self._get_relation_info(relation).dynamic_table_selects.append(select)

    def _var_name(self, relation_id: int, arg: Union[ir.Var, ir.Field]):
        name = helpers.sanitize(self.relation_arg_name_cache.get_name((relation_id, arg.id), arg.name))
        return f'"{name}"' if name.lower() in {"any", "order"} else name

    def _register_relation_args(self, relations: list[ir.Relation]):
        """
        Register all relation arguments in the cache to ensure they have unique names.
        This is necessary for SQL compilation to avoid name collisions.
        """
        self.relation_arg_name_cache = NameCache()
        for r in relations:
            for rel_field in r.fields:
                self.relation_arg_name_cache.get_name((r.id, rel_field.id), rel_field.name)

    def _sort_builtin_lookups(self, lookups: list[ir.Lookup], output_vars: set[ir.Var]) -> list[ir.Lookup]:
        # Process lookups with output vars at last because they depend on other builtin lookups.
        lookups_with_output_vars = [lookup for lookup in lookups if builtins.is_eq(lookup.relation)
                                    and any(arg in output_vars for arg in lookup.args)]
        other_lookups = [lookup for lookup in lookups if lookup not in lookups_with_output_vars]

        sorted_lookups = topological_sort(other_lookups, self._build_builtin_lookups_dependencies(other_lookups))

        return sorted_lookups + lookups_with_output_vars

    @staticmethod
    def _build_builtin_lookups_dependencies(lookups: list[ir.Lookup]) -> list[Tuple[ir.Lookup, ir.Lookup]]:
        """
        Builds dependency edges for topological_sort:
        1. Terminal comparisons (neq, gt, lt, gte, lte) come last.
        2. Conditionals (starts_with, contains, etc.) come after basic lookups but before terminals.
        3. eq with only constants comes first.
        4. eq with two vars must wait until one of them is grounded.
        5. A lookup whose last argument is used non-terminally in another must come first.
        6. For builtins that take multiple input arguments (like range, concat, substring, etc.),
            ensure that all non-terminal arguments are processed before the builtin that consumes them.
        """

        edges = []
        arg_usages = defaultdict(list)  # arg -> List[(lookup, position)]

        terminal_relations = {
            builtins.neq.name, builtins.gt.name, builtins.lt.name, builtins.gte.name, builtins.lte.name
        }

        conditional_relations = {
            builtins.starts_with.name, builtins.ends_with.name, builtins.contains.name, builtins.like_match.name
        }

        # Step 1: Collect argument usage positions
        for lookup in lookups:
            for idx, arg in enumerate(lookup.args):
                arg_usages[arg].append((lookup, idx))

        # Step 2: Add edges based on lookup semantics
        for lookup in lookups:
            relation_name = lookup.relation.name
            args = lookup.args

            # Rule 1: Terminal relations depend on everything else
            if relation_name in terminal_relations:
                for other in lookups:
                    other_name = other.relation.name
                    if other is not lookup and other_name not in terminal_relations:
                        edges.append((other, lookup))
                continue  # skip rest of rules for terminal lookups

            # Rule 2: Conditional relations go before terminals, but after others
            if relation_name in conditional_relations:
                for other in lookups:
                    if other is not lookup:
                        other_name = other.relation.name
                        if other_name not in terminal_relations and other_name not in conditional_relations:
                            edges.append((other, lookup))  # only non-conditional, non-terminal
                continue

            if relation_name == builtins.eq.name:
                var_args = [arg for arg in args if isinstance(arg, ir.Var)]

                # Rule 3: eq with only constants comes first
                if len(var_args) == 1:
                    # This lookup defines a var — should come before any that use this var non-terminally
                    grounded_var = var_args[0]
                    for other, pos in arg_usages[grounded_var]:
                        if other is not lookup:
                            if pos != len(other.args) - 1:
                                edges.append((lookup, other))
                    continue  # skip adding other edges among terminal assignments like a=2, b=2

                # Rule 4: eq with two vars must wait until one of them is grounded
                elif len(var_args) == 2:
                    # eq(x, y): both are vars — lookup must come after those grounding either var
                    for var in var_args:
                        for other, pos in arg_usages[var]:
                            if other is not lookup:
                                if other.args[-1] == var:
                                    edges.append((other, lookup))
                    continue

            # In generate builtins has a single output var but `split` returns `index` and `part`
            num_outputs = 2 if lookup.relation == builtins.split else 1

            # Rule 5: last output args must go first if used elsewhere non-terminally
            for out_arg in args[-num_outputs:]:
                for other, pos in arg_usages.get(out_arg, []):
                    if other is not lookup and pos != len(other.args) - 1:
                        edges.append((lookup, other))

            # Rule 6: builtins with multiple input args must wait until all input args are grounded,
            #   for example, range(start, end, step, result)
            if len(args) > num_outputs:
                for input_arg in args[:-num_outputs]:
                    for other, pos in arg_usages.get(input_arg, []):
                        if other is not lookup:
                            other_name = other.relation.name
                            if other_name not in terminal_relations and other_name not in conditional_relations:
                                # Ensure any lookup that defines this arg (as last) comes before
                                if other.args[-1] == input_arg:
                                    edges.append((other, lookup))

        return edges

    def _union_output_selects(self, statements: list[sql.Node]) -> list[sql.Node]:
        """Group consecutive sql.Select nodes into a single sql.UnionAllSelect if there is multiple."""
        result: list[sql.Node] = []
        selects: list[sql.Select] = []

        for statement in statements:
            if isinstance(statement, sql.Select):
                selects.append(statement)
            else:
                result.append(statement)

        if selects:
            if len(selects) > 1:
                result.append(sql.UnionAllSelect(selects))
            else:
                result.extend(selects)

        return result

    def _sort_dependencies(self, statements: list[sql.Node]) -> list[sql.Node]:
        """
            Sorts SQL statements to ensure proper execution order:
            1. CREATE TABLE statements
            2. INSERT statements and CREATE VIEW (topologically sorted by dependencies)
            3. UPDATE statements
            3. Other statements except SELECT queries
            4. SELECT queries
        """
        udfs = []
        create_tables = []
        need_sort: dict[str, list[Union[sql.Insert, sql.CreateView, sql.CreateDynamicTable]]] = defaultdict(list)
        updates = []
        miscellaneous_statements = []
        selects = []

        for statement in statements:
            if isinstance(statement, sql.CreateTable):
                create_tables.append(statement)
            elif isinstance(statement, sql.Insert):
                need_sort[statement.table].append(statement)
            elif isinstance(statement, sql.CreateView):
                need_sort[statement.name].append(statement)
            elif isinstance(statement, sql.CreateDynamicTable):
                need_sort[statement.name].append(statement)
            elif isinstance(statement, sql.Update):
                updates.append(statement)
            elif isinstance(statement, sql.Select):
                selects.append(statement)
            elif isinstance(statement, sql.CreateFunction):
                udfs.append(statement)
            else:
                miscellaneous_statements.append(statement)

        sorted_statements = self._sort_statements_dependency_graph(need_sort)

        return udfs + create_tables + sorted_statements + updates + miscellaneous_statements + selects

    @staticmethod
    def _sort_statements_dependency_graph(statements: dict[str, list[Union[sql.Insert, sql.CreateView, sql.CreateDynamicTable]]]) -> list[sql.Insert]:
        """ Topologic sort INSERT and CREATE VIEW statements based on dependencies in their SELECT FROM clauses. """
        edges = ordered_set()
        nodes = OrderedSet.from_iterable(statements.keys())

        def extract_dependencies(select: Optional[sql.Select], target_table: str):
            """Recursively extract dependency edges from FROM, JOIN, and WHERE clauses."""
            if not select:
                return

            def register_dependency(source_table: str):
                edges.add((source_table, target_table))
                nodes.add(source_table)

            # Process FROM clause
            if select.froms:
                if isinstance(select.froms, sql.Select):  # Single sub-select
                    extract_dependencies(select.froms, target_table)
                else:
                    for from_clause in select.froms:
                        register_dependency(from_clause.table)

            # Process JOIN clause
            if select.joins:
                for join in select.joins:
                    register_dependency(join.table)

            # Process WHERE clause recursively
            def _extract_from_expr(expr: sql.Expr):
                if isinstance(expr, sql.NotExists):
                    extract_dependencies(expr.expr, target_table)
                elif isinstance(expr, (sql.And, sql.Or)):
                    for sub_expr in expr.expr:
                        _extract_from_expr(sub_expr)

            if select.where and select.where.expression:
                _extract_from_expr(select.where.expression)

        for target_table, table_statements in statements.items():
            for statement in table_statements:
                if statement.query:
                    query = statement.query
                    if isinstance(query, list):
                        for sub_query in query:
                            extract_dependencies(sub_query, target_table)
                    elif isinstance(query, sql.Select):
                        extract_dependencies(query, target_table)
                    elif isinstance(query, sql.CTE):
                        for select in query.selects:
                            extract_dependencies(select, target_table)

        sorted_tables = topological_sort(list(nodes), list(edges))

        sorted_statements = []
        for table in sorted_tables:
            if table in statements:
                sorted_statements.extend(statements.get(table, []))

        return sorted_statements

class RecursiveLookupsRewriter(v.Rewriter):
    def __init__(self, recursive_relation: ir.Relation, new_recursive_relation: ir.Relation):
        super().__init__()
        self._recursive_relation:ir.Relation = recursive_relation
        self._new_recursive_relation:ir.Relation = new_recursive_relation

    def handle_lookup(self, node: ir.Lookup, parent: ir.Node):
        if node.relation == self._recursive_relation:
            return node.reconstruct(node.engine, self._new_recursive_relation, node.args, node.annotations)
        return node

class DerivedRelationsVisitor(v.Visitor):
    _is_derived: bool = True

    def is_derived(self) -> bool:
        return self._is_derived

    def visit_relation(self, node: ir.Relation, parent: Optional[ir.Node]):
        if self._is_derived and from_cdc_annotation in node.annotations:
            self._is_derived = False
