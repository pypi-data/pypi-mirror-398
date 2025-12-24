from __future__ import annotations

from dataclasses import dataclass
from v0.relationalai.semantics.metamodel import ir, compiler as c, factory as f, visitor


class DoubleNegation(c.Pass):
    """
        Pass to drop double negations.

        Examples:
        not_(not_(Person.age > 18, Person.id == 2)) -> (Person.age > 18, Person.id == 2)
        not_(not_(not_(Person.age > 18, Person.id == 2))) -> not_(Person.age > 18, Person.id == 2)
    """

    def rewrite(self, model: ir.Model, options: dict = {}) -> ir.Model:
        return DropDoubleNegationsVisitor().walk(model)


@dataclass
class DropDoubleNegationsVisitor(visitor.Rewriter):
    """
    Visitor drops double negations when they are followed one by one in IR Model.
    The rewrite occurs only when `ir.Not`'s task is an `ir.Logical` with single `ir.Not` in the body.

    Example:
        Not
            Logical
                Not
                    Logical
                        age(person, age)
                        age > 18

        Logical
            age(person, age)
            age > 18
    """

    def handle_not(self, node: ir.Not, parent: ir.Node):
        if isinstance(node.task, ir.Logical) and len(node.task.body) == 1 and isinstance(node.task.body[0], ir.Not):
            new_task = self.walk(node.task.body[0].task, node.task.body[0])
            # dropping redundant Logical if it has only 1 element in his body
            if isinstance(new_task, ir.Logical) and len(new_task.body) == 1:
                return new_task.body[0]
            else:
                return new_task
        else:
            new_task = self.walk(node.task, node)
            return node if node.task is new_task else f.not_(new_task)
