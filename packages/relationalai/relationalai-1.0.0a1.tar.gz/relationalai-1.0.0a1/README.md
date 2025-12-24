# PyRel

This repository contains the source code for PyRel, the Python library for RelationalAI.

## Documentation

The documentation for PyRel can be found at https://private.relational.ai/early-access/pyrel.

## Development

### Local

```bash
make install
make sync
```

### Docstrings

API reference documentation is generated from docstrings in the code.
Please ensure that all public modules, attributes, functions, and classes, and class methods have docstrings formatted according to the [NumPy docstring standard](https://numpydoc.readthedocs.io/en/latest/format.html).

#### Docstring Templates

To help maintain consistency in docstring formatting, you can use the following templates for common constructs:

**Modules:**

Add a short description of the module's purpose to the top of each module file above the imports, and include the `__include_in_docs__` attribute set to `True`.

```python
"""
The `<module_name>` module provides `<brief_description>`.
"""
import ...

__include_in_docs__ = True
```

**Module Attributes:**

Add docstrings to module-level attributes directly below their definitions:

```python
THE_MEANING: int = 42
"""The meaning of life, the universe, and everything."""
```

**Functions:**

Import the `include_in_docs` decorator from `util.docutils` and apply it to the public function.
Then add a docstring with a brief description, parameters, return value, and one or two usage examples.

> [!IMPORTANT]
> Functions must be fully typed with type hints for all public parameters and return values.

```python
from util.docutils import include_in_docs

@include_in_docs
def add(a: int, b: int) -> int:
    """Add two integers.

    Parameters
    ----------
    a : int
        The first integer to add.
    b : int
        The second integer to add.

    Returns
    -------
    int
        The sum of the two integers.

    Examples
    --------

    >>> add(2, 3)
    5
    >>> add(-1, 1)
    0
    """
    return a + b
```

**Classes:**

Import the `include_in_docs` decorator from `util.docutils` and apply it to the public class and its public methods.
Add a docstring to the class with a brief description, parameters for the constructor, and one or two usage examples.
Add docstrings to each public method with a brief description, parameters, return value, and one or two usage examples.

> [!NOTE]
> You do not need to add a docstring to the `__init__` method; include constructor parameters in the class docstring instead.

> [!NOTE]
> Methods are documented just like functions. You do not need to document the `self` parameter in methods.

```python
from util.docutils import include_in_docs

@include_in_docs
class Calculator:
    """A simple calculator class for basic arithmetic operations.

    Parameters
    ----------
    name : str
        The name of the calculator.

    Examples
    --------

    >>> calc = Calculator("MyCalc")
    >>> calc.add(2, 3)
    5
    """
    def __init__(self, name: str) -> None:
        self.name = name

    @include_in_docs
    def add(self, a: int, b: int) -> int:
        """Add two integers.

        Parameters
        ----------
        a : int
            The first integer to add.
        b : int
            The second integer to add.

        Returns
        -------
        int
            The sum of the two integers.

        Examples
        --------

        >>> calc.add(2, 3)
        5
        >>> calc.add(-1, 1)
        0
        """
        return a + b
```

#### Previewing Documentation Changes

When you open a pull request that modifies docstrings, a preview of the updated documentation will be automatically built and deployed to a temporary URL.
To view the preview, look for a comment from the "Docs Preview" GitHub Action in your pull request.
The comment will contain a link to the preview site where you can review the changes.
Open the link and navigate to the `/api/python/` section and use the left-hand sidebar to find the updated documentation for the modified modules, classes, functions, or attributes.

The API docs are organized by module, so you can easily locate the relevant sections.
For example, if you modified the `relationalai.semantics.std.string` module, the docstring will can be found at:

```
https://<preview-url>/api/python/semantics/std/strings
```
