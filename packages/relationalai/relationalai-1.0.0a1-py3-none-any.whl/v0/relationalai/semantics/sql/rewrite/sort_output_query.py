from typing import cast

from v0.relationalai.semantics.metamodel import ir, compiler as c, factory as f, builtins
from v0.relationalai.semantics.metamodel.builtins import concept_relation_annotation
from v0.relationalai.semantics.metamodel.util import ordered_set, OrderedSet
from v0.relationalai.semantics.metamodel.dependency import analyze_bindings


class SortOutputQuery(c.Pass):
    """
        This pass reorders lookups and logical tasks inside the model to ensure deterministic ordering of dependencies
        for queries that produce output.

        Algorithm Overview:
        -------------------
        1. For each top-level logical in the model that contains `ir.Output` inside:
           - Partition its inner tasks into:
             * Logical nodes
             * Top-level lookups (non-builtins)
             * Other tasks (including builtins)

        2. Build a mapping from each variable to the top-level lookups that produce it.

        3. For each logical node:
           a. Identify bound variables (variables it consumes).
           b. Sort **only the inner lookups** (excluding builtins) in a deterministic order
              based on their variable dependencies.
           c. Append any non-lookup or builtin tasks in their original order.
           d. Find the "best" top-level lookup that matches the logical's input variables,
              preferring lookups without `concept_relation_annotation` in their annotations.
              If found, add it to the new top-level body and remove it from the pool so
              it won't be reused.

        4. After all logical nodes are processed:
           - Add any remaining reachable top-level lookups by expanding the current variable
             domain.
           - Append any leftover unconnected lookups.
           - Append the other inner tasks (builtins, constructs, etc.).

        5. Replace the original logical body with the reordered one.

        Stability:
        ----------
        - Applies only after Flatten pass.
        - Only logicals containing `ir.Output` are processed, so non-output queries remain untouched.

        Examples:

            #1

            Flatten IR:
                Logical
                    Logical
                        Person(person::Person)
                        Logical ^[car=None]
                            Car(car::Car)
                            owns(person::Person, car::Car)
                        Car(car::Car)
                        Logical ^[state=None]
                            State(state::State)
                            registered_in(car::Car, state::State)
                        -> output[person::Person, car::Car, state::State](car::Car as 'car', state::State as 'state')

            Sorted IR:
                Logical
                    Logical
                        Person(person::Person)
                        Logical ^[car=None]
                            owns(person::Person, car::Car)
                            Car(car::Car)
                        Car(car::Car)
                        Logical ^[state=None]
                            registered_in(car::Car, state::State)
                            State(state::State)
                        -> output[person::Person, car::Car, state::State](car::Car as 'car', state::State as 'state')

            #2

            Flatten IR:
                Logical
                    Logical
                        Student(student::Student)
                        goes_at(student::Student, school::School)
                        subject(school::School, subject::Subject)
                        desc(subject::Subject, desc::String)
                        desc::String = "English"
                        Logical ^[id=None]
                            id(student::Student, id::Int128)
                        Logical ^[name=None, course=None]
                            attends(student::Student, course::Course)
                            instructor(course::Course, instructor::Instructor)
                            name(instructor::Instructor, name::String)
                        -> output[student::Student, course::Course, subject::Subject](id::Int128 as 'id', name::String as 'name', desc::String as 'desc')

            Sorted IR:
                Logical
                    Logical
                        goes_at(student::Student, school::School)
                        Logical ^[id=None]
                            id(student::Student, id::Int128)
                        Student(student::Student)
                        Logical ^[name=None, course=None]
                            attends(student::Student, course::Course)
                            instructor(course::Course, instructor::Instructor)
                            name(instructor::Instructor, name::String)
                        subject(school::School, subject::Subject)
                        desc(subject::Subject, desc::String)
                        desc::String = "English"
                        -> output[student::Student, course::Course, subject::Subject](id::Int128 as 'id', name::String as 'name', desc::String as 'desc')
    """
    def rewrite(self, model: ir.Model, options: dict = {}) -> ir.Model:
        root_logical = cast(ir.Logical, model.root)

        output_task_ids = set()
        for task in root_logical.body:
            if isinstance(task, ir.Logical) and self._is_query(task):
                output_task_ids.add(task.id)

        if not output_task_ids:
            return model

        new_model_body = []
        bindings_info = analyze_bindings(root_logical)
        for task in root_logical.body:
            if task.id not in output_task_ids:
                new_model_body.append(task)
                continue

            id_to_logical = {}
            id_to_top_level_lookup = {}
            other_inner_tasks = []

            top_level_logical = cast(ir.Logical, task)

            # Partition inner tasks
            for inner_task in top_level_logical.body:
                if isinstance(inner_task, ir.Logical):
                    id_to_logical[inner_task.id] = inner_task
                elif isinstance(inner_task, ir.Lookup):
                    if builtins.is_builtin(inner_task.relation):
                        other_inner_tasks.append(inner_task)
                    else:
                        id_to_top_level_lookup[inner_task.id] = inner_task
                else:
                    other_inner_tasks.append(inner_task)

            # Variable → top-level lookups producing it
            var_to_top_lookups = {}
            for lookup in id_to_top_level_lookup.values():
                for var in bindings_info.output_bindings.get(lookup.id, ordered_set()):
                    var_to_top_lookups.setdefault(var, []).append(lookup)

            # --- Process logicals and directly attach best matching top-level lookup ---
            new_top_level_body = []
            domain = ordered_set()

            for lid, logical in id_to_logical.items():
                original_bound_vars = bindings_info.input_bindings.get(logical.id, ordered_set())
                bound_vars = OrderedSet.from_iterable(original_bound_vars)
                domain.update(bound_vars)

                # Order inner lookups in a single pass
                ordered_inner, leftover_inner = self._order_lookups(
                    [task for task in logical.body if isinstance(task, ir.Lookup) and not builtins.is_builtin(task.relation)],
                    bindings_info.output_bindings,
                    bound_vars
                )

                ordered_inner.extend(t for t in logical.body if not isinstance(t, ir.Lookup) or
                                     (isinstance(t, ir.Lookup) and builtins.is_builtin(t.relation)))
                sorted_logical = f.logical(ordered_inner + leftover_inner, logical.hoisted, logical.engine, logical.annotations)

                # Find best candidate top-level lookup using var_to_top_lookups
                candidates = OrderedSet.from_iterable(c for var in original_bound_vars for c in reversed(var_to_top_lookups.get(var, ())))
                best = self._pick_best_candidate(candidates)
                if best:
                    new_top_level_body.append(best)
                    outputs = bindings_info.output_bindings.get(best.id, ordered_set())
                    domain.update(outputs)
                    # remove from mapping so it won't be picked again
                    for var in outputs:
                        var_to_top_lookups[var] = [lookup for lookup in var_to_top_lookups[var] if lookup != best]

                new_top_level_body.append(sorted_logical)

            # --- Add any remaining top-level lookups reachable from domain ---
            reachable = ordered_set()
            queue = OrderedSet.from_iterable(domain)
            while queue:
                var = queue.pop()
                for lookup in var_to_top_lookups.get(var, ()):
                    if lookup not in reachable:
                        reachable.add(lookup)
                        new_top_level_body.append(lookup)
                        new_vars = bindings_info.output_bindings.get(lookup.id, ordered_set())
                        domain.update(new_vars)
                        queue.update(new_vars)

            # Add any leftover unconnected lookups
            unused = [lookup for lookup in id_to_top_level_lookup.values() if lookup not in new_top_level_body]
            new_top_level_body.extend(unused)
            new_top_level_body.extend(other_inner_tasks)

            new_model_body.append(
                f.logical(new_top_level_body, top_level_logical.hoisted, top_level_logical.engine,
                          list(top_level_logical.annotations))
            )

        return model.reconstruct(model.engines, model.relations, model.types, f.logical(new_model_body),
                                 model.annotations)

    def _order_lookups(self, lookups, outputs_map, bound_vars):
        ordered = []
        queue = lookups[:]
        while queue:
            progress = False
            remaining = []
            for lookup in queue:
                outputs = outputs_map.get(lookup.id, ordered_set())
                if outputs & bound_vars:
                    ordered.append(lookup)
                    bound_vars.update(outputs)
                    progress = True
                else:
                    remaining.append(lookup)
            if not progress:
                break
            queue = remaining
        return ordered, queue

    def _pick_best_candidate(self, candidates):
        if not candidates:
            return None
        best = None
        for candidate in candidates:
            if not best:
                best = candidate
            elif concept_relation_annotation not in candidate.relation.annotations:
                best = candidate
        return best

    def _is_query(self, task: ir.Logical):
        for sub_task in task.body:
            if isinstance(sub_task, ir.Output):
                return True
        return False