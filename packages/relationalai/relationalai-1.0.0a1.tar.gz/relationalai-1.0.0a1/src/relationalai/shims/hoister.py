from __future__ import annotations

from collections import defaultdict
import itertools
from dataclasses import dataclass
from typing import  Iterable, Sequence as seq

from relationalai.semantics.metamodel import metamodel as mm
from relationalai.semantics.metamodel.builtins import builtins as b
from relationalai.semantics.metamodel.rewriter import NO_WALK, Walker
from relationalai.util.structures import OrderedSet
from .helpers import is_output_update, is_main_output, ContainerWalker


@dataclass(frozen=True)
class VarRef:
    node: mm.Container
    input: bool = False

    def is_input(self) -> bool:
        return self.input

    def is_output(self) -> bool:
        return not self.input


class Scope:
    def __init__(self):
        # a variable to all references to it
        self.var_refs: dict[mm.Var, OrderedSet[VarRef]] = {}
        # a container to its parent container
        self.parent: dict[mm.Container, mm.Container] = {}
        # the variable of a main output to the container that hosts it
        self.main_output: dict[mm.Var, mm.Container] = {}
        self.available_vars: dict[mm.Container, OrderedSet[mm.Var]] = defaultdict(OrderedSet[mm.Var])

    def is_ancestor(self, ancestor: mm.Container, descendant: mm.Container) -> bool:
        if ancestor == descendant:
            return True
        n = descendant
        while n in self.parent:
            if n == ancestor:
                return True
            n = self.parent[n]
        return n == ancestor

    def least_common_ancestor(self, c1: mm.Container, c2: mm.Container) -> mm.Container | None:
        ancestors1 = set()
        n = c1
        while n in self.parent:
            ancestors1.add(n)
            n = self.parent[n]
        ancestors1.add(n)
        n = c2
        while n not in ancestors1:
            n = self.parent[n]
        return n


class Hoister(ContainerWalker):
    def __init__(self):
        super().__init__()
        # the result of the whole analysis
        self.hoists: dict[mm.Container, OrderedSet[mm.Var]] = defaultdict(OrderedSet[mm.Var])
        self.container_vars: dict[mm.Container, set[mm.Var]] = defaultdict(set)
        self.allowed_vars: dict[mm.Container, set[mm.Var]] = {}
        # the current scope
        self.scope: Scope = Scope()
        # stack of containers being traversed
        self.stack: list[mm.Container] = []

    #------------------------------------------------------
    # Stack
    #------------------------------------------------------

    def top(self) -> mm.Container | None:
        if self.stack:
            return self.stack[-1]
        return None

    def grand_parent(self) -> mm.Container | None:
        if len(self.stack) > 1:
            return self.stack[-2]
        return None

    #------------------------------------------------------
    # Public API
    #------------------------------------------------------

    def analyze(self, model: mm.Model):
        self.clear()
        self(model.root)
        self.scope = Scope()

    def analyze_task(self, task: mm.Task):
        self.clear()
        self(task)
        self.scope = Scope()

    def clear(self):
        self.hoists.clear()
        self.scope = Scope()

    def hoisted(self, container: mm.Container) -> OrderedSet[mm.Var]:
        return self.hoists[container]

    #------------------------------------------------------
    # Walking
    #------------------------------------------------------

    def enter_container(self, container: mm.Container, children: seq[mm.Node]):
        # potentially reset scope (can we nest scopes?)
        if container.scope:
            self.scope = Scope()
        # compute parent relationship
        parent = self.top()
        if parent:
            self.scope.parent[container] = parent
        # push container onto stack
        self.stack.append(container)

    def exit_container(self, container: mm.Container, children: seq[mm.Node]):
        if isinstance(container, (mm.Match, mm.Union)):
            var_sets = [set(self.scope.available_vars[child]) for child in container.tasks if isinstance(child, mm.Container)]
            # allowed vars are those that appear in all branches
            allowed = set.intersection(*var_sets) if var_sets else set()
            parent_hoists = self.hoists[container]
            for child in container.tasks:
                if isinstance(child, mm.Container):
                    self.hoists[child] = parent_hoists
                    self.allowed_vars[child] = allowed
            self.allowed_vars[container] = allowed

        if container.scope:
            # when leaving the scope, compute hoisted vars
            for var, var_refs in self.scope.var_refs.items():
                # find all places where this var is used as input but there's no output for
                # the var in an ancestor container; this means we need to hoist the var from
                # some output
                requires_hoist: OrderedSet[VarRef] = OrderedSet()
                for ref in var_refs:
                    if ref.is_input() and not any(self.scope.is_ancestor(other.node, ref.node) for other in var_refs if other != ref and other.is_output()):
                        requires_hoist.add(ref)

                # for references that require a hoist, find some other output and hoist
                # that up until the least common ancestor of the two references
                for ref in requires_hoist:
                    for other in var_refs:
                        if other != ref and other.is_output():
                            # find least common ancestor of the two references
                            lca = self.scope.least_common_ancestor(ref.node, other.node)
                            assert(lca is not None)
                            if var not in self.container_vars[lca]:
                                self._hoist_until(var, other.node, lca)

        # pop container from stack
        self.stack.pop()

    def _hoist_until(self, var: mm.Var, from_container: mm.Container, to_container: mm.Container):
        """ Hoist the variable from `from_container` up to (but not including) `to_container`. """
        n = from_container
        hoisted = True
        while n != to_container:
            if isinstance(n, mm.Not):
                hoisted = False
                break
            if self.allowed_vars.get(n) is not None:
                allowed = self.allowed_vars[n]
                if var not in allowed:
                    hoisted = False
                    break
            self.hoists[n].add(var)
            n = self.scope.parent[n]
        if hoisted:
            self.container_vars[to_container].add(var)

    #------------------------------------------------------
    # Tasks that manipulate variables
    #------------------------------------------------------

    def _register_use(self, var: mm.Value, input: bool, container: mm.Container | None =None):
        if isinstance(var, mm.Var):
            parent = self.top() if container is None else container
            assert(parent is not None)

            if var not in self.scope.var_refs:
                self.scope.var_refs[var] = OrderedSet()
            self.scope.var_refs[var].add(VarRef(parent, input))
            self.scope.available_vars[parent].add(var)

    def lookup(self, l: mm.Lookup):
        for arg, field in zip(l.args, l.relation.fields):
            if not field.input or l.relation == b.core["="]:
                self._register_use(arg, input=False)
            else:
                self._register_use(arg, input=True)

    def update(self, u: mm.Update):
        if is_main_output(u):
            # just register the container for the main output, using the output variable as key
            self.scope.main_output[u.args[0]] = self.top() # type: ignore
        else:
            main_output_container = self.scope.main_output[u.args[0]] if is_output_update(u) else None # type: ignore
            for arg in u.args:
                self._register_use(arg, input=True)
                # if this is an output update, register that the container hosting the main
                # output needs this variable as input
                if main_output_container is not None:
                    self._register_use(arg, input=True, container=main_output_container)

    def aggregate(self, a: mm.Aggregate):
        self._register_use(a.projection, input=True)
        for g in a.group:
            self._register_use(g, input=True)
        for arg, field in zip(a.args, a.aggregation.fields):
            self._register_use(arg, input=field.input)

    def construct(self, c: mm.Construct):
        for v in c.values:
            self._register_use(v, input=True)
        self._register_use(c.id_var, input=False)
