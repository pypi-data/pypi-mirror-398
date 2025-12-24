from __future__ import annotations

from v0.relationalai.semantics.metamodel import ir
from v0.relationalai.semantics.metamodel.compiler import Pass
from v0.relationalai.semantics.metamodel.visitor import Rewriter
from v0.relationalai.semantics.metamodel.util import OrderedSet
from v0.relationalai.semantics.metamodel import helpers, factory as f, types, builtins
from typing import Optional, Any, Iterable, Tuple
from collections import defaultdict

"""
Given an Output with a group of keys (some of them potentially null),
* extract the lookups that bind (transitively) all the keys
* extract the lookups that bind (transitively) properties of the keys
* generate all the valid combinations of keys being present or not
  * first all keys are present,
  * then we remove one key at a time,
  * then we remove two keys at a time,and so on.
  * the last combination is when all the *nullable* keys are missing.
* for each combination:
  * create a compound (hash) key
  * create a Logical that:
      * contains all the relevant lookups for keys and properties
      * contains negated lookups for null keys
      * outputs using the compound key

E.g., we go from

Logical
    Foo(foo)
    rel1(foo, x)
    Logical ^[v1=None]
        rel2(foo, v1)
    Logical ^[v2=None, k2=None]
        rel3(foo, k2)
        rel4(k2, v2)
    Logical ^[v3=None, k3=None]
        rel5(foo, y)
        rel6(y, k3)
        rel7(k3, v3)
    output[foo, k2, k3](v1, v2, v3)

to

Logical
    Logical
        Logical
            Foo(foo)
            rel1(foo, x)
            Logical ^[k2=None, k3=None]
                rel3(foo, k2)
                rel5(foo, y)
                rel6(y, k3)
            Logical ^[v1=None]
                rel2(foo, v1)
            Logical ^[v2=None, k2=None]
                rel4(k2, v2)
            Logical ^[v3=None, k3=None]
                rel7(k3, v3)
            construct(Hash, "Foo", foo, "Concept2", k2, "Concept3", k3, compound_key)
            output[compound_key](v1, v2, v3)
        Logical
            Foo(foo)
            rel1(foo, x)
            Logical ^[k2=None, k3=None]
                rel5(foo, y)
                rel6(y, k3)
            Not
                Logical
                    rel3(foo, k2)
            Logical ^[v1=None]
                rel2(foo, v1)
            Logical ^[v3=None, k3=None]
                rel7(k3, v3)
            construct(Hash, "Foo", foo, "Concept3", k3, compound_key)
            output[compound_key](v1, None, v3)
        Logical
            Foo(foo)
            rel1(foo, x)
            Logical ^[k2=None, k3=None]
                rel3(foo, k2)
                rel5(foo, y)
            Not
                Logical
                    rel6(y, k3)
            Logical ^[v1=None]
                rel2(foo, v1)
            Logical ^[v2=None, k2=None]
                rel4(k2, v2)
            construct(Hash, "Foo", foo, "Concept2", k2, compound_key)
            output[compound_key](v1, v2, None)
        Logical
            Foo(foo)
            rel1(foo, x)
            Logical ^[k2=None, k3=None]
                rel5(foo, y)
            Not
                Logical
                    rel3(foo, k2)
                    rel6(y, k3)
            Logical ^[v1=None]
                rel2(foo, v1)
            construct(Hash, "Foo", foo, compound_key)
            output[compound_key](v1, None, None)
"""
class ExtractKeys(Pass):
    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        return ExtractKeysRewriter().walk(model)

