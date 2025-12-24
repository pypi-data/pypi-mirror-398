from typing import List

from v0.relationalai.early_access.dsl.core.builders.logic import LogicBuilder
from v0.relationalai.early_access.dsl.core.constraints.predicate.atomic import ElementOf, NotElementOf
from v0.relationalai.early_access.dsl.core.exprs import Wildcard, Expr
from v0.relationalai.early_access.dsl.core.exprs.scalar import ScalarExpr
from v0.relationalai.early_access.dsl.schemas.components import SchemaComponent
from v0.relationalai.early_access.dsl.schemas.exprs import Domain, Range


class SchemaBuilder(LogicBuilder):

    def build_element_of(self, e, set):
        if not isinstance(e, ScalarExpr):
            raise Exception(f"Currently do not support element-of constraints on non-scalar exprs like {e.display()}")

        if not set.relational():
            raise Exception(
                f"Currently do not support element-of constraints on non-relational arguments like {set.display()}")

        # When this construction checks that an expression is in the domain
        # of some Relation, then rewrite using Wildcard
        #
        if isinstance(set, Domain):
            p = set.part
            if isinstance(p, SchemaComponent):
                rel = p.typeof()
                args: List[Expr] = [e]
                for i in range(2, rel.arity() + 1):
                    args.append(Wildcard())
                return self.build_atom(p, args)

        # Similarly for when checking in the domain of some Relation
        #
        if isinstance(set, Range):
            p = set.part
            if isinstance(p, SchemaComponent):
                rel = p.typeof()
                args: List[Expr] = []
                for i in range(1, rel.arity() - 1):
                    args.append(Wildcard())
                args.append(e)
                return self.build_atom(p, args)

        return ElementOf(e, set)

    def build_not_element_of(self, e, set):
        return NotElementOf(e, set)
