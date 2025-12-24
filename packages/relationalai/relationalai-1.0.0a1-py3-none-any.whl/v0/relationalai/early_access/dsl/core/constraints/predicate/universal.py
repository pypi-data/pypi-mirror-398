from abc import abstractmethod

from v0.relationalai.early_access.dsl.core.constraints import Constraint


# A universal predciate constraint is one that can be formalized
# over one or more Relations using variables that are universally
# quantified
#
class UniversalConstraint(Constraint):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def rename(self, bdgs):
        return UniversalConstraint(self.left.rename(bdgs), self.right.rename(bdgs))

    @abstractmethod
    def xi(self) -> bool:
        pass

    # If this constraint is a Xi constraint, returns it in a form that can be
    # applied as substitution of the more heavily decorated variable with the
    # less decorated one
    #
    def xiSubstitution(self):
        if self.xi():
            lexpr = self.left
            rexpr = self.right
            if (lexpr.var.name == rexpr.var.name) and (lexpr.var.dashes < rexpr.var.dashes):
                return RelationalEqualityConstraint(rexpr, lexpr)
            else:
                return self
        else:
            return None


class RelationalEqualityConstraint(UniversalConstraint):

    def __init__(self, left, right):
        super().__init__(left, right)

    def pprint(self):
        return self.left.display() + " == " + self.right.display()

    def rename(self, bdgs):
        return RelationalEqualityConstraint( self.left.rename(bdgs),
                                             self.right.rename(bdgs) )

    def relational(self) -> bool:
        return True

    def entityid(self):
        return hash((RelationalEqualityConstraint,
                     self.left.entityid(),
                     self.right.entityid()))

    # A Xi constraint is one that equates two schema variables of
    # compatible relational type. These are so-called because they
    # typically arise through application of the Xi schema operator.
    #
    def xi(self):

        lexpr = self.left
        if lexpr.variable():
            rexpr = self.right
            if rexpr.variable():
                return lexpr.typeof().entityid() == rexpr.typeof().entityid()
            else:
                return False
        else:
            return False
