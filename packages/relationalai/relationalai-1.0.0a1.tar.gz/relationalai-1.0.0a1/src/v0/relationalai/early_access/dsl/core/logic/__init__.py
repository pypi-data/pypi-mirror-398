from v0.relationalai.early_access.dsl.core import warn
from v0.relationalai.early_access.dsl.core.builders.logic import LogicBuilder
from v0.relationalai.early_access.dsl.core.cset import ConstraintSet
from v0.relationalai.early_access.dsl.core.exprs.scalar import ScalarVariable, ScalarExprBuilder

class RelVariable(ScalarVariable):

    def __init__(self, nm, tp):
        self._name = nm
        self._type = tp

    def display(self): return self._name

    def entityid(self):
        return hash((self._name, self._type.entityid()))

    def physical_typeof(self):
        return self.typeof().physical_typeof()

    def typeof(self): return self._type

    def __hash__(self):
        return hash((self._name, self._type))

    def map_builder(self, builder):
        return RelVariable(self._name, self._type)

class LogicFragment(ConstraintSet, LogicBuilder, ScalarExprBuilder):

    def __init__(self):
        ConstraintSet.__init__(self)
        self._scalars = {}
        self._existentials = {}

    def add_component(self, d):
        vname = d.display()

        if vname not in self._scalars:
            self._scalars[vname] = d
            return True
        else:
            d1 = d.typeof()
            d2 = self._scalars[vname].typeof()
            if not d2.subtype_of(d1):
                if d1.subtype_of(d2):
                    self._scalars[vname] = d
                else:
                    raise Exception(
                        f"++ Error: Cannot declare two scalar variables named {vname} in the same schema context")

        return False

    def add_existential_constraint(self, c):
        self._existentials[id(c)] = c
        return c

    def build_atom(self, rel, args):
        atom = LogicBuilder.build_atom(self, rel, args)
        self.add_atomic_constraint(atom)
        return atom

    def build_comparison(self, left, op, right):
        c = LogicBuilder.build_comparison(self, left, op, right)
        self.add_scalar_constraint(c)
        return c

    def build_scalar_variable(self, args, kwargs):
        tp = args[0]
        if len(args) < 2 or not isinstance(args[1], str):
            raise Exception("This should not happen")

        decl = RelVariable(args[1], tp)
        self.add_component(decl)
        return decl

    def build_relation_variable(self, args, kwargs):
        tp = args[0]

        # [REKS] Very subtle. This is needed because when tp is a ConstrainedValueType,
        #        this method will be called. Correct during type analysis, but incorrect
        #        during declarations of Rel variables of said type
        #
        if tp.nominal():
            return self.build_scalar_variable(args, kwargs)

        # [REKS] Another subtlety. In Rel, we can name a Relation the same as an EntityType,
        #        and we often do this for relations that maintain the finite population of
        #        entites of that type. But then we can refer to these relations as Atoms in
        #        rules, and they will be interpreted as requests to instantiate the EntityType
        #        with a variable name -- which is not a name but a RelVariable meant to range
        #        over the population of the relation.
        #
        varorname = args[1]
        if isinstance(varorname, RelVariable):
            # [VAMI] TODO: uncomment later
            # warn(f"Corner case to follow up on when building_relation_varornameiable {varorname.display()}")
            return self.build_atom(tp.population(), [varorname])
        else:
            decl = RelVariable(varorname, tp)

            self.add_component(decl)
            return decl


    # Partially evaluate this Schema by substituting values for
    # its schema variables, simplifying where possible.
    #
    def evaluate(self, bdgs):

        # Project away from decls any variables that are declared in pdecls
        #
        def project_decls(decls, pdecls):
            return {v: decls[v] for v in decls if v not in pdecls}

        decls = project_decls(self._scalars, bdgs)

        super = ConstraintSet.evaluate(self, bdgs)

        if super is None:
            return super
        else:
            s = LogicFragment()
            s._scalars = decls
            s._sconstraints = super._sconstraints
            s._atoms = super._atoms
            return s

    def propositional_constraints(self):
        par = ConstraintSet.propositional_constraints(self)
        if len(self._existentials) == 0:
            return par
        else:
            d = self._existentials
            for x in d:
                par[x] = d[x]
        return par

    def rel_formula(self):
        subf = ConstraintSet.rel_formula(self)
        if len(self._existentials) == 0:
            if len(subf) == 0:
                return '    true'
            else:
                return subf
        else:
            xcs = [c.rel_formula() for c in self._existentials.values()]
            xf = "\n".join(xcs)
            if subf == "":
                return xf
            return subf + "\n" + xf

    # Given an optional set of constraints that defaults to all propositional
    # constraints in this LogicFragment, returns a dictionary that represents
    # that subset of this Fragment's scalar variables that is not grounded by
    # those constraints.
    #
    # Grounding is decided the same way it is in datalog, namely if the
    # variable is referenced positively in a finite relation or in an
    # atom of an infinite relation in which every other variable in that
    # atom is grounded.
    #
    def ungrounded_components(self, constraints=None):

        if constraints is None:
            constraints = self.propositional_constraints()
        vars = [d for d in self._scalars.values()]

        groundings = {}
        glen = -1

        while glen < len(groundings):
            glen = len(groundings)

            for c in constraints.values():
                for v in vars:
                    if c.grounds(v, groundings):
                        groundings[v.display()] = v

        return [v for v in vars if v.display() not in groundings]

    def view(self, view_name):
        c = self.ungrounded_components()

        args = ", ".join([v.display() for v in self._scalars.values()])
        body = self.rel_formula()
        rule = f"def {view_name}({args}): " + "\n" + body

        if len(c) > 0:
            vstr = ", ".join([v.display() for v in c])
            warn(f"Ungrounded variables ({vstr}) in schema prevent materialization (declaring view @inline)")
            return "@inline\n" + rule
        else:
            return rule
