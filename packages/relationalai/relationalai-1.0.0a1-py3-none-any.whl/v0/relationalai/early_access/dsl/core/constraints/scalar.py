from v0.relationalai.early_access.dsl.core.constraints import Constraint, TrueConstraint, FalseConstraint

class ScalarConstraint(Constraint):

    def __init__(self, x, y, z):
        self.op = y
        if y == "=" and x.grounded():
            self.left = z
            self.right = x
        else:
            self.left = x
            self.right = z

    # A binding is a definition in which the right-hand side of the equality
    # comparison is grounded and so will evaluate to a constant (e.g., "x == 20")
    #
    def binding(self):
        return self.definition() and self.right.grounded()

    def commutative_definition(self):
        return self.definition() and self.right.variable()

    def commute(self):
        if not self.commutative_definition():
            raise Exception(f"Cannot commute non-commutative definition {self.pprint()}")
        return ScalarConstraint( self.right, '=', self.left )

    # A definition is a left var ScalarConstraint of the form that involves an
    # equality operator (e.g., "x == 20", or "x == y + 5" )
    #
    def definition(self):
        return self.left.variable() and self.equality()

    def equality(self):
        return self.op == "="

    def negate(self):
        left = self.left
        right = self.right
        if self.op == "=":
            return ScalarConstraint(left, "!=", right)
        if self.op == "!=":
            return ScalarConstraint(left, "=", right)
        if self.op == "<=":
            return ScalarConstraint(left, ">", right)
        if self.op == "<":
            return ScalarConstraint(left, ">=", right)
        if self.op == ">=":
            return ScalarConstraint(left, "<", right)
        if self.op == ">":
            return ScalarConstraint(left, "<=", right)

        raise Exception(f"Cannot negate constraint {self.pprint()}")

    # Emit this schema to a textual output using the Z display style
    #
    def pprint(self):

        left = self.left
        right = self.right
        result = []

        if hasattr(left, "display"):
            result.append(left.display())
        else:
            result.append(left)

        if self.op == "=":
            result.append("==")
        else:
            result.append(self.op)

        if hasattr(right, "display"):
            result.append(right.display())
        else:
            result.append(right)

        return " ".join(result)

    def rel_formula(self):
        return f"{self.left.display()} {self.op} {self.right.display()}"

    def grounded(self):
        return self.left.grounded() and self.right.grounded()

    def grounds(self, v, groundings):
        if self.equality():
            lv = self.left
            if lv.variable():
                if lv.entityid() == v.entityid():
                    return self.right.grounded_using(groundings)
                else:
                    rv = self.right
                    if rv.variable() and rv.entityid() == v.entityid():
                        return self.left.grounded_using(groundings)
        return False

    def scalar_refs(self):
        dic = self.left.scalar_refs()
        rdict = self.right.scalar_refs()
        for v in rdict:
            if v not in dic:
                dic[v] = rdict[v]
        return dic

    def refersto(self, varname: str) -> bool:
        return self.left.refersto(varname) or self.right.refersto(varname)

    def relational(self) -> bool:
        return self.left.relational() or self.right.relational()

    def rename(self, renaming):
        return ScalarConstraint(self.left.rename(renaming),
                                self.op,
                                self.right.rename(renaming))

    def revar(self, vmap):
        return ScalarConstraint(self.left.revar(vmap),
                                self.op,
                                self.right.revar(vmap))

    # Report out the propositional variables that are used in this constraint as
    # an extension to the bindings dictionary that is provided.
    #
    def report_propositional_variable_usage(self, bindings):
        uses = self.scalar_refs()

        if len(bindings) == 0:
            return uses
        else:
            bdgs = bindings.copy()
            for v in uses:
                if v not in bindings:
                    bdgs[v] = uses[v]

            return bdgs

    def simplify(self):
        if self.grounded():
            exec(f"self.x = {self.pprint()}")
            if self.x: # type: ignore
                return TrueConstraint()
            else:
                return FalseConstraint()
        else:
            left = self.left.simplify()
            right = self.right.simplify()
            if left.grounded() and self.equality():
                return ScalarConstraint(right, self.op, left)
            else:
                return ScalarConstraint(left, self.op, right)

    def substitute(self, bindings):
        x = self.left.substitute(bindings)
        y = self.right.substitute(bindings)
        return ScalarConstraint(x, self.op, y)

    def map_builder(self, builder):
        x = self.left.map_builder(builder)
        y = self.right.map_builder(builder)
        return ScalarConstraint(x, self.op, y)

    def entityid(self):
        return hash((self.op,
                     self.left.entityid(),
                     self.right.entityid()))


