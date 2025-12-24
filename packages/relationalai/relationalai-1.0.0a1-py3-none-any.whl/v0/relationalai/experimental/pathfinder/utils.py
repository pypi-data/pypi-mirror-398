from typing import Callable
from v0.relationalai.dsl import get_graph, Graph
# -----------------------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------------------

#
# Get the string representation of a lambda function (with moderate effort).
#
def get_lambda_str(f: Callable) -> str:
    try:
        if f.__name__ == '<lambda>':
            return f"λ{','.join(f.__code__.co_varnames)}:... @{hex(id(f))}"
        else:
            return f"{f.__name__}({','.join(f.__code__.co_varnames)}):... @{hex(id(f))}"
    except Exception as _:
        return str(f)

#
# Returns the model to use for emitting the logic defining paths and calling the Pathfinder.
#
def get_model(options) -> Graph:
    if options['model'] is not None:
        return options['model']
    else:
        return get_graph()
