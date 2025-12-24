from __future__ import annotations

from typing import Optional
from v0.relationalai.semantics.metamodel import builtins
from v0.relationalai.semantics.metamodel.ir import (
    Node, Model, Require, Logical, Relation, Annotation, Update
)
from v0.relationalai.semantics.metamodel.compiler import Pass
from v0.relationalai.semantics.metamodel.visitor import Rewriter, Visitor
from v0.relationalai.semantics.lqp.rewrite.functional_dependencies import (
    is_valid_unique_constraint, normalized_fd
)

# In the future iterations of PyRel metamodel, `Require` nodes will have a single `Check`
# (and no `errors`). Currently, however, the unique constraints may result in multiple
# `Check` nodes and for simplicity we split them in to separate `Require` nodes. This step
# will be removed in the future.
#
# Note that unique constraints always have an empty `domain` so apply the splitting only
# to such `Require` nodes.
class SplitMultiCheckRequires(Pass):
    """
    Pass splits unique Require nodes that have empty domain but multiple checks into multiple
    Require nodes with single check each.
    """

    def rewrite(self, model: Model, options: dict = {}) -> Model:
        return SplitMultiCheckRequiresRewriter().walk(model)


class SplitMultiCheckRequiresRewriter(Rewriter):
    """
    Splits unique Require nodes that have empty domain but multiple checks into multiple
    Require nodes with single check each.
    """
    def handle_require(self, node: Require, parent: Node):

        if isinstance(node.domain, Logical) and not node.domain.body and len(node.checks) > 1:
            require_nodes = []
            for check in node.checks:
                single_check = self.walk(check, node)
                require_nodes.append(
                    node.reconstruct(node.engine, node.domain, (single_check,), node.annotations)
                )
            return require_nodes

        return node


class FunctionAnnotations(Pass):
    """
    Pass marks all appropriate relations with `function` annotation. Collects functional
    dependencies from unique Require nodes and uses this information to identify functional
    relations.
    """

    def rewrite(self, model: Model, options: dict = {}) -> Model:
        collect_fds = CollectFDsVisitor()
        collect_fds.visit_model(model, None)
        annotated_model = FunctionalAnnotationsRewriter(collect_fds.functional_relations).walk(model)
        return annotated_model


class CollectFDsVisitor(Visitor):
    """
    Visitor collects all unique constraints.
    """

    # Currently, only information about k-functional fd is collected.
    def __init__(self):
        super().__init__()
        self.functional_relations:dict[Relation, int] = {}

    def visit_require(self, node: Require, parent: Optional[Node]):
        if is_valid_unique_constraint(node):
            fd = normalized_fd(node)
            assert fd is not None
            if fd.is_structural:
                relation = fd.structural_relation
                k = fd.structural_rank
                current_k = self.functional_relations.get(relation, 0)
                self.functional_relations[relation] = max(current_k, k)


class FunctionalAnnotationsRewriter(Rewriter):
    """
    This visitor marks functional_relations with `@function(:checked [, k])` annotation.
    """

    def __init__(self, functional_relations: dict[Relation, int]):
        super().__init__()
        self.functional_relations = functional_relations

    def get_functional_annotation(self, rel: Relation) -> Optional[Annotation]:
        k = self.functional_relations.get(rel, None)
        if k is None:
            return None
        if k == 1:
            return builtins.function_checked_annotation
        return builtins.function_ranked_checked_annotation(k)

    def handle_relation(self, node: Relation, parent: Node):
        function_annotation = self.get_functional_annotation(node)
        if function_annotation:
            return node.reconstruct(node.name, node.fields, node.requires,
                                    node.annotations | [function_annotation], node.overloads)
        return node.reconstruct(node.name, node.fields, node.requires, node.annotations, node.overloads)

    def handle_update(self, node: Update, parent: Node):
        function_annotation = self.get_functional_annotation(node.relation)
        if function_annotation:
            return node.reconstruct(node.engine, node.relation, node.args, node.effect,
                                    node.annotations | [function_annotation])
        return node.reconstruct(node.engine, node.relation, node.args, node.effect, node.annotations)