# Given a dictionary 'props' of ScalarConstraints, return the dictionary
# containing that subset of props that are binding definitions
#
def binding_definitions_of(props):
    return {c.entityid(): c for c in props.values() if c.binding()}


# Given a set props of ScalarConstraints, partition props into
# (bcons, other) where bcons are binding definitions, and return
# (bdgs, bcons, other) where bdgs is a binding dictionary used to
# apply constraints from bcons.
#
def bindings_from(props):
    bdgs = {}
    bcons = {}
    other = []

    bprops = binding_definitions_of(props)

    # Partition props into a dictionary of substitution bindings (bdgs)
    # that derive from the binding definitions in props and any other
    # (non-binding) constraints in props.
    #
    for chash in props:
        c = props[chash]
        if chash in bprops:
            v = c.left.display()
            if v in bdgs:
                # Then we have (at least 2) constraints of the form:
                #    v == expr1
                #    v == expr2
                # for expressions expr1 and expr2. In this case, we
                # need to add the equality constraint `expr1 == expr2`
                # to other.
                #
                expr1 = bdgs[v]
                expr2 = c.right
                if expr2.variable():
                    # Prefer to put the variable on the LHS when possible
                    #
                    other.append(ScalarConstraint(expr2, "=", expr1))
                else:
                    other.append(ScalarConstraint(expr1, "=", expr2))
            else:
                bdgs[v] = c.right
                bcons[chash] = c
        else:
            other.append(c)

    return bdgs, bcons, other

def commutative_definitions_from(props):
    defns = {}
    cdcons = {}
    other = []

    cdefs = commutative_definitions_of(props)

    # Partition props into a dictionary of commutative definitions (defns)
    # that derive from the binding definitions in props and any other
    # (non-binding) constraints in props.
    #
    for chash in props:
        c = props[chash]
        if chash in cdefs and c.commute().entityid() not in defns:
            # Add {chash: c} to defns if its commuted equivalent not already there!
            defns[c.left.display()] = c.right
            cdcons[chash] = c
        else:
            other.append(c)

    return defns, cdcons, other

def definitions_of(props):
    return {c.entityid(): c for c in props.values() if c.definition()}

def commutative_definitions_of(props):
    return {c.entityid(): c for c in props.values() if c.commutative_definition()}

# Given a set (comps, atoms) of ScalarConstraints and AtomicConstraints respectively,
# find any binding constraints in comps and use them to do constant folding within
# (comps, atoms), returning that set of constraints that is equivalent following
# one or more rounds of constant folding.
#
def fold_constants(comps, atoms):
    (bdgs, newcomps, other) = bindings_from(comps)
    blen = 0

    if len(bdgs) == 0:
        return comps, atoms

    # Otherwise, there is at least one binding to try to apply.

    while blen < len(bdgs):
        # Note that len(bdgs) is non-decreasing with each iteration
        #
        blen = len(bdgs)

        # We have not yet applied all bindings. So try to fold
        # any bound value into other constraints, simplifying
        # where possible.
        #
        for c in other:
            cprime = c.substitute(bdgs).simplify()
            if isinstance(cprime, FalseConstraint):
                # Signal that the whole set of constraints is unsatisfiable
                return {1: cprime}, {}
            if not isinstance(cprime, TrueConstraint):
                newcomps[cprime.entityid()] = cprime

        comps = newcomps
        (bdgs, newcomps, other) = bindings_from(comps)

    newatoms = {}
    for c in atoms:
        cprime = atoms[c].substitute(bdgs).simplify()
        newatoms[cprime.entityid()] = cprime

    return comps, newatoms


# Given a set (comps, atoms) of ScalarConstraints and AtomicConstraints respectively,
# find any commutative-definition constraints in comps and propagatge them within
# (comps, atoms), returning that set of constraints that is equivalent following
# one or more rounds of propagation.
#
def propagate_definitions(comps, atoms):

    (cdefs, newcomps, other) = commutative_definitions_from(comps)

    if len(cdefs) == 0:
        return comps, atoms
    for c in other:
        cprime = c.substitute(cdefs)
        newcomps[cprime.entityid()] = cprime

    newatoms = {}
    for c in atoms:
        cprime = atoms[c].substitute(cdefs)
        newatoms[cprime.entityid()] = cprime

    return newcomps, newatoms
