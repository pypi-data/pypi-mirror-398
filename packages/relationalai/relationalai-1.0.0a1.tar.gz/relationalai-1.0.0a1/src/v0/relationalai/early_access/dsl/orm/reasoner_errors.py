class MultipleSupertypesUnsupportedError(NotImplementedError):
    """Raised when an entity type has multiple supertypes, which is not supported."""
    def __init__(self, entity_type):
        super().__init__(f"Entity type '{entity_type}' has multiple supertypes, which is unsupported.")
        self.entity_type = entity_type


class MissingReferenceSchemeError(KeyError):
    """Raised when a reference scheme for an entity type is missing in the model."""
    def __init__(self, entity_type, lookup_chain):
        super().__init__(f"No reference scheme found for entity type '{entity_type}' in chain {lookup_chain}.")
        self.entity_type = entity_type
        self.lookup_chain = lookup_chain