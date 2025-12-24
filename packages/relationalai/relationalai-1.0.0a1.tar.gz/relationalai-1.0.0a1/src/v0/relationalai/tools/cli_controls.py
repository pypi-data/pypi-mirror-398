#pyright: reportPrivateImportUsage=false
from __future__ import annotations

# Standard library imports
import io
import itertools
import os
import shutil
import sys
import threading
import time
import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Sequence, TextIO, cast

# Third-party imports
import rich
from InquirerPy import inquirer, utils as inquirer_utils
from InquirerPy.base.complex import FakeDocument
from InquirerPy.base.control import Choice
from prompt_toolkit.key_binding import KeyPressEvent
from prompt_toolkit.validation import ValidationError
from rich.color import Color
from rich.console import Console, Group
from wcwidth import wcwidth

# Local imports
from v0.relationalai import debugging
from v0.relationalai.util.format import format_duration
from ..environments import (
    HexEnvironment,
    JupyterEnvironment,
    NotebookRuntimeEnvironment,
    SnowbookEnvironment,
    runtime_env,
)

#--------------------------------------------------
# Constants
#--------------------------------------------------

# Display symbols
ARROW = "➜"
CHECK_MARK = "✓"
SUCCESS_ICON = "✅"
FAIL_ICON = "❌"

# Spinner animation frames
SPINNER_FRAMES = ["▰▱▱▱", "▰▰▱▱", "▰▰▰▱", "▰▰▰▰", "▱▰▰▰", "▱▱▰▰", "▱▱▱▰", "▱▱▱▱"]

# Terminal display constants
DEFAULT_TERMINAL_WIDTH = 80
SEPARATOR_WIDTH = 40

# Task progress constants
INITIALIZATION_COMPLETED_TEXT = "Parallel init finished in"
MIN_CATEGORY_DURATION_SECONDS = 0.25  # Only show categories with duration > 250ms

# Task category constants
TASK_CATEGORY_INDEXING = "indexing"
TASK_CATEGORY_PROVISIONING = "provisioning"
TASK_CATEGORY_CHANGE_TRACKING = "change_tracking"
TASK_CATEGORY_CACHE = "cache"
TASK_CATEGORY_RELATIONS = "relations"
TASK_CATEGORY_STATUS = "status"
TASK_CATEGORY_VALIDATION = "validation"
TASK_CATEGORY_OTHER = "other"

# Default summary categories
DEFAULT_SUMMARY_CATEGORIES = {
    TASK_CATEGORY_INDEXING: "Indexing",
    TASK_CATEGORY_PROVISIONING: "Provisioning",
    TASK_CATEGORY_CHANGE_TRACKING: "Change tracking",
    TASK_CATEGORY_RELATIONS: "Relations",
    TASK_CATEGORY_STATUS: "Status",
    TASK_CATEGORY_VALIDATION: "Validation",
    TASK_CATEGORY_OTHER: "Other"
}

# Parallel task categories (for duration calculation)
PARALLEL_TASK_CATEGORIES = {
    TASK_CATEGORY_INDEXING,
    TASK_CATEGORY_PROVISIONING,
    TASK_CATEGORY_VALIDATION,
    TASK_CATEGORY_CHANGE_TRACKING
}

# Prompt constants
REFETCH = "[REFETCH LIST]"
MANUAL_ENTRY = "[MANUAL ENTRY]"

# Timing constants
HIGHLIGHT_DURATION = 2.0
COMPLETION_DISPLAY_DURATION = 8.0
TIMER_CHECK_INTERVAL = 0.1
SPINNER_UPDATE_INTERVAL = 0.15
INITIAL_DISPLAY_DELAY = 0.25
BRIEF_PAUSE = 0.1
LIVE_REFRESH_RATE = 10

#--------------------------------------------------
# Style
#--------------------------------------------------

STYLE = inquirer_utils.get_style({
    "fuzzy_prompt": "#e5c07b"
}, False)

#--------------------------------------------------
# Helpers
#--------------------------------------------------

def rich_str(string:str, style:str|None = None) -> str:
    output = io.StringIO()
    console = Console(file=output, force_terminal=True)
    console.print(string, style=style)
    return output.getvalue()

def _load_ipython_display() -> tuple[Any, Callable[..., Any]]:
    """Load IPython display helpers, raising if unavailable."""
    try:
        module = importlib.import_module("IPython.display")
    except ImportError as exc:  # pragma: no cover - only triggered without IPython
        raise RuntimeError(
            "NotebookTaskProgress requires IPython when running in a notebook environment."
        ) from exc

    html_factory = getattr(module, "HTML")
    display_fn = getattr(module, "display")
    return html_factory, cast(Callable[..., Any], display_fn)

def nat_path(path: Path, base: Path):
    resolved_path = path.resolve()
    resolved_base = base.resolve()
    if resolved_base in resolved_path.parents or resolved_path == resolved_base:
        return resolved_path.relative_to(resolved_base)
    else:
        return resolved_path.absolute()

def get_default(value:str|None, list_of_values:Sequence[str]):
    if value is None:
        return None
    list_of_values_lower = [v.lower() for v in list_of_values]
    value_lower = value.lower()
    if value_lower in list_of_values_lower:
        return value

#--------------------------------------------------
# Dividers
#--------------------------------------------------

def divider(console=None, flush=False):
    div = "\n[dim]---------------------------------------------------\n "
    if console is None:
        rich.print(div)
    else:
        console.print(div)
    if flush:
        sys.stdout.flush()

def abort():
    rich.print()
    rich.print("[yellow]Aborted")
    divider()
    sys.exit(1)

#--------------------------------------------------
# Prompts
#--------------------------------------------------

default_bindings = cast(Any, {
    "interrupt": [
        {"key": "escape"},
        {"key": "c-c"},
        {"key": "c-d"}
    ],
    "skip": [
        {"key": "c-s"}
    ]
})

def prompt(message:str, value:str|None, newline=False, validator:Callable|None = None, invalid_message:str|None = None) -> str:
    if value:
        return value
    if invalid_message is None:
        invalid_message = "Invalid input"
    try:
        result:str = inquirer.text(
            message,
            validate=validator,
            invalid_message=invalid_message,
            keybindings=default_bindings,
        ).execute()
    except KeyboardInterrupt:
        abort()
        raise Exception("Unreachable")
    if newline:
        rich.print("")
    return result

def select(message:str, choices:List[str|Choice], value:str|None, newline=False, **kwargs) -> str|Any:
    if value:
        return value
    try:
        result:str = inquirer.select(message, choices, keybindings=default_bindings, **kwargs).execute()
    except KeyboardInterrupt:
        abort()
        raise Exception("Unreachable")
    if newline:
        rich.print("")
    return result

def _enumerate_static_choices(choices: inquirer_utils.InquirerPyChoice) -> inquirer_utils.InquirerPyChoice:
    return [{"name": f"{i+1} {choice}", "value": choice} for i, choice in enumerate(choices)]

def _enumerate_choices(choices: inquirer_utils.InquirerPyListChoices) -> inquirer_utils.InquirerPyListChoices:
    if callable(choices):
        return lambda session: _enumerate_static_choices(choices(session))
    else:
        return _enumerate_static_choices(choices)

