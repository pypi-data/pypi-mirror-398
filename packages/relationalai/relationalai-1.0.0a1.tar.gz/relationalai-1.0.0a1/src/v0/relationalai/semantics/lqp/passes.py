from v0.relationalai.semantics.metamodel.compiler import Pass
from v0.relationalai.semantics.metamodel import ir, builtins as rel_builtins, factory as f, visitor
from v0.relationalai.semantics.metamodel.typer import Checker, InferTypes, typer
from v0.relationalai.semantics.metamodel import helpers, types
from v0.relationalai.semantics.metamodel.util import FrozenOrderedSet

from v0.relationalai.semantics.metamodel.rewrite import Flatten

from ..metamodel.rewrite import DNFUnionSplitter, ExtractNestedLogicals, FormatOutputs
from .rewrite import (
    AnnotateConstraints, CDC, ExtractCommon, ExtractKeys, FunctionAnnotations, QuantifyVars,
    Splinter, SplitMultiCheckRequires
)
from v0.relationalai.semantics.lqp.utils import output_names

from typing import cast, List, Sequence, Tuple, Union, Optional, Iterable
from collections import defaultdict
import pandas as pd
import hashlib

def lqp_passes() -> list[Pass]:
    return [
        SplitMultiCheckRequires(),
        FunctionAnnotations(),
        AnnotateConstraints(),
        Checker(),
        CDC(), # specialize to physical relations before extracting nested and typing
        ExtractNestedLogicals(), # before InferTypes to avoid extracting casts
        InferTypes(),
        DNFUnionSplitter(),
        ExtractKeys(),
        FormatOutputs(),
        ExtractCommon(), # Extracts tasks that will become common after Flatten into their own definition
        Flatten(),
        Splinter(), # Splits multi-headed rules into multiple rules
        QuantifyVars(), # Adds missing existentials
        EliminateData(),  # Turns Data nodes into ordinary relations.
        DeduplicateVars(),  # Deduplicates vars in Updates and Outputs.
        PeriodMath(),  # Rewrite date period uses.
        ConstantsToVars(),  # Turns constants in Updates and Outputs into vars.
        UnifyDefinitions(),
    ]

