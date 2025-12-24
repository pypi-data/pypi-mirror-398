from v0.relationalai.semantics.metamodel import ir, builtins, helpers, types
from v0.relationalai.semantics.metamodel.visitor import collect_by_type
from v0.relationalai.semantics.metamodel.util import FrozenOrderedSet
from v0.relationalai.semantics.lqp import ir as lqp, utils, types as lqp_types, builtins as lqp_builtins
from v0.relationalai.semantics.lqp.primitives import lqp_avg_op, lqp_operator, build_primitive
from v0.relationalai.semantics.lqp.pragmas import pragma_to_lqp_name
from v0.relationalai.semantics.lqp.types import meta_type_to_lqp
from v0.relationalai.semantics.lqp.constructors import (
    mk_abstraction, mk_and, mk_exists, mk_or, mk_pragma, mk_primitive,
    mk_specialized_value, mk_type, mk_value, mk_attribute
)
from v0.relationalai.semantics.lqp.utils import TranslationCtx, gen_unique_var
from v0.relationalai.semantics.lqp.validators import assert_valid_input
from v0.relationalai.semantics.lqp.rewrite.functional_dependencies import (
    normalized_fd, contains_only_declarable_constraints
)
from decimal import Decimal as PyDecimal
from datetime import datetime, date, timezone
from typing import Tuple, cast, Union, Optional
from warnings import warn
import re
import uuid

# Main access point for translating metamodel to lqp. Converts the model IR to an LQP epoch.
def to_lqp(model: ir.Model, fragment_name: bytes, ctx: TranslationCtx) -> tuple[Optional[tuple], lqp.Epoch]:
    assert_valid_input(model)
    decls: list[lqp.Declaration] = []
    reads: list[lqp.Read] = []

    # LQP only accepts logical tasks
    # These are asserted at init time
    root = cast(ir.Logical, model.root)
    for subtask in root.body:
        assert isinstance(subtask, ir.Logical)
        new_decls = _translate_to_decls(ctx, subtask)
        decls.extend(new_decls)

    # Add pyrel error attributes to reads.
    for err_id in _extract_pyrel_error_ids(ctx, model):
        ctx.output_ids.append(err_id)

    reads.extend(_get_output_reads(ctx.output_ids))

    export_info = None
    if len(ctx.export_ids) > 0:
        export_filename, col_types, export_reads = _get_export_reads(ctx.export_ids)
        reads.extend(export_reads)
        export_info = (export_filename, col_types)

    debug_info = lqp.DebugInfo(id_to_orig_name=ctx.rel_id_to_orig_name, meta=None)
    fragment_id = lqp.FragmentId(id=fragment_name, meta=None)
    fragment = lqp.Fragment(id=fragment_id, declarations=decls, meta=None, debug_info=debug_info)
    define_op = lqp.Define(fragment=fragment, meta=None)

    txn = lqp.Epoch(
        reads=reads,
        writes=[lqp.Write(write_type=define_op, meta=None)],
        meta=None
    )

    return (export_info, txn)

def _effect_bindings(effect: Union[ir.Output, ir.Update]) -> list[ir.Value]:
    if isinstance(effect, ir.Output):
        # Unions may not return anything. The generated IR contains a None value when this
        # happens. We ignore it here.
        return [v for v in helpers.output_values(effect.aliases) if v]
    else:
        return list(effect.args)

def _get_output_reads(output_ids: list[tuple[lqp.RelationId, str]]) -> list[lqp.Read]:
    reads = []
    for (rel_id, name) in output_ids:
        assert isinstance(rel_id, lqp.RelationId)
        output = lqp.Output(name=name, relation_id=rel_id, meta=None)
        reads.append(lqp.Read(read_type=output, meta=None))
    return reads

def _get_export_reads(export_ids: list[tuple[lqp.RelationId, int, lqp.Type]]) -> tuple[str, list, list[lqp.Read]]:
    reads = []
    csv_columns = []
    col_info = []
    for (col_id, col_num, col_type) in sorted(export_ids, key=lambda x: x[1]):
        col_name = f"col{col_num:03}"
        csv_columns.append(lqp.ExportCSVColumn(column_name=col_name, column_data=col_id, meta=None))
        col_info.append((col_name, col_type))

    # Generate a random name for the internal export path
    export_filename = "export_" + str(uuid.uuid4()).replace("-", "_")

    # Note that the engine will append the transaction id to the export path for access
    # control reasons. So the actual final path will be
    # `.../export/{export_filename}/data_{txn_id}`
    export_path = f"snowflake://APP_STATE.RAI_INTERNAL_STAGE/export/{export_filename}/data"
    export_csv_config = lqp.ExportCSVConfig(
        path=export_path,
        data_columns=csv_columns,
        compression="gzip",
        partition_size=200,
        syntax_escapechar='"',  # To follow Snowflake's expected format
        meta=None,
    )
    reads.append(lqp.Read(read_type=lqp.Export(config=export_csv_config, meta=None), meta=None))
    return (export_filename, col_info, reads)

