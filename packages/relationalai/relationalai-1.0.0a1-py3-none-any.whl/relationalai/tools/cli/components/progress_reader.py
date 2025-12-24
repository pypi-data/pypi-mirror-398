#pyright: reportPrivateImportUsage=false
from __future__ import annotations

# Standard library imports
import re
import threading
import time
import textwrap
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, overload
import uuid


if TYPE_CHECKING:
    from rich.console import ConsoleOptions, RenderableType
    from rich.progress import Progress, TaskID

# Third-party imports
import rich
from rich.console import Console, Group
from rich.live import Live
from rich.text import Text

# Local imports
from relationalai.util.format import format_duration
from .utils import normalize_tasks


#--------------------------------------------------
# Constants
#--------------------------------------------------

# Display symbols
CHECK_MARK = "✓"
FAIL_ICON = "ⓧ"

# Spinner animation frames for running tasks
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# Terminal display constants
DEFAULT_TERMINAL_WIDTH = 80

# Animation constants
ANIMATION_INTERVAL = 0.1  # Seconds between animation frame updates (~10 fps)
REFRESH_RATE = 10  # Rich Live refresh rate (frames per second)
MIN_DETAIL_WIDTH = 20  # Minimum width for task details text wrapping


# ============================================================================
# Task Status Enum
# ============================================================================

class TaskStatus(str, Enum):
    """Enumeration of valid task statuses.

    Using str as the base class allows the enum values to be used as strings
    in comparisons and string operations, while providing type safety and
    preventing typos.
    """
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ============================================================================
# Task Class
# ============================================================================

class _RenderableWrapper:
    """Wrapper to make a callable renderable for Rich's Live.

    Rich's ``Live`` container expects a renderable object that implements
    ``__rich_console__`` and returns fresh content each time the live display
    refreshes. ``ProgressReader`` generates its layout on the fly via a
    callable, so we wrap that callable in this helper to bridge the protocol
    gap: ``Live`` sees a renderable, but internally we still recompute the
    layout lazily on every refresh.
    """

    def __init__(self, callable_fn: Callable[[], "RenderableType"]) -> None:
        """Initialize the renderable wrapper.

        Args:
            callable_fn: A callable that returns a Rich renderable object
        """
        self._callable = callable_fn

    def __rich_console__(
        self, console: Console, options: "ConsoleOptions"
    ) -> Iterator["RenderableType"]:
        """Rich protocol - yield the result of calling the callable."""
        result = self._callable()
        # Result should always be a Group, which implements __rich_console__
        yield from result.__rich_console__(console, options)

@dataclass(frozen=False)
class Task:
    """Represents a single task with its status and optional error.

    Note: Task objects are mutable only through ProgressReader APIs. When using
    ProgressReader from multiple threads, avoid modifying Task objects directly
    from different threads concurrently. Use ProgressReader helpers
    (complete_task, fail_task, update_task_status, update_task_details, etc.) for
    thread-safe updates and to ensure the UI refreshes."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    details: str = ""
    status: TaskStatus = field(default=TaskStatus.RUNNING)
    error: str = ""
    _allow_direct_mutation: bool = field(default=True, init=False, repr=False, compare=False)

    _PROTECTED_FIELDS = {"status", "details", "error"}

    def __setattr__(self, name: str, value: object) -> None:
        if name in Task._PROTECTED_FIELDS:
            try:
                allow = object.__getattribute__(self, "_allow_direct_mutation")
            except AttributeError:
                allow = True
            if not allow:
                raise AttributeError(
                    "Task attributes are managed by ProgressReader. Use its public API to make changes."
                )
        object.__setattr__(self, name, value)

    def __post_init__(self):
        """Validate status values and ensure task_id."""
        # Validate that id is a non-empty string if explicitly provided
        # (If not provided, default_factory generates a UUID automatically)
        if not isinstance(self.id, str):
            raise ValueError(
                f"Task id must be a string, got {type(self.id).__name__}: {self.id!r}. "
                "Either provide a non-empty string id or omit it to auto-generate one."
            )
        if not self.id:
            raise ValueError(
                f"Task id cannot be empty. Got: {self.id!r}. "
                "Either provide a non-empty string id or omit it to auto-generate one."
            )
        # Validate status is a TaskStatus enum value
        if not isinstance(self.status, TaskStatus):
            # Allow string values for backward compatibility, but convert to enum
            try:
                self.status = TaskStatus(self.status)
            except ValueError:
                raise ValueError(
                    f"Invalid status: {self.status}. Must be one of: "
                    f"{', '.join(s.value for s in TaskStatus)}"
                )
        object.__setattr__(self, "_allow_direct_mutation", False)

    def __hash__(self) -> int:
        """Make Task hashable for use in sets.

        Uses task ID for hashing, ensuring that tasks with the same ID
        have the same hash value (required for consistent behavior in sets/dicts).
        """
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Equality comparison based on task ID.

        Two Task objects are considered equal if they have the same ID.
        This is more reliable than identity-based comparison since Task IDs
        are unique identifiers within a registry.
        """
        if not isinstance(other, Task):
            return False
        return self.id == other.id

