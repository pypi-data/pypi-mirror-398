from __future__ import annotations
import ast
from dataclasses import dataclass, field
from functools import lru_cache
import os
import sys
import textwrap
import dis
from bisect import bisect_right
from types import CodeType

cwd = os.getcwd()

#------------------------------------------------------
# Path utilities
#------------------------------------------------------

# relpath is a shockingly slow operation, so caching it
@lru_cache(maxsize=128)
def relative_path(path: str) -> str:
    try:
        return os.path.relpath(path, cwd)
    except ValueError:
        return path

#------------------------------------------------------
# Frame utilities
#------------------------------------------------------

_line_map_cache = {}

def instruction_line(code, lasti):
    pairs = _line_map_cache.get(code)
    if pairs is None:
        pairs = list(dis.findlinestarts(code))  # (addr, line_number)
        _line_map_cache[code] = pairs

    idx = bisect_right(pairs, (lasti, float("inf"))) - 1
    if idx < 0:
        return code.co_firstlineno
    return pairs[idx][1]

def first_non_relationalai_frame():
    frame = sys._getframe(2)  # skip this function and the previous one
    while frame and frame.f_back:
        mod_name = frame.f_globals.get("__name__", "")
        if mod_name.startswith("relationalai") or mod_name.startswith("v0.relationalai"):
            frame = frame.f_back
            continue
        return frame
    return frame

#------------------------------------------------------
# Source utilities
#------------------------------------------------------

@lru_cache(maxsize=128)
def get_source_code(filename: str) -> str|None:
    """Get the source code of a file."""
    try:
        with open(filename, "r") as f:
            return f.read()
    except Exception:
        return None

parses = {}
def find_root_expression(source_code: str, target_line: int, relative_filename: str):
    # Parse the source code into an AST
    if relative_filename not in parses:
        parses[relative_filename] = ast.parse(source_code)
    tree = parses[relative_filename]

    class ExpressionChainFinder(ast.NodeVisitor):
        def __init__(self, target_line):
            self.target_line = target_line
            self.candidates = []

        def visit(self, node):
            # Consider all expression nodes, including Call nodes
            is_expr_node = isinstance(node, (ast.Expr, ast.Call, ast.Attribute, ast.BinOp,
                                          ast.UnaryOp, ast.IfExp, ast.Compare, ast.Subscript,
                                          ast.Dict, ast.List, ast.Tuple, ast.Set))

            if hasattr(node, "lineno") and is_expr_node:
                end_lineno = getattr(node, "end_lineno", node.lineno)

                # Check if this node contains our target line
                if node.lineno <= self.target_line <= end_lineno:
                    # Store the node with its line span information
                    self.candidates.append((node, node.lineno, end_lineno))

            # Continue visiting children
            for child in ast.iter_child_nodes(node):
                self.visit(child)

    finder = ExpressionChainFinder(target_line)
    finder.visit(tree)

    if finder.candidates:
        # Sort candidates by their starting line (ascending) and then by span size (descending)
        # This prioritizes expressions that start earlier and cover more lines
        sorted_candidates = sorted(finder.candidates,
                                  key=lambda x: (x[1], -(x[2] - x[1])))

        # Find the outermost expression that contains our target line
        # This will capture the entire multi-line function call
        outermost_candidates = []
        for node, start_line, end_line in sorted_candidates:
            # Check if this is a new candidate or extends an existing one
            if not outermost_candidates or start_line < outermost_candidates[0][1]:
                outermost_candidates = [(node, start_line, end_line)]

            # If we have a node that starts at the same line but ends later, prefer it
            elif start_line == outermost_candidates[0][1] and end_line > outermost_candidates[0][2]:
                outermost_candidates = [(node, start_line, end_line)]

        if outermost_candidates:
            node, start_line, end_line = outermost_candidates[0]

            # Extract the lines from the source code
            block_lines = source_code.splitlines()[start_line - 1:end_line]
            block_code = "\n".join(block_lines)
            return SourcePos(relative_filename, _line=start_line, _source=textwrap.dedent(block_code))

    # If no nodes were found, return the single line
    lines = source_code.splitlines()
    if target_line > len(lines):
        return SourcePos(relative_filename, _line=target_line)
    return SourcePos(relative_filename, _line=target_line, _source=lines[target_line - 1])

#------------------------------------------------------
# SourcePos
#------------------------------------------------------

counts = 0

@dataclass(slots=True)
class SourcePos:
    file: str = field(default="Unknown")
    _block:SourcePos|None = None
    _lasti: int|None = field(default=0)
    _pycode: CodeType|None = field(default=None)
    _source: str|None = field(default=None)
    _line: int|None = field(default=None)

    @classmethod
    def new(cls):
        caller_frame = first_non_relationalai_frame()
        if not caller_frame:
            return cls()

        filename = caller_frame.f_code.co_filename
        lasti = caller_frame.f_lasti
        pycode = caller_frame.f_code

        return cls(filename, _lasti=lasti, _pycode=pycode)

    @property
    def line(self):
        if self._line is None and self._pycode:
            self._line = instruction_line(self._pycode, self._lasti)
        return self._line or 0

    @property
    def source(self):
        if self._source is None and self.file:
            self._source = get_source_code(self.file)
        return self._source or ""

    @property
    def block(self):
        if not self.source or not self.line:
            return SourcePos()
        if not self._block:
            self._block = find_root_expression(self.source, self.line, self.file)
        return self._block

    def transform(self, transformer:ast.NodeTransformer) -> SourcePos|None:
        if not self.block or not self.block.source:
            return

        new_ast = transformer.visit(ast.parse(self.block.source))
        new_source = ast.unparse(new_ast)
        new = SourcePos(self.file, _line=self.line, _source=new_source)
        return new