def _translate_to_decls(ctx: TranslationCtx, rule: ir.Logical) -> list[lqp.Declaration]:
    if contains_only_declarable_constraints(rule):
        return _translate_to_constraint_decls(ctx, rule)
    else:
        return _translate_to_standard_decl(ctx, rule)

def _translate_to_constraint_decls(ctx: TranslationCtx, rule: ir.Logical) -> list[lqp.Declaration]:
    constraint_decls: list[lqp.Declaration] = []
    for task in rule.body:
        assert isinstance(task, ir.Require)
        fd = normalized_fd(task)
        assert fd is not None

        # check for unresolved types
        if any(types.is_any(var.type) for var in fd.keys + fd.values):
            warn(f"Ignoring FD with unresolved type: {fd}")
            continue

        lqp_typed_keys = [_translate_term(ctx, key) for key in fd.keys]
        lqp_typed_values = [_translate_term(ctx, value) for value in fd.values]
        lqp_typed_vars:list[Tuple[lqp.Var, lqp.Type]] = lqp_typed_keys + lqp_typed_values # type: ignore
        lqp_guard_atoms = [_translate_to_atom(ctx, atom) for atom in fd.guard]
        lqp_guard = mk_abstraction(lqp_typed_vars, mk_and(lqp_guard_atoms))
        lqp_keys:list[lqp.Var] = [var for (var, _) in lqp_typed_keys] # type: ignore
        lqp_values:list[lqp.Var] = [var for (var, _) in lqp_typed_values] # type: ignore

        fd_decl = lqp.FunctionalDependency(
            guard=lqp_guard,
            keys=lqp_keys,
            values=lqp_values,
            meta=None
        )

        constraint_decls.append(fd_decl)

    return constraint_decls

def _translate_to_standard_decl(ctx: TranslationCtx, rule: ir.Logical) -> list[lqp.Declaration]:
    effects = collect_by_type((ir.Output, ir.Update), rule)
    aggregates = collect_by_type(ir.Aggregate, rule)
    ranks = collect_by_type(ir.Rank, rule)

    # TODO: should this ever actually come in as input?
    if len(effects) == 0:
        return []

    assert len(ranks) == 0 or len(aggregates) == 0, "rules cannot have both aggregates and ranks"

    conjuncts = []
    for task in rule.body:
        if isinstance(task, (ir.Output, ir.Update)):
            continue
        conjuncts.append(_translate_to_formula(ctx, task))

    # Aggregates reduce over the body
    if aggregates or ranks:
        aggr_body = mk_and(conjuncts)
        conjuncts = []
        for aggr in aggregates:
            conjuncts.append(_translate_aggregate(ctx, aggr, aggr_body))
        for rank in ranks:
            conjuncts.append(_translate_rank(ctx, rank, aggr_body))

    return [_translate_effect(ctx, effect, mk_and(conjuncts)) for effect in effects]

def _translate_annotations(annotations: FrozenOrderedSet[ir.Annotation]) -> list[lqp.Attribute]:
    attributes = []
    for annotation in annotations:

        if annotation.relation.name in lqp_builtins.annotations_to_emit:
            if any(not isinstance(a, ir.Literal) for a in annotation.args):
                warn("LQP currently ignores annotation parameters with non-literal values")
                continue

            # Convert literal arguments to LQP values
            args = []
            for a in annotation.args:
                assert isinstance(a, ir.Literal)
                args.append(mk_value(a.value))
            attributes.append(mk_attribute(annotation.relation.name, args))
    return attributes

# Translates an effect (export, output, or update) into the corresponding def. Note that
# this method only generates the def and not the LQP read operation, which is added later by
# `_get_output_reads` and `_get_export_reads`.
def _translate_effect(ctx: TranslationCtx, effect: Union[ir.Output, ir.Update], body: lqp.Formula) -> lqp.Declaration:
    bindings = _effect_bindings(effect)

    def _is_export(e):
        return isinstance(e, ir.Output) and builtins.export_annotation in e.annotations

    if isinstance(effect, ir.Output):
        projection, eqs, suffix = _translate_output_bindings(ctx, bindings)
        meta_id = effect.id

        if _is_export(effect):
            def_name = "export_relation" + suffix
        else:
            def_name = "output" + suffix

        def_name = ctx.output_names.get_name_by_id(meta_id, def_name)
        rel_id = get_output_id(ctx, def_name, meta_id)
    else:
        projection, eqs = _translate_bindings(ctx, bindings)
        def_name = effect.relation.name
        rel_id = get_relation_id(ctx, effect.relation, projection)

    eqs.append(body)
    new_body = mk_and(eqs)

    # Context bookkeeping for exports and outputs
    if _is_export(effect):
        # The row id is the first n-1 elements, and the actual data is the last element. Its
        # type is stored in the first element of the tuple.
        col_type = projection[-1][1]
        _col_num_match = re.search(r"export_relation_col([0-9]+)", def_name)
        assert _col_num_match, f"Could not find column number in suffix: {def_name}"
        col_num = int(_col_num_match.group(1))
        ctx.export_ids.append((rel_id, col_num, col_type))
    elif isinstance(effect, ir.Output):
        ctx.output_ids.append((rel_id, def_name))

    # First we collect annotations on the effect itself, e.g. from something like
    # `select(...).annotate(...)`.
    annotations = effect.annotations
    if isinstance(effect, ir.Update):
        # Then we translate annotations on the relation itself, e.g.
        # ```
        # Bar.foo = model.Relationship(...)
        # Bar.foo.annotate(...)
        # ```
        annotations = annotations | effect.relation.annotations

    return lqp.Def(
        name = rel_id,
        body = mk_abstraction(projection, new_body),
        attrs = _translate_annotations(annotations),
        meta = None,
    )