@dataclass
class _TimingTracker:
    enabled: bool
    task_start_times: dict[Task, float] = field(default_factory=dict)
    task_end_times: dict[Task, float] = field(default_factory=dict)
    run_start: float | None = None
    run_end: float | None = None
    summary_printed: bool = False

    def track_initial_tasks(self, tasks: Iterable[Task]) -> None:
        if not self.enabled:
            return
        now = time.time()
        for task in tasks:
            self.task_start_times.setdefault(task, now)
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                self.task_end_times.setdefault(task, now)

    def track_start(self, task: Task) -> None:
        if not self.enabled:
            return
        self.task_start_times.setdefault(task, time.time())

    def track_end(self, task: Task) -> None:
        if not self.enabled:
            return
        self.task_end_times.setdefault(task, time.time())

    def clear_end(self, task: Task) -> None:
        if not self.enabled:
            return
        self.task_end_times.pop(task, None)

    def forget(self, task: Task) -> None:
        if not self.enabled:
            return
        self.task_start_times.pop(task, None)
        self.task_end_times.pop(task, None)

    def start_run(self) -> None:
        if not self.enabled:
            return
        self.run_start = time.time()
        self.run_end = None
        self.summary_printed = False

    def stop_run(self) -> None:
        if not self.enabled:
            return
        self.run_end = time.time()

    def format_duration(self, task: Task) -> str | None:
        if not self.enabled:
            return None
        start = self.task_start_times.get(task)
        if start is None:
            return None
        end = self.task_end_times.get(task)
        if end is None:
            if task.status == TaskStatus.RUNNING:
                return None
            end = time.time()
        duration = max(0.0, end - start)
        return format_duration(duration)

    def consume_elapsed_runtime(self) -> str | None:
        if not self.enabled or self.summary_printed:
            return None
        start_candidates: list[float] = []
        if self.run_start is not None:
            start_candidates.append(self.run_start)
        start_candidates.extend(self.task_start_times.values())
        if not start_candidates:
            return None
        start_time = min(start_candidates)

        end_candidates: list[float] = []
        if self.run_end is not None:
            end_candidates.append(self.run_end)
        end_candidates.extend(self.task_end_times.values())
        if not end_candidates:
            end_candidates.append(time.time())

        elapsed = max(0.0, max(end_candidates) - start_time)
        self.summary_printed = True
        return format_duration(elapsed)

# ============================================================================
# TaskRegistry - Task Storage and Lookup
# ============================================================================

class TaskRegistry:
    """Thread-safe registry for task storage, ID lookups, and basic operations.

    This class manages the core data structure for tasks, providing:
    - Task storage and indexing
    - ID-based lookups
    - Add/remove operations
    - Completed task tracking

    All operations are thread-safe using an RLock.
    """

    def __init__(self, tasks: Iterable[Task] | None = None):
        """Initialize the task registry.

        Args:
            tasks: Optional iterable of Task objects to seed the registry with
        """
        self._lock = threading.RLock()
        self._tasks: list[Task] = []
        self._tasks_by_id: dict[str, Task] = {}
        self._completed_tasks: set[Task] = set()

        # Initialize with provided tasks
        if tasks is not None:
            for task in tasks:
                self._add_task_internal(task)

    def _add_task_internal(self, task: Task) -> None:
        """Internal method to add a task without lock (caller must hold lock)."""
        if not isinstance(task, Task):
            raise TypeError("TaskRegistry expects Task instances")

        # Assign and validate task ID
        task_id = task.id
        existing = self._tasks_by_id.get(task_id)
        if existing is not None and existing is not task:
            raise ValueError(f"Duplicate task_id detected: {task_id}")

        self._tasks.append(task)
        self._tasks_by_id[task_id] = task

    def add_task(self, task: Task | Iterable[Task]) -> None:
        """Add one or more tasks to the registry.

        Args:
            task: A Task object or iterable of Task objects to add
        """
        tasks_to_add = normalize_tasks(task)
        if not tasks_to_add:
            return

        with self._lock:
            for item in tasks_to_add:
                self._add_task_internal(item)

    def remove_task(self, task: Task | Iterable[Task]) -> bool:
        """Remove one or more tasks from the registry.

        Args:
            task: A Task object or iterable of Task objects to remove

        Returns:
            True if any tasks were removed, False if no tasks were removed.
            Note: If a task is not in the registry, it is silently ignored
            (idempotent operation).
        """
        tasks = normalize_tasks(task)
        if not tasks:
            return False

        with self._lock:
            removed = False
            for t in tasks:
                try:
                    self._tasks.remove(t)
                    self._completed_tasks.discard(t)
                    if t.id is not None:
                        self._tasks_by_id.pop(t.id, None)
                    removed = True
                except ValueError:
                    pass  # Task not found, continue
            return removed

    def get_task_by_id(self, task_id: str) -> Task | None:
        """Get a task by its ID.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            The Task object if found, None otherwise
        """
        with self._lock:
            return self._tasks_by_id.get(task_id)

    def get_task_index_by_id(self, task_id: str) -> int | None:
        """Get the index of a task by its ID.

        Args:
            task_id: The ID of the task to find

        Returns:
            The index of the task if found, None otherwise
        """
        with self._lock:
            task = self._tasks_by_id.get(task_id)
            if task is None:
                return None
            try:
                return self._tasks.index(task)
            except ValueError:
                return None

    def find_task(self, text: str) -> Task | None:
        """Find a task by its text.

        Args:
            text: The text of the task to find

        Returns:
            The Task object if found, None otherwise
        """
        with self._lock:
            for task in self._tasks:
                if task.text == text:
                    return task
        return None

    def get_task_index(self, task: Task) -> int | None:
        """Get the index of a task.

        Args:
            task: The Task object to find

        Returns:
            The index of the task if found, None otherwise
        """
        with self._lock:
            try:
                return self._tasks.index(task)
            except ValueError:
                return None

    @property
    def tasks(self) -> list[Task]:
        """Get a read-only copy of the tasks list."""
        with self._lock:
            return list(self._tasks)

    @property
    def completed_tasks(self) -> set[Task]:
        """Get a copy of the completed tasks set."""
        with self._lock:
            return set(self._completed_tasks)

    def mark_completed(self, task: Task) -> bool:
        """Mark a task as completed.

        Args:
            task: The task to mark as completed

        Returns:
            True if the task was newly marked as completed, False if already completed
        """
        with self._lock:
            if task not in self._completed_tasks:
                self._completed_tasks.add(task)
                return True
            return False

    def _unmark_completed(self, task: Task) -> None:
        """Remove a task from the completed set.

        Internal method used when a task transitions back to RUNNING status.

        Args:
            task: The task to remove from completed set
        """
        with self._lock:
            self._completed_tasks.discard(task)

    def __len__(self) -> int:
        """Return the number of tasks."""
        with self._lock:
            return len(self._tasks)

    def __contains__(self, item: object) -> bool:
        """Check if a task is in the registry."""
        with self._lock:
            return item in self._tasks


