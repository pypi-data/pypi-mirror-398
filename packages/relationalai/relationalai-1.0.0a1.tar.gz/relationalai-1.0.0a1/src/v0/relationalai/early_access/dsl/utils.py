from v0.relationalai.early_access.dsl.core.types import Type
from v0.relationalai.early_access.dsl.core.utils import camel_to_snake, to_rai_way_string, to_pascal_case
from v0.relationalai.early_access.dsl.constants import VERBAL_PART_CONNECTION
from v0.relationalai.early_access.dsl.ontologies.roles import Role

def normalize(s):
    return "\n".join(line.strip() for line in s.splitlines() if line.strip())

def build_relation_name(roles, verbal_parts):
    """
    Build the relation name from the verbal parts and roles. The relation name does not include the namespace.
    We can derive the name of the relation from the Role names and the reading (verbal_parts).

    Simple case: the Relationship is either unary or binary.
    In case when the reading starts with:
    - "is": we use the reading omitting "is";
    - "has": we use the reading omitting "has";
    if role doesn't have a name then role's player name transformed from camel case to snake is used.
    - otherwise, the reading is used.
    Examples:
    - reading: "{Person} is female" -> namespace: "person", relation name: "female"
    - reading: "{Person} has birth {Date}" -> namespace: "person", relation name: "birth"
    - reading: "{Account} has {AccountNr}" -> namespace: "account", relation name: "nr" (or "account_nr" when role has no name)
    - reading: "{Account} created on {Date}" -> namespace: "account", relation name: "created_on"

    Complex case: the Relationship has more than two Roles.
    We typically omit the name of the first Role in the reading, use the rest of the reading filling in
    the role name positions with the names.
    Examples:
    - reading: "{Person} has {Child} born on {Date}" -> namespace: "person", relation name: "has_child_born_on_date"
    - reading: "{Account} on {Date} has activation- {Event}" -> namespace: "account", relation name: "on_date_has_activation_event"

    """
    rel_name = ""
    if len(roles) == 1:  # for unary relations
        if len(verbal_parts) > 0:
            rel_name = to_rai_way_string(verbal_parts[0])
        if not rel_name:
            rel_name = _get_role_name(roles[0])
    elif len(roles) == 2:  # for binary relations
        s_role = roles[1]
        if len(verbal_parts) > 0:
            rel_name = to_rai_way_string(verbal_parts[0])
            if verbal_parts[0].strip().startswith(("has", "is")):
                if not rel_name:
                    rel_name += _get_role_name(s_role)
        else:
            rel_name = _get_role_name(s_role)
    else:
        # assumption that len(roles) - 1 == len(verbal_parts)
        join_parts = [to_rai_way_string(verbal_parts[0], False)]
        for i in range(1, len(roles)): # skip the first role
            role = roles[i]
            join_parts.append(_get_role_name(role))
            if i < len(roles) - 1:  # append verbal part after each iteration except the last one
                join_parts.append(to_rai_way_string(verbal_parts[i]))
        rel_name = VERBAL_PART_CONNECTION.join(join_parts)
    return rel_name

def build_relationship_name(roles, verbal_parts):
    """
    Build the relationship name from the verbal parts and roles.

    """
    relationship_name = ""
    for i in range(len(roles)):
        relationship_name += to_pascal_case(roles[i].verbalize())
        # assumption that len(roles) >= than len(verbal_parts)
        if i < len(verbal_parts):
            relationship_name += to_pascal_case(verbal_parts[i])

    return relationship_name

def extract_relation_text_with_signature(*args):
    types = []
    text_frags = []
    if len(args) < 2:
        raise Exception("Invalid declaration for the unary relation. Type should be followed by a text.")

    for i in range(len(args)):
        a = args[i]
        # even must be 'Type' and odd must be 'str'
        if i % 2 == 0:
            if not isinstance(a, Type):
                raise Exception(f"Invalid declaration for the relation. Argument {i + 1} is not a type.")
            types.append(a)
        else:
            if not isinstance(a, str):
                raise Exception(f"Invalid declaration for the relation. Argument {i + 1} is not a text.")
            text_frags.append(a)
    # check that N-ary relation ends with Type. Exclude the case for unary when args == 2: (Person, "is adult")
    if len(text_frags) == len(types) and len(args) > 2:
        raise Exception("Invalid declaration for the relation. Relations with arity > 2 must end with a type.")

    return text_frags, types

def _get_role_name(role) -> str:
    if isinstance(role, Type):
        return camel_to_snake(role.display())
    elif isinstance(role, Role):
        return to_rai_way_string(role.ref_name(), False) if role.name else camel_to_snake(role.player().display())
    raise Exception(f"Invalid declaration for the relation. Argument {role} is not a 'Type' or a 'Role'.")