def _translate_output_bindings(ctx: TranslationCtx, bindings: list[ir.Value]) -> Tuple[list[Tuple[lqp.Var, lqp.Type]], list[lqp.Formula], str]:
    symbol_literals = []
    non_symbols = []
    for binding in bindings:
        if isinstance(binding, ir.Literal) and binding.type == types.Symbol:
            symbol_literals.append(binding.value)
        else:
            non_symbols.append(binding)
    projection, eqs = _translate_bindings(ctx, non_symbols)
    if len(symbol_literals) > 0:
        name_suffix = "_"
        name_suffix += "_".join(symbol_literals)
    else:
        name_suffix = ""

    return projection, eqs, name_suffix

def _translate_rank(ctx: TranslationCtx, rank: ir.Rank, body: lqp.Formula) -> lqp.Formula:
    # Ascending rank is constructed using rel_primitive_sort. If a limit is added to an
    # ascending rank we can use rel_primitive_top for an efficient evaluation.
    #
    # Descending rank is constructed as an ascending sort, then the ascending rank is
    # subtracted from a count of the elements (plus 1 so that we still start at 1).
    # Adding a limit to a descending rank is done by adding a filter of rank <= limit.

    # Limits are the sort plus a filter on rank <= limit.
    if all(o for o in rank.arg_is_ascending):
        ascending = True
    elif all(not o for o in rank.arg_is_ascending):
        ascending = False
    else:
        raise Exception("Mixed orderings in rank are not supported yet.")

    # Filter out the group-by variables, since they are introduced outside the rank.
    input_args, input_eqs = _translate_bindings(ctx, list(rank.args))
    introduced_meta_projs = [arg for arg in rank.projection if arg not in rank.group and arg not in rank.args]
    projected_args, projected_eqs = _translate_bindings(ctx, list(introduced_meta_projs))

    # rank expects an Int128 result, but the primitive will return an Int64 result.
    # we need to set up an intermediary variable to hold the Int64 result, and a cast
    # to convert it to Int128.
    result_var, _ = _translate_term(ctx, rank.result)
    # The primitive will return an Int64 result, so we need a var to hold the intermediary.
    result_64_var = gen_unique_var(ctx, "v_rank")
    result_64_type = mk_type(lqp.TypeName.INT)

    cast = lqp.Cast(input=result_64_var, result=result_var, meta=None)

    body = mk_and([body] + input_eqs + projected_eqs)
    abstr_args = input_args + projected_args

    if ascending:
        ranker = _translate_ascending_rank(ctx, rank.limit, result_64_var, body, abstr_args)
    else:
        ranker = _translate_descending_rank(ctx, rank.limit, result_64_var, body, abstr_args)

    return mk_exists([(result_64_var, result_64_type)], mk_and([ranker, cast]))

