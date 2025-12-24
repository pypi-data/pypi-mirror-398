from __future__ import annotations

from v0.relationalai.semantics.metamodel import builtins
from v0.relationalai.semantics.metamodel.ir import Node, Model, Require
from v0.relationalai.semantics.metamodel.compiler import Pass
from v0.relationalai.semantics.metamodel.rewrite.discharge_constraints import (
    DischargeConstraintsVisitor
)
from v0.relationalai.semantics.lqp.rewrite.functional_dependencies import (
    is_valid_unique_constraint, normalized_fd
)

_DISABLE_CONSTRAINT_DECLARATIONS = True

class AnnotateConstraints(Pass):
    """
    Extends `DischargeConstraints` pass by discharging only those Require nodes that cannot
    be declared as constraints in LQP.

    More precisely, the pass annotates Require nodes depending on how they should be
    treated when generating code:
     * `@declare_constraint` if the Require represents a constraint that can be declared in LQP.
     * `@discharge` if the Require represents a constraint that should be dismissed during
       code generation. Namely, when it cannot be declared in LQP and uses one of the
       `unique`, `exclusive`, `anyof` builtins. These nodes are removed from the IR model
       in the Flatten pass.
    """

    def rewrite(self, model: Model, options: dict = {}) -> Model:
        return AnnotateConstraintsRewriter().walk(model)


class AnnotateConstraintsRewriter(DischargeConstraintsVisitor):
    """
    Visitor marks all nodes which should be removed from IR model with `discharge` annotation.
    """

    def _should_be_declarable_constraint(self, node: Require) -> bool:
        if _DISABLE_CONSTRAINT_DECLARATIONS:
            return False
        if not is_valid_unique_constraint(node):
            return False
        # Currently, we only declare non-structural functional dependencies.
        fd = normalized_fd(node)
        assert fd is not None  # already checked by _is_valid_unique_constraint
        return not fd.is_structural

    def handle_require(self, node: Require, parent: Node):
        if self._should_be_declarable_constraint(node):
            return node.reconstruct(
                node.engine,
                node.domain,
                node.checks,
                node.annotations | [builtins.declare_constraint_annotation]
            )

        return super().handle_require(node, parent)
