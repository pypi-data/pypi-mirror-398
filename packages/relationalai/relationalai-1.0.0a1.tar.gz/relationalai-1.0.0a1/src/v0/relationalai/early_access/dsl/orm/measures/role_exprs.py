from abc import ABC, abstractmethod
from typing import Union, Optional

from v0.relationalai.early_access.dsl.orm.measures.initializer import get_reasoner
from v0.relationalai.early_access.dsl.orm.models import Role
from v0.relationalai.semantics.metamodel.util import OrderedSet, ordered_set

class RoleExpr(ABC):

    def __init__(self):
        self._reasoner = get_reasoner()

    @staticmethod
    def flat_concat(x1, x2):
        def flatten(expr):
            return expr._seq if expr.composer() else [expr]

        parts = flatten(x1) + flatten(x2)
        return ComposeRoleExpr(*parts)

    def ending_roles(self) -> OrderedSet[Role] : return ordered_set()

    @abstractmethod
    def guid(self) -> int: pass

    def composer(self) -> bool: return False
    def nil(self) -> bool: return False
    def kleene_plus(self) -> bool: return False
    def kleene_star(self) -> bool: return False
    def simple(self) -> bool: return False
    def mandatory(self) -> bool: return False

    def plus(self):
        return PlusRoleExpr(self)

    def star(self):
        return StarRoleExpr(self)

    def subsumes(self, other) -> Union[tuple['RoleExpr', Optional['RoleExpr']], tuple[None, None]]:
        return (self, None) if other.nil() else (None, None)

    @abstractmethod
    def pretty_print(self) -> str:
        pass

class NilRoleExpr(RoleExpr):

    def __init__(self):
        super().__init__()

    def guid(self) -> int: return hash("Nil")

    def mandatory(self): return True

    def nil(self): return True

    def pretty_print(self) -> str: return "Nil"

class SimpleRoleExpr(RoleExpr):

    def __init__(self, r: Role):
        super().__init__()
        if not isinstance(r, Role):
            raise Exception(f"Tried to instantiate a SimpleRoleExpr with a non-role: {r} of type {type(r)}")
        self._role = r
        
    def ending_roles(self): return ordered_set(self._role)

    def guid(self) -> int: return hash(self._role._guid())

    def simple(self): return True

    def mandatory(self):
        this = self._role

        if not self._reasoner.is_one_role(this):
            return False

        roles = this.siblings()
        if len(roles) > 1:
            return False

        return self._reasoner.is_mandatory_role(roles[0])

    def pretty_print(self) -> str:
        return f"{self._role}"

    def subsumes(self, other):
        if other.simple():
            return (self, None) if self._role._guid() == other._role._guid() else (None, None)
        return super().subsumes(other)

class UnionRoleExpr(RoleExpr):
    def __init__(self, *roles):
        super().__init__()

        if not roles:
            raise ValueError("At least one role must be provided for the UnionRoleExpr.")

        self._roles = roles

        matcher=None
        for r in roles:
            if r is None:
                raise ValueError("NoneType role provided to UnionRoleExpr.")
            if matcher is None:
                matcher = r
            else:
                if not self._reasoner.are_roles_compatible(r, matcher):
                    raise Exception(f"Two roles {r} and {matcher} with incompatible players used in a union role expression")

        assert matcher is not None, "Matcher should not be None after processing roles."
        self._role_player = matcher.player()

    def common_player(self): return self._role_player

    def guid(self) -> int:
        role_hashes = [hash(r) for r in self._roles]
        return hash(tuple(role_hashes))

    def pretty_print(self) -> str:
        expr = " | ".join([f"{r}" for r in self._roles])
        return f"( {expr} )"

    def roles(self): return self._roles

