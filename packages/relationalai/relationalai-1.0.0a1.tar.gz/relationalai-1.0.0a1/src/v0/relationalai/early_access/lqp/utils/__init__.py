import warnings

from v0.relationalai.semantics.lqp.utils import TranslationCtx, gen_unique_var, output_names, UniqueNames

__all__ = ["TranslationCtx", "gen_unique_var", "output_names", "UniqueNames"]

warnings.warn(
    "relationalai.early_access.lqp.utils is deprecated. "
    "Please migrate to relationalai.semantics.lqp.utils",
    DeprecationWarning,
    stacklevel=2,
)