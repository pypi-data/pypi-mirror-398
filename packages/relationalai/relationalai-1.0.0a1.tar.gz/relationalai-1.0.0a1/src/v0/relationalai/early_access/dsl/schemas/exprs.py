from v0.relationalai.early_access.dsl.core.constraints.predicate.atomic import Atom
from v0.relationalai.early_access.dsl.core.exprs import Expr, Wildcard


class Domain(Expr):

    def __init__(self, v):
        self.part = v

    def display(self):
        return f"dom {self.part.display()}"

    def grounded_using(self, groundings): return False

    def decorated(self) -> bool:
        return self.part.decorated()

    def entityid(self):
        return hash((Domain, self.part.entityid()))

    def project(self, comp):
        nargs = self.part.typeof().arity() - 1
        wc = Wildcard()

        seq = [wc] * nargs
        seq.insert(0, comp)

        return Atom(self.part, seq)

    def scalar_refs(self): return self.part.scalar_refs()

    def refersto(self, varname: str) -> bool:
        return self.part.refersto(varname)

    def relational(self) -> bool: return True

    def rename(self, renaming):
        return Domain(self.part.rename(renaming))

    def simplify(self): return self

    def substitute(self, bindings):
        p = self.part.substitute(bindings)
        return Domain(p)

    def undecorated(self) -> bool:
        return self.part.undecorated()


class Range(Expr):
    def __init__(self, v):
        self.part = v

    def display(self):
        return f"ran {self.part.display()}"

    def entityid(self):
        return hash((Range, self.part.entityid()))

    def grounded_using(self, groundings): return False

    def decorated(self) -> bool:
        return self.part.decorated()

    def project(self, comp):
        nargs = self.part.arity()
        seq = [Wildcard()] * nargs - 1
        seq.append(comp)

        return Atom(self.part, seq)

    def scalar_refs(self): return self.part.scalar_refs()

    def refersto(self, varname: str) -> bool:
        return self.part.refersto(varname)

    def relational(self) -> bool: return True

    def rename(self, renaming):
        return Range(self.part.rename(renaming))

    def simplify(self): return self

    def substitute(self, bindings):
        p = self.part.substitute(bindings)
        return Range(p)

    def undecorated(self) -> bool:
        return self.part.undecorated()
