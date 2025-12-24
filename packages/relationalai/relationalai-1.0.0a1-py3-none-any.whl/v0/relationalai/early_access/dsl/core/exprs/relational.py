from v0.relationalai.early_access.dsl.core.exprs import Expr, contextStack
from v0.relationalai.early_access.dsl.core.exprs.scalar import box_number


# Relational non-scalar Exprs

class RelationVariable(Expr):

    # RelationVariables may be "invoked" to declare Atoms
    #
    def __call__(self, *args):
        return contextStack.root_context().build_atom(self, [box_number(a) for a in args])

    def arity(self): pass

    def typeof(self): pass

    def variable(self): return True
