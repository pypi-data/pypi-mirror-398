from __future__ import annotations
import sys
from types import TracebackType
import ast
import io
import json
import re
import textwrap
from typing import Any, List, Literal, NamedTuple, Tuple

import rich.markup
from rich.console import Console
from rich.text import Text
from rich.table import Table
from rich import box
from enum import Enum
import contextlib
import contextvars

from .metamodel import Action, Task
from .environments import runtime_env, IPythonEnvironment, SnowbookEnvironment
from . import debugging
from .tools.constants import SHOW_FULL_TRACES


#--------------------------------------------------
# Print helpers
#--------------------------------------------------


_current_console = contextvars.ContextVar('current_console', default=None)

def get_console(*args, **kwargs):
   current = _current_console.get()
   if current is not None:
       return current
   return Console(*args, **kwargs)

@contextlib.contextmanager
def using_console(console):
   token = _current_console.set(console)
   try:
       yield
   finally:
       _current_console.reset(token)

@contextlib.contextmanager
def record(retain_buffer = False):
    buffer = io.StringIO()
    console = Console(record=True, file=buffer)
    with using_console(console):
        try:
            yield (console, buffer)
        finally:
            if not retain_buffer:
                buffer.close()

def rich_str(item:Any, style:str|None = None) -> str:
    output = io.StringIO()
    console = Console(file=output, force_terminal=True)
    console.print(item, style=style)
    return output.getvalue()

def body_text(console, body:str):
    body = textwrap.dedent(body)
    for line in body.splitlines():
        if not line.startswith("  "):
            console.print(line)
        else:
            console.print(line, soft_wrap=True)

def mark_source(source: debugging.SourceInfo|None, start_line:int|None=None, end_line:int|None=None, indent=8, highlight="yellow", highlight_lines = []):
    if source is None:
        return ""

    final_lines = []
    all_lines = source.source.splitlines()
    source_start = source.source_start_line or source.line or start_line or 0
    start_line = start_line if start_line is not None else source.line
    max_line = source.line + len(all_lines)
    end_line = end_line if end_line is not None else max_line
    line_number_len = len(str(max_line))
    for ix, line in enumerate(source.source.splitlines()):
        cur = line
        cur_indent = indent if ix > 0 else 0
        line_number = source_start + ix
        color = "dim white"
        if (line_number >= start_line and line_number <= end_line) or line_number in highlight_lines:
            color = highlight + " bold"
        cur = f"{' '*cur_indent}[{color}]  {line_number :>{line_number_len}} |  {cur}[/{color}]"
        final_lines.append(cur)
    return "\n".join(final_lines)

def print_source_error(source, name:str, content:str, color="red"):
    fixed_content_length = len(name) + len(source.file) + len(str(source.line)) + 2  # 2 for the spaces around the dash
    num_dashes = 74 - fixed_content_length
    dashes = '-' * num_dashes
    console = get_console(width=80, force_jupyter=False, stderr=True)
    console.print("\n")
    console.print(f"[{color}]--- {name} {dashes} {source.file}: {source.line}")
    console.print()
    body_text(console, content)
    console.print()
    console.print(f'[{color}]{"-" * 80}')
    console.print()

def print_error(name:str, content:str, color="red"):
    fixed_content_length = len(name) + 2  # 2 for the spaces around the dash
    num_dashes = 76 - fixed_content_length
    dashes = '-' * num_dashes
    console = get_console(width=80, force_jupyter=False, stderr=True)
    console.print("\n")
    console.print(f"[{color}]--- {name} {dashes}")
    console.print()
    body_text(console, content)
    console.print()
    console.print(f'[{color}]{"-" * 80}')
    console.print()

def print_error_name(name:str, color="red"):
    console = get_console(width=80, force_jupyter=False, stderr=True)
    console.print("\n")
    console.print(f'[{color}]{"-" * 80}')
    console.print()
    body_text(console, name)
    console.print()
    console.print(f'[{color}]{"-" * 80}')
    console.print()

SuggestionEnv = Literal["cli", "notebook", "python"]
class Suggestion(NamedTuple):
   env: SuggestionEnv
   cmd: str
   style: str|None = "green"

def suggest(suggestions: list[Suggestion], prefix = "with the following command", prefix_multi: str|None = None):
   """Format a list of suggestions, adapted to the current runtime environment."""
   if prefix_multi is None:
      prefix_multi = prefix + "s"

   relevant: list[Suggestion] = []
   for suggestion in suggestions:
      relevant += adapt_to_env(suggestion)

   if len(relevant) == 1:
      return "\n".join([
         prefix + ":",
         "",
         fmt_suggestion(relevant[0]),
      ])
   else:
      return "\n".join([
         prefix_multi + ":",
         "",
         "\n\n".join(fmt_suggestion(suggestion) for suggestion in relevant)
      ])

def fmt_suggestion(suggestion: Suggestion) -> str:
   """Format a single styled suggestion."""
   cmd = textwrap.dedent(suggestion.cmd)
   return "\n".join(f"[{suggestion.style}]{line}[/{suggestion.style}]" for line in cmd.splitlines()) if suggestion.style else cmd

def adapt_to_env(suggestion: Suggestion) -> list[Suggestion]:
   """Adapt a suggestion to work in the current runtime environment if possible, or exclude it if not."""
   if suggestion.env == "cli":
      if isinstance(runtime_env, SnowbookEnvironment) and runtime_env.runner == "warehouse":
         return []
      if isinstance(runtime_env, (IPythonEnvironment, SnowbookEnvironment)):
         return [Suggestion("notebook", "\n".join(f"! {subcmd}" for subcmd in partition_by_indent(textwrap.dedent(suggestion.cmd))), suggestion.style)]
      return [suggestion]
   else:
      return [suggestion]

def partition_by_indent(text):
    # Split on newlines followed by non-whitespace
    groups = re.split(r'\n(?=\S)', text)
    # Strip any trailing whitespace from each group
    return [group.rstrip() for group in groups]

#--------------------------------------------------
# Transformers
#--------------------------------------------------

class IfToWithTransformer(ast.NodeTransformer):
    def visit_If(self, node):
        with_node = ast.With(
            items=[ast.withitem(context_expr=node.test, optional_vars=None)],
            body=node.body,
            lineno=node.lineno,
            type_comment=None)
        return with_node

class WithDynamic(ast.NodeTransformer):
    def visit_With(self, node):
        content = ast.unparse(node.items[0].context_expr).replace(")", "dynamic=True)")
        with_node = ast.With(
            items=[ast.withitem(context_expr=ast.Name(id=content), optional_vars=node.items[0].optional_vars)],
            body=[],
            lineno=node.lineno,
            type_comment=None)
        return with_node

class SetToMethod(ast.NodeTransformer):
    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Attribute):
            keyword = ast.keyword(arg=node.targets[0].attr, value=node.value)
            return ast.Expr(value=ast.Call(
                func=ast.Attribute(value=node.targets[0].value, attr="set", ctx=ast.Load()),
                args=[],
                keywords=[keyword],
                lineno=node.lineno
            ))
        return node

class AssignToCompare(ast.NodeTransformer):
    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Attribute) and len(node.targets) == 1:
            compare_node = ast.Compare(
                left=node.targets[0],
                ops=[ast.Eq()],
                comparators=[node.value]
            )
            expr_node = ast.Expr(value=compare_node)
            ast.copy_location(expr_node, node)

            return expr_node
        return node

class PropertyNameReplacer(ast.NodeTransformer):
    def __init__(self, old_name, new_name):
        self.old_name = old_name
        self.new_name = new_name

    def visit_Attribute(self, node):
        # Check if the attribute name matches the old name
        if isinstance(node.attr, str) and node.attr == self.old_name:
            # Replace the attribute name with the new name
            node.attr = self.new_name
        return node

    def visit_Name(self, node):
        # Check if the variable name matches the old name
        if isinstance(node.id, str) and node.id == self.old_name:
            # Replace the variable name with the new name
            node.id = self.new_name
        return node

#--------------------------------------------------
# Finders
#--------------------------------------------------

class PropertyFinder(ast.NodeVisitor):
    def __init__(self, start_line, properties):
        self.errors = []
        self.start_line = start_line
        self.properties = properties
        self.found_properties_lines = []  # To store lines where properties are found
        self.dynamic_properties = []  # To store dynamic properties

    def to_line_numbers(self, node):
        return (node.lineno, node.end_lineno)

    def visit_Attribute(self, node):
        if node.attr in self.properties:
            line_numbers = self.to_line_numbers(node)
            if line_numbers[0] >= self.start_line:
                self.found_properties_lines.append(node.lineno)
        self.generic_visit(node)

    def visit_Call(self, node):
        # Check if this is a call to 'getattr'
        if (isinstance(node.func, ast.Name) and node.func.id == 'getattr' and
                len(node.args) >= 2):
            if isinstance(node.args[1], ast.Str):
                property_name = node.args[1].s
                if property_name in self.properties:
                    line_numbers = self.to_line_numbers(node)
                    if line_numbers[0] >= self.start_line:
                        self.found_properties_lines.append(node.lineno)
            else:
                line_numbers = self.to_line_numbers(node)
                if line_numbers[0] >= self.start_line:
                    self.dynamic_properties.append(node.lineno)
        self.generic_visit(node)

#--------------------------------------------------
# Metaclass
#--------------------------------------------------

class RAIPostInitMeta(type):
    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        instance.__post_init__()
        return instance

# --------------------------------------------------
# RAIException
# --------------------------------------------------

