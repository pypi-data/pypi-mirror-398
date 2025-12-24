from __future__ import annotations
from typing import Optional

from v0.relationalai.semantics.metamodel import ir, factory as f, builtins as bt, types, helpers
from v0.relationalai.semantics.metamodel.compiler import Pass
from v0.relationalai.semantics.metamodel.util import OrderedSet, ordered_set
from v0.relationalai.semantics.metamodel import dependency

class CDC(Pass):
    """
    Pass to process tables brought to Relational AI logical engines by CDC. When CDC occurs,
    wide snowflake tables are shredded into smaller tables. This pass ensures that code that
    reads from the wide relation is changed to read from the smaller tables. Furthermore,
    it attaches the @function annotation to the property lookups, as an optimization.

    Beware that this pass makes assumptions about the names and types of CDC relations and
    columns!

    From:
        Logical
            TPCH.SF1.LINEITEM(l_orderkey, l_partkey, l_suppkey, l_linenumber, l_quantity, l_extendedprice, l_discount, l_tax, l_returnflag, l_linestatus, l_shipdate, l_commitdate, l_receiptdate, l_shipinstruct, l_shipmode, l_comment)
            construct(LineItem, "l_orderkey", l_orderkey, "l_linenumber", l_linenumber, lineitem)
            -> derive LineItem(lineitem)
            -> derive l_orderkey(lineitem, l_orderkey)
            -> derive l_linenumber(lineitem, l_linenumber)
    To:
    Logical
        tpch_sf1_lineitem("L_ORDERKEY", row_id, l_orderkey)
        tpch_sf1_lineitem("L_LINENUMBER", row_id, l_linenumber)
        construct(LineItem, "l_orderkey", l_orderkey, "l_linenumber", l_linenumber, lineitem)
        -> derive LineItem(lineitem)
        -> derive l_orderkey(lineitem, l_orderkey) (@function)
        -> derive l_linenumber(lineitem, l_linenumber) (@function)
    """

    #--------------------------------------------------
    # Public API
    #--------------------------------------------------
    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        # create the dependency analysis context
        ctx = CDC.CDCContext(model)

        # rewrite the root
        replacement = self.handle(model.root, ctx)

        # the new root contains the extracted top level logicals and the rewritten root
        if ctx.rewrite_ctx.top_level:
            new_root = ir.Logical(model.root.engine, tuple(), tuple(ctx.rewrite_ctx.top_level + [replacement]))
        else:
            new_root = replacement

        # create the new model, updating relations and root
        return ir.Model(
            model.engines,
            OrderedSet.from_iterable(model.relations).update(ctx.rewrite_ctx.relations).frozen(),
            model.types,
            new_root
        )

    class CDCContext():
        def __init__(self, model: ir.Model):
            self.model = model
            self.rewrite_ctx = helpers.RewriteContext()
            self.cdc_relations = dict()
            self.info: Optional[dependency.DependencyInfo] = None

        def get_info(self):
            """ Lazily compute info as needed. """
            if self.info is None:
                # no need for dependency analsyis, only inputs/outputs
                self.info = dependency.analyze_bindings(self.model.root)
            return self.info

    #--------------------------------------------------
    # IR handlers
    #--------------------------------------------------

    def handle(self, task: ir.Task, ctx: CDC.CDCContext):
        # currently we only extract if it's a sequence of Logicals, but we could in the
        # future support other intermediate nodes
        if isinstance(task, ir.Logical):
            return self.handle_logical(task, ctx)
        elif isinstance(task, ir.Not):
            return self.handle_not(task, ctx)
        else:
            return task

    def handle_logical(self, task: ir.Logical, ctx: CDC.CDCContext):

        wide_cdc_table_lookups = ordered_set()
        for child in task.body:
            if isinstance(child, ir.Lookup) and bt.from_cdc_annotation in child.relation.annotations:
                wide_cdc_table_lookups.add(child)

        # optimization to avoid creating a frame if unnecessary
        if not wide_cdc_table_lookups:
            # no need to analyze dependencies, just handle children recursively and
            # reconstruct the logical
            body:OrderedSet[ir.Task] = ordered_set()
            for child in task.body:
                body.add(self.handle(child, ctx))
            return ir.Logical(task.engine, task.hoisted, tuple(body), task.annotations)

        # ensure function annotation is in the model
        # TODO: need to revisit this to add @function annotations only when we really need them
        # ctx.analysis_ctx.relations.append(rel_bt.function)

        # process the children
        body:OrderedSet[ir.Task] = ordered_set()

        # find variables required by the other tasks
        required_vars = ordered_set()
        for child in task.body:
            if child not in wide_cdc_table_lookups:
                required_vars.update(ctx.get_info().task_inputs(child))
                #
                # Vars used in atoms (outputs) may be column variables:
                # e.g.:
                #       Transaction.type(source.COLUMN)
                #    or
                #       Transaction.type = source.COLUMN
                #
                # Neither of these mark their vars as inputs, so we pull from the outputs as well.
                # The only exception is RowId, since there's no need to join on `METADATA$KEY` if
                # a non-table atom has `RowId` in keys.
                #
                output_vars = ctx.get_info().task_outputs(child) or []
                output_vars = [var for var in output_vars if not types.matches(var.type, types.RowId)]
                required_vars.update(output_vars)

        # We must return anything that's hoisted
        required_vars.update(helpers.hoisted_vars(task.hoisted))

        # rewrite the cdc table lookup into lookups for each required variable
        for child in task.body:
            if child in wide_cdc_table_lookups:
                assert isinstance(child, ir.Lookup)
                wide_relation = child.relation
                properties = required_vars & ctx.get_info().task_outputs(child)
                if properties:
                    assert isinstance(child.args[0], ir.Var) and types.matches(child.args[0].type, types.RowId)
                    row_id = child.args[0]
                    for property in properties:
                        if types.matches(property.type, types.RowId) and len(properties) > 1:
                            continue

                        relation = self._get_property_cdc_relation(wide_relation, property, ctx)
                        field_name = ir.Literal(types.Symbol, property.name)
                        if types.matches(property.type, types.RowId):
                            field_name = ir.Literal(types.Symbol, "METADATA$KEY")
                            property = ir.Var(type=types.RowId, name=property.name)

                            # METADATA$KEY is unary
                            relation = f.relation(
                                relation.name,
                                [f.field("symbol", types.Symbol), f.field("row_id", types.RowId)],
                                annos=[*relation.annotations],
                            )
                            body.add(ir.Lookup(
                                task.engine,
                                relation,
                                tuple([field_name, row_id])
                            ))
                        else:
                            body.add(ir.Lookup(
                                task.engine,
                                relation,
                                tuple([field_name, row_id, property])
                            ))

            # handle non cdc table children, adding @function to the updates
            for child in task.body:
                if child not in wide_cdc_table_lookups:
                    body.add(self.handle(child, ctx))

                    # TODO: need to revisit this to add @function annotations only when we really need them
                    # replacement = self.handle(child, ctx)
                    # if isinstance(replacement, ir.Update):
                    #     if len(replacement.args) == 1:
                    #         body.add(replacement)
                    #     else:
                    #         body.add(replacement.reconstruct(
                    #             replacement.engine,
                    #             replacement.relation,
                    #             replacement.args,
                    #             replacement.effect,
                    #             replacement.annotations | [rel_bt.function_annotation]
                    #         ))
                    # else:
                    #     body.add(replacement)

        return ir.Logical(task.engine, task.hoisted, tuple(body), task.annotations)

    def handle_not(self, not_task: ir.Not, ctx: CDC.CDCContext):
        sub_task = self.handle(not_task.task, ctx)
        return ir.Not(not_task.engine, sub_task, not_task.annotations)

    def _get_property_cdc_relation(self, wide_cdc_relation: ir.Relation, property: ir.Var, ctx: CDC.CDCContext):
        """
        Get the relation that represents this property var in this wide_cdc_relation. If the
        relation is not yet available in the context, this method will create and register it.
        """
        relation_name = wide_cdc_relation.name.lower().replace(".", "_")
        key = (relation_name, property.name)
        if key not in ctx.cdc_relations:
            # the property relation is overloaded for all properties of the same wide cdc relation, so they have
            # the same name, but potentially a different type in the value column; also note that they are
            # annotated as external to avoid renaming.
            relation = f.relation(
                relation_name,
                [f.field("symbol", types.Symbol), f.field("row_id", types.Number), f.field("value", property.type)],
                annos=[bt.external_annotation]
            )
            ctx.cdc_relations[key] = relation
            ctx.rewrite_ctx.relations.append(relation)
        return ctx.cdc_relations[key]