def _fuzzy(message:str, choices:inquirer_utils.InquirerPyListChoices, default:str|None = None, multiselect=False, show_index=False, **kwargs) -> str|list[str]|None:
    if show_index:
        choices = _enumerate_choices(choices)

    try:
        kwargs["keybindings"] = default_bindings
        if multiselect:
            kwargs["keybindings"] = { # pylint: disable=assignment-from-no-return
                "toggle": [
                    {"key": "tab"},   # toggle choices
                ],
                "toggle-down": [
                    {"key": "tab", "filter":False},
                ],
            }.update(default_bindings)
            kwargs["multiselect"] = True

        # NOTE: Using the builtin `default` kwarg to do this also filters
        #       results which is undesirable and confusing for pre-filled
        #       fields, so we move the cursor ourselves using the internals :(
        prompt = inquirer.fuzzy(message, choices=choices, max_height=8, border=True, style=STYLE, **kwargs)
        prompt._content_control._get_choices(prompt._content_control.choices, default)

        return prompt.execute()
    except KeyboardInterrupt:
        return abort()

def fuzzy(message:str, choices:inquirer_utils.InquirerPyListChoices, default:str|None = None, show_index=False, **kwargs) -> str:
    return cast(str, _fuzzy(message, choices, default=default, show_index=show_index, **kwargs))

def fuzzy_multiselect(message:str, choices:inquirer_utils.InquirerPyListChoices, default:str|None = None, show_index=False, **kwargs) -> list[str]:
    return cast(list[str], _fuzzy(message, choices, default=default, show_index=show_index, multiselect=True, **kwargs))

def fuzzy_with_refetch(prompt: str, type: str, fn: Callable, *args, **kwargs):
    exception = None
    auto_select = kwargs.get("auto_select", None)
    not_found_message = kwargs.get("not_found_message", None)
    manual_entry = kwargs.get("manual_entry", None)
    items = []
    with Spinner(f"Fetching {type}", f"Fetched {type}"):
        try:
            items = fn(*args)
        except Exception as e:
            exception = e
    if exception is not None:
        rich.print(f"\n[red]Error fetching {type}: {exception}\n")
        return exception
    if len(items) == 0:
        if not_found_message:
            rich.print(f"\n[yellow]{not_found_message}\n")
        else:
            rich.print(f"\n[yellow]No valid {type} found\n")
        return None

    if auto_select and len(items) == 1 and items[0].lower() == auto_select.lower():
        return auto_select

    if manual_entry:
        items.insert(0, MANUAL_ENTRY)
    items.insert(0, REFETCH)

    passed_default = kwargs.get("default", None)
    passed_mandatory = kwargs.get("mandatory", False)

    rich.print("")
    result = fuzzy(
        prompt,
        items,
        default=get_default(passed_default, items),
        mandatory=passed_mandatory
    )
    rich.print("")

    while result == REFETCH:
        result = fuzzy_with_refetch(prompt, type, fn, *args, **kwargs)
    return result

def confirm(message:str, default:bool = False) -> bool:
    try:
        return inquirer.confirm(message, default=default, keybindings=default_bindings).execute()
    except KeyboardInterrupt:
        return abort()

def text(message:str, default:str|None = None, validator:Callable|None = None, invalid_message:str|None = None, **kwargs) -> str:
    if not invalid_message:
        invalid_message = "Invalid input"
    try:
        return inquirer.text(
            message,
            default=default or "",
            keybindings=default_bindings,
            validate=validator,
            invalid_message=invalid_message,
            **kwargs
        ).execute()
    except KeyboardInterrupt:
        return abort()

def password(message:str, default:str|None = None, validator:Callable|None = None, invalid_message:str|None = None) -> str:
    if invalid_message is None:
        invalid_message = "Invalid input"
    try:
        return inquirer.secret(
            message,
            default=default or "",
            keybindings=default_bindings,
            validate=validator,
            invalid_message=invalid_message
        ).execute()
    except KeyboardInterrupt:
        return abort()

def number(message:str, default:float|int|None = None, validator:Callable|None = None, invalid_message:str|None = None, **kwargs) -> float|int:
    if not invalid_message:
        invalid_message = "Invalid input"
    try:
        return inquirer.number(
            message,
            default=default or 0,
            keybindings=default_bindings,
            validate=validator,
            invalid_message=invalid_message,
            **kwargs
        ).execute()
    except KeyboardInterrupt:
        return abort()

def file(message: str, start_path:Path|None = None, allow_freeform=False, **kwargs) -> str|None:
    try:
        return FuzzyFile(message, start_path, allow_freeform=allow_freeform, max_height=8, border=True, style=STYLE, **kwargs).execute()
    except KeyboardInterrupt:
        return abort()

class FuzzyFile(inquirer.fuzzy):
    def __init__(self, message: str, initial_path: Path|None = None, allow_freeform = False,  *args, **kwargs):
        self.initial_path = initial_path or Path()
        self.current_path = Path(self.initial_path)
        self.allow_freeform = allow_freeform

        kwargs["keybindings"] = {
            **default_bindings,
            "answer": [
                {"key": os.sep},
                {"key": "enter"},
                {"key": "tab"},
                {"key": "right"}
            ],
            **kwargs.get("keybindings", {})
        }

        super().__init__(message, *args, **kwargs, choices=self._get_choices)

    def _get_prompt_message(self) -> List[tuple[str, str]]:
        pre_answer = ("class:instruction", f" {self.instruction} " if self.instruction else " ")
        result = str(nat_path(self.current_path, self.initial_path))

        if result:
            sep = " " if self._amark else ""
            return [
                ("class:answermark", self._amark),
                ("class:answered_question", f"{sep}{self._message} "),
                ("class:answer", f"{result}{os.sep if not self.status['answered'] else ''}"),
            ]
        else:
            sep = " " if self._qmark else ""
            return [
                ("class:answermark", self._amark),
                ("class:questionmark", self._qmark),
                ("class:question", f"{sep}{self._message}"),
                pre_answer
            ]

    def _handle_enter(self, event: KeyPressEvent) -> None:
        try:
            fake_document = FakeDocument(self.result_value)
            self._validator.validate(fake_document)  # type: ignore
            cc = self.content_control
            if self._multiselect:
                self.status["answered"] = True
                if not self.selected_choices:
                    self.status["result"] = [cc.selection["name"]]
                    event.app.exit(result=[cc.selection["value"]])
                else:
                    self.status["result"] = self.result_name
                    event.app.exit(result=self.result_value)
            else:
                res_value = cc.selection["value"]
                self.current_path /= res_value
                if self.current_path.is_dir():
                    self._update_choices()
                else:
                    self.status["answered"] = True
                    self.status["result"] = cc.selection["name"]
                    event.app.exit(result=str(nat_path(self.current_path, self.initial_path)))
        except ValidationError as e:
            self._set_error(str(e))
        except IndexError:
            self.status["answered"] = True
            res = self._get_current_text() if self.allow_freeform else None
            if self._multiselect:
                res = [res] if res is not None else []
            self.status["result"] = res
            event.app.exit(result=res)

    def _get_choices(self, _ = None):
        choices = os.listdir(self.current_path)
        choices.append("..")
        return choices

    def _update_choices(self):
        raw_choices = self._get_choices()
        cc = self.content_control
        cc.selected_choice_index = 0
        cc._raw_choices = raw_choices
        cc.choices = cc._get_choices(raw_choices, None)
        cc._safety_check()
        cc._format_choices()
        self._buffer.reset()

#--------------------------------------------------
# Line Clearing Mixin
#--------------------------------------------------

