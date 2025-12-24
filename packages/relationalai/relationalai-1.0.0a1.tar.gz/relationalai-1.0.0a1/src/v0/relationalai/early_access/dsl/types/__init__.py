from typing import Optional

from v0.relationalai.early_access.dsl.core.relations import Relation, AbstractRelation


class AbstractConcept:

    # We can add relation components to a ConceptModule by invoking it
    # with arguments that interleave reading text with the Types used
    # to play various Roles
    #
    def __setattr__(self, key, value):
        if key in dir(self) and key not in self.__dict__:
            raise Exception(f"Cannot override method {key} of Type {self._name} as an attribute.")
        else:
            if key[0] != '_':
                self._relations[key] = value
            return super().__setattr__(key, value)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __init__(self, model, name):
        self._name = name
        self._model = model
        self._relations = {}

    def relation(self, *args, name: Optional[str] = None, functional: bool=False) -> Relation:
        if len(args) == 1 and not isinstance(args[0], str):
            raise ValueError("For binary or higher order relations parameter 'args' should contain "
                            "Sequence of text fragments followed by Types.")
        relationship = self._model.relationship(*[self, *args], relation_name=name)
        rel = next(iter(relationship.relations()), None)
        if rel is not None:
            rel.signature().set_functional(functional)
            return rel
        raise Exception(f"Could not find relation for relationship {relationship.name()}")

    def _add_relation(self, relation: AbstractRelation):
        self.__setattr__(relation._relname, relation)