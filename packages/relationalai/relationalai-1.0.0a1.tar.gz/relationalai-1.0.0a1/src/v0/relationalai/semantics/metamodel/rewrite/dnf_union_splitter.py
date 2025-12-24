from __future__ import annotations

from v0.relationalai.semantics.metamodel import ir
from v0.relationalai.semantics.metamodel.compiler import Pass
from v0.relationalai.semantics.metamodel.visitor import Visitor, Rewriter
from v0.relationalai.semantics.metamodel.util import OrderedSet
from v0.relationalai.semantics.metamodel import helpers, factory as f
from typing import Optional, Any

"""
Handle DNF decomposition of unions

E.g., we go from

Logical
    Logical
        Union
            Logical
                Foo(foo::Foo)
                a(foo::Foo, a::Int128)
                a::Int128 < 100::Int128
                Union
                    Logical
                        b(foo::Foo, b::Int128)
                        b::Int128 < 100::Int128
                    Logical
                        c(foo::Foo, c::Int128)
                        c::Int128 > 0::Int128
            Logical
                Foo(foo::Foo)
                id(foo::Foo, id::Int128)
                id::Int128 < 100::Int128
            Logical
                Foo(foo::Foo)
                x(foo::Foo, x::Int128)
                x::Int128 < 100::Int128
                Union
                    Logical
                        y(foo::Foo, y::Int128)
                        y::Int128 < 100::Int128
                    Logical
                        z(foo::Foo, z::Int128)
                        z::Int128 > 0::Int128
        ...
        -> output(...)

to

Logical
    Logical
        Logical
            Foo(foo::Foo)
            a(foo::Foo, a::Int128)
            a::Int128 < 100::Int128
            Logical
                b(foo::Foo, b::Int128)
                b::Int128 < 100::Int128
        ...
        -> output(...)
    Logical
        Logical
            Foo(foo::Foo)
            a(foo::Foo, a::Int128)
            a::Int128 < 100::Int128
            Logical
                c(foo::Foo, c::Int128)
                c::Int128 > 0::Int128
        ...
        -> output(...)
    Logical
        Logical
            Foo(foo::Foo)
            id(foo::Foo, id::Int128)
            id::Int128 < 100::Int128
        ...
        -> output(...)
    Logical
        Logical
            Foo(foo::Foo)
            x(foo::Foo, x::Int128)
            x::Int128 < 100::Int128
            Logical
                y(foo::Foo, y::Int128)
                y::Int128 < 100::Int128
        ...
        -> output(...)
    Logical
        Logical
            Foo(foo::Foo)
            x(foo::Foo, x::Int128)
            x::Int128 < 100::Int128
            Logical
                z(foo::Foo, z::Int128)
                z::Int128 > 0::Int128
        ...
        -> output(...)
"""
class DNFUnionSplitter(Pass):
    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        visitor = DNFExtractor()
        model.accept(visitor)
        return DNFRewriter(visitor).walk(model) if visitor.replaced_by else model

class DNFExtractor(Visitor):
    def __init__(self):
        # The logical that contains the output.
        # The assumption for the IR at this point is that there is only one output.
        self.output_logical: Optional[ir.Logical] = None
        self.active_negations: list[ir.Not] = []
        # Nodes that have to split into multiple similar nodes, depending on the changes
        # of sub-nodes.
        self.should_split: OrderedSet[ir.Node] = OrderedSet()
        # Track that a node has to be replaced by other nodes.
        # If node X should be replaced by nodes Y and Z, then the parent should be replicated
        # one time replacing X with Y and one time replacing X with Z.
        self.replaced_by: dict[ir.Node, list[ir.Task]] = {}

    def enter(self, node: ir.Node, parent: Optional[ir.Node]=None) -> Visitor:
        if isinstance(node, ir.Logical):
            if any(isinstance(x, ir.Output) for x in node.body):
                assert not self.output_logical, "multiple outputs"
                self.output_logical = node

        elif isinstance(node, ir.Not):
            self.active_negations.append(node)

        return self

    def leave(self, node: ir.Node, parent: Optional[ir.Node]=None) -> ir.Node:
        if isinstance(node, ir.Logical) and node in self.should_split:
            # The given logical, will be replaced by multiple logicals, each with a different
            # group of tasks. We need to generate all the possible groups.
            # A list of logical bodies (lists).
            replacement_bodies: list[list[ir.Task]] = [[]]
            for task in node.body:
                if task in self.replaced_by:
                    new_replacement_bodies: list[list[ir.Task]] = []
                    replacement_tasks = self.replaced_by[task]
                    for body in replacement_bodies:
                        for new_task in replacement_tasks:
                            # copy to mutate
                            new_body = list(body)
                            new_body.append(new_task.clone())
                            new_replacement_bodies.append(new_body)
                    replacement_bodies = new_replacement_bodies

                else:
                    for new_body in replacement_bodies:
                        new_body.append(task.clone())

            replacement_tasks: list[ir.Task] = []
            for body in replacement_bodies:
                new_task = f.logical(body, node.hoisted)
                replacement_tasks.append(new_task)
            self.replaced_by[node] = replacement_tasks

            if node != self.output_logical:
                self.should_split.add(parent)
            elif node == self.output_logical:
                assert parent and isinstance(parent, ir.Logical)
                new_parent = f.logical(tuple(replacement_tasks), node.hoisted)
                self.replaced_by[parent] = [new_parent]

        elif isinstance(node, ir.Not) and self.active_negations[-1] == node:
            self.active_negations.pop()

        elif (isinstance(node, ir.Union) and
              self.output_logical and
              len(self.active_negations) % 2 == 0 and
              len(node.tasks) > 1):
            # We split the union when there is a branch with vars "X,Y" and another with "X,Z"
            # If some branches have vars "X, Y, Z" and others have "X, Y" or "Y, Z" we don't split
            should_split = False
            all_vars = helpers.collect_vars(node.tasks[0])
            for t in node.tasks[1:]:
                vars = helpers.collect_vars(t)
                curr_intersection = vars.get_set().intersection(all_vars.get_set())
                should_split |= not (curr_intersection == vars.get_set() or curr_intersection == all_vars.get_set())
                if should_split:
                    replacements:list[ir.Task] = []
                    for t in node.tasks:
                        # If some branch should already be replaced, we flatten all the replacements here.
                        if t in self.replaced_by:
                            replacements.extend(self.replaced_by[t])
                        else:
                            replacements.append(t)
                    self.replaced_by[node] = replacements
                    self.should_split.add(parent)
                    break
                all_vars.update(vars)

        if isinstance(node, ir.Logical) and node == self.output_logical:
            self.output_logical = None

        return node

class DNFRewriter(Rewriter):
    def __init__(self, visitor: DNFExtractor):
        super().__init__()
        self.visitor = visitor
        self.outer_parent_logical: Optional[ir.Logical] = None

    def handle_logical(self, node: ir.Logical, parent: ir.Node, ctx:Optional[Any]=None) -> ir.Logical:
        if node in self.visitor.replaced_by:
            new_tasks = self.visitor.replaced_by[node]
            assert len(new_tasks) == 1
            new_task = new_tasks[0]
            assert isinstance(new_task, ir.Logical)
            return new_task
        return node