"""
* First, figure out all tasks that are common for all alternative logicals that will be
  generated
* Second, generate the appropriate negated tasks for when some keys are missing
* Third, add tasks that are needed for the final output columns
  (e.g., lookup name if we select name)
* Lastly, create the approprite Output task, with some of the columns being None if they are
  missing (None will be filtered out in a later step -- we just need the column number to be
  the same here).
"""
class ExtractKeysRewriter(Rewriter):
    def handle_logical(self, node: ir.Logical, parent: ir.Node, ctx:Optional[Any]=None) -> ir.Logical:
        outputs = [x for x in node.body if isinstance(x, ir.Output) and x.keys]
        # We are not in a logical with an output at this level.
        if not outputs:
            new_body = self.walk_list(node.body, node)
            return node if new_body is node.body else f.logical(new_body, node.hoisted)
        assert len(outputs) == 1, "multiple outputs with keys in a logical"
        output = outputs[0]
        assert output.keys
        output_keys = output.keys

        all_vars = OrderedSet.from_iterable(output_keys)
        all_vars.update(helpers.output_vars(output.aliases))

        info = self.preprocess_logical(node, output_keys)
        top_level_tasks, var_to_default, nullable_keys, non_nullable_keys = info
        # we only need to transform the logical if there are nullable keys
        if not nullable_keys:
            return node

        # Flatten the contents of (direct) logicals that comprise the body of this output
        flat_body = OrderedSet[ir.Task]()
        for task in node.body:
            if isinstance(task, ir.Logical):
                if any(isinstance(t, (ir.Aggregate, ir.Rank)) for t in task.body):
                    flat_body.add(task)
                else:
                    flat_body.update(task.body)
            elif isinstance(task, ir.Output):
                continue
            else:
                flat_body.add(task)

        # Add to all_vars the vars of lookups that were flattened above (from some logical)
        for task in flat_body:
            if isinstance(task, ir.Lookup):
                all_vars.update(helpers.vars(task.args))

        partitions, deps = self.partition_tasks(flat_body, all_vars)

        # Compute all valid key combinations (keys that are not null)
        combinations = self.key_combinations(nullable_keys, deps, 0, non_nullable_keys.get_list())
        # there is no need to transform if there is only a single combination
        if len(combinations) == 1:
            return node

        ####################################################################################

        outer_body: list[ir.Task] = []
        annos = list(output.annotations)
        annos.append(f.annotation(builtins.output_keys, tuple(output_keys)))
        # Create a compound key that will be used in place of the original keys.
        compound_key = f.var("compound_key", types.Hash)

        for key_combination in combinations:
            missing_keys = OrderedSet.from_iterable(output_keys)
            missing_keys.difference_update(key_combination)

            # top-level tasks are always present in every clone
            body = OrderedSet.from_iterable(top_level_tasks)
            # add tasks that are specific to the keys present in the current combination
            for key in key_combination:
                assert key in partitions
                body.update(partitions[key])

            # vars used in a positive context
            positive_vars = OrderedSet[ir.Var]()
            for task in body:
                if isinstance(task, ir.Lookup):
                    positive_vars.update(helpers.vars(task.args))

            # handle the construct node in each clone
            values: list[ir.Value] = [compound_key.type]
            for key in output_keys:
                assert isinstance(key.type, ir.ScalarType)
                values.append(ir.Literal(types.String, key.type.name))
                if key in key_combination:
                    values.append(key)
            body.add(ir.Construct(None, tuple(values), compound_key, OrderedSet().frozen()))

            # find variables used only inside the negated context
            negative_vars = OrderedSet[ir.Var]()
            for key in missing_keys:
                negative_partition = partitions[key]
                for task in negative_partition:
                    if isinstance(task, ir.Lookup):
                        args = helpers.vars(task.args)
                        for arg in args:
                            if arg not in positive_vars:
                                negative_vars.add(arg)

            out_vars = helpers.output_vars(output.aliases)
            # output variables that depend on a missing key. They have to be skipped
            missing_out_vars = OrderedSet[ir.Var]()
            # output variables that depend on a negated variable that's not a missing key
            # they have to be handled in a more complicated manner
            problematic_out_vars = OrderedSet[ir.Var]()
            for out_var in out_vars:
                out_deps = deps[out_var]
                if out_var in missing_keys:
                    missing_out_vars.add(out_var)
                elif any(x in missing_keys for x in out_deps):
                    missing_out_vars.add(out_var)
                elif any(x in negative_vars for x in out_deps):
                    problematic_out_vars.add(out_var)

            if problematic_out_vars:
                assert len(problematic_out_vars) == 1
                exclude_vars = deps[problematic_out_vars[0]] & negative_vars
                has_problematic_var = True
            else:
                exclude_vars = out_vars
                has_problematic_var = False

            self.negate_missing_keys(body, missing_keys, var_to_default, partitions, deps,
                                     out_vars, exclude_vars, negative_vars, has_problematic_var)

            new_output_aliases = []
            for alias, out_value in output.aliases:
                if not isinstance(out_value, ir.Var):
                    new_out_value = out_value
                else:
                    new_out_value = None if out_value in missing_out_vars else out_value
                new_output_aliases.append((alias, new_out_value))
            body.add(f.output(new_output_aliases, [compound_key], annos=annos))

            # Create the final logical for this combination
            outer_body.append(f.logical(tuple(body), []))

        return f.logical(tuple(outer_body), [])

    def noop_logical(self, node: ir.Logical) -> bool:
        # logicals that don't hoist variables are essentially filters like lookups
        if not node.hoisted:
            return True
        if len(node.body) != 1:
            return False
        inner = node.body[0]
        if not isinstance(inner, (ir.Match, ir.Union)):
            return False
        outer_vars = helpers.hoisted_vars(node.hoisted)
        inner_vars = helpers.hoisted_vars(inner.hoisted)
        for v in outer_vars:
            if v not in inner_vars:
                return False
        # all vars hoisted by the outer logical, are also
        # hoisted by the inner Match/Union
        return True

    # compute inital information that's needed for later steps. E.g., what's nullable or
    # not, do some output columns have a default value, etc.
    def preprocess_logical(self, node: ir.Logical, output_keys: Iterable[ir.Var]):
        top_level_tasks = OrderedSet()
        non_nullable_vars = OrderedSet()
        nullable_vars = OrderedSet()
        var_to_default: dict[ir.Var, ir.Default] = {}

        for task in node.body:
            # Top-level lookups use only non-nullable vars
            if isinstance(task, ir.Lookup):
                vars = helpers.vars(task.args)
                non_nullable_vars.update(vars)
                top_level_tasks.add(task)
            elif isinstance(task, ir.Logical):
                if self.noop_logical(task):
                    top_level_tasks.add(task)
                    non_nullable_vars.update(helpers.hoisted_vars(task.hoisted))
                    continue

                for h in task.hoisted:
                    # Hoisted vars without a default are not nullable
                    if isinstance(h, ir.Var):
                        non_nullable_vars.add(h)
                    elif isinstance(h, ir.Default):
                        var_to_default[h.var] = h
                        # Hoisted vars with a non-None default are not nullable
                        if h.value is not None:
                            non_nullable_vars.add(h.var)
                        else:
                            nullable_vars.add(h.var)

            # Variables appearing in an aggregate's group-by are not nullable
            elif isinstance(task, ir.Aggregate):
                top_level_tasks.add(task)
                for v in task.group:
                    non_nullable_vars.add(v)

            elif isinstance(task, ir.Construct):
                top_level_tasks.add(task)
                non_nullable_vars.add(task.id_var)
            elif isinstance(task, ir.Data):
                top_level_tasks.add(task)
                non_nullable_vars.update(task.vars)
            # TODO: should Union and Match be used for hoisted vars?
            elif isinstance(task, (ir.Not, ir.Match, ir.Union)):
                top_level_tasks.add(task)

            else:
                if not isinstance(task, ir.Output):
                    raise ValueError(f"Unexpected task type: {type(task)}")

        # Any variable appearing in both sets is non-nullable
        nullable_vars = nullable_vars - non_nullable_vars

        non_nullable_keys = OrderedSet.from_iterable(output_keys)
        non_nullable_keys.difference_update(nullable_vars)
        nullable_keys = OrderedSet.from_iterable(output_keys)
        nullable_keys.difference_update(non_nullable_keys)

        return top_level_tasks, var_to_default, nullable_keys, non_nullable_keys

    # given a set of variables, compute the tasks that each variable is using and also
    # other variables needed for this variable to bind correctly
    def partition_tasks(self, tasks:Iterable[ir.Task], vars:Iterable[ir.Var]):
        partitions:dict[ir.Var, OrderedSet[ir.Task]] = defaultdict(OrderedSet)
        dependencies:dict[ir.Var, OrderedSet[ir.Var]] = defaultdict(OrderedSet)

        worklist = list(vars)
        while worklist:
            var = worklist.pop()
            extended_vars = OrderedSet[ir.Var]()
            extended_vars.add(var)

            there_is_progress = True
            while there_is_progress:
                there_is_progress = False
                for task in tasks:
                    if task in partitions[var]:
                        continue
                    # Already added this task to this partition
                    elif isinstance(task, ir.Lookup):
                        args = helpers.vars(task.args)
                        if len(args) == 1 and args[0] in extended_vars:
                            partitions[var].add(task)
                        # TODO: hack to have dot_joins work
                        elif len(args) >= 3 and args[-2] in extended_vars:
                            partitions[var].add(task)
                            extended_vars.add(args[-1])
                            dependencies[var].add(args[-1])
                            there_is_progress = True
                        elif len(args) > 1 and args[-1] in extended_vars:
                            partitions[var].add(task)
                            for arg in args[:-1]:
                                extended_vars.add(arg)
                                dependencies[var].add(arg)
                            there_is_progress = True
                    elif isinstance(task, ir.Logical):
                        hoisted = helpers.hoisted_vars(task.hoisted)
                        if var in hoisted:
                            partitions[var].add(task)
                            there_is_progress = True

        return partitions, dependencies

    # Generate all the valid combinations of non-nullable keys and nullable keys.
    def key_combinations(self, nullable_keys: OrderedSet[ir.Var], key_deps, idx: int, non_null_keys: list[ir.Var]) -> OrderedSet[Tuple[ir.Var]]:
        if idx < len(nullable_keys):
            key = nullable_keys[idx]
            set1 = self.key_combinations(nullable_keys, key_deps, idx + 1, non_null_keys + [key])
            set2 = self.key_combinations(nullable_keys, key_deps, idx + 1, non_null_keys)
            set1.update(set2)
            return set1
        else:
            final_keys = []
            for k in non_null_keys:
                # If a key depends on other keys, all of them should be present in this combination.
                # If some dependency is not present, ignore the current key.
                deps = key_deps.get(k)
                if deps and any(dk in nullable_keys and dk not in non_null_keys for dk in deps):
                    continue
                final_keys.append(k)
            return OrderedSet.from_iterable([tuple(final_keys)])

    def negate_missing_keys(self, body, missing_keys, var_to_default, partitions, deps,
                            out_vars, exclude_vars, negative_vars, has_problematic_var:bool):
        # for keys that are not present in the current combination
        # we have to include their tasks negated
        negated_tasks = OrderedSet[ir.Task]()
        positive_tasks = defaultdict(OrderedSet)

        for key in missing_keys:
            negative_body = OrderedSet[ir.Task]()
            negative_partition = partitions[key]
            for task in negative_partition:
                # task is already present positively at the top-level context
                if task in body:
                    continue
                if not isinstance(task, ir.Lookup):
                    negative_body.add(task)
                    continue

                args = helpers.vars(task.args)
                if args[-1] in exclude_vars and args[-1] not in missing_keys:
                    positive_tasks[args[-1]].add(task)
                else:
                    negative_body.add(task)

            negated_tasks.update(negative_body)
            if len(negative_body) > 1:
                body.add(f.not_(f.logical(tuple(negative_body), [])))
            elif len(negative_body) == 1:
                body.add(f.not_(negative_body[0]))

        if positive_tasks:
            for _, d in positive_tasks.items():
                body.update(d)

        for out_var in out_vars:
            out_deps = deps[out_var]
            if has_problematic_var and any(x in missing_keys for x in out_deps):
                continue
            elif not has_problematic_var and any(x in missing_keys or x in negative_vars for x in out_deps):
                continue

            default = var_to_default.get(out_var)
            partition = OrderedSet.from_iterable(partitions[out_var])
            partition.difference_update(body)
            property_body = OrderedSet[ir.Task]()
            if not has_problematic_var:
                for task in partition:
                    if isinstance(task, ir.Lookup):
                        vars = helpers.vars(task.args)
                        if any(x in negative_vars for x in vars):
                            continue
                    property_body.add(task)
            else:
                property_body.update(partition)
            if property_body:
                body.add(f.logical(tuple(property_body), [default] if default else []))
