from typing import Optional, Iterable, List, Sequence as _Sequence
from dataclasses import dataclass, field

from .metamodel import *
import datetime as _dt
from ...util.dataclasses import print_tree as print_dataclass_tree
from ...util.naming import NameCache

#------------------------------------------------------
# pprint
#------------------------------------------------------

_INDENT = "    "
_DERIVE_ARROW = "→"
VERBOSE = False
# VERBOSE = True

def _indent_line(indent: int, text: str) -> str:
        return f"{_INDENT * indent}{text}"

@dataclass(frozen=True)
class Printer():
    """Pretty Printer for Metamodel Nodes"""
    name_cache: NameCache = field(default_factory=NameCache)

    def format_type(self, type_: Type, include_supertypes: bool = False) -> str:
        if type_ is None:
            return ""
        if isinstance(type_, ScalarType):
            if include_supertypes and type_.super_types:
                supertypes = ", ".join(
                    self.format_type(t, include_supertypes=True) for t in type_.super_types
                )
                return f"{type_.name or 'Scalar'} < {supertypes}" if supertypes else (type_.name or "Scalar")
            else:
                return type_.name or "Scalar"
        if isinstance(type_, UnionType):
            inner = [name for name in (self.format_type(t) for t in type_.types) if name]
            joined = " | ".join(inner)
            return joined or "Union"
        if isinstance(type_, ListType):
            inner = self.format_type(type_.element_type)
            return f"List[{inner}]" if inner else "List"
        if isinstance(type_, TypeNode):
            return type_.__class__.__name__
        return str(type_)

    def primitive(self, value: Primitive) -> str:
        if value is None:
            return "None"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str):
            escaped = value.replace("\"", "\\\"")
            return f'"{escaped}"'
        if isinstance(value, _dt.datetime):
            return value.isoformat()
        return str(value)

    def var(self, var: Var) -> str:
        name = var.name or f"var_{var.id}"
        name = self.name_cache.get_name(var.id, name)
        type_name = self.format_type(var.type)
        return f"{name}::{type_name}" if type_name else name

    def literal(self, literal: Literal) -> str:
        value = self.primitive(literal.value)
        type_name = self.format_type(literal.type)
        return f"{value}::{type_name}" if type_name else value

    def binding(self, binding: Var) -> str:
        return self.var(binding)

    def relation(self, relation: Relation) -> str:
        name = relation.name or f"Relation#{relation.id}"
        if VERBOSE:
            fields = ", ".join(
                f"{field.name or field.id}::{self.format_type(field.type)}"
                for field in relation.fields
            )
            return f"{name}[{fields}]"
        else:
            return name

    def capability_str(self, capability: Capability) -> str:
        return capability.name or f"Capability#{capability.id}"

    def reasoner_str(self, reasoner: Reasoner) -> str:
        name = reasoner.type or f"Reasoner#{reasoner.id}"
        suffix_parts: List[str] = []
        if reasoner.capabilities:
            suffix_parts.append(
                "capabilities[" + ", ".join(self.capability_str(cap) for cap in reasoner.capabilities) + "]"
            )
        if reasoner.relations:
            suffix_parts.append(
                "relations[" + ", ".join(self.relation(rel) for rel in reasoner.relations) + "]"
            )
        if reasoner.info is not None:
            suffix_parts.append(f"info={reasoner.info!r}")
        if suffix_parts:
            return f"{name} " + " ".join(suffix_parts)
        return name

    def value(self, val: Value) -> str:
        if isinstance(val, Var):
            return self.var(val)
        if isinstance(val, Literal):
            return self.literal(val)
        if isinstance(val, Relation):
            return self.relation(val)
        if isinstance(val, TypeNode):
            return self.format_type(val)
        if isinstance(val, Field):
            return f"{val._relation.name}.{val.name or val.id}"
        if isinstance(val, list):
            return "[" + ", ".join(self.value(v) for v in val) + "]"
        if isinstance(val, tuple):
            return "(" + ", ".join(self.value(v) for v in val) + ")"
        if isinstance(val, bool):
            return "true" if val else "false"
        if val is None:
            return "None"
        return str(val)


    def annotation(self, annotation: Annotation) -> str:
        name = self.relation(annotation.relation)
        if not annotation.args:
            return f"@{name}"
        args = ", ".join(self.value(arg) for arg in annotation.args)
        return f"@{name}({args})"


    def header(
        self,
        name: str,
        *,
        annotations: Optional[_Sequence[Annotation]] = None,
        suffix: str = "",
    ) -> str:
        parts = [name]
        if suffix:
            parts.append(suffix)
        head = " ".join(part for part in parts if part).rstrip()
        if annotations:
            annos = " ".join(self.annotation(anno) for anno in annotations)
            head = f"{head} {annos}" if annos else head
        return head


    def relation_call(self, rel: Relation, args: _Sequence[Value], reading: Reading|None) -> str:
        args_str = ", ".join(self.value(arg) for arg in args)
        reading_ix = rel.readings.index(reading) if reading else 0
        reading_suffix = f"<{reading_ix}>" if reading_ix > 0 else ""
        return f"{self.relation(rel)}({args_str}){reading_suffix}"


    def _render_task(self, task: Task, indent: int = 0) -> Iterable[str]:
        if isinstance(task, Container):
            head = f"{type(task).__name__}{'{…}' if task.scope else ''}{'?' if task.optional else ''}"
        else:
            head = ""

        if isinstance(task, Logical):
            yield _indent_line(
                indent,
                self.header(
                    head, annotations=task.annotations
                ),
            )
            for inner in task.body:
                yield from self._render_task(inner, indent + 1)
            return

        if isinstance(task, Sequence):
            yield _indent_line(
                indent,
                self.header(
                    head, annotations=task.annotations
                ),
            )
            for inner in task.tasks:
                yield from self._render_task(inner, indent + 1)
            return

        if isinstance(task, Union):
            yield _indent_line(
                indent,
                self.header(head, annotations=task.annotations),
            )
            for inner in task.tasks:
                yield from self._render_task(inner, indent + 1)
            return

        if isinstance(task, Match):
            yield _indent_line(
                indent,
                self.header(head, annotations=task.annotations),
            )
            for inner in task.tasks:
                yield from self._render_task(inner, indent + 1)
            return

        if isinstance(task, Until):
            yield _indent_line(
                indent,
                self.header(head, annotations=task.annotations),
            )
            yield _indent_line(indent + 1, "check")
            yield from self._render_task(task.check, indent + 2)
            yield _indent_line(indent + 1, "body")
            yield from self._render_task(task.body, indent + 2)
            return

        if isinstance(task, Wait):
            yield _indent_line(
                indent,
                self.header(head, annotations=task.annotations),
            )
            yield _indent_line(indent + 1, "check")
            yield from self._render_task(task.check, indent + 2)
            return

        if isinstance(task, Loop):
            suffix_parts: List[str] = []
            if task.over:
                suffix_parts.append(
                    "over [" + ", ".join(self.var(v) for v in task.over) + "]"
                )
            if task.concurrency != 1:
                suffix_parts.append(f"concurrency={task.concurrency}")
            suffix = " ".join(suffix_parts)
            yield _indent_line(
                indent,
                self.header(head, annotations=task.annotations, suffix=suffix),
            )
            yield _indent_line(indent + 1, "body")
            yield from self._render_task(task.body, indent + 2)
            return

        if isinstance(task, Break):
            yield _indent_line(
                indent, self.header("Break", annotations=task.annotations)
            )
            yield _indent_line(indent + 1, "check")
            yield from self._render_task(task.check, indent + 2)
            return

        if isinstance(task, Require):
            yield _indent_line(
                indent,
                self.header(
                    head, annotations=task.annotations
                ),
            )
            yield _indent_line(indent + 1, "domain")
            if not isinstance(task.domain, Logical) or task.domain.body:
                yield from self._render_task(task.domain, indent + 2)
            yield _indent_line(indent + 1, "check")
            yield from self._render_task(task.check, indent + 2)
            if task.error:
                yield _indent_line(indent + 1, "error")
                yield from self._render_task(task.error, indent + 2)
            return

        if isinstance(task, Not):
            yield _indent_line(
                indent, self.header(head, annotations=task.annotations)
            )
            yield from self._render_task(task.task, indent + 1)
            return

        if isinstance(task, Exists):
            suffix = ""
            if task.vars:
                suffix = "[" + ", ".join(self.var(v) for v in task.vars) + "]"
            yield _indent_line(
                indent,
                self.header(head, annotations=task.annotations, suffix=suffix),
            )
            yield from self._render_task(task.task, indent + 1)
            return

        if isinstance(task, Lookup):
            yield _indent_line(
                indent,
                self.header(
                    self.relation_call(task.relation, task.args, task.reading_hint),
                    annotations=task.annotations,
                ),
            )
            return

        if isinstance(task, Update):
            yield _indent_line(
                indent,
                self.header(
                    f"{_DERIVE_ARROW} {task.effect.value} "
                    + self.relation_call(task.relation, task.args, task.reading_hint),
                    annotations=task.annotations,
                ),
            )
            return

        if isinstance(task, Aggregate):
            args = ", ".join(self.value(arg) for arg in task.args)
            suffix_parts: List[str] = []
            if task.projection:
                suffix_parts.append(
                    "projection["
                    + ", ".join(self.var(v) for v in task.projection)
                    + "]"
                )
            if task.group:
                suffix_parts.append(
                    "group[" + ", ".join(self.var(v) for v in task.group) + "]"
                )
            suffix = " ".join(suffix_parts)
            head = f"aggregate {self.relation(task.aggregation)}({args})"
            if suffix:
                head = f"{head} {suffix}"
            yield _indent_line(indent, self.header(head, annotations=task.annotations))
            if task.body:
                yield from self._render_task(task.body, indent + 1)
            return

        if isinstance(task, Construct):
            values = [self.value(val) for val in task.values]
            id_var = task.id_var
            if isinstance(id_var, Var):
                has_identity = id_var.name or getattr(id_var, "type", None) is not None
                if has_identity:
                    values.append(self.var(id_var))
            elif id_var is not None:
                values.append(self.value(id_var))
            line = f"construct({', '.join(values)})"
            yield _indent_line(
                indent, self.header(line, annotations=task.annotations)
            )
            return

        yield _indent_line(indent, repr(task))

    def _render_model(self, model: Model, indent: int = 0) -> Iterable[str]:
        summary_parts: List[str] = []
        if model.reasoners:
            summary_parts.append(f"reasoners={len(model.reasoners)}")
        if model.relations:
            summary_parts.append(f"relations={len(model.relations)}")
        if model.types:
            summary_parts.append(f"types={len(model.types)}")
        head = "Model"
        if summary_parts:
            head = f"{head} ({', '.join(summary_parts)})"
        yield _indent_line(indent, head)
        if model.reasoners:
            yield _indent_line(indent + 1, "reasoners")
            for reasoner in model.reasoners:
                yield _indent_line(indent + 2, self.reasoner_str(reasoner))
        if model.relations:
            yield _indent_line(indent + 1, "relations")
            for rel in model.relations:
                yield _indent_line(indent + 2, self.relation(rel))
        if model.types:
            yield _indent_line(indent + 1, "types")
            for type_ in model.types:
                yield _indent_line(indent + 2, self.format_type(type_, include_supertypes=VERBOSE))
        yield _indent_line(indent + 1, "root")
        if isinstance(model.root, Task):
            yield from self._render_task(model.root, indent + 2)
        else:
            yield _indent_line(indent + 2, repr(model.root))

    def format_task(self, task: Task, indent: Optional[int] = None) -> str:
        start_indent = 0 if indent is None else indent
        return "\n".join(self._render_task(task, start_indent))

    def format_model(self, model: Model, indent: Optional[int] = None) -> str:
        start_indent = 0 if indent is None else indent
        return "\n".join(self._render_model(model, start_indent))

    def format(self, node: Node|list|tuple, indent: Optional[int] = None) -> str:
        start_indent = 0 if indent is None else indent
        if isinstance(node, Task):
            return self.format_task(node, start_indent)
        elif isinstance(node, Model):
            return self.format_model(node, start_indent)
        elif isinstance(node, TypeNode):
            return self.format_type(node)
        elif isinstance(node, Literal):
            return self.literal(node)
        elif isinstance(node, Var):
            return self.var(node)
        elif isinstance(node, Relation):
            return self.relation(node)
        elif isinstance(node, (list, tuple)):
            return "List\n" + "\n".join(self.format(n, start_indent+1) for n in node)
        elif isinstance(node, Field):
            return self.value(node)
        else:
            return repr(node)


def format(node: Node|list|tuple, indent: Optional[int] = None) -> str:
    return Printer().format(node, indent)

def pprint(node: Node|list|tuple, indent: Optional[int] = None):
    print(Printer().format(node, indent))

def print_tree(node: Node):
    print_dataclass_tree(node, hide_fields=["source"])