class RAIException(Exception, metaclass=RAIPostInitMeta):
    def __init__(self, message, name=None, content=None, source: debugging.SourceInfo|None=None, **kwargs):
        super().__init__(message)
        self.name = name
        self.message = message
        self.content = content
        self.source = source

        # Store any additional keyword arguments as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        return self.message

    def __post_init__(self):
        self.raw_content = self.strip_rich_tags()

    def pprint(self):
        if self.source and self.content:
            print_source_error(self.source, self.name or self.message, self.content.strip())
        elif self.content:
            print_error(self.name or self.message, self.content.strip())
        else:
            print_error_name(self.name or self.message)

    def __eq__(self, other):
        if isinstance(other, RAIException):
            return self.message == other.message and self.__dict__ == other.__dict__
        return False

    def strip_rich_tags(self):
        if self.content:
            # Use Text.from_markup to remove rich tags
            plain_text = Text.from_markup(self.content).plain
            # Split the content into lines
            lines = plain_text.split('\n')
            # Remove leading empty lines or lines with only whitespace
            while lines and not lines[0].strip():
                lines.pop(0)
            # Strip leading whitespace from the first non-empty line
            if lines:
                lines[0] = lines[0].lstrip()
            # Join the lines back together
            cleaned_content = '\n'.join(lines)
            return cleaned_content
        else:
            return self.message

    def clone(self, config=None):
        show_full_traces = SHOW_FULL_TRACES
        if config is not None:
            show_full_traces = config.get("show_full_traces", SHOW_FULL_TRACES)

        if show_full_traces:
            return self

        try:
            raise AssertionError
        except AssertionError:
            traceback = sys.exc_info()[2]
            back_frame = traceback.tb_frame.f_back if traceback else None

            if back_frame is None:
                return self.with_traceback(traceback)

        back_tb = TracebackType(tb_next=None,
                                    tb_frame=back_frame,
                                    tb_lasti=back_frame.f_lasti,
                                    tb_lineno=back_frame.f_lineno)
        return self.with_traceback(back_tb)

    def message_for_environment(self, message, cli_command, provider_call):
        if isinstance(runtime_env, SnowbookEnvironment):
            return textwrap.dedent(f"""
            {message} with the following call:

            [green]{provider_call}[/green]
            """)
        else:
            return textwrap.dedent(f"""
            {message} with either of the following commands:

            [green]{cli_command}[/green]

            [green]{provider_call}[/green]
            """)

class NonExistentConfigFileError(RAIException):
    def __init__(self, file_name: str):
        self.file_name = file_name
        self.message =  f"The specified configuration file '{file_name}' does not exist."
        self.name =  "Configuration file not found"

        # Format the content and raw_content
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return textwrap.dedent(f"""
        Configuration file '{self.file_name}' does not exist.

        To initialize one, use:

        [green]rai init[/green]
        """)

class InvalidActiveProfileError(RAIException):
    def __init__(self, active_profile_name: str):
        self.active_profile_name = active_profile_name
        self.message = f"The specified active profile '{self.active_profile_name}' set in the config is not found."
        self.name = f"Active profile '{active_profile_name}' not found"

        # Format the content and raw_content
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return textwrap.dedent(f"""
        The specified active profile '{self.active_profile_name}' is not found.
        Please check your configuration and ensure that the profile exists.

        To switch to a different profile, use the following command:

        [green]rai profile:switch[/green]

        To create a new profile, use:

        [green]rai init[/green]
        """)

class ModelError(RAIException):
    error_locations = {}

    def __init__(self, problems):
        super().__init__("Error object added")
        problem = problems[0]
        self.problems = problems
        self.source = ModelError.error_locations.get(problem["props"]["pyrel_id"], debugging.SourceInfo())
        self.message = problem["message"]
        self.name = "Model error"
        self.content = self.format_message()

    def get_formatted_props_string(self):
        # Create a table
        table = Table(show_header=True, box=box.ROUNDED, padding=(0, 1))
        ks = list([k for k in self.problems[0]["props"].keys() if not k.startswith("pyrel_")])
        for k in ks:
            table.add_column(k)

        for problem in self.problems:
            row = []
            for k in ks:
                row.append(str(problem["props"].get(k, "")))
            table.add_row(*row)

        with io.StringIO() as string_io:
            console = Console(file=string_io)
            console.print(table)
            table_string = string_io.getvalue()

        return table_string

    def format_message(self):
        row_str = self.get_formatted_props_string()

        marked = mark_source(self.source, self.source.line, self.source.line, indent=2) if self.source else ""
        return "\n\n".join([self.message, "  " + marked, row_str])


class RelQueryError(RAIException):
    def __init__(self, problem, source: debugging.SourceInfo|None = None):
        super().__init__("Rel query error")
        self.problem = problem
        self.source = source
        self.message = "Query error"
        self.name = "Query error"
        self.content = self.format_message()

    def format_message(self):
        problem = self.problem
        marked = mark_source(self.source, -1, -1) if self.source else ""
        return textwrap.dedent(f"""
        {rich.markup.escape(problem["report"])}
        {rich.markup.escape(problem["message"])}

        {marked}
        """)

class RAIExceptionSet(RAIException):
    def __init__(self, exceptions: List[RAIException]):
        super().__init__("Multiple Errors, see above")
        self.exceptions = exceptions

    def pprint(self):
        for exception in self.exceptions:
            exception.pprint()

    def clone(self, config=None):
        return RAIExceptionSet([exception.clone(config) for exception in self.exceptions])

# --------------------------------------------------
# Warning
# --------------------------------------------------

class RAIWarning(Warning, metaclass=RAIPostInitMeta):
    name = ""
    message: str|None = None
    content = None
    source = None

    def __init__(self, message="", name=None, content=None, source=None):
        self.name = name
        self.message = message
        self.content = content
        self.source = source

    def pprint(self):
        msg = self.name or self.message or ""
        if self.source and self.content:
            print_source_error(self.source, msg, self.content.strip(), color="yellow")
        elif self.content:
            print_error(msg, self.content.strip(), color="yellow")
        else:
            print_error_name(msg, color="yellow")

    def __post_init__(self):
        self.raw_content = self.strip_rich_tags()
        debugging.warn(self)

    def strip_rich_tags(self):
        if self.content:
            # Use Text.from_markup to remove rich tags
            plain_text = Text.from_markup(self.content).plain
            # Split the content into lines
            lines = plain_text.split('\n')
            # Remove leading empty lines or lines with only whitespace
            while lines and not lines[0].strip():
                lines.pop(0)
            # Strip leading whitespace from the first non-empty line
            if lines:
                lines[0] = lines[0].lstrip()
            # Join the lines back together
            cleaned_content = '\n'.join(lines)

            return cleaned_content
        else:
            return self.name

    def __str__(self):
        return f"{self.name}: {self.raw_content}"

class RelQueryWarning(RAIWarning):
    def __init__(self, problem, source):
        super().__init__("Query warning")
        self.name = "Query warning"
        self.problem = problem
        self.source = source
        self.message = "Query warning"
        self.content = self.format_message()

    def format_message(self):
        problem = self.problem
        marked = mark_source(self.source, -1, -1)
        return textwrap.dedent(f"""
        {problem["report"]}
        {problem["message"]}

        {marked}
        """)

class UnknownSourceWarning(RAIWarning):
    def __init__(self, source_fqns: list[str], role: str | None = None):
        name = "Unknown Source"

        if len(source_fqns) == 1:
            msg = textwrap.fill(
                f"Unable to access source '{source_fqns[0]}'. Ensure the fully qualified name is correct "
                f"and that your active role(s) have the required privileges.",
                78,
            )
        else:
            prefix = "The following sources could not be accessed:"
            suffix = textwrap.fill(
                "Ensure the fully qualified names are correct and that your active role(s) have the required privileges.",
                78,
            )
            msg = "\n".join(
                [prefix, "", *[f"- {fqn}" for fqn in source_fqns], "", suffix]
            )

        if role:
            msg += f"\n\nYour current primary role is '{role}', and by default all assigned roles are used as secondary roles."

        msg += "\n\n" + textwrap.fill(
            "While access via secondary roles is supported, we recommend granting the necessary privileges "
            "directly to your primary role to ensure consistent access.",
            78,
        )

        super().__init__(name, name, msg)
        self.source_fqns = source_fqns

class InvalidSourceTypeWarning(RAIWarning):
    def __init__(self, source_types: dict[str, str]):
        if len(source_types) == 1:
            [(fqn, type)] = source_types.items()
            msg = f"RAI currently only supports tables and views.\n The source '{fqn}' has type '{type}'"
        else:
            prefix = "RAI currently only supports tables and views. These have other types:"
            msg = "\n".join([
                prefix,
                "",
                *[f"- {fqn} ({type})" for fqn, type in source_types.items()]
            ])

        name = "Invalid source type"
        super().__init__(name, name, msg)
        self.source_types = source_types

class IntegrityConstraintViolation(RAIException):
    def __init__(self, violation, source=None):
        self.violation = violation
        self.source = source

        body = violation["message"]
        self.name = "Integrity constraint violation"
        self.message = "Integrity constraint violation"
        self.content = self.format_message(body)
        super().__init__(self.message, self.name, self.content, self.source)

    def format_message(self, body):
        marked = mark_source(self.source, -1, -1)

        f"Integrity constraint violation\n{body}"

        return textwrap.dedent(f"""
        {body}

        {marked}
        """)

    def clone(self, config=None):
        return IntegrityConstraintViolation(self.violation, self.source)

