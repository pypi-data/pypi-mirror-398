from v0.relationalai.early_access.dsl.core.relations import Relation


def prev(r: 'Relation') -> Relation:
    p = Relation(r._container, f"{r._relname}__prev", r._signature)
    return p