


# Creates a new relation with the same attributes as `r`
def clone_relation(r):
    atts = ""
    for col in r._fields:
        atts += f"{{{col.type_str}}}"

    s = r._model.Relationship(atts)

    return s
