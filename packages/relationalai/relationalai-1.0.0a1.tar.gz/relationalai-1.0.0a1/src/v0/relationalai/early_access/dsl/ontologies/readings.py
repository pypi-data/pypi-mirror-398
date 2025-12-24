from typing import List, Optional

from v0.relationalai.early_access.dsl.core.types import Type
from v0.relationalai.early_access.dsl.core.utils import generate_stable_uuid
from v0.relationalai.early_access.dsl.ontologies.roles import AbstractRole
from v0.relationalai.early_access.dsl.utils import build_relation_name, build_relationship_name


class Reading:

    # We initialize a Reading with a tuple that mixes text with Roles.
    #
    def __init__(self, *args, name: Optional[str] = None):
        self.rel_name = name  # Local name of Relation that materializes this Reading
        self.roles = []
        self.text_frags = []
        for i in range(len(args)):
            a = args[i]
            if isinstance(a, str):
                self.text_frags.append(a)
            else:
                if isinstance(a, AbstractRole):
                    self.roles.append(a)
                else:
                    raise Exception(f"Unknown Reading component {a} -- should be either text or a Role")

    def guid(self):
        return generate_stable_uuid(self.verbalize())

    def types(self) -> List[Type]:
        return [role.player() for role in self.roles]

    def template(self):
        temp_frags = []
        for i in range(len(self.roles)):
            temp_frags.append('{' + f"{i}" + '}')
            if i in range(len(self.text_frags)):
                temp_frags.append(self.text_frags[i])
        return " ".join(temp_frags)

    def verbalize(self):
        temp_frags = []
        for i in range(len(self.roles)):
            temp_frags.append(self.roles[i].verbalize())
            if i in range(len(self.text_frags)):
                temp_frags.append(self.text_frags[i])
        return " ".join(temp_frags)

    def to_rel_name(self):
        if self.rel_name:
            return self.rel_name
        return build_relation_name(self.roles, self.text_frags)

    def to_relationship_name(self):
        return build_relationship_name(self.roles, self.text_frags)

    def role_at(self, idx):
        if idx < 0 or idx >= len(self.roles):
            raise Exception(f'Role index {idx} out of bounds for Reading {self.to_rel_name()}')
        return self.roles[idx]