from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from v0.relationalai.semantics.metamodel import ir, factory as f, helpers, visitor
from v0.relationalai.semantics.metamodel.compiler import Pass
from v0.relationalai.semantics.metamodel.util import OrderedSet, ordered_set
from v0.relationalai.semantics.metamodel import dependency
from v0.relationalai.semantics.metamodel import builtins

from functools import reduce

class ExtractCommon(Pass):
    """
    Pass to analyze Logical bodies and extract lookups in their own Logical if it makes
    sense. The heuristic is that, if there are multiple lookups, and there are also multiple
    sibling nested logicals that will eventually be extracted by Flatten, then it makes
    sense to extract these logicals into their own "rule", and then make the original body
    just lookup this common rule.

    From:
        Logical
            Logical
                lookup1
                lookup2
                Logical1 ...
                Logical2 ...
    To:
        Logical
            Logical
                lookup1
                lookup2
                derive common
            Logical
                lookup common
                Logical1 ...
                Logical2 ...
    """

    # The extraction plan heuristic is as follows:
    #
    # Given a set of binder tasks B and a set of extractable tasks E, we find:
    #   - A subset of common tasks C in B, and
    #   - A subset of exposed variables V output from tasks in C
    # where:
    #   - The intersection of common dependencies of all tasks in E are contained in C
    #     (including transitive dependencies)
    #   - The union of input variables for all tasks in E intersected with the output
    #     variables of tasks in C are contained in V

    #--------------------------------------------------
    # Public API
    #--------------------------------------------------
    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        # create the  context
        ctx = ExtractCommon.Context(model, options)

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

    #--------------------------------------------------
    # Extra classes
    #--------------------------------------------------

    class Context():
        def __init__(self, model: ir.Model, options: dict):
            self.rewrite_ctx = helpers.RewriteContext()
            self.info = dependency.analyze(model.root)
            self.options = options

    @dataclass
    class ExtractionPlan():
        # tasks to extract to the body of the common logical
        common_body: OrderedSet[ir.Task]
        # tasks to remain in the original body
        remaining_body: OrderedSet[ir.Task]
        # variables to be exposed by the common logical
        exposed_vars: OrderedSet[ir.Var]
        # map from nested composite to the tasks in the common body that still need to be
        # included in its body, because it contains variables not exposed by the common logical
        local_dependencies: dict[ir.Task, OrderedSet[ir.Task]]
        # a reference to the common connection created for this plan, if any
        common_reference: Optional[ir.Lookup] = None

    #--------------------------------------------------
    # IR handlers
    #--------------------------------------------------

    def handle(self, task: ir.Task, ctx: Context):
        # Currently we only extract if it's a sequence of Logicals, but we could in the
        # future support other intermediate nodes
        if isinstance(task, ir.Logical):
            return self.handle_logical(task, ctx)
        else:
            return task

    def handle_logical(self, task: ir.Logical, ctx: Context):
        # Process the original body to find candidates for extraction. Each task is in one
        # of three categories:
        # - Binders: tasks that bind variables. These are candidates for extracting into
        #   the common body.
        # - Flattenables: tasks that will later be extracted by the Flatten pass
        # - Other: tasks that are neither binders nor flattenables; these will remain
        #   in the body as-is.

        binders = ordered_set()
        flattenables = ordered_set()
        other = ordered_set()

        for child in task.body:
            if _is_binder(child):
                binders.add(child)
            elif _is_flattenable(ctx, child):
                flattenables.add(child)
            else:
                other.add(child)

        # The new body of the rewritten task
        body:OrderedSet[ir.Task] = ordered_set()

        # Quick check to see if it's worth doing more analysis; we only want to extract
        # common binders if there are multiple, and there are also multiple flattenables
        # that will be extracted by the flatten pass later (so that they can share the
        # extracted logic).
        plan: Optional[ExtractCommon.ExtractionPlan] = None
        if len(binders) > 1 and len(flattenables) > 1:
            plan = _create_extraction_plan(ctx, binders, flattenables, other)
            if plan:
                # plan is worthwhile, extract the common body and add the connection to the body
                exposed_vars = plan.exposed_vars.get_list()
                plan.common_reference = f.lookup(helpers.extract(task, plan.common_body, exposed_vars, ctx.rewrite_ctx, "common"), exposed_vars)

                # Add plan common reference to the body.
                body.add(plan.common_reference)

        # recursively handle children
        for child in task.body:
            # skip children that were extracted
            if plan and child not in other and child not in plan.remaining_body and child not in flattenables:
                continue

            # no plan or child is not a composite, so just add the handled to the body
            if not plan or child not in flattenables:
                body.add(self.handle(child, ctx))
                continue

            # there is a plan and the child is in composites, so...
            replacement = self.handle(child, ctx)

            # this child needs either extra local dependencies or the common reference
            if child in plan.local_dependencies:
                # the new body will have maybe the common reference and the local deps
                replacement_body = ordered_set()

                hoisted = OrderedSet()
                if isinstance(replacement, ir.Logical):
                    # if replacement is a logical, just keep the same hoisted vars
                    hoisted.update(replacement.hoisted)
                else:
                    # otherwise, we need to hoist the vars that are output from local deps
                    # and input to the replacement task
                    dep_outputs = OrderedSet()
                    for d in plan.local_dependencies.get(child, ordered_set()):
                        dep_outputs.update(ctx.info.task_outputs(d))
                    hoisted.update(dep_outputs & ctx.info.task_inputs(replacement))

                if child in plan.local_dependencies:
                    for local_dep in plan.local_dependencies[child]:
                        replacement_body.add(local_dep.clone())

                if isinstance(replacement, ir.Logical):
                    # if the replacements is a logical, we can just add to the body
                    body.add(replacement.reconstruct(
                        replacement.engine,
                        tuple(hoisted.get_list()),
                        tuple(replacement_body.update(replacement.body).get_list()),
                        replacement.annotations
                    ))
                else:
                    # Otherwise, wrap the local dependencies in a Lookup where the output
                    # variables are hoisted, and keep the computed replacement.
                    body.add(f.logical(replacement_body.get_list(), hoisted.get_list(), replacement.engine))
                    body.add(replacement)
            else:
                # child does not need extras in the body, just add it to the main body
                body.add(replacement)

        return ir.Logical(task.engine, task.hoisted, tuple(body))


