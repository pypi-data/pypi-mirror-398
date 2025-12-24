from v0.relationalai.early_access.dsl.types import AbstractConcept
from v0.relationalai.early_access.dsl.core.types.constrained.nominal import ValueType as CoreValueType
from v0.relationalai.early_access.dsl.core.types.constrained.subtype import ValueSubtype as CoreValueSubtype


class ValueType(AbstractConcept, CoreValueType):

    def __init__(self, model, nm, *args):
        super().__init__(model, nm)
        CoreValueType.__init__(self, nm, *args)


class ValueSubtype(AbstractConcept, CoreValueSubtype):

    def __init__(self, model, nm, *args):
        super().__init__(model, nm)
        CoreValueSubtype.__init__(self, nm, *args)
