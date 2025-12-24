from abc import abstractmethod

from v0.relationalai.early_access.dsl.core.builders import ExprBuilder
from v0.relationalai.early_access.dsl.core.exprs import Expr, contextStack

# Arithmetic expressions are those Numbers, ScalarVariables, and larger
# expressions that combine these with arithmetic operators
#
class ScalarExpr(Expr):

    # ScalarExpr building operators and methods

    def __add__(self, other):
        return contextStack.root_context().build_plus(self, other)

    def __radd__(self, other):
        return contextStack.root_context().build_plus(self, other)

    def __mod__(self, other):
        return contextStack.root_context().build_modulus(self, other)

    def __rmod__(self, other):
        return contextStack.root_context().build_modulus(self, other)

    def __mul__(self, other):
        return contextStack.root_context().build_times(self, other)

    def __rmul__(self, other):
        return contextStack.root_context().build_times(self, other)

    def __neg__(self):
        return contextStack.root_context().build_negate(self)

    def __sub__(self, other):
        return contextStack.root_context().build_minus(self, other)

    def __rsub__(self, other):
        return contextStack.root_context().build_minus(self, other)

    def __truediv__(self, other):
        return contextStack.root_context().build_divide(self, other)

    def __rtruediv__(self, other):
        return contextStack.root_context().build_divide(self, other)

    # Constraint-building operators and methods

    def __ge__(self, other):
        contextStack.root_context().build_comparison(self, ">=", other)

    def __gt__(self, other):
        contextStack.root_context().build_comparison(self, ">", other)

    def __le__(self, other):
        contextStack.root_context().build_comparison(self, "<=", other)

    def __lt__(self, other):
        contextStack.root_context().build_comparison(self, "<", other)

    def __ne__(self, other): # type: ignore
        contextStack.root_context().build_comparison(self, "!=", other)

    def is_in(self, other):
        return contextStack.root_context().build_element_of(self, other)

    def not_in(self, other):
        return contextStack.root_context().build_not_element_of(self, other)

    @abstractmethod
    def map_builder(self, builder):
        raise NotImplementedError(f"Not implemented for \"{type(self)}\".")


class ScalarVariable(ScalarExpr):

    def physical_typeof(self):
        raise Exception(f"Cannot retrieve phsyical type of variable {self.display()}")

    def grounded(self):
        return False

    def grounded_using(self, groundings):
        return self.display() in groundings

    def refersto(self, varname: str) -> bool:
        return self.display() == varname

    def scalar_refs(self):
        return {self.display(): self}

    def rename(self, renaming):
        vname = self.display()
        if vname in renaming:
            return renaming[vname]
        else:
            return self

    def substitute(self, bindings):
        return self.rename(bindings)

    def typeof(self):
        pass

    def variable(self):
        return True

class Literal(ScalarExpr):
    def __init__(self, v): self.val = v

    def display(self): return str(self.val)

    def entityid(self): return hash(self.val)

    def grounded(self): return True

    def grounded_using(self, groundings): return True

    def rename(self, renaming): return self

    def revar(self, vmap): return self

    def refersto(self, varname): return False

    def simplify(self): return self

    def substitute(self, bindings): return self

    def __hash__(self):
        return hash(self.val)

    def map_builder(self, builder):
        return self

class Number(Literal):
    pass

class String(Literal):

    def display(self): return f"\"{self.val}\""


class Negate(ScalarExpr):
    def __init__(self, x):
        self._part = x

    def display(self):
        p = self._part
        return f"- {p.display()}"

    def entityid(self):
        return hash((Negate, self._part.entityid()))

    # Attempts to evaluate this expression statically, returning a single Number if
    # possible, otherwise returns self.
    #
    def evaluate(self):
        if self.grounded():
            exec(f"self.x = {self.display()}")
            return Number(self.x) # type: ignore
        else:
            return self

    def grounded(self):
        return self._part.grounded()

    def grounded_using(self, groundings):
        return self._part.grounded_using(groundings)

    def scalar_refs(self):
        return self._part.scalar_refs()

    def refersto(self, varname):
        return self._part.refersto(varname)

    def rename(self, renaming):
        return Negate(self._part.rename(renaming))

    def revar(self, vmap):
        return Negate(self._part.revar(vmap))

    def simplify(self):
        ev = self.evaluate()
        if ev.entityid() != self.entityid():
            return ev
        else:
            return Negate(self._part.simplify())

    def substitute(self, bindings):
        return Negate(self._part.substitute(bindings))


class BinaryScalarExpr(ScalarExpr):

    def __init__(self, op):
        self._op = op

    def display(self):
        return f"{self._left.display()} {self._op} {self._right.display()}"

    # Attempts to evaluate this expression statically, returning a single Number if
    # possible, otherwise returns self.
    #
    def evaluate(self):
        if self.grounded():
            exec(f"self.x = {self.display()}")
            return Number(self.x) # type: ignore
        else:
            return self

    def grounded(self):
        return self._left.grounded() and self._right.grounded()

    def grounded_using(self, groundings):
        return self._left.grounded_using(groundings) and self._right.grounded_using(groundings)

    def scalar_refs(self):
        dic = self._left.scalar_refs()
        rdict = self._right.scalar_refs()
        for v in rdict:
            if v not in dic:
                dic[v] = rdict[v]
        return dic

    def refersto(self, varname):
        return self._left.refersto(varname) or self._right.refersto(varname)

    def set_args(self, x, z):
        self._left = box_number(x)
        self._right = box_number(z)

    def op(self):
        return self._op


