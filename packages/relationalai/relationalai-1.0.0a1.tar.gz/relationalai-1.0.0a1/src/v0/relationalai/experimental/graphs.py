from ..std.graphs import Graph
from ..std import minimum, maximum
from enum import Enum

# --------------------------------------------------
# to_undirected_graph
# --------------------------------------------------

class AggregationFunction(Enum):
    SUM = 0
    MIN = 1
    MAX = 2
_Agg = AggregationFunction

def to_undirected_graph(model, in_graph:Graph, attributes=[], *, aggregation:_Agg):
    # This expects a directed graph that does not have multi-edges in Set semantics.
    # Examples
    # The edges  (1, 2, 1.0) and (1, 2, 1.0) are allowed but will be counted once.
    # The edges  (1, 2, 1.0) and (2, 1, 1.0) are allowed, and will
    #   be transformed into one undirected edge between nodes 1 and 2 with weight
    #   2.0 (if the aggregation is sum), or 1.0 (if the aggregation is max or min).
    # The edges  (1, 2, 1.0) and (2, 1, 2.0) are allowed, and will
    #   be transformed into one undirected edge between nodes 1 and 2 with weight
    #   3.0 (if the aggregation is sum), or 1.0 (if the aggregation is min)
    #   or 2.0 (if the aggregation is max).
    # The edges  (1, 2, 2.0) and (2, 1, 1.0) and (2, 1, 1.0) are allowed, and will
    #   be transformed into one undirected edge between nodes 1 and 2 with weight
    #   3.0 (if the aggregation is sum), or 1.0 (if the aggregation is min)
    #   or 2.0 (if the aggregation is max).
    assert not in_graph.undirected, f"Expect directed input graph. Got undirected input `graph{in_graph.id}`."

    # Create graph
    out_graph = Graph(model, undirected = True, weighted = in_graph.weighted)
    OutNode, OutEdge = out_graph.Node, out_graph.Edge
    InNode, InEdge = in_graph.Node, in_graph.Edge

    # We get automatic error detection if we pass an attribute that does not exist.
    # And if a certain node does not have an attribute, and others have that attribute,
    # it will be set to null (Rel takes care of this).
    OutNode.extend(InNode)
    with model.rule():
        n = InNode()
        OutNode(n).set(**{attr: getattr(n, attr) for attr in attributes})

    if in_graph.weighted:

        # E(a,b) and not E(b,a)
        with model.rule():
            e1 = InEdge()
            with model.not_found():
                InEdge(from_ = e1.to, to = e1.from_)
            OutEdge.add(from_ = e1.from_, to = e1.to, weight = e1.weight)

        # E(a,b) and E(b,a)
        with model.rule():
            e1 = InEdge()
            # This is a useful performance improvement, since we cut
            # the size of the produced edge-list in half. Additionally, it
            # excludes self loops from the aggregation, which would be
            # incorrect. Self-loops are handled separately, below.
            e1.from_ < e1.to
            e2 = InEdge(from_ = e1.to, to = e1.from_)
            if aggregation == _Agg.SUM:
                OutEdge.add(from_ = e1.from_, to = e1.to, weight = e1.weight + e2.weight)
            elif aggregation == _Agg.MIN:
                OutEdge.add(from_ = e1.from_, to = e1.to, weight = minimum(e1.weight, e2.weight))
            elif aggregation == _Agg.MAX:
                OutEdge.add(from_ = e1.from_, to = e1.to, weight = maximum(e1.weight, e2.weight))

        # E(a,a)
        with model.rule():
            e1 = InEdge()
            e1.from_ == e1.to
            OutEdge.add(from_ = e1.from_, to = e1.to, weight = e1.weight)

    else:  # Unweighted input

        with model.rule():
            e = InEdge()
            OutEdge.add(from_ = e.from_, to = e.to)

    return out_graph
