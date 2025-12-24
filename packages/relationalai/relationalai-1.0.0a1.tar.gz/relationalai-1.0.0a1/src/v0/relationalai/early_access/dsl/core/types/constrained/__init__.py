from abc import abstractmethod

from v0.relationalai.early_access.dsl.core.builders.logic import ScalarConstraintBuilder, LogicBuilder
from v0.relationalai.early_access.dsl.core.cset import ConstraintSet
from v0.relationalai.early_access.dsl.core.exprs.scalar import ScalarExprBuilder, box_number
from v0.relationalai.early_access.dsl.core.relations import RelationSignature, ExternalRelation
from v0.relationalai.early_access.dsl.core.types import AbstractValueType
from v0.relationalai.early_access.dsl.core.types.variables import UnstableConstraintSet, NominalTypeVariable, \
    BasicTypeVariable, TypeVariable


# A ConstrainedValueType:
#
#  * is identified by a *name*,
#  * is parameterized by a sequence *params* of TypeVariables
#  * has a set *constraints* of ScalarConstraints
#
# We implement constraint sets using an int-keyed dictionary to simplify
# duplicate constraint removal.
#
class ConstrainedValueType(AbstractValueType, ScalarExprBuilder, LogicBuilder):

    def __enter__(self): # type: ignore
        super().__enter__()
        return self.typevar_tuple()

    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)
        self.name_type_variables()

    def __init__(self, nm):
        AbstractValueType.__init__(self, nm)
        self._params = []
        self._type_constraints = UnstableConstraintSet()
        self._constructor = None

    def __xor__(self, args):
        return self.constructor()(*args)

    def build_comparison(self, left, op, right):
        c = ScalarConstraintBuilder.build_comparison(self, left, op, right)
        tc = self._type_constraints
        tc.add_scalar_constraint(c)
        return c

    # Generates a string that displays the TypeVariable constraints (one per line)
    # declared by this ConstrainedValueType
    #
    def constraint_display(self):
        exists = []
        for v in self._params:
            if isinstance(v, NominalTypeVariable):
                exists.append(v.all_constraint_display())
        exists_atoms = "\n".join(exists)
        exists_ppr = exists_atoms + "\n" if exists_atoms != "" else ""

        constraints = [f"   {c.pprint()}" for c in self.denotes().values()]
        if exists_ppr != "":
            return exists_ppr + "\n" + "\n".join(constraints)
        else:
            return "\n".join(constraints)

    def constructor(self):
        if self._constructor is None:
            # Create a constructor function (relation) for this ValueType
            ctortype = [item.typeof() for item in self.ctordomain()]
            ctortype.append(self)
            self._constructor = ExternalRelation(self.namespace(),
                                                 self.ctor_name(),
                                                 RelationSignature(*tuple(ctortype)))
        return self._constructor

    # Returns True if the Python constant `val` is an instance of this ValueType
    def contains(self, val):

        if self.signature_arity() != 1:
            raise Exception(
                f"NOT IMPLEMENTED: Check containment of values in ({self.display()}) which is not unary")

        # Get the lone type variable over which `self` imposes additional constraints
        tvar = self._params[0]
        if tvar.decl.contains(val) and isinstance(self._type_constraints, ConstraintSet):
            return self._type_constraints.evaluate({tvar.varname(): box_number(val)}) is not None

        return False

    def ctordomain(self):
        return self._params

    def ctor_name(self):
        return f"^{self.display()}"

    # Returns what ORM would consider to be the "DataType" of this AbstractValueType, if it makes sense.
    #
    def datatype(self):
        if not self.unary():
            raise Exception(
                f"Cannot infer an ORM datatype from AbstractValueType {self.display()}, which is not a "
                f"ConstrainedUnaryValueType")

        return self._params[0].typeof()

    # Assemble the set of constraints that are either declared or inherited by
    # this ConstrainedValueType. This method does not attempt to minimize constraints,
    # in contrast with verifies.
    #
    def denotes(self):
        C = self._type_constraints._sconstraints.copy()
        for ac in self._type_constraints._atoms.values():
            scs = self.interpret_type_atom(ac)
            for s in scs:
                if s not in C:
                    C[s] = scs[s]

        for p in self._params:
            C = p.denotes(C)

        return C

    # Generates the headline declaration of this ConstrainedValueType, separately
    # form the constraints, as the structure of this headline varies based on
    # whether this is a ValueType or a ValueSubtype
    #
    @abstractmethod
    def head_display(self) -> str: pass

    # Interpret Atom ac as an AtomicConstraint of the form:
    #
    #    T(x)
    #
    # where T is a ConstrainedValueType and x is a TypeVariable.
    #
    # Checks that the type of x conforms to that of the lone TypeVariable
    # that parameterizes T and returns all ScalarConstraints that T imposes
    # on those variables.
    #
    def interpret_type_atom(self, ac):

        T = ac.relation()
        args = ac.args

        if len(args) > 1:
            raise Exception(f"Cannot apply ValueSubtype constraint ({T.display()}) to more than one TypeVariable")

        vmap = {}
        tv = args[0]
        if isinstance(tv, BasicTypeVariable):
            if T.nominal():
                raise Exception(
                        f"Argument mismatch when using type {T.display()} as an AtomicConstraint in context of ValueType {self.display()}")

            if T.root_unconstrained_type() != tv.decl.root_unconstrained_type():
                raise Exception(
                    f"Applying type constraint {T.display()} to variable of incompatible unconstrained "
                    f"type {tv.decl.physical_typeof().pprint()}")

            vmap[id(T._params[0])] = tv
        else:
            # tv is a NominalTypeVariable

            ttup = flatten_typevar_tuple([], T.typevar_tuple())
            tvtup = flatten_typevar_tuple([], tv.typevar_tuple())

            if len(ttup) != len(tvtup):
                raise Exception(
                    f"Argument mismatch when using type {T.display()} as an AtomicConstraint in context of ValueType {self.display()}")

            for i in range(len(ttup)):
                if not isinstance(tvtup[i], TypeVariable):
                    raise Exception(
                        f"When using type {T.display()} as an AtomicConstraint in context of ValueType {self.display()}, {i}-th "
                        f"argument is not a TypeVariable")

                tup_basic_type = ttup[i].physical_typeof()
                tvtup_basic_type = tvtup[i].physical_typeof()

                # Validate that tup_basic_type and arg_basic_type are compatible

                if tup_basic_type != tvtup_basic_type:
                    raise Exception(
                        f"Applying basic type constraint {T.display()} to variable of incompatible unconstrained "
                        f"type {tvtup_basic_type.pprint()}")

                vmap[id(ttup[i])] = tvtup[i]

        rv = {}
        constraints = T.denotes()
        for cindex in constraints:
            c = constraints[cindex]
            dupc = c.revar(vmap)
            rv[dupc.entityid()] = dupc
        return rv

    # Assign a unique number to each type variable (including the parts of nominal type variables,
    # recursively) so that each type variable in the signature of this ConstrainedValueType will
    # have a unique name to use in interpreting type constraints.
    #
    def name_type_variables(self, initial_pos=0):
        pos = initial_pos
        for v in self._params:
            pos = v.setpos(pos)
        self._type_constraints = self._type_constraints.stabilize()

    def pprint(self):
        body = self.constraint_display()
        if body != "":
            return self.head_display() + ":\n" + body
        else:
            return self.head_display()

    def signature_arity(self):
        sum = 0
        for v in self._params:
            sum = sum + v.typeof().signature_arity()
        return sum

    # Returns the (possibly nested) tuple of BasicTypeVariables over which this ConstrainedValueType
    # ranges. This is useful when instantiating this type, as the calling context will often need to
    # directly reference these BasicTypeVariables. So, for instance, using this facility, we can
    # write code like:
    #
    #    ((x, y), (w, z)) = DoubleInterval.typevar_tuple()
    #
    # The flatten_typevar_tuple function can be used to flatten these tuples into an array, in this
    # case:
    #
    #    [ x, y, w, z ]
    #
    def typevar_tuple(self):
        tvars = []
        for tvar in self._params:
            tp = tvar.typeof()
            if tp.nominal():
                tvars.append(tvar.typevar_tuple())
            else:
                tvars.append(tvar)
        if len(tvars) == 1:
            return tvars[0]
        else:
            return tuple(tvars)

    # Helper method that returns the UnconstrainedSignature of this ConstrainedValueType
    # in the special case where that tuple is a single BasicTypeVariable, raising
    # an exception otherwise.
    #
    def value(self):
        if self.signature_arity() != 1:
            raise Exception(
                f"Cannot refer to singleton value type variable for non-unary AbstractValueType {self.display()}")
        else:
            return self.typevar_tuple()

    def constraint(self) -> bool:
        return True


def flatten_typevar_tuple(seq, tup):
    if type(tup) is tuple:
        for v in tup:
            if tuple(v):
                seq = flatten_typevar_tuple(seq, v)
            else:
                seq.append(v)
    else:
        seq.append(tup)

    return seq
