from __future__ import annotations
from typing import Optional, Any, Union

import re
import v0.relationalai.semantics as qb
from v0.relationalai.semantics.internal.internal import RelationshipFieldRef, Field
from v0.relationalai.early_access.dsl.core.utils import generate_stable_uuid
from v0.relationalai.early_access.dsl.orm.utils import generate_rai_way_name

##########
# Utility functions for parsing RelationshipReading patterns
#

def leading_text_of(reading: RelationshipReading):
    pattern = r"^([^{]*).*$"
    return re.findall(pattern, reading._madlib)[0].strip()

# Returns the dictionary of texts following a role (empty string if not present)
# indexed by the role position
#
def roles_data_from(reading: RelationshipReading):
    # This pattern capture the player name (with optional role name) and the following text for each
    # role in the madlib string
    # \{([^{}]*)\}   Player or role_name:Player
    # ([^{]*)       Following text
    pattern = r"\{([^{}]*)\}([^{]*)"

    matches = re.findall(pattern, reading._madlib)
    following_texts = dict()

    for i, (_, follows) in enumerate(matches):
        following_texts[i] = follows.strip()
    return following_texts

# Analyzes a substring of relationship-reading pattern text that contains
# no role occurrences and refines it into a triple of 3 optional strings:
#
#  - post: is a substring of text that post-binds to the role occurrence
#    that this text follows
#  - inter: is a substring that is not part of any post or pre bound text
#  - pre: is a substring that pre-binds the role occurrence that follows
#    this text sequence in the original reading pattern.
#
# Any of these sequences could be empty on return.
#
def refine_reading_text(text):
    found_prefix = False
    post = None
    inter = None
    pre = None

    inter_seq = []
    pre_seq = []

    tokens = text.split()
    for v in tokens:
        if v.startswith('-'):
            if found_prefix:
                raise Exception(f"Malformed reading text {text} has prefix text preceding postfix text")
            inter_seq.append(v[1:])
            post = " ".join(inter_seq)
            inter_seq = []
        elif v.endswith('-'):
            if found_prefix:
                raise Exception(f"Malformed reading text {text} has multple postfix text delimeters")
            found_prefix = True
            pre_seq = [ v[0:len(v)-1] ]
        else:
            if found_prefix:
                pre_seq.append(v)
            else:
                inter_seq.append(v)

    if len(pre_seq) > 0:
        pre = " ".join(pre_seq)
    if len(inter_seq) > 0:
        inter = " ".join(inter_seq)

    return (post, inter, pre)


class Relationship(qb.Relationship):

    def __init__(self, model, madlib:Any, short_name:str="", fields:Optional[list[Field]]=None):
        super().__init__(madlib, short_name=short_name, model=model.qb_model(), fields=fields)
        self._dsl_model = model
        self._rel_roles = {field.name: self.__getitem__(field.name) for field in self._fields}
        self._readings[0] = RelationshipReading(self._dsl_model, madlib, self, short_name)

    def __getitem__(self, arg:Union[str, int, qb.Concept]) -> Any:
        rel_field_ref = super().__getitem__(arg)
        field_name = rel_field_ref._field_ref._name
        if hasattr(self, "_rel_roles"):
            if field_name in self._rel_roles:
                return self._rel_roles[field_name]
            else:
                raise ValueError(f"{arg} is undefined for {self._name}")
        return Role._from_field(rel_field_ref)

    def _guid(self):
        return generate_stable_uuid(str(self._id))

    def alt(self, madlib:Any, short_name:str = "", reading:qb.RelationshipReading|None = None) -> qb.RelationshipReading:
        return super().alt(madlib, short_name=short_name,
                           reading=RelationshipReading(self._dsl_model, madlib, self, short_name))

    def _unary(self):
        return self._arity() == 1

    def _binary(self):
        return self._arity() == 2

    def _first(self):
        return self.__getitem__(0)

    def _roles(self):
        return [self._rel_roles[field.name] for field in self._fields]


