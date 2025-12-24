from abc import abstractmethod
from typing import Any

from v0.relationalai.early_access.dsl.core.cset import UnstableConstraintSet
from v0.relationalai.early_access.dsl.core.exprs.relational import RelationVariable
from v0.relationalai.early_access.dsl.core.exprs.scalar import ScalarVariable

# We use TypeVariables to formalize the meaning of a ConstrainedValueType.
# Each represents what would be a variable in a ValueType or ValueSubtype
# declaration.
#
class TypeVariable:

    # Each TypeVariable declares some AbstractValueType (vt) which might
    # be a ValueSubtype. In addition, each TypeVariable has a Position
    # that is used to form the name of the variable when needed.
    #
    def __init__(self, vt, vmap={}):
        self.pos = None
        self._cset = UnstableConstraintSet()
        self.decl = vt
        self._vmap = vmap

    # Returns the set of ScalarConstraints that this TypeVariable denotes
    #
    def denotes(self, C={}):
        for sc in self._cset._sconstraints.values():
            C[sc.entityid()] = sc

        for ac in self._cset._atoms.values():
            # [REKS] Check the following logic carefully to make sure we don't accidentally
            #        capture any variable names duirng interpretation of type atoms
            #
            scs = self.decl.interpret_type_atom(ac)
            for s in scs:
                if s not in C:
                    C[s] = scs[s]
        return C

    @abstractmethod
    def dupe(self, vmap) -> tuple['TypeVariable', Any]: pass

    def setpos(self, pos): pass

    @abstractmethod
    def varname(self) -> str: pass

class BasicTypeVariable(ScalarVariable, TypeVariable):

    # An UnconstrainedTypeVarible ranges over some UnconstrainedValueType,
    # which will be the root unconstrained type of vt.
    #
    def __init__(self, vt, vmap={}):
        if vt.nominal():
            raise Exception(f"Cannot create BasicTypeVariable of nominal type {vt._name}")
        super().__init__(vt, vmap)

    def display(self):
        return self.varname()

    def dupe(self, vmap={}):
        d = BasicTypeVariable(self.decl, vmap)
        vmap[id(self)] = d
        cs = self._cset._sconstraints
        for c in cs.values():
            newc = c.revar(vmap)
            d._cset._sconstraints[id(newc)] = newc
        return (d, vmap)

    def entityid(self):
        return hash(self.varname())

    def grounded(self):
        return False

    def grounded_using(self, groundings):
        return False

    def physical_typeof(self):
        return self.decl.root_unconstrained_type()

    def rename(self, renaming):
        nm = self.varname()
        if nm in renaming:
            return renaming[nm]
        else:
            return self

    def revar(self, vmap):
        nm = id(self)
        if nm in vmap:
            return vmap[nm]
        else:
            return self

    def setpos(self, pos):
        self.pos = pos
        self._cset = self._cset.stabilize()
        return pos+1

    def typeof(self):
        return self.decl

    def typevar_tuple(self):
        return self

    def varname(self):
        return f"x{str(self.pos)}"

class NominalTypeVariable(RelationVariable, TypeVariable):

    # If vt is nominal, then the TypeVariable itself is nominal
    # and ranges over some root nominal ValueType.
    #
    def __init__(self, vt, vmap={}):
        super().__init__(vt, vmap)
        self._parts = []

    def all_constraint_display(self):
        parts = [self.constraint_display()]
        for p in self._parts:
            if isinstance(p, NominalTypeVariable):
                parts.append(p.all_constraint_display())
        return "\n".join(parts)

    def constraint_display(self):
        parts = [ p.varname() for p in self._parts ]
        args = ", ".join(parts)
        return f"   {self.varname()}({args})"

    def denotes(self, C={}):
        C = super().denotes(C)
        for p in self._parts:
            C = p.denotes(C)
        return C

    def display(self):
        return self.varname()

    def dupe(self, vmap={}):
        d = NominalTypeVariable(self.decl, vmap)
        vmap[id(self)] = d

        for p in self._parts:
            (pprime, vmap) = p.dupe(vmap)
            d._parts.append(pprime)

        vmap = d._vmap

        cs = self._cset._sconstraints
        for c in cs.values():
            newc = c.revar(vmap)
            d._cset._sconstraints[id(newc)] = newc
        acs = self._cset._atoms
        for ac in acs.values():
            newac = ac.revar(vmap)
            d._cset._atoms[id(newac)] = newac
        return (d, vmap)

    def entityid(self):
        return hash(self.varname())

    def rename(self, renaming):
        nm = self.varname()
        if nm in renaming:
            return renaming[nm]
        else:
            return self

    def revar(self, vmap):
        nm = id(self)
        if nm in vmap:
            return vmap[nm]
        else:
            return self

    def setpos(self, pos):
        self.pos = pos
        pos = pos + 1
        for p in self._parts:
            pos = p.setpos(pos)
        self._cset = self._cset.stabilize()
        return pos

    def typeof(self):
        return self.decl

    def typevar_tuple(self):
        tvars = []

        for tvar in self._parts:
            if isinstance(tvar, NominalTypeVariable):
                tvars.append(tvar.typevar_tuple())
            else:
                tvars.append(tvar)
        if len(tvars) == 1:
            result = tvars[0]
        else:
            result = tuple(tvars)
        return result

    def varname(self):
        return f"y{str(self.pos)}"
