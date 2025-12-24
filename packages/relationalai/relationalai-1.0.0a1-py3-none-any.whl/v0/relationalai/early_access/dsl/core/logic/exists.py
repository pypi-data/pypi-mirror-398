from v0.relationalai.early_access.dsl.core.constraints import Constraint
from v0.relationalai.early_access.dsl.core.exprs import contextStack
from v0.relationalai.early_access.dsl.core.logic import LogicFragment
from v0.relationalai.early_access.dsl.core.logic.helper import one_point_reduce

class ExistentialConstraint(Constraint, LogicFragment):

    # Each Schema object is a ContextManager
    def __enter__(self):
        contextStack.push(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        contextStack.pop()

    def __init__(self):
        LogicFragment.__init__(self)

    def grounds(self, v, groundings):

        # First, we need to extend grounds to include variables introduce in this constraint
        prop_vars = [d for d in self._scalars.values() if not d.relational()]

        addl = {}
        glen = -1

        props = self.propositional_constraints()

        while glen < len(addl):
            glen = len(addl)

            for c in props.values():
                for pv in prop_vars:
                    if c.grounds(pv, dict(groundings, **addl)):
                        addl[pv.display()] = pv

        gdgs = dict(groundings, **addl)

        for c in props.values():
            if c.grounds(v, gdgs):
                return True

        return False

    def free_variables(self):
        fvars = {}
        bvars = self._scalars
        for c in self.propositional_constraints().values():
            cdict = c.scalar_refs()
            for v in cdict:
                if v not in bvars:
                    fvars[v] = cdict[v]
        return fvars

    # Returns a new ExistentialConstraint that duplicates self after
    # mapping every Relation referred to by an atom through relmap
    #
    def map(self, relmap):
        x = ExistentialConstraint()
        x._scalars = self._scalars
        x._sconstraints = self._sconstraints
        for a in self._atoms.values():
            newatom = a.map(relmap)
            x._atoms[newatom.entityid()] = newatom
        for ex in self._existentials.values():
            newex = ex.map(relmap)
            x._existentials[newex.entityid()] = newex
        return x

    # Returns a new ExistentialConstraint that duplicates self after
    # replacing each atom with the one constructed by the given builder
    # function taking the relational component and arguments of the current atom.
    #
    def map_builder(self, builder):
        x = ExistentialConstraint()
        x._scalars = self._scalars      
        x._sconstraints = {}
        for a in self._sconstraints.values():
            ap = a.map_builder(builder)
            x._sconstraints[ap.entityid()] = ap

        for a in self._atoms.values():
            new_atom = a.map_builder(builder)
            x._atoms[new_atom.entityid()] = new_atom
        for ex in self._existentials.values():
            new_ex = ex.map_builder(builder)
            x._existentials[new_ex.entityid()] = new_ex
        return x

    @staticmethod
    def build_existential() -> 'ExistentialConstraint':
        return ExistentialConstraint()

    @staticmethod
    def assemble_existential(decls, comps, atoms) -> 'ExistentialConstraint':
        x = ExistentialConstraint.build_existential()
        x._scalars = decls
        x._sconstraints = comps
        x._atoms = atoms
        return x

    # Emit this schema to a textual output using the Z display style
    #
    def pprint(self):
        vdecl = "; ".join([v for v in self._scalars])
        head = f"exists(({vdecl}) |"

        props = [f"    {c.pprint()}" for c in self.propositional_constraints().values()]
        body = " true )" if len(props) == 0 else "\n" + "\n".join(props) + " )"

        return head + body

    def scalar_refs(self):
        return self.free_variables()

    def refersto(self, varname: str) -> bool:
        return varname in self.free_variables()

    def rel_formula(self):
        propcs = self.propositional_constraints()

        if len(self._scalars) + len(propcs) == 0:
            return "true"

        props = [f"    {c.rel_formula()}" for c in propcs.values()]

        if len(self._scalars) > 0:
            vdecl = ", ".join([v for v in self._scalars])
            head = f"exists(({vdecl}) |"
            if len(props) == 0:
                return head + " true)"
            else:
                return head + "\n" + " and\n".join(props) + " )"
        else:
            if len(props) == 0:
                return ""
            else:
                return "(" + " and\n".join(props) + " )"

    def rename(self, renaming):

        new_vars = {}
        for d in self._scalars:
            dv = self._scalars[d]
            if d in renaming:
                new_vars[d] = dv.rename(renaming[d])
            else:
                new_vars[d] = dv

        new_comps = {}
        for a in self._sconstraints.values():
            ap = a.rename(renaming)
            new_comps[ap.entityid()] = ap

        new_atoms = {}
        for a in self._atoms.values():
            ap = a.rename(renaming)
            new_atoms[ap.entityid()] = ap

        return self.assemble_existential(new_vars, new_comps, new_atoms)

    def simplify(self):
        comps = {}
        for p in self._sconstraints.values():
            ps = p.simplify()
            comps[ps.entityid()] = ps

        atoms = {}
        for p in self._atoms.values():
            ps = p.simplify()
            atoms[ps.entityid()] = ps

        (decls, c, a) = one_point_reduce(self._scalars, comps, atoms)
        return self.assemble_existential(decls, c, a)

    def substitute(self, bindings):
        decls = {}
        for d in self._scalars.values():
            dp = d.substitute(bindings)
            decls[dp.display()] = dp

        comps = {}
        for p in self._sconstraints.values():
            pp = p.substitute(bindings)
            comps[pp.entityid()] = pp

        atoms = {}
        for p in self._atoms.values():
            pp = p.substitute(bindings)
            atoms[pp.entityid()] = pp

        return self.assemble_existential(decls, comps, atoms)

    def entityid(self):
        return hash((hash(tuple(self._scalars)),
                     hash(tuple(self._sconstraints)),
                     hash(tuple(self._atoms))))

# Given a LogicFragment of the form:
#
#     (bvars: sconsts & atoms)
#
# where:
#
#   - bvars is a set of ScalarVariable declarations,
#   - sconsts is a dictionary of ScalarConstraints, and
#   - atoms is a dictionary of AtomicConstraints
#
# Existentially quantify out all of the variables in bvars, returning either
# a modified pair (sconsts', atoms') or an ExistentialConstraint that introduces
# any remaining variables bvarsPrime under a quantifier.
#
# Note that constraints in sconsts and/or atoms could refer to ScalarVariables
# that are not in bvars. In this case, those variables will occur free in the
# fragment returned.
#
def existentially_quantify(bvars, sconsts, atoms):
    (n, c, a) = one_point_reduce(bvars, sconsts, atoms)

    if len(n) > 0:
        return {}, {}, ExistentialConstraint.assemble_existential(n, c, a)
    else:
        return c, a, None