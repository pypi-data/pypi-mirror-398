# For builder components.
from v0.relationalai.semantics import Integer, define
from v0.relationalai.experimental.paths.graph import Graph


def two_balls_repetition(g:Graph, Source, Target, max_length):
    edge = g.Edge
    Node = g.Node

    source_ball = g.model.Relationship(f"source_ball1 {{Integer}} {{{Node}}}")
    target_ball = g.model.Relationship(f"target_ball1 {{Integer}} {{{Node}}}")

    radius_S = max_length // 2
    radius_T = max_length - radius_S

    u, v, src, tgt = Node.ref(), Node.ref(), Node.ref(), Node.ref()
    level = Integer.ref()

    # Ball around src contains src at distance 0:
    define(source_ball(0, src)).where(Source(src))

    # Recursive case:
    define(source_ball(level, u)).where(
        level <= radius_S,
        source_ball(level - 1, v),
        edge(v, u)
    )

    # Ball around dst contains dst at distance 0:
    define(target_ball(0, tgt)).where(Target(tgt))

    # Recursive case:
    define(target_ball(level, u)).where(
        level <= radius_T,
        target_ball(level - 1, v),
        edge(u, v)
    )

    return source_ball, target_ball
