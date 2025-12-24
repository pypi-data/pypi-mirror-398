"""
A simple metamodel for Rel.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal as PyDecimal
from io import StringIO
from typing import Optional, Tuple, Union as PyUnion
from v0.relationalai.semantics.metamodel import helpers
from v0.relationalai.semantics.rel import rel_utils
from v0.relationalai.semantics.metamodel.util import OrderedSet, Printer as BasePrinter, ordered_set
import json


#--------------------------------------------------
# Node
#--------------------------------------------------

@dataclass(frozen=True)
class Node:
    def __str__(self):
        return to_string(self)

    @property
    def kind(self):
        return self.__class__.__name__.lower()

#--------------------------------------------------
# Top level program and declarations
#--------------------------------------------------

@dataclass(frozen=True)
class Program(Node):
    # top-level declarations
    declarations: Tuple[PyUnion[Declare, Def, RawSource], ...]

@dataclass(frozen=True)
class Declare(Node):
    """ declare $premise [requires $requires] """
    premise: Expr
    requires: Optional[Expr]
    annotations: Tuple[Annotation, ...] = field(default_factory=tuple)

@dataclass(frozen=True)
class Def(Node):
    """ def $name($params) { $body } """
    name: str
    params: Tuple[PyUnion[Var, Primitive, MetaValue], ...]
    body: Expr
    annotations: Tuple[Annotation, ...] = field(default_factory=tuple)

@dataclass(frozen=True)
class RawSource(Node):
    """ Any string representing Rel code. """
    source: str

#--------------------------------------------------
# Primitives, Annotations
#--------------------------------------------------

Primitive = PyUnion[str, int, float, bool, PyDecimal]

@dataclass(frozen=True)
class Annotation(Node):
    """ @$name($args) """
    name: str
    args: Tuple[PyUnion[Primitive, MetaValue], ...]


#--------------------------------------------------
# Expr
#--------------------------------------------------

@dataclass(frozen=True)
class CompositeExpr(Node):
    pass

Expr = PyUnion[Primitive, CompositeExpr]

@dataclass(frozen=True)
class MetaValue(CompositeExpr):
    """ #$value """
    value: Primitive

@dataclass(frozen=True)
class Var(CompositeExpr):
    """ $name[...] [in $type] """
    name: str
    varargs: bool = False
    type: Optional[str] = None

@dataclass(frozen=True)
class Identifier(CompositeExpr):
    """ $name

    Used to declare a relation by name or to refer to a relation (e.g. Int, String)
    """
    name: str

@dataclass(frozen=True)
class Atom(CompositeExpr):
    """ $expr($args)

    Represents atoms like identifier($name)($args) as well as literal relations
    relations like {(:a, Int, 1)}(x...)
    """
    expr: Expr
    args: Tuple[Expr, ...]

def create_eq(lhs: Expr, rhs: Expr) -> Atom:
    return Atom(Identifier("rel_primitive_eq"), (lhs, rhs))

def atom(name: str, args: Tuple[Expr, ...]):
    """ Helper to create a Atom where expression is an identifier. """
    return Atom(Identifier(name), args)

# Represent the true {()} and false {} relations in Rel
true = Identifier("true")
false = Identifier("false")

@dataclass(frozen=True)
class RelationalAbstraction(CompositeExpr):
    """ ($head): $body """
    head: Tuple[Expr, ...]
    body: Expr

@dataclass(frozen=True)
class And(CompositeExpr):
    """ $body[0] and $body[1] ... and $body[n] """
    body: OrderedSet[Expr]

def create_and(exprs: list[Expr]) -> And:
    """ Create an And expression from this list, pulling out the body of nested Ands. """
    s = ordered_set()
    work = exprs.copy()
    while(work):
        expr = work.pop(0)
        if isinstance(expr, And):
            work.extend(expr.body)
        else:
            s.add(expr)
    return And(s)

@dataclass(frozen=True)
class Or(CompositeExpr):
    """ $body[0] or $body[1] ... or $body[n] """
    body: OrderedSet[Expr]

@dataclass(frozen=True)
class Exists(CompositeExpr):
    """ exists(($vars) | $body ) """
    vars: Tuple[Var, ...]
    body: Expr

@dataclass(frozen=True)
class ForAll(CompositeExpr):
    """ forall(($vars) | $body ) """
    vars: Tuple[Var, ...]
    body: Expr

@dataclass(frozen=True)
class Not(CompositeExpr):
    """ not ( $body ) """
    body: Expr

@dataclass(frozen=True)
class BinaryExpr(CompositeExpr):
    """ $lhs $op $rhs """
    lhs: Expr
    op: str
    rhs: Expr

