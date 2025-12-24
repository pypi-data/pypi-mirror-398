"""
    Support for traversing the IR, often to search for information.
"""
from dataclasses import dataclass, field
from typing import Callable, Optional, TypeVar, cast, Tuple, Union as PyUnion, Generic
from abc import abstractmethod
from .util import OrderedSet, flatten_tuple, ordered_set, FrozenOrderedSet, rewrite_list, rewrite_set
from . import ir

#--------------------------------------------------
# Visitor Abstraction
#--------------------------------------------------

Result = TypeVar('Result')
class GenericVisitor(Generic[Result]):
    """
    Abstract visitor with handlers for each IR node type.
    Each handler should return a value of type `Result`.

    Actual behavior (e.g., AST traversal) should be implemented in
    subclasses of `GenericVisitor`.
    """

    ##################################################
    # Model

    @abstractmethod
    def visit_model(self, node: ir.Model, parent: Optional[ir.Node]) -> Result:
        pass

    ##################################################
    # Engine

    @abstractmethod
    def visit_capability(self, node: ir.Capability, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_engine(self, node: ir.Engine, parent: Optional[ir.Node]) -> Result:
        pass

    ##################################################
    # Types

    @abstractmethod
    def visit_scalartype(self, node: ir.ScalarType, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_decimaltype(self, node: ir.DecimalType, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_listtype(self, node: ir.ListType, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_uniontype(self, node: ir.UnionType, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_tupletype(self, node: ir.TupleType, parent: Optional[ir.Node]) -> Result:
        pass

    ##################################################
    # Relations

    @abstractmethod
    def visit_field(self, node: ir.Field, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_relation(self, node: ir.Relation, parent: Optional[ir.Node]) -> Result:
        pass

    ##################################################
    # Variables and values

    @abstractmethod
    def visit_var(self, node: ir.Var, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_default(self, node: ir.Default, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_literal(self, node: ir.Literal, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_data(self, node: ir.Data, parent: Optional[ir.Node]) -> Result:
        pass

    ##################################################
    # Composite tasks

    @abstractmethod
    def visit_logical(self, node: ir.Logical, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_union(self, node: ir.Union, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_sequence(self, node: ir.Sequence, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_match(self, node: ir.Match, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_until(self, node: ir.Until, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_wait(self, node: ir.Wait, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_require(self, node: ir.Require, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_check(self, node: ir.Check, parent: Optional[ir.Node]) -> Result:
        pass

    ##################################################
    # Logical tasks

    @abstractmethod
    def visit_not(self, node: ir.Not, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_exists(self, node: ir.Exists, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_forall(self, node: ir.ForAll, parent: Optional[ir.Node]) -> Result:
        pass

    ##################################################
    # Iteration tasks

    @abstractmethod
    def visit_loop(self, node: ir.Loop, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_break(self, node: ir.Break, parent: Optional[ir.Node]) -> Result:
        pass

    ##################################################
    # Leaf tasks

    @abstractmethod
    def visit_update(self, node: ir.Update, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_annotation(self, node: ir.Annotation, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_lookup(self, node: ir.Lookup, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_output(self, node: ir.Output, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_construct(self, node: ir.Construct, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_aggregate(self, node: ir.Aggregate, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_rank(self, node: ir.Rank, parent: Optional[ir.Node]) -> Result:
        pass

    @abstractmethod
    def visit_task(self, node: ir.Task, parent: Optional[ir.Node]) -> Result:
        pass

@dataclass
class Visitor(GenericVisitor[None]):
    """
    A visitor that just walks the AST, performing no changes.
    """

    def enter(self, node: ir.Node, parent: Optional[ir.Node]=None) -> "Visitor":
        """ Visit the node, possibly returning a new visitor to be used to visit the node's children. """
        return self

    def prune(self):
        """ Return a new Visitor that just returns each node unchanged without traversing its children. """
        return PruneVisitor()

    def leave(self, node: ir.Node, parent: Optional[ir.Node]=None) -> ir.Node:
        """ Visit the node after visiting it and its children. """
        return node

    def _walk_node(self, node: ir.Node, parent: Optional[ir.Node]=None):
        # Enter the node, returning a new context.
        v = self.enter(node, parent)

        # Dispatch to the handler for the node.
        # By default the handler traverses the node's children and reconstructs the node.
        node.accept(v, parent)

        self.leave(node, parent)

    # Avoid dispatch overhead for some types.
    # These should never be called directly.
    def _walk_var(self, node: ir.Var, parent: Optional[ir.Node]):
        v = self.enter(node, parent)
        v.visit_var(node, parent)
        self.leave(node, parent)

    def _walk_var_or_default(self, node: PyUnion[ir.Var, ir.Default], parent: Optional[ir.Node]):
        v = self.enter(node, parent)
        if isinstance(node, ir.Var):
            v.visit_var(node, parent)
        else:
            v.visit_default(node, parent)
        self.leave(node, parent)

    def _walk_value(self, node: ir.Value, parent: Optional[ir.Node]):
        if node is None:
            return None
        elif isinstance(node, ir.Var):
            return self._walk_var(node, parent)
        elif isinstance(node, ir.Relation):
            return self._walk_relation(node, parent)
        elif isinstance(node, ir.Node):
            return self._walk_node(node, parent)
        elif isinstance(node, Tuple):
            for item in node:
                self._walk_value(item, parent)
        elif isinstance(node, FrozenOrderedSet):
            for item in node:
                self._walk_value(item, parent)

    def _walk_engine(self, node: ir.Engine, parent: Optional[ir.Node]):
        v = self.enter(node, parent)
        v.visit_engine(node, parent)
        self.leave(node, parent)

    def _walk_relation(self, node: ir.Relation, parent: Optional[ir.Node]):
        v = self.enter(node, parent)
        v.visit_relation(node, parent)
        self.leave(node, parent)

    def _walk_type(self, node: ir.Type, parent: Optional[ir.Node]):
        # The if-isinstance chain saves about 10% on a traversal vs. node.accept(v, parent)
        v = self.enter(node, parent)
        if isinstance(node, ir.DecimalType):
            v.visit_decimaltype(node, parent)
        elif isinstance(node, ir.ScalarType):
            v.visit_scalartype(node, parent)
        elif isinstance(node, ir.ListType):
            v.visit_listtype(node, parent)
        elif isinstance(node, ir.UnionType):
            v.visit_uniontype(node, parent)
        elif isinstance(node, ir.TupleType):
            v.visit_tupletype(node, parent)
        else:
            raise NotImplementedError(f"visit_type not implemented for {type(node)}")
        self.leave(node, parent)

    ##################################################
    # Model

    def visit_model(self, node: ir.Model, parent: Optional[ir.Node]):
        for c in node.engines:
            self._walk_engine(c, node)
        for c in node.relations:
            self._walk_relation(c, node)
        for c in node.types:
            self._walk_type(c, node)
        self._walk_node(node.root, node)

    ##################################################
    # Engine

    def visit_capability(self, node: ir.Capability, parent: Optional[ir.Node]):
        pass

    def visit_engine(self, node: ir.Engine, parent: Optional[ir.Node]):
        for c in node.capabilities:
            self._walk_node(c, node)
        for c in node.relations:
            self._walk_relation(c, node)

    ##################################################
    # Types

    def visit_scalartype(self, node: ir.ScalarType, parent: Optional[ir.Node]):
        for t in node.super_types:
            self._walk_type(t, node)
        for a in node.annotations:
            self._walk_node(a, node)

    def visit_decimaltype(self, node: ir.DecimalType, parent: Optional[ir.Node]):
        self.visit_scalartype(node, parent)

    def visit_listtype(self, node: ir.ListType, parent: Optional[ir.Node]):
        self._walk_type(node.element_type, node)

    def visit_uniontype(self, node: ir.UnionType, parent: Optional[ir.Node]):
        for t in node.types:
            self._walk_type(t, node)

    def visit_tupletype(self, node: ir.TupleType, parent: Optional[ir.Node]):
        for t in node.types:
            self._walk_type(t, node)

    ##################################################
    # Relations

    def visit_field(self, node: ir.Field, parent: Optional[ir.Node]):
        self._walk_type(node.type, node)

    def visit_relation(self, node: ir.Relation, parent: Optional[ir.Node]):
        for f in node.fields:
            self._walk_node(f, node)
        for r in node.requires:
            self._walk_node(r, node)
        for r in node.overloads:
            self._walk_node(r, node)

    ##################################################
    # Variables and values

    def visit_var(self, node: ir.Var, parent: Optional[ir.Node]):
        self._walk_type(node.type, node)

    def visit_default(self, node: ir.Default, parent: Optional[ir.Node]):
        self._walk_var(node.var, node)
        self._walk_value(node.value, node)

    def visit_literal(self, node: ir.Literal, parent: Optional[ir.Node]):
        self._walk_type(node.type, node)

    def visit_data(self, node: ir.Data, parent: Optional[ir.Node]):
        for v in node.vars:
            self._walk_var(v, node)

    ##################################################
    # Composite tasks

    def visit_logical(self, node: ir.Logical, parent: Optional[ir.Node]):
        if node.engine is not None:
            self._walk_engine(node.engine, node)
        for h in node.hoisted:
            self._walk_var_or_default(h, node)
        for b in node.body:
            self._walk_node(b, node)
        for a in node.annotations:
            self._walk_node(a, node)

    def visit_union(self, node: ir.Union, parent: Optional[ir.Node]):
        if node.engine is not None:
            self._walk_engine(node.engine, node)
        for h in node.hoisted:
            self._walk_var_or_default(h, node)
        for t in node.tasks:
            self._walk_node(t, node)
        for a in node.annotations:
            self._walk_node(a, node)

    def visit_sequence(self, node: ir.Sequence, parent: Optional[ir.Node]):
        if node.engine is not None:
            self._walk_engine(node.engine, node)
        for h in node.hoisted:
            self._walk_var_or_default(h, node)
        for t in node.tasks:
            self._walk_node(t, node)
        for a in node.annotations:
            self._walk_node(a, node)

    def visit_match(self, node: ir.Match, parent: Optional[ir.Node]):
        if node.engine is not None:
            self._walk_engine(node.engine, node)
        for h in node.hoisted:
            self._walk_var_or_default(h, node)
        for t in node.tasks:
            self._walk_node(t, node)
        for a in node.annotations:
            self._walk_node(a, node)

    def visit_until(self, node: ir.Until, parent: Optional[ir.Node]):
        if node.engine is not None:
            self._walk_engine(node.engine, node)
        for h in node.hoisted:
            self._walk_var_or_default(h, node)
        self._walk_node(node.check, node)
        self._walk_node(node.body, node)
        for a in node.annotations:
            self._walk_node(a, node)

    def visit_wait(self, node: ir.Wait, parent: Optional[ir.Node]):
        if node.engine is not None:
            self._walk_engine(node.engine, node)
        for h in node.hoisted:
            self._walk_var_or_default(h, node)
        self._walk_node(node.check, node)
        for a in node.annotations:
            self._walk_node(a, node)

    def visit_require(self, node: ir.Require, parent: Optional[ir.Node]):
        if node.engine is not None:
            self._walk_engine(node.engine, node)
        self._walk_node(node.domain, node)
        for check in node.checks:
            self._walk_node(check, node)
        for a in node.annotations:
            self._walk_node(a, node)

    def visit_check(self, node: ir.Check, parent: Optional[ir.Node]):
        self._walk_node(node.check, node)
        if node.error:
            self._walk_node(node.error, node)
        for a in node.annotations:
            self._walk_node(a, node)

    ##################################################
    # Logical tasks

    def visit_not(self, node: ir.Not, parent: Optional[ir.Node]):
        if node.engine is not None:
            self._walk_engine(node.engine, node)
        self._walk_node(node.task, node)
        for a in node.annotations:
            self._walk_node(a, node)

    def visit_exists(self, node: ir.Exists, parent: Optional[ir.Node]):
        if node.engine is not None:
            self._walk_engine(node.engine, node)
        for v in node.vars:
            self._walk_var(v, node)
        self._walk_node(node.task, node)
        for a in node.annotations:
            self._walk_node(a, node)

    def visit_forall(self, node: ir.ForAll, parent: Optional[ir.Node]):
        if node.engine is not None:
            self._walk_engine(node.engine, node)
        for v in node.vars:
            self._walk_var(v, node)
        self._walk_node(node.task, node)
        for a in node.annotations:
            self._walk_node(a, node)

    ##################################################
    # Iteration tasks

    def visit_loop(self, node: ir.Loop, parent: Optional[ir.Node]):
        if node.engine is not None:
            self._walk_engine(node.engine, node)
        for h in node.hoisted:
            self._walk_var_or_default(h, node)
        self._walk_var(node.iter, node)
        self._walk_node(node.body, node)
        for a in node.annotations:
            self._walk_node(a, node)

    def visit_break(self, node: ir.Break, parent: Optional[ir.Node]):
        if node.engine is not None:
            self._walk_engine(node.engine, node)
        self._walk_node(node.check, node)
        for a in node.annotations:
            self._walk_node(a, node)

    ##################################################
    # Leaf tasks

    def visit_update(self, node: ir.Update, parent: Optional[ir.Node]):
        if node.engine is not None:
            self._walk_engine(node.engine, node)
        self._walk_relation(node.relation, node)
        for a in node.args:
            self._walk_value(a, node)
        for a in node.annotations:
            self._walk_node(a, node)

    def visit_annotation(self, node: ir.Annotation, parent: Optional[ir.Node]):
        self._walk_relation(node.relation, node)
        for a in node.args:
            self._walk_value(a, node)

    def visit_lookup(self, node: ir.Lookup, parent: Optional[ir.Node]):
        if node.engine is not None:
            self._walk_engine(node.engine, node)
        self._walk_relation(node.relation, node)
        for a in node.args:
            self._walk_value(a, node)
        for a in node.annotations:
            self._walk_node(a, node)

    def visit_output(self, node: ir.Output, parent: Optional[ir.Node]):
        if node.engine is not None:
            self._walk_engine(node.engine, node)
        for _, v in node.aliases:
            self._walk_value(v, node)
        if node.keys:
            for k in node.keys:
                self._walk_var(k, node)
        for a in node.annotations:
            self._walk_node(a, node)

    def visit_construct(self, node: ir.Construct, parent: Optional[ir.Node]):
        if node.engine is not None:
            self._walk_engine(node.engine, node)
        for v in node.values:
            self._walk_value(v, node)
        self._walk_var(node.id_var, node)
        for a in node.annotations:
            self._walk_node(a, node)

    def visit_aggregate(self, node: ir.Aggregate, parent: Optional[ir.Node]):
        if node.engine is not None:
            self._walk_engine(node.engine, node)
        self._walk_relation(node.aggregation, node)
        for p in node.projection:
            self._walk_var(p, node)
        for g in node.group:
            self._walk_var(g, node)
        for a in node.args:
            self._walk_value(a, node)
        for a in node.annotations:
            self._walk_node(a, node)

    def visit_rank(self, node: ir.Rank, parent: Optional[ir.Node]):
        if node.engine is not None:
            self._walk_engine(node.engine, node)
        for p in node.projection:
            self._walk_var(p, node)
        for g in node.group:
            self._walk_var(g, node)
        for a in node.args:
            self._walk_value(a, node)
        self._walk_value(node.result, node)
        for a in node.annotations:
            self._walk_node(a, node)

    def visit_task(self, node: ir.Task, parent: Optional[ir.Node]):
        if node.engine is not None:
            self._walk_engine(node.engine, node)

#--------------------------------------------------
# Some generally useful visitors
#--------------------------------------------------

@dataclass
class PruneVisitor(Visitor):
    """ A Visitor that does not walk children. """

    def _walk_node(self, node: ir.Node, parent: Optional[ir.Node]=None):
        pass
    def _walk_var(self, node: ir.Var, parent: Optional[ir.Node]):
        pass
    def _walk_var_or_default(self, node: ir.VarOrDefault, parent: Optional[ir.Node]):
        pass
    def _walk_engine(self, node: ir.Engine, parent: Optional[ir.Node]):
        pass
    def _walk_relation(self, node: ir.Relation, parent: Optional[ir.Node]):
        pass
    def _walk_type(self, node: ir.Type, parent: Optional[ir.Node]):
        pass

@dataclass
class DAGVisitor(Visitor):
    """ A visitor that just walks the AST, performing no changes. Nodes are visited at most once. """
    seen: set[ir.Node] = field(default_factory=set)

    def _walk_node(self, node: ir.Node, parent: Optional[ir.Node]=None):
        if node in self.seen:
            return
        self.seen.add(node)
        return super()._walk_node(node, parent)
    def _walk_var(self, node: ir.Var, parent: Optional[ir.Node]):
        if node in self.seen:
            return
        self.seen.add(node)
        return super()._walk_var(node, parent)
    def _walk_var_or_default(self, node: ir.VarOrDefault, parent: Optional[ir.Node]):
        if node in self.seen:
            return
        self.seen.add(node)
        return super()._walk_var_or_default(node, parent)
    def _walk_engine(self, node: ir.Engine, parent: Optional[ir.Node]):
        if node in self.seen:
            return
        self.seen.add(node)
        return super()._walk_engine(node, parent)
    def _walk_relation(self, node: ir.Relation, parent: Optional[ir.Node]):
        if node in self.seen:
            return
        self.seen.add(node)
        return super()._walk_relation(node, parent)
    def _walk_type(self, node: ir.Type, parent: Optional[ir.Node]):
        if node in self.seen:
            return
        self.seen.add(node)
        return super()._walk_type(node, parent)

class Collector(Visitor):
    """ A visitor that collects instances that match a predicate. """
    def __init__(self, predicate: Callable[[ir.Node, Optional[ir.Node]], bool]):
        super().__init__()
        self.elements: OrderedSet = ordered_set()
        self.predicate = predicate

    def enter(self, node: ir.Node, parent: Optional[ir.Node]=None):
        if self.predicate(node, parent):
            self.elements.add(node)
        return self

def collect(predicate: Callable[[ir.Node, Optional[ir.Node]], bool], *nodes: ir.Node) -> OrderedSet[ir.Node]:
    """ Collect children of node that match the predicate. """
    c = Collector(predicate)
    for n in nodes:
        n.accept(c)
    return c.elements

T = TypeVar('T')
def collect_by_type(t: PyUnion[type[T], tuple[type[T], ...]], *nodes: ir.Node) -> OrderedSet[T]:
    """ Collect instances of the type t by traversing this node and its children. """
    return cast(OrderedSet[T],
        collect(lambda n, parent: isinstance(n, t), *nodes)
    )

@dataclass
class ReadWriteVisitor(Visitor):
    """
    Compute the set of reads and writes for Logical nodes.

    Note that reads are Lookups and writes are Updates. We don't consider Output a write
    because it is not targeting a relation.
    """
    # TODO: we currently only compute for Logical nodes, but it may be useful for other nodes
    _reads: dict[int, OrderedSet[ir.Relation]] = field(default_factory=dict)
    _writes: dict[int, OrderedSet[ir.Relation]] = field(default_factory=dict)

    def reads(self, key: ir.Logical):
        # TODO - use a singleton empty set
        return self._reads[key.id] if key.id in self._reads else ordered_set()

    def writes(self, key: ir.Logical):
        return self._writes[key.id] if key.id in self._writes else ordered_set()

    _stack: list[ir.Logical] = field(default_factory=list)

    def visit_logical(self, node: ir.Logical, parent: Optional[ir.Node]):
        self._stack.append(node)
        super().visit_logical(node, parent)
        self._stack.pop()

    def visit_lookup(self, node: ir.Lookup, parent: Optional[ir.Node]):
        for lu in self._stack:
            if lu.id not in self._reads:
                self._reads[lu.id] = ordered_set()
            self._reads[lu.id].add(node.relation)
        return super().visit_lookup(node, parent)

    def visit_aggregate(self, node: ir.Aggregate, parent: Optional[ir.Node]):
        for lu in self._stack:
            if lu.id not in self._reads:
                self._reads[lu.id] = ordered_set()
            self._reads[lu.id].add(node.aggregation)
        return super().visit_aggregate(node, parent)

    def visit_update(self, node: ir.Update, parent: Optional[ir.Node]):
        for lu in self._stack:
            if lu.id not in self._writes:
                self._writes[lu.id] = ordered_set()
            self._writes[lu.id].add(node.relation)
        return super().visit_update(node, parent)

@dataclass
class Rewriter():
    """
    Rewrite a model, being careful to visit nodes only once.
    """

    rewritten: dict[int, ir.Node] = field(default_factory=dict, init=False, compare=False, hash=False)
    handler_cache: dict[str, Callable[[ir.Node, Optional[ir.Node]], ir.Node]] = field(default_factory=dict, init=False, compare=False, hash=False)

    T = TypeVar('T', bound=PyUnion[ir.Node, ir.Value])
    def walk(self, node: T, parent=None) -> T:
        # if node is a tuple, walk the list
        if isinstance(node, tuple):
            return self.walk_list(node, parent)
        # if node is a value, just return it
        if not isinstance(node, ir.Node):
            return node

        result = self.rewritten.get(node.id, None)
        if result:
            return cast(T, result) # type: ignore[reportReturnType]

        # node is actually some Node type, handle with the appropriate handler
        handler = self.handler_cache.get(node.kind, None)
        if not handler:
            handler = getattr(self, f"handle_{node.kind}", None)
            if handler:
                self.handler_cache[node.kind] = handler
        if handler:
            result = cast(ir.Node, handler(node, parent))
            self.rewritten[node.id] = result
            return cast(T, result) # type: ignore[reportReturnType]
        else:
            raise NotImplementedError(f"walk: {node.kind}")

    def walk_set(self, items: FrozenOrderedSet[T], parent=None) -> FrozenOrderedSet[T]:
        return ordered_set(*[self.walk(n, parent) for n in items]).frozen()

    def walk_list(self, items: Tuple[T, ...], parent=None) -> Tuple[T, ...]:
        return tuple([self.walk(n, parent) for n in items])

    #-------------------------------------------------
    # Public Types - Model
    #-------------------------------------------------

    def handle_model(self, model: ir.Model, parent: None):
        engines = rewrite_set(ir.Engine, lambda n: self.walk(n, model), model.engines)
        relations = rewrite_set(ir.Relation, lambda n: self.walk(n, model), model.relations)
        types = rewrite_set(ir.Type, lambda n: self.walk(n, model), model.types)
        root = self.walk(model.root, model)

        return model.reconstruct(engines, relations, types, root, model.annotations)

    #-------------------------------------------------
    # Public Types - Engine
    #-------------------------------------------------

    def handle_capability(self, node: ir.Capability, parent: ir.Node):
        return node

    def handle_engine(self, node: ir.Engine, parent: ir.Node):
        return node

    #-------------------------------------------------
    # Public Types - Data Model
    #-------------------------------------------------

    def handle_scalartype(self, node: ir.ScalarType, parent: ir.Node):
        return node

    def handle_decimaltype(self, node: ir.DecimalType, parent: ir.Node):
        return node

    def handle_listtype(self, node: ir.ListType, parent: ir.Node):
        return node

    def handle_uniontype(self, node: ir.UnionType, parent: ir.Node):
        # TODO - we could traverse the children
        return node

    def handle_tupletype(self, node: ir.TupleType, parent: ir.Node):
        # TODO - we could traverse the children
        return node

    def handle_field(self, node: ir.Field, parent: ir.Node):
        type_val = self.walk(node.type, node)
        return node.reconstruct(node.name, type_val, node.input)

    def handle_relation(self, node: ir.Relation, parent: ir.Node):
        fields = rewrite_list(ir.Field, lambda n: self.walk(n, node), node.fields)
        requires = rewrite_set(ir.Capability, lambda n: self.walk(n, node), node.requires)
        annotations = rewrite_set(ir.Annotation, lambda n: self.walk(n, node), node.annotations)
        overloads = rewrite_set(ir.Relation, lambda n: self.walk(n, node), node.overloads)
        return node.reconstruct(node.name, fields, requires, annotations, overloads)

    #-------------------------------------------------
    # Public Types - Tasks
    #-------------------------------------------------

    def handle_task(self, node: ir.Task, parent: ir.Node):
        return node

    #
    # Task composition
    #

    def handle_logical(self, node: ir.Logical, parent: ir.Node):
        hoisted = rewrite_list(ir.VarOrDefault, lambda n: self.walk(n, node), node.hoisted)
        body = rewrite_list(ir.Task, lambda n: self.walk(n, node), node.body)

        return node.reconstruct(node.engine, hoisted, flatten_tuple(body, ir.Task), node.annotations)

    def handle_union(self, node: ir.Union, parent: ir.Node):
        hoisted = rewrite_list(ir.VarOrDefault, lambda n: self.walk(n, node), node.hoisted)
        tasks = rewrite_list(ir.Task, lambda n: self.walk(n, node), node.tasks)

        return node.reconstruct(node.engine, hoisted, tasks, node.annotations)

    def handle_sequence(self, node: ir.Sequence, parent: ir.Node):
        hoisted = rewrite_list(ir.VarOrDefault, lambda n: self.walk(n, node), node.hoisted)
        tasks = rewrite_list(ir.Task, lambda n: self.walk(n, node), node.tasks)

        return node.reconstruct(node.engine, hoisted, flatten_tuple(tasks, ir.Task), node.annotations)

    def handle_match(self, node: ir.Match, parent: ir.Node):
        hoisted = rewrite_list(ir.VarOrDefault, lambda n: self.walk(n, node), node.hoisted)
        tasks = rewrite_list(ir.Task, lambda n: self.walk(n, node), node.tasks)

        return node.reconstruct(node.engine, hoisted, tasks, node.annotations)

    def handle_until(self, node: ir.Until, parent: ir.Node):
        hoisted = rewrite_list(ir.VarOrDefault, lambda n: self.walk(n, node), node.hoisted)
        check = self.walk(node.check, node)
        body = self.walk(node.body, node)

        return node.reconstruct(node.engine, hoisted, check, body, node.annotations)

    def handle_wait(self, node: ir.Wait, parent: ir.Node):
        hoisted = rewrite_list(ir.VarOrDefault, lambda n: self.walk(n, node), node.hoisted)
        check = self.walk(node.check, node)

        return node.reconstruct(node.engine, hoisted, check, node.annotations)

    def handle_require(self, node: ir.Require, parent: ir.Node):
        domain = self.walk(node.domain, node)
        checks = rewrite_list(ir.Check, lambda n: self.walk(n, node), node.checks)

        return node.reconstruct(node.engine, domain, checks, node.annotations)

    def handle_check(self, node: ir.Check, parent: ir.Node):
        check = self.walk(node.check, node)
        error = None
        if node.error:
            error = self.walk(node.error, node)

        return node.reconstruct(check, error, node.annotations)

    #
    # Relational Operations
    #

    def handle_var(self, node: ir.Var, parent: ir.Node):
        type_val = self.walk(node.type, node)
        name_val = node.name or f"v{node.id}"
        return node.reconstruct(type_val, name_val)

    def handle_default(self, node: ir.Default, parent: ir.Node):
        var = self.walk(node.var, node)
        return node.reconstruct(var, node.value)

    def handle_literal(self, node: ir.Literal, parent: ir.Node):
        type_val = self.walk(node.type, node)
        return node.reconstruct(type_val, node.value)

    def handle_data(self, node: ir.Data, parent: ir.Node):
        vars = rewrite_list(ir.Var, lambda n: self.walk(n, node), node.vars)
        return node.reconstruct(node.engine, node.data, vars)

    def handle_annotation(self, node: ir.Annotation, parent: ir.Node):
        return node

    def handle_update(self, node: ir.Update, parent: ir.Node):
        relation = self.walk(node.relation, node)
        args = rewrite_list(ir.Value, lambda n: self.walk(n, node), node.args)
        return node.reconstruct(node.engine, relation, args, node.effect, node.annotations)

    def handle_lookup(self, node: ir.Lookup, parent: ir.Node):
        relation = self.walk(node.relation, node)
        args = rewrite_list(ir.Value, lambda n: self.walk(n, node), node.args)
        return node.reconstruct(node.engine, relation, args, node.annotations)

    def handle_output(self, node: ir.Output, parent: ir.Node):
        def rewrite_alias(pair: Tuple[str, ir.Value]):
            name, x = pair
            new_x = self.walk(x, node)
            if new_x is not x:
                return (name, new_x)
            else:
                return pair
        # rewrite_set can't be passed a generic type, so just use Tuple and cast the result.
        aliases = cast(
            FrozenOrderedSet[Tuple[str, ir.Value]],
            rewrite_set(
                Tuple,
                rewrite_alias,
                node.aliases))
        keys = rewrite_list(ir.Var, lambda n: self.walk(n, node), tuple(node.keys)) if node.keys else None
        return node.reconstruct(node.engine, aliases, keys, node.annotations)

    def handle_construct(self, node: ir.Construct, parent: ir.Node):
        values = rewrite_list(ir.Value, lambda n: self.walk(n, node), node.values)
        id_var = self.walk(node.id_var, node)
        return node.reconstruct(node.engine, values, id_var, node.annotations)

    def handle_aggregate(self, node: ir.Aggregate, parent: ir.Node):
        aggregation = self.walk(node.aggregation, node)
        projection = rewrite_list(ir.Var, lambda n: self.walk(n, node), node.projection)
        group = rewrite_list(ir.Var, lambda n: self.walk(n, node), node.group)
        args = rewrite_list(ir.Value, lambda n: self.walk(n, node), node.args)
        return node.reconstruct(node.engine, aggregation, projection, group, args, node.annotations)

    def handle_rank(self, node: ir.Rank, parent: ir.Node):
        projection = rewrite_list(ir.Var, lambda n: self.walk(n, node), node.projection)
        group = rewrite_list(ir.Var, lambda n: self.walk(n, node), node.group)
        args = rewrite_list(ir.Value, lambda n: self.walk(n, node), node.args)
        result = self.walk(node.result, node)
        return node.reconstruct(node.engine, projection, group, args, node.arg_is_ascending, result, node.limit,node.annotations)

    #
    # Logical Quantifiers
    #

    def handle_not(self, node: ir.Not, parent: ir.Node):
        task = self.walk(node.task, node)
        return node.reconstruct(node.engine, task, node.annotations)

    def handle_exists(self, node: ir.Exists, parent: ir.Node):
        vars = rewrite_list(ir.Var, lambda n: self.walk(n, node), node.vars)
        task = self.walk(node.task, node)
        return node.reconstruct(node.engine, vars, task, node.annotations)

    def handle_forall(self, node: ir.ForAll, parent: ir.Node):
        vars = rewrite_list(ir.Var, lambda n: self.walk(n, node), node.vars)
        task = self.walk(node.task, node)
        return node.reconstruct(node.engine, vars, task, node.annotations)

    #
    # Iteration (Loops)
    #
    def handle_loop(self, node: ir.Loop, parent: ir.Node):
        hoisted = rewrite_list(ir.VarOrDefault, lambda n: self.walk(n, node), node.hoisted)
        iter_val = self.walk(node.iter, node)
        body = self.walk(node.body, node)
        return node.reconstruct(node.engine, hoisted, iter_val, body, node.annotations)

    def handle_break(self, node: ir.Break, parent: ir.Node):
        check = self.walk(node.check, node)
        return node.reconstruct(node.engine, check, node.annotations)