def _translate_descending_rank(ctx: TranslationCtx, limit: int, result: lqp.Var, body: lqp.Formula, abstr_args) -> lqp.Formula:
    result_var = result
    result_type = mk_type(lqp.TypeName.INT)

    # Rename abstracted args in the body to new variable names
    var_map = {var.name: gen_unique_var(ctx, 't_' + var.name) for (var, _) in abstr_args}
    body = utils.rename_vars_formula(body, var_map)
    new_abstr_args = [(var_map[var.name], typ) for (var, typ) in abstr_args]

    # Construct a conjunction of the ranking, a counter for the body, a subtraction
    # of the rank from the count and an addition of 1. Wrap this in an abstraction.
    count_res = gen_unique_var(ctx, "count_res")

    # Add one to the count to account for the rank starting at 1.
    one, one_eq = constant_to_var(ctx, to_lqp_value(1, types.Int64), "one")
    one_bigger = gen_unique_var(ctx, "one_bigger")
    addition = mk_primitive("rel_primitive_add_monotype", [count_res, one, one_bigger])

    # Subtract the rank from the count + 1
    asc_rank = gen_unique_var(ctx, "asc_rank")
    subtraction = mk_primitive("rel_primitive_subtract_monotype", [one_bigger, result_var, asc_rank])

    # Construct the ranking
    desc_ranking_terms = [asc_rank] + [v[0] for v in abstr_args]
    ranking = lqp.FFI(
        meta=None,
        name="rel_primitive_sort",
        args=[mk_abstraction(new_abstr_args, body)],
        terms=desc_ranking_terms,
    )

    # Count the number of rows in the body
    count_type = meta_type_to_lqp(types.Int64)
    count_var, count_eq = constant_to_var(ctx, to_lqp_value(1, types.Int64), "counter")
    desc_body = mk_and([body, count_eq])
    aggr_abstr_args = new_abstr_args + [(count_var, count_type)]
    count_aggr = lqp.Reduce(
        op=lqp_operator(
            ctx,
            "count",
            "count",
            mk_type(lqp.TypeName.INT)
        ),
        body=mk_abstraction(aggr_abstr_args, desc_body),
        terms=[count_res],
        meta=None
    )

    # Bring it all together and do the maths.
    ranking = mk_exists(
        vars=[
            (asc_rank, result_type),
            (count_res, result_type),
            (one, result_type),
            (one_bigger, result_type)
        ],
        value=mk_and([ranking, count_aggr, one_eq, addition, subtraction])
    )

    # If there is a limit, we need to add a filter to the ranking.
    # Wrap with a rank <= limit
    if limit != 0:
        limit_term, _ = _translate_term(ctx, ir.Literal(types.Int64, limit))
        limiter = mk_primitive("rel_primitive_lt_eq_monotype", [result_var, limit_term])
        ranking = mk_and([ranking, limiter])

    return ranking

def _translate_ascending_rank(ctx: TranslationCtx, limit: int, result_var: lqp.Var, body: lqp.Formula, abstr_args) -> lqp.Formula:
    terms = [result_var] + [v[0] for v in abstr_args]

    # Rename abstracted args in the body to new variable names
    var_map = {var.name: gen_unique_var(ctx, 't_' + var.name) for (var, _) in abstr_args}
    body = utils.rename_vars_formula(body, var_map)
    new_abstr_args = [(var_map[var.name], typ) for (var, typ) in abstr_args]
    sort_abstr = mk_abstraction(new_abstr_args, body)

    if limit == 0:
        return lqp.FFI(
            meta=None,
            name="rel_primitive_sort",
            args=[sort_abstr],
            terms=terms,
        )
    else:
        limit_type = meta_type_to_lqp(types.Int64)
        limit_var, limit_eq = constant_to_var(ctx, to_lqp_value(limit, types.Int64), "limit")
        limit_abstr = mk_abstraction([(limit_var, limit_type)], limit_eq)
        return lqp.FFI(
            meta=None,
            name="rel_primitive_top",
            args=[sort_abstr, limit_abstr],
            terms=terms,
        )