class ComposeRoleExpr(RoleExpr):

    def __init__(self, *exprs):
        super().__init__()
        self._seq = []
        for exp in exprs:
            if not isinstance(exp, RoleExpr):
                raise Exception(f"Tried to concatenate with non- role expr: {exp} of type {type(exp)}")
            self._seq.append(exp)

    def composer(self) -> bool: return True

    # Finds all ending roles of this ConcatExpr. We have to iterate
    # in reverse until we find the first non Kleene star expr to make
    # sure we account for exprs like:
    #    r1 . r2 . ( r3 )* . (r4 . r5)*
    # which should return { r2, r3, r5 }
    #
    def ending_roles(self):
        roles = ordered_set()
        for expr in reversed(self._seq):
            roles.update(expr.ending_roles())
            if not expr.kleene_star():
                break
        return roles

    def guid(self) -> int:
        role_hashes = [x.guid() for x in self._seq]
        return hash(tuple(role_hashes))

    def mandatory(self):
        for e in self._seq:
            if not e.mandatory():
                return False
        return True

    def pretty_print(self) -> str:
        parts = [ p.pretty_print() for p in self._seq ]
        return " . ".join(parts)

    def subsumes(self, other):

        if other.nil():
            return self, None

        o_seq = other._seq if other.composer() else [other]
        my_seq = self._seq
        o_seq_length = len(o_seq)

        if len(my_seq) < o_seq_length:
            return None, None

        splice_point_stack = []
        for i in range(o_seq_length):
            my_expr = my_seq[i]
            (x, splicer) = my_expr.subsumes(o_seq[i])
            if x is None:
                return None, None
            else:
                if my_expr.kleene_star():
                    splice_point_stack.append(my_expr)
                else:
                    splice_point_stack = [my_expr]

        # Upon exit, splice_point_stack must contain at least one role expr,
        # and because len(o_seq) could be less than len(my_seq) we need to
        # consider any remaining exprs in my_seq when creating the splicer.

        if len(splice_point_stack) == 1:
            join_expr = splice_point_stack[0]
        else:
            oset = ordered_set()
            for x in splice_point_stack:
                for r in x.ending_roles():
                    oset.add(r)
            join_expr = UnionRoleExpr(*oset)


        if len(my_seq) == o_seq_length:
            return join_expr, None
        else:
            if len(my_seq) - o_seq_length == 1:
                return join_expr, my_seq[o_seq_length]
            else:
                # Create a composer that represents what to splice onto
                # any dimension at the join point denoted by join_expr
                expr_seq = []
                for i in range(o_seq_length, len(my_seq), 1):
                    expr_seq.append(my_seq[i])

            return join_expr, ComposeRoleExpr(*expr_seq)

class ClosureRoleExpr(RoleExpr):
    def __init__(self, x):
        super().__init__()
        if not isinstance(x, RoleExpr):
            raise Exception(f"Tried to take the reflexive a closure of something other than a role expression: {x} of type {type(x)}")
        self._component = x

    def ending_roles(self):
        return self._component.ending_roles()

    def mandatory(self):
        return self._component.mandatory()
    
    def role_body(self):
        assert(isinstance(self._component, SimpleRoleExpr))
        return self._component._role

class StarRoleExpr(ClosureRoleExpr):
    def __init__(self, x):
        super().__init__(x)

    def guid(self) -> int: return hash(("*", self._component.guid()))

    def kleene_star(self) -> bool: return True

    def pretty_print(self) -> str:
        return f"( {self._component.pretty_print()} ) *"

    def subsumes(self, other):
        if other.kleene_star():
            (x, _) = self._component.subsumes(other._component)
            return (x, None) if x is not None else (None, None)
        return super().subsumes(other)

class PlusRoleExpr(ClosureRoleExpr):
    def __init__(self, x):
        super().__init__(x)

    def guid(self) -> int: return hash(("+", self._component.guid()))

    def kleene_plus(self) -> bool: return True

    def pretty_print(self) -> str:
        return f"( {self._component.pretty_print()} ) +"

    def subsumes(self, other):
        if other.kleene_plus():
            (x, _) = self._component.subsumes(other._component)
            return (x, None) if x is not None else (None, None)
        return super().subsumes(other)