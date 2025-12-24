from v0.relationalai.early_access.dsl.core.constraints import Constraint
from v0.relationalai.early_access.dsl.core.constraints.scalar import ScalarConstraint
from v0.relationalai.early_access.dsl.core.exprs import Expr, Wildcard

# An AtomicConstraint is a Constraint that will ultimately realize as a
# literal in the head or body of a datalog rule. The concrete subclass
# Atom allows users to declare these directly, while other subclasses
# provide a slightly higher-level means for doing so by treating
# relations as sets.
#
class AtomicConstraint(Constraint):

    relcomp = None

    def component(self): return self.relcomp # type: ignore

    def decorated(self) -> bool:
        return self.relcomp.decorated() # type: ignore

    def undecorated(self) -> bool:
        return self.relcomp.undecorated() # type: ignore


# An Atom is a constraint that can be used as a literal in the
# head or body of a datalog rule, i.e.:
#
#   R(x1, x2, ..., xn)
#
# or:
#
#   not R(x1, x2, ..., xn)
#
# where x1, x2, ..., xn are arithmetic expressions.
#
class Atom(AtomicConstraint):

    def __init__(self, r, args):
        self.relcomp = r
        self.args = args
        self.negated = False

    def entityid(self):
        hvals = [a.entityid() for a in self.args]
        hvals.append(self.relcomp.entityid())
        return hash(tuple(hvals))

    def grounds(self, v, groundings):
        for a in self.args:
            if a.entityid() == v.entityid():
                return True
        return False

    # Returns a new Atom that duplicates self after mapping
    # the Relation component through relmap
    #
    def map(self, relmap):
        newrel = relmap[self.relcomp.entityid()]
        newatom = Atom(newrel, self.args)
        newatom.negated = self.negated
        return newatom

    # Returns a new Atom that is constructed by the given
    # builder function
    #
    def map_builder(self, builder):
        new_atom = builder(self.relcomp, self.args)
        new_atom.negated = self.negated
        return new_atom

    def __invert__(self):
        self.negated = not self.negated
        return self

    def relation(self):
        return self.relcomp.typeof() if hasattr(self.relcomp, 'typeof') else self.relcomp

    # Emit this schema to a textual output using the Z display style
    #
    def pprint(self):
        relname = self.relcomp.display()
        head_str = ", ".join([v.display() for v in self.args])
        patom = f"{relname}({head_str})"
        if self.negated:
            return "not " + patom
        else:
            return patom

    def rel_formula(self):
        relname = self.relcomp.display()
        head_str = ", ".join([v.display() for v in self.args])

        if self.relation().arity() == len(self.args):
            patom = f"{relname}({head_str})"
        else:
            patom = f"{relname}[{head_str}]"

        if self.negated:
            return "not " + patom
        else:
            return patom

    def scalar_refs(self):
        dic = {}
        for a in self.args:
            if a.variable():
                dic[a.display()] = a
            else:
                cdic = a.scalar_refs()
                for v in cdic:
                    if v not in dic:
                        dic[v] = cdic[v]
        return dic

    def refersto(self, varname: str) -> bool:
        if self.relcomp.refersto(varname):
            return True
        for a in self.args:
            if a.refersto(varname):
                return True
        return False

    def rename(self, renaming):
        #
        # `self.relcomp` can either be a `RelationalComponent` or another type such as `ExternalRelation`.
        # Note that `RelationalComponent` and `ExternalRelation` do not have a common supertype.
        # Only instances of `RelationalComponent` support renaming, so we need to check for that here.
        # We need to import `RelationalComponent` locally to avoid circular dependencies.
        #
        # TODO: This requires a proper fix, which would possibly introduce a common supertype for the types which can
        #  occur here and separate the relation and variable renamings into distinct maps (as is done elsewhere, e.g.,
        #  in callers of this method).
        #
        from v0.relationalai.early_access.dsl.schemas import RelationalComponent
        new_relcomp = self.relcomp.rename(renaming) if isinstance(self.relcomp, RelationalComponent) else self.relcomp
        renamed = Atom(new_relcomp,
                       [a.rename(renaming) for a in self.args])
        renamed.negated = self.negated
        return renamed

    def simplify(self):
        return self

    def substitute(self, bindings):
        return Atom(self.relcomp.substitute(bindings),
                    [a.substitute(bindings)
                     for a in self.args])

    # [REKS] Need a better name. The purpose of this method is to undash an atom
    #        that involves relation R when we are generating a recursive Rel rule
    #        from an operation Schema involving relational components that are
    #        dashed and undashed occurrences of R. The "undashed" atom will be
    #        used to form the head of this rule.
    #
    def rule_head(self):
        return Atom(self.relcomp.undash(), self.args)

    def value_column(self):
        rel = self.relation()
        pos = rel.arity() - 1  # Position of value component
        return self.args[pos]