class ModelWarning(RAIWarning):
    error_locations = {}

    def __init__(self, problems):
        super().__init__("Error object added")
        problem = problems[0]
        self.problems = problems
        self.source = ModelError.error_locations.get(problem["props"]["pyrel_id"], debugging.SourceInfo())
        self.message = problem["message"]
        self.name = "Model warning"
        self.content = self.format_message()

    def get_formatted_props_string(self):
        # Create a table
        table = Table(show_header=True, box=box.ROUNDED, padding=(0, 1))
        ks = list([k for k in self.problems[0]["props"].keys() if not k.startswith("pyrel_")])
        for k in ks:
            table.add_column(k)

        for problem in self.problems:
            row = []
            for k in ks:
                row.append(str(problem["props"].get(k, "")))
            table.add_row(*row)

        with io.StringIO() as string_io:
            console = Console(file=string_io)
            console.print(table)
            table_string = string_io.getvalue()

        return table_string

    def format_message(self):
        row_str = self.get_formatted_props_string()

        marked = mark_source(self.source, self.source.line, self.source.line, indent=2) if self.source else ""
        return "\n\n".join([self.message or "", "  " + marked, row_str])

class RowsDroppedFromTargetTableWarning(RAIWarning):
    def __init__(self, rejected_rows: list[dict], rejected_rows_count: int, col_names_map: dict):
        """
        Warning raised when loading data into a table (exec_into_table API) and some rows are rejected due to erroneous data.
        """
        self.parsing_errors = self.replace_column_names(rejected_rows, col_names_map)
        self.name = "Rejected rows"
        self.content = self.format_message(rejected_rows, rejected_rows_count, self.parsing_errors)
        self.rejected_rows = rejected_rows
        self.rejected_rows_count = rejected_rows_count
        self.col_names_map = col_names_map
        super().__init__(self.name, self.name, self.content)

    def format_message(self, rejected_rows: list[dict], rejected_rows_count: int, parsing_errors: list[dict]) -> str:
        grouped_errors = {}

        # Group errors by ROW_NUMBER
        for i, row in enumerate(rejected_rows):
            error_indices = {e["index"] for e in parsing_errors}
            if i in error_indices:
                continue
            try:
                row_number = row['ROW_NUMBER']
                if row_number not in grouped_errors:
                    grouped_errors[row_number] = {'rejected_record': row['REJECTED_RECORD'], 'errors': []}
                grouped_errors[row_number]['errors'].append(f"Erroneous column: {row['COLUMN_NAME']}\nError message: {row['ERROR']}")
            except Exception as e:
                parsing_errors.append({"index": i, "message": str(e), "row": str(row)})

        msg = f"Your data has been loaded but {rejected_rows_count} rows were skipped due to erroneous data. Here are the first {len(grouped_errors)} rejected rows:\n"
        for row_number, data in grouped_errors.items():
            msg += f"""Rejected record: {data['rejected_record']}"""
            for error in data['errors']:
                msg += f"- {error}\n"
            msg += "\n"

        return msg

    """Replaces the autogenerated pyrel COLUMN_NAME in rejected_rows with the actual column names of the target table according to the mapping in col_names_map."""
    def replace_column_names(self, rejected_rows: list[dict], col_names_map: dict) -> list[dict]:
        # col_names_map looks like this: {col000: TIMESTAMPS, col002: id}
        # COLUMN_NAME in rejected_rows looks like this: "OUT23A38988_10B1_4BCB_B566_89F7F3C8D1FB_INTERNAL"["COL000":1]

        parsing_errors = []

        # Convert col_names_map keys to lowercase for case-insensitive matching
        col_names_map = {key.lower(): value for key, value in col_names_map.items()}
        for i, row in enumerate(rejected_rows):
            try:
                col_name = row['COLUMN_NAME'].split('[')[1].split(':')[0].replace('"', '').strip().lower()
                if col_name in col_names_map:
                    row['COLUMN_NAME'] = col_names_map[col_name]
            except Exception as e:
                parsing_errors.append({"index": i, "message": str(e), "row": str(row)})
        return parsing_errors
    
# --------------------------------------------------
# ERP Exceptions
# --------------------------------------------------

class ERPNotRunningError(RAIException):
    def __init__(self):
        super().__init__("ERP service state")
        self.name = "ERP service state"
        self.content = self.format_message()

    def format_message(self):
        return textwrap.dedent("""
            The ERP service is not available. Check your internet connection.
            If this issue persists, please contact support.
        """)

# --------------------------------------------------
# Rel Exceptions/warnings
# --------------------------------------------------

class NumericOverflow(RAIException):
    def __init__(self, problem, source):
        super().__init__("Numeric Overflow")
        self.problem = problem
        self.source = source
        self.message = "Numeric Overflow"
        self.name = "Numeric Overflow"
        self.content = self.format_message()

    def format_message(self):
        problem = self.problem
        marked = mark_source(self.source, -1, -1)
        info = problem["report"].split("\n--------------")[0].strip()
        return textwrap.dedent(f"""
        {info}

        {marked}
        """)

class ArityMismatch(RAIWarning):
    def __init__(self, problem, source):
        self.name = "Arity mismatch"
        self.message = problem["message"]
        self.source = source
        self.content = self.format_message()

    def format_message(self):
        source = self.source
        match = re.search(r"`(.+?)` expects (.*)", self.message or "")
        if match is None:
            return self.message
        fq_name = match.group(1)
        rel_name = fq_name.split("::")[-1]
        arity_sentence = match.group(2)
        found = PropertyFinder(source.line, [rel_name])
        if source.block:
            found.visit(source.block)
        found_lines = found.found_properties_lines or found.dynamic_properties
        marked = mark_source(self.source, -1, -1, highlight_lines=found_lines)
        return textwrap.dedent(f"""
        The relation [yellow]{rel_name}[/yellow] expects {arity_sentence}

        {marked}
        """)

class UninitializedPropertyException(RAIException):
    def __init__(self, undefined_list: List[Tuple[str, Any]]):
        self.content = ""
        self.raw_content = ""
        self.source = None
        message_chunks = []
        chunks: list[str] = []
        underscore_prefixed_list = list[Tuple[str, Any]]()

        # Deduplicate items in undefined_list
        seen = set()
        undefined_list = [item for item in undefined_list if item[0] not in seen and not seen.add(item[0])]

        # Check for properties that start with an underscore
        for item in undefined_list:
            if item[0].startswith("_"):
                underscore_prefixed_list.append(item)

        # Remove the underscore-prefixed items from the undefined_list
        if len(underscore_prefixed_list) > 0:
            for item in underscore_prefixed_list:
                undefined_list.remove(item)

        len_undefined = len(undefined_list)
        len_underscore = len(underscore_prefixed_list)

        if len_undefined > 0:
            if len_undefined == 1:
                message_chunks.append("Uninitialized property: " + undefined_list[0][0])
            else:
                message_chunks.append("Uninitialized properties: " + ", ".join([item[0] for item in undefined_list]))

        if len_underscore > 0:
            prefix = "renamed" if len_undefined > 0 else "Renamed"
            suffix = " property:" if len_undefined == 0 else ":"
            if len_underscore == 1:
                message_chunks.append(f"{prefix}{suffix} " + underscore_prefixed_list[0][0])
            else:
                suffix = " properties:" if len_undefined == 0 else ":"
                message_chunks.append(f"{prefix}{suffix} " + ", ".join([item[0] for item in underscore_prefixed_list]))

        self.message = ", ".join(message_chunks)
        self.name = self.message

        if len(undefined_list) > 0:
            source_map_undefined: dict[str, tuple[debugging.SourceInfo, list[str]]] = {}
            for name, source in undefined_list:
                if source.source not in source_map_undefined:
                    source_map_undefined[source.source] = (source, [name])
                else:
                    source_map_undefined[source.source][1].append(name)

            for (source, names) in source_map_undefined.values():
                self.source = source
                unique_names = list(set(names))
                props = ", ".join([f"[yellow]{name}[/yellow]" for name in unique_names])
                prop_line = (
                    f"property {props} has"
                    if len(unique_names) == 1
                    else f"properties {props} have"
                )
                found = PropertyFinder(source.line, unique_names)
                if source.block:
                    found.visit(source.block)
                found_lines = found.found_properties_lines or found.dynamic_properties
                marked = mark_source(source, -1, -1, indent=0, highlight_lines=found_lines)
                chunks.append(textwrap.dedent(f"""
                The {prop_line} never been set or added to and so will always cause the rule or query to fail.
                """))
                chunks.append(marked)

        if len(underscore_prefixed_list) > 0:
            source_map_underscore: dict[str, tuple[debugging.SourceInfo, list[str]]] = {}
            for name, source in underscore_prefixed_list:
                if source.source not in source_map_underscore:
                    source_map_underscore[source.source] = (source, [name])
                else:
                    source_map_underscore[source.source][1].append(name)

            for (source, names) in source_map_underscore.values():
                self.source = source
                unique_names = list(set(names))
                found = PropertyFinder(source.line, unique_names)
                if source.block:
                    found.visit(source.block)
                found_lines = found.found_properties_lines or found.dynamic_properties
                marked = mark_source(source, -1, -1, indent=0, highlight_lines=found_lines)
                chunks.append(textwrap.dedent("""
                Column names prefixed with '_' are clashing with internal properties.
                In your code replace the column name with the alias shown below:
                """))
                chunks.append("\n".join((f"[yellow]{name}[/yellow] \trename to:\t [green]{'col' + name}[/green]" for name, _ in underscore_prefixed_list)))
                chunks.append(marked)

        self.content = "\n\n".join(chunks)

        super().__init__(self.name, self.message, self.content, self.source)

