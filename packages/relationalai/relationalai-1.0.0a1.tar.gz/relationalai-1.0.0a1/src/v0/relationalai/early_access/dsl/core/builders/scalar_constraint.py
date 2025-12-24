from v0.relationalai.early_access.dsl.core.constraints.scalar import Constraint, ScalarConstraint
from v0.relationalai.early_access.dsl.core.exprs.scalar import box_number


# A ScalarConstraintBuilder is used to build ScalarConstraints
# (comparisons between ScalarExpressions)
#
class ScalarConstraintBuilder:

    def build_comparison(self, left, op, right) -> Constraint:
        return ScalarConstraint(left, op, box_number(right))
