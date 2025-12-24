from v0.relationalai.early_access.dsl.core.builders.scalar_constraint import ScalarConstraintBuilder
from v0.relationalai.early_access.dsl.core.constraints.predicate.atomic import Atom
from v0.relationalai.early_access.dsl.core.exprs.scalar import box_number


# A LogicBuilder is used to construct LogicFragments
#
class LogicBuilder(ScalarConstraintBuilder):

    def build_atom(self, rel, args):
        nargs = len(args)
        nroles = rel.arity()

        if nargs != nroles:
            raise Exception(
                f"++ Error: Reference of {nroles}-ary relation {rel.qualified_name()} with {nargs} arguments")

        boxedargs = [box_number(a) for a in args]
        return Atom(rel, boxedargs)
