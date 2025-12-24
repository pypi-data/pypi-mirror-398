# For builder components.
from v0.relationalai.semantics import Integer, define
from v0.relationalai.experimental.paths.graph import Graph


def ball_with_repetition(g:Graph, Source, max_length):
    edge = g.Edge
    Node = g.Node

    ball = g.model.Relationship(f"ball_rep {{Integer}} {{{Node}}}") # , [Integer, Node])

    u, v, src = Node.ref(), Node.ref(), Node.ref()
    level, m = Integer.ref(), Integer.ref()

    # Base case: a node is reachable from itself
    define(ball(0, src)).where(Source(src))

    # Recursive case:
    define(ball(level, v)).where(
        ball(m, u),
        m == level - 1,
        edge(u, v),
        level <= max_length
    )

    return ball