class RAITypeError(RAIException, TypeError):
    def __init__(self, param: str, message: str):
        self.param = param
        self.message = message
        self.name = "Invalid type error"
        self.source = Errors.call_source(4)

        # Mark the source if available
        if self.source:
            self.marked = mark_source(self.source, self.source.line, self.source.line)
        else:
            self.marked = ""

        # Format the content and raw_content
        self.content = self.format_message()
        self.raw_content = self.strip_rich_tags()

        super().__init__(self.message, self.name, self.content, self.source)

    def format_message(self):
        if self.source:
            return textwrap.dedent(f"""
            The parameter [yellow]{self.param}[/yellow] is of the wrong type.

            {self.marked}
            """)
        else:
            return textwrap.dedent(f"""
            The parameter [yellow]{self.param}[/yellow] is of the wrong type.
            """)

class RAIValueError(RAIException, ValueError):
    def __init__(self, message: str):
        self.message = message
        self.name = "Invalid value error"
        self.source = Errors.call_source(4)

        # Mark the source if available
        if self.source:
            self.marked = mark_source(self.source, self.source.line, self.source.line)
        else:
            self.marked = ""

        # Format the content and raw_content
        self.content = self.format_message()
        self.raw_content = self.strip_rich_tags()

        super().__init__(self.message, self.name, self.content, self.source)

    def format_message(self):
        if self.source:
            return textwrap.dedent(f"""
            {self.message}

            {self.marked}
            """)
        else:
            return textwrap.dedent(f"""
            {self.message}
            """)



class RAIAbortedTransactionError(RAIException):
    def __init__(self, type, message, report):
        self.type = type
        self.message = message
        self.report = report
        self.name = "Transaction aborted"

        self.content = self.format_message()
        self.raw_content = self.strip_rich_tags()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        clean_report = "\n".join(line.lstrip() for line in self.report.splitlines())

        formatted = textwrap.dedent(f"""
            [yellow]The transaction was aborted due to the following error:[/yellow]

            Type: [yellow]{self.type}[/yellow]

            Message: [yellow]{self.message}[/yellow]

            Report: {clean_report}
            """)

        final_formatted = "\n".join(line.lstrip() for line in formatted.splitlines())
        return final_formatted


# --------------------------------------------------
# DSL scope errors
# --------------------------------------------------
class OutOfContextException(RAIException):
    def __init__(self, source=None):
        self.name = "Outside of context"
        self.message = (
            "Looks like this object is being used outside of a rule or query."
        )
        self.source = source or Errors.call_source() or debugging.SourceInfo()
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content, source=source)

    def format_message(self):
        marked = mark_source(self.source, self.source.line, self.source.line)
        return textwrap.dedent(f"""
        Looks like this [yellow]object[/yellow] is being used outside of a rule or query.

        {marked}
        """)


class VariableOutOfContextException(RAIException):
    def __init__(self, source, name: str|None, is_property=False):
        self.name = "Variable out of context"
        if name is None:
            self.message = "Looks like a variable is being used outside of the rule or query it was defined in."
        else:
            self.message = f"Looks like a variable representing '{name}' is being used outside of the rule or query it was defined in."
        self.source = source
        self.is_property = is_property
        self.content = self.format_message(name)

        super().__init__(self.message, self.name, self.content, source=source)

    def format_message(self, name):
        marked = mark_source(self.source, self.source.line, self.source.line)
        return textwrap.dedent(f"""
        Looks like a variable representing [yellow bold]{name}[/yellow bold] is being used outside of the rule or query it was defined in.

        {marked}
        """)

class SelectOutOfContext(RAIException):
    def __init__(self):
        self.name = "Outside of context"
        self.message = (
            "Looks like this select is being used outside of the query it was originally from."
        )
        self.source = Errors.call_source() or debugging.SourceInfo()
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content, source=self.source)

    def format_message(self):
        marked = mark_source(self.source, self.source.line, self.source.line)
        return textwrap.dedent(f"""
        Looks like this [yellow]select[/yellow] is being used outside of the query it is from.

        {marked}
        """)

#--------------------------------------------------
# DSL Type errors
#--------------------------------------------------

class FilterAsValue(RAIException):
    def __init__(self, source=None):
        self.name = "Filter used as a value"
        self.message = "Boolean expressions are filters and can't be used as values directly, use std.as_bool to cast them into True/False."
        self.source = source or Errors.call_source()
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content, source=self.source)

    def format_message(self):
        marked = mark_source(self.source, self.source.line, self.source.line) if self.source else ""
        return textwrap.dedent(f"""
        Boolean expressions are filters and can't be used as values directly. You can use relationalai.std.as_bool(..) to cast them into True/False.

        {marked}
        """)

class AsBoolForNonFilter(RAIException):
    def __init__(self, source=None):
        self.name = "as_bool used on non-filter"
        self.message = "as_bool can only be used on boolean expressions."
        self.source = source or Errors.call_source()
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content, source=self.source)

    def format_message(self):
        marked = mark_source(self.source, self.source.line, self.source.line) if self.source else ""
        return textwrap.dedent(f"""
        as_bool can only be used on boolean expressions.

        {marked}
        """)

class PropertyCaseMismatch(RAIWarning):
    def __init__(self, name, found_name):
        self.name = "Similar property name"
        self.message = ".{name} doesn't exist, but .{found_name} does"
        self.source = Errors.call_source()
        self.content = self.format_message(name, found_name)

    def format_message(self, name, found_name):
        source = self.source or debugging.SourceInfo()
        found = PropertyFinder(source.line, [name])
        if source.block:
            found.visit(source.block)
        found_lines = found.found_properties_lines or found.dynamic_properties
        marked = mark_source(source, -1, -1, indent=8, highlight_lines=found_lines)

        updated = mark_source(
            source.modify(PropertyNameReplacer(name, found_name)),
            -1, -1, indent=8, highlight_lines=found_lines, highlight="green",
        )

        return textwrap.dedent(f"""
        The property [yellow]{name}[/yellow] doesn't exist, but the very similar [green]{found_name}[/green] does.

        {marked}

        Did you mean [green]{found_name}[/green] instead?

        {updated}
        """)


class NonVarObject(RAIException, TypeError):
    def __init__(self, obj: Any, message: str):
        self.obj = obj
        self.message = message
        self.name = "non-var object used as variable"
        self.source = Errors.call_source(4)

        # Mark the source if available
        if self.source:
            self.marked = mark_source(self.source, self.source.line, self.source.line)
        else:
            self.marked = ""

        # Format the content and raw_content
        self.content = self.format_message()
        self.raw_content = self.strip_rich_tags()

        super().__init__(self.message, self.name, self.content, self.source)

    def format_message(self):
        if self.source:
            return textwrap.dedent(f"""
            [yellow]{self.obj.__class__.__name__}[/yellow] objects can't be used as variables, such as in a .add(), .set(), or select().

            {self.marked}
            """)
        else:
            return textwrap.dedent(f"""
            [yellow]{self.obj.__class__.__name__}[/yellow] objects can't be used as variables, such as in a .add(), .set(), or select().
            """)

class KeyedCantBeExtended(RAIException):
    def __init__(self):
        self.name = "Keyed types can't be extended"
        self.message = "Keyed types can't be extended."
        self.source = Errors.call_source() or debugging.SourceInfo()
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content, source=self.source)

    def format_message(self):
        marked = mark_source(self.source, self.source.line, self.source.line)
        return textwrap.dedent(f"""
        Keyed types can't be extended, use .add() in a rule instead.

        {marked}
        """)

class KeyedWrongArity(RAIException):
    def __init__(self, name:str, keys:List[str], given:int):
        self.name = "Incorrect number of keys"
        verb = "was" if given == 1 else "were"
        self.message = f"{name} expects {len(keys)} keys ({', '.join(keys)}), but only {given} {verb} given."
        self.source = Errors.call_source() or debugging.SourceInfo()
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content, source=self.source)

    def format_message(self):
        marked = mark_source(self.source, self.source.line, self.source.line)
        return textwrap.dedent(f"""
        {self.message}

        {marked}
        """)

class RowLiteralTooLargeWarning(RAIWarning):
    def __init__(self, size, max_size=1000):
        self.name = "Large row literal"
        self.message = f"Rows with more than {max_size} items can be slow to compile."
        self.size = size
        self.max_size = max_size
        self.source = Errors.call_source() or debugging.SourceInfo()
        self.content = self.format_message()

    def format_message(self):
        marked = mark_source(self.source, self.source.line, self.source.line)
        return textwrap.dedent(f"""
        Rows with more than {self.max_size} items can be slow to compile. This one has {self.size} items:

        {marked}
        """)

class RowLiteralTooLarge(RAIException):
    def __init__(self, size, max_size=10000):
        self.name = "Row literal too large"
        self.message = f"Rows can't have more than {max_size} items."
        self.size = size
        self.max_size = max_size
        self.source = Errors.call_source() or debugging.SourceInfo()
        self.content = self.format_message()

    def format_message(self):
        marked = mark_source(self.source, self.source.line, self.source.line)
        return textwrap.dedent(f"""
        Rows can't have more than {self.max_size} items. This one has {self.size} items:

        {marked}
        """)

class RowLiteralMismatch(RAIException):
    def __init__(self, mismatched_thing:str):
        self.name = "Row literal mismatch"
        self.message = f"All rows in a row literal must have the same {mismatched_thing}"
        self.mismatched_thing = mismatched_thing
        self.source = Errors.call_source() or debugging.SourceInfo()
        self.content = self.format_message()

    def format_message(self):
        marked = mark_source(self.source, self.source.line, self.source.line)
        return textwrap.dedent(f"""
        All rows in a row literal must have the same {self.mismatched_thing}

        {marked}
        """)


