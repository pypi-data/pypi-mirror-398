from abc import ABC, abstractmethod
from typing import Optional

from v0.relationalai.early_access.dsl.orm.measures.initializer import get_reasoner
from v0.relationalai.semantics.metamodel.util import OrderedSet, ordered_set
from v0.relationalai.early_access.dsl.orm.models import Role
from v0.relationalai.semantics import Concept

from v0.relationalai.early_access.dsl.orm.measures.role_exprs import RoleExpr, SimpleRoleExpr


class DimensionExpr(ABC):

    def __init__(self, role_expr):
        self._role_expr = role_expr
        self._cuts = False
        self._reasoner = get_reasoner()

    def cuts(self) -> bool:
        return self._cuts

    def cut(self):
        self._cuts = True
        return self

    # The grouping roles of a DimensionExpr are those played by nodes
    #   that terminate paths that conform to its
    def grouping_roles(self) -> Optional[OrderedSet[Role]]:
        if self.cuts():
            return None

        if self._role_expr.nil():
            return self.measuring_roles()

        roles = self._role_expr.ending_roles()

        if self._role_expr.kleene_star():
            roles.update(self.measuring_roles())

        return roles

    def grouping_role_player(self) -> Optional[Concept]:
        roles = self.grouping_roles()
        if roles is None:
            return None

        concept = None
        for role in roles:
            player = role.player()
            if concept is None:
                concept = player
            else:
                common = self._reasoner.least_supertype(concept, player)
                if common is None:
                    raise Exception(f"Incompatible role players {concept} and {common} in derived measure (Currently we don't analyze sub/supertypes)")
                else:
                    concept = common
        return concept

    @abstractmethod
    def guid(self) -> int: pass

    def measuring_roles(self) -> OrderedSet[Role]:
        return ordered_set()

    def splicer(self) -> bool: return False

class Splicer(DimensionExpr):

    def __init__(self, splice_expr, role_expr):
        super().__init__(role_expr)

        if isinstance(splice_expr, Role):
            self._measuring_role = splice_expr
            self._splice_expr = None
        else:
            self._measuring_role = None
            self._splice_expr = splice_expr

    def guid(self) -> int:
        if self._measuring_role is None:
            assert self._splice_expr is not None
            g1 = self._splice_expr.guid()
        else:
            g1 = self._measuring_role._guid()
        return hash((g1, self._role_expr.guid()))

    def pretty_print(self):
        if self._measuring_role is not None:
            prefix = f"( {self._measuring_role}, {self._role_expr.pretty_print()} )"
        else:
            raise Exception("TBD")

        return f"{prefix} !" if self.cuts() else prefix

    def splicer(self) -> bool: return True

    def splices(self, dim):
        grouping_roles = dim.grouping_roles()
        if len(grouping_roles) == 1:
            grole = grouping_roles[0]
            if self._measuring_role is None or self._measuring_role._guid() != grole._guid():
                return False
        else:
            if self._splice_expr is None:
                return False
            splice_roles = self._splice_expr.roles()

            if len(grouping_roles) != len(splice_roles):
                return False

            # Check that each grouping role is in splice_roles and vice versa.
            for role in grouping_roles:
                role_guid = role._guid()
                for r2 in splice_roles:
                    if role_guid == r2._guid():
                       break
        return True

class Dimension(DimensionExpr):

    def __init__(self, measuring_role, role_expr):
        super().__init__(role_expr)
        if not isinstance(measuring_role, Role):
            raise Exception(f"Tried to instantiate Dimension with non-measuring role {measuring_role}")

        self._measuring_role = measuring_role

    # Try to extend self into a new dimension by either splicing with or
    # subsuming by e. Returns this new dimension if it can be formed,
    # or else None 
    def extend_by(self, e):
        if e.splicer():
            newdim = self.splice(e)
            if newdim is not None:
                return newdim
        else:
            (x, y) = e.subsumes(self)
            if x is not None:
                return e
        return None

    def guid(self) -> int:
        return hash((self._measuring_role._guid(), self._role_expr.guid()))

    def measuring_role(self): return self._measuring_role

    def measuring_roles(self) -> OrderedSet[Role]:
        return ordered_set(self.measuring_role())

    def mandatory(self) -> bool:
        if not self._reasoner.is_mandatory_role(self.measuring_role()):
            return False
        return self._role_expr.mandatory()

    def pretty_print(self):
        prefix = f"( {self._measuring_role}, {self._role_expr.pretty_print()} )"
        return f"{prefix} !" if self.cuts() else prefix

    # Try to splice self with splicer to produce a new Dimension that subsumes
    # self. Returns None if no such subsuming Dimension can be formed
    #
    def splice(self, splicer):
        spliced_dim = None

        if splicer.splices(self):

            if self._role_expr.nil():
                spliced_dim = Dimension(self.measuring_role(), splicer._role_expr)
            else:
                if splicer._role_expr.nil():
                    spliced_dim = Dimension(self.measuring_role(), self._role_expr)
                else:
                    spliced_dim = Dimension(self.measuring_role(),
                                            RoleExpr.flat_concat(self._role_expr, splicer._role_expr))
            if splicer.cuts():
                spliced_dim.cut()
        return spliced_dim

    # This dimension subsumes other in the sense that every path that conforms
    # to `self`` is prefixed by some subpath that conforms to `other``.
    #
    def subsumes(self, other):
        measuring_role = self.measuring_role()
        if measuring_role._guid() != other.measuring_role()._guid():
            return None, None

        (x, y) = self._role_expr.subsumes(other._role_expr)

        if x is None:
            return None, None

        if y is None:
            # Two cases here. Self and other are the same dimension; or
            #   other is a base-measure dimension and self is not.
            if self.guid() == other.guid():
                return x, None
            return SimpleRoleExpr(measuring_role), x

        return x, y