def _translate_aggregate(ctx: TranslationCtx, aggr: ir.Aggregate, body: lqp.Formula) -> Union[lqp.Reduce, lqp.Formula]:
    # TODO: handle this properly
    aggr_name = aggr.aggregation.name
    supported_aggrs = ("sum", "count", "avg", "min", "max", "rel_primitive_solverlib_ho_appl")
    assert aggr_name in supported_aggrs, f"only support {supported_aggrs} for now, not {aggr.aggregation.name}"

    meta_output_terms = []
    meta_input_terms = []

    for (field, arg) in zip(aggr.aggregation.fields, aggr.args):
        if field.input:
            meta_input_terms.append(arg)
        else:
            meta_output_terms.append(arg)

    output_terms = [_translate_term(ctx, term) for term in meta_output_terms]
    output_vars = [term[0] for term in output_terms]

    body_conjs = [body]
    input_args, input_eqs = _translate_bindings(ctx, meta_input_terms)

    # TODO: Can this safely be applied to all aggregates?
    if aggr_name in ("sum", "min", "max"):
        assert len(output_terms) == 1, f"{aggr_name} expects a single output variable"
        assert len(meta_input_terms) == 1, f"{aggr_name} expects a single input variable"
        assert isinstance(meta_output_terms[0], ir.Var)
        assert input_args[0][1] == output_terms[0][1], f"{aggr_name}({input_args[0][1].type_name}) had output type of {output_terms[0][1].type_name}"

    # Filter out the group-by variables, since they are introduced outside the aggregation.
    # Input terms are added later below.
    introduced_meta_projs = [arg for arg in aggr.projection if arg not in aggr.group and arg not in meta_input_terms]
    projected_args, projected_eqs = _translate_bindings(ctx, list(introduced_meta_projs))
    body_conjs.extend(input_eqs)
    body_conjs.extend(projected_eqs)
    abstr_args: list[Tuple[lqp.Var, lqp.Type]] = projected_args + input_args

    if aggr_name == "count":
        assert len(output_terms) == 1, "Count and avg expect a single output variable"
        assert isinstance(meta_output_terms[0], ir.Var)
        # Count sums up "1" for each row. We use the expected output type for the type
        # of the count variable.
        typ = meta_type_to_lqp(meta_output_terms[0].type)
        one_var, eq = constant_to_var(ctx, to_lqp_value(1, meta_output_terms[0].type), "one")
        body_conjs.append(eq)
        abstr_args.append((one_var, typ))
        body = mk_and(body_conjs)

    # Average needs to wrap the reduce in Exists(Conjunction(Reduce, div))
    if aggr_name == "avg":
        assert len(output_vars) == 1, "avg should only have one output variable"
        output_var = output_vars[0]

        # Count sums up "1" for each row. We make the reasonably safe assumption that there
        # are less than 2^31 rows in the body.
        count_type = meta_type_to_lqp(types.Int64)
        one_var, eq = constant_to_var(ctx, to_lqp_value(1, types.Int64), "one")
        body_conjs.append(eq)
        abstr_args.append((one_var, count_type))
        body = mk_and(body_conjs)

        # The average will produce two output variables: sum and count.
        sum_result = gen_unique_var(ctx, "sum")
        count_result = gen_unique_var(ctx, "count")

        # Second to last is the variable we're summing over.
        (sum_var, sum_type) = abstr_args[-2]

        result = lqp.Reduce(
            op=lqp_avg_op(ctx, aggr.aggregation.name, sum_var.name, sum_type),
            body=mk_abstraction(abstr_args, body),
            terms=[sum_result, count_result],
            meta=None,
        )

        if sum_type == count_type:
            div = mk_primitive("rel_primitive_divide_monotype", [sum_result, count_result, output_var])
            conjunction = mk_and([result, div])

            # Finally, we need to wrap everything in an `exists` to project away the sum and
            # count variables and only keep the result of the division.
            result_terms = [(sum_result, sum_type), (count_result, count_type)]
        else:
            # If the sum type and count type don't match, we need to cast the count
            count_casted = gen_unique_var(ctx, "count_casted")
            count_cast = lqp.Cast(input=count_result, result=count_casted, meta=None)

            div = mk_primitive("rel_primitive_divide_monotype", [sum_result, count_casted, output_var])
            conjunction = mk_and([result, count_cast, div])

            # Finally, we need to wrap everything in an `exists` to project away the sum and
            # count variables and only keep the result of the division.
            result_terms = [(sum_result, sum_type), (count_result, count_type), (count_casted, sum_type)]

        return mk_exists(result_terms, conjunction)

    # `input_args` hold the types of the input arguments, but they may have been modified
    # if we're dealing with a count, so we use `abstr_args` to find the type.
    (aggr_arg, aggr_arg_type) = abstr_args[-1]

    # Group-bys do not need to be handled at all, since they are introduced outside already
    reduce = lqp.Reduce(
        op=lqp_operator(ctx, aggr.aggregation.name, aggr_arg.name, aggr_arg_type),
        body=mk_abstraction(abstr_args, body),
        terms=output_vars,
        meta=None
    )
    return reduce

def _translate_to_formula(ctx: TranslationCtx, task: ir.Task) -> lqp.Formula:
    if isinstance(task, ir.Logical):
        conjuncts = [_translate_to_formula(ctx, child) for child in task.body]
        return mk_and(conjuncts)
    elif isinstance(task, ir.Lookup):
        return _translate_to_atom(ctx, task)
    elif isinstance(task, ir.Not):
        return lqp.Not(arg=_translate_to_formula(ctx, task.task), meta=None)
    elif isinstance(task, ir.Exists):
        lqp_vars, conjuncts = _translate_bindings(ctx, list(task.vars))
        conjuncts.append(_translate_to_formula(ctx, task.task))
        return mk_exists(lqp_vars, mk_and(conjuncts))
    elif isinstance(task, ir.Construct):
        assert len(task.values) >= 1, "Construct should have at least one value"
        terms = [_translate_term(ctx, arg) for arg in task.values]
        result_term = _translate_term(ctx, task.id_var)
        terms.append(result_term)
        assert result_term[1].type_name == lqp.TypeName.UINT128, \
            f"Attempting to store a {task.id_var} in a type `{result_term[1].type_name}`"

        return mk_primitive("rel_primitive_hash_tuple_uint128", [v for v, _ in terms])
    elif isinstance(task, ir.Union):
        # TODO: handle hoisted vars if needed
        disjs = [_translate_to_formula(ctx, child) for child in task.tasks]
        return mk_or(disjs)
    elif isinstance(task, (ir.Aggregate, ir.Output, ir.Update)):
        # Nothing to do here, handled in _translate_to_decls
        return mk_and([])
    elif isinstance(task, ir.Rank):
        # Nothing to do here, handled in _translate_to_decls
        return mk_and([])
    else:
        raise NotImplementedError(f"Unknown task type (formula): {type(task)}")