#--------------------------------------------------
# Utilities
#--------------------------------------------------

def _create_extraction_plan(ctx: ExtractCommon.Context, binders: OrderedSet[ir.Task], flattenables: OrderedSet[ir.Task], others: OrderedSet[ir.Task]) -> Optional[ExtractCommon.ExtractionPlan]:
    """
    Compute a plan to extract tasks in this frame that are common dependencies
    across these composite tasks.
    """
    # If there are any pragma lookups, then don't extract anything. Pragma lookups are
    # designed to control execution order, and extracting them may affect their
    # semantics.
    for b in binders:
        if isinstance(b, ir.Lookup) and builtins.is_pragma(b.relation):
            return None

    # Compute intersection of task dependencies
    all_deps = [ctx.info.task_dependencies(f) for f in flattenables]
    deps = reduce(lambda a, b: a & b, all_deps)
    common_body = binders & deps

    # We don't need to extract anything if there's only zero or one common tasks
    if len(common_body) < 2:
        return None

    # Keep track of remaining tasks that are not extracted in the common body
    remaining = ordered_set()

    # Compute the vars that should be output from the common body. These are the union of
    # all input vars across all non-extracted tasks, intersected with output vars of
    # the common body.

    # First, compute the output vars of the common body
    common_body_output_vars = OrderedSet()
    for child in common_body:
        common_body_output_vars.update(ctx.info.task_outputs(child))

    # Next, compute the union of the input vars of all non-extracted tasks
    non_extracted_tasks = (binders - common_body) | flattenables | others
    all_exposed_vars: list[OrderedSet[ir.Var]] = []
    for t in non_extracted_tasks:
        input_vars = ctx.info.task_inputs(t)
        all_exposed_vars.append(input_vars if input_vars else OrderedSet())

    exposed_vars = reduce(lambda a, b: a | b, all_exposed_vars) & common_body_output_vars

    # If there are no vars in common, then it's not worth extracting
    if not exposed_vars:
        return None

    # Make sure that all local dependencies of the common body are included in the common
    # body. This is important for the safety of this rewrite.
    for task in common_body:
        local_deps = ctx.info.local_dependencies(task)
        if local_deps:
            common_body.update(local_deps & binders)

    # check which of the original binders remain, and make sure their dependencies also stay
    for binder in binders:
        if binder not in common_body:
            remaining.add(binder)
            deps = _compute_local_dependencies(ctx, binders, binder, exposed_vars)
            if deps:
                remaining.update(deps)

    # for each composite, check if there are additional tasks needed, because the task
    # depends on it but it is not exposed by the vars
    local_dependencies: dict[ir.Task, OrderedSet[ir.Task]] = dict()
    for flattenable in flattenables:
        local = _compute_local_dependencies(ctx, binders, flattenable, exposed_vars)
        if local:
            local_dependencies[flattenable] = local

    return ExtractCommon.ExtractionPlan(common_body, remaining, exposed_vars, local_dependencies)

