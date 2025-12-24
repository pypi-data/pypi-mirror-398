from v0.relationalai.early_access.dsl.core import warn
from v0.relationalai.early_access.dsl.core.constraints import FalseConstraint
from v0.relationalai.early_access.dsl.core.constraints.predicate.atomic import reduce_relational_atoms
from v0.relationalai.early_access.dsl.core.constraints.scalar import fold_constants
from v0.relationalai.early_access.dsl.core.exprs.scalar import Literal, box_number
from v0.relationalai.early_access.dsl.core.logic import LogicFragment
from v0.relationalai.early_access.dsl.core.logic.helper import occurrences, instantiate_type_constraints_for
from v0.relationalai.early_access.dsl.core.logic.exists import existentially_quantify
from v0.relationalai.early_access.dsl.rulesets import RuleSet

class SchemaFragment(LogicFragment):

    def __init__(self):
        super().__init__()

        self._relations = {}
        self._universals = {}

    # Attempts to add relational declaration d to the declarations part of this
    # SchemaFragment. If d is new to this fragment, returns True. If the variable
    # d declares already exists in this fragment and is type consistent with d,
    # then returns False. If the variable exists and is type inconsistent with d,
    # raises an exception.
    #
    def add_relational_component(self, d):
        vname = d.display()
        if vname not in self._relations:
            self._relations[vname] = d
            return True
        else:
            d1 = d.typeof()
            d2 = self._relations[vname].typeof()
            if not d2.subtype_of(d1):
                if d1.subtype_of(d2):
                    self._relations[vname] = d
                else:
                    raise Exception(
                        f"++ Error: Cannot declare two relational variables named {vname} in the same schema context")

    # Add c to the constraint part of this Schema. Note that we distinguish propositional
    # from predicate constraints based on the nature of c. Propositional constraints are
    # used directly in the bodies of generated rules and queries. Predciate constraints
    # are used to reason about how to generate rules that populate relations.
    #
    def add_predicate_constraint(self, c):
        cv = c.entityid()
        if not c.relational():
            raise Exception(f"Attempt to add {c.pprint()} as a predicate constraint")

        if cv not in self._universals:
            self._universals[cv] = c

    # Let self be an operation schema fragment and pre an undecorated state schema
    # fragment. This operation returns a fragment that is self reduced by constraints
    # that are entailed by what remains if we assume pre.
    #
    def assume_precondition(self, pre):
        tconsts = self._sconstraints
        new_trans = self.duplicate()
        new_trans._sconstraints = tconsts
        return new_trans

    # Returns the schema formed by concealing under an existential quantifier any component
    # variables whose names appear in the list cvars.
    #
    # Note: Clients typically call this method indirectly from the hide method, where they
    #       pass in the components directly using named Schema instance variables.
    #
    def conceal(self, cvars):

        edecls = {c: self._scalars[c] for c in cvars}

        s = SchemaFragment()
        s._relations = self._relations
        s._scalars = {v: self._scalars[v] for v in self._scalars if v not in edecls}
        s._universals = self._universals

        (s._sconstraints,
         s._atoms,
         xc) = existentially_quantify(edecls, self._sconstraints, self._atoms)

        s.add_existential_constraint(xc)
        return s

    # Computes a dictionary of constraints that are declared in rcdict
    # but not in lcdict after first renaming the variables of rcdict so
    # that its constraints will refer to the same exact SchemaComponents
    # as are used in self for any variables that are common.
    #
    # We use this extension when conjoining these two Schemas.
    #
    def constraint_extension(self, lcdict, rcdict):
        ext = {}
        decls = dict(self._scalars, **self._relations)
        for c in rcdict.values():
            cv = c.entityid()
            if cv not in lcdict:
                ext[cv] = c.rename(decls)
        return ext

    # Returns a decorated (dashed) version of this SchemaFragment
    #
    def decorate(self):
        scalars = self._scalars
        relations = self._relations
        scalar_renaming = { v : scalars[v].after for v in scalars }
        rel_renaming = { v : relations[v].after for v in relations }
        return self.rewrite(scalar_renaming, rel_renaming)

    # Given a tuple of relational vars, return a new SchemaFragment that is a duplicate
    # of self with RelationIsEmpty constraints on all v in vars
    #
    def is_empty(self, *vars):
        s = self.rewrite(self._scalars, self._relations)
        for v in vars:
            s.add_predicate_constraint(v.empty())
        return s

    # Returns a prefixed version of this SchemaFragment in which every
    # component is prefixed by pref (a string)
    #
    def prefix(self, pref):
        scalars = self._scalars
        relations = self._relations
        scalar_renaming = { v : scalars[v].prefix(pref) for v in scalars }
        rel_renaming = { v : relations[v].prefix(pref) for v in relations }

        return self.rewrite(scalar_renaming, rel_renaming)

    def rewrite(self, scalar_renaming, rel_renaming):
        newfrag = SchemaFragment()

        for v in self._scalars:
            if v in scalar_renaming:
                newvar = self._scalars[v].rename(scalar_renaming)
                newfrag._scalars[newvar.display()] = newvar
            else:
                newfrag._scalars[v] = self._scalars[v]

        for v in self._relations:
            if v in rel_renaming:
                newvar = self._relations[v].rename(rel_renaming)
                newfrag._relations[newvar.display()] = newvar
            else:
                newfrag._relations[v] = self._relations[v]

        scalarcs = {}
        for c in self._sconstraints.values():
            newc = c.rename(scalar_renaming)
            scalarcs[newc.entityid()] = newc
        newfrag._sconstraints = scalarcs

        relcs = {}
        for c in self._atoms.values():
            newc = c.rename(rel_renaming).rename(scalar_renaming)
            relcs[newc.entityid()] = newc
        newfrag._atoms = relcs

        # [REKS TODO] Verify that we properly rename the relation components
        #             in existentials.
        #
        xcs = {}
        for c in self._existentials.values():
            newc = c.rename(scalar_renaming).rename(rel_renaming)
            xcs[newc.entityid()] = newc
        newfrag._existentials = xcs

        predcs = {}
        for c in self._universals.values():
            newc = c.rename(rel_renaming)
            predcs[newc.entityid()] = newc
        newfrag._universals = predcs

        return newfrag

    # Return the list of decorated positively bound atoms from among the propositional
    # constraints of this Schema. We use these to extract Rel rule(s) from the Schema
    #
    def decorated_atoms(self):
        return {c.entityid(): c
                for c in self._atoms.values()
                if c.decorated()}

    def duplicate(self):
        newFragment = SchemaFragment()

        scalars = self._scalars
        relations = self._relations
        newFragment._scalars = {v: scalars[v] for v in scalars}
        newFragment._relations = {v: relations[v] for v in relations}
        scalarcs = self._sconstraints
        relcs = self._atoms
        predcs = self._universals
        xcs = self._existentials
        newFragment._sconstraints = {c: scalarcs[c] for c in scalarcs}
        newFragment._atoms = {c: relcs[c] for c in relcs}
        newFragment._existentials = { c: xcs[c].duplicate() for c in xcs }
        newFragment._universals = {c: predcs[c] for c in predcs}

        return newFragment

    # Partially evaluate this Schema by substituting values for
    # its schema variables, simplifying where possible.
    #
    def evaluate(self, bdgs):

        decls = {}
        for v in self._scalars:

            var = self._scalars[v]
            if v in bdgs:
                # Then type check val against var
                var_type = var.typeof()
                val = bdgs[v]

                if not var_type.contains(val.val if isinstance(val, Literal) else val):
                    return None

                if not isinstance(val, Literal):
                    # ... val needs to be boxed before checking other constraints
                    bdgs[v] = box_number(val)
            else:
                decls[v] = self._scalars[v]

        decls = { v: self._scalars[v] for v in self._scalars if v not in bdgs}

        super = LogicFragment.evaluate(self, bdgs)

        if super is None:
            return super
        else:
            s = SchemaFragment()
            s._scalars = decls
            s._sconstraints = super._sconstraints
            s._atoms = super._atoms
            s._relations = self._relations
            s._universals = self._universals
            return s

    # Merge this SchemaFragment with some other SchemaFragment to produce a new one
    # that is the conjunction of the two.
    #
    def merge(self, other):
        s = SchemaFragment()
        s._scalars = merge_decls(self._scalars, other._scalars)
        s._relations = merge_decls(self._relations, other._relations)
        #
        propc = self._sconstraints.copy()
        propc.update(self.constraint_extension(self._sconstraints, other._sconstraints))
        s._sconstraints = propc
        #
        propc = self._atoms.copy()
        propc.update(self.constraint_extension(self._atoms, other._atoms))
        s._atoms = propc
        #
        predc = self._universals.copy()
        predc.update(self.constraint_extension(self._universals, other._universals))
        s._universals = predc
        #
        return s

    # Returns True if this SchemaFragment is an OperationFragment -- meaning
    # that each component is either decorated or undecorated and there exists
    # at least one decorated AtomicConstraint
    #
    def operation(self):
        isop = False
        for c in self._scalars.values():
            if not c.decorated() and not c.undecorated():
                return False

        for c in self._relations.values():
            if not c.decorated() and not c.undecorated():
                return False

        for c in self._atoms.values():
            if c.decorated():
                isop = True
            else:
                if not c.undecorated():
                    return False

        return isop

    # Emit this schema to a textual output using the Z display style
    #
    def pprint(self):
        # Separator used when pretty-printing Schemas in the Z style
        componentSeparator = "+----------"

        declStrings = []
        declStrings.append(componentSeparator)

        for v in self._relations:
            declStrings.append(f"| {self._relations[v].pprint()}")

        for v in self._scalars:
            declStrings.append(f"| {self._scalars[v].pprint()}")

        declStrings.append(componentSeparator)

        propcs = self.propositional_constraints()

        if len(propcs) + len(self._universals) > 0:
            predStrings = [f"| {c.pprint()}      # [ic]" for c in self._universals.values()]
            propStrings = [f"| {c.pprint()}" for c in propcs.values()]

            declStrings.extend(predStrings)
            declStrings.extend(propStrings)
            declStrings.append(componentSeparator)

        return "\n".join(declStrings)

    # A Schema is propositional if none of its variables is of relation type.
    #
    def propositional(self):
        return len(self._relations) == 0

    def reduce(self):
        return self.reduce_relational_atoms()

    # Simplify thus Schema by projecting out decls that are equated with other
    # decls via predicate constraints. These commonly arise when decorating
    # Schemas using the Xi operator. When reducing we try to remove the SchemaComponent
    # with the larger number of dashes to simplify Rel rule generation.
    #
    def reduce_by_xi(self):
        simplifyingICs = [c.xiSubstitution() for c in self._universals.values() if c.xi()]
        if len(simplifyingICs) > 0:
            bindings = {c.left.display(): c.right for c in simplifyingICs}

            s = SchemaFragment()
            s._scalars = self._scalars
            s._relations = self._relations # todo: verify the implementation for projectDecls(self._relations, bindings)
            s._sconstraints = self._sconstraints

            for c in self._atoms.values():
                cp = c.rename(bindings)
                s._atoms[cp.entityid()] = cp

            for c in self._universals.values():
                if not c.xi():
                    cp = c.rename(bindings)
                    s._universals[cp.entityid()] = cp

            return s
        else:
            return self

    # Reduce the AtomicConstraints of this Schema using unification, where
    # possible, and existential reduction.
    #
    # Returns None if FalseConstraints are detected during reduction.
    #
    def reduce_relational_atoms(self):
        (neweqs, reduced_atoms) = reduce_relational_atoms(self._atoms)
        sconsts = neweqs | self._sconstraints
        (newcomps, newatoms) = fold_constants(sconsts, reduced_atoms)
        if len(newcomps) == 1:
            for c in newcomps.values():
                if isinstance(c, FalseConstraint):
                    return None

        s = SchemaFragment()
        s._universals = self._universals
        s._sconstraints = newcomps
        s._atoms = newatoms
        s._scalars = self._scalars
        s._relations = self._relations
        return s

    # Attempt to refine this OperationFragment into a RuleSet that implements it
    #
    def refine(self):
        if not self.operation():
            raise Exception(f"Can only refine OperationFragments, but this isn't one:\n {self.pprint()}\n----")

        datoms = self.decorated_atoms()
        satoms = self._atoms
        body_atoms = {c: satoms[c] for c in satoms if c not in datoms}

        rs = RuleSet(datoms, self._sconstraints, body_atoms)

        grounding_constraints = {} | self._sconstraints | body_atoms

        c = self.ungrounded_components(grounding_constraints)
        if len(c) > 0:
            # Ungrounded variables could signal a spec that is too loose to fully refine
            # into datalog. If the vars in c occur in at least one constraint, then we'll
            # need to warn the user and mark the generated RuleSet as inline
            #
            ungrounded_occurrences = []
            for v in c:
                vname = v.display()
                if occurrences(vname, grounding_constraints) != 0 and occurrences(vname, datoms) != 0:
                    ungrounded_occurrences.append(v)
            if len(ungrounded_occurrences) > 0:
                vstr = ", ".join([v.display() for v in c])
                warn(f"Ungrounded variables ({vstr}) in schema prevent materialization (declaring view @inline)")
                rs.make_inline()

        return rs

    def rename(self, xform):

        scalars = self._scalars
        relations = self._relations
        scalar_renaming = {}
        rel_renaming = {}

        for v in xform:
            if v in scalars:
                scalar_renaming[v] = xform[v]
            else:
                if v in relations:
                    rel_renaming[v] = xform[v]

        return self.rewrite(scalar_renaming, rel_renaming)


