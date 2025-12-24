from v0.relationalai.early_access.dsl.core.types.constrained import ConstrainedValueType
from v0.relationalai.early_access.dsl.core.types.variables import NominalTypeVariable


class ValueSubtype(ConstrainedValueType):

    def __init__(self, nm, *args):
        super().__init__(nm)
        for arg in args:
            self.build_scalar_variable([arg], {})
        self.name_type_variables()

    def arity(self):
        return self._parent.arity()

    def build_scalar_variable(self, args, kwargs):
        if len(args) == 0:
            raise Exception(f"Unexpected error in ValueSubtype {self.display()}")

        if len(kwargs) != 0:
            raise Exception(
                f"Cannot use keyword arguments when instantiating a type parameter for ValueSubtype {self.display()}")

        ptype = args[0]
        if len(args) == 1:
            self._parent = ptype
            tvar = ptype.ranges_over()
            self._params = [tvar]
            return self.typevar_tuple()
        else:
            self._type_constraints.add_atomic_constraint(self.build_atom(ptype, args[1:]))

    def build_relation_variable(self, args, kwargs):
        if len(args) == 0:
            raise Exception(f"Unexpected error in ValueSubtype {self.display()}")

        if len(args) > 1:
            raise Exception(f"Cannot declare type variable of ValueSubtype {self.display()} by supplying more than a type")

        if len(kwargs) != 0:
            raise Exception(
                f"Cannot use keyword arguments when instantiating a type parameter for ValueSubtype {self.display()}")

        vtype = args[0]
        self._parent = vtype

        tvar = vtype.ranges_over()
        self._params.append(tvar)

        return tvar.typevar_tuple()

    def instantiate(self, *val):
        return self._parent.instantiate(val[0])

    def nominal(self):
        return self._parent.nominal()

    # Return a fresh type variable that ranges over this ValueSubtype
    #
    def ranges_over(self):

        # Self is a ValueSubtype, which is either nominal or not

        if self.nominal():
            # If nominal, then the variable that ranges over self must be a NominalTypeVariable
            tvar = NominalTypeVariable(self)
            tvar._parts = []
            vmap = {}
            selfparts = self._params[0]._parts
            for p in selfparts:
                (pprime, vmap) = p.dupe(vmap)
                tvar._parts.append(pprime)
            tvar._vmap = vmap

            # Because tvar might have multiple part variables, any subtype constraints that constrain
            # self will need to apply not to tvar.

            # Instantiate all scalar constraints from vt using vmap
            for c in self._type_constraints._sconstraints.values():
                cnew = c.revar(vmap)
                tvar._cset._sconstraints[id(cnew)] = cnew

            for c in self._type_constraints._atoms:
                cnew = c.revar(vmap)
                tvar._cset._atoms[id(cnew)] = cnew

            return tvar

        else:
            # If this type is not nominal, then it should have exactly one
            # TypeVariable parameter, which we can dupe and then extend
            # with any additional scalar constraints declared by this type.
            #
            lone_type_var = self._params[0]

            (tvar, vmap) = lone_type_var.dupe()
            vmap[id(lone_type_var)] = tvar
            # tvar._vmap = vmap
            tvar.decl = self
            for c in self._type_constraints._sconstraints.values():
                cnew = c.revar(vmap)
                tvar._cset._sconstraints[id(cnew)] = cnew
            return tvar

    def head_display(self):
        parent = self.parent()
        headvars = []
        for v in self._params:
            vt = v.typeof()
            if vt == parent:
                headvars.append(f"{v.display()}")
            else:
                headvars.append(f"{v.display()} in {vt.display()}")
        head = ", ".join(headvars)
        return f"value type {self.display()} <: {parent.display()}({head})"

    def parent(self):
        return self._parent

    def root_nominal_type(self):
        return self._parent.root_nominal_type()

    def root_unconstrained_type(self):
        return self._parent.root_unconstrained_type()
