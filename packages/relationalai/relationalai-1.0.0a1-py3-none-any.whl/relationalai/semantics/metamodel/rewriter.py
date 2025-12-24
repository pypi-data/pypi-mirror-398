import keyword
from typing import Any, Callable, Dict, Type

from relationalai.util.structures import OrderedSet
from .metamodel import (
    Node, Model, NumberType, ScalarType, Task, Logical, Sequence, Union, Match, Until, Wait, Loop, Break, Require,
    Not, Exists, Lookup, Update, Aggregate, Construct, Var, Annotation, Field, Literal, UnionType, ListType, TupleType
)
import datetime as _dt

#------------------------------------------------------
# Constants
#------------------------------------------------------

_ATOMS = (str, int, float, bool, type(None), _dt.datetime)
NO_WALK = object()

WALK_FIELDS: Dict[Type[Node], tuple[str, ...]] = {
    # Top-level
    Model: ("root",),

    # Control flow
    Logical: ("body",),
    Sequence: ("tasks",),
    Union: ("tasks",),
    Match: ("tasks",),
    Until: ("check", "body",),
    Wait: ("check",),
    Loop: ("over", "body",),
    Break: ("check",),

    # Constraints / Quantifiers
    Require: ("domain", "check", "error"),
    Not: ("task",),
    Exists: ("vars", "task"),

    # Relation ops
    Lookup: ("args",),  # relation has no tasks/vars; args is ISeq[Value]
    Update: ("args",),
    Aggregate: ("projection", "group", "args", "body"),
    Construct: ("values", "id_var"),

    # Annotations can contain Values which can contain Vars
    Annotation: ("args",),

    # Var: no children, but we include it so enter_var/var() can run
    Var: (),
    Field: (),
    Literal: (),
    ScalarType: (),
    NumberType: (),
    UnionType: (),
    ListType: (),
    TupleType: (),
}

#------------------------------------------------------
# Walker
#------------------------------------------------------

class Walker:
    visits = 0
    _walkers: Dict[Type[Node], Callable] = {}
    __slots__ = ("_seen_ids",)

    def __init__(self):
        # ids of nodes on the current recursion path (for cycle detection)
        self._seen_ids: set[int] = set()

    def __call__(self, obj):
        self._seen_ids.clear()
        try:
            self._walk(obj)
        except StopIteration:
            pass
        return obj

    def _walk(self, x):
        if isinstance(x, Node):
            return self._visit_node(x)
        if isinstance(x, _ATOMS):
            return x
        if isinstance(x, (tuple, list, OrderedSet)):
            for v in x:
                self._walk(v)
            return x
        if isinstance(x, dict):
            for v in x.values():
                self._walk(v)
            return x
        return x

    def _visit_node(self, node: Node):
        nid = id(node)
        if nid in self._seen_ids:  # cycle guard by identity
            return node

        Walker.visits += 1
        self._seen_ids.add(nid)

        cls = type(node)
        self._walkers[cls](self, node)

        if nid in self._seen_ids:
            self._seen_ids.remove(nid)
        return node

    def stop(self):
        raise StopIteration()

    #------------------------------------------------------
    # Generate walkers
    #------------------------------------------------------

    @classmethod
    def generate_walkers(cls):
        dispatch: Dict[Type[Node], Callable] = {}

        for node in WALK_FIELDS.keys():
            base_name = node.__name__.lower()
            enter_name = f"enter_{base_name}"
            exit_name = base_name if not keyword.iskeyword(base_name) else f"{base_name}_"

            # default no-op enter handler
            def _no_op(self, node):
                return None
            setattr(cls, enter_name, _no_op)
            setattr(cls, exit_name, _no_op)

            # Generate the per-class walker via exec for speed
            ns = {"NO_WALK": NO_WALK}
            lines =      ["def walker(self, node):"]
            lines.append(f"    no_walk = self.{enter_name}(node)")
            lines.append(f"    if no_walk is not NO_WALK:")
            lines.extend(f"        self._walk(node.{fld})" for fld in WALK_FIELDS.get(node, ()))
            lines.append(f"        self.{exit_name}(node)")
            exec("\n".join(lines), ns)
            dispatch[node] = ns["walker"] # type: ignore

        cls._walkers = dispatch

