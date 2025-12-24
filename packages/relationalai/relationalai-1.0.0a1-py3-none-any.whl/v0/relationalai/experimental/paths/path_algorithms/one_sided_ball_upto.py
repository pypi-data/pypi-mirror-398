from v0.relationalai.semantics import Integer, define, not_
from ..graph import Graph
from ..utilities.iterators import setup_iteration


# Source and Target are concepts representing sets of nodes
def ball_upto(g:Graph, Source, Target, max_length=None):
    edge = g.Edge
    Node = g.Node

    # ball(d, ⋅) is the sphere of nodes at distance d from the source node
    # visited(d, ⋅) is the union of all balls up to distance d

    ball = g.model.Relationship(f"ball1 {{Integer}} {{{Node}}}") # , [Integer, Node])
    visited = g.model.Relationship(f"visited1 {{{Node}}}") # , [Integer, Node])
    condition = g.model.Relationship("condition1 {Integer}")

    if max_length is None:
        iter = setup_iteration(g.model, condition, 0, 1000000)
    else:
        iter = setup_iteration(g.model, condition, 0, max_length)

    src, tgt = Node.ref(), Node.ref()

    # Ball around src contains src at distance 0:
    define(ball(0, src)).where(Source(src))

    u, v = g.Node.ref(), g.Node.ref()
    n, k = Integer.ref(), Integer.ref()

    # Recursive case:
    define(ball(k, v)).where(
        iter(k),
        ball(k - 1, u),
        edge(u, v),
        not_(
            visited(v),
        ),
    )

    define(ball(k, u)).where(
        ball(k, u)
    )

    define(visited(u)).where(
        iter(k),
        ball(k, u)
    )

    define(visited(u)).where(
        visited(u)
    )

    define(condition(n)).where(
        iter(n),
        ball(n, u),
        not_(
            ball(n, tgt),
            Target(tgt)
        )
    )

    return ball


def ball_upto_alt(g:Graph, Source, Target, max_length=None):
    edge = g.Edge
    Node = g.Node

    # ball(d, ⋅) is the sphere of nodes at distance d from the source node

    ball = g.model.Relationship(f"ball2 {{Integer}} {{{Node}}}") # , [Integer, Node])
    condition = g.model.Relationship("condition2 {Integer}")

    if max_length is None:
        iter = setup_iteration(g.model, condition, 0, 1000000)
    else:
        iter = setup_iteration(g.model, condition, 0, max_length)

    src, tgt = Node.ref(), Node.ref()

    # Ball around src contains src at distance 0:
    define(ball(0, src)).where(Source(src))

    u, v = g.Node.ref(), g.Node.ref()
    n, k = Integer.ref(), Integer.ref()

    # Recursive case:
    define(ball(k, v)).where(
        iter(k),
        ball(k - 1, u),
        edge(u, v),
        not_(
            ball(n, v),
        ),
    )

    define(ball(k, u)).where(
        ball(k, u)
    )

    define(condition(n)).where(
        iter(n),
        ball(n, u),
        not_(
            ball(n, tgt),
            Target(tgt)
        )
    )

    return ball
