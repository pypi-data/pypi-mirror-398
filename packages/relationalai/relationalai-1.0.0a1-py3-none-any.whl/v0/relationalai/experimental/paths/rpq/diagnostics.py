from v0.relationalai.errors import RAIWarning, RAIException

# -----------------------------------------------------------------------------------------
# All User-facing diagnostic messages: Warnings and Errors
# -----------------------------------------------------------------------------------------

class PathfinderParameterWarning(RAIWarning):
    def __init__(self, message: str):
        super().__init__(message)

class PathfinderSizeWarning(RAIWarning):
    def __init__(self, pattern, prune_states_only: bool):
        from .rpq import RPQ
        assert isinstance(pattern, RPQ)

        message = f"WARNING: RPQ pattern is prohibitively large {len(pattern)} >= 50"
        if prune_states_only:
            message += "\nSkipping transitions pruning"
            message += "\nUse 'force_transition_pruning=True' to force transition pruning"
        super().__init__(message)

class PathfinderNonDeterminismWarning(RAIWarning):
    def __init__(self, pattern, a, prune_states_only: bool):
        from .rpq import RPQ
        from .automaton import Automaton
        assert isinstance(pattern, RPQ)
        assert isinstance(a, Automaton)

        message = "WARNING: RPQ pattern is non-deterministic\n"
        if prune_states_only:
            message += "Using 'force_transition_pruning=True' may solve this issue\n"
        message += str(pattern)
        message += "\n"
        for reason in a.determinism_report():
            message += " *" + reason + '\n'
        message += "Pathfinder may return duplicate results"
        super().__init__(message)

class PathfinderUngroundedPatternError(RAIException):
    def __init__(self, pattern):
        from .rpq import RPQ
        assert isinstance(pattern, RPQ)

        message = "ERROR: Input RPQ pattern is ungrounded\n"
        message += "Pattern potentially admits an infinite number of single-node paths\n"
        message += str(pattern)
        super().__init__(message)

class PathfinderVoidPatternError(RAIException):
    def __init__(self, pattern):
        from .rpq import RPQ
        assert isinstance(pattern, RPQ)

        message = "ERROR: Input RPQ pattern is void (admits no paths)\n"
        message += str(pattern)
        super().__init__(message)