# --------------------------------------------------
# DSL property exceptions
# --------------------------------------------------


class ReservedPropertyException(RAIException):
    def __init__(self, source, property_name: str):
        self.name = "Reserved property name"
        self.message = f"The property '{property_name}' is a reserved property name on RelationalAI types."
        self.source = source
        self.content = self.format_message(property_name)

        super().__init__(self.message, self.name, self.content, source=self.source)

    def format_message(self, property_name):
        marked = mark_source(self.source, self.source.line, self.source.line)
        return textwrap.dedent(f"""
        The property '{property_name}' is a reserved property name on RelationalAI types.

        {marked}
        """)


class NonCallablePropertyException(RAIException):
    def __init__(self, source, property_name: str):
        self.name = "Non-callable property"
        self.message = f"The property '{property_name}' is not callable."
        self.source = source
        self.content = self.format_message(property_name)

        super().__init__(self.message, self.name, self.content, source=source)

    def format_message(self, property_name):
        marked = mark_source(self.source, self.source.line, self.source.line)
        return textwrap.dedent(f"""
        The property '{property_name}' is not callable on RelationalAI types.

        {marked}
        """)

class InvalidPropertySetException(RAIException):
    def __init__(self, source):
        self.name = "Invalid property set"
        self.message = "You can't set properties directly on a RAI object."
        self.source = source
        self.start_line = source.line
        self.end_line = source.line
        self.content = self.format_message()
        self.raw_content = self.strip_rich_tags()
        super().__init__(
            message=self.message, name=self.name, source=source, content=self.content
        )

    def format_message(self):
        marked = self.mark_source()
        dynamic = mark_source(
            self.source.modify(SetToMethod()),
            self.start_line,
            self.end_line,
            highlight="green",
        )
        compare = mark_source(
            self.source.modify(AssignToCompare()),
            self.start_line,
            self.end_line,
            highlight="green",
        )

        return textwrap.dedent(f"""
        You can't set properties directly on a RAI object.

        {marked}

        If you are trying to set the value of a property use [green]set()[/green]:

        {dynamic}

        Or maybe you meant [green]==[/green] instead?

        {compare}
        """)

    def mark_source(self):
        return mark_source(self.source, self.start_line, self.end_line)

class MultipleIdentities(RAIException):
    def __init__(self):
        source = Errors.call_source()
        self.name = "Multiple identities"
        self.message = "You can't pass multiple identity variables for a single object."
        self.source = source
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content, source=self.source)

    def format_message(self):
        marked = mark_source(self.source, self.source.line, self.source.line) if self.source else ""
        return textwrap.dedent(f"""
        You can't pass multiple identity variables for a single object.

        {marked}
        """)

# --------------------------------------------------
# Graph library exceptions
# --------------------------------------------------

class DirectedGraphNotApplicable(RAIValueError):
    def __init__(self, name: str):
        super().__init__(name)
        self.name = f"algorithm `{name}` is not applicable to directed graphs"

class DirectedGraphNotSupported(RAIValueError):
    def __init__(self, name: str, message_addendum: str = ""):
        message = f"algorithm `{name}` does not currently support directed graphs{'' if not message_addendum else f'. {message_addendum}'}"
        super().__init__(message)

class ParameterTypeMismatch(RAIValueError):
    def __init__(self, name: str, type_, value):
        super().__init__(name)
        self.name = (
            f"parameter `{name}` must be of type {type_.__name__.lower()}, "
            f"but its value {value!r} is of type {type(value)}"
        )

class ParameterBoundBelowInclusive(RAIValueError):
    def __init__(self, name: str, value, minimum):
        super().__init__(name)
        self.name = f"parameter `{name}` must be greater than or equal to {minimum}, but is {value!r}"

class ParameterBoundAboveInclusive(RAIValueError):
    def __init__(self, name: str, value, maximum):
        super().__init__(name)
        self.name = f"parameter `{name}` must be less than or equal to {maximum}, but is {value!r}"

class ParameterBoundBelowExclusive(RAIValueError):
    def __init__(self, name: str, value, minimum):
        super().__init__(name)
        self.name = f"parameter `{name}` must be strictly greater than {minimum}, but is {value!r}"

class ParameterBoundAboveExclusive(RAIValueError):
    def __init__(self, name: str, value, maximum):
        super().__init__(name)
        self.name = f"parameter `{name}` must be strictly less than {maximum}, but is {value!r}"


# --------------------------------------------------
# Engine exceptions
# --------------------------------------------------


class EngineNotFoundException(RAIException):
    def __init__(self, engine_name: str, message: str):
        self.engine_name = engine_name
        self.message = message
        self.name = "Engine unavailable"

        # Format the content and raw_content
        self.content = self.format_message()
        self.raw_content = self.strip_rich_tags()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        message = "We were unable to detect an existing engine or provision a new engine for you. To manually create an engine:"
        return self.message_for_environment(
            message,
            f"rai engines:create --name {self.engine_name}",
            f"rai.Provider().create_engine('{self.engine_name}')"
        )

class EngineProvisioningFailed(RAIException):
    def __init__(self, engine_name: str, original_exception: Exception | None = None):
        self.engine_name = engine_name
        self.original_exception = original_exception
        self.message = "Engine provisioning failed"
        self.name = self.message

        # Format the content and raw_content
        self.content = self.format_message()
        self.raw_content = self.strip_rich_tags()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        base_message = "\n".join([
            f"We tried to provision the engine [yellow]{self.engine_name}[/yellow] but it failed."
            "\n\n",
            "To learn more about how to manually manage engines, see:"
            "\n",
            "https://docs.relational.ai/api/cli/engines"
        ])

        # Add original exception details if available
        if self.original_exception:
            original_msg = str(self.original_exception).strip()
            if original_msg:
                base_message += f"\n\n[red]Error:[/red] {original_msg}"

        return base_message

class DuoSecurityFailed(RAIException):
    def __init__(self, _: Exception):
        self.message = "Connection failed due to Duo security"
        self.name = "Connection failed"

        # Format the content and raw_content
        self.content = self.format_message()
        self.raw_content = self.strip_rich_tags()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return "Establishing connection failed due to Duo security.\nPlease check your Duo security code/settings and try again."
class EnginePending(RAIException):
    def __init__(self, engine_name: str):
        self.engine_name = engine_name
        self.message = "Engine is in a pending state"
        self.name = "Engine not ready"

        # Format the content and raw_content
        self.content = self.format_message()
        self.raw_content = self.strip_rich_tags()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        message = f"The engine [yellow]{self.engine_name}[/yellow] is in a pending state. You can see the status of engines"
        return self.message_for_environment(
            message,
            "rai engines:list",
            "rai.Provider().list_engines()"
        )


class EngineResumeFailed(RAIException):
    def __init__(self, engine_name: str):
        self.engine_name = engine_name
        self.message = "Unable to resume engine"
        self.name = "Unable to resume engine"
        # Format the content and raw_content
        self.content = self.format_message()
        self.raw_content = self.strip_rich_tags()
        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        suggestions = [
           Suggestion("cli", f"""
           rai engines:delete --name {self.engine_name}
           rai engines:create --name {self.engine_name}
           """[1:-1]),
           Suggestion("python", f"""
           rai.Provider().delete_engine('{self.engine_name}')
           rai.Provider().create_engine('{self.engine_name}')
           """[1:-1])
        ]
        return "\n".join([
           f"The engine [yellow]{self.engine_name}[/yellow] could not be automatically resumed. Please ensure both your native app install and the `relationalai` package are up to date.",
           "",
           f"You can also manually recreate the engine {suggest(suggestions)}"
        ])


class InvalidEngineSizeError(RAIException):
    def __init__(self, engine_size: str, valid_sizes: list[str]):
        msg = f"Invalid engine size '{engine_size}'"
        self.name = msg
        self.message = msg

        # Format the content and raw_content
        self.content = "".join([
            f"Invalid engine size [yellow]{engine_size}[/yellow] provided. Please check your config."
            "\n",
            f"Valid engine sizes are: [green]{', '.join(valid_sizes)}[/green]"
        ])

        super().__init__(self.message, self.name, self.content)

class EngineNameValidationException(RAIException):
    def __init__(self, engine_name: str):
        self.engine_name = engine_name
        msg = "Engine auto-creation failed due to invalid engine name"
        self.name = msg
        self.message = msg

        # Format the content and raw_content
        self.content = self.format_message()
        self.raw_content = self.strip_rich_tags()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        from v0.relationalai.tools.cli_helpers import ENGINE_NAME_ERROR
        return "\n".join([
            f"We tried to auto-create engine [yellow]{self.engine_name}[/yellow] but it failed."
            "\n",
            f"Engine name requirements are: [yellow]{ENGINE_NAME_ERROR}[/yellow]"
        ])

# --------------------------------------------------
# Hex exceptions
# --------------------------------------------------

class HexSessionException(RAIException):
    def __init__(self):
        self.name = "Hex session error"
        self.message = "Missing Snowflake session object in Hex"
        self.content = self.format_message()
        self.raw_content = self.strip_rich_tags()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return textwrap.dedent("""
        To use RelationalAI in Hex, get your Snowflake session and supply it as a connection parameter to `rai.Model` or `rai.Provider`:

        [green]
        import hextoolkit
        hex_snowflake_conn = hextoolkit.get_data_connection('<Your Connection Name>')
        hex_snowpark_session = hex_snowflake_conn.get_snowpark_session()
        [/green]
        """)