Walker.generate_walkers()

#------------------------------------------------------
# Rewriter
#------------------------------------------------------

class Rewriter:
    _rewriters: Dict[Type[Node], Callable] = {}
    __slots__ = ("_seen_ids", "_memo")

    def __init__(self):
        # ids of nodes on the current recursion path (for cycle detection)
        self._seen_ids: set[int] = set()
        # id(node) -> rewritten node
        self._memo: Dict[int, Node] = {}

    def __call__(self, obj):
        self._seen_ids.clear()
        self._memo.clear()
        return self._rewrite(obj)

    def _rewrite(self, x):
        if isinstance(x, Node):
            return self._rewrite_node(x)
        if isinstance(x, _ATOMS):
            return x
        if isinstance(x, (tuple, list)):
            seq_out: list[Any] = []
            changed = False
            for v in x:
                nv = self._rewrite(v)
                if nv is not v:
                    changed = True
                seq_out.append(nv)
            if not changed:
                return x
            return tuple(seq_out) if isinstance(x, tuple) else seq_out
        if isinstance(x, dict):
            out: Dict[Any, Any] = {}
            changed = False
            for k, v in x.items():
                nv = self._rewrite(v)
                if nv is not v:
                    changed = True
                out[k] = nv
            if not changed:
                return x
            return out
        return x

    def _rewrite_node(self, node: Node):
        nid = id(node)

        # If we've already rewritten this exact node, reuse the result.
        rewritten = self._memo.get(nid)
        if rewritten is not None:
            return rewritten

        # Cycle guard by identity for pathological graphs.
        if nid in self._seen_ids:
            return node

        self._seen_ids.add(nid)
        cls = type(node)
        rewriter = self._rewriters[cls]
        new = rewriter(self, node)
        self._seen_ids.remove(nid)

        self._memo[nid] = new
        return new

    #------------------------------------------------------
    # Generate rewriters
    #------------------------------------------------------

    @classmethod
    def generate_rewriters(cls):
        dispatch: Dict[Type[Node], Callable] = {}

        for node in WALK_FIELDS.keys():
            base_name = node.__name__.lower()
            enter_name = f"enter_{base_name}"
            exit_name = base_name if not keyword.iskeyword(base_name) else f"{base_name}_"

            # default handlers: return None => "no replacement"
            def _no_op(self, nd):
                return None
            setattr(cls, enter_name, _no_op)
            setattr(cls, exit_name, _no_op)

            fields = WALK_FIELDS.get(node, ())

            ns: Dict[str, Any] = {}
            lines: list[str] = []

            # def rewriter(self, node):
            lines.append("def rewriter(self, node):")
            lines.append("    new = node")

            # pre-order hook: enter_<name>(node) -> optional replacement
            lines.append(f"    tmp = self.{enter_name}(node)")
            lines.append(f"    if tmp is not None and tmp is not node:")
            lines.append(f"        new = tmp")
            # rewrite children in WALK_FIELDS, track changes
            lines.extend(f"    v_{fld} = self._rewrite(new.{fld})" for fld in fields)

            if fields:
                cond = " or ".join(f"v_{fld} is not new.{fld}" for fld in fields)
                kwargs = ", ".join(f"{fld}=v_{fld}" for fld in fields)
                lines.append(f"    if {cond}:")
                lines.append(f"        new = new.mut({kwargs})")

            # post-order hook: <name>(node) -> optional replacement
            lines.append(f"    tmp = self.{exit_name}(new)")
            lines.append(f"    if tmp is not None and tmp is not new:")
            lines.append(f"        new = tmp")

            lines.append("    return new")

            exec("\n".join(lines), {}, ns)
            dispatch[node] = ns["rewriter"]

        cls._rewriters = dispatch

Rewriter.generate_rewriters()
