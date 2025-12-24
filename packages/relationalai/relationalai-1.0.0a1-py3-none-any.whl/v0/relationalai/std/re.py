from __future__ import annotations
from typing import Union

from .. import dsl, std, errors, metamodel as m


# Custom types
_String = Union[str, dsl.Producer]
_Integer = Union[int, dsl.Producer]

def escape(regex: _String) -> dsl.Expression:
    return dsl.rel.escape_regex_metachars(regex)

dsl.tag(dsl.rel.pyrel_regex_match, m.Builtins.Filter)
dsl.tag(dsl.rel.pyrel_regex_search, m.Builtins.Filter)
dsl.tag(dsl.rel.regex_compile, m.Builtins.Expensive)
dsl.tag(dsl.rel.num_chars, m.Builtins.SingleValued)

class Pattern:
    def __init__(self, graph: dsl.Graph, regex: _String):
        self._graph = graph
        self.pattern = regex
        with graph.rule():
            dsl.rel.__compiled_patterns.add(regex, dsl.rel.regex_compile(regex))

    @property
    def _compiled(self):
        return dsl.rel.__compiled_patterns(self.pattern)

    def match(self, string: _String, pos: _Integer = 0) -> Match:
        return Match(self._graph, self._compiled, string, pos)

    def search(self, string: _String, pos: _Integer = 0) -> Match:
        return Match(self._graph, self._compiled, string, pos, _how="search")

    def fullmatch(self, string: _String, pos: _Integer = 0) -> Match:
        return Match(self._graph, self._compiled, string, pos, _how="fullmatch")

    def findall(self, string: _String) -> tuple[dsl.Producer, dsl.Producer]:
        return findall(self.pattern, string)

    def sub(self, repl: _String, string: _String) -> dsl.Expression:
        # NOTE: self.pattern must be used here instead of self._compiled
        # because the compiled pattern throws an FFIException.
        return sub(self.pattern, repl, string)

    def _to_var(self):
        raise errors.NonVarObject(self, "Pattern objects cannot be used as variables")


def compile(regex: _String) -> Pattern:
    return Pattern(dsl.get_graph(), regex)


class Match(dsl.Producer):
    def __init__(self, graph:dsl.Graph, regex: Pattern | _String, string: _String, pos: _Integer = 0, _how: str = "match"):
        super().__init__(graph)
        if isinstance(regex, Pattern):
            self.re = regex._compiled
        else:
            self.re = dsl.rel.regex_compile(regex)
        self.string = string
        self.pos = pos
        self._how = _how
        self._fullmatch = dsl.create_var()
        self._start = dsl.create_var()
        if self._how == "match":
            dsl.rel.pyrel_regex_match(self.re, self.string, self.pos + 1, self._start, self._fullmatch)
        elif self._how == "search":
            dsl.rel.pyrel_regex_search(self.re, self.string, self.pos + 1, self._start, self._fullmatch)
        elif self._how == "fullmatch":
            dsl.rel.pyrel_regex_match(self.re, self.string, self.pos + 1, self._start, self._fullmatch)
            self._fullmatch == dsl.rel.substring(self.string, self.pos + 1, dsl.rel.num_chars(self.string))
        else:
            raise ValueError(f"Invalid match type: {self._how!r}")

    def group(self, index: _Integer | _String = 0) -> dsl.Instance:
        if index == 0:
            return self._fullmatch
        else:
            return dsl.rel.pyrel_capture_group(self.re, self.string, self.pos + 1, index)

    def start(self) -> dsl.Expression:
        return self._start - 1

    def end(self) -> dsl.Expression:
        return dsl.rel.num_chars(self._fullmatch) + self._start - 1

    def span(self) -> tuple[dsl.Producer, dsl.Producer]:
        return self.start(), self.end()

    def __getitem__(self, index: _Integer | _String) -> dsl.Instance:
        return self.group(index)

    def _to_var(self):
        return self.group()


def match(regex: _String, string: _String) -> Match:
    return Match(dsl.get_graph(), regex, string)


def search(regex: _String, string: _String) -> Match:
    return Match(dsl.get_graph(), regex, string, _how="search")


def fullmatch(regex: _String, string: _String) -> Match:
    return Match(dsl.get_graph(), regex, string, _how="fullmatch")


def findall(regex: _String, string: _String) -> tuple[dsl.Producer, dsl.Producer]:
    ix, match = dsl.create_vars(2)
    dsl.rel.regex_match_all(regex, string, ix, match)
    rank = std.aggregates.rank_asc(ix, match, per=[string])
    return rank, match


def sub(regex: _String, repl: _String, string: _String) -> dsl.Expression:
    return dsl.rel.pyrel_regex_sub(regex, repl, string)


__all__ = [
    "compile",
    "escape",
    "findall",
    "fullmatch",
    "match",
    "search",
    "sub",
]
