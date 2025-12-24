
from ..frontend.base import FieldRef, Fragment, Library, Expression, Field, Value, TupleVariable, Variable, Concept, Ref, MetaRef
from ..frontend import core

# the front-end library object
library = Library("constraints")

#------------------------------------------------------
# Constraint Relations
#------------------------------------------------------

_unique = library.Relation("unique", [Field.input("values", core.Any, is_list=True)])
_unique_fields = library.Relation("unique_fields", [Field.input("fields", core.Field, is_list=True)])
_exclusive = library.Relation("exclusive", [Field.input("concepts", core.Relation, is_list=True)])
_anyof =library.Relation("anyof", [Field.input("concepts", core.Relation, is_list=True)])

#------------------------------------------------------
# API
#------------------------------------------------------

def unique(*args: Variable) -> Expression:
    if all(isinstance(arg, FieldRef) for arg in args):
        fields = [MetaRef(arg._resolved) for arg in args] # type: ignore - we know these are FieldRefs from the all above
        return _unique_fields(TupleVariable(fields))
    return _unique(TupleVariable(args))

def exclusive(*args: Concept|Ref) -> Expression:
    concepts = [arg._to_concept() for arg in args]
    return _exclusive(TupleVariable(concepts))

def anyof(*args: Concept|Ref) -> Expression:
    concepts = [arg._to_concept() for arg in args]
    return _anyof(TupleVariable(concepts))

def oneof(*args: Concept | Ref) -> Fragment:
    model = args[0]._model
    return model.where(anyof(*args), exclusive(*args))