class Plus(BinaryScalarExpr):

    def __init__(self, x, z):
        super().__init__("+")
        self.set_args(x, z)

    def rename(self, renaming):
        return Plus(self._left.rename(renaming),
                    self._right.rename(renaming))

    def revar(self, vmap):
        return Plus(self._left.revar(vmap),
                    self._right.revar(vmap))

    def simplify(self):
        ev = self.evaluate()
        if ev.entityid() != self.entityid():
            return ev
        else:
            return Plus(self._left.simplify(), self._right.simplify())

    def substitute(self, bindings):
        return Plus(self._left.substitute(bindings), self._right.substitute(bindings))

    def entityid(self):
        return hash((Plus,
                     self._left.entityid(),
                     self._right.entityid()))

    def map_builder(self, builder):
        return Plus(self._left.map_builder(builder), self._right.map_builder(builder))


class Minus(BinaryScalarExpr):

    def __init__(self, x, z):
        super().__init__("-")
        self.set_args(x, z)

    def rename(self, renaming):
        return Minus(self._left.rename(renaming),
                     self._right.rename(renaming))

    def revar(self, vmap):
        return Minus(self._left.revar(vmap),
                     self._right.revar(vmap))

    def simplify(self):
        ev = self.evaluate()
        if ev.entityid() != self.entityid():
            return ev
        else:
            return Minus(self._left.simplify(), self._right.simplify())

    def substitute(self, bindings):
        return Minus(self._left.substitute(bindings), self._right.substitute(bindings))

    def entityid(self):
        return hash((Minus,
                     self._left.entityid(),
                     self._right.entityid()))

    def map_builder(self, builder):
        return Minus(self._left.map_builder(builder), self._right.map_builder(builder))


class Modulus(BinaryScalarExpr):
    def __init__(self, x, z):
        super().__init__("%")
        self.set_args(x, z)

    def rename(self, renaming):
        return Modulus(self._left.rename(renaming),
                       self._right.rename(renaming))

    def revar(self, vmap):
        return Modulus(self._left.revar(vmap),
                       self._right.revar(vmap))

    def simplify(self):
        ev = self.evaluate()
        if ev.entityid() != self.entityid():
            return ev
        else:
            return Modulus(self._left.simplify(), self._right.simplify())

    def substitute(self, bindings):
        return Modulus(self._left.substitute(bindings), self._right.substitute(bindings))

    def entityid(self):
        return hash((Modulus,
                     self._left.entityid(),
                     self._right.entityid()))


class Times(BinaryScalarExpr):

    def __init__(self, x, z):
        super().__init__("*")
        self.set_args(x, z)

    def rename(self, renaming):
        return Times(self._left.rename(renaming),
                     self._right.rename(renaming))

    def revar(self, vmap):
        return Times(self._left.revar(vmap),
                     self._right.revar(vmap))

    def simplify(self):
        ev = self.evaluate()
        if ev.entityid() != self.entityid():
            return ev
        else:
            return Times(self._left.simplify(), self._right.simplify())

    def substitute(self, bindings):
        return Times(self._left.substitute(bindings), self._right.substitute(bindings))

    def entityid(self):
        return hash((Times,
                     self._left.entityid(),
                     self._right.entityid()))


class Divide(BinaryScalarExpr):

    def __init__(self, x, z):
        super().__init__("/")
        self.set_args(x, z)

    def entityid(self):
        return hash((Divide,
                     self._left.entityid(),
                     self._right.entityid()))

    def rename(self, renaming):
        return Divide(self._left.rename(renaming),
                      self._right.rename(renaming))

    def revar(self, vmap):
        return Divide(self._left.revar(vmap),
                      self._right.revar(vmap))

    def simplify(self):
        ev = self.evaluate()
        if ev.entityid() != self.entityid():
            return ev
        else:
            return Divide(self._left.simplify(), self._right.simplify())

    def substitute(self, bindings):
        return Divide(self._left.substitute(bindings), self._right.substitute(bindings))


class ScalarExprBuilder(ExprBuilder):

    def build_divide(self, left, right): return Divide(left, box_number(right))

    def build_plus(self, left, right): return Plus(left, box_number(right))

    def build_minus(self, left, right): return Minus(left, box_number(right))

    def build_modulus(self, left, right): return Modulus(left, box_number(right))

    def build_negate(self, expr): return Negate(expr)

    def build_times(self, left, right): return Times(left, box_number(right))


def box_number(x):
    if isinstance(x, (int, float)):
        return Number(x)
    else:
        if isinstance(x, str):
            return String(x)
        else:
            return x
