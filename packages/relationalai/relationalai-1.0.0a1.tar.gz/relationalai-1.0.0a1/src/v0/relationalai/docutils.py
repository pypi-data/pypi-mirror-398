from enum import Enum
from typing import Any
from typing import Optional


class ProductStage(Enum):
    """Product stages for features and APIs."""
    GA = "generally available"
    PREVIEW = "public preview"
    EARLY_ACCESS = "early access"


def include_in_docs(
    obj: Any,
    stage: Optional[ProductStage] = None
) -> Any:
    """Marks an object for inclusion in documentation.

    Parameters
    ----------
    obj : Any
        The object to mark for inclusion in documentation.
    stage : ProductStage or None
        The stage of the product for which the object is included in documentation.
        Defaults to None, which means it inherits the product stage of its parent.

    Examples
    --------
    Use as a decorator to mark a function for inclusion in documentation:

    >>> @include_in_docs
    >>> def double(x: int):
    >>>     return x * 2

    Use as a decorator to mark classes and methods for inclusion in documentation:

    >>> @include_in_docs
    >>> class Dog:
    >>>     def __init__(self, name: str):
    >>>         self.name = name
    >>>     @include_in_docs(ProductStage.PREVIEW)
    >>>     def bark(self):
    >>>         return "Woof!"

    Use as a function to mark other objects like constants or modules for inclusion in documentation:

    >>> from my_package import my_module
    >>> include_in_docs(my_module, ProductStage.EARLY_ACCESS)
    >>> MY_CONSTANT = include_in_docs(42)
    """
    setattr(obj, "__include_in_docs__", True)
    setattr(obj, "__rai_product_stage__", stage)
    return obj