class RelationshipReading(qb.RelationshipReading):

    def __init__(self, model, madlib:Any, alt_of:Relationship, short_name:str):
        super().__init__(madlib, alt_of, short_name, model=model.qb_model())
        self._dsl_model = model
        self._prepare()

    def __getitem__(self, arg:Union[str, int, qb.Concept]) -> Any:
        return Role._from_field(super().__getitem__(arg))

    def _guid(self):
        return generate_stable_uuid(str(self._id))

    def _unary(self):
        return self._arity() == 1

    def _binary(self):
        return self._arity() == 2

    def _first(self):
        return self.__getitem__(0)

    def _last(self):
        roles = self._roles()
        return roles[len(roles) - 1]

    def _roles(self):
        return [self._alt_of._rel_roles[field.name] for field in self._fields]

    def rai_way_name(self):
        return generate_rai_way_name(self)

    def _sample_fact(self) -> str:
        verb = []
        for idx in range(len(self._role_in_reading)):
            verb.append(str(self._role_in_reading[idx]))
            follows = self._follows[idx]
            if follows is not None:
                verb.append(follows)
        return ' '.join(verb)

    # Analyzes the reading pattern supplied with this reading to compute:
    #  - the leading text (or None)
    #  - the sequence of role occurrences in this reading order, and
    #  - the sequence of text fragments that follow each role occurrence
    #    in this reading order
    #
    def _prepare(self):

        self._follows: list[Optional[str]] = []
        self._role_in_reading: list[RoleOccurrence] = []

        (post, self._leading_text, pre) = refine_reading_text(leading_text_of(self))
        pre_seq = {0: pre}
        role_seq = self._roles()

        idx = 0
        dict = roles_data_from(self)
        for v in dict.values():
            (post, inter, pre) = refine_reading_text(v)
            self._role_in_reading.append(RoleOccurrence(role_seq[idx], pre_seq[idx], post))
            self._follows.append(inter)
            pre_seq[idx + 1] = pre
            idx += 1


class Role(RelationshipFieldRef):
    _sibling: Optional[Role] = None

    def __init__(self, parent:Any, part_of, pos):
        super().__init__(parent, part_of, pos)

    def _guid(self):
        return generate_stable_uuid(f"{self._field_ix}_{self._part_of()._guid()}")

    def player(self) -> qb.Concept:
        return self._concept

    def sibling(self):
        if self._relationship._arity() == 2 and not self._sibling:
            first_role = self._relationship[0]
            sibling = self._relationship[1] if self._id == first_role._id else first_role
            self._sibling = sibling
        return self._sibling
    
    def siblings(self):
        return [self._relationship[i] for i in range(self._relationship._arity()) if i != self._field_ix]

    def _part_of(self):
        return self._relationship

    @staticmethod
    def _from_field(field:RelationshipFieldRef):
        return Role(field._parent, field._relationship, field._field_ix)

    def __hash__(self):
        return hash(f"Role({self._guid()})")

    def __eq__(self, other):
        if not isinstance(other, Role):
            return False
        return self._guid() == other._guid() and self._part_of() == other._part_of()

# A RoleOccurrence objectifies the occurrence of a Role in some RelationshipReading
# to account for any pre- and/or post-bound text around the Role occurrence in
# that reading. For instance, in the RelationshipReading with this reading pattern:
#
#     "{Person} has personal- {Vehicle}"
#
# the RoleOccurrences for the roles verbalize as
#
#     "Person" and
#     "personal Vehicle"
#
class RoleOccurrence:

    def __init__(self, role: Role, pre: Optional[str], post: Optional[str]):
        self._prefix: Optional[str] = pre
        self._postfix: Optional[str] = post
        self._role: Role = role
        self._verbalizes_as: Optional[str] = None

    def __str__(self):
        if self._verbalizes_as is None:
            verb_seq = []
            if self._prefix is not None:
                verb_seq.append(self._prefix)
            verb_seq.append(str(self._role.player()))
            if self._postfix is not None:
                verb_seq.append(self._postfix)
            self._verbalizes_as = " ".join(verb_seq)
        return self._verbalizes_as