# Only used for translating terms on relatoms, which can be specialized values.
def _translate_relterm(ctx: TranslationCtx, term: ir.Value) -> Tuple[lqp.RelTerm, lqp.Type]:
    if isinstance(term, ir.Literal) and term.type == types.Symbol:
        if isinstance(term.value, str):
            value = mk_value(term.value)
            return mk_specialized_value(value), meta_type_to_lqp(types.String)
        elif isinstance(term.value, int):
            value = mk_value(term.value)
            return mk_specialized_value(value), meta_type_to_lqp(types.Int64)
        else:
            raise NotImplementedError(f"Cannot specialize literal of type {type(term.value)}")
    return _translate_term(ctx, term)

def _translate_term(ctx: TranslationCtx, term: ir.Value) -> Tuple[lqp.Term, lqp.Type]:
    if isinstance(term, ir.ScalarType):
        # TODO: ScalarType is not like other terms, should be handled separately.
        return to_lqp_value(term.name, types.String), meta_type_to_lqp(types.String)
    elif isinstance(term, ir.Var):
        t = meta_type_to_lqp(term.type)
        return _translate_var(ctx, term), t
    else:
        assert isinstance(term, ir.Literal), f"Cannot translate value {term!r} of type {type(term)} to LQP Term; neither Var nor Literal."
        v = to_lqp_value(term.value, term.type)
        return v, meta_type_to_lqp(term.type)

def _translate_to_atom(ctx: TranslationCtx, task: ir.Lookup) -> lqp.Formula:
    if task.relation == builtins.cast:
        assert len(task.args) == 3, f"expected three terms for {task.relation.name}, got {len(task.args)}"

        terms = []
        for arg in task.args[1:]:
            term, _ = _translate_relterm(ctx, arg)
            terms.append(term)
        return lqp.Cast(input=terms[0], result=terms[1], meta=None)

    if task.relation == builtins.join:
        return _translate_join(ctx, task)
    elif task.relation == builtins.infomap:
        return _translate_infomap(ctx, task)
    elif task.relation == builtins.louvain:
        return _translate_louvain(ctx, task)
    elif task.relation == builtins.label_propagation:
        return _translate_label_propagation(ctx, task)

    terms = []
    term_types = []
    for arg in task.args:
        # Handle varargs, which come wrapped in a tuple.
        if isinstance(arg, tuple):
            for vararg in arg:
                term, ty = _translate_relterm(ctx, vararg)
                terms.append(term)
                term_types.append(ty)
        else:
            term, ty = _translate_relterm(ctx, arg)
            terms.append(term)
            term_types.append(ty)

    if builtins.is_pragma(task.relation):
        lqp_name = pragma_to_lqp_name(task.relation.name)
        return mk_pragma(lqp_name, terms)

    if builtins.is_builtin(task.relation):
        return build_primitive(task.relation.name, terms, term_types)

    if helpers.is_external(task.relation):
        return lqp.RelAtom(name=task.relation.name, terms=terms, meta=None)

    projection, _ = _translate_bindings(ctx, list(task.args))
    rid = get_relation_id(ctx, task.relation, projection)
    return lqp.Atom(name=rid, terms=terms, meta=None)


def get_relation_id(ctx: TranslationCtx, relation: ir.Relation, projection: list[Tuple[lqp.Var, lqp.Type]] = []) -> lqp.RelationId:
    types = "_".join([str(t.type_name) for (_, t) in projection])
    if types:
        types = "_" + types
    if relation.id in ctx.def_names.id_to_name:
        unique_name = ctx.def_names.id_to_name[relation.id]
    else:
        name = helpers.relation_name_prefix(relation) + relation.name
        name = helpers.sanitize(name)
        unique_name = ctx.def_names.get_name_by_id(relation.id, name)

    return utils.gen_rel_id(ctx, unique_name, types)

def get_output_id(ctx: TranslationCtx, orig_name: str, metamodel_id: int) -> lqp.RelationId:
    unique_name = ctx.output_names.get_name_by_id(metamodel_id, orig_name)
    return utils.gen_rel_id(ctx, unique_name)

def _translate_bindings(ctx: TranslationCtx, bindings: list[ir.Value]) -> Tuple[list[Tuple[lqp.Var, lqp.Type]], list[lqp.Formula]]:
    lqp_vars = []
    conjuncts = []
    for binding in bindings:
        lqp_var, typ, eq = binding_to_lqp_var(ctx, binding)
        lqp_vars.append((lqp_var, typ))
        if eq is not None:
            conjuncts.append(eq)

    return lqp_vars, conjuncts

