from v0.relationalai.early_access.dsl.core.constraints import FalseConstraint, TrueConstraint
from v0.relationalai.early_access.dsl.core.constraints.predicate.atomic import AtomicConstraint
from v0.relationalai.early_access.dsl.core.constraints.scalar import ScalarConstraint, fold_constants


# A ConstraintSet is a stable collection of constraints that can be composed
# into a conjunctive datalog query. These are useful for structuring declarative
# specifications of types, formulae, and more abstract schemas, as well as
# forming the basis for Rel rules.
#
# One interesting problem concerns the construction of stable constraints, as
# we may need to create UnstableConstraintSets before all of the constraints
# stabilize and then generate the ConstraintSet once they do
#

class AbstractConstraintSet:

    def __init__(self):
        self._atoms = {}
        self._sconstraints = {}

    def add_atomic_constraint(self, c): pass

    def add_scalar_constraint(self, c): pass

    # Returns a ConstraintSet that stabilizes the constraints declared in this set by
    # replacing object ids in the dictionaries with (now stable) constraint entityids.
    #
    def stabilize(self):
        cset = ConstraintSet()
        cset._sconstraints = {c.entityid(): c for c in self._sconstraints.values()}
        cset._atoms = {c.entityid(): c for c in self._atoms.values()}
        return cset


class ConstraintSet(AbstractConstraintSet):

    def __init__(self):
        super().__init__()

    def add_scalar_constraint(self, c):
        cv = c.entityid()
        if not isinstance(c, ScalarConstraint):
            raise Exception(f"Attempt to add {c.pprint()} as a scalar constraint")

        if cv not in self._sconstraints:
            self._sconstraints[cv] = c

    def add_atomic_constraint(self, c):
        cv = c.entityid()
        if not isinstance(c, AtomicConstraint):
            raise Exception(f"Attempt to add {c.pprint()} as an atomic constraint")

        if cv not in self._atoms:
            self._atoms[cv] = c

    # Partially evaluate this ConstraintSet by substituting values
    # for its scalar variables, simplifying where possible.
    #
    # Returns None if the result of evaluation is infeasible
    #
    def evaluate(self, bdgs):

        # First we evaluate each constraint with bdgs
        #
        comps = {}
        for c in self._sconstraints.values():
            cprime = c.substitute(bdgs).simplify()
            if isinstance(cprime, FalseConstraint):
                return None
            else:
                if not isinstance(cprime, TrueConstraint):
                    comps[cprime.entityid()] = cprime

        atoms = {}
        for c in self._atoms.values():
            cprime = c.substitute(bdgs).simplify()
            atoms[cprime.entityid()] = cprime

        (comps, atoms) = fold_constants(comps, atoms)

        if 1 in comps and isinstance(comps[1], FalseConstraint):
            return None
        else:
            s = ConstraintSet()
            s._sconstraints = comps
            s._atoms = atoms
            return s

    def propositional_constraints(self):
        return self._sconstraints | self._atoms

    # Textual representation of a Rel formula that represents the body of a rule by
    # conjoining the propsitional constraints of this Schema
    #
    def rel_formula(self):
        props = [f"    {c.rel_formula()}" for c in self._sconstraints.values()]
        for c in self._atoms.values():
            props.append(f"    {c.rel_formula()}")
        return " and\n".join(props)


# In uses like value-type construction, constraints must be added before the
# constraints stabilize -- meaning the constraints exist and refer to variables,
# but the name or other identifying information about the variables has yet to
# be assigned. Because ConstraintSets assume stable constraints, we have to
# implement such use cases using UnstableConstraintSets that can be stabilized
# to produce ConstraintSets.
#
# These unstable sets cannot rely on stable constraint entityids to manage the
# sets and instead use simple object ids.
#
class UnstableConstraintSet(AbstractConstraintSet):

    def __init__(self):
        super().__init__()

    def add_scalar_constraint(self, c):
        cv = id(c)
        if not isinstance(c, ScalarConstraint):
            raise Exception(f"Attempt to add {c.pprint()} as a scalar constraint")

        if cv not in self._sconstraints:
            self._sconstraints[cv] = c

    def add_atomic_constraint(self, c):
        cv = id(c)
        if not isinstance(c, AtomicConstraint):
            raise Exception(f"Attempt to add {c.pprint()} as an atomic constraint")

        if cv not in self._atoms:
            self._atoms[cv] = c
