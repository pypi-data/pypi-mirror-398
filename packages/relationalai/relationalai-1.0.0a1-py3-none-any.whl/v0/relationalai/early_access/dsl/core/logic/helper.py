from v0.relationalai.early_access.dsl.core.constraints.scalar import fold_constants, propagate_definitions


# Counts the number of constraints of props in which variable x occurs.
#
def occurrences(x: str, props):
    count = 0
    for c in props.values():
        if c.refersto(x):
            count += 1
    return count


# Given a LogicFragment of the form:
#
#     (bvars: sconsts & atoms)
#
# where:
#
#   - bvars is a set of (Scalar) bound variable declarations,
#   - sconsts is a dictionary of ScalarConstraints, and
#   - atoms is a dictionary of AtomicConstraints
#
# Note that constraints in sconsts and/or atoms could refer to *free variables*,
# i.e., ScalarVariables that are not in bvars. We use type constraints on free
# variables when reasoning to help check domain constraints on bound variables.
#
# This function folds constraints and applies the one-point rule where possible to
# generate a hopefully simpler but equivalent fragment (bvars' : sconsts' & atoms')
# where:
#
#    - |bvars'| <= |bvars|
#    - |sconsts'| <= |sconsts|
#
# Recall the formal definition of the one-point rule:
#
#       exists(x in D : P and (x=t) )
#      =============================== [one-point]
#             t in D and P[t/x]
#
# To apply it, we take advantage of the fact that constant folding will often do
# most of the substitution work (i.e., P[t/x]) for ScalarConstraints of the form:
#
#     x == t
#
# which means we can apply the rule by merely removing such constraints (and in
# some cases also the variable ScalarVariable x) provided that we can stacially
# check that t is in D, where D is the (value-) type of ScalarVariable x. This
# check is called the "domain check" on t. Note that we cannot always statically
# discharge the domain check.
#
def one_point_reduce(bvars, sconsts, atoms):

    if len(sconsts) == 0:
        return bvars, sconsts, atoms

    # Start by folding constants
    #
    (sc_folded, atoms_folded) = fold_constants(sconsts, atoms)

    # Next infer the set of free variables (those referenced in some constraint but
    # that are not in bvars) so that we can commute and then and propagate definitions.
    #
    freevars = free_variable_refs(bvars, sc_folded, atoms_folded)

    # Now that we know the free variables, go instantiate their type constraints so
    # that we can leverage them to do more precise domain checking below.
    #
    free_var_constraints = {}
    for v in freevars.values():
        free_var_constraints = free_var_constraints | instantiate_type_constraints_for(v, v._scalartype)

    sc_commuted = commute_definitions(freevars, sc_folded)

    # Next, propagate definitions
    #
    (sc_propagated, atoms_propagated) = propagate_definitions(sc_commuted, atoms_folded)

    # Post: Any ScalarVariable `x` in bvars that forms the lhs of some definition constraint
    #       (of the form "x == t") can now be considered for elimination via the one-point
    #       rule.
    #
    # We choose to eliminate the constraint (and the variable 'x') if 'x' occurs only in that
    # constraint and if we can prove the domain check on `x` is satisfied
    #

    # Here are the variables from definition constraints that occur only in that definition
    # constraint.
    #
    defns = {c.left.display(): c for c in sc_propagated.values() if c.definition()}
    occurs_once = [x for x in bvars
                   if x in defns and occurrences(x, sc_propagated) == 1 and occurrences(x, atoms_propagated) == 0]

    # Any bound that occurs once and satisfies the domain constraint can be removed.
    #
    vars_to_remove = [x for x in occurs_once]

    # Compute the set of new declarations to place under an existential quantifier.
    # These should include any bvars that we have *not* selected for removal by
    # virtue of applying the one-point rule.
    #
    existential_vars = {v: bvars[v] for v in bvars if v not in vars_to_remove}

    # These constraints trigger an application of the one-point rule and so can
    # be removed.
    #
    triggers = [defns[x] for x in vars_to_remove]

    # These are the constraints that remain after removing those that were
    # selected for removal using the one-point rule
    #
    sconsts_prime = {c.entityid(): c for c in sc_propagated.values() if c not in triggers}

    return existential_vars, sconsts_prime, atoms_propagated


def free_variable_refs(bvars, sconsts, atoms):
    fvars = {}
    for c in sconsts.values():
        refs = c.scalar_refs()
        for r in refs:
            if r not in bvars:
                fvars[r] = refs[r]

    for a in atoms.values():
        refs = a.scalar_refs()
        for r in refs:
            if r not in bvars:
                fvars[r] = refs[r]

    return fvars

# We commute any commutative definitions that involve a free variable
# to try to ensure the bound variable is in the lhs of the constratint
#
def commute_definitions(fvars, constraints):
    commuted_constraints = {}
    for c in constraints:
        const = constraints[c]
        if const.commutative_definition() and const.left.display() in fvars:

            newc = const.commute()
            commuted_constraints[newc.entityid()] = newc
        else:
            commuted_constraints[c] = const

    return commuted_constraints


# Given a ScalarVariable var and a ConstrainedValueType tp,
# returns the set of type constraints on tp where the type
# variable is replaced by var -- essentially "instantiating"
# those constraints on var.
#
def instantiate_type_constraints_for(var, tp):
    constraints = {}
    if tp.constraint_unary():
        tvar = tp.value()
        typecs = tp.denotes()
        for c in typecs.values():
            xc = c.substitute({tvar.display(): var})
            constraints[xc.entityid()] = xc
    return constraints