def binding_to_lqp_var(ctx: TranslationCtx, binding: ir.Value) -> Tuple[lqp.Var, lqp.Type, Union[None, lqp.Formula]]:
    if isinstance(binding, ir.Var):
        var, typ = _translate_term(ctx, binding)
        assert isinstance(var, lqp.Var)
        return var, typ, None
    elif isinstance(binding, ir.Literal):
        lqp_value = to_lqp_value(binding.value, binding.type)
        var, formula = constant_to_var(ctx, lqp_value)
        return var, meta_type_to_lqp(binding.type), formula
    else:
        raise Exception(f"Unsupported binding type: {type(binding)}")

def to_lqp_value(value: ir.PyValue, value_type: ir.Type) -> lqp.Value:
    typ = meta_type_to_lqp(value_type)

    # Ensure int values match the requested integer type.
    if typ.type_name == lqp.TypeName.INT and isinstance(value, int):
        assert lqp_types.INT_MIN <= value <= lqp_types.INT_MAX, f"{value} out of range for a 64-bit INT value"
        val = value
    elif typ.type_name == lqp.TypeName.INT128 and isinstance(value, int):
        assert lqp_types.INT128_MIN <= value <= lqp_types.INT128_MAX, f"{value} out of range for an INT128 value"
        val = lqp.Int128Value(value=value, meta=None)
    elif typ.type_name == lqp.TypeName.UINT128 and isinstance(value, int):
        assert lqp_types.UINT128_MIN <= value <= lqp_types.UINT128_MAX, f"{value} out of range for an UINT128 value"
        val = lqp.UInt128Value(value=value, meta=None)
    elif typ.type_name == lqp.TypeName.FLOAT and isinstance(value, float):
        val = value
    elif typ.type_name == lqp.TypeName.STRING and isinstance(value, str):
        val = value
    elif typ.type_name == lqp.TypeName.DECIMAL and isinstance(value, PyDecimal):
        precision = typ.parameters[0].value
        scale = typ.parameters[1].value
        assert isinstance(precision, int) and isinstance(scale, int)
        val = lqp.DecimalValue(precision=precision, scale=scale, value=value, meta=None)
    elif typ.type_name == lqp.TypeName.DATE and isinstance(value, date):
        val = lqp.DateValue(value=value, meta=None)
    elif typ.type_name == lqp.TypeName.DATETIME and isinstance(value, datetime):
        utc_value = value.astimezone(timezone.utc) if value.tzinfo is not None else value # Convert to UTC cf. Iceberg
        val = lqp.DateTimeValue(value=utc_value, meta=None)
    elif typ.type_name == lqp.TypeName.BOOLEAN and isinstance(value, bool):
        val = lqp.BooleanValue(value=value, meta=None)
    else:
        raise Exception(f"Unsupported type for constant: {typ.type_name} with value {value} of type {type(value)}")

    return mk_value(val)

def constant_to_var(ctx: TranslationCtx, value: lqp.Value, name_hint: str = "cvar") -> Tuple[lqp.Var, lqp.Formula]:
    var = gen_unique_var(ctx, name_hint)
    eq = mk_primitive("rel_primitive_eq", [var, value])
    return var, eq

def _extract_pyrel_error_ids(ctx: TranslationCtx, model: ir.Model) -> list[Tuple[lqp.RelationId, str]]:
    effects = collect_by_type(ir.Update, model)
    pyrel_error_attrs = []
    # We use a separate counter here to avoid modifying the current model.
    i = 1
    for effect in effects:
        if "pyrel_error_attrs" not in effect.relation.name:
            continue
        projection, _ = _translate_bindings(ctx, _effect_bindings(effect))
        rel_id = get_relation_id(ctx, effect.relation, projection)
        name = f"{effect.relation.name}_{i}"
        pyrel_error_attrs.append((rel_id, name))
        i += 1

    return pyrel_error_attrs

# Translate a relation reference into an abstraction over its fields.
def _translate_relation_ref(ctx: TranslationCtx, relation: ir.Relation) -> lqp.Abstraction:
    projection = []
    for field in relation.fields:
        var = gen_unique_var(ctx, field.name)
        typ = meta_type_to_lqp(field.type)
        projection.append((var, typ))

    rid = get_relation_id(ctx, relation, projection)
    atom = lqp.Atom(name=rid, terms=[var for (var, _) in projection], meta=None)
    return mk_abstraction(projection, atom)

