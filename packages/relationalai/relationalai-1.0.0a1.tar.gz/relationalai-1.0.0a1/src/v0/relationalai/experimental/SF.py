from v0.relationalai.dsl import safe_symbol
from v0.relationalai.rel_utils import sanitize_identifier
from v0.relationalai.std import rel


def SFRawType(model, *, source):
    raw_relation_name = sanitize_identifier(source.lower())

    # We run the normal machinery to setup the source + retrieve metadata, but never actually consume the relations
    PyRelType = model.Type(f"__PyRel__{raw_relation_name}", source=source)

    sf_gnf_rel_name = sanitize_identifier(raw_relation_name + "_pyrel_id")

    # Generate the type from the raw table
    # @NOTE: The actual type isn't associated with the source, we handle mapping the raw CDC relations directly via
    #        zero-copy rules. This means the SFRawType entity ids are SF 160bit IDs instead of 128bit IDs, so
    #        intermixing will cause issues. Use with caution.
    # @NOTE: This work will be replaced by upstream work that does a similar thing but updates the CDC-created relations
    #        to be in the exact format we want.
    Typ = model.Type(f"__SF_RAW__{sf_gnf_rel_name}")
    relation = getattr(rel, sf_gnf_rel_name)  # unary relation of IDs
    with model.rule():
        Typ.add(relation())

    props = PyRelType.known_properties()

    # Generate the property mappings for the SF columns
    code = ""
    for prop in props:
        code += f"""
            def {sanitize_identifier(prop)}(row, value): {{
                {raw_relation_name}({safe_symbol(prop.upper())}, row, value)
            }}
        """

    model.install_raw(code)

    return Typ
