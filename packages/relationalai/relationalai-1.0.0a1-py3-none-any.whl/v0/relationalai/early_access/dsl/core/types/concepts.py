from typing import Optional

from v0.relationalai.early_access.dsl.core.types import Type
from v0.relationalai.early_access.dsl.core.types.constrained import ConstrainedValueType

class Concept(ConstrainedValueType):

    def __init__(self, name: str, extends: Optional[Type]=None):
        super().__init__(name)
        self._name = name
        self._types = []
        if extends is not None:
            self._types.append(extends)

        for t in self._types:
            self.build_scalar_variable([t], {})
        self.name_type_variables()

    def build_scalar_variable(self, args, kwargs):
        if len(args) == 0:
            raise Exception(f"Unexpected error in Concept {self.display()}")

        if len(kwargs) != 0:
            raise Exception(
                f"Cannot use keyword arguments when instantiating a type parameter for Concept {self.display()}")

        p_type = args[0]
        if len(args) == 1:

            # Then we are instantiating T to create a new TypeVariable that will parameterize
            # this Concept (self)
            #
            self._parent = p_type
            tv = p_type.ranges_over()
            self.addparam(tv)
            return tv
        else:
            self._type_constraints.add_atomic_constraint(self.build_atom(p_type, args[1:]))

    def build_relation_variable(self, args, kwargs):
        if len(args) == 0:
            raise Exception(f"Unexpected error in Concept {self.display()}")

        if len(args) > 1:
            raise Exception(f"Cannot declare type variable of Concept {self.display()} by supplying more than a type")

        if len(kwargs) != 0:
            raise Exception(
                f"Cannot use keyword arguments when instantiating a type parameter for Concept {self.display()}")

        self._parent = args[0]

        tvar = self._parent.ranges_over()
        self._params.append(tvar)

        return tvar.typevar_tuple()

    # Add TypeVariable *tv* as a parameter to this type
    #
    def addparam(self, tv):
        self._params.append(tv)
        return tv

    def arity(self) -> int:
        if self._parent is None:
            return len(self._params)
        else:
            return self._parent.arity()

    # Returns True if this type is an EntityType or one of its subtypes
    # and False otherwise
    #
    def entity(self) -> bool:
        return False

    # Returns the Rel required to instantiate an instance of this Type
    # from a given value val. By default, just return val; subclasses
    # will override as appropriate
    #
    def instantiate(self, *val):
        if self._parent is None:
            return val[0]
        else:
            return self._parent.instantiate(val[0])

    def ranges_over(self):
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
        headvars = []
        for v in self._params:
            vt = v.typeof()
            if vt == self._parent:
                headvars.append(f"{v.display()}")
            else:
                headvars.append(f"{v.display()} in {vt.display()}")
        head = ", ".join(headvars)
        if self._parent is None:
            return f"value type {self.display()}({head})"
        else:
            return f"value type {self.display()} <: {self._parent.display()}({head})"

    def root_nominal_type(self): # type: ignore
        if self._parent is None:
            return self
        else:
            return self._parent.root_nominal_type()

    # A non-composite Concept can have a root unconstrained type.
    #
    def root_unconstrained_type(self):
        if self.arity() == 1:
            return self._params[0].typeof().root_unconstrained_type()
        else:
            raise Exception(f"Composite nominal type {self.display()} has no root unconstrained type")