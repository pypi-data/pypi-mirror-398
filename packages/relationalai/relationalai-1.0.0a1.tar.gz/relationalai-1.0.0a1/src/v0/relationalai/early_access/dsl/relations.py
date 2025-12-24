from v0.relationalai.early_access.dsl.core.relations import AbstractRelationSignature, RelationSignature
from v0.relationalai.early_access.dsl.core.types import Type
from v0.relationalai.early_access.dsl.core.types.standard import PositiveInteger, UnsignedInteger

class AbstractFunctionSignature(AbstractRelationSignature):

    def functional(self): return True

class EmptyRelation:

    def __init__(self, sig):
        self._signature = sig

    def display(self): return 'EMPTYSET'

    def entityid(self): return hash((EmptyRelation, self._signature.entityid()))

    def pprint(self):
        return self.display() + self._signature.display()

    def rename(self, bdgs): return self

class FunctionSignature(AbstractFunctionSignature):
    pass

class Sequence(AbstractFunctionSignature):

    def __init__(self, T, *types):
        super().__init__(*types)
        self._range = T

    def range(self): return self._range

class SequenceOne(Sequence):

    def __init__(self, T):
        super().__init__(T, PositiveInteger, T)

    def display(self):
        return f"seq {self.range().display()}"

    def entityid(self):
        return hash((Sequence, self.range().entityid()))

class SequenceZero(Sequence):

    def __init__(self, T):
        super().__init__(T, UnsignedInteger, T)

    def display(self):
        return f"seq0 {self.range().display()}"

    def entityid(self):
        return hash((SequenceZero, self.range().entityid()))

class InjectiveSequenceOne(SequenceOne):

    def __init__(self, T):
        Sequence.__init__(self, T)

    def display(self):
        return f"iseq {self.range().display()}"

    def entityid(self):
        return hash((InjectiveSequenceOne, self.range().entityid()))


class InjectiveSequenceZero(SequenceZero):

    def __init__(self, T):
        Sequence.__init__(self, T)

    def display(self):
        return f"iseq0 {self.range().display()}"

    def entityid(self):
        return hash((InjectiveSequenceZero, self.range().entityid()))

class FunctionFactory:

    def __call__(self, *args):

        nargs = len(args)

        if nargs < 2 or nargs > 3:
            raise Exception("Must instantiate functions with two type arguments and an optional name")

        dtype = args[0]
        rtype = args[1]

        if not isinstance(dtype, Type):
            raise Exception(f"Function signature domain must be a valid Type, not {dtype}")

        if not isinstance(rtype, Type):
            raise Exception(f"Function signature range must be a valid Type, not {rtype}")

        rsig = FunctionSignature((dtype, rtype))

        if nargs == 3:
            name = args[2]
            if isinstance(name, str):
                return rsig(name)
            else:
                raise Exception("Component name provide when instantiating Func is not a string")
        else:
            return rsig


class RelationFactory:

    def __call__(self, *args):

        if len(args) == 0:
            raise Exception("Must instantiate relations with one or more column types and an optional name")

        nargs = len(args)
        includes_name = isinstance(args[nargs - 1], str)
        columns = nargs - 1 if includes_name else nargs
        column_types = []
        for i in range(columns):
            if not isinstance(args[i], Type):
                raise Exception(f"Relation signatures must comprise a types, not {args[i]}")

            column_types.append(args[i])
        rsig = RelationSignature(*column_types)

        if includes_name:
            return rsig(args[nargs - 1])
        else:
            return rsig


class SequenceFactory:

    def __init__(self, ctor):
        self._ctor = ctor

    def __call__(self, *args):

        if len(args) == 0:
            raise Exception("Must instantiate sequence types with an element type")

        if len(args) > 2:
            raise Exception("Cannot create sequences of composite element type")

        element_type = args[0]
        if not isinstance(element_type, Type):
            raise Exception("First parameter of Sequence instance must be an element type")

        seq = self._ctor(element_type)
        if len(args) == 2:
            if isinstance(args[1], str):
                return seq(args[1])
            else:
                raise Exception("Can only instantiate sequence type with a string name")
        else:
            return seq


# Constructors that can be used in Schema declarations for relations of
# various kinds that are not declared in an ontology.
#

Rel = RelationFactory()
Func = FunctionFactory()

Seq = SequenceFactory(SequenceOne)
Seq0 = SequenceFactory(SequenceZero)
Iseq = SequenceFactory(InjectiveSequenceOne)
Iseq0 = SequenceFactory(InjectiveSequenceZero)
