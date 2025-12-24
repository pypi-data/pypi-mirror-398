import typing
import v0.relationalai

import v0.relationalai.experimental
import v0.relationalai.experimental.pathfinder
import v0.relationalai.experimental.pathfinder.bridge
from v0.relationalai.experimental.pathfinder.rpq import RPQ

__all__ = [
    'node_filter',
    'node',
    'edge',
    'path',
    'optional',
    'plus',
    'star',
    'union',
    'RPQ',
    'find_paths'
]

#-----------------------------------------------------------------------------
# Parsing RPQ elements specified with strings (node and edge labels).
#-----------------------------------------------------------------------------

Segment = typing.Union[str, v0.relationalai.dsl.Type, RPQ]

def _process_segment(s: Segment) -> RPQ:
    from v0.relationalai.experimental.pathfinder.filter import NodeLabel, parse_label
    from v0.relationalai.experimental.pathfinder.rpq import Node, Edge

    if isinstance(s, str):
        label = parse_label(s)
        if isinstance(label, NodeLabel):
            return Node(label)
        else:
            return Edge(label)
    elif isinstance(s, v0.relationalai.dsl.Type):
        return Node(NodeLabel(s._type.name))
    elif isinstance(s, RPQ):
        return s
    else:
        raise Exception(f"Incorrect type {type(s)} of segment '{s}'")


#-----------------------------------------------------------------------------
# User-facing RPQ constructors
#-----------------------------------------------------------------------------

# (filter)
def node_filter(filter: typing.Callable) -> RPQ:
    from v0.relationalai.experimental.pathfinder.filter import AnonymousNodeFilter
    from v0.relationalai.experimental.pathfinder.rpq import Node

    return Node(label = None, filter = AnonymousNodeFilter(filter))


# (node_lab {∧ filter})
def node(node_lab: typing.Union[str,v0.relationalai.dsl.Type],
         filter: typing.Optional[typing.Callable] = None) -> RPQ:
    from v0.relationalai.experimental.pathfinder.filter import (
        NodeLabel, AnonymousNodeFilter, parse_label
    )
    from v0.relationalai.experimental.pathfinder.rpq import Node

    filter = AnonymousNodeFilter(filter) if filter is not None else None

    if isinstance(node_lab, v0.relationalai.dsl.Type):
        label = NodeLabel(node_lab._type.name)
    else:
        label = parse_label(node_lab)
    assert isinstance(label, NodeLabel), f"Expected a node label, got {label}"

    return Node(label, filter)

# -[edge_lab {∧ filter}]- or <-[edge_lab {∧ filter}]-
def edge(edge_lab:str, filter: typing.Optional[typing.Callable] = None) -> RPQ:
    from v0.relationalai.experimental.pathfinder.filter import (
        EdgeLabel, AnonymousEdgeFilter, parse_label
    )
    from v0.relationalai.experimental.pathfinder.rpq import Edge

    label = parse_label(edge_lab)
    assert isinstance(label, EdgeLabel), f"Expected an edge label, either `-[...]->` or `<-[...]-`, got {label}"
    filter = AnonymousEdgeFilter(filter) if filter is not None else None
    return Edge(label, filter)


# (expr₁ ⋅ ... ⋅ exprₙ)
def path(segment: Segment, *segments: Segment) -> RPQ:
    from v0.relationalai.experimental.pathfinder.rpq import Concat

    pattern = _process_segment(segment)
    for seg in segments:
        pattern = Concat(pattern, _process_segment(seg))

    return pattern

# (expr₁ ⋅ ... ⋅ exprₙ)?
def optional(*segments: Segment) -> RPQ:
    from v0.relationalai.experimental.pathfinder.rpq import Optional

    return Optional(path(*segments))

# (expr₁ ⋅ ... ⋅ exprₙ)+
def plus(segment: Segment, *segments: Segment) -> RPQ:
    from v0.relationalai.experimental.pathfinder.rpq import Plus

    return Plus(path(segment, *segments))

# (expr₁ ⋅ ... ⋅ exprₙ)*
def star(segment: Segment, *segments: Segment) -> RPQ:
    from v0.relationalai.experimental.pathfinder.rpq import Star

    return Star(path(segment, *segments))

# (expr₁ | ... | exprₙ)
def union(segment: Segment, *segments: Segment) -> RPQ:
    from v0.relationalai.experimental.pathfinder.rpq import Union

    pattern = _process_segment(segment)
    for seg in segments:
        pattern = Union(pattern, _process_segment(seg))

    return pattern

#-----------------------------------------------------------------------------
# UI for path finding
#-----------------------------------------------------------------------------

# Create a type storing paths specified by the given RPQ pattern.
def find_paths(pattern: RPQ, **params):
    from v0.relationalai.experimental.pathfinder.options import normalized_options
    from v0.relationalai.experimental.pathfinder.bridge import invoke_pathfinder

    options = normalized_options(params)

    return invoke_pathfinder(pattern, options)

# Creates a connectivity relation from a given RPQ pattern.
def conn(pattern: RPQ, **params):
    from v0.relationalai.std import rel
    from v0.relationalai.dsl import create_vars
    from v0.relationalai.experimental.pathfinder.options import normalized_options
    from v0.relationalai.experimental.pathfinder.compiler import compile_conn
    from v0.relationalai.experimental.pathfinder.datalog import install_program
    from v0.relationalai.experimental.pathfinder.utils import get_model

    options = {**normalized_options(params), 'suppress_groundedness_test': True}
    program = compile_conn(pattern, options)
    pq_conn_rel = program.root_rel['conn_rel']

    install_program(get_model(options), program, options)

    x, y = create_vars(2)
    getattr(rel, pq_conn_rel)(x, y)

    return x, y
