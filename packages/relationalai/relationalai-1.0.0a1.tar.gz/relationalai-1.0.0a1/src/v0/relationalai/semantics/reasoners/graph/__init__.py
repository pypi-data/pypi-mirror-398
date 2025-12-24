"""
RelationalAI Graph Library
"""

__version__ = "0.0.0"

import warnings
from v0.relationalai.docutils import ProductStage
from .core import Graph

# Mark this package's docstrings for inclusion
# in automatically generated web documentation.
__include_in_docs__ = True
__rai_product_stage__ = ProductStage.EARLY_ACCESS

# Warn on import that this package is at an early stage of development,
# intended for internal consumers only, and ask those internal consumers
# to contact the symbolic reasoning team such that we can track usage,
# get feedback, and help folks through breaking changes.
warnings.warn(
    (
        "\n\nThis library is still in early stages of development and is intended "
        "for internal use only. Among other considerations, interfaces will change, "
        "and performance is appropriate only for exploring small graphs. Please "
        "see this package's README for additional information.\n\n"
        "If you are an internal user seeing this, please also contact "
        "the symbolic reasoning team such that we can track usage, get "
        "feedback, and help you through breaking changes.\n"
    ),
    FutureWarning,
    stacklevel=2
)

# Finally make this package's core functionality publicly available.
__all__ = [
    "Graph",
]
