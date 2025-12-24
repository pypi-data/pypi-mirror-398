# pretty.py

from __future__ import annotations
from typing import Any, Iterable

from .base import *

#------------------------------------------------------
# Utility helpers
#------------------------------------------------------

def _is_multiline(s: str) -> bool:
    return "\n" in s

def _indent(s: str, level: int, unit: str) -> str:
    pad = unit * level
    return "\n".join(pad + line if line else pad for line in s.splitlines())

def _join_inline(parts: Iterable[str]) -> str:
    return ", ".join(parts)

_BUILTIN_LABEL_OVERRIDES: dict[str, str] = {
}

def _relationship_label(rel: Relationship, *, include_owner: bool = True) -> str:
    short = getattr(rel, "_short_name", "")
    if short:
        model = getattr(rel, "_model", None)
        model_name = getattr(model, "name", "")
        if model_name == "Builtins":
            return _BUILTIN_LABEL_OVERRIDES.get(short, short)
        if not include_owner:
            return short
        fields = getattr(rel, "_fields", [])
        if fields:
            owner = fields[0].type
            owner_name = getattr(owner, "_name", None)
            if owner_name:
                return f"{owner_name}.{short}"
        return short
    reading = getattr(rel, "_reading", "")
    if reading:
        return reading
    readings = getattr(rel, "_readings", None)
    if readings:
        return readings[0]._reading
    return ""

def _block(name: str, body_lines: list[str], level: int, unit: str, max_inline_len: int | None = None) -> str:
    """
    Renders:
    (name
      line1
      line2)
    """
    if not body_lines:
        return ""
    if (
        max_inline_len is not None
        and len(body_lines) == 1
        and not _is_multiline(body_lines[0])
    ):
        inline_form = f"({name} {body_lines[0]})"
        if len(inline_form) <= max_inline_len:
            return inline_form
    head = f"({name}"
    inner_lines = [_indent(line, 1, unit) for line in body_lines]
    if inner_lines:
        inner_lines[-1] = f"{inner_lines[-1]})"
    return "\n".join([head] + inner_lines)

#------------------------------------------------------
# The Pretty Printer
#------------------------------------------------------

