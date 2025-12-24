import v0.relationalai.semantics as qb


def reference_entity(concept: qb.Concept, *args, check_population: bool=True):
    kwargs = entity_kwargs(concept, *args, shallow=True)
    if check_population:
        return concept.filter_by(**kwargs)
    else:
        return concept.to_identity(**kwargs)

def construct_entity(concept: qb.Concept, *args):
    kwargs = entity_kwargs(concept, *args)
    return concept.to_identity(**kwargs)

def entity_kwargs(concept: qb.Concept, *args, shallow=False):
    ref_scheme = concept._ref_scheme(shallow=shallow)
    if not ref_scheme:
        raise ValueError(f'Concept {concept} has no reference scheme defined')
    keys = [rel._short_name for rel in ref_scheme]
    if len(args) != len(keys):
        raise ValueError(f'Expected {len(keys)} arguments for constructor of {concept}, got {len(args)}')
    kwargs = dict(zip(keys, args))
    return kwargs
