import warnings

from v0.relationalai.semantics.reasoners.optimization import make_name, all_different, implies, Solver, Provider, SolverModel

__all__ = [
    "Solver",
    "Provider",
    "SolverModel",
    "make_name",
    "all_different",
    "implies",
]

warnings.warn(
    "relationalai.early_access.solvers.* is deprecated. "
    "Please migrate to relationalai.semantics.reasoners.optimization.*",
    DeprecationWarning,
    stacklevel=2,
)