from v0.relationalai.early_access.dsl.core.constraints import disjoint_union_of
from v0.relationalai.early_access.dsl.core.logic import LogicFragment
from v0.relationalai.early_access.dsl.core.logic.exists import existentially_quantify


class RuleSet(LogicFragment):

    def __init__(self, datoms, sconsts, uatoms):

        def bound_variables(fvars, C):

            bvars = {}
            for c in C:
                cdict = c.scalar_refs()
                for v in cdict:
                    if v not in fvars:
                        bvars[v] = cdict[v]
            return bvars

        self._inline = False
        LogicFragment.__init__(self)

        self._decorated_atoms = datoms
        freevars = {}
        for a in datoms.values():
            cdict = a.scalar_refs()
            for v in cdict:
                freevars[v] = cdict[v]

        propcs = disjoint_union_of(sconsts, uatoms)
        boundvars = bound_variables(freevars, propcs.values())

        (self._sconstraints, self._atoms, econs) = existentially_quantify(boundvars, sconsts, uatoms)

        rels = {}
        for a in uatoms.values():
            r = a.component()
            rels[r.entityid()] = r

        self._scalars = {v: freevars[v] for v in freevars}
        for v in boundvars:
            self._scalars[v] = boundvars[v]

        self._relations = rels
        if econs is not None:
            self.add_existential_constraint(econs)

    def body_formula(self):
        return self.rel_formula()

    def make_inline(self): self._inline = True

    def pprint(self):

        indent = "    "

        datoms = self._decorated_atoms
        head = [a.rule_head() for a in datoms.values()]

        head_atoms = [atom.pprint() for atom in head]
        head = f",\n{indent}".join(head_atoms)

        body = indent + self.body_formula().replace("\n", f"\n{indent}")

        rule = f"def {head}:\n{body}"
        if self._inline:
            return '@inline\n' + rule
        else:
            return rule