# Given a set A of AtomicConstraints, look for any variables used in a
# role that is played by a ValueType that applies constraints and
# return the constraints instantiated by the variable(s)
#
def infer_referent_constraints(A):
    constraints = {}
    # [REKS] Go fill this in to actually use constraints that we can
    #        infer from positive AtomicConstraint references
    #
    for a in A.values():
        role_players = a.relcomp.typeof()._types
        args = a.args
        for i in range(len(role_players)):
            tp = role_players[i]
            expr = args[i]
            if tp.constraint_unary() and expr.variable():
                tcs = instantiate_type_constraints_for(expr, tp)
                constraints.update(tcs)
    return constraints


# Merges the declarations of this Schema and another to produce a SchemaComponent
# dictionary that is suitable for a Scheme formed from the composition of these
# two Schemas.
#
# Returns a SchemaComponent dictionary (decls) that satisfies the following:
#  - decls == self.decls UNION (other.decls NDRES dom(self.decls))
#  - for all v in dom(self.decls) INTERSECT dom(other.decls)
#        self.decls[v].typeof() == other.decls[v].typeof()
# Raises an exception if Schemas declare the same variable with incompatible
# types.
#
def merge_decls(left, right):
    decls = dict(left)

    for v in right:
        svar = right[v]
        if v in decls:
            if decls[v].typeof().entityid() != svar.typeof().entityid():
                raise Exception(f"++ During schema composition, operands declare incompatible types for variable {v}.")
        else:
            decls[v] = svar

    return decls
