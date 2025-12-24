from abc import abstractmethod
from typing import Optional

from v0.relationalai.early_access.dsl.core.types import Type
from v0.relationalai.early_access.dsl.core.utils import generate_stable_uuid, camel_to_snake


class AbstractRole:
    _postfix: Optional[str] = None
    _prefix: Optional[str] = None
    _sibling: Optional['AbstractRole'] = None

    # Initialize an AbstractRole with a UUID to use to identify it, the
    # Relationship of which it will be a part, and an optional name
    #
    def __init__(self, part_of, pos, name:Optional[str] = None):
        self._part_of = part_of
        self._pos = pos
        self._name = name

    def guid(self):
        return generate_stable_uuid(f"{self._pos}_{self._part_of.guid()}")

    def name(self) -> Optional[str]:
        return self._name

    def ref_name(self):
        defined_name = self.name()
        if not defined_name:
            defined_name = camel_to_snake(self.verbalize())
        return defined_name

    @abstractmethod
    def player(self)-> Type:
        pass

    def verbalization(self, prefix=None, postfix=None) -> 'AbstractRole':
        self._prefix = prefix
        self._postfix = postfix
        return self

    def verbalize(self):
        vfrags = []
        if self._prefix is not None:
            vfrags.append(f"{self._prefix}-")
        vfrags.append(f"{self.player().display()}")
        if self._postfix is not None:
            vfrags.append(f"-{self._postfix}")
        return " ".join(vfrags)

    def sibling(self):
        if self._part_of.arity() == 2:
            if not self._sibling:
                roles = self._part_of.roles()
                sibling = roles[1] if self == roles[0] else roles[0]
                self._sibling = sibling
        return self._sibling

    @property
    def part_of(self):
        return self._part_of

    @part_of.setter
    def part_of(self, rel):
        if self._part_of is not None and self._part_of != rel:
            raise ValueError(f"Role is already part of another relationship: {self._part_of}")
        self._part_of = rel

    @property
    def postfix(self):
        return self._postfix

    @property
    def prefix(self):
        return self._prefix


class Role(AbstractRole):

    def __init__(self, t, rel, pos, name=None):
        AbstractRole.__init__(self, rel, pos, name)
        if not isinstance(t, Type):
            raise Exception(f"Tried to create Role with unparsable player {t}")
        self.player_type = t

    def player(self):
        return self.player_type
