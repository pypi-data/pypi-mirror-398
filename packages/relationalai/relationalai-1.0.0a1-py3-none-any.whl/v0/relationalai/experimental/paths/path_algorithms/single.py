# For builder components.
from v0.relationalai.semantics import Integer, where, define, select, min
from v0.relationalai.experimental.paths.graph import Graph
from v0.relationalai.experimental.paths.path_algorithms.one_sided_ball_repetition import ball_with_repetition
from v0.relationalai.experimental.paths.path_algorithms.one_sided_ball_upto import ball_upto

# find a (deterministic) path from src to dst inside the given ball
# where dst is at distance radius from src


def single_path(g: Graph, ball, dst, radius):
    edge = g.Edge
    Node = g.Node

    path = g.model.Relationship(f"path {{Integer}} {{v:{Node}}}")

    d = Integer.ref()
    u, v = Node.ref(), Node.ref()

    define(path(radius, dst))  # path of length 0 starts at src

    where(
        path(d, v),
        edge(u, v),
        ball(d - 1, u)
    ).define(path(d - 1, min(v, u).per(d)))

    return path


def single_walk(g: Graph, Source, Target, radius):
    Node = g.Node

    ball = ball_with_repetition(g, Source, radius)

    # choose a destination node at distance radius:
    u = Node.ref()
    dst = where(ball(radius, u), Target(u)).select(min(u))
    walk = single_path(g, ball, dst, radius)

    return walk


def single_shortest_path(g: Graph, Source, Target):
    Node = g.Node

    cand = g.model.Relationship(f"candidate {{Integer}} {{v:{Node}}}")

    ball = ball_upto(g, Source, Target)

    # choose a destination node at distance radius:
    level = Integer.ref()
    u, tgt = Node.ref(), Node.ref()
    define(cand(level, u)).where(ball(level, u), Target(u))
    radius = select(level).where(cand(level, u))
    tgt = select(min(u)).where(cand(level, u))
    path = single_path(g, ball, tgt, radius)

    return path
