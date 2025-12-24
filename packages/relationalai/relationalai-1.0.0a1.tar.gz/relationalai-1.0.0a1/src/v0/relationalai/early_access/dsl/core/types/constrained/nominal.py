from v0.relationalai.early_access.dsl.core.instances import Instance, ValueTypeInstance
from v0.relationalai.early_access.dsl.core.types import Type
from v0.relationalai.early_access.dsl.core.types.constrained import ConstrainedValueType
from v0.relationalai.early_access.dsl.core.types.variables import NominalTypeVariable


class ValueType(ConstrainedValueType):

    def __init__(self, nm, *args):
        super().__init__(nm)
        self._types = args
        for arg in args:
            self.build_scalar_variable([arg], {})
        self.name_type_variables()

    # Add TypeVariable *tv* as a parameter to this type
    #
    def addparam(self, tv):
        self._params.append(tv)
        return tv

    def arity(self) -> int:
        return len(self._params)

    def build_scalar_variable(self, args, kwargs):
        if len(args) == 0:
            raise Exception(f"Unexpected error in ValueType {self.display()}")

        if len(kwargs) != 0:
            raise Exception(
                f"Cannot use keyword arguments when instantiating a type parameter for ValueSubtype {self.display()}")

        T = args[0]
        if len(args) == 1:

            # Then we are instantiating T to create a new TypeVariable that will parameterize
            # this ValueType (self)
            #
            tv = T.ranges_over()
            self.addparam(tv)
            return tv
        else:
            self._type_constraints.add_atomic_constraint(self.build_atom(T, args[1:]))

    def build_relation_variable(self, args, kwargs):
        if len(args) == 0:
            raise Exception(f"Unexpected error in ValueType {self.display()}")

        if len(kwargs) != 0:
            raise Exception(
                f"Cannot use keyword arguments when instantiating a type parameter for ValueSubtype {self.display()}")

        T = args[0]
        if not isinstance(T, Type):
            raise Exception("When an AtomicConstraint is asserted in context of a ValueType, the predicate must name a Type")

        if len(args) == 1:
            # Then we are instantiating T to create a new TypeVariable that will parameterize
            # this ValueType (self)
            #

            tvar = T.ranges_over() # type: ignore
            self.addparam(tvar)

            return tvar.typevar_tuple()

        else:
            # Otherwise, we expect T to behave as a type predicate that is applied to a tuple
            # (args[1:]) of BasicTypeVariables for the purpose of imposing T's constraints
            # on those variables. We implement this by creating a renaming using tuple args[1:]
            # and then applying that renaming to each constraint that T verifies, adding the
            # result to the constraints declared by self.
            #
            self._type_constraints.add_atomic_constraint(self.build_atom(T, args[1:]))

    # Generates the string used to display the opening declaration for this ValueType
    #
    def head_display(self):
        headvars = []
        for v in self._params:
            vt = v.typeof()
            headvars.append(f"{v.display()} in {vt.display()}")
        head = ", ".join(headvars)
        return f"value type {self.display()}({head})"

    def instantiate(self, *tup):

        cvars = self._params
        if len(tup) != len(cvars):
            raise Exception(
                f"ValueType {self.display()} constructor expects {len(cvars)} arguments but was instantiated with {len(tup)}")

        params = []
        for i in range(len(cvars)):
            arg = tup[i]
            tp = cvars[i].decl
            if isinstance(arg, Instance) or not tp.nominal():
                params.append(arg)
            else:
                params.append(tp.instantiate(arg))
        return ValueTypeInstance(self, params)

    def nominal(self) -> bool:
        return True

    # Return a fresh type variable that ranges over this nominal ValueType
    #
    def ranges_over(self):
        tvar = NominalTypeVariable(self)

        # For each TypeVariable that parameterizes self, duplicate
        # it to form a part of tvar
        #
        vmap = {}
        for p in self._params:
            (pprime, vmap) = p.dupe(vmap)
            tvar._parts.append(pprime)
        tvar._vmap = vmap

        # Instantiate all scalar constraints from self using vmap

        for c in self._type_constraints._sconstraints.values():
            cnew = c.revar(vmap)
            tvar._cset._sconstraints[id(cnew)] = cnew

        for c in self._type_constraints._atoms:
            cnew = c.revar(vmap)
            tvar._cset._atoms[id(cnew)] = cnew

        return tvar

    def root_nominal_type(self): return self # type: ignore

    # A non-composite ValueType can have a root unconstrained type.
    #
    def root_unconstrained_type(self):
        if self.arity() == 1:
            return self._params[0].typeof().root_unconstrained_type()
        else:
            raise Exception(f"Composite nominal type {self.display()} has no root unconstrained type")

    def __str__(self):
        return f"ValueType({self.display()})"
