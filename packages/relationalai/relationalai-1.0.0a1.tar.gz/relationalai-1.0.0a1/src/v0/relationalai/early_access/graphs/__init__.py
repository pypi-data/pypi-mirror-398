__version__ = "0.0.0"
import warnings

from v0.relationalai.semantics.reasoners.graph.core import Graph

__all__ = ["Graph"]

warnings.warn(
    "relationalai.early_access.graphs.* is deprecated. "
    "Please migrate to relationalai.semantics.reasoners.graph.*",
    DeprecationWarning,
    stacklevel=2,
)