# --------------------------------------------------
# Snowflake errors
# --------------------------------------------------

def handle_missing_integration(e: Exception):
    in_warehouse = (
        isinstance(runtime_env, SnowbookEnvironment)
        and runtime_env.runner == "warehouse"
    )
    if in_warehouse and any((name in str(type(e)) for name in ("NameResolutionError", "ProgrammingError", "SnowflakeIntegrationMissingException"))):
        raise SnowflakeIntegrationMissingException() from None

access_integration_warning = textwrap.dedent("""
Make sure that S3_RAI_INTERNAL_BUCKET_EGRESS_INTEGRATION is enabled. You can access the toggle from the vertical ellipsis button in the top-right corner of the Snowflake notebook window: ⋮ > Notebook settings > External access.

If you don't see S3_RAI_INTERNAL_BUCKET_EGRESS_INTEGRATION listed, get an account administrator to run Step 4 in the installation notebook here:

https://relational.ai/notebooks/relationalai-installation.ipynb
""")

class SnowflakeMissingConfigValuesException(RAIException):
    def __init__(self, missing_keys: list[str], profile: str | None = None, config_file_path: str | None = None):
        sorted_missing_keys = sorted(missing_keys)
        self.name = f"Missing {len(missing_keys)} required configuration value{'s' if len(missing_keys) > 1 else ''}"
        config_info = f"File: {config_file_path}\n" if config_file_path else ""
        profile_info = f"Profile: '{profile}'\n" if profile else ""
        self.message = f"""
{self.name}:

[green]{', '.join(sorted_missing_keys)}[/green]

{config_info}{profile_info}
[yellow]Please update the configuration file above to include the missing values.
"""
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return f"""{self.message}"""

class SnowflakeDatabaseException(RAIException):
    def __init__(self, exception: Exception):
        self.message = str(exception)
        self.name = "Snowflake Database Error"
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return f"""{self.message}"""

class SnowflakeIntegrationMissingException(RAIException):
    def __init__(self):
        self.message = access_integration_warning
        self.name = "Integration not enabled"
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return access_integration_warning

class SnowflakeAppMissingException(RAIException):
    def __init__(self, app_name: str, role: str | None = None):
        self.app_name = app_name
        self.role = role
        self.message = (
            f"Either the app '{app_name}' isn't installed in this Snowflake account "
            f"or you don't have permission to access it."
        )
        self.name = "Couldn't find RelationalAI Snowflake application"
        self.content = self.format_message()
        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        base = (
            f"Either the app '{self.app_name}' isn't installed in this Snowflake account, "
            f"or your active role(s) don't have permission to access it.\n\n"
            f"If it's installed under a different name, run 'rai init' on the command line to set the app name."
        )

        if self.role:
            base += f"\n\nYour current primary role is '{self.role}', and by default all assigned roles are used as secondary roles."

        base += "\n\nWhile access via secondary roles is supported, we recommend granting the necessary privileges directly to your primary role to ensure consistent access."

        return base


class SnowflakeImportMissingException(RAIException):
    def __init__(self, source: debugging.SourceInfo|None, import_name: str, model_name: str):
        self.source = source
        self.import_name = import_name
        self.model_name = model_name
        self.message = (
            f"The Snowflake object '{import_name}' hasn't been imported into RAI."
        )
        self.name = "Couldn't find import"
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return textwrap.dedent(f"""
            The Snowflake object '{self.import_name}' hasn't been imported into RAI.
            To automatically handle imports please verify that `use_graph_index` is not set to `False` in your config.

            You can also create an import for it using:

            [green]rai imports:stream --source {self.import_name} --model {self.model_name}[/green]

            [green]rai.Provider().create_streams(['{self.import_name}'], '{self.model_name}')[/green]
        """)


class SnowflakeChangeTrackingNotEnabledException(RAIException):
    def __init__(self, obj: tuple[str, str] | list[tuple[str, str]]):
        self.obj = obj
        if isinstance(obj, tuple):
            fqn, type = obj
            self.sql = f"[green]ALTER {type.upper()} {fqn} SET CHANGE_TRACKING = TRUE;[/green]"
            self.message = f"Change tracking isn't enabled for '{obj}'."
        elif isinstance(obj, list):
            self.sql = "\n".join([f"[green]ALTER {type.upper()} {fqn} SET CHANGE_TRACKING = TRUE;[/green]" for fqn, type in obj])
            self.message = f"Change tracking isn't enabled for the following sources: {', '.join(fqn for fqn, _ in obj)}"

        self.name = "Change tracking not enabled"
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        if isinstance(self.obj, tuple):
            fqn_str, _ = self.obj
        elif isinstance(self.obj, list):
            fqn_str = ', '.join(fqn for fqn, _ in self.obj)
        else:
            fqn_str = self.obj
        return (
            f"Change tracking isn't enabled for [yellow]{fqn_str}[/yellow].\n\n"
            f"To enable change tracking, you'll need to run the following SQL:\n\n"
            f"{self.sql}\n\n"
            f"If you want automatic enabling, please add [cyan]ensure_change_tracking = true[/cyan] to your config or Model"
        ).strip()

class ModelNotFoundException(RAIException):
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.message = "Model not found"
        self.name = f"Model '{model_name}' not found"

        # Format the content and raw_content
        self.content = self.format_message()
        self.raw_content = self.strip_rich_tags()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return textwrap.dedent(f"""
        The model '{self.model_name}' does not exist. You can create it by running a program containing the following:

        model = relationalai.Model("{self.model_name}")
        """)


class SnowflakeTableObject:
    def __init__(self, message: str, source: str):
        self.message = message
        self.source = source

class SnowflakeTableObjectsException(RAIException):
    def __init__(self, table_objects: List[SnowflakeTableObject]):
        self.table_objects = table_objects
        table_count = len(table_objects)
        table_word = "table" if table_count == 1 else "tables"

        self.message = f"Getting the following {table_word} failed with the error in Snowflake."
        self.name = f"Snowflake {table_word.capitalize()} Streaming Error"

        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        formatted_objects = [
            f"Source: [yellow bold]{obj.source}[/yellow bold]\n\n"
            f"Message: {obj.message.strip()}"
            for obj in self.table_objects
        ]
        return "\n\n".join(formatted_objects)

class SnowflakeInvalidSource(RAIException):
    def __init__(self, source, type_source: str):
        self.source = source
        self.type_source = type_source
        self.message = "Invalid source"
        self.name = "Invalid source"
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content, self.source)

    def format_message(self):
        marked = mark_source(self.source, self.source.line, self.source.line)
        return textwrap.dedent(f"""
        The source provided isn't a fully qualified Snowflake table or view name:

        {marked}
        """)

class SnowflakeRaiAppNotStarted(RAIException):
    def __init__(self, app_name: str):
        self.app_name = app_name
        self.message = f"The RelationalAI app '{app_name}' isn't started."
        self.name = "The RelationalAI application not started"
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return textwrap.dedent(f"""
        Your app '{self.app_name}' has not been activated.
        You can activate it by running the following SQL:

        [green]call {self.app_name}.app.activate();[/green]
        """)

# --------------------------------------------------
# RAI Warnings
# --------------------------------------------------

class InvalidIfWarning(RAIWarning):
    def __init__(self, task: Task | Action, start_line: int, end_line: int):
        self.name = "Invalid if"
        self.source = debugging.get_source(task)
        self.start_line = start_line
        self.end_line = end_line
        self.content = self.format_message()

    def format_message(self):
        marked = self.mark_source()
        updated = mark_source(
            self.source.modify(IfToWithTransformer()),
            self.start_line,
            self.end_line,
            highlight="green",
        ) if self.source else ""
        dynamic = mark_source(
            self.source.modify(WithDynamic()),
            self.source.line,
            self.end_line,
            highlight="green",
        ) if self.source else ""

        return textwrap.dedent(f"""
        In a RelationalAI query, using an if statement dynamically modifies the structure of the query itself, rather than adding a conditional.

        {marked}

        If you're trying to do an action based on a condition, use a [green]with[/green] statement instead.

        {updated}

        If you are trying to create a dynamic query where parts are conditional, add the [green]dynamic=True[/green] flag to the query like so:

        {dynamic}
        """)

    def mark_source(self):
        return mark_source(self.source, self.start_line, self.end_line)


class InvalidLoopWarning(RAIWarning):
    def __init__(self, task: Task | Action, start_line: int, end_line: int):
        self.name = "Invalid loop"
        self.source = debugging.get_source(task)
        self.start_line = start_line
        self.end_line = end_line
        self.content = self.format_message()

    def format_message(self):
        marked = self.mark_source() if self.source else ""
        dynamic = mark_source(
            self.source.modify(WithDynamic()),
            self.source.line,
            self.end_line,
            highlight="green",
        ) if self.source else ""

        return textwrap.dedent(f"""
        In a RelationalAI query, using a loop statement would dynamically modify the query itself, like a macro.

        {marked}

        If that's the goal, you can add the [green]dynamic=True[/green] flag to the query:

        {dynamic}
        """)

    def mark_source(self):
        return mark_source(self.source, self.start_line, self.end_line)

