"""
Framework for performing dataflow analysis on the IR.
"""
from dataclasses import dataclass, field
from typing import Dict, TypeVar, Generic
from functools import reduce

from .util import OrderedSet, ordered_set
from . import ir

T = TypeVar('T')

@dataclass
class DataflowAnalyzer(Generic[T]):
    """
    A framework for performing dataflow analysis on the IR.

    The analysis works over a semilattice `T`, which is a set of values that can be combined
    using a meet() operation. The meet() operation is must be:
    - Associative: (a ∧ b) ∧ c = a ∧ (b ∧ c)
    - Commutative: a ∧ b = b ∧ a
    - Idempotent: a ∧ a = a

    Subclasses must also specify a bottom() element for `T`.

    Typically elements of `T` are a set and the meet operation is intersection or union.
    Users can overload transfer() to define their specific analysis.
    """
    def __init__(self):
        # Maps nodes to their dataflow values
        self._in: Dict[ir.Node, T] = field(default_factory=dict)
        self._out: Dict[ir.Node, T] = field(default_factory=dict)
        self._succs: Dict[ir.Node, OrderedSet[ir.Node]] = field(default_factory=dict)
        self._preds: Dict[ir.Node, OrderedSet[ir.Node]] = field(default_factory=dict)

    def transfer(self, node: ir.Node, in_val: T) -> T:
        """
        Transfer function that defines how data flows through a node.
        Override this to define the analysis-specific transfer function.
        """
        return in_val

    def meet(self, a: T, b: T) -> T:
        """
        Meet operation that combines two dataflow values.
        """
        raise NotImplementedError

    def add_flow(self, src: ir.Node, dst: ir.Node):
        """Record a flow from src to dst."""
        self._succs[src].add(dst)
        self._preds[dst].add(src)

    def bottom(self) -> T:
        """Create a bottom element for the semilattice."""
        raise NotImplementedError

    def _get_predecessors(self, node: ir.Node) -> OrderedSet[ir.Node]:
        """Get all nodes that flow into this node."""
        return self._preds.get(node, ordered_set())

    def _get_successors(self, node: ir.Node) -> OrderedSet[ir.Node]:
        """Get all nodes that this node flows into."""
        return self._succs.get(node, ordered_set())

    def _solve(self):
        """Solve the dataflow equations using a worklist algorithm."""
        # Initialize worklist with all nodes that have flows
        worklist = ordered_set()
        for src in self._succs:
            worklist.add(src)

        while worklist:
            node = next(iter(worklist))
            worklist.remove(node)

            # Get predecessors' out values
            pred_outs = [
                self._out.get(pred, self.bottom()) 
                for pred in self._get_predecessors(node)
            ]
            
            # Compute new in value using meet
            new_in = reduce(self.meet, pred_outs, self.bottom())
            # Compute new out value using transfer
            new_out = self.transfer(node, new_in)

            # Update values if they changed
            if (new_in != self._in.get(node, self.bottom()) or 
                new_out != self._out.get(node, self.bottom())):
                self._in[node] = new_in
                self._out[node] = new_out
                # Add successors to worklist
                worklist.update(self._get_successors(node))

    def analyze(self, root: ir.Node):
        """
        Build the flow graph and solve the dataflow equations.
        This should be called after all flows have been added.
        """
        self._solve()

    def get_in(self, node: ir.Node) -> T:
        """Get the dataflow value flowing into a node."""
        return self._in.get(node, self.bottom())

    def get_out(self, node: ir.Node) -> T:
        """Get the dataflow value flowing out of a node."""
        return self._out.get(node, self.bottom())