# LQP does not support multiple definitions for the same relation. This pass unifies all
# definitions for each relation into a single definition using a union.
class UnifyDefinitions(Pass):
    def __init__(self):
        super().__init__()

    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        # Maintain a cache of renamings for each relation. These need to be consistent
        # across all definitions of the same relation.
        self.renamed_relation_args: dict[Union[ir.Value, ir.Relation], list[ir.Var]] = {}

        root = cast(ir.Logical, model.root)
        new_tasks = self.get_combined_multidefs(root)
        return ir.Model(
            model.engines,
            model.relations,
            model.types,
            f.logical(
                tuple(new_tasks),
                root.hoisted,
                root.engine,
            ),
            model.annotations,
        )

    def _get_heads(self, logical: ir.Logical) -> list[Union[ir.Update, ir.Output]]:
        derives = []
        for task in logical.body:
            if isinstance(task, ir.Update) and task.effect == ir.Effect.derive:
                derives.append(task)
            elif isinstance(task, ir.Output):
                derives.append(task)
        return derives

    def _get_non_heads(self, logical: ir.Logical) -> list[ir.Task]:
        non_derives = []
        for task in logical.body:
            if not(isinstance(task, ir.Update) and task.effect == ir.Effect.derive) and not isinstance(task, ir.Output):
                non_derives.append(task)
        return non_derives

    def _get_head_identifier(self, head: Union[ir.Update, ir.Output]) -> Optional[ir.Value]:
        if isinstance(head, ir.Update):
            return head.relation
        else:
            assert isinstance(head, ir.Output)
            if len(head.aliases) <= 2:
                # For processing here, we need output to have at least the column markers
                # `cols` and `col`, and also a key
                return None

            output_alias_names = helpers.output_alias_names(head.aliases)
            output_vals = helpers.output_values(head.aliases)

            # For normal outputs, the pattern is output[keys](cols, "col000" as 'col', ...)
            if output_alias_names[0] == "cols" and output_alias_names[1] == "col":
                return output_vals[1]

            # For exports, the pattern is output[keys]("col000" as 'col', ...)
            if rel_builtins.export_annotation in head.annotations:
                if output_alias_names[0] == "col":
                    return output_vals[0]

        return None

    def get_combined_multidefs(self, root: ir.Logical) -> list[ir.Logical]:
        # Step 1: Group tasks by the relation they define.
        relation_to_tasks: dict[Union[None, ir.Value, ir.Relation], list[ir.Logical]] = defaultdict(list)

        for task in root.body:
            task = cast(ir.Logical, task)
            task_heads = self._get_heads(task)

            # Some relations do not need to be grouped, e.g., if they don't contain a
            # derive. Use `None` as a placeholder key for these cases.
            if len(task_heads) != 1:
                relation_to_tasks[None].append(task)
                continue

            head_id = self._get_head_identifier(task_heads[0])
            relation_to_tasks[head_id].append(task)

        # Step 2: For each relation, combine all of the body definitions into a union.
        result_tasks = []
        for relation, tasks in relation_to_tasks.items():
            # If there's only one task for the relation, or if grouping is not needed, then
            # just keep the original tasks.
            if len(tasks) == 1 or relation is None:
                result_tasks.extend(tasks)
                continue

            result_tasks.append(self._combine_tasks_into_union(tasks))
        return result_tasks

    def _get_variable_mapping(self, logical: ir.Logical) -> dict[ir.Value, ir.Var]:
        heads = self._get_heads(logical)
        assert len(heads) == 1, "should only have one head in a logical at this stage"
        head = heads[0]

        var_mapping = {}
        head_id = self._get_head_identifier(head)

        if isinstance(head, ir.Update):
            args_for_renaming = head.args
        else:
            assert isinstance(head, ir.Output)
            output_alias_names = helpers.output_alias_names(head.aliases)
            if output_alias_names[0] == "cols" and output_alias_names[1] == "col":
                assert len(head.aliases) > 2

                # For outputs, we do not need to rename the `cols` and `col` markers or the
                # keys.
                output_values = helpers.output_values(head.aliases)[2:]

            else:
                assert rel_builtins.export_annotation in head.annotations and output_alias_names[0] == "col"
                assert len(head.aliases) > 1

                # For exports, we do not need to rename the `col` marker or the keys.
                output_values = helpers.output_values(head.aliases)[1:]

            args_for_renaming = []
            for v in output_values:
                if head.keys and isinstance(v, ir.Var) and v in head.keys:
                    continue
                args_for_renaming.append(v)

        if head_id not in self.renamed_relation_args:
            renamed_vars = []
            for (i, arg) in enumerate(args_for_renaming):
                typ = typer.to_type(arg)
                assert arg not in var_mapping, "args of update should be unique"
                if isinstance(arg, ir.Var):
                    var_mapping[arg] = ir.Var(typ, arg.name)
                else:
                    var_mapping[arg] = ir.Var(typ, f"arg_{i}")

                renamed_vars.append(var_mapping[arg])
            self.renamed_relation_args[head_id] = renamed_vars
        else:
            for (arg, var) in zip(args_for_renaming, self.renamed_relation_args[head_id]):
                var_mapping[arg] = var

        return var_mapping

    def _rename_variables(self, logical: ir.Logical) -> ir.Logical:
        class RenameVisitor(visitor.Rewriter):
            def __init__(self, var_mapping: dict[ir.Value, ir.Var]):
                super().__init__()
                self.var_mapping = var_mapping

            def _get_mapped_value(self, val: ir.Value) -> ir.Value:
                if isinstance(val, tuple):
                    return tuple(self._get_mapped_value(t) for t in val)
                return self.var_mapping.get(val, val)

            def _get_mapped_values(self, vals: Iterable[ir.Value]) -> list[ir.Value]:
                return [self._get_mapped_value(v) for v in vals]

            def handle_var(self, node: ir.Var, parent: ir.Node) -> ir.Var:
                return self.var_mapping.get(node, node)

            # TODO: ideally, extend the rewriter class to allow rewriting PyValue to Var so
            # we don't need to separately handle all cases containing them.
            def handle_update(self, node: ir.Update, parent: ir.Node) -> ir.Update:
                return ir.Update(
                    node.engine,
                    node.relation,
                    tuple(self._get_mapped_values(node.args)),
                    node.effect,
                    node.annotations,
                )

            def handle_lookup(self, node: ir.Lookup, parent: ir.Node) -> ir.Lookup:
                return ir.Lookup(
                    node.engine,
                    node.relation,
                    tuple(self._get_mapped_values(node.args)),
                    node.annotations,
                )

            def handle_output(self, node: ir.Output, parent: ir.Node) -> ir.Output:
                new_aliases = FrozenOrderedSet(
                    [(name, self._get_mapped_value(value)) for name, value in node.aliases]
                )
                if node.keys:
                    new_keys = FrozenOrderedSet(
                        [self.var_mapping.get(key, key) for key in node.keys]
                    )
                else:
                    new_keys = node.keys

                return ir.Output(
                    node.engine,
                    new_aliases,
                    new_keys,
                    node.annotations,
                )

            def handle_construct(self, node: ir.Construct, parent: ir.Node) -> ir.Construct:
                new_values = tuple(self._get_mapped_values(node.values))
                new_id_var = self.var_mapping.get(node.id_var, node.id_var)
                return ir.Construct(
                    node.engine,
                    new_values,
                    new_id_var,
                    node.annotations,
                )

            def handle_aggregate(self, node: ir.Aggregate, parent: ir.Node) -> ir.Aggregate:
                new_projection = tuple(self.var_mapping.get(arg, arg) for arg in node.projection)
                new_group = tuple(self.var_mapping.get(arg, arg) for arg in node.group)
                new_args = tuple(self._get_mapped_values(node.args))
                return ir.Aggregate(
                    node.engine,
                    node.aggregation,
                    new_projection,
                    new_group,
                    new_args,
                    node.annotations,
                )

            def handle_rank(self, node: ir.Rank, parent: ir.Node) -> ir.Rank:
                new_projection = tuple(self.var_mapping.get(arg, arg) for arg in node.projection)
                new_group = tuple(self.var_mapping.get(arg, arg) for arg in node.group)
                new_args = tuple(self.var_mapping.get(arg, arg) for arg in node.args)
                new_result = self.var_mapping.get(node.result, node.result)

                return ir.Rank(
                    node.engine,
                    new_projection,
                    new_group,
                    new_args,
                    node.arg_is_ascending,
                    new_result,
                    node.limit,
                    node.annotations,
                )

        var_mapping = self._get_variable_mapping(logical)

        renamer = RenameVisitor(var_mapping)
        result = renamer.walk(logical)

        # Also need to append the equality for each renamed constant. E.g., if the mapping
        # contains (50.0::FLOAT -> arg_2::FLOAT), we need to add
        # `eq(arg_2::FLOAT, 50.0::FLOAT)` to the result.
        value_eqs = []
        for (old_var, new_var) in var_mapping.items():
            if not isinstance(old_var, ir.Var):
                value_eqs.append(f.lookup(rel_builtins.eq, [new_var, old_var]))

        return ir.Logical(
            result.engine,
            result.hoisted,
            tuple(value_eqs) + tuple(result.body),
            result.annotations,
        )

    # This function is the main workhorse for this rewrite pass. It takes a list of tasks
    # that define the same relation, and combines them into a single task that defines
    # the relation using a union of all of the bodies.
    def _combine_tasks_into_union(self, tasks: list[ir.Logical]) -> ir.Logical:
        # Step 1: Rename the variables in all tasks so that they will match the final derive
        # after reconstructing into a union
        renamed_tasks = [self._rename_variables(task) for task in tasks]

        # Step 2: Get the final derive
        derives = self._get_heads(renamed_tasks[0])
        assert len(derives) == 1, "should only have one derive in a logical at this stage"
        # Also make sure that all the derives are the same. This should be the case because
        # we renamed all the variables to be the same in step 1.
        for task in renamed_tasks[1:]:
            assert self._get_heads(task) == derives, "all derives should be the same"

        derive = derives[0]

        # Step 3: Remove the final `derive` from each task
        renamed_task_bodies = [
            f.logical(
                tuple(self._get_non_heads(t)),  # Only keep non-head tasks
                t.hoisted,
                t.engine,
            )
            for t in renamed_tasks
        ]

        # Step 4: Construct a union of all the task bodies
        union = f.union(
            tuple(renamed_task_bodies),
            [],
            renamed_tasks[0].engine,
        )

        # Step 5: Add the final derive back
        return f.logical(
            (union, derive),
            [],
            renamed_tasks[0].engine,
        )