class ElementOf(AtomicConstraint):

    def __init__(self, x, y):
        self.element = x
        self.relcomp = y

        # Emit this schema to a textual output using the Z display style

    #
    def pprint(self):
        return self.element.display() + " IN " + self.relcomp.display()

    def rel_formula(self):
        elem = self.element
        if elem.relational():
            raise Exception(f"Cannot make expr {elem.display()} an argument of an AtomicConstraint")

        return self.relcomp.project(elem).rel_formula()

    def grounded(self):
        return self.element.grounded()

    def grounds(self, v, groundings):
        return self.element.entityid() == v.entityid()

    def scalar_refs(self):
        dic = self.relcomp.scalar_refs()
        elem = self.element
        if elem.variable():
            dic[elem.display()] = elem
        else:
            edic = elem.scalar_refs()
            for v in edic:
                if v not in dic:
                    dic[v] = edic[v]
        return dic

    def refersto(self, varname: str) -> bool:
        return self.element.refersto(varname) or self.relcomp.refersto(varname)

    def rename(self, renaming):
        return ElementOf(self.element.rename(renaming),
                         self.relcomp.rename(renaming))

    def simplify(self):
        return ElementOf(self.element, self.relcomp.simplify())

    def substitute(self, bindings):
        e = self.element.substitute(bindings)
        p = self.relcomp.substitute(bindings)
        return ElementOf(e, p)

    def entityid(self):
        return hash((ElementOf,
                     self.element.entityid(),
                     self.relcomp.entityid()))


class NotElementOf(AtomicConstraint):

    def __init__(self, x, y):
        self.element = x
        self.relcomp = y

    # Emit this schema to a textual output using the Z display style
    #
    def pprint(self):
        return self.element.display() + " NOT IN " + self.relcomp.display()

    def rel_formula(self):
        return "not " + self.relcomp.project(self.element).rel_formula()

    def grounded(self):
        return self.element.grounded()

    def grounds(self, v, groundings):
        return False

    def scalar_refs(self):
        dic = self.relcomp.scalar_refs()
        elem = self.element
        if elem.variable():
            dic[elem.display()] = elem
        else:
            edic = elem.scalar_refs()
            for v in edic:
                if v not in dic:
                    dic[v] = edic[v]
        return dic

    def refersto(self, varname: str) -> bool:
        return self.element.refersto(varname) or self.relcomp.refersto(varname)

    def rename(self, renaming):
        return NotElementOf(self.element.rename(renaming),
                            self.relcomp.rename(renaming))

    def simplify(self):
        return ElementOf(self.element, self.relcomp.simplify())

    def substitute(self, bindings):
        e = self.element.substitute(bindings)
        p = self.relcomp.substitute(bindings)
        return NotElementOf(e, p)

    def entityid(self):
        return hash((NotElementOf,
                     self.element.entityid(),
                     self.relcomp.entityid()))


# This module declares operations that range over sets of scalar and
# relational constraints.
#
# By convention, we model constraint sets as dictionaries that map
# a hash of the Constraint to the Constraint itself to aid in
# deduplication.
#


# AtomicConstraint set optimizations follow


