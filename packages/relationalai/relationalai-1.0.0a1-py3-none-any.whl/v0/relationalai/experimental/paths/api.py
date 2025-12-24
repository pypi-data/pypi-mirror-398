import typing
from .rpq.rpq import RPQ, Segment, _process_segment, Star
from .rpq.rpq import Node, Edge, Concat, Optional, Plus, Union
from .rpq.filter import AnonymousNodeFilter
from .find_paths_via_automaton import find_paths_via_automaton
from .product_graph import project_product_graph_paths_to_original_graph

from v0.relationalai.semantics import Concept, Relationship, define

#-----------------------------------------------------------------------------
# User-facing RPQ constructors
#-----------------------------------------------------------------------------

# (filter)
def node_filter(filter: typing.Callable) -> RPQ:
    from .rpq import Node

    return Node(label = None, filter = AnonymousNodeFilter(filter))


# (node_lab {∧ filter})
def node(node_lab: typing.Union[str,Concept],
         filter: typing.Optional[typing.Callable] = None) -> RPQ:
    from .rpq.filter import NodeLabel, parse_label

    filter = AnonymousNodeFilter(filter) if filter is not None else None

    if isinstance(node_lab, Concept):
        label = NodeLabel(node_lab._name)
    else:
        label = parse_label(node_lab)
    assert isinstance(label, NodeLabel), f"Expected a node label, got {label}"

    return Node(label, filter)

# -[edge_lab {∧ filter}]- or <-[edge_lab {∧ filter}]-
def edge(edge_lab:str, filter: typing.Optional[typing.Callable] = None) -> RPQ:
    from .rpq.filter import EdgeLabel, AnonymousEdgeFilter, parse_label

    label = parse_label(edge_lab)
    assert isinstance(label, EdgeLabel), f"Expected an edge label, either `-[...]->` or `<-[...]-`, got {label}"
    filter = AnonymousEdgeFilter(filter) if filter is not None else None
    return Edge(label, filter)


# (expr₁ ⋅ ... ⋅ exprₙ)
def path(segment: Segment, *segments: Segment) -> RPQ:

    pattern = _process_segment(segment)
    for seg in segments:
        pattern = Concat(pattern, _process_segment(seg))

    return pattern

# (expr₁ ⋅ ... ⋅ exprₙ)?
def optional(*segments: Segment) -> RPQ:

    return Optional(path(*segments))

# (expr₁ ⋅ ... ⋅ exprₙ)+
def plus(segment: Segment, *segments: Segment) -> RPQ:

    return Plus(path(segment, *segments))

# (expr₁ ⋅ ... ⋅ exprₙ)*
def star(segment: Segment, *segments: Segment) -> RPQ:

    return Star(path(segment, *segments))

# (expr₁ | ... | exprₙ)
def union(segment: Segment, *segments: Segment) -> RPQ:

    pattern = _process_segment(segment)
    for seg in segments:
        pattern = Union(pattern, _process_segment(seg))

    return pattern

#-----------------------------------------------------------------------------
# UI for path finding
#-----------------------------------------------------------------------------


def match(graph, pattern, source=None, target=None,
          num_paths=None, max_length=1000,
          type="shortest"):
    """
    Find paths matching a given pattern in the graph from src to dst.

    Args:
        graph: The graph
        pattern: RPQ pattern
        src: Source node entity
        dst: Destination node entity

    Returns:
        Projected paths in the original graph
    """

    model = graph.model
    Node = graph.Node

    # Convert the pattern to an automaton
    g = pattern.glushkov()
    automaton = g.automaton()
    automaton.reduce()

    # Print the automaton for debugging
    # print(automaton)

    # Find paths via the automaton

    # allow a single source node; if so, wrap it in a relationship:
    if source is None:
        Source = Node
    elif isinstance(source, Concept) or isinstance(source, Relationship):
        Source = source
    else:
        Source = model.Relationship(f"source {{{Node}}}")
        define(Source(source))

    if target is None:
        Target = Node
    elif isinstance(target, Concept) or isinstance(target, Relationship):
        Target = target
    else:
        Target = model.Relationship(f"target {{{Node}}}")
        define(Target(target))

    # Source.inspect()
    # Target.inspect()

    product_graph, product_graph_paths = find_paths_via_automaton(
        graph, automaton, Source, Target,
        num_paths=num_paths, max_length=max_length,
        type=type)

    # Project the paths back to the original graph
    projected_paths = project_product_graph_paths_to_original_graph(product_graph, product_graph_paths, automaton)

    return projected_paths