# Common translation logic for graph algorithms.
# task.args[0] : normalized weight list (int64, int64, float)
# task.args[1] : normalized node count (relation or constant int64)
# task.args[2] : normalized edge count (relation or constant int64)
# task.args[3:-3] : algorithm parameters (var or constant)
# task.args[-3] : diagnostic info
# task.args[-2] : node index
# task.args[-1] : community ident
def _translate_graph_common(name: str, ctx: TranslationCtx, task: ir.Lookup):
    abstractions = []

    assert isinstance(task.args[0], ir.Relation), \
        f"Expected relation as first arg to {name}, got {task.args[0]}:{type(task.args[0])}"
    abstractions.append(_translate_relation_ref(ctx, task.args[0]))

    # Allow constant args for node and edge count
    for arg in task.args[1:3]:
        if isinstance(arg, ir.Relation):
            abst = _translate_relation_ref(ctx, arg)
            typ = abst.vars[0][1]
            assert typ.type_name == lqp.TypeName.INT, \
                f"Expected Int64 types for node and edge counts, got type {typ.type_name}"
            abstractions.append(abst)
        else:
            var, typ, eq = binding_to_lqp_var(ctx, arg)
            assert eq is not None, \
                f"Expected equality formula for {name} arg {arg}:{type(arg)}"
            abstractions.append(mk_abstraction([(var, typ)], mk_and([eq])))

    for arg in task.args[3:-3]:
        var, typ, eq = binding_to_lqp_var(ctx, arg)
        if eq:
            abstractions.append(mk_abstraction([(var, typ)], mk_and([eq])))
        else:
            print(f"Primitive graph algorithm arg without eq:\n var:{var}, typ:{typ}\n arg:{arg}:{type(arg)}")
            abstractions.append(mk_abstraction([(var, typ)], mk_and([])))

    terms = []
    for arg in task.args[-3:]:
        term, _ = _translate_relterm(ctx, arg)
        terms.append(term)

    return (abstractions, terms)

def _translate_infomap(ctx: TranslationCtx, task: ir.Lookup) -> lqp.Formula:
    abstractions, terms = _translate_graph_common("infomap", ctx, task)

    return lqp.FFI(
        meta=None,
        name="rel_primitive_infomap",
        args=abstractions,
        terms=terms,
    )

def _translate_louvain(ctx: TranslationCtx, task: ir.Lookup) -> lqp.Formula:
    abstractions, terms = _translate_graph_common("louvain", ctx, task)

    return lqp.FFI(
        meta=None,
        name="rel_primitive_louvain",
        args=abstractions,
        terms=terms,
    )

def _translate_label_propagation(ctx: TranslationCtx, task: ir.Lookup) -> lqp.Formula:
    abstractions, terms = _translate_graph_common("label_propagation", ctx, task)

    return lqp.FFI(
        meta=None,
        name="rel_primitive_async_label_propagation",
        args=abstractions,
        terms=terms,
    )

# Hard-coded implementation of Rel's string_join
def _translate_join(ctx: TranslationCtx, task: ir.Lookup) -> lqp.Formula:
    assert len(task.args) == 3
    (strs, separator, target) = task.args
    assert isinstance(separator, ir.Node)
    assert isinstance(target, ir.Var)
    assert isinstance(strs, tuple)

    # Enumerate the strings we're going to be reducing over
    enumerated_conjunctions = []
    index_var, index_type = gen_unique_var(ctx, "idx"), meta_type_to_lqp(types.Int64)
    string_var, string_type = gen_unique_var(ctx, "s"), meta_type_to_lqp(types.String)
    for i, s in enumerate(strs):
        index = to_lqp_value(i, types.Int64)
        string = _translate_term(ctx, s)[0]
        eq_idx = mk_primitive("rel_primitive_eq", [index_var, index])
        eq_string = mk_primitive("rel_primitive_eq", [string_var, string])
        enumerated_conjunctions.append(mk_and([eq_idx, eq_string]))
    body = mk_abstraction([(index_var, index_type), (string_var, string_type)], mk_or(enumerated_conjunctions))

    # Make the function we're reducing
    a_var, a_type = gen_unique_var(ctx, "a"), meta_type_to_lqp(types.String)
    b_var, b_type = gen_unique_var(ctx, "b"), meta_type_to_lqp(types.String)
    curr_var, curr_type = gen_unique_var(ctx, "curr"), meta_type_to_lqp(types.String)
    res_var, res_type = gen_unique_var(ctx, "res"), meta_type_to_lqp(types.String)

    sep, _ = _translate_term(ctx, separator)

    op = mk_abstraction(
        [(a_var, a_type), (b_var, b_type), (curr_var, curr_type)],
        mk_exists([(res_var, res_type)],
            mk_and([
                mk_primitive("rel_primitive_concat", [res_var, b_var, curr_var]),
                mk_primitive("rel_primitive_concat", [a_var, sep, res_var])
            ])
        )
    )

    output_term = _translate_term(ctx, target)[0]

    return lqp.Reduce(meta=None, op=op, body=body, terms=[output_term])

def _translate_var(ctx: TranslationCtx, term: ir.Var) -> lqp.Var:
    name = ctx.var_names.get_name_by_id(term.id, term.name)
    return lqp.Var(name=name, meta=None)