def _compute_local_dependencies(ctx: ExtractCommon.Context, binders: OrderedSet[ir.Task], composite: ir.Task, exposed_vars: OrderedSet[ir.Var]):
    """
    The tasks in common_body will be extracted into a logical that will expose the exposed_vars.
    Compute which additional dependencies are needed specifically for this composite, because
    it depends on some tasks that are extracted to common_body but not exposed by exposed_vars.
    """

    # working list of vars we still need to fulfill
    inputs = ctx.info.task_inputs(composite)
    if not inputs:
        return None

    # vars exposed by exposed vars + tasks added to the local body
    vars_exposed = OrderedSet.from_iterable(exposed_vars)
    vars_needed = (inputs - vars_exposed)
    if not vars_needed:
        return None

    # this is a greedy algorithm that uses the first task in the common body that provides
    # a variable needed; it may result in sub-optimal extraction, but should be correct
    local_body = ordered_set()
    while(vars_needed):
        v = vars_needed.pop()
        for x in binders:
            if x not in local_body:
                # an x that is not yet in local_body can fulfill v
                x_outputs = ctx.info.task_outputs(x)
                if x_outputs and v in x_outputs:
                    # add it to local_body and add its outputs to vars exposed
                    local_body.add(x)
                    vars_exposed.add(x_outputs)
                    # but add its inputs the vars now needed
                    inputs = ctx.info.task_inputs(x)
                    if inputs:
                        vars_needed.update(inputs - vars_exposed)
    return local_body

def _is_binder(task: ir.Task):
    # If the task itself is a binder
    if any(isinstance(task, binder) for binder in (ir.Lookup, ir.Construct, ir.Exists, ir.Data, ir.Not)):
        return True

    # If the task is a Logical containing only binders
    if isinstance(task, ir.Logical) and all(_is_binder(c) for c in task.body):
        return True

    # If the task is a Union containing only binders
    if isinstance(task, ir.Union) and all(_is_binder(c) for c in task.tasks):
        return True

    return False

def _is_flattenable(ctx: ExtractCommon.Context, task: ir.Task):
    # Each output will be flattened into its own top-level def
    if isinstance(task, ir.Output):
        return True

    extractable_types = (ir.Update, ir.Aggregate, ir.Match, ir.Rank)
    return isinstance(task, ir.Logical) and len(visitor.collect_by_type(extractable_types, task)) > 0
