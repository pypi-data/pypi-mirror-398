from dataclasses import dataclass, field, fields, is_dataclass
from functools import lru_cache
from typing import Tuple, Any

def is_dataclass_instance(obj) -> bool:
    """Checks if the object is a dataclass instance, excluding the class itself."""
    return is_dataclass(obj) and not isinstance(obj, type)

def print_tree(node, field_name=None, indent=0, hide_fields=[], seen=set()):
    """Recursively print a dataclass tree structure.

    Args:
        node: The dataclass instance or value to print.
        field_name: Optional name of the field (for nested calls).
        indent: Current indentation level.
        hide_fields: List of field names to hide in the output."""
    if id(node) in seen:
        _indent_print(indent, "<recursion>", field_name)
        return
    seen.add(id(node))
    if is_dataclass_instance(node):
        _indent_print(indent, f"{node.__class__.__name__}:", field_name)
        next = indent + 2
        for field in fields(node):
            if field.name not in hide_fields:
                print_tree(getattr(node, field.name), field.name, next, hide_fields)
    elif isinstance(node, list) or isinstance(node, tuple):
        # just ignore sequences that are empty
        if node:
            _indent_print(indent, f"[", field_name)
            next = indent + 2
            for item in node:
                print_tree(item, None, next, hide_fields)
            _indent_print(indent, f"]")
    else:
        _indent_print(indent, str(node), field_name)


def _indent_print(indent, value, field_name=None):
    if field_name:
        print(" " * indent + f"{field_name}: {value}")
    else:
        print(" " * indent + value)