@dataclass(frozen=True)
class Product(CompositeExpr):
    """ ($body[0] , $body[1] ... , $body[n]) """
    body: Tuple[Expr, ...]

@dataclass(frozen=True)
class Union(CompositeExpr):
    """ {$body[0] ; $body[1] ... ; $body[n]} """
    body: Tuple[Expr, ...]



#--------------------------------------------------
# Printer
#--------------------------------------------------

infix = ["+", "-", "*", "/", "%", "=", "!=", "<", "<=", ">", ">="]

def to_string(node) -> str:
    io = StringIO()
    Printer(io).print_node(node, 0)
    return io.getvalue()

@dataclass(frozen=True)
class Printer(BasePrinter):

    def _join(self, args, sep=', ', indent=0):
        for i, s in enumerate(args):
            if i != 0:
                if indent != 0:
                    self._print(sep.rstrip())
                    self._nl()
                else:
                    self._print(sep)
            self.print_node(s, indent)

    def _print_value(self, value, convert:bool=False):
        if isinstance(value, tuple):
            self._print("(")
            for i, v in enumerate(value):
                if i != 0:
                    self._print(", ")
                self._print_value(v, convert=True)
            self._print(")")
        elif isinstance(value, str):
            self._print(json.dumps(value))
        elif isinstance(value, bool):
            self._print(f"rel_primitive_boolean_{str(value).lower()}")
        elif isinstance(value, int) and convert:
            self._print("::std::common::int[128,")
            self._print(str(value))
            self._print("]")
        elif isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            self._print(value.astimezone(timezone.utc).isoformat())
        elif isinstance(value, date):
            self._print(value.isoformat())
        else:
            self._print(str(value))

    def print_node(self, node, indent=0) -> None:
        #--------------------------------------------------
        # Top level program and declarations
        #--------------------------------------------------
        if isinstance(node, Program):
            for idx, d in enumerate(node.declarations):
                self.print_node(d, indent)
                # Avoid an extra newline at the end of the file.
                if idx != len(node.declarations) - 1:
                    self._nl()

        elif isinstance(node, Declare):
            for anno in node.annotations:
                self.print_node(anno, indent)
                self._nl()
            self._indent_print(indent, f"declare {node.premise}")
            if node.requires:
                self._print(" requires ")
                self.print_node(node.requires, 0)
            self._nl()

        elif isinstance(node, Def):
            for anno in node.annotations:
                self.print_node(anno, indent)
                self._nl()
            self._indent_print(indent, f"def {helpers.sanitize(node.name)}")
            if node.params:
                self._print("(")
                self._join(node.params)
                self._print("):")
            else:
                self._print(" {")
            self._nl()
            self.print_node(node.body, indent+1)
            self._nl()
            if not node.params:
                self._indent_print(indent, "}")
                self._nl()

        elif isinstance(node, RawSource):
            self._nl()
            self._print(node.source)
            self._nl()

        #--------------------------------------------------
        # Primitives, Annotations
        #--------------------------------------------------
        elif node is None:
            self._indent_print(indent, "")
            self._print("missing")

        elif isinstance(node, (str, int, float, bool, PyDecimal, tuple)):
            self._indent_print(indent, "")
            self._print_value(node)

        elif isinstance(node, date) and not isinstance(node, datetime):
            self._indent_print(indent, node.isoformat())

        elif isinstance(node, datetime):
            if node.tzinfo is None:
                node = node.replace(tzinfo=timezone.utc)

            self._indent_print(indent, node.astimezone(timezone.utc).isoformat())

        elif isinstance(node, Annotation):
            self._indent_print(indent, f"@{node.name}")
            if node.args:
                self._print("(")
                self._join(node.args)
                self._print(")")


        #--------------------------------------------------
        # Expr
        #--------------------------------------------------

        elif isinstance(node, MetaValue):
            if isinstance(node.value, str):
                self._print(":")
            else:
                self._print("#")
            self._print_value(node.value)

        elif isinstance(node, Var):
            self._indent_print(indent, f"{node.name}")
            if node.varargs:
                self._print("...")
            if node.type and node.type != "Any":
                self._print(f" in {node.type if node.type != 'Enum' else 'UInt128'}")

        elif isinstance(node, Identifier):
            self._indent_print(indent, helpers.sanitize(node.name))

        elif isinstance(node, Atom):
            if isinstance(node.expr, Identifier) and node.expr.name in infix:
                # deal with the 3 kinds of infix operators
                if len(node.args) == 1:
                    self.print_node(node.expr, indent)
                    self.print_node(node.args[0])
                elif len(node.args) == 2:
                    self.print_node(node.args[0], indent)
                    self._print(" ")
                    self.print_node(node.expr)
                    self._print(" ")
                    self.print_node(node.args[1])
                elif len(node.args) == 3:
                    self.print_node(node.args[2], indent)
                    self._print(" = ")
                    self.print_node(node.args[0])
                    self._print(" ")
                    self.print_node(node.expr)
                    self._print(" ")
                    self.print_node(node.args[1])
                else:
                    raise NotImplementedError(f"emit_action: {node}")
            else:
                is_higher_order = False
                is_like = False
                if isinstance(node.expr, Identifier):
                    is_higher_order = node.expr.name in rel_utils.HIGHER_ORDER
                    is_like = node.expr.name == "::std::common::like_match"

                    self.print_node(node.expr, indent)
                elif isinstance(node.expr, Union):
                    self.print_node(node.expr, indent)
                else:
                    self._indent_print(indent, "{")
                    self.print_node(node.expr, indent)
                    self._print("}")

                self._print("(")
                if is_higher_order:
                    self._nl()
                    self._join(node.args, indent=indent+1)
                    self._nl()
                    self._indent_print(indent, ")")
                elif is_like:
                    self._print("raw\"")
                    self._print(node.args[1])
                    self._print("\", ")
                    self.print_node(node.args[0])
                    self._print(")")
                else:
                    self._join(node.args)
                    self._print(")")

        elif isinstance(node, RelationalAbstraction):
            if node.head:
                self._indent_print(indent, "{(")
                self._join(node.head)
                self._print("):")
                if self._is_simple_body(node.body):
                    self._print(" ")
                    self.print_node(node.body)
                    self._print("}")
                else:
                    self._nl()
                    self.print_node(node.body, indent+1)
                    self._nl()
                    self._indent_print(indent, "}")
            else:
                self.print_node(node.body, indent)

        elif isinstance(node, And):
            self._join(node.body, " and ", indent)

        elif isinstance(node, Or):
            self._indent_print(indent, "(")
            self._join(node.body, " or ")
            self._print(")")

        elif isinstance(node, Exists):
            self._indent_print(indent, "exists((")
            self._join(node.vars)
            self._print(") |")
            if self._is_simple_body(node.body):
                self._print(" ")
                self.print_node(node.body)
                self._print(")")
            else:
                self._nl()
                self.print_node(node.body, indent+1)
                self._nl()
                self._indent_print(indent, ")")

        elif isinstance(node, ForAll):
            self._indent_print(indent, "forall((")
            self._join(node.vars)
            self._print(") |")
            if self._is_simple_body(node.body):
                self._print(" ")
                self.print_node(node.body)
                self._print(")")
            else:
                self._nl()
                self.print_node(node.body, indent+1)
                self._nl()
                self._indent_print(indent, ")")

        elif isinstance(node, Not):
            self._indent_print(indent, "not (")
            if self._is_simple_body(node.body):
                self._print(" ")
                self.print_node(node.body)
                self._print(" )")
            else:
                self._nl()
                self.print_node(node.body, indent+1)
                self._nl()
                self._indent_print(indent, ")")

        elif isinstance(node, BinaryExpr):
            self.print_node(node.lhs, indent)
            self._print(f" {node.op} ")
            self.print_node(node.rhs)

        elif isinstance(node, Product):
            self._indent_print(indent, "(")
            self._join(node.body, ", ")
            self._print(")")

        elif isinstance(node, Union):
            if all(isinstance(b, Atom) for b in node.body):
                self._join(node.body, " or ", indent)
            else:
                self._indent_print(indent, "{")
                self._nl()
                self._join(node.body, " ; ", indent+1)
                self._nl()
                self._indent_print(indent, "}")

        else:
            raise Exception(f"Missing implementation in Rel printer: {type(node)}")

    def _is_simple_body(self, node: Expr) -> bool:
        if isinstance(node, (Var, Primitive, MetaValue, Identifier)):
            return True
        elif isinstance(node, Atom):
            return self._is_simple_body(node.expr) and all(self._is_simple_body(a) for a in node.args)
        elif isinstance(node, Exists):
            return self._is_simple_body(node.body)
        elif isinstance(node, ForAll):
            return self._is_simple_body(node.body)
        elif isinstance(node, Not):
            return self._is_simple_body(node.body)
        elif isinstance(node, BinaryExpr):
            return self._is_simple_body(node.lhs) and self._is_simple_body(node.rhs)
        return False