# ============================================================================
# ProgressReader - Progress Display and Task Orchestration
# ============================================================================

class ProgressReader:
    """A progress component that reads a list of tasks with progress tracking.

    Shows a progress bar and updates task status as tasks are processed.
    Can be used as a context manager or with manual start/stop methods.

    Example (context manager):
        tasks = [
            Task(text="Task 1"),
            Task(text="Task 2"),
        ]

        with ProgressReader(tasks) as reader:
            for task in reader:
                # Process task...
                reader.complete_task(task)  # Mark as done

    Example (manual control):
        reader = ProgressReader(tasks)
        reader.start()
        for task in reader:
            process_task(task)
            reader.complete_task(task)
        reader.stop()

    Note:
        For multi-threaded usage, prefer the public API methods
        (e.g., ``complete_task``, ``fail_task``, ``update_task_status``)
        instead of mutating ``Task`` attributes directly. This ensures the
        UI stays in sync and timing information remains accurate.
    """

    def __init__(
        self,
        tasks: Iterable[Task] | None = None,
        description: str = "Processing tasks",
        show_task_count: bool = True,
        show_progress_bar: bool = True,
        show_durations: bool = True,
        max_visible_tasks: int | None = 20,
        show_run_log: bool = False,
        log_file_folder: str | Path | None = "logs",
    ):
        """Initialize the ProgressReader.

        Args:
            tasks: Optional iterable of Task objects to seed the reader with
            description: Description to show in the progress bar
            show_task_count: Whether to show the "x/y" task count display (default: True)
            show_progress_bar: Whether to show the progress bar (default: True)
            show_durations: Whether to display per-task and summary durations (default: True)
            max_visible_tasks: Maximum number of active tasks (``RUNNING`` or ``FAILED``) to render at once.
                Completed tasks are omitted from the live view. Set to ``None`` to show every task.
            show_run_log: Whether to print a full task log to the console when the reader stops.
                Useful for archival/logging scenarios. Defaults to False.
            log_file_folder: Folder path where log files will be saved. A log file will be created with
                a timestamped filename (format: ``YYYYMMDD_HHMMSS.log``). Defaults to
                ``logs`` (saves in a visible folder relative to the current working directory, following
                conventions used by dbt and other major platforms). Set to ``None`` to disable file logging.
        """
        # --------------------------------------------------------------------
        # Configuration
        # --------------------------------------------------------------------
        self.description = description
        self.show_task_count = show_task_count
        self.show_progress_bar = show_progress_bar
        self.show_durations = show_durations
        self.show_run_log = show_run_log
        if max_visible_tasks is not None and max_visible_tasks <= 0:
            raise ValueError("max_visible_tasks must be a positive integer or None")
        self.max_visible_tasks = max_visible_tasks
        self.log_file_folder = Path(log_file_folder) if log_file_folder is not None else None

        # --------------------------------------------------------------------
        # Task Registry - Core data management
        # --------------------------------------------------------------------
        self._registry = TaskRegistry(tasks)

        # --------------------------------------------------------------------
        # Timing Information
        # --------------------------------------------------------------------
        self._timing = _TimingTracker(show_durations)
        if tasks is not None:
            self._timing.track_initial_tasks(tasks)

        # --------------------------------------------------------------------
        # Display Components (Rich library)
        # --------------------------------------------------------------------
        self.console = Console()
        self._progress: "Progress | None" = None
        self._task_id: "TaskID | None" = None
        self._live: Live | None = None
        self._started = False

        # --------------------------------------------------------------------
        # Animation
        # --------------------------------------------------------------------
        self._spinner_frame_index = 0  # Current spinner animation frame
        self._animation_thread: threading.Thread | None = None
        self._stop_animation = threading.Event()

        # --------------------------------------------------------------------
        # Thread Safety
        # --------------------------------------------------------------------
        self._lock = threading.RLock()  # Reentrant lock for thread-safe operations

    # ------------------------------------------------------------------------
    # Task Access (delegates to registry)
    # ------------------------------------------------------------------------

    @property
    def tasks(self) -> list[Task]:
        """Get a read-only copy of the tasks list."""
        return self._registry.tasks

    # ------------------------------------------------------------------------
    # Display Helpers
    # ------------------------------------------------------------------------

    def _get_progress_and_id(self) -> tuple["Progress", "TaskID"] | None:
        """Get progress and task_id if active, None otherwise. Helps with type narrowing."""
        if self._started and self._progress is not None and self._task_id is not None:
            return (self._progress, self._task_id)
        return None

    # ------------------------------------------------------------------------
    # Task Utilities
    # ------------------------------------------------------------------------

    def _ensure_task_list(self, task_or_tasks: Task | Iterable[Task]) -> list[Task]:
        """Convert task or iterable to list of tasks, with validation.

        This is a wrapper around the shared normalize_tasks utility for consistency.
        """
        return normalize_tasks(task_or_tasks)

    # ------------------------------------------------------------------------
    # Text Formatting
    # ------------------------------------------------------------------------

    @staticmethod
    def _wrap_detail_lines(details: str, max_width: int) -> list[str]:
        if not details:
            return []

        raw_lines = details.splitlines() or [details]
        if details.endswith("\n"):
            raw_lines.append("")

        wrapped: list[str] = []
        for raw in raw_lines:
            if raw:
                wrapped.extend(
                    textwrap.wrap(
                        raw,
                        width=max_width,
                        replace_whitespace=False,
                        drop_whitespace=False,
                    )
                    or [""]
                )
            else:
                wrapped.append("")
        return wrapped

    def _render_task_row(
        self,
        task: Task,
        spinner_char: str,
        detail_indent: str,
        max_detail_width: int,
    ) -> Text:
        line = Text("  ")
        detail_style = "dim"

        if task.status == TaskStatus.RUNNING:
            line.append(f"{spinner_char} ", style="dim")
            line.append(task.text, style="yellow dim")
        elif task.status == TaskStatus.COMPLETED:
            line.append(f"{CHECK_MARK} ")
            line.append(task.text, style="white")
            duration_text = self._timing.format_duration(task)
            if duration_text:
                line.append(f" ({duration_text})")
        elif task.status == TaskStatus.FAILED:
            error_msg = f" ({task.error})" if task.error else ""
            line = Text(f"  {FAIL_ICON} {task.text}{error_msg}", style="red")
            duration_text = self._timing.format_duration(task)
            if duration_text:
                line.append(f" ({duration_text})", style="red")
        else:
            line.append(task.text)

        for detail_line in self._wrap_detail_lines(task.details, max_detail_width):
            line.append("\n")
            line.append(detail_indent)
            if detail_line:
                line.append(detail_line, style=detail_style)

        return line

    # ------------------------------------------------------------------------
    # Task Mutation & Status Management
    # ------------------------------------------------------------------------

    def _validate_and_convert_status(self, status: TaskStatus | str) -> TaskStatus:
        """Validate and convert status to TaskStatus enum.

        Args:
            status: Status value (TaskStatus enum or string)

        Returns:
            TaskStatus enum value

        Raises:
            ValueError: If status is invalid
        """
        if isinstance(status, str):
            # Convert string to enum (for backward compatibility)
            try:
                return TaskStatus(status)
            except ValueError:
                raise ValueError(
                    f"Invalid status: {status!r}. Must be one of: "
                    f"{', '.join(s.value for s in TaskStatus)}"
                )
        elif not isinstance(status, TaskStatus):
            # Reject invalid types (e.g., int, None, etc.)
            raise ValueError(
                f"Invalid status type: {type(status).__name__}. "
                f"Expected TaskStatus enum or string, got: {status!r}"
            )
        return status

    def _update_task_attributes(
        self, task: Task, status: TaskStatus | None, error: str | None, details: str | None
    ) -> tuple[bool, bool]:
        """Update task attributes (status, error, details) and track timing.

        Args:
            task: The task to update
            status: New status to set (validated TaskStatus enum)
            error: New error message to set
            details: New details text to set

        Returns:
            Tuple of (should_refresh_totals, should_update_description)
        """
        should_refresh_totals = False
        should_update_description = False

        if status is not None:
            self._timing.track_start(task)
            object.__setattr__(task, "status", status)
            if status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                self._timing.track_end(task)
            elif status == TaskStatus.RUNNING:
                # Remove from completed set if transitioning back to RUNNING
                was_completed = task in self._registry._completed_tasks
                self._registry._unmark_completed(task)
                if was_completed:
                    should_refresh_totals = True
                self._timing.clear_end(task)
            should_update_description = True

        if error is not None:
            object.__setattr__(task, "error", error)
            should_update_description = True

        if details is not None:
            object.__setattr__(task, "details", details)
            should_update_description = True

        return should_refresh_totals, should_update_description

    def _mutate_task(
        self,
        task: Task,
        *,
        status: TaskStatus | str | None = None,
        error: str | None = None,
        details: str | None = None,
        advance: bool = True,
    ) -> bool:
        """Mutate a task's attributes (status, error, details).

        Args:
            task: The task to mutate
            status: New status to set
            error: New error message to set
            details: New details text to set
            advance: Whether to advance progress bar

        Returns:
            True if the task was found and updated, False if the task was not in registry
        """
        if status is None and error is None and details is None:
            return True  # Nothing to do, but task exists

        # Check if task exists in registry
        with self._registry._lock:
            if task not in self._registry._tasks:
                return False  # Task not in registry

            # Validate and convert status if provided
            validated_status = None
            if status is not None:
                validated_status = self._validate_and_convert_status(status)

            # Update task attributes
            should_refresh_totals, should_update_description = self._update_task_attributes(
                task, validated_status, error, details
            )

        # Handle status-specific side effects
        if validated_status == TaskStatus.COMPLETED:
            self._mark_task_completed(task, advance=advance)
        elif validated_status == TaskStatus.FAILED:
            self._mark_task_failed(task, advance=advance)

        if should_refresh_totals:
            self.update_progress_total()

        if should_update_description:
            self._update_progress(description=f"[bright_cyan]{task.text}[/bright_cyan]")

        return True  # Task was found and updated successfully

    # ------------------------------------------------------------------------
    # Progress Bar Management
    # ------------------------------------------------------------------------

    def _update_progress(self, advance: bool = False, **kwargs) -> None:
        """Update the progress bar if active.

        Args:
            advance: If True, advance the progress by 1
            **kwargs: Keyword arguments to pass to progress.update()
        """
        with self._lock:
            progress_info = self._get_progress_and_id()
            if progress_info:
                progress, task_id = progress_info
                if advance:
                    progress.advance(task_id)
                if kwargs:
                    progress.update(task_id, **kwargs)

    # ------------------------------------------------------------------------
    # Output & Logging
    # ------------------------------------------------------------------------

    def _print_elapsed_runtime(self, log_file_path: Path | None = None) -> None:
        runtime = self._timing.consume_elapsed_runtime()
        if runtime:
            rich.print()
            if log_file_path is not None:
                rich.print(f"Elapsed runtime: [cyan]{runtime}[/cyan], logs: [cyan]{log_file_path}[/cyan]")
            else:
                rich.print(f"Elapsed runtime: [cyan]{runtime}[/cyan]")

    def _print_run_log(self) -> Path | None:
        """Print run log and save to file if configured.

        Returns:
            Path to the saved log file if file logging was successful, None otherwise.
        """
        if not self.show_run_log and self.log_file_folder is None:
            return None

        with self._registry._lock:
            tasks = list(self._registry._tasks)

        if not tasks:
            return None

        detail_indent = "    "
        console_width = self.console.size.width if self.console else DEFAULT_TERMINAL_WIDTH
        max_detail_width = max(console_width - len(detail_indent) - 2, MIN_DETAIL_WIDTH)

        # Prepare log content
        log_lines: list[str] = []
        if self.show_run_log:
            rich.print()
            rich.print("[bold]Task log[/bold]")

        log_lines.append("Task log")
        log_lines.append("=" * 80)

        # Create file console once for converting Rich renderables to plain text
        # Use no_color=True and StringIO to strip ANSI escape codes from file output
        file_buffer = StringIO() if self.log_file_folder is not None else None
        file_console = Console(file=file_buffer, width=console_width, legacy_windows=False, no_color=True) if file_buffer is not None else None

        for task in tasks:
            row = self._render_task_row(task, " ", detail_indent, max_detail_width)
            if self.show_run_log:
                self.console.print(row)
            # Convert Rich renderable to plain text for file logging
            if file_console is not None and file_buffer is not None:
                file_console.print(row)
                # Get the text and strip any remaining ANSI escape codes as a safety measure
                text = file_buffer.getvalue()
                file_buffer.seek(0)
                file_buffer.truncate(0)
                # Remove ANSI escape codes (pattern matches \x1b[...m sequences)
                text = re.sub(r'\x1b\[[0-9;]*m', '', text)
                log_lines.append(text.rstrip('\n'))

        # Save to file if log_file_folder is provided
        if self.log_file_folder is not None:
            return self._save_log_to_file(log_lines)

        return None

    def _save_log_to_file(self, log_lines: list[str]) -> Path | None:
        """Save log content to a timestamped file.

        Args:
            log_lines: List of log lines to write to file.

        Returns:
            Path to the saved log file if successful, None otherwise.
        """
        if self.log_file_folder is None:
            return None

        try:
            # Create directory if it doesn't exist
            self.log_file_folder.mkdir(parents=True, exist_ok=True)

            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"{timestamp}.log"
            log_file_path = self.log_file_folder / log_filename

            # Write log content to file
            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(log_lines))
                f.write("\n")

            return log_file_path
        except Exception as e:
            # Don't fail silently, but also don't break the main flow
            rich.print(f"[red]Warning: Failed to save log file: {e}[/red]")
            return None

    def _create_progress_components(self) -> tuple["Progress", "TaskID", Live]:
        """Create Rich progress components (Progress, TaskID, Live).

        Returns:
            Tuple of (progress, task_id, live) objects

        Raises:
            RuntimeError: If Live fails to start
        """
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

        # Capture values needed for Rich object creation
        total = len(self._registry) if self.show_progress_bar else None
        description = self.description
        show_progress_bar = self.show_progress_bar
        show_task_count = self.show_task_count

        # Always show spinner and description
        columns = [
            SpinnerColumn(style="bright_cyan"),
            TextColumn("[bright_cyan]{task.description}[/bright_cyan]"),
        ]

        # Add progress bar components only if enabled
        if show_progress_bar:
            columns.extend([
                BarColumn(bar_width=None, complete_style="bright_cyan", finished_style="bright_cyan", pulse_style="bright_cyan"),
                TextColumn("[bright_cyan]{task.percentage:>3.0f}%"),
            ])

            # Conditionally add task count display (only relevant with progress bar)
            if show_task_count:
                columns.extend([
                    TextColumn("•"),
                    TextColumn("{task.completed}/{task.total}"),
                ])

        # Create Progress but don't start it - Live will handle rendering
        progress = Progress(*columns, console=self.console, transient=True)

        # Add the main overall progress task
        task_id = progress.add_task(description, total=total)

        # Start Live display - it will render both Progress and tasks
        # Use a wrapper class to ensure Rich recognizes it as renderable
        renderable_wrapper = _RenderableWrapper(lambda: self._render_all())
        live = Live(
            renderable_wrapper,
            console=self.console,
            refresh_per_second=REFRESH_RATE,
            vertical_overflow="crop",
        )

        return progress, task_id, live

    def start(self):
        """Start the progress display."""
        with self._lock:
            if self._started:
                return
            # Set _started early to prevent race condition with concurrent start() calls
            self._started = True

        # Create Rich objects outside lock to minimize lock duration
        progress, task_id, live = self._create_progress_components()

        self._timing.start_run()

        try:
            live.start()
        except Exception as e:
            # If Live fails to start, reset _started flag and clean up
            with self._lock:
                self._started = False
            progress.stop()
            raise RuntimeError(f"Failed to start progress display: {e}") from e

        # Update state while holding lock
        with self._lock:
            self._progress = progress
            self._task_id = task_id
            self._live = live

        # Start animation thread for spinner updates
        self._start_animation()

    def stop(self):
        """Stop the progress display."""
        # Stop animation first
        self._stop_animation_thread()

        with self._lock:
            progress_info = self._get_progress_and_id()
            if progress_info:
                progress, task_id = progress_info
                # Complete the progress bar and clear description
                progress.update(task_id, completed=len(self._registry), description="")
                # Don't call progress.stop() - Live will handle cleanup

            # Stop Live display (this will also clean up Progress)
            if self._live is not None:
                try:
                    self._live.stop()
                except Exception:
                    pass  # Ignore errors during stop
                self._live = None

            self._started = False
            self._timing.stop_run()

        # Print elapsed runtime with log file location combined
        log_file_path = self._print_run_log()
        self._print_elapsed_runtime(log_file_path)

    def __enter__(self) -> "ProgressReader":
        """Enter the context manager and start the progress display."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager and stop the progress display."""
        self.stop()
        return False  # Don't suppress exceptions

    # ------------------------------------------------------------------------
    # Iterator Protocol
    # ------------------------------------------------------------------------

    def __iter__(self) -> Iterator[Task]:
        """Iterate through tasks, updating progress as we go.

        Note: Creates a snapshot of tasks and releases the lock during iteration
        to avoid deadlocks and allow concurrent modifications.
        """
        with self._registry._lock:
            tasks_copy = list(self._registry._tasks)  # Create a snapshot to iterate over

        # Lock is released here to allow concurrent modifications during iteration
        for i, task in enumerate(tasks_copy):
            # Show current task being processed
            self._update_progress(description=f"[bright_cyan]{task.text}[/bright_cyan]")

            yield task

            # Check status and update display (don't advance - iterator handles it)
            self._update_task_status_display(task, advance=False)

            # Advance overall progress (based on iteration, not completion)
            self._update_progress(advance=True)

            # If this is the last task, clear the description
            if i == len(tasks_copy) - 1:
                progress_info = self._get_progress_and_id()
                if progress_info:
                    progress, task_id = progress_info
                    progress.update(task_id, description="")

    # ------------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------------

    def _select_visible_tasks(self, tasks: list[Task]) -> tuple[list[Task], dict[str, int], bool]:
        """Select a subset of active tasks to render and compute hidden task statistics.

        Returns:
            Tuple of (visible_tasks, hidden_counts, all_done)
            - visible_tasks: List of tasks to display
            - hidden_counts: Dict with counts of hidden tasks by status
            - all_done: True if no RUNNING tasks remain (all completed or failed)
        """
        limit = self.max_visible_tasks

        # Single pass: filter active tasks and separate by status
        failed_tasks = []
        non_failed_tasks = []
        running_count = 0

        for task in tasks:
            if task.status == TaskStatus.COMPLETED:
                continue

            if task.status == TaskStatus.FAILED:
                failed_tasks.append(task)
            else:
                non_failed_tasks.append(task)
                if task.status == TaskStatus.RUNNING:
                    running_count += 1

        active_tasks = failed_tasks + non_failed_tasks

        if limit is None or len(active_tasks) <= limit:
            all_done = running_count == 0
            return active_tasks, {"total": 0, "RUNNING": 0, "FAILED": 0}, all_done

        # Calculate remaining slots (limit is guaranteed to be an int here due to early return above)
        remaining_slots = max(limit - len(failed_tasks), 0)

        visible = failed_tasks + non_failed_tasks[:remaining_slots]
        hidden_tasks = non_failed_tasks[remaining_slots:]

        # Count hidden tasks by status and track running tasks
        # Note: All RUNNING tasks are in non_failed_tasks (failed tasks are never RUNNING)
        hidden_running = 0
        for task in hidden_tasks:
            if task.status == TaskStatus.RUNNING:
                hidden_running += 1

        # all_done is True if no RUNNING tasks exist (neither visible nor hidden)
        all_done = running_count == 0

        counts = {
            "total": len(hidden_tasks),
            "RUNNING": hidden_running,
            "FAILED": 0,  # Failed tasks are always visible, so hidden_failed is always 0
        }

        return visible, counts, all_done

    def _render_all(self) -> Group:
        """Render both Progress and task list as a Group for Live display."""
        # Minimize lock time - only grab what we need
        with self._registry._lock:
            tasks = list(self._registry._tasks)
            spinner_char = SPINNER_FRAMES[self._spinner_frame_index]
            progress_info = self._get_progress_and_id()

        # Build task list (outside lock for better performance)
        task_lines = []

        console_width = self.console.size.width if self.console else DEFAULT_TERMINAL_WIDTH
        detail_indent = "    "
        max_detail_width = max(console_width - len(detail_indent) - 2, MIN_DETAIL_WIDTH)

        visible_tasks, hidden_counts, all_done = self._select_visible_tasks(tasks)

        # Build task lines
        for task in visible_tasks:
            task_lines.append(
                self._render_task_row(task, spinner_char, detail_indent, max_detail_width)
            )

        if hidden_counts["total"] > 0:
            hidden_parts = []
            if hidden_counts["RUNNING"]:
                hidden_parts.append(f"{hidden_counts['RUNNING']} running")
            # Note: hidden_counts["FAILED"] is always 0 because failed tasks are always visible
            detail_suffix = f" ({', '.join(hidden_parts)})" if hidden_parts else ""
            task_lines.append(
                Text(f"... {hidden_counts['total']} more active tasks hidden{detail_suffix}", style="dim")
            )

        if not visible_tasks and hidden_counts["total"] == 0 and not tasks:
            task_lines.append(Text("No active tasks", style="dim"))

        task_display = Group(*task_lines) if task_lines else Text("")

        if progress_info and not all_done:
            progress, _ = progress_info
            spacer = Text("")
            return Group(progress, spacer, task_display)

        # Either no progress bar or all tasks done
        return Group(task_display)

    # ------------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------------

    def _start_animation(self) -> None:
        """Start the animation thread for spinner updates."""
        if self._animation_thread is not None and self._animation_thread.is_alive():
            return

        def animate():
            while not self._stop_animation.is_set():
                with self._lock:
                    self._spinner_frame_index = (self._spinner_frame_index + 1) % len(SPINNER_FRAMES)
                # Live will auto-refresh and call _render_all(), which uses the updated spinner_frame_index
                time.sleep(ANIMATION_INTERVAL)

        self._stop_animation.clear()
        self._animation_thread = threading.Thread(target=animate, daemon=True)
        self._animation_thread.start()

    def _stop_animation_thread(self) -> None:
        """Stop the animation thread."""
        self._stop_animation.set()
        if self._animation_thread is not None:
            self._animation_thread.join(timeout=0.5)

    # ------------------------------------------------------------------------
    # Task Status Handlers
    # ------------------------------------------------------------------------

    def _mark_task_completed(self, task: Task, advance: bool = True) -> None:
        """Mark a task as completed and display the result.

        Args:
            task: The task to mark as completed
            advance: Whether to advance the progress bar (True for manual completion, False during iteration)
        """
        # Mark in registry (thread-safe)
        newly_completed = self._registry.mark_completed(task)

        # Note: timing.track_end() is already called in _mutate_task, so we don't duplicate it here
        if newly_completed and advance:
            self._update_progress(advance=True)
        # Live will automatically update the display via _render_all()

    def _mark_task_failed(self, task: Task, advance: bool = True) -> None:
        """Mark a task as failed and display the result.

        Args:
            task: The task to mark as failed
            advance: Whether to advance the progress bar (True for manual completion, False during iteration)
        """
        # Mark in registry (thread-safe)
        newly_completed = self._registry.mark_completed(task)

        # Note: timing.track_end() is already called in _mutate_task, so we don't duplicate it here
        if newly_completed and advance:
            self._update_progress(advance=True)
        # Live will automatically update the display via _render_all()

    def _update_task_status_display(self, task: Task, advance: bool = True) -> None:
        """Update the display based on task status.

        Args:
            task: The task to check and display
            advance: Whether to advance the progress bar (True for manual completion, False during iteration)
        """
        if task.status == TaskStatus.COMPLETED:
            self._mark_task_completed(task, advance)
        elif task.status == TaskStatus.FAILED:
            self._mark_task_failed(task, advance)
        # RUNNING tasks are handled automatically by Live display

    # ------------------------------------------------------------------------
    # Task Lookup (delegates to registry)
    # ------------------------------------------------------------------------

    def __len__(self) -> int:
        """Return the number of tasks."""
        return len(self._registry)

    def find_task(self, text: str) -> Task | None:
        """Find a task by its text.

        Args:
            text: The text of the task to find

        Returns:
            The Task object if found, None otherwise
        """
        return self._registry.find_task(text)

    def get_task_index(self, task: Task) -> int | None:
        """Get the index of a task.

        Args:
            task: The Task object to find

        Returns:
            The index of the task if found, None otherwise
        """
        return self._registry.get_task_index(task)

    def get_task_by_id(self, task_id: str) -> Task | None:
        """Get a task by its ID.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            The Task object if found, None otherwise
        """
        return self._registry.get_task_by_id(task_id)

    def get_task_index_by_id(self, task_id: str) -> int | None:
        """Get the index of a task by its ID.

        Args:
            task_id: The ID of the task to find

        Returns:
            The index of the task if found, None otherwise
        """
        return self._registry.get_task_index_by_id(task_id)

    # ------------------------------------------------------------------------
    # Public API - Task Status Management
    # ------------------------------------------------------------------------

    @overload
    def complete_task(self, task: Task) -> bool: ...

    @overload
    def complete_task(self, task: Iterable[Task]) -> bool: ...

    def complete_task(self, task: Task | Iterable[Task]) -> bool:
        """Mark one or more tasks as completed.

        Args:
            task: A Task object or iterable of Task objects to mark as completed

        Returns:
            True if all tasks were found and updated, False if any task was not found
        """
        tasks = self._ensure_task_list(task)
        if not tasks:
            return False

        all_succeeded = True
        for t in tasks:
            success = self._mutate_task(t, status=TaskStatus.COMPLETED)
            if not success:
                all_succeeded = False

        return all_succeeded

    @overload
    def fail_task(self, task: Task, error: str = "") -> bool: ...

    @overload
    def fail_task(self, task: Iterable[Task], error: str = "") -> bool: ...

    def fail_task(self, task: Task | Iterable[Task], error: str = "") -> bool:
        """Mark one or more tasks as failed.

        Args:
            task: A Task object or iterable of Task objects to mark as failed
            error: Optional error message (applied to all tasks if iterable is provided)

        Returns:
            True if all tasks were found and updated, False if any task was not found
        """
        tasks = self._ensure_task_list(task)
        if not tasks:
            return False

        all_succeeded = True
        for t in tasks:
            success = self._mutate_task(t, status=TaskStatus.FAILED, error=error)
            if not success:
                all_succeeded = False

        return all_succeeded

    def update_task_status(self, task: Task, status: TaskStatus | str, error: str | None = None) -> bool:
        """Update the status of a task.

        Args:
            task: The task to update
            status: New status (TaskStatus enum or string for backward compatibility)
            error: Optional error message if status is "FAILED"

        Returns:
            True if the task was found and updated, False if the task was not found
        """
        return self._mutate_task(task, status=status, error=error)

    def update_task_details(self, task: Task, details: str) -> bool:
        """Update the details text of a task.

        Args:
            task: The task to update
            details: New details content to display under the task text

        Returns:
            True if the task was found and updated, False if the task was not found
        """
        return self._mutate_task(task, details=details, advance=False)

    # ------------------------------------------------------------------------
    # Public API - Task Management
    # ------------------------------------------------------------------------

    @overload
    def add_task(self, task: Task) -> None: ...

    @overload
    def add_task(self, task: Iterable[Task]) -> None: ...

    def add_task(self, task: Task | Iterable[Task]) -> None:
        """Add one or more tasks to the list and automatically update the progress bar total.

        Tasks in RUNNING status are displayed immediately when added. Tasks in other statuses
        are handled by their respective status update methods.

        Args:
            task: A Task object or iterable of Task objects to append to the reader
        """
        tasks_to_add = self._ensure_task_list(task)
        if not tasks_to_add:
            return

        # Add to registry
        self._registry.add_task(tasks_to_add)

        # Track timing for new tasks
        with self._lock:
            for item in tasks_to_add:
                self._timing.track_start(item)

            # Update totals once after all tasks are added
            self.update_progress_total()

    @overload
    def remove_task(self, task: Task) -> bool: ...

    @overload
    def remove_task(self, task: Iterable[Task]) -> bool: ...

    def remove_task(self, task: Task | Iterable[Task]) -> bool:
        """Remove one or more tasks from the list and automatically update the progress bar total.

        Args:
            task: A Task object or iterable of Task objects to remove

        Returns:
            True if any tasks were removed, False if no tasks were removed.
            Note: If a task is not in the registry, it is silently ignored
            (idempotent operation).
        """
        tasks = self._ensure_task_list(task)
        if not tasks:
            return False

        # Remove from registry
        removed = self._registry.remove_task(tasks)

        if removed:
            # Clean up timing information
            with self._lock:
                for t in tasks:
                    self._timing.forget(t)
                # Update totals after removal
                self.update_progress_total()

        return removed

    # ------------------------------------------------------------------------
    # Public API - ID-based Operations
    # ------------------------------------------------------------------------

    def complete_task_by_id(self, task_id: str) -> bool:
        """Mark the task with ``task_id`` as completed.

        Returns ``True`` if the task exists and was updated, ``False`` otherwise.
        """
        task = self.get_task_by_id(task_id)
        if task is None:
            return False
        self.complete_task(task)
        return True

    def fail_task_by_id(self, task_id: str, error: str = "") -> bool:
        """Mark the task with ``task_id`` as failed.

        Returns ``True`` if the task exists and was updated, ``False`` otherwise.
        """
        task = self.get_task_by_id(task_id)
        if task is None:
            return False
        self.fail_task(task, error=error)
        return True

    def update_task_status_by_id(self, task_id: str, status: TaskStatus | str, error: str | None = None) -> bool:
        """Update the status of the task identified by ``task_id``.

        Returns ``True`` if the task exists and was updated, ``False`` otherwise.
        """
        task = self.get_task_by_id(task_id)
        if task is None:
            return False
        self.update_task_status(task, status, error)
        return True

    def update_task_details_by_id(self, task_id: str, details: str) -> bool:
        """Update the details of the task identified by ``task_id``.

        Returns ``True`` if the task exists and was updated, ``False`` otherwise.
        """
        task = self.get_task_by_id(task_id)
        if task is None:
            return False
        self.update_task_details(task, details)
        return True

    # ------------------------------------------------------------------------
    # Progress Bar Updates
    # ------------------------------------------------------------------------

    def update_progress_total(self) -> None:
        """Update the progress bar total to match the current number of tasks.

        This is automatically called when using add_task() or remove_task().

        Also updates the completed count to preserve the current progress percentage
        when the total changes (e.g., when tasks are added dynamically).

        Note: This method may be called while already holding the lock, which is safe
        because we use RLock.
        """
        with self._lock:
            # Count how many tasks are actually completed
            completed_count = len(self._registry.completed_tasks)
            total = len(self._registry)
            # Update progress while holding lock to ensure atomicity
            progress_info = self._get_progress_and_id()
            if progress_info:
                progress, task_id = progress_info
                progress.update(task_id, total=total, completed=completed_count)