# Creates intermediary relations for all Data nodes and replaces said Data nodes
# with a Lookup into these created relations. Reuse duplicate created relations.
class EliminateData(Pass):
    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        r = self.DataRewriter()
        return r.walk(model)

    # Does the actual work.
    class DataRewriter(visitor.Rewriter):
        new_relations: list[ir.Relation]
        new_updates: list[ir.Logical]
        # Counter for naming new relations.
        # It must be that new_count == len new_updates == len new_relations.
        new_count: int
        # Cache for Data nodes to avoid creating duplicate intermediary relations
        data_cache: dict[str, ir.Relation]

        def __init__(self):
            self.new_relations = []
            self.new_updates = []
            self.new_count = 0
            self.data_cache = {}
            super().__init__()

        # Create a cache key for a Data node based on its structure and content
        def _data_cache_key(self, node: ir.Data) -> str:
            values = pd.util.hash_pandas_object(node.data).values
            return hashlib.sha256(bytes(values)).hexdigest()

        def _intermediary_relation(self, node: ir.Data) -> ir.Relation:
            cache_key = self._data_cache_key(node)
            if cache_key in self.data_cache:
                return self.data_cache[cache_key]
            self.new_count += 1
            intermediary_name = f"formerly_Data_{self.new_count}"

            intermediary_relation = f.relation(
                intermediary_name,
                [f.field(v.name, v.type) for v in node.vars]
            )
            self.new_relations.append(intermediary_relation)

            intermediary_update = f.logical([
                # For each row (union), equate values and their variable (logical).
                f.union(
                    [
                        f.logical(
                            [
                                f.lookup(rel_builtins.eq, [f.literal(val), var])
                                for (val, var) in zip(row, node.vars)
                            ],
                        )
                        for row in node
                    ],
                    hoisted = node.vars,
                ),
                # And pop it back into the relation.
                f.update(intermediary_relation, node.vars, ir.Effect.derive),
            ])
            self.new_updates.append(intermediary_update)

            # Cache the result for reuse
            self.data_cache[cache_key] = intermediary_relation

            return intermediary_relation

        # Create a new intermediary relation representing the Data (and pop it in
        # new_updates/new_relations) and replace this Data with a Lookup of said
        # intermediary.
        def handle_data(self, node: ir.Data, parent: ir.Node) -> ir.Lookup:
            intermediary_relation = self._intermediary_relation(node)
            replacement_lookup = f.lookup(intermediary_relation, node.vars)

            return replacement_lookup

        # Walks the model for the handle_data work then updates the model with
        # the new state.
        def handle_model(self, model: ir.Model, parent: None):
            walked_model = super().handle_model(model, parent)
            assert len(self.new_relations) == len(self.new_updates) and self.new_count == len(self.new_relations)

            # This is okay because its LQP.
            assert isinstance(walked_model.root, ir.Logical)
            root_logical = cast(ir.Logical, walked_model.root)

            # We may need to add the new intermediaries from handle_data to the model.
            if self.new_count  == 0:
                return model
            else:
                return ir.Model(
                    walked_model.engines,
                    walked_model.relations | self.new_relations,
                    walked_model.types,
                    ir.Logical(
                        root_logical.engine,
                        root_logical.hoisted,
                        root_logical.body + tuple(self.new_updates),
                        root_logical.annotations,
                    ),
                    walked_model.annotations,
                )