class LineClearingMixin:
    """Mixin class that provides line clearing functionality for different environments."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_line_length = 0
        # Detect environment capabilities
        import sys
        self.is_tty = sys.stdout.isatty()
        self.is_snowflake_notebook = isinstance(runtime_env, SnowbookEnvironment)
        self.is_jupyter = isinstance(runtime_env, JupyterEnvironment)

    def _get_terminal_width(self):
        """Get terminal width, with fallback to reasonable default."""
        try:
            return shutil.get_terminal_size().columns
        except (OSError, AttributeError):
            return 80  # Fallback width

    def _clear_line(self, new_text: str):
        """Clear the current line and write new text using the best available method."""
        import sys

        if self.is_tty and not self.is_snowflake_notebook and not self.is_jupyter:
            # Use proper ANSI clear line sequence for terminals
            sys.stdout.write(f"\r\033[K{new_text}")
        else:
            # For notebooks and environments without ANSI support, use smart padding
            terminal_width = self._get_terminal_width()

            # Truncate text if it exceeds terminal width to prevent wrapping
            if len(new_text) > terminal_width:
                new_text = new_text[:terminal_width - 3] + "..."

            # Calculate how much of the line we need to clear
            # Use the maximum of last line length or terminal width to ensure full clearing
            clear_width = max(self.last_line_length, terminal_width)

            # Clear with spaces and write new text
            sys.stdout.write(f"\r{' ' * clear_width}\r{new_text}")

        sys.stdout.flush()
        # Update the tracked line length
        self.last_line_length = len(new_text)

    def _write_line(self, text: str, newline: bool = False):
        """Write text to the current line, optionally adding a newline."""
        import sys
        if newline:
            sys.stdout.write(f"{text}\n")
        else:
            sys.stdout.write(text)
        sys.stdout.flush()

    def _clear_and_write(self, text: str, newline: bool = False):
        """Clear the current line and write new text, with optional newline."""
        self._clear_line(text)
        if newline:
            import sys
            sys.stdout.write("\n")
            sys.stdout.flush()


#--------------------------------------------------
# Spinner
#--------------------------------------------------

class Spinner(LineClearingMixin):
    """Shows a spinner control while a task is running.
    The finished_message will not be printed if there was an exception and the failed_message is provided.
    """
    busy = False

    def __init__(
        self,
        message="",
        finished_message: str = "",
        failed_message=None,
        delay=None,
        leading_newline=False,
        trailing_newline=False,
    ):
        self.message = message
        self.finished_message = finished_message
        self.failed_message = failed_message
        self.spinner_generator = itertools.cycle(SPINNER_FRAMES)
        self.is_snowflake_notebook = isinstance(runtime_env, SnowbookEnvironment)
        self.is_hex = isinstance(runtime_env, HexEnvironment)
        self.is_jupyter = isinstance(runtime_env, JupyterEnvironment)
        self.in_notebook = isinstance(runtime_env, NotebookRuntimeEnvironment)
        self.is_tty = sys.stdout.isatty()

        self._set_delay(delay)
        self.leading_newline = leading_newline
        self.trailing_newline = trailing_newline
        self.last_message = ""
        self.display = None
        # Add lock to prevent race conditions between spinner thread and main thread
        self._update_lock = threading.Lock()

    def _set_delay(self, delay: float|int|None) -> None:
        """Set appropriate delay based on environment and user input."""
        # If delay value is provided, validate and use it
        if delay:
            if isinstance(delay, (int, float)) and delay > 0:
                self.delay = float(delay)
                return
            else:
                raise ValueError(f"Invalid delay value: {delay}")
        # Otherwise, set delay based on environment
        elif self.is_hex:
            self.delay = 0 # Hex tries to append a new block each frame
        elif self.is_snowflake_notebook:
                self.delay = 0.5 # SF notebooks get bogged down
        elif self.in_notebook or self.is_tty:
            # Fast refresh for other notebooks or terminals with good printing support
            self.delay = 0.1
        else:
            # Otherwise disable the spinner animation entirely
            # for non-interactive environments.
            self.delay = 0

    def get_message(self, starting=False):
        max_width = shutil.get_terminal_size().columns
        spinner = "⏳⏳⏳⏳" if not self.is_tty and starting else next(self.spinner_generator)
        full_message = f"{spinner} {self.message}"
        if len(full_message) > max_width:
            return full_message[:max_width - 3] + "..."
        else:
            return full_message

    def update(self, message:str|None=None, color:str|None=None, file:TextIO|None=None, starting=False):
        # Use lock to prevent race conditions between spinner thread and main thread
        with self._update_lock:
            if message is None:
                message = self.get_message(starting=starting)
            if self.is_jupyter:
                # @NOTE: IPython isn't available in CI. This won't ever get invoked w/out IPython available though.
                from IPython.display import HTML, display # pyright: ignore[reportMissingImports]
                color_string = ""
                if color:
                    color_value = Color.parse(color)
                    rgb_tuple = color_value.get_truecolor()
                    rgb_hex = f"#{rgb_tuple[0]:02X}{rgb_tuple[1]:02X}{rgb_tuple[2]:02X}"
                    color_string = f"color: {rgb_hex};" if color is not None else ""
                content = HTML(f"<span style='font-family: monospace;{color_string}'>{message}</span>")
                if self.display is not None:
                    self.display.update(content)
                else:
                    self.display = display(content, display_id=True)
            else:
                if self.can_use_terminal_colors() and color is not None:
                    rich_message = f"[{color}]{message}"
                else:
                    rich_message = message
                rich_string = rich_str(rich_message)
                def width(word):
                    return sum(wcwidth(c) for c in word)
                diff = width(self.last_message) - width(rich_string)
                self.reset_cursor()
                # Use rich.print with lock protection
                output_file = file or sys.stdout
                rich.print(rich_message + (" " * diff), file=output_file, end="", flush=False)
                if output_file.isatty() or self.in_notebook:
                    output_file.flush()
                self.last_message = rich_string

    def can_use_terminal_colors(self):
        return not self.is_snowflake_notebook

    def update_messages(self, updater: dict[str, str]):
        if "message" in updater:
            self.message = updater["message"]
        if "finished_message" in updater:
            self.finished_message = updater["finished_message"]
        if "failed_message" in updater:
            self.failed_message = updater["failed_message"]
        self.update()

    def spinner_task(self):
        while self.busy and self.delay:
            self.update(color="magenta")
            time.sleep(self.delay) #type: ignore[union-attr] | we only call spinner_task if delay is not None anyway
            self.reset_cursor()

    def reset_cursor(self):
        if self.is_tty:
            # Clear the entire line and move cursor to beginning
            sys.stdout.write("\r\033[K")
        elif not self.is_jupyter:
            sys.stdout.write("\r")

    def __enter__(self):
        if self.leading_newline:
            rich.print()
        self.update(color="magenta", starting=True)
        # return control to the event loop briefly so stdout can be sure to flush:
        if self.delay:
            time.sleep(INITIAL_DISPLAY_DELAY)
        self.reset_cursor()
        if not self.delay:
            return self
        self.busy = True
        threading.Thread(target=self.spinner_task, daemon=True).start()
        return self

    def __exit__(self, exception, value, _):
        self.busy = False
        if exception is not None:
            if self.failed_message is not None:
                self.update(f"{self.failed_message} {value}", color="yellow", file=sys.stderr)
                # Use rich.print with explicit newline to ensure proper formatting
                rich.print(file=sys.stderr)
                return True
            return False
        if self.delay: # will be None for non-interactive environments
            time.sleep(self.delay)
        self.reset_cursor()
        if self.finished_message != "":
            final_message = f"▰▰▰▰ {self.finished_message}"
            self.update(final_message, color="green")
            # Use rich.print with explicit newline to ensure proper formatting
            rich.print()
        elif self.finished_message == "":
            self.update("")
            self.reset_cursor()
        if self.trailing_newline:
            rich.print()

class DebuggingSpan:
    span: debugging.Span
    def __init__(self, span_type: str):
        self.span_type = span_type
        self.span_attrs = {}

    def attrs(self, **kwargs):
        self.span_attrs = kwargs
        return self

    def __enter__(self):
        self.span = debugging.span_start(self.span_type, **self.span_attrs)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        debugging.span_end(self.span)

class SpanSpinner(Spinner):
    span: debugging.Span
    def __init__(self, span_type: str, *spinner_args, **spinner_kwargs):
        super().__init__(*spinner_args, **spinner_kwargs)
        self.span_type = span_type
        self.span_attrs = {}

    def attrs(self, **kwargs):
        self.span_attrs = kwargs
        return self

    def __enter__(self):
        self.span = debugging.span_start(self.span_type, **self.span_attrs)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)
        debugging.span_end(self.span)


@dataclass
class TaskInfo:
    """Represents a single task with its state and metadata."""
    description: str
    category: str = "other"
    completed: bool = False
    added_time: float = 0.0
    completed_time: float = 0.0
    hidden: bool = False

    def __post_init__(self):
        if self.added_time == 0.0:
            self.added_time = time.time()

    def get_duration(self) -> float:
        """Get the duration of this task in seconds."""
        if not self.completed or self.completed_time == 0.0:
            return 0.0

        return self.completed_time - self.added_time


class _TimerManager:
    """Manages all delayed operations for TaskProgress."""

    def __init__(self, progress_instance):
        self._progress = progress_instance
        self._operations = {}  # task_id -> (operation_type, scheduled_time)
        self._thread = None
        self._running = False

    def schedule_highlight_removal(self, task_id: str, delay: float | None = None):
        """Schedule removal of highlighting for a task."""
        if delay is None:
            delay = HIGHLIGHT_DURATION
        scheduled_time = time.time() + delay
        self._operations[task_id] = ("remove_highlighting", scheduled_time)
        self._start()

    def schedule_task_removal(self, task_id: str, delay: float | None = None):
        """Schedule removal of a completed task."""
        if delay is None:
            delay = COMPLETION_DISPLAY_DURATION
        scheduled_time = time.time() + delay
        self._operations[task_id] = ("delayed_removal", scheduled_time)
        self._start()

    def schedule_task_hiding(self, task_id: str, delay: float | None = None):
        """Schedule hiding of a completed task from display (but keep in data structure)."""
        if delay is None:
            delay = COMPLETION_DISPLAY_DURATION
        scheduled_time = time.time() + delay
        self._operations[task_id] = ("delayed_hiding", scheduled_time)
        self._start()


    def _start(self):
        """Start the timer thread if not already running."""
        if self._thread is None or not self._thread.is_alive():
            self._running = True
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()

    def _worker(self):
        """Worker thread for handling delayed operations."""
        while self._running:
            current_time = time.time()
            completed_ops = []

            # Find completed operations
            for task_id, (op_type, scheduled_time) in self._operations.items():
                if current_time >= scheduled_time:
                    completed_ops.append((task_id, op_type))

            # Process completed operations
            for task_id, op_type in completed_ops:
                self._process_operation(task_id, op_type)
                del self._operations[task_id]

            time.sleep(TIMER_CHECK_INTERVAL)

    def _process_operation(self, task_id: str, op_type: str):
        """Process a completed delayed operation."""
        progress = self._progress
        if op_type == "remove_highlighting":
            if hasattr(progress, "_highlighted_tasks") and task_id in progress._highlighted_tasks:
                del progress._highlighted_tasks[task_id]
                if hasattr(progress, "_after_task_update"):
                    progress._after_task_update()
        elif op_type == "delayed_removal":
            if hasattr(progress, "_tasks") and task_id in progress._tasks:
                del progress._tasks[task_id]
                if hasattr(progress, "_after_task_update"):
                    progress._after_task_update()
        elif op_type == "delayed_hiding":
            if hasattr(progress, "_tasks") and task_id in progress._tasks:
                progress._tasks[task_id].hidden = True
                if hasattr(progress, "_after_task_update"):
                    progress._after_task_update()

    def stop(self):
        """Stop the timer manager."""
        self._running = False
        self._operations.clear()


class _TaskStateMixin:
    """Shared task management helpers for notebook and terminal progress displays."""

    enable_highlighting: bool = True

    def _init_task_state(self, *, hide_on_completion: bool = False, show_duration_summary: bool = True) -> None:
        self.hide_on_completion = hide_on_completion
        self.show_duration_summary = show_duration_summary
        self._tasks: dict[str, TaskInfo] = {}
        self._next_task_id: int = 1
        self._highlighted_tasks: dict[str, float] = {}
        self._process_start_time: float | None = None
        self._process_end_time: float | None = None
        self.main_completed: bool = False
        self.main_failed: bool = False
        self._timer_manager = _TimerManager(self)

    def _after_task_update(self) -> None:
        """Hook for subclasses to react when task state changes."""
        # Implemented by subclasses when they need to update the display immediately.
        return None

    def _generate_task_id(self) -> str:
        """Generate a unique task ID."""
        task_id = f"task_{self._next_task_id}"
        self._next_task_id += 1
        return task_id

    def add_sub_task(self, description: str, task_id: str | None = None, category: str = "general") -> str:
        """Add a new sub-task and return its unique ID."""
        if task_id is None:
            task_id = self._generate_task_id()

        if task_id not in self._tasks:
            self._tasks[task_id] = TaskInfo(description=description, category=category)
            self._after_task_update()

        return task_id

    def update_sub_task(self, task_id: str, description: str) -> None:
        """Update an existing sub-task description."""
        if task_id in self._tasks:
            task_info = self._tasks[task_id]
            if self.enable_highlighting and task_info.description != description:
                self._highlighted_tasks[task_id] = time.time() + HIGHLIGHT_DURATION
                self._timer_manager.schedule_highlight_removal(task_id)

            task_info.description = description
            self._after_task_update()

    def complete_sub_task(self, task_id: str, record_time: bool = True) -> None:
        """Complete a sub-task by marking it as done."""
        if task_id in self._tasks:
            if task_id in self._highlighted_tasks:
                del self._highlighted_tasks[task_id]

            if not self._tasks[task_id].completed and record_time:
                self._tasks[task_id].completed_time = time.time()
            self._tasks[task_id].completed = True

            self._after_task_update()
            self._timer_manager.schedule_task_hiding(task_id)

    def remove_sub_task(self, task_id: str, animate: bool = True) -> None:
        """Remove a sub-task by ID with optional completion animation."""
        if task_id in self._tasks:
            if task_id in self._highlighted_tasks:
                del self._highlighted_tasks[task_id]

            if animate:
                self.complete_sub_task(task_id)
            else:
                del self._tasks[task_id]
                self._after_task_update()

    def update_sub_status(self, sub_status: str) -> None:
        """Legacy method for backward compatibility - creates/updates a default sub-task."""
        self.add_sub_task(sub_status, "default")
        self.update_sub_task("default", sub_status)

    def update_main_status(self, message: str) -> None:
        """Update the main status line with custom information."""
        if getattr(self, "description", "") != message:
            self.description = message
            self._after_task_update()

    def update_messages(self, updater: dict[str, str]) -> None:
        """Update both main message and sub-status if provided."""
        if "message" in updater:
            self.description = updater["message"]
            self._after_task_update()
        if "sub_status" in updater:
            self.update_sub_status(updater["sub_status"])
        if "success_message" in updater:
            self.success_message = updater["success_message"]
        if "failure_message" in updater:
            self.failure_message = updater["failure_message"]

    def get_sub_task_count(self) -> int:
        """Get the current number of active sub-tasks."""
        return len(self._tasks)

    def list_sub_tasks(self) -> list[str]:
        """Get a list of all active sub-task IDs."""
        return list(self._tasks.keys())

    def get_task_status(self) -> str:
        """Get a human-readable status of current task count vs limit."""
        return f"› Active tasks: {len(self._tasks)}"

    def get_task_duration(self, task_id: str) -> float:
        """Get the duration of a specific task in seconds."""
        if task_id in self._tasks:
            return self._tasks[task_id].get_duration()
        return 0.0

    def get_completed_tasks(self) -> dict[str, TaskInfo]:
        """Get all completed tasks with their timing information."""
        return {task_id: task_info for task_id, task_info in self._tasks.items() if task_info.completed}

    def get_tasks_by_category(self, category: str) -> dict[str, TaskInfo]:
        """Get all tasks (completed or active) for a specific category."""
        return {
            task_id: task_info
            for task_id, task_info in self._tasks.items()
            if task_info.category == category
        }

    def get_completed_tasks_by_category(self, category: str) -> dict[str, TaskInfo]:
        """Get all completed tasks for a specific category."""
        return {
            task_id: task_info
            for task_id, task_info in self._tasks.items()
            if task_info.category == category and task_info.completed
        }

    def _clear_all_tasks(self) -> None:
        """Clear all tasks and related data."""
        self._tasks.clear()
        self._highlighted_tasks.clear()

    def set_process_start_time(self) -> None:
        """Set the overall process start time."""
        self._process_start_time = time.time()

    def set_process_end_time(self) -> None:
        """Set the overall process end time."""
        self._process_end_time = time.time()

    def get_total_duration(self) -> float:
        """Get the total duration from first task added to last task completed."""
        if not self._tasks:
            return 0.0

        completed_tasks = self.get_completed_tasks()
        if not completed_tasks:
            return 0.0

        start_times = [task.added_time for task in self._tasks.values()]
        completion_times = [task.completed_time for task in completed_tasks.values() if task.completed_time > 0]

        if not start_times or not completion_times:
            return 0.0

        earliest_start = min(start_times)
        latest_completion = max(completion_times)
        return latest_completion - earliest_start


class TaskProgress(_TaskStateMixin):
    """A progress component that uses Rich's Live system to provide proper two-line display.

    This class provides:
    - Main progress line with spinner and description
    - Sub-status lines with hierarchical arrow indicators (➜)
    - Proper error handling with success/failure messages
    - Task-based progress tracking with context managers
    - Highlighting of subtask text changes in yellow for 2 seconds when text differs
    - Consistent task ordering with active tasks displayed above completed ones
    """

    def __init__(
        self,
        description: str = "",
        success_message: str = "",
        failure_message: str = "",
        leading_newline: bool = False,
        trailing_newline: bool = False,
        transient: bool = False,
        hide_on_completion: bool = False,
        show_duration_summary: bool = True,
    ):
        # Public configuration
        self.description = description
        self.success_message = success_message
        self.failure_message = failure_message
        self.leading_newline = leading_newline
        self.trailing_newline = trailing_newline
        self.transient = transient
        self._init_task_state(
            hide_on_completion=hide_on_completion,
            show_duration_summary=show_duration_summary,
        )
        self.enable_highlighting = True

        # Detect CI environment to avoid cursor control issues
        from ..environments import CIEnvironment
        self.is_ci = isinstance(runtime_env, CIEnvironment)
        self.is_jupyter = isinstance(runtime_env, JupyterEnvironment)

        # Core components
        # In CI or Jupyter, avoid forcing terminal rendering to prevent duplicate outputs
        force_terminal = not self.is_ci and not self.is_jupyter
        force_jupyter = True if self.is_jupyter else None
        self.console = Console(
            force_terminal=force_terminal,
            force_jupyter=force_jupyter,
        )
        self.live = None
        self.main_completed = False
        self.main_failed = False

        # Animation state
        self.spinner_index = 0

        # Performance optimizations
        self._render_cache = None
        self._last_state_hash = None

        self._spinner_thread = None

    def _generate_task_id(self) -> str:
        """Generate a unique task ID."""
        task_id = f"task_{self._next_task_id}"
        self._next_task_id += 1
        return task_id

    def _compute_state_hash(self) -> int:
        """Compute a simple hash of the current state for caching."""
        # Use a simple hash based on key state variables
        state_parts = [
            str(self.main_completed),
            str(self.main_failed),
            self.description,
            str(self.spinner_index),
            str(len(self._tasks)),
            str(len(self._highlighted_tasks)),
        ]

        # Add task states (only essential info for performance)
        for task_id, task_info in self._tasks.items():
            state_parts.append(f"{task_id}:{task_info.completed}:{task_info.description}")
            if task_id in self._highlighted_tasks:
                state_parts.append(f"highlight:{task_id}")

        return hash(tuple(state_parts))

    def _render_display(self):
        """Render the current display state with caching optimization."""
        # Check if we need to re-render
        current_hash = self._compute_state_hash()
        if current_hash == self._last_state_hash and self._render_cache is not None:
            return self._render_cache

        from rich.text import Text

        # Build main task line
        if self.main_failed:
            # Split the description to style only the "Failed:" part in red
            if self.description.startswith("Failed:"):
                failed_part = "Failed:"
                rest_part = self.description[len("Failed:"):].lstrip()
                main_line = (Text(f"{FAIL_ICON} ", style="red") +
                        Text(failed_part, style="red") +
                        Text(f" {rest_part}", style="default"))
            else:
                # Fallback if description doesn't start with "Failed:"
                main_line = Text(f"{FAIL_ICON} ", style="red") + Text(self.description, style="red")
        elif self.main_completed:
            main_line = Text(f"{SUCCESS_ICON} ", style="green") + Text(self.description, style="green")
        else:
            spinner_text = SPINNER_FRAMES[self.spinner_index]
            main_line = Text(f"{spinner_text} ", style="magenta") + Text(self.description, style="magenta")

        # Build subtask lines
        subtask_lines = self._render_subtask_lines()

        # Combine all lines
        all_lines = [main_line] + subtask_lines

        # Cache the result
        self._render_cache = Group(*all_lines)
        self._last_state_hash = current_hash

        return self._render_cache

    def _render_subtask_lines(self):
        """Render all subtask lines efficiently."""
        from rich.text import Text

        subtask_lines = []
        current_time = time.time()

        # Separate incomplete and completed tasks
        incomplete_tasks = []
        completed_tasks = []

        for task_id, task_info in self._tasks.items():
            # Skip hidden tasks
            if task_info.hidden:
                continue
            if task_info.completed:
                completed_tasks.append((task_id, task_info))
            else:
                incomplete_tasks.append((task_id, task_info))

        # Render incomplete tasks first
        for task_id, task_info in incomplete_tasks:
            is_highlighted = (task_id in self._highlighted_tasks and
                            current_time < self._highlighted_tasks[task_id])

            style = "yellow" if is_highlighted else "white"
            line = Text(f"   {ARROW} ", style=style) + Text(task_info.description, style=style)
            subtask_lines.append(line)

        # Render completed tasks
        for task_id, task_info in completed_tasks:
            line = Text(f"   {CHECK_MARK} ", style="green") + Text(task_info.description, style="green")
            subtask_lines.append(line)

        return subtask_lines

    def _advance_spinner(self):
        """Advance the spinner animation."""
        self.spinner_index = (self.spinner_index + 1) % len(SPINNER_FRAMES)

    def _invalidate_cache(self):
        """Invalidate the render cache to force re-rendering."""
        self._last_state_hash = None
        self._render_cache = None

    def _update_display(self):
        """Update the display if live."""
        if self.live:
            self.live.update(self._render_display())

    def _after_task_update(self) -> None:
        """Refresh the live display when task state changes."""
        self._invalidate_cache()
        self._update_display()

    def _clear_all_tasks(self) -> None:
        """Clear tasks and refresh display."""
        super()._clear_all_tasks()
        self._after_task_update()

    def generate_summary(self, categories: dict[str, str] | None = None) -> str:
        """Generate a summary of completed tasks by category."""
        if categories is None:
            categories = DEFAULT_SUMMARY_CATEGORIES

        category_durations: dict[str, float] = {}
        for category_name in categories:
            tasks = self.get_completed_tasks_by_category(category_name)
            category_durations[category_name] = _calculate_category_duration(category_name, tasks)

        if not any(category_durations.values()):
            return ""

        total_duration = self.get_total_duration()

        try:
            from rich.console import Console
            from rich.table import Table

            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("Operation", style="white")
            table.add_column("Duration", style="green", justify="right")

            if total_duration > 0:
                table.add_row(
                    INITIALIZATION_COMPLETED_TEXT,
                    format_duration(total_duration)
                )

            for category_name, display_name in categories.items():
                duration = category_durations[category_name]
                if duration > MIN_CATEGORY_DURATION_SECONDS:
                    table.add_row(
                        f" {ARROW} {display_name}",
                        format_duration(duration)
                    )

            table.add_row("", "")

            console = Console()
            with console.capture() as capture:
                console.print(table)
            return capture.get()

        except ImportError:
            lines: list[str] = []
            if total_duration > 0:
                lines.append(f"{INITIALIZATION_COMPLETED_TEXT} {format_duration(total_duration)}")

            for category_name, display_name in categories.items():
                duration = category_durations[category_name]
                if duration > MIN_CATEGORY_DURATION_SECONDS:
                    lines.append(f" {ARROW} {display_name} {format_duration(duration)}")

            if lines:
                lines.append("")

            return "\n".join(lines)

    def __enter__(self):
        if self.leading_newline:
            print()

        # Start the live display
        from rich.live import Live
        self.live = Live(self._render_display(), console=self.console, refresh_per_second=LIVE_REFRESH_RATE)
        self.live.start()

        # Start spinner animation
        self._start_spinner()

        return self

    def _start_spinner(self):
        """Start the spinner animation thread."""
        def spinner_animation():
            while self.live and not self.main_completed and not self.main_failed:
                time.sleep(SPINNER_UPDATE_INTERVAL)
                if self.live:
                    self._advance_spinner()
                    self.live.update(self._render_display())

        self._spinner_thread = threading.Thread(target=spinner_animation, daemon=True)
        self._spinner_thread.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Stop timer manager
        self._timer_manager.stop()

        if exc_type is not None:
            # Exception occurred - show failure message
            self._handle_failure(exc_val)
            return False  # Don't suppress the exception
        else:
            # Success - show completion
            self._handle_success()

        return True

    def _handle_failure(self, exc_val):
        """Handle failure case in context manager exit."""
        # Clear all tasks and update main task to show failure state
        self._clear_all_tasks()
        self.main_failed = True

        # Update main task description to show failure message
        if self.failure_message:
            self.description = self.failure_message
        else:
            self.description = f"Failed: {exc_val}"

        # Update the display to show the failure state before stopping
        if self.live:
            self.live.update(self._render_display())
            # Brief pause to show the failure state
            time.sleep(BRIEF_PAUSE)

        if self.trailing_newline:
            print()
        self._cleanup()

    def _handle_success(self):
        """Handle success case in context manager exit."""
        self.main_completed = True

        # Generate summary before clearing tasks (so we have the timing data)
        # Only generate if show_duration_summary flag is True
        summary = self.generate_summary() if self.show_duration_summary else ""

        self._clear_all_tasks()

        # Update main task description to show success message
        if self.success_message:
            self.description = self.success_message

        # Show success message in Rich Live display
        if self.live:
            self.live.update(self._render_display())
            # Stop the live display
            self.live.stop()

        # Print summary if available
        if summary:
            print()  # Blank line for separation
            print(summary, end="")  # summary already has trailing newline
            print()  # Add extra blank line after summary

        if self.trailing_newline:
            print()
        self._cleanup()

    def _cleanup(self):
        """Clean up resources."""
        if self.live:
            # Stop the live display first
            self.live.stop()
            # Clear the current line using ANSI escape sequence (only in TTY, not in CI)
            if not self.is_ci and sys.stdout.isatty():
                print("\r\033[K", end="", flush=True)

def _calculate_category_duration(category_name: str, tasks: Dict[str, TaskInfo]) -> float:
    """Calculate duration for a category based on task type (parallel vs sequential)."""
    if not tasks:
        return 0.0

    if category_name in PARALLEL_TASK_CATEGORIES:
        # For parallel tasks, use time span (max completion - min start)
        category_start_times = [task_info.added_time for task_info in tasks.values()]
        category_completion_times = [
            task_info.completed_time for task_info in tasks.values()
            if task_info.completed_time > 0
        ]
        if category_start_times and category_completion_times:
            return max(category_completion_times) - min(category_start_times)
        else:
            return 0.0
    else:
        # For sequential tasks, sum individual durations
        return sum(task_info.get_duration() for task_info in tasks.values())


def create_progress(description: str = "", success_message: str = "", failure_message: str = "",
leading_newline: bool = False, trailing_newline: bool = False, show_duration_summary: bool = True):
    """Factory function to create the appropriate progress component based on environment.

    Automatically detects if we're in a notebook environment (Snowflake, Jupyter, etc.)
    and returns the appropriate progress class.
    """
    from ..environments import runtime_env, SnowbookEnvironment, NotebookRuntimeEnvironment

    if isinstance(runtime_env, (SnowbookEnvironment, NotebookRuntimeEnvironment)):
        # Use NotebookTaskProgress for Snowflake and Jupyter notebooks
        return NotebookTaskProgress(
            description=description,
            success_message=success_message,
            failure_message=failure_message,
            leading_newline=leading_newline,
            trailing_newline=trailing_newline,
            show_duration_summary=show_duration_summary
        )
    else:
        # Use TaskProgress for other environments (terminal, CI, etc.)
        return TaskProgress(
            description=description,
            success_message=success_message,
            failure_message=failure_message,
            leading_newline=leading_newline,
            trailing_newline=trailing_newline,
            show_duration_summary=show_duration_summary
        )


class SubTaskContext:
    """Context manager for individual subtasks within a TaskProgress."""

    def __init__(self, task_progress: TaskProgress, description: str, task_id: str | None = None):
        self.task_progress = task_progress
        self.description = description
        self.task_id = task_id
        self._task_id = None

    def __enter__(self):
        # Add the subtask and get its ID
        self._task_id = self.task_progress.add_sub_task(self.description, self.task_id)
        return self._task_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._task_id and exc_type is None:
            # Success - complete the subtask automatically when context exits
            self.task_progress.complete_sub_task(self._task_id)
        # If there was an exception, leave the subtask as-is for debugging
        return False  # Don't suppress exceptions


class NotebookTaskProgress(_TaskStateMixin):
    """A progress component specifically designed for notebook environments like Snowflake.

    This class copies the EXACT working Spinner code and adapts it for notebook use.
    """

    def __init__(
        self,
        description: str = "",
        success_message: str = "",
        failure_message: str = "",
        leading_newline: bool = False,
        trailing_newline: bool = False,
        show_duration_summary: bool = True,
    ):
        self.description = description
        self.success_message = success_message
        self.failure_message = failure_message
        self.leading_newline = leading_newline
        self.trailing_newline = trailing_newline
        self._init_task_state(show_duration_summary=show_duration_summary)
        self.enable_highlighting = False

        self.spinner_generator = itertools.cycle(SPINNER_FRAMES)

        # Environment detection for notebook environments only
        self.is_snowflake_notebook = isinstance(runtime_env, SnowbookEnvironment)
        self.is_hex = isinstance(runtime_env, HexEnvironment)
        self.is_jupyter = isinstance(runtime_env, JupyterEnvironment)
        self.in_notebook = isinstance(runtime_env, NotebookRuntimeEnvironment)

        self._set_delay(None)

        self.last_message = ""
        self.display = None
        self._update_lock = threading.Lock()

        # Add sub-task support for TaskProgress compatibility
        self.spinner_thread = None
        self._current_subtask = ""
        self.busy = False  # Initialize busy state


    def _generate_task_id(self) -> str:
        """Generate a unique task ID."""
        task_id = f"task_{self._next_task_id}"
        self._next_task_id += 1
        return task_id

    def _set_delay(self, delay: float|int|None) -> None:
        """Set appropriate delay for notebook environments."""
        # If delay value is provided, validate and use it
        if delay:
            if isinstance(delay, (int, float)) and delay > 0:
                self.delay = float(delay)
                return
            else:
                raise ValueError(f"Invalid delay value: {delay}")
        # Simple delay for notebooks - no complex environment detection needed
        elif self.in_notebook or self.is_snowflake_notebook or self.is_jupyter or self.is_hex:
            self.delay = 0.2  # Simple, consistent delay for all notebook environments
        else:
            # Disable animation for non-interactive environments
            self.delay = 0

    def get_message(self, starting=False):
        """Get the current message with spinner - notebook environments only."""
        # For notebook environments, use a reasonable default width
        max_width = DEFAULT_TERMINAL_WIDTH
        try:
            max_width = shutil.get_terminal_size().columns
        except (OSError, AttributeError):
            pass  # Use default width if terminal size can't be determined

        spinner = "⏳⏳⏳⏳" if starting else next(self.spinner_generator)

        # If there's an active subtask, show ONLY the subtask
        if hasattr(self, '_current_subtask') and self._current_subtask:
            full_message = f"{spinner} {self._current_subtask}"
        else:
            # Otherwise show the main task with subtask count if any
            if len(self._tasks) > 0:
                full_message = f"{spinner} {self.description} ({len(self._tasks)} active)"
            else:
                full_message = f"{spinner} {self.description}"

        if len(full_message) > max_width:
            return full_message[:max_width - 3] + "..."
        else:
            return full_message

    def update(self, message:str|None=None, file:TextIO|None=None, starting=False):
        """Update the display - notebook environments only."""
        # Use lock to prevent race conditions between spinner thread and main thread
        with self._update_lock:
            if self.is_jupyter:
                _, display_fn = _load_ipython_display()

                if message is None:
                    lines = self._build_jupyter_lines(starting=starting)
                elif message == "":
                    lines = []
                else:
                    lines = [message]

                rendered = "\n".join(lines)
                content = {"text/plain": rendered}
                if self.display is not None:
                    self.display.update(content, raw=True)
                else:
                    self.display = display_fn(content, display_id=True, raw=True)
                return

            if message is None:
                message = self.get_message(starting=starting)

            rich_string = rich_str(message)

            def width(word):
                return sum(wcwidth(c) for c in word)

            diff = width(self.last_message) - width(rich_string)

            sys.stdout.write("\r")           # Move to beginning
            sys.stdout.write(" " * DEFAULT_TERMINAL_WIDTH)  # Clear with spaces
            sys.stdout.write("\r")           # Move back to beginning

            sys.stdout.write(message + (" " * diff))  # Write text directly
            if self.in_notebook:
                sys.stdout.flush()                    # Force output
            self.last_message = rich_string

    def _build_jupyter_lines(self, starting: bool) -> list[str]:
        """Compose the main status and subtasks for Jupyter display."""
        if self.busy or starting:
            spinner = SPINNER_FRAMES[0] if starting else next(self.spinner_generator)
            main_line = f"{spinner} {self.description}"
        else:
            main_text = self.success_message or self.description
            main_line = f"{SUCCESS_ICON} {main_text}"

        visible_tasks = self._collect_visible_tasks()
        lines = [main_line]

        for marker, tasks in (
            (ARROW, visible_tasks["incomplete"]),
            (CHECK_MARK, visible_tasks["completed"]),
        ):
            for task_info in tasks:
                lines.append(f"   {marker} {task_info.description}")

        return lines

    def _collect_visible_tasks(self) -> dict[str, list["TaskInfo"]]:
        """Separate visible tasks into incomplete and completed lists."""
        incomplete: list["TaskInfo"] = []
        completed: list["TaskInfo"] = []

        for task_info in self._tasks.values():
            if task_info.hidden:
                continue
            if task_info.completed:
                completed.append(task_info)
            else:
                incomplete.append(task_info)

        return {"incomplete": incomplete, "completed": completed}

    def reset_cursor(self):
        """Reset cursor to beginning of line - notebook environments only."""
        # For notebook environments, use simple carriage return
        if not self.is_jupyter:
            sys.stdout.write("\r")

    def spinner_task(self):
        """Spinner animation task."""
        while self.busy and self.delay:
            self.update()
            time.sleep(self.delay) #type: ignore[union-attr] | we only call spinner_task if delay is not None anyway
            self.reset_cursor()

    def _update_subtask_display(self, subtask_text: str):
        """Update sub-task display - shows ONLY the subtask text."""
        # Store the current display state
        if not hasattr(self, '_current_display'):
            self._current_display = ""

        # Only update if the display has changed
        if self._current_display != subtask_text:
            # Store the subtask text for the spinner to use
            self._current_subtask = subtask_text
            self._current_display = subtask_text
            # The spinner will now show the subtask instead of main task

    def add_sub_task(self, description: str, task_id: str | None = None, category: str = "general") -> str:
        task_id = super().add_sub_task(description, task_id, category)
        # Update spinner display with the active subtask
        if task_id in self._tasks:
            self._update_subtask_display(self._tasks[task_id].description)
        return task_id

    def update_sub_task(self, task_id: str, description: str) -> None:
        super().update_sub_task(task_id, description)
        if task_id in self._tasks:
            self._update_subtask_display(description)

    def complete_sub_task(self, task_id: str, record_time: bool = True) -> None:
        super().complete_sub_task(task_id, record_time=record_time)
        # Clear the subtask display when completed
        self._current_subtask = ""
        self._current_display = ""

    def remove_sub_task(self, task_id: str, animate: bool = True) -> None:
        """Remove a sub-task by ID."""
        task_description: str | None = None
        if task_id in self._tasks:
            task_description = self._tasks[task_id].description

        # Notebook display should drop the subtask immediately to clear the UI.
        super().remove_sub_task(task_id, animate=False)

        if task_description and getattr(self, "_current_subtask", "") == task_description:
            self._current_subtask = ""
            self._current_display = ""
            # The spinner will now show the main task again

    def update_sub_status(self, sub_status: str):
        """Legacy method for backward compatibility - creates/updates a default sub-task."""
        super().update_sub_status(sub_status)

    def update_main_status(self, message: str):
        """Update the main status line with real-time updates."""
        super().update_main_status(message)
        self._current_subtask = ""
        self._current_display = ""
        # The spinner will now show the updated main task

    def update_messages(self, updater: dict[str, str]):
        """Update both main message and sub-status if provided."""
        super().update_messages(updater)

    def _clear_all_tasks(self) -> None:
        super()._clear_all_tasks()
        self._current_subtask = ""
        self._current_display = ""

    def __enter__(self):
        # Skip leading newline for Jupyter - it interferes with IPython display
        if self.leading_newline and not self.is_jupyter:
            rich.print()
        self.update(starting=True)
        # return control to the event loop briefly so stdout can be sure to flush:
        if self.delay:
            time.sleep(INITIAL_DISPLAY_DELAY)
        self.reset_cursor()
        if not self.delay:
            return self
        self.busy = True
        threading.Thread(target=self.spinner_task, daemon=True).start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.busy = False
        if exc_type is not None:
            if self.failure_message is not None:
                self.update(f"{self.failure_message} {exc_val}", file=sys.stderr)
                # For non-Jupyter, add newline to ensure proper formatting
                # For Jupyter, IPython display handles formatting
                if not self.is_jupyter:
                    rich.print(file=sys.stderr)
                return True
            return False
        if self.delay: # will be None for non-interactive environments
            time.sleep(self.delay)

        # Generate summary BEFORE clearing the spinner line (so we have timing data)
        # Only generate if show_duration_summary flag is True
        summary = self.generate_summary() if self.show_duration_summary else ""

        # Clear the spinner line completely
        self._clear_spinner_line()

        final_message: str | None = None
        if self.success_message:
            final_message = f"{SUCCESS_ICON} {self.success_message}"
        elif summary:
            final_message = f"{SUCCESS_ICON} Done"

        if final_message:
            if self.is_jupyter:
                if self.display is not None:
                    self.display.update({"text/plain": final_message}, raw=True)
                else:
                    _, display_fn = _load_ipython_display()
                    self.display = display_fn({"text/plain": final_message}, display_id=True, raw=True)
            else:
                print(final_message)
        elif self.success_message == "":
            # When there's no success message, clear the display for notebooks
            # The summary will be printed below if available
            if self.is_jupyter:
                self.update("")
            # For non-Jupyter notebooks, _clear_spinner_line() already handled it

        # Print summary if there are completed tasks
        if summary:
            if self.is_jupyter:
                # Use IPython display to avoid blank stdout lines in notebooks
                _, display_fn = _load_ipython_display()
                display_fn({"text/plain": summary.strip()}, raw=True)
            else:
                print()
                print(summary.strip())  # Summary includes visual separator line

        # Skip trailing newline for Jupyter - it interferes with IPython display
        if self.trailing_newline and not self.is_jupyter:
            rich.print()
        return True

    def _clear_spinner_line(self):
        """Clear the current spinner line completely."""
        # Skip clearing for Jupyter notebooks - IPython display handles it
        if self.is_jupyter:
            return

        # Write enough spaces to clear any content, then move to start of line
        terminal_width = DEFAULT_TERMINAL_WIDTH
        try:
            terminal_width = shutil.get_terminal_size().columns
        except (OSError, AttributeError):
            pass

        # Clear with spaces, carriage return, and newline to ensure we're on a fresh line
        sys.stdout.write("\r" + " " * terminal_width + "\r\n")
        sys.stdout.flush()

    def set_process_start_time(self) -> None:
        """Set the overall process start time."""
        self._process_start_time = time.time()

    def set_process_end_time(self) -> None:
        """Set the overall process end time."""
        self._process_end_time = time.time()

    def get_total_duration(self) -> float:
        """Get the total duration from first task added to last task completed."""
        if not self._tasks:
            return 0.0

        completed_tasks = self.get_completed_tasks()
        if not completed_tasks:
            return 0.0

        # Find earliest start time and latest completion time
        start_times = [task.added_time for task in self._tasks.values()]
        completion_times = [task.completed_time for task in completed_tasks.values() if task.completed_time > 0]

        if not start_times or not completion_times:
            return 0.0

        earliest_start = min(start_times)
        latest_completion = max(completion_times)

        return latest_completion - earliest_start

    def generate_summary(self, categories: dict[str, str] | None = None) -> str:
        """Generate a summary of completed tasks by category."""
        if categories is None:
            categories = DEFAULT_SUMMARY_CATEGORIES

        # Get completed tasks by category and calculate durations
        category_durations = {}
        for category_name in categories:
            tasks = self.get_completed_tasks_by_category(category_name)
            category_durations[category_name] = _calculate_category_duration(category_name, tasks)

        # If there's nothing meaningful to show, return empty string
        if not any(category_durations.values()):
            return ""

        # Generate summary lines with proper alignment
        summary_lines = []
        label_width = 30  # Width for category labels
        time_width = 10   # Width for time column (right-aligned)

        # Add total time FIRST (at the top) - align with arrow lines
        total_duration = self.get_total_duration()
        if total_duration > 0:
            formatted_total = format_duration(total_duration)
            # Use the same format as arrow lines but with a different prefix
            # This ensures perfect alignment with the time column
            summary_lines.append(f" {INITIALIZATION_COMPLETED_TEXT:<{label_width-1}} {formatted_total:>{time_width}}")

        # Add category breakdown
        category_lines = []
        for category_name, display_name in categories.items():
            duration = category_durations[category_name]
            if duration > MIN_CATEGORY_DURATION_SECONDS:  # Only show significant durations
                formatted_duration = format_duration(duration)
                # Use arrow for visual consistency with right-aligned time
                category_lines.append(f" {ARROW} {display_name:<{label_width-4}} {formatted_duration:>{time_width}}")

        # Only add category lines if there are any
        if category_lines:
            summary_lines.extend(category_lines)

        # Add a visual separator line for Snowflake notebook environment
        summary_lines.append("─" * SEPARATOR_WIDTH)

        return "\n".join(summary_lines) + "\n"

    def get_completed_tasks(self) -> dict[str, TaskInfo]:
        """Get all completed tasks with their timing information."""
        return {task_id: task_info for task_id, task_info in self._tasks.items() if task_info.completed}

    def get_completed_tasks_by_category(self, category: str) -> dict[str, TaskInfo]:
        """Get all completed tasks for a specific category."""
        return {task_id: task_info for task_id, task_info in self._tasks.items()
                if task_info.category == category and task_info.completed}