class InvalidTryWarning(RAIWarning):
    def __init__(self, task: Task | Action, start_line: int, end_line: int):
        self.name = "Invalid try"
        self.source = debugging.get_source(task)
        self.start_line = start_line
        self.end_line = end_line
        self.content = self.format_message()

    def format_message(self):
        marked = self.mark_source()
        dynamic = mark_source(
            self.source.modify(WithDynamic()),
            self.source.line,
            self.end_line,
            highlight="green",
        ) if self.source else ""

        return textwrap.dedent(f"""
        In a RelationalAI query, using a try statement will have no effect unless a macro-like function is being called and can fail.

        {marked}

        If macro-like behavior is the goal, you can add the [green]dynamic=True[/green] flag to the query:

        {dynamic}
        """)

    def mark_source(self):
        return mark_source(self.source, self.start_line, self.end_line)


class InvalidBoolWarning(RAIWarning):
    def __init__(self, source):
        self.name = "Invalid boolean expression with Producer"
        self.source = source
        self.start_line = source.line
        self.end_line = source.line
        self.content = self.format_message()
        self.raw_content = self.strip_rich_tags()

    def format_message(self):
        marked = self.mark_source()
        return textwrap.dedent(f"""
        In a RelationalAI query, the truth values of Producer objects are unknown
        until the query has been evaluated. You may not use Producers in boolean
        expressions, such as those involving [green]if[/green], [green]while[/green], [green]and[/green], [green]or[/green], and [green]not[/green]:

        {marked}

        Producer objects include:

        - [green]Instance[/green] objects, such as [green]person[/green].
        - [green]InstanceProperty[/green] objects, such as [green]person.age[/green].
        - [green]Expression[/green] objects, such as [green]person.age >= 18[/green].
        """)

    def mark_source(self):
        return mark_source(self.source, self.start_line, self.end_line)

# whether the python library or the Rel schema is out of date (or both!)
class InvalidVersionKind(Enum):
    LibraryOutOfDate = 'LibraryOutOfDate'
    SchemaOutOfDate = 'SchemaOutOfDate'
    Incompatible = 'Incompatible'

class RAIInvalidVersionWarning(RAIWarning):
    def __init__(
        self,
        kind: InvalidVersionKind,
        expected: List[Tuple[str, str, str]],
        lock: dict,
        platform: str,
        model_name: str,
        app_name: str,
        engine_name: str,
        errors: List[Tuple[InvalidVersionKind, str, str]] = []
    ):
        super().__init__()
        self.libraries = self.get_current_libs(errors)
        self.expected_lib_version = self.get_expected_lib_version(expected)
        self.current_lib_version = self.get_current_lib_version(lock)
        self.model_name = model_name
        self.app_name = app_name
        self.engine_name = engine_name

        self.name = "Invalid version"

        if kind == InvalidVersionKind.LibraryOutOfDate:
            msg = textwrap.dedent("""
                The RelationalAI Python library is out of date with respect to the schema. You can update the library using the following command:

                [green]pip install relationalai --upgrade[/green]
            """).strip()
        elif kind == InvalidVersionKind.SchemaOutOfDate:
            # if the "schema" is out of date, we need to delete the engine and recreate it
            msg = textwrap.dedent(
                    f"""The engine [yellow]{self.engine_name}[/yellow] is out of date with your version of the relationalai Python package.
                    Please delete the engine using the CLI command below and re-run your program:

                    [green]rai engines:delete --name {self.engine_name}[/green]""").strip()
        else:
            command = "pip install relationalai --upgrade"
            warehouse_notebook = (
                isinstance(runtime_env, SnowbookEnvironment)
                and runtime_env.runner == "warehouse"
            )
            if isinstance(runtime_env, IPythonEnvironment) and not warehouse_notebook:
                command = "!" + command
            if warehouse_notebook:
                lib_msg = textwrap.dedent("""
                    The RelationalAI Python library is incompatible with the current schema.

                    You can update the library by downloading the latest ZIP file from https://relational.ai/relationalai.zip and uploading it here.
                """).strip()
            else:
                lib_msg = textwrap.dedent(f"""
                    The RelationalAI Python library is incompatible with the current schema.
                    You can update the library using the following command:

                    [green]{command}[/green]
                """).strip()

            msg = f"{lib_msg}\n\nIn addition, the schema must be recreated."

        if len(self.libraries) > 0:
            library_info = self.generate_library_info()
            full_msg = f"{msg}\n\n{library_info}"
        else:
            full_msg = msg

        self.content = full_msg

    def extract_version(self, version_obj):
        match = re.search(r"\('([^']+)'\)", repr(version_obj))
        if match:
            return match.group(1)
        else:
            return ""

    def get_expected_lib_version(self, expected):
        libraries = {}
        for name, _, version_range in expected:
            from_version = self.extract_version(version_range[0])
            to_version = self.extract_version(version_range[1])
            libraries[name] = {"from": from_version, "to": to_version}
        return libraries

    def get_current_lib_version(self, lock):
        libraries = {}
        for k, v in lock.items():
            libraries[k[0]] = v
        return libraries

    def get_current_libs(self, errors=[]):
        if len(errors) == 0:
            return []

        libraries = []
        for _, library, _ in errors:
            libraries.append(library)
        return libraries

    def generate_library_info(self):
        if len(self.libraries) == 1:
            lib = self.libraries[0]
            current_version = self.current_lib_version.get(lib, "unknown")
            expected_version = self.expected_lib_version.get(lib, {})
            from_version = expected_version.get("from", "unknown")
            to_version = expected_version.get("to", "unknown")
            return (
                f"Your current library '{lib}' has version {current_version}. "
                f"However, it is expected to have a version range between {from_version} and {to_version}."
            )
        else:
            info = "Your current libraries have the following issues:\n"
            for lib in self.libraries:
                current_version = self.current_lib_version.get(lib, "unknown")
                expected_version = self.expected_lib_version.get(lib, {})
                from_version = expected_version.get("from", "unknown")
                to_version = expected_version.get("to", "unknown")
                info += (
                    f"- Library '{lib}' has version {current_version}. "
                    f"Expected version range: {from_version} to {to_version}.\n"
                )
            return info.strip()

class UnsupportedVisualizationError(RAIException):
    def __init__(self):
        name = "Unsupported Visualization Error"
        self.source = Errors.call_source() or debugging.SourceInfo()
        super().__init__(name, name, self.format_message(), self.source)

    def format_message(self):
        marked = mark_source(self.source)
        return textwrap.dedent(f"""
        This environment does not support embedding interactive visualizations via Graph.visualize().

        {marked}

        You can use graph.fetch() [1] to retrieve the necessary data to render your own visualization via whatever means the environment supports. Alternatively, consider running your program in another supported environment like a python script or jupyter.

        [1]: https://relational.ai/docs/reference/python/std/graphs/Graph/fetch
        """)

class EngineSizeMismatchWarning(RAIWarning):
    def __init__(self, engine_name: str, existing_size: str, requested_size: str):
        self.engine_name = engine_name
        self.existing_size = existing_size
        self.requested_size = requested_size
        self.message = f"An engine named '{engine_name}' already exists with a different size ('{existing_size}'). The existing engine will be used."
        self.name = "Engine size mismatch"

        # Format the content and raw_content
        self.content = self.format_message()
        self.raw_content = self.strip_rich_tags()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return textwrap.dedent(f"""
        An engine named '{self.engine_name}' already exists with a different size ('{self.existing_size}'). The existing engine will be used. You can change the size of '{self.engine_name}' by deleting the existing engine.

        You can delete the engine with either of the following commands:

        [green]rai engines:delete --name {self.engine_name}[/green]

        [green]rai.Provider().delete_engine('{self.engine_name}')[/green]
        """)

#--------------------------------------------------
# Deprecations + Migrations
#--------------------------------------------------

class DeprecationWarning(RAIWarning):
    def __init__(self, api: str, fix: str|None = None):
        self.api = api
        self.fix = fix

        self.name = "Deprecation Warning"
        self.prefix = f"'{api}' is deprecated and should no longer be used."
        self.message =  f"{self.prefix} {fix}" if fix else self.prefix
        self.source = Errors.call_source() or debugging.SourceInfo()
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content, source=self.source)

    def format_message(self):
        marked = mark_source(self.source, self.source.line, self.source.line)
        return textwrap.dedent(f"""
        {self.prefix}

        {marked}

        {self.fix}
        """)

class SnowflakeProxyAPIDeprecationWarning(DeprecationWarning):
   def __init__(self):
      super().__init__("clients.snowflake.Snowflake", "Instead, use the `source` keyword argument when defining types. See https://relational.ai/docs/reference/python/Model/Type for details.")

class SnowflakeProxySourceError(RAIException):
    def __init__(self):
        self.name = "Snowflake Proxy Source Error"
        self.message =  "Data sources derived from the deprecated snowflake proxy 'clients.snowflake.Snowflake' aren't supported with your current configuration."
        self.source = Errors.call_source() or debugging.SourceInfo()
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content, source=self.source)

    def format_message(self):
        marked = mark_source(self.source, self.source.line, self.source.line)
        return textwrap.dedent(f"""
        {self.message}

        {marked}

        Instead, use the `source` keyword argument when defining types. See https://relational.ai/docs/reference/python/Model/Type for details.
        """)

#--------------------------------------------------
# Direct Access Warnings
#--------------------------------------------------

class DirectAccessInvalidAuthWarning(RAIWarning):
    def __init__(self, authenticator, valid_authenticators):
        self.authenticator = authenticator
        self.valid_authenticators = valid_authenticators
        self.name = "Direct Access Invalid Auth"
        self.message = f"Due to security constraints in Snowflake, the selected authenticator '{authenticator}' is not supported when using direct access." 
        self.content = self.format_message()
        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        valid_authenticators_str = ", ".join(self.valid_authenticators)
        return textwrap.dedent(f"""
        {self.message}
        Falling back to 'use_direct_access=False'. This comes with a potential negative latency impact.
        Direct access requires one of the following authenticators: {valid_authenticators_str}
        """)

