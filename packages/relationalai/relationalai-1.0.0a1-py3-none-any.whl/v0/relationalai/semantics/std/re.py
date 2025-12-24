from __future__ import annotations

from v0.relationalai.semantics.internal import internal as i
from v0.relationalai.semantics.metamodel.util import OrderedSet
from .std import _Integer, _String, _make_expr
from typing import Literal, Any
from .. import std


def escape(regex: _String) -> i.Expression:
    return _make_expr("escape_regex_metachars", regex, i.String.ref())

class Match(i.Producer):

    def __init__(self, regex: _String, string: _String, pos: _Integer = 0, _type: Literal["search", "fullmatch", "match"] = "match"):
        super().__init__(i.find_model([regex, string, pos]))
        self.regex = regex
        self.string = string
        self.pos = pos

        if _type == "match":
            self._expr = _regex_match_all(self.regex, self.string, std.cast_to_int64(self.pos + 1))
            self._offset, self._full_match = self._expr._arg_ref(2), self._expr._arg_ref(3)
        elif _type == "search":
            raise NotImplementedError("`search` is not implemented")
        elif _type == "fullmatch":
            _exp = _regex_match_all(self.regex, self.string, std.cast_to_int64(self.pos + 1))
            self._offset, self._full_match = _exp._arg_ref(2), _exp._arg_ref(3)
            self._expr = self._full_match == std.strings.substring(self.string, std.cast_to_int64(self.pos), std.strings.len(self.string))

    def group(self, index: _Integer = 0) -> i.Producer:
        if index == 0:
            return self._full_match
        else:
            return _make_expr("capture_group_by_index", self.regex, self.string, std.cast_to_int64(self.pos + 1), std.cast_to_int64(index), i.String.ref("res"))

    def group_by_name(self, name: _String) -> i.Producer:
        return _make_expr("capture_group_by_name", self.regex, self.string, std.cast_to_int64(self.pos + 1), name, i.String.ref("res"))

    def start(self) -> i.Expression:
        return self._offset - 1

    def end(self) -> i.Expression:
        return std.strings.len(self.group(0)) + self.start() - 1

    def span(self) -> tuple[i.Producer, i.Producer]:
        return self.start(), self.end()

    def _to_keys(self) -> OrderedSet[Any]:
        return i.find_keys(self._expr)

    def _compile_lookup(self, compiler:i.Compiler, ctx:i.CompilerContext):
        compiler.lookup(self.regex, ctx)
        compiler.lookup(self.string, ctx)
        compiler.lookup(self.pos, ctx)
        return compiler.lookup(self._expr, ctx)

    def __getattr__(self, name: str) -> Any:
        return object.__getattribute__(self, name)

    def __setattr__(self, name: str, value: Any) -> None:
        object.__setattr__(self, name, value)


def match(regex: _String, string: _String) -> Match:
    return Match(regex, string)

def search(regex: _String, string: _String, pos: _Integer = 0) -> Match:
    return Match(regex, string, pos, _type="search")

def fullmatch(regex: _String, string: _String, pos: _Integer = 0) -> Match:
    return Match(regex, string, pos, _type="fullmatch")

def findall(regex: _String, string: _String) -> tuple[i.Producer, i.Producer]:
    exp = _regex_match_all(regex, string)
    ix, match = exp._arg_ref(2), exp._arg_ref(3)
    rank = i.rank(i.asc(ix, match))
    return rank, match

def _regex_match_all(regex: _String, string: _String, pos: _Integer|None = None) -> i.Expression:
    if pos is None:
        pos = i.Int64.ref()
    return _make_expr("regex_match_all", regex, string, pos, i.String.ref())