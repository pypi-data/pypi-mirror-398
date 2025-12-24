from typing import Any, TypeVar
from typing import Optional

T = TypeVar('T')
def include_in_docs(obj: T) -> T:
    """Marks an object for inclusion in documentation.

    Parameters
    ----------
    obj : Any
        The object to mark for inclusion in documentation.

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
    >>>     @include_in_docs
    >>>     def bark(self):
    >>>         return "Woof!"

    To mark a module for inclusion in the documentation, set the
    `__include_in_docs__` attribute to True in the module itself.
    You do not need to use this function for modules.

    For attributes, module and class-level attributes, simply provide
    a docstring and they will be included in the documentation. There is
    no need to use this function for attributes.
    """
    setattr(obj, "__include_in_docs__", True)
    return obj
