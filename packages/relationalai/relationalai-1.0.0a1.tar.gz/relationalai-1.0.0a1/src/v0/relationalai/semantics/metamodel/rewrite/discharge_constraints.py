from __future__ import annotations

from dataclasses import dataclass
from v0.relationalai.semantics.metamodel import ir, compiler as c, visitor as v, builtins
from v0.relationalai.semantics.metamodel.util import rewrite_list


class DischargeConstraints(c.Pass):
    """
    Since we should not generate code for `unique`, `exclusive`, `anyof` builtins all Require Check nodes marked with
    `discharge` annotation when at least one of the builtins is presented in a check.
    All Require/Check ir nodes marked with `discharge` annotation will be removed from the IR model in Flatten pass.
    """

    def rewrite(self, model: ir.Model, options: dict = {}) -> ir.Model:
        return DischargeConstraintsVisitor().walk(model)


@dataclass
class DischargeConstraintsVisitor(v.Rewriter):
    """
    Visitor marks all nodes which should be removed from IR model with `discharge` annotation.
    """

    def handle_require(self, node: ir.Require, parent: ir.Node):
        checks = rewrite_list(ir.Check, lambda n: self.walk(n, node), node.checks)
        # discharge require if all the checks are discharged
        if all(builtins.discharged_annotation in check.annotations for check in checks):
            return node.reconstruct(node.engine, node.domain, checks, node.annotations | [builtins.discharged_annotation])
        return node.reconstruct(node.engine, node.domain, checks, node.annotations)

    def handle_check(self, node: ir.Check, parent: ir.Node):
        check = self.walk(node.check, node)
        assert isinstance(check, ir.Logical)
        discharged_names = [builtins.unique.name, builtins.exclusive.name, builtins.anyof.name]
        for item in check.body:
            if isinstance(item, ir.Lookup) and item.relation.name in discharged_names:
                return node.reconstruct(check, node.error, node.annotations | [builtins.discharged_annotation])
        return node.reconstruct(check, node.error, node.annotations)
