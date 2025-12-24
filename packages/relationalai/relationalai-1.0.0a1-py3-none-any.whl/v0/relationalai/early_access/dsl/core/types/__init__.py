from abc import abstractmethod

from v0.relationalai.early_access.dsl.core.exprs import contextStack
from v0.relationalai.early_access.dsl.core.namespaces import Namespace
from v0.relationalai.early_access.dsl.core.types.variables import TypeVariable
from v0.relationalai.early_access.dsl.core.utils import generate_stable_uuid


# This abstract class generalizes over all types
#
class Type:

    # A Type T can be "instantiated" for one of several purposes, depending
    # on context:
    #
    #   1) in the context of a ConstrainedValueType, to add a parameter TypeVariable
    #      to that type; and
    #   2) in the context of a ConjunctiveSchema:
    #      a) if the argument is a string name, then adds a new ScalarComponent of
    #         that name to the schema; or
    #      b) if the argument is a ScalarVariable, then adds an atom that references
    #         the unary population relation for the EntityType in a Rel body formula
    #
    # In case (1), there should be no arguments (args); in case (2a), we expect there
    # to be exactly one string argument that names the component being added to the
    # SchemaFragment; while in context (2b) we expect there to be exactly one argument
    # of type ScalarVariable.
    #
    # Because we use RelationVariables to range over the parameters of a nominal value
    # type, to properly handle case (1) we have to call one of:
    #
    #  - build_relation_variable
    #  - build_scalar_variable
    #
    # depending on whether T is a nominal type. But that distinction is really only
    # relevant to case (1) -- which means the concrete builder objects that implement
    # the ScalarConstraintBuilder interface for cases (2a) and (2b) must implement
    # both methods the same way.
    #
    def __call__(self, *args, **kwargs):
        seq = [self]
        for i in range(len(args)):
            seq.append(args[i])

        if self.nominal() or self.entity():
            return contextStack.root_context().build_relation_variable(seq, kwargs)
        else:
            return contextStack.root_context().build_scalar_variable(seq, kwargs)

    def __enter__(self):
        contextStack.push(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        contextStack.pop()

    def __init__(self, nm):
        self._name = nm
        #
        if not contextStack.empty():
            tp = contextStack.root_context()
            if isinstance(tp, Namespace):
                self._namespace = tp
            else:
                self._namespace = Namespace.top
        else:
            self._namespace = Namespace.top

    # Returns the number of TypeVariables that parameterize this Type
    #
    def arity(self) -> int:
        return 1

    def display(self):
        return self._name

    # Returns True if this type is an EntityType or one of its subtypes
    # and False otherwise
    #
    def entity(self) -> bool:
        return False

    # Returns an integer (hash) that identifies this Type, allowing us
    # to treat Types sort of like entity types for which we had declared
    # a preferred identifier to allow different physical objects to unify
    # to the same entity. Contrast this with the "id" method which would
    # not allow us to do this unification.
    #
    def entityid(self):
        return hash(self._name)

    def guid(self):
        return generate_stable_uuid(self._name)

    # Returns the Rel required to instantiate an instance of this Type
    # from a given value val. By default, just return val; subclasses
    # will override as appropriate
    #
    def instantiate(self, *val):
        return val[0]

    def namespace(self):
        return self._namespace

    # This predicate returns True if this type is a ValueType or
    # some subtype of a ValueType.
    #
    def nominal(self) -> bool:
        return False


class AbstractValueType(Type):

    def __init__(self, nm):
        Type.__init__(self, nm)

    # Returns true if self is both unconstrained and also numeric, meaning its constraints
    # (if any) can be statically verified.
    #
    def basic_numeric(self) -> bool: return False

    # Returns True if the Python constant `val` is an instance of this ValueType
    def contains(self, val) -> bool: return False

    # Gathers the set of BasicTypeVariable constraints that this AbstractValueType denotes
    # either by declaring or inheriting.
    #
    def denotes(self): return {}

    # Returns true if this is a nominal value type or a subtype that is rooted by a nominal
    # value type
    #
    def nominal(self) -> bool: return False

    # Returns true if this is a constraint value type or a subtype that is rooted by a constrained
    # value type
    #
    def constraint(self) -> bool: return False

    # Returns true if this is a constraint value type or a subtype that is rooted by a constrained
    # value type and signature_arity is 1
    #
    def constraint_unary(self) -> bool:
        return self.constraint() and self.unary()

    # Creates a new TypeVariable that ranges over this AbstractValueType, including all
    # constraints (if any) suitably instantiated to the new TypeVariable
    #
    @abstractmethod
    def ranges_over(self) -> TypeVariable: pass

    # Where possible, returns the lone UnconstrainedValueType that will be used as the physical
    # representation of instances of this AbstractValueType at runtime.
    #
    def root_nominal_type(self):
        raise Exception(f"Cannot determine root nominal type of AbstractValueType {self.display()}")

    # The signature arity of a AbstractValueType refers to the number of BasicTypeVariables
    # that occur in its physical implementation. For UnconstrainedValueTypes, the arity is 1.
    # For ConstrainedValueTypes, the arity is the size of the flattened basic-type variable
    # tuple that it constrains.
    #
    def signature_arity(self) -> int: return 1

    # Returns true if this is a value type has signature_arity == 1
    #
    def unary(self):
        return self.signature_arity() == 1

    def subtype_of(self, T2):
        if self.nominal():
            if not T2.nominal():
                return False

            # Both are nominal value types, so make sure names are the same
            #
            nt1 = self.root_nominal_type()
            nt2 = T2.root_nominal_type()
            if nt1.display() != nt2.display():
                return False
        else:
            if T2.nominal():
                return False

            # Neither type is nominal, so check if one or both are unconstrained

            if self.unconstrained():
                return self.display() == T2.display()

            if T2.unconstrained():
                u2 = self.root_unconstrained_type() # type: ignore
                return T2.display() == u2.display()

        # All nominal type checking has passed and neither type is Unconstrained

        if self.signature_arity() != T2.signature_arity():
            return False

        # Types have same signature arities, so check constraints on type variables.

        mapping = map_type_var_tuple_to(self.typevar_tuple(), T2.typevar_tuple())

        if len(mapping) != self.signature_arity():
            return False

        # Same typevar tuples, so now just check that the every models of self is also
        # a model of T2.
        #
        cset1 = {}
        for c in self.denotes().values():
            cprime = c.rename(mapping)
            cset1[cprime.entityid()] = cprime

        return True

    # Returns true if this type is Unconstrained
    #
    def unconstrained(self) -> bool:
        return False

    @abstractmethod
    def typevar_tuple(self) -> tuple[TypeVariable, ...]:
        pass


def basic_type_instance(val):
    if isinstance(val, str):
        return True
    if isinstance(val, int):
        return True
    if isinstance(val, float):
        return True
    return False

def map_type_var_tuple_to(tup1, tup2):
    return map_type_var_tuple_to_rec(tup1, tup2, {})

def map_type_var_tuple_to_rec(tup1, tup2, m):
    if type(tup1) is tuple:
        if type(tup2) is not tuple:
            return {}

        v1 = tup1[0]
        v2 = tup2[0]
        m[v1.display()] = v2
        return map_type_var_tuple_to_rec(tup1[1:], tup2[1:], m)
    else:
        if type(tup2) is tuple:
            return {}
        m[tup1.display()] = tup2

    return m

def typevar_tuple_string_rec(tup) -> str:
    if type(tup) is not tuple:
        return tup.display()

    results = [typevar_tuple_string_rec(v) for v in tup]

    if len(results) == 1:
        return results[0]
    else:
        return "(" + ", ".join(results) + ")"


def typevar_tuple_string(tup) -> str:
    if type(tup) is not tuple:
        return f"({tup.display()})"
    else:
        return typevar_tuple_string_rec(tup)
