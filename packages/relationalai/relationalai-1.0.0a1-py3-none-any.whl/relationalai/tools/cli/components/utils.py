"""Utility functions for CLI controls."""

from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .progress_reader import Task


def normalize_tasks(task_or_tasks: "Task | Iterable[Task]") -> list["Task"]:
    """Convert a single task or iterable of tasks to a list.

    This utility function normalizes task inputs, handling both single Task
    objects and iterables of Task objects. Used by TaskRegistry and ProgressReader
    to normalize task inputs consistently.

    Args:
        task_or_tasks: A Task object or iterable of Task objects

    Returns:
        List of Task objects (empty list if input is empty)

    Raises:
        TypeError: If input is not a Task and not iterable, or if iterable contains non-Task items

    Example:
        >>> task = Task(text="Example")
        >>> normalize_tasks(task)
        [Task(text="Example", ...)]
        >>> normalize_tasks([task, task])
        [Task(text="Example", ...), Task(text="Example", ...)]
    """
    # Import here to avoid circular dependency
    from .progress_reader import Task

    if isinstance(task_or_tasks, Task):
        return [task_or_tasks]

    # Try to convert to list, handling non-iterable inputs
    try:
        tasks = list(task_or_tasks)
    except TypeError:
        raise TypeError(
            f"Expected Task or Iterable[Task], got {type(task_or_tasks).__name__}"
        ) from None

    if not tasks:
        return []

    # Validate all items are Task instances
    for item in tasks:
        if not isinstance(item, Task):
            raise TypeError(
                f"Expected Task instances, got {type(item).__name__}"
            )

    return tasks