class PrettyPrinter:
    def __init__(
        self,
        indent_unit: str = "  ",
        max_inline_len: int = 80,
        inline_args_threshold: int = 3,
    ):
        self.indent_unit = indent_unit
        self.max_inline_len = max_inline_len
        self.inline_args_threshold = inline_args_threshold
        # cache already-rendered nodes (protects against cycles / re-visits)
        self._seen = {}

    # Public entrypoint
    def format(self, obj: Any, level: int = 0) -> str:
        key = (id(obj), level)
        if key in self._seen:
            return self._seen[key]

        # dynamic single-dispatch
        meth = None
        for cls in type(obj).__mro__:
            meth = getattr(self, f"_fmt_{cls.__name__}", None)
            if meth:
                break
        if meth is None:
            # Fallback: plain str/repr
            out = str(obj)
            self._seen[key] = out
            return out

        out = meth(obj, level)
        self._seen[key] = out
        return out

    #------------------------------------------------------
    # Leaf-ish nodes
    #------------------------------------------------------

    def _fmt_Concept(self, c: Concept, level: int) -> str:
        return c._name

    def _fmt_Table(self, t: Table, level: int) -> str:
        return t._name  # Table inherits Concept; Chain lives in _name

    def _fmt_Literal(self, lit: Literal, level: int) -> str:
        # lit.__str__ is fine, but we bypass it to avoid nested old-printers
        v = lit._value
        return repr(v)

    def _fmt_Alias(self, a: Alias, level: int) -> str:
        src = self.format(a._source, level)
        return f"{src} AS {a._alias}"

    def _fmt_FieldRef(self, fr: FieldRef, level: int) -> str:
        src = self.format(fr._root, level)
        # render the key as given by the user (str|int|Concept)
        if isinstance(fr._field, (int,)):
            key = f"{fr._field}"
        elif hasattr(fr._field, "_name"):
            key = getattr(fr._field, "_name")
        else:
            key = str(fr._field)
        return f"{src}[{key}]"

    def _fmt_Ref(self, ref: Ref, level: int) -> str:
        concept = getattr(ref, "_concept", None)
        if concept is None:
            return "<ref>"
        concept_label = self.format(concept, level) if isinstance(concept, Variable) else str(concept)
        return f"{concept_label}.ref"

    def _fmt_DerivedColumn(self, col: DerivedColumn, level: int) -> str:
        if col._name:
            return col._name  # user-provided alias

        table = col._table
        index = col._index

        if table is not None and isinstance(index, int):
            if isinstance(table, Fragment):
                source_values = table._select
                if isinstance(source_values, (list, tuple)) and 0 <= index < len(source_values):
                    return self.format(source_values[index], level)
            table_label = table.__class__.__name__
            return f"{table_label}[{index}]"

        return f"col{index}" if index is not None else "<col>"

    #------------------------------------------------------
    # Relationship / Reading
    #------------------------------------------------------

    def _fmt_Field(self, f: Field, level: int) -> str:
        t = self.format(f.type, level)
        return f"{f.name}:{t}"

    def _fmt_Relationship(self, r: Relationship, level: int) -> str:
        label = _relationship_label(r)
        if label:
            return label
        fields = ", ".join(self._fmt_Field(f, level) for f in r._fields)
        return f"rel({fields})"

    def _fmt_Reading(self, rd: Reading, level: int) -> str:
        label = _relationship_label(rd)
        if label:
            return label
        return rd._reading

    #------------------------------------------------------
    # Chains & Expressions
    #------------------------------------------------------

    def _fmt_Chain(self, p: Chain, level: int) -> str:
        start = self.format(p._start, level)
        nxt = _relationship_label(p._next, include_owner=False)
        if not nxt:
            nxt = self.format(p._next, level)
        return f"{start}.{nxt}"

    def _fmt_New(self, new: New, level: int) -> str:
        concept_label = self.format(new._op, level)
        op = f"{concept_label}.new"
        if new._identity_only:
            op += "_identity"
        arg_strs = [self.format(a, level) for a in new._args]
        kw_strs = [f"{k}={self.format(v, level)}" for k, v in (new._kwargs or {}).items()]
        parts = arg_strs + kw_strs

        if not parts:
            return op

        unit = self.indent_unit
        inline_pieces = [op] + parts
        inline_str = " ".join(inline_pieces)
        if (
            len(parts) <= self.inline_args_threshold
            and len(inline_str) + 2 <= self.max_inline_len
            and not any(_is_multiline(p) for p in parts)
        ):
            return f"({inline_str})"

        return _block(op, parts, level, unit, self.max_inline_len)

    def _fmt_Expression(self, e: Expression, level: int) -> str:
        op = self.format(e._op, level)
        # Prepare args/kwargs strings
        args = list(e._args)
        if isinstance(e._op, (Relationship, Reading)) and args:
            fields: list[Field] = getattr(e._op, "_fields", [])
            if fields:
                owner = fields[0].type
                if args and args[0] is owner:
                    args = args[1:]
        arg_strs = [self.format(a, level) for a in args]
        kw_strs = [f"{k}={self.format(v, level)}" for k, v in (e._kwargs or {}).items()]
        parts = arg_strs + kw_strs

        # No-arg expressions: treat as bare operator name
        if not parts:
            return op

        unit = self.indent_unit
        inline_pieces = [op] + parts
        inline_str = " ".join(inline_pieces)
        if (
            len(parts) <= self.inline_args_threshold
            and len(inline_str) + 2 <= self.max_inline_len
            and not any(_is_multiline(p) for p in parts)
        ):
            return f"({inline_str})"

        return _block(op, parts, level, unit, self.max_inline_len)

    #------------------------------------------------------
    # Match, Union, Not, Distinct
    #------------------------------------------------------

    def _fmt_Match(self, m: Match, level: int) -> str:
        unit = self.indent_unit
        items = [self.format(it, level + 1) for it in m._items]
        # inline if small & single-line
        inline = " | ".join(items)
        if len(inline) <= self.max_inline_len and all(not _is_multiline(s) for s in items):
            return f"(match {inline})"
        body = [s for s in items]
        return _block("match", body, level, unit)

    def _fmt_Union(self, u: Union, level: int) -> str:
        unit = self.indent_unit
        items = [self.format(it, level + 1) for it in u._items]
        inline = " & ".join(items)
        if len(inline) <= self.max_inline_len and all(not _is_multiline(s) for s in items):
            return f"(union {inline})"
        body = [s for s in items]
        return _block("union", body, level, unit)

    def _fmt_Not(self, n: Not, level: int) -> str:
        unit = self.indent_unit
        items = [self.format(it, level + 1) for it in n._items]
        inline = _join_inline(items)
        if len(inline) <= self.max_inline_len and all(not _is_multiline(s) for s in items):
            return f"(not {inline})"
        return _block("not", items, level, unit)

    def _fmt_Distinct(self, d: Distinct, level: int) -> str:
        unit = self.indent_unit
        items = [self.format(it, level + 1) for it in d._items]
        inline = _join_inline(items)
        if len(inline) <= self.max_inline_len and all(not _is_multiline(s) for s in items):
            return f"(distinct {inline})"
        return _block("distinct", items, level, unit)

    def _fmt_Group(self, group: Group, level: int) -> str:
        unit = self.indent_unit
        items = [self.format(it, level + 1) for it in group._args]
        if not items:
            return "(group)"
        inline = _join_inline(items)
        if len(inline) <= self.max_inline_len and all(not _is_multiline(s) for s in items):
            return f"(group {inline})"
        return _block("group", items, level, unit)

    def _fmt_Aggregate(self, agg: Aggregate, level: int) -> str:
        unit = self.indent_unit

        op_label = _relationship_label(agg._op, include_owner=False)
        if not op_label:
            op_label = self.format(agg._op, level)

        parts: list[str] = [self.format(arg, level + 1) for arg in agg._args]

        group_args = getattr(agg._group, "_args", [])
        if group_args:
            pretty_group = [self.format(x, level + 1) for x in group_args]
            inline = _join_inline(pretty_group)
            if len(inline) <= self.max_inline_len and all(not _is_multiline(s) for s in pretty_group):
                parts.append(f"(per {inline})")
            else:
                parts.append(_block("per", pretty_group, level, unit, self.max_inline_len))

        where_fragment = agg._where
        if where_fragment is not None:
            where_items = where_fragment._where
            if where_items:
                pretty_where = [self.format(x, level + 1) for x in where_items]
                inline = _join_inline(pretty_where)
                if len(inline) <= self.max_inline_len and all(not _is_multiline(s) for s in pretty_where):
                    parts.append(f"(where {inline})")
                else:
                    parts.append(_block("where", pretty_where, level, unit, self.max_inline_len))

        if not parts:
            return op_label

        inline_pieces = [op_label] + parts
        inline_str = " ".join(inline_pieces)
        if (
            len(parts) <= self.inline_args_threshold
            and len(inline_str) + 2 <= self.max_inline_len
            and not any(_is_multiline(p) for p in parts)
        ):
            return f"({inline_str})"

        return _block(op_label, parts, level, unit, self.max_inline_len)

    #------------------------------------------------------
    # Fragment
    #------------------------------------------------------

    def _fmt_Fragment(self, f: Fragment, level: int) -> str:
        """
        Renders (select ...)\n(where ...)\n(require ...)\n(then ...)\n(order_by ...)\n(limit N)
        Omit empty sections. Properly indents nested structures.
        """
        unit = self.indent_unit
        sections: list[str] = []

        def _fmt_list(name: str, items: list[Any]) -> None:
            if not items:
                return
            pretty_items = [self.format(x, level + 1) for x in items]
            # force multiline block semantics for Fragment sections
            sections.append(_block(name, pretty_items, level, unit, self.max_inline_len))

        _fmt_list("select", f._select)
        _fmt_list("require", f._require)
        _fmt_list("define",   f._define)
        _fmt_list("where", f._where)
        if f._order_by:
            # order_by: allow inline if all single-line and short
            pretty_items = [self.format(x, level + 1) for x in f._order_by]
            inline = _join_inline(pretty_items)
            if len(inline) <= self.max_inline_len and all(not _is_multiline(s) for s in pretty_items):
                sections.append(_indent(f"(order_by {inline})", level, unit))
            else:
                sections.append(_block("order_by", pretty_items, level, unit, self.max_inline_len))
        if getattr(f, "_limit", 0):
            sections.append(_indent(f"(limit {f._limit})", level, unit))

        sections = [s for s in sections if s]
        if not sections:
            return "(fragment)"
        return _block("fragment", sections, level, unit, self.max_inline_len)

    #------------------------------------------------------
    # Fallbacks for generic nodes
    #------------------------------------------------------

    def _fmt_Variable(self, v: Variable, level: int) -> str:
        # For unknown Variable subtypes, fall back to a safe identity-ish string
        # You can specialize more types above as needed.
        cls = v.__class__.__name__
        return f"<{cls} #{id(v):x}>"

#------------------------------------------------------
# Convenience API
#------------------------------------------------------

def format(obj: Any, **opts) -> str:
    """
    Pretty-format any DSL object.
    Example: print(format(fragment))
    """
    return PrettyPrinter(**opts).format(obj)

def pprint(obj: Any, **opts):
    """
    Pretty-print any DSL object.
    Example: print(pp(fragment))
    """
    print(format(obj, **opts))