# Given a set A of AtomicConstraints:
#
#   - Remove any obviously redundant atoms, and
#   - Unify any pair { c1, c2 } subseteq A, if c1 and c2 refer to the
#     same Relation and that Relation is functional, then if c2 and c2
#     can be shown to refer to the same fact, add new equality
#     constraints to record this knowledge.
#
# Returns the set A less any redundant atoms and extended by any equality
# constraints that can be discovered through unification.
#
# We peform unification by constructing a UnificationTree (Utree), which is
# a recursive dictionary of dictionaries ultimately terminating in lists of
# atoms from A. Each dictionary at depth k implements the decision to extend
# the tuple formed by decisions made at depths > k with a decision (column
# value) at depth k. For instance, were A to contain the following atoms:
#
#    a1 = foo(x, y, 2)
#    a2 = foo(x, y, v)
#    a3 = foo(a, y, c)
#    a4 = foo(a, z, d)
#
# then the Utree would look like this:
#
#    { a: { y: [a3],
#           z: [a4] },
#      x: { y: [a1, a2] } }
#
# where {a, x, y, z} in these keys are the hashes of those expressions
#
def reduce_relational_atoms(A):

    # Given a set of AtomicConstraints A and a Relation hash r, returns those
    # atoms in A that reference the Relation whose hash is r
    #
    def references(A, r):
        return {a.entityid(): a
                for a in A.values()
                if a.relcomp.entityid() == r}

    # Given a set of AtomicConstraints A, return the minimal set of relations
    # such that each Relation in the return set is referenced in at least
    # one atom in A
    #
    def rel_refs_of(A):
        rels = {}
        for a in A.values():
            rel = a.relcomp
            rv = rel.entityid()
            if rv not in rels:
                rels[rv] = rel
        return rels

    # A UnificationTree (Utree) is a decision-tree representation (ordered
    # by column number) of one or more facts that are asserted by a set of
    # AtomicConstraints that all reference the same Relation
    #
    def utree_digest(utree, depth, args, atom):
        cval = args[0]
        v = cval.entityid() if isinstance(cval, Expr) else cval
        if v in utree:
            if depth == 1:
                utree[v].append(atom)
            else:
                utree_digest(utree[v], depth - 1, args[1:], atom)
        else:
            if depth == 1:
                utree[v] = [atom]
            else:
                utree[v] = {}
                utree_digest(utree[v], depth - 1, args[1:], atom)

    # Flatten a Utree by recording all of the atoms at its leaves
    # in the set atoms
    #
    def utree_export(utree, depth, atoms):
        for v in utree.values():
            if depth == 1:
                atoms[a.entityid()] = a
            else:
                utree_export(v, depth - 1, atoms)
        return atoms

    # Mutate utree to remove atoms with Wildcard values when we can show
    # those atoms are redundant
    #
    def utree_remove_wildcards(utree, depth):
        if depth == 1:
            for n in utree.values():
                if len(n) > 1:
                    # If a functional relation has an n-1 tuple prefix that maps
                    # to multiple values, then any atom with a Wildcard value
                    # is redundant and can be removed
                    #
                    for a in n:
                        if isinstance(a.value_column(), Wildcard):
                            n.remove(a)
        else:
            for pref in utree:
                utree_remove_wildcards(utree[pref], depth - 1)

    # Given a Utree, whose paths represent a set of referent_atoms that refer to some
    # functional relation, walk that tree to unify referent_atoms that differ only in
    # the last column so as to produce two sets:
    #
    #  - unique_atoms, which is a minimal set of referent atoms such that no two
    #    atoms will reference the same key tuple; and
    #
    #  - unifying_constraints, which is a set of equality constraints that equate
    #    any expressions that that arise from unifying two or more paths in the tree
    #    that reference the same key tuple.
    #
    # This function should be called with a root Utree, its depth, and two empty
    # dictionaries that represent the sets unique_atoms and unifying_constraints,
    # and the function will recursively walk the tree to fill in these sets.
    #
    # If the set referent_atoms already has the unique key tuple property, then on
    # return:
    #
    #    unique_atoms == referent_atoms and unifying_constraints == {}
    #
    # Otherwise, on return:
    #
    #    unique_atoms \subset referent_atoms and unifying_constraints != {}
    #
    def utree_unify_and_export(utree, depth, unique_atoms, unifying_constraints):
        for v in utree.values():
            if depth == 1:
                prev_value = None
                for idx, a in enumerate(v):
                    last_col = a.value_column()
                    if idx == 0:
                        prev_value = last_col
                        unique_atoms[a.entityid()] = a
                    else:
                        eq = ScalarConstraint(prev_value, "=", last_col)
                        unifying_constraints[eq.entityid()] = eq
            else:
                utree_unify_and_export(v, depth - 1, unique_atoms, unifying_constraints)

    equality_constraints = {}
    atoms = {}
    relations = rel_refs_of(A)
    for r in relations:

        # Depth to which we need to build interior nodes (lists) in the
        # unification tree
        #
        rel = relations[r].typeof()
        depth = rel.arity() - 1

        referents = references(A, r)

        if depth == 0:
            for a in referents:
                atoms[a] = referents[a]
        else:
            # Assemble a Utree for the atoms that reference Relation r
            #
            r_utree = {}
            for a in referents.values():
                utree_digest(r_utree, depth, a.args, a)

            utree_remove_wildcards(r_utree, depth)
            if rel.functional:
                utree_unify_and_export(r_utree, depth, atoms, equality_constraints)
            else:
                utree_export(r_utree, depth, atoms)

    return (equality_constraints, atoms)
