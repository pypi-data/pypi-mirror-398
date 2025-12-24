from __future__ import annotations

from v0.relationalai.semantics.internal import internal as b

def unique(*args: b.RelationshipFieldRef|b.Relationship|b.RelationshipRef|b.RelationshipReading, model:b.Model|None=None) -> tuple[b.Expression, ...]:
    if not args:
        raise ValueError("unique expects at least 1 argument")
    if len(args) > 1:
        if not all(isinstance(a, b.RelationshipFieldRef) for a in args):
            raise TypeError("Not all items are relationship fields")
        uc = b.Unique(*args, model=model) # type: ignore
    else:
        assert args
        if isinstance(args[0], b.RelationshipFieldRef):
            uc = b.Unique(*args) # type: ignore
        elif isinstance(args[0], (b.Relationship, b.RelationshipRef, b.RelationshipReading)):
            rel = args[0]._relationship if isinstance(args[0], b.RelationshipRef) else args[0]
            if rel._arity() != 2:
                raise ValueError("Only binary relationships are allowed")
            uc = b.Unique(rel[1], model=model)
        else:
            raise TypeError("Unexpected argument type. Only relationship fields or relationships are allowed")
    return uc.to_expressions()

def exclusive(*args: b.Concept|b.Ref, model:b.Model|None=None) -> tuple[b.Expression, ...]:
    return b.Exclusive(*_extract_concepts(*args), model=model).to_expressions()

def anyof(*args: b.Concept|b.Ref, model:b.Model|None=None) -> tuple[b.Expression, ...]:
    return b.Anyof(*_extract_concepts(*args), model=model).to_expressions()

def oneof(*args: b.Concept | b.Ref, model: b.Model | None = None) -> tuple[b.Expression, ...]:
    return exclusive(*args, model=model) + anyof(*args, model=model)

def _extract_concepts(*args: b.Concept|b.Ref) -> list[b.Concept]:
    concepts = []
    for arg in args:
        c = arg
        if isinstance(c, b.Ref):
            c = c._thing
            if not isinstance(c, b.Concept):
                raise TypeError("Only concepts and concept's ref are allowed as arguments")
        concepts.append(arg)
    return concepts
