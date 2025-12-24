"""
    Support for dependency analysis of metamodel IRs.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable, Optional
from itertools import count
from more_itertools import peekable
from v0.relationalai.semantics.metamodel import builtins, ir, helpers, visitor
from v0.relationalai.semantics.metamodel.util import OrderedSet, ordered_set


#--------------------------------------------------
# Public API
#--------------------------------------------------

@dataclass
class DependencyInfo():
    """
    Represents the result of performing binding and dependency analysis on a metamodel tree.

    All dicts are keyed by task ids.
    """
    # input vars for a task
    input_bindings: dict[int, OrderedSet[ir.Var]] = field(default_factory=dict)
    # output vars for a task
    output_bindings: dict[int, OrderedSet[ir.Var]] = field(default_factory=dict)
    # clusters of dependency that each task participates on
    dependency_clusters: dict[int, Cluster] = field(default_factory=dict)
    # keep track of the parents of each task
    parent: dict[int, ir.Task] = field(default_factory=dict)
    # keep track of replacements that were made during a rewrite
    replacements: dict[int, ir.Task] = field(default_factory=dict)

    def task_inputs(self, node: ir.Task) -> Optional[OrderedSet[ir.Var]]:
        """ The input variables for this task, if any. """
        if node.id in self.input_bindings:
            return self.input_bindings[node.id]
        return None

    def has_inputs(self, node: ir.Task):
        return node.id in self.input_bindings

    def task_outputs(self, node: ir.Task) -> Optional[OrderedSet[ir.Var]]:
        """ The output variables for this task, if any. """
        if node.id in self.output_bindings:
            return self.output_bindings[node.id]
        return None

    def has_outputs(self, node: ir.Task):
        return node.id in self.output_bindings

    def task_dependencies(self, task: ir.Task) -> OrderedSet[ir.Task]:
        """
        All dependencies for this task, if any. This includes tasks in outer contexts,
        not only siblings.
        """

        deps = ordered_set()
        cluster = self.dependency_clusters.get(task.id, None)
        parent = self.parent.get(task.id)

        if cluster:
            self._collect_deps(cluster, deps)
        while parent:
            cluster = self.dependency_clusters.get(parent.id, None)
            if cluster:
                self._collect_deps(cluster, deps)
                parent = self.parent[cluster.content[0].id]
            else:
                parent = None
        return self._with_replacements(deps)

    def local_dependencies(self, task: ir.Task) -> Optional[OrderedSet[ir.Task]]:
        """ Similar to task_dependencies but returns only dependencies that are siblings. """

        if task.id in self.dependency_clusters:
            deps = ordered_set()
            self._collect_deps(self.dependency_clusters[task.id], deps)
            return self._with_replacements(deps)
        return None

    def replaced(self, original: ir.Task, replacement: ir.Task):
        """
        Inform that, during some pass, this original task was replaced with this replacement
        task. This affects the info of .task_dependencies(...) since it will answer with
        the replacement when the original is in the set of dependencies.
        """
        self.replacements[original.id] = replacement

    #
    # Implementation details
    #
    def _collect_deps(self, cluster: Cluster, deps: OrderedSet[ir.Task]):
            queue = []
            # start with the cluster dependencies, because cluster represents the task we
            # care about
            queue.extend(cluster.dependencies)
            seen = set()
            while queue:
                cluster = queue.pop()
                if cluster.id in seen:
                    continue
                seen.add(cluster.id)
                deps.update(cluster.content)
                queue.extend(cluster.dependencies)

    def _with_replacements(self, deps):
        # Return deps with all tasks that need replacements (because they are in the
        # replacements dict) replaced.
        if any([dep.id in self.replacements for dep in deps]):
            # Only allocate and compute replacements if there's a dep that was replaced
            info = ordered_set()
            for dep in deps:
                info.add(self.replacements.get(dep.id, dep))
            return info
        return deps


def analyze_bindings(task: ir.Task) -> DependencyInfo:
    """
    Perform just the binding analysis, skipping the dependency analysis. This is useful
    for passes that only require knowing the input/output sets for nodes, but do not need
    the more expensive dependency information.

    The returned DependencyInfo object will only have input and output bindings filled.
    """
    binding = BindingAnalysis()
    task.accept(binding)
    return binding.info

def analyze(task: ir.Task) -> DependencyInfo:
    """
    Perform binding and dependency analysis on this task.

    The returned DependencyInfo object will have all dictionaries filled.
    """
    # first perform binding analysis to get inputs and outputs
    info = analyze_bindings(task)

    # TODO - if the toplevel task needs inputs, that's a groundness error

    # now perform the dependency analysis
    dependency = DependencyAnalysis(info)
    task.accept(dependency)
    return info

#--------------------------------------------------
# Dependency Analysis
#--------------------------------------------------

# id generator for Clusters
_global_id = peekable(count(0))
def next_id():
    return next(_global_id)

class Cluster():
    def __init__(self, info: DependencyInfo, task: ir.Task):
        """ Create a cluster starting with only this task. """
        self.id = next_id()
        self.info = info
        # exists and lookups for nullary relations are always required (i.e. everything
        # should depend on them)
        self.required = isinstance(task, ir.Exists) or (isinstance(task, ir.Lookup) and not task.args)
        # this is a binders cluster, which is a candidate to being merged
        self.mergeable = not self.required and isinstance(task, helpers.BINDERS)
        # this is a cluster that will only hold an effect
        self.effectful = isinstance(task, helpers.EFFECTS)
        # this is a cluster that will only hold a composite
        self.composite = isinstance(task, helpers.COMPOSITES)
        # content is either a single task or a set of tasks
        self.content: OrderedSet[ir.Task] = ordered_set(task)
        # combined inputs and outputs for all tasks in the cluster
        self.inputs: OrderedSet[ir.Var] = OrderedSet.from_iterable(info.input_bindings.get(task.id))
        self.outputs: OrderedSet[ir.Var] = OrderedSet.from_iterable(info.output_bindings.get(task.id))
        # eventually we will compute dependencies between clusters
        self.dependencies: OrderedSet[Cluster] = ordered_set()

    def __str__(self) -> str:
        if isinstance(self.content, ir.Task):
            return str(self.content.id)
        else:
            return ', '.join(str(node.id) for node in self.content)

    def __eq__(self, other):
        return isinstance(other, Cluster) and other.id == self.id

    def __hash__(self):
        return hash(self.id)

    def depends_on(self, other: Cluster):
        """ Assert that this cluster depends on the other cluster. """
        if self in other.dependencies:
            # prevent cycles caused by bugs, like the union hoisting pets in the
            # relationship7 test
            print("Warning: there is a cycle in the dependency graph. This is likely a bug.")
            # k = ','.join(str(x.id) for x in self.content)
            # v = ','.join(str(x.id) for x in other.content)
            # print(f"{k} --> {v}")
        else:
            self.dependencies.add(other)

    def shares_variable(self, other: Cluster):
        """ Returns True iff this cluster and the other cluster have at least one var in common. """
        return (
            any(i in other.inputs or i in other.outputs for i in self.inputs) or
            any(o in other.inputs or o in other.outputs for o in self.outputs)
        )

    def try_merge(self, other: Cluster, hoisted_vars: OrderedSet[ir.Var]):
        """
        Verify that this cluster and the other cluster can be merged. If so, merge the
        other cluster into this cluster and return True. Otherwise, return False and the
        clusters are left unmodified.
        """

        # 1. only mergeable
        if not (self.mergeable and other.mergeable):
            return False

        # 2. share some variable
        if not self.shares_variable(other):
            return False

        # 3. all inputs are covered by outputs within the cluster
        if not all(v in self.outputs or v in other.outputs for v in self.inputs):
            return False
        if not all(v in self.outputs or v in other.outputs for v in other.inputs):
            return False

        # 4. if there are hoisted vars in context, we can only merge clusters that bind the
        # same hoisted vars
        if hoisted_vars:
            for v in hoisted_vars:
                # if self binds v and other does not bind v, they can't be merged
                if v in self.outputs or v in self.inputs:
                    if v not in other.outputs or v not in other.inputs:
                        return False
                # the other way around
                if v in other.outputs or v in other.inputs:
                    if v not in self.outputs or v not in self.inputs:
                        return False

        # ok, can merge
        self.merge(other)
        return True

    def try_merge_group(self, others: list[Cluster]):
        """
        Verify that this cluster and the other clusters can all be merged together. If so,
        merge the other clusters into this cluster and return True. Otherwise, return False
        and all clusters are left unmodified.
        """
        assert(len(others) > 0)

        # 1. only mergeable
        if not (self.mergeable and all(o.mergeable for o in others)):
            return False

        # 2. share some variable
        if not self.shares_variable(others[0]):
            return False

        # 3. all inputs are covered by outputs within the newly formed cluster
        if len(others) == 1:
            others_outputs = others[0].outputs
        else:
            others_outputs = ordered_set()
            [others_outputs.update(o.outputs) for o in others]
        if not all(v in self.outputs or v in others_outputs for v in self.inputs):
            return False
        for other in others:
            if not all(v in self.outputs or v in others_outputs for v in other.inputs):
                return False

        # ok, can merge
        self.merge(others)
        return True

    def merge(self, other: Cluster|Iterable[Cluster]):
        """
        Merge the other cluster(s) into this one. This assumes that the merge makes sense.
        In general, we should use try_merge or try_merge_group instead.
        """
        # merge the other cluster's content, inputs and outputs
        if isinstance(other, Cluster):
            self.content.update(other.content)
            self.inputs.update(other.inputs)
            self.outputs.update(other.outputs)
            # update dependencies, ensuring we remove the other from the self
            self.dependencies.update(other.dependencies)
            self.dependencies.remove(other)
        else:
            for o in other:
                self.content.update(o.content)
                self.inputs.update(o.inputs)
                self.outputs.update(o.outputs)
                self.dependencies.update(o.dependencies)
                self.dependencies.remove(o)


class DependencyAnalysis(visitor.Visitor):
    """
    A visitor to perform dependency analysis in logicals and store the result in a
    DependencyInfo object.

    The dependency analysis is performed for Logical nodes in 3 steps:

    1. form clusters of children that are mutually dependent, because they are binders (like
    lookups and aggregates) that have variables in common.

    2. compute dependencies between the clusters based on input and outputs.

    3. attempt to merge clusters that could form larger clusters.

    Consider the following example, where we are computing dependencies for the numbered nodes:

        Logical
    |1|    Edges(edges)
    |2|    i(edges, i)
    |3|    Logical ⇑[v]
              Logical ⇑[j=None]
                j(edges, j)
              count([edges, j], [i], [v])
    |4|    i < 10
    |5|    i < v
    |6|    Logical ⇑[v_2=None]
              max([i], [], [v, v_2])
    |7|    → output[i](v, v_2 as 'v2')

    In step 1., we merge (1,2,4) because they have `edges` and `i` in common, but nothing
    else. In particular, (5) is not merged as it also depends on v.

    In step 2. we compute dependencies:
      (1,2,4)
      (3) -> (1,2,4)
      (5) -> (1,2,4), (3)
      (6) -> (1,2,4), (3), (5)
      (7) -> (1,2,4), (3), (5), (6)

    For this example, step 3. does not change anything.

    This result can be interpreted as, in order to compute task 6, tasks (1,2,4), (3) and (5)
    must hold. This means that a compiler pass that extracts the logical in task 6 into its
    own top-level logical must bring these dependencies together.

    To illustrate the need for step 3, consider this example:

        Logical
    |1|    Edge(edge)
    |2|    i(edge, i)
    |3|    Edge(edge_2)
    |4|    j(edge_2, j)
    |5|    i = j
    |6|    Logical ⇑[res=None]
            .....
    |7|    → output[edge, j, i](i, res)

    The result of step 2 is the following:
    (1,2)
    (3,4)
    (5) -> (1,2), (3,4)
    (6) -> (1,2), (3,4), (5)
    (7) -> (1,2), (3,4), (5), (6)

    Step 3 observes that task (5) is a bridge between (1,2) and (3,4), so that merging those
    3 clusters together yields a consistent cluster. So the result is:

    (1,2,3,4,5)
    (6) -> (1,2,3,4,5)
    (7) -> (1,2,3,4,5), (6)

    """
    def __init__(self, info: DependencyInfo):
        self.info = info


    def enter(self, node: ir.Node, parent: Optional[ir.Node]=None):
        # keep track of parents of all nodes
        if parent and isinstance(parent, ir.Task):
            self.info.parent[node.id] = parent
        return super().enter(node, parent)


    def visit_logical(self, node: ir.Logical, parent: Optional[ir.Node]):
        # quick check to see if it's worth it computing clusters at all
        some_child_has_bindings = False
        for child in node.body:
            if child.id in self.info.input_bindings or child.id in self.info.output_bindings:
                some_child_has_bindings = True
                break

        if some_child_has_bindings:
            # print(ir.node_to_string(node, print_ids=True))
            # compute clusters for the nodes based on inputs/outputs and shared variables
            clusters = self.compute_clusters(node)
            # compute the dependencies between those clusters
            self.compute_dependencies(clusters)
            # attempt to further merge clusters
            self.merge_clusters(clusters)
            # index the clusters by tasks participating in those clusters, and record it
            self.index(clusters)
            # self._print_debug_info(node, clusters)

        return super().visit_logical(node, parent)


    def compute_clusters(self, task: ir.Logical) -> list[Cluster]:
        """
        Cluster the children of the logical, storing together children that are mutually
        dependent.
        """
        # create initial clusters
        clusters:list[Cluster] = [Cluster(self.info, child) for child in task.body]

        # all hoisted vars of children, used to ensure we don't merge clusters that depend
        # on a variable hoisted by a composite
        hoisted_vars = ordered_set()
        for child in task.body:
            if isinstance(child, helpers.COMPOSITES):
                hoisted_vars.update(helpers.hoisted_vars(child.hoisted))

        # iterate clustering until nothing changes
        merging = True
        while merging:
            merging = False
            cs = list(clusters)
            while cs:
                # last c1 merged some c2s, so cs was modified, restart
                if merging:
                    break
                c1 = cs.pop()
                for c2 in cs:
                    if c1 is c2:
                        continue
                    if c1.try_merge(c2, hoisted_vars):
                        clusters.remove(c2)
                        merging = True
        return clusters


    def compute_dependencies(self, clusters: list[Cluster]):
        """
        Traverse the clusters finding dependencies between them, based on input and output
        variables used by tasks within the clusters.
        """
        def has_dependency(c1: Cluster, c2: Cluster):
            # c2 is a required cluster, everything depends no it
            if c2.required:
                return True
            # if c1 has an effect and c2 is mergeable (basically it contains only binders)
            # then c2 behaves like a filter, so c1 must depend on it, even if it does not
            # have variables in common (this may bring other dependencies).
            if c1.effectful and c2.mergeable:
                return True
            # if c1 has an effect and c2 is a composite without hoisted variables or with a
            # hoisted variable that does not have a default (it is a plain var), then c2
            # behaves like a filter and c1 depends on it.
            if c1.effectful and c2.composite:
                task = c2.content.some()
                assert(isinstance(task, helpers.COMPOSITES))
                if not task.hoisted:
                    return True
                for h in task.hoisted:
                    if isinstance(h, ir.Var): # no default
                        return True

            # if c1 is a composite and c2 binds its hoisted vars, c1 can't depend on c2
            # (dependency is the other way around)
            if c1.composite and c1.outputs:
                for v in c1.outputs:
                    if c2.outputs and v in c2.outputs:
                        return False
                    if c2.inputs and v in c2.inputs:
                        return False

            # c1 does not depend on c2 if one of its output vars is an input to c2
            # (dependency is the other way around)
            if (c1.outputs and c2.inputs):
                # optimization for any([v in c2.inputs for v in c1_outputs])):
                for v in c1.outputs:
                    if v in c2.inputs:
                        return False

            # c1 depends on c2 if one of its input vars is an output of c2
            if (c1.inputs and c2.outputs):
                # optimization for any([v in c2.outputs for v in c1_inputs])):
                for v in c1.inputs:
                    if v in c2.outputs:
                        return True

            # c1 is a composite with hoisted variables; it depends on c2 if c2 is a
            # composite that does not have hoisted vars, hence behaving like a filter.
            if c1.composite and c2.composite:
                c1task = c1.content.some()
                assert(isinstance(c1task, helpers.COMPOSITES))
                if c1task.hoisted:
                    c2task = c2.content.some()
                    assert(isinstance(c2task, helpers.COMPOSITES))
                    if not c2task.hoisted:
                        return True
            return False

        cs = list(clusters)
        while cs:
            c1 = cs.pop()
            for c2 in cs:
                if c1 is c2:
                    continue

                if has_dependency(c1, c2):
                    c1.depends_on(c2)
                if has_dependency(c2, c1):
                    c2.depends_on(c1)


    def merge_clusters(self, clusters: list[Cluster]):
        """
        Traverse clusters trying to merge multiple clusters if they together form a larger
        cluster.
        """
        # iterate clustering until nothing changes
        merging = True
        while merging:
            merging = False
            cs = list(clusters)
            while cs:
                if merging:
                    break
                c = cs.pop()
                if c.dependencies and c.mergeable:
                    deps = list(c.dependencies)
                    if c.try_merge_group(deps):
                        # remove the deps from clusters
                        for d in deps:
                            clusters.remove(d)
                        # rewire other clusters to the new node
                        # this is not very efficient but should not happen often
                        for c2 in clusters:
                            if c2 is not c:
                                for d in deps:
                                    if d in c2.dependencies:
                                        c2.dependencies.add(c)
                                        c2.dependencies.remove(d)
                        merging = True


    def index(self, clusters: list[Cluster]):
        """
        Index clusters by task, and record in the info
        """
        for dep_node in clusters:
            for n in dep_node.content:
                self.info.dependency_clusters[n.id] = dep_node


    def _print_debug_info(self, node, clusters: list[Cluster]):
        # print(ir.node_to_string(node, print_ids=True))
        print("dependencies")
        for dep_node in clusters:
            k = ','.join(str(x.id) for x in dep_node.content)
            print(f"({k}) ->")
            for v in dep_node.dependencies:
                v = ','.join(str(x.id) for x in v.content)
                print(f"    ({v})")
        print()
        print("clusters")
        for c in clusters:
            print(f"{c}")
            if c.inputs:
                print(f"    inputs: {','.join(str(v.name) for v in c.inputs)}")
            if c.outputs:
                print(f"    outputs: {','.join(str(v.name) for v in c.outputs)}")
        print()



class BindingAnalysis(visitor.Visitor):
    """
    Visitor to perform binding analysis, i.e. figure out for each task in the tree, which
    variables it binds as input ad output.
    """
    def __init__(self):
        self.info = DependencyInfo()
        # a stack of variables grounded by the last logical being visited
        self._grounded: list[OrderedSet[ir.Var]] = []


    def input(self, key: ir.Task, val: Optional[ir.Var|Iterable[ir.Var]]):
        """ Assert that this task binds this variable(s) as input. """
        self._register(self.info.input_bindings, key, val)


    def output(self, key: ir.Task, val: Optional[ir.Var|Iterable[ir.Var]]):
        """ Assert that this task binds this variable(s) as output. """
        self._register(self.info.output_bindings, key, val)


    def _register(self, map, key: ir.Task, val: Optional[ir.Var|Iterable[ir.Var]]):
        """ Register key.id -> val in this map, assuming the map holds ordered sets of vals. """
        if val is None or (isinstance(val, Iterable) and not val):
            return
        if key.id not in map:
            map[key.id] = ordered_set()
        if isinstance(val, Iterable):
            for v in val:
                map[key.id].add(v)
        else:
            map[key.id].add(val)


    #
    # Composite tasks
    #
    def visit_logical(self, node: ir.Logical, parent: Optional[ir.Node]):
        # compute variables grounded by children of this logical
        grounds = ordered_set()
        grounded_by_ancestors = None
        if self._grounded:
            # grounded variables inherited from ancestors or siblings
            grounded_by_ancestors = self._grounded[-1]
            grounds.update(grounded_by_ancestors)

        potentially_grounded = ordered_set()
        for child in node.body:
            # leaf constructs that ground variables
            if isinstance(child, ir.Lookup):
                    # special case eq because it can be input or output
                    # TODO: this is similar to what's done below in visit_lookup, modularize
                    if builtins.is_eq(child.relation):
                        x, y = child.args[0], child.args[1]
                        # Compute input/output vars of the equality
                        if isinstance(x, ir.Var) and not isinstance(y, ir.Var):
                            # Variable x is potentially grounded by other expressions at
                            # level in the Logical. If it is, then we should mark it as
                            # input (which is done later).
                            potentially_grounded.add((child, x, x))
                        elif not isinstance(x, ir.Var) and isinstance(y, ir.Var):
                            potentially_grounded.add((child, y, y))
                        elif isinstance(x, ir.Var) and isinstance(y, ir.Var):
                            # mark as potentially grounded, if any is grounded in other atoms then we later ground both
                            potentially_grounded.add((child, x, y))
                    else:
                        # grounds only outputs
                        for idx, f in enumerate(child.relation.fields):
                            arg = child.args[idx]
                            if not f.input and isinstance(arg, ir.Var):
                                grounds.add(arg)
            elif isinstance(child, ir.Data):
                # grounds all vars
                grounds.update(child.vars)
            elif isinstance(child, ir.Aggregate):
                # grounds output args
                for idx, f in enumerate(child.aggregation.fields):
                    arg = child.args[idx]
                    if not f.input and isinstance(arg, ir.Var):
                        grounds.add(arg)
            elif isinstance(child, ir.Rank):
                # grounds the info
                grounds.add(child.result)
            elif isinstance(child, ir.Construct):
                # grounds the output var
                grounds.add(child.id_var)

        # add child hoisted vars to grounded so that they can be picked up by the children
        for child in node.body:
            if isinstance(child, helpers.COMPOSITES):
                grounds.update(helpers.hoisted_vars(child.hoisted))

        # equalities where both sides are already grounded mean that both sides are input
        for child, x, y in potentially_grounded:
            if x in grounds and y in grounds:
                self.input(child, x)
                self.input(child, y)

        # deal with potentially grounded vars up to a fixpoint
        changed = True
        while changed:
            changed = False
            for child, x, y in potentially_grounded:
                if x in grounds and y not in grounds:
                    self.input(child, x)
                    self.output(child, y)
                    grounds.add(y)
                    changed = True
                elif y in grounds and x not in grounds:
                    self.input(child, y)
                    self.output(child, x)
                    grounds.add(x)
                    changed = True

        # now visit the children
        self._grounded.append(grounds)
        super().visit_logical(node, parent)
        self._grounded.pop()

        hoisted_vars = helpers.hoisted_vars(node.hoisted)
        if grounded_by_ancestors:
            # inputs to this logical: grounded by ancestor while being used by a child,
            # excluding variables hoisted by the logical
            vars = helpers.collect_vars(node)
            self.input(node, (grounded_by_ancestors & vars) - hoisted_vars)

        # outputs are vars declared as hoisted
        self.output(node, hoisted_vars)


    def visit_union(self, node: ir.Union, parent: Optional[ir.Node]):
        # visit children first
        super().visit_union(node, parent)

        # inputs taken from all children
        for child in node.tasks:
            self.input(node, self.info.task_inputs(child))
        # outputs are vars declared as hoisted
        self.output(node, helpers.hoisted_vars(node.hoisted))


    def visit_match(self, node: ir.Match, parent: Optional[ir.Node]):
        # visit children first
        super().visit_match(node, parent)

        # inputs taken from all children
        for child in node.tasks:
            self.input(node, self.info.task_inputs(child))
        # outputs are vars declared as hoisted
        self.output(node, helpers.hoisted_vars(node.hoisted))


    def visit_require(self, node: ir.Require, parent: Optional[ir.Node]):
        # visit children first
        super().visit_require(node, parent)

        # inputs taken from the domain and all check tasks
        self.input(node, self.info.task_inputs(node.domain))
        for check in node.checks:
            self.input(node, self.info.task_inputs(check.check))


    #
    # Logical tasks
    #
    def visit_not(self, node: ir.Not, parent: Optional[ir.Node]):
        # visit children first
        super().visit_not(node, parent)

        # not gets the inputs from its child
        self.input(node, self.info.task_inputs(node.task))


    def visit_exists(self, node: ir.Exists, parent: Optional[ir.Node]):
        # visit children first
        super().visit_exists(node, parent)

        # exists variables are local, so they are ignored
        self.input(node, self.info.task_inputs(node.task))


    #
    # Leaf tasks
    #
    def visit_data(self, node: ir.Data, parent: Optional[ir.Node]):
        # data outputs all its variables
        for v in helpers.vars(node.vars):
            self.output(node, v)

        return super().visit_data(node, parent)


    def visit_update(self, node: ir.Update, parent: Optional[ir.Node]):
        # register variables being used as arguments to the update, it's always considered an input
        for v in helpers.vars(node.args):
            self.input(node, v)
        return super().visit_update(node, parent)


    def visit_lookup(self, node: ir.Lookup, parent: Optional[ir.Node]):
        def register(node, field, arg):
            if isinstance(arg, ir.Var):
                if field.input:
                    self.input(node, arg)
                else:
                    self.output(node, arg)

        if builtins.is_eq(node.relation):
            # Most cases are covered already at the parent level if the equality is part of
            # a Logical. The remaining cases are when the equality is a child of a
            # non-Logical, or if its variables are not ground elsewhere in the Logical.
            if self.info.task_inputs(node) or self.info.task_outputs(node):
                # already covered
                pass
            else:
                x, y = node.args[0], node.args[1]
                grounds = self._grounded[-1] if self._grounded else ordered_set()
                if isinstance(x, ir.Var):
                    if x in grounds:
                        self.input(node, x)
                    else:
                        self.output(node, x)
                if isinstance(y, ir.Var):
                    if y in grounds:
                        self.input(node, y)
                    else:
                        self.output(node, y)
        else:
            # register variables depending on the input flag of the relation bound to the lookup
            for idx, f in enumerate(node.relation.fields):
                arg = node.args[idx]
                if isinstance(arg, Iterable):
                    # deal with ListType fields that pack arguments in a tuple
                    for element in arg:
                        register(node, f, element)
                else:
                    register(node, f, arg)
        return super().visit_lookup(node, parent)


    def visit_output(self, node: ir.Output, parent: Optional[ir.Node]):
        # register variables being output, they always considered an input to the task
        for v in helpers.output_vars(node.aliases):
            self.input(node, v)
        # also register keys as inputs
        self.input(node, node.keys)
        return super().visit_output(node, parent)


    def visit_construct(self, node: ir.Construct, parent: Optional[ir.Node]):
        # values are inputs, id_var is an output
        for v in helpers.vars(node.values):
            self.input(node, v)
        self.output(node, node.id_var)


    def visit_aggregate(self, node: ir.Aggregate, parent: Optional[ir.Node]):
        # register projection and group as inputs
        for v in node.projection:
            self.input(node, v)
        for v in node.group:
            self.input(node, v)

        # register variables depending on the input flag of the aggregation relation
        for idx, f in enumerate(node.aggregation.fields):
            arg = node.args[idx]
            if isinstance(arg, ir.Var):
                if f.input:
                    self.input(node, arg)
                else:
                    self.output(node, arg)
        return super().visit_aggregate(node, parent)


    def visit_rank(self, node: ir.Rank, parent: Optional[ir.Node]):
        # register projection and group as inputs
        for v in node.projection:
            self.input(node, v)
        for v in node.group:
            self.input(node, v)
        for v in node.args:
            self.input(node, v)

        self.output(node, node.result)
        return super().visit_rank(node, parent)
