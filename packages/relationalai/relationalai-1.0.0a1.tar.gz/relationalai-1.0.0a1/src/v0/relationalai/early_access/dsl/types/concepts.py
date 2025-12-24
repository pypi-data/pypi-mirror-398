from typing import Optional

from v0.relationalai.early_access.dsl.core.types.concepts import Concept as CoreConcept
from v0.relationalai.early_access.dsl.types import AbstractConcept
from v0.relationalai.early_access.dsl.core.types import Type as CoreType


class Concept(AbstractConcept, CoreConcept):

    def __init__(self, model, name, extends: Optional[CoreType]=None):
        super().__init__(model, name)
        CoreConcept.__init__(self, name, extends)