# Deduplicate Vars in Updates and Outputs.
class DeduplicateVars(Pass):
    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        r = self.VarDeduplicator()
        return r.walk(model)

    # Return 1) a new list of Values with no duplicates (at the object level) and
    # 2) equalities between any original Value and a deduplicated Value.
    @staticmethod
    def dedup_values(vals: Sequence[ir.Value]) -> Tuple[List[ir.Value], List[ir.Lookup]]:
        # If a var is seen more than once, it is a duplicate and we will create
        # a new Var and equate it with the seen one.
        seen_vars = set()

        new_vals = []
        eqs = []

        for i, val in enumerate(vals):
            # Duplicates can only occur within Vars.
            # TODO: we don't know for sure if these are the only relevant cases.
            if isinstance(val, ir.Default) or isinstance(val, ir.Var):
                var = val if isinstance(val, ir.Var) else val.var
                if var in seen_vars:
                    new_var = ir.Var(var.type, var.name + "_dup_" + str(i))
                    new_val = new_var if isinstance(val, ir.Var) else ir.Default(new_var, val.value)
                    new_vals.append(new_val)
                    eqs.append(f.lookup(rel_builtins.eq, [new_var, var]))
                else:
                    seen_vars.add(var)
                    new_vals.append(val)
            else:
                # No possibility of problematic duplication.
                new_vals.append(val)

        return new_vals, eqs

    # Returns a reconstructed output with no duplicate variable objects
    # (dedup_values) and now necessary equalities between any two previously
    # duplicate variables.
    @staticmethod
    def dedup_output(output: ir.Output) -> List[Union[ir.Output, ir.Lookup]]:
        vals = helpers.output_values(output.aliases)
        deduped_vals, req_lookups = DeduplicateVars.dedup_values(vals)
        # Need the names so we can recombine.
        alias_names = output_names(output.aliases)
        new_output = ir.Output(
            output.engine,
            FrozenOrderedSet(list(zip(alias_names, deduped_vals))),
            output.keys,
            output.annotations,
        )
        return req_lookups + [new_output]

    # Returns a replacement update with no duplicate variable objects
    # (dedup_values) and now necessary equalities between any two previously
    # duplicate variables.
    @staticmethod
    def dedup_update(update: ir.Update) -> List[Union[ir.Update, ir.Lookup]]:
        deduped_vals, req_lookups = DeduplicateVars.dedup_values(update.args)
        new_update = ir.Update(
            update.engine,
            update.relation,
            tuple(deduped_vals),
            update.effect,
            update.annotations,
        )
        return req_lookups + [new_update]

    # Does the actual work.
    class VarDeduplicator(visitor.Rewriter):
        def __init__(self):
            super().__init__()

        # We implement handle_logical instead of handle_update/handle_output
        # because in addition to modifying said update/output we require new
        # lookups (equality between original and deduplicated variables).
        def handle_logical(self, node: ir.Logical, parent: ir.Node):
            # In order to recurse over subtasks.
            node = super().handle_logical(node, parent)

            new_body = []
            for subtask in node.body:
                if isinstance(subtask, ir.Output):
                    new_body.extend(DeduplicateVars.dedup_output(subtask))
                elif isinstance(subtask, ir.Update):
                    new_body.extend(DeduplicateVars.dedup_update(subtask))
                else:
                    new_body.append(subtask)

            return ir.Logical(
                node.engine,
                node.hoisted,
                tuple(new_body),
                node.annotations
            )