class InsecureKeychainWarning(RAIWarning):
    def __init__(self):
        self.message = "Insecure keyring detected. Please use a secure keyring backend."
        self.name = "Insecure Keyring Warning"
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return textwrap.dedent(f"""
        {self.message}
        
        A secure keychain is used to cache refresh tokens for oauth authentication. Without
        this caching mechanism a re-authentication will be required for each execution.
        """)

class KeychainFailureWarning(RAIWarning):
    def __init__(self, message):
        self.message = message
        self.name = "Keychain Failure Warning"
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return textwrap.dedent(f"""
        {self.message}

        This may be due to a misconfiguration or an issue with the keyring backend.
        A secure keychain is used to cache refresh tokens for oauth authentication. Without
        this caching mechanism a re-authentication will be required for each execution.
        """)

#--------------------------------------------------
# Direct Access Exceptions
#--------------------------------------------------

class DirectAccessInvalidAuthException(RAIException):
    def __init__(self, authenticator, valid_authenticators):
        self.authenticator = authenticator
        self.valid_authenticators = valid_authenticators
        self.name = "Direct Access Invalid Auth"
        self.message = f"Due to security constraints in Snowflake, the selected authenticator '{authenticator}' is not supported when using direct access." 
        self.content = self.format_message()
        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        valid_authenticators_str = ", ".join(self.valid_authenticators)
        return textwrap.dedent(f"""
        {self.message}
        Use a valid authenticator or deactivate direct access via 'use_direct_access=False'.
        Direct access requires one of the following authenticators: {valid_authenticators_str}
        """)

class ResponseStatusException(RAIException):
    def __init__(self, message: str, response):
        self.message = message
        self.response = response
        self.response_message = self._extract_response_message()
        self.name = "Response Status Error"
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return f"{self.message} Status Code: {self.response.status_code}, Reason: {self.response.reason} {self.response_message}"

    def _extract_response_message(self):
        try:
            return self.response.json().get("message", self.response.text)
        except Exception:
            return self.response.text

class OAuthFailedPortBinding(RAIException):
    def __init__(self, redirect_port, exception):
        self.redirect_port = redirect_port
        self.message = f"Failed to bind to the OAuth redirect URI port {self.redirect_port}."
        self.name = "OAuth Failed Port Binding Error"
        self.exception = exception
        self.content = self.format_message()
        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return textwrap.dedent(f"""
        {self.message}

        This usually happens when the specified port for the OAuth redirect URI is not available.
        You can fix the issue by ensuring that the port {self.redirect_port} is open and accessible.
        You can check which processes are using this port with the command 'lsof -t -i :{self.redirect_port}' on Unix-based systems or 'netstat -ano | findstr :{self.redirect_port}' on Windows.
        If you are sure no process should be running on this port, you can try killing any processes that are using it.

        The original exception was: {self.exception}
        """)

#TODO: Take out call_source from Errors class and put it in the main module
class Errors:
    @staticmethod
    def call_source(steps=None):
        if steps is None:
            return runtime_env.get_source()
        return runtime_env.get_source(steps + 1)


class InvalidAliasError(RAIException):
    def __init__(self, msg: str):
        self.message = msg
        self.name = "Invalid property alias found"
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return self.message


class LeftOverRelationException(RAIException):
    def __init__(self, import_name: str, model: str):
        self.import_name = import_name
        self.model = model
        self.message = f"Relations are not empty for import '{import_name}'"
        self.name = f"Stream relations for '{import_name}' are not empty"
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return textwrap.dedent(f"""
        The import '{self.import_name}' cannot be created due to existing non-empty relationships.

        You can use the [green]--force[/green] parameter to overwrite these:

        [green]rai imports:stream --source {self.import_name.upper()} --model {self.model} --force[/green]

        To delete the import and all its relationships, use the [green]--force[/green] parameter:

        [green]rai imports:delete --object {self.import_name.upper()} --model {self.model} --force[/green]
        """)

class UnsupportedColumnTypesWarning(RAIWarning):
    def __init__(self, table_invalid_columns: dict[str, dict[str, str]]):
        self.table_invalid_columns = table_invalid_columns
        self.message = self._generate_message()
        self.name = self._generate_name()
        self.content = self.format_message()

        super().__init__(self.message, self.name, self.content)

    def _generate_message(self):
        total_tables = len(self.table_invalid_columns)
        total_columns = sum(len(invalid_columns) for invalid_columns in self.table_invalid_columns.values())

        if total_tables == 1:
            table_name = next(iter(self.table_invalid_columns.keys()))
            return f"Found {total_columns} unsupported column type(s) in table '{table_name}'"
        else:
            return f"Found {total_columns} unsupported column type(s) across {total_tables} tables"

    def _generate_name(self):
        total_tables = len(self.table_invalid_columns)
        total_columns = sum(len(invalid_columns) for invalid_columns in self.table_invalid_columns.values())

        if total_tables == 1:
            table_name = next(iter(self.table_invalid_columns.keys()))
            return f"Unsupported Column Types - {total_columns} column(s) in {table_name}"
        else:
            return f"Unsupported Column Types - {total_columns} column(s) across {total_tables} tables"

    def format_message(self):
        def extract_type(data_type):
            # Extract just the basic type from Snowflake data_type
            # data_type might be a JSON string like {"type":"VARIANT","nullable":true}
            # or a simple string like "VARIANT"
            try:
                parsed = json.loads(data_type)
                if isinstance(parsed, dict) and "type" in parsed:
                    return parsed["type"]
                return str(parsed)
            except (json.JSONDecodeError, TypeError):
                # If it's not JSON, treat it as a simple string
                if '(' in data_type:
                    return data_type.split('(')[0]
                return data_type

        total_tables = len(self.table_invalid_columns)
        total_columns = sum(len(invalid_columns) for invalid_columns in self.table_invalid_columns.values())

        # Build organized display by table
        table_sections = []
        columns_displayed = 0
        MAX_COLUMNS_TO_DISPLAY = 10

        for table_name, invalid_columns in self.table_invalid_columns.items():
            table_columns = []
            for col_name, data_type in invalid_columns.items():
                if columns_displayed >= MAX_COLUMNS_TO_DISPLAY:
                    break
                type_only = extract_type(data_type)
                table_columns.append(f"  [yellow]{col_name}[/yellow]: [red]{type_only}[/red]")
                columns_displayed += 1

            if table_columns:
                table_sections.append(f"[yellow]{table_name}[/yellow]:\n" + "\n".join(table_columns))

            if columns_displayed >= MAX_COLUMNS_TO_DISPLAY:
                break

        # Build the message
        if total_tables == 1:
            table_name = next(iter(self.table_invalid_columns.keys()))
            message = f"Found {total_columns} unsupported column type(s) in table '{table_name}':"
        else:
            message = f"Found {total_columns} unsupported column type(s) across {total_tables} tables:"

        if total_columns > MAX_COLUMNS_TO_DISPLAY:
            message += f" (showing first {MAX_COLUMNS_TO_DISPLAY} for brevity)"

        note = "These columns will not be accessible in your model.\n\nFor the list of supported column types see: https://docs.relational.ai/api/cli/imports/stream/#supported-column-types"

        columns_text = "\n\n".join(table_sections)

        return textwrap.dedent(f"""
{message}

{columns_text}

{note}
""")

class QueryTimeoutExceededException(RAIException):
    def __init__(self, timeout_mins: int, query_id: str | None = None, config_file_path: str | None = None):
        self.timeout_mins = timeout_mins
        self.name = "Query Timeout Exceeded"
        self.message = f"Query execution time exceeded the specified timeout of {self.timeout_mins} minutes."
        self.query_id = query_id or ""
        self.config_file_path = config_file_path or ""
        self.content = self.format_message()
        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return textwrap.dedent(f"""
        Query execution time exceeded the specified timeout of {self.timeout_mins} minutes{f' for query with ID: {self.query_id}' if self.query_id else ''}.

        Consider increasing the 'query_timeout_mins' parameter in your configuration file{f' (stored in {self.config_file_path})' if self.config_file_path else ''} to allow more time for query execution.
        """)


#--------------------------------------------------
# Azure Exceptions
#--------------------------------------------------

class AzureUnsupportedQueryTimeoutException(RAIException):
    def __init__(self, config_file_path: str | None = None):
        self.message = "Query timeouts aren't supported on platform Azure."
        self.name = "Azure Unsupported Query Timeout Error"
        self.config_file_path = config_file_path or ""
        self.content = self.format_message()
        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return textwrap.dedent(f"""
        {self.message}

        Please remove the 'query_timeout_mins' from your configuration file{f' (stored in {self.config_file_path})' if self.config_file_path else ''} when running on platform Azure.
        """)

class AzureLegacyDependencyMissingException(RAIException):
    def __init__(self):
        self.message = "The Azure platform requires the 'legacy' extras to be installed."
        self.name = "Azure Legacy Dependency Missing"
        self.content = self.format_message()
        super().__init__(self.message, self.name, self.content)

    def format_message(self):
        return textwrap.dedent("""
        The Azure platform requires the 'rai-sdk' package, which is not installed.

        To use the Azure platform, please install the legacy extras:

            pip install relationalai[legacy]

        Or if upgrading an existing installation:

            pip install --upgrade relationalai[legacy]
        """)

