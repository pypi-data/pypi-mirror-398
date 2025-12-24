from __future__ import annotations


from . import StringValue, IntegerValue, strings, _function_not_implemented
from ..frontend.base import Library, Expression, Field, Variable
from ..frontend.core import Number, String, Integer
from enum import Enum

# the front-end library object
library = Library("re")

#--------------------------------------------------
# Relationships
#--------------------------------------------------

_regex_match_all = library.Relation("regex_match_all", [Field.input("regex", String), Field.input("value", String), Field("pos", Integer), Field("match", String)])
# _regex_replace = library.Relation("regex_replace", [Field.input("regex", String), Field.input("replacement", String), Field.input("value", String), Field("result", String)])

# _regex_escape = library.Relation("regex_escape", [Field.input("regex", String), Field("result", String)])
# _capture_group_by_index = library.Relation("capture_group_by_index", [Field.input("regex", String), Field.input("string", String), Field.input("pos", Integer), Field.input("index", Integer), Field("result", String)])
# _capture_group_by_name = library.Relation("capture_group_by_name", [Field.input("regex", String), Field.input("string", String), Field.input("pos", Integer), Field.input("name", String), Field("result", String)])


#--------------------------------------------------
# Operations
#--------------------------------------------------

#  match is ^{REGEX} , search is {REGEX}, and fullmatch is ^{REGEX}$

def match(regex: StringValue, value: StringValue) -> RegexMatch:
    """ Check if the regex matches the value from the start. """
    # REGEXP_LIKE
    return RegexMatch(regex, value, type=RegexMatchType.MATCH)

def search(regex: StringValue, value: StringValue, pos: IntegerValue = 0) -> RegexMatch:
    _function_not_implemented("re.search")
    return RegexMatch(regex, value, pos, type=RegexMatchType.SEARCH)

def fullmatch(regex: StringValue, value: StringValue, pos: IntegerValue = 0) -> RegexMatch:
    """ Check if the regex matches the entire value starting at the given position. """
    return RegexMatch(regex, value, pos, type=RegexMatchType.FULLMATCH)

def findall(regex: StringValue, value: StringValue) -> tuple[Variable, Variable]:
    """ Find all non-overlapping matches of the regex in the value. """
    _function_not_implemented("re.findall")
    # exp = _regex_match_all(regex, value)
    # ix, match = exp._arg_ref(2), exp._arg_ref(3)
    # rank = i.rank(i.asc(ix, match))
    # return rank, match
    raise

def sub(regex: StringValue, repl: StringValue, value: StringValue):
    """ Replace occurrences of the regex in the value with the replacement string. """
    _function_not_implemented("re.sub")
    # return _regex_replace(regex, repl, value)

class RegexMatchType(Enum):
    MATCH = "match"
    SEARCH = "search"
    FULLMATCH = "fullmatch"

class RegexMatch(Expression):

    def __init__(self, regex: StringValue, value: StringValue, pos: IntegerValue = 0, type=RegexMatchType.MATCH):
        if type == RegexMatchType.FULLMATCH:
            # fullmatch: ^{REGEX}$
            self.regex = strings.concat(regex, "$")
        else:
            self.regex = regex
        self.value = value
        # pos is the 0-based index in value where we start matching
        self.pos = pos
        # return value is the matched string
        self.match = String.ref("match")
        super().__init__(_regex_match_all, (self.regex, value, self.pos, self.match))

    def start(self) -> IntegerValue:
        return self.pos

    def end(self) -> IntegerValue:
        return strings.len(self.match) + self.pos - 1

    def span(self) -> tuple[IntegerValue, IntegerValue]:
        return self.start(), self.end()

    def group(self, index: IntegerValue = 0) -> Variable:
        _function_not_implemented("re.RegexMatch.group")
        raise

    def group_by_name(self, name: StringValue) -> Variable:
        _function_not_implemented("re.RegexMatch.group_by_name")
        raise

#--------------------------------------------------
# Helpers
#--------------------------------------------------

# def _regex_match_all(regex: StringValue, string: StringValue, pos: IntegerValue|None = None) -> i.Expression:
#     if pos is None:
#         pos = i.Int64.ref()
#     return _make_expr("regex_match_all", regex, string, pos, i.StringValue.ref())
