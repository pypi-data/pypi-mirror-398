from v0.relationalai.semantics.metamodel import factory as f
from v0.relationalai.semantics.metamodel.util import FrozenOrderedSet
from v0.relationalai.semantics.metamodel import builtins

# Indicates a relation is short-lived, thus, backends should not optimize for incremental
# maintenance.
adhoc = f.relation("adhoc", [])
adhoc_annotation = f.annotation(adhoc, [])

# We only want to emit attributes for a known set of annotations.
annotations_to_emit = FrozenOrderedSet([
    adhoc.name,
    builtins.function.name,
    builtins.track.name,
    builtins.recursion_config.name,
])