# Generate date arithmetic expressions, such as
# `rel_primitive_date_add(:day, [date] delta, res_2)` by finding the period
# expression for the delta and adding the period type to the date arithmetic expression.
#
# date_add and it's kin are generated by a period expression, e.g.,
# `day(delta, res_1)`
# followed by the date arithmetic expression using the period
# `date_add([date] res_1 res_2)`
class PeriodMath(Pass):
    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        period_rewriter = self.PeriodRewriter()
        model = period_rewriter.walk(model)
        period_math_rewriter = self.PeriodMathRewriter(period_rewriter.period_vars)
        model = period_math_rewriter.walk(model)
        return model

    # Find all period builtins. We need to make them safe for the emitter (either by
    # translating to a cast, or removing) and store the variable and period type for use
    # in the date/datetime add/subtract expressions.
    class PeriodRewriter(visitor.Rewriter):
        def __init__(self):
            super().__init__()
            self.period_vars: dict[ir.Var, str] = {}

        def handle_lookup(self, node: ir.Lookup, parent: ir.Node) -> ir.Lookup:
            if not rel_builtins.is_builtin(node.relation):
                return node

            if node.relation.name not in {
                "year", "month", "week", "day", "hour", "minute", "second", "millisecond", "microsecond", "nanosecond"
            }:
                return node

            assert len(node.args) == 2, "Expect 2 arguments for period builtins"
            assert isinstance(node.args[1], ir.Var), "Expect result to be a variable"
            period = node.relation.name
            result_var = node.args[1]
            self.period_vars[result_var] = period

            # Ideally we could now remove the unused and unhandled period type construction
            # but we may also need to cast the original variable to an Int64 for use by the
            # date/datetime add/subtract expressions.
            # TODO: Remove the node entirely where possible and update uses of the result
            return f.lookup(rel_builtins.cast, [types.Int64, node.args[0], result_var])

    # Update date/datetime add/subtract expressions with period information.
    class PeriodMathRewriter(visitor.Rewriter):
        def __init__(self, period_vars: dict[ir.Var, str]):
            super().__init__()
            self.period_vars: dict[ir.Var, str] = period_vars

        def handle_lookup(self, node: ir.Lookup, parent: ir.Node) -> ir.Lookup:
            if not rel_builtins.is_builtin(node.relation):
                return node

            if node.relation.name not in {
                "date_add", "date_subtract", "datetime_add", "datetime_subtract"
            }:
                return node

            if len(node.args) == 4:
                # We've already visited this lookup
                return node

            assert isinstance(node.args[1], ir.Var), "Expect period to be a variable"
            period_var = node.args[1]
            assert period_var in self.period_vars, "datemath found, but no vars to insert"

            period = self.period_vars[period_var]

            new_args = [f.literal(period, types.Symbol)] + [arg for arg in node.args]

            return f.lookup(node.relation, new_args)

# Rewrite constants to vars in Updates. This results in a more normalized format where
# updates contain only variables. This allows for easier rewrites in later passes.
class ConstantsToVars(Pass):
    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        r = self.ConstantToVarRewriter()
        return r.walk(model)

    # Return 1) a new list of Values with no duplicates (at the object level) and
    # 2) equalities between any original Value and a deduplicated Value.
    @staticmethod
    def replace_constants_with_vars(vals: Sequence[ir.Value]) -> Tuple[List[ir.Value], List[ir.Lookup]]:
        new_vals = []
        eqs = []

        for i, val in enumerate(vals):
            if isinstance(val, ir.PyValue) or isinstance(val, ir.Literal):
                # Replace constant with a new Var.
                typ = typer.to_type(val)
                assert isinstance(typ, ir.ScalarType), "can only replace scalar constants with vars"
                new_var = ir.Var(typ, f"{typ.name.lower()}_{i}")
                new_vals.append(new_var)
                eqs.append(f.lookup(rel_builtins.eq, [new_var, val]))
            else:
                new_vals.append(val)

        return new_vals, eqs

    @staticmethod
    def dedup_update(update: ir.Update) -> List[Union[ir.Update, ir.Lookup]]:
        deduped_vals, req_lookups = ConstantsToVars.replace_constants_with_vars(update.args)
        new_update = ir.Update(
            update.engine,
            update.relation,
            tuple(deduped_vals),
            update.effect,
            update.annotations,
        )
        return req_lookups + [new_update]

    # Does the actual work.
    class ConstantToVarRewriter(visitor.Rewriter):
        def __init__(self):
            super().__init__()

        # We implement handle_logical instead of handle_update because in
        # addition to modifying said update we require new lookups (equality
        # between original and deduplicated variables).
        def handle_logical(self, node: ir.Logical, parent: ir.Node):
            # In order to recurse over subtasks.
            node = super().handle_logical(node, parent)

            new_body = []
            for subtask in node.body:
                if isinstance(subtask, ir.Update):
                    new_body.extend(ConstantsToVars.dedup_update(subtask))
                else:
                    new_body.append(subtask)

            return ir.Logical(
                node.engine,
                node.hoisted,
                tuple(new_body),
                node.annotations
            )
