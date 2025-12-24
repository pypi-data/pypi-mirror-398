import warnings

from v0.relationalai.semantics.metamodel.ir import (sanitize, node_to_string, value_to_string, Task, Var, Logical,
                                                 ScalarType, Node, Capability, ListType, _global_id)

__all__ = ["sanitize", "node_to_string", "value_to_string", "Task", "Var", "Logical", "ScalarType", "Node",
           "Capability", "ListType", "_global_id"]

warnings.warn(
    "relationalai.early_access.metamodel.ir is deprecated, "
    "Please migrate to relationalai.semantics.metamodel.ir",
    DeprecationWarning,
    stacklevel=2,
)