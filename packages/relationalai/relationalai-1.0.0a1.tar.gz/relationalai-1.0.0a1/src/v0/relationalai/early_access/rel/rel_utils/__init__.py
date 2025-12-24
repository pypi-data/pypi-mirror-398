import warnings

from v0.relationalai.semantics.rel.rel_utils import sanitize_identifier

__all__ = ['sanitize_identifier']

warnings.warn(
    "relationalai.early_access.rel.rel_utils is deprecated, "
    "use relationalai.semantics.rel.rel_utils instead",
    DeprecationWarning,
    stacklevel=2,
)