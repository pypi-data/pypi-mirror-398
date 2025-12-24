# For builder components.
from v0.relationalai.semantics import Integer, define, sum, not_
from v0.relationalai.experimental.paths.graph import Graph
from v0.relationalai.experimental.paths.path_algorithms.one_sided_ball_upto import ball_upto
from v0.relationalai.experimental.paths.path_algorithms.one_sided_ball_repetition import ball_with_repetition


def compute_usp(g: Graph, Source, Target, max_length=None):
    # Computes the Union of Shortest Paths (USP) from a source set to a destination set
    # USP is a subgraph of the original graph

    edge = g.Edge
    Node = g.Node

    n, d = Integer.ref(), Integer.ref()
    tgt, u, v = Node.ref(), g.Node.ref(), g.Node.ref()

    ball = ball_upto(g, Source, Target, max_length)
    usp_nodes = g.model.Relationship(f"usp_nodes {{{Node}}}")
    usp = g.model.Relationship(f"usp {{{Node}}} {{{Node}}}")
    boundary = g.model.Relationship(f"usp_boundary {{{Node}}}")

    # propagate backwards to find the nodes that are in the USP:
    define(boundary(tgt)).where(
        Target(tgt),
        ball(n, tgt)
    )

    define(usp_nodes(tgt)).where(
        boundary(tgt)
    )

    define(usp_nodes(u)).where(
        usp(u, v)
    )

    define(usp(u, v)).where(
        usp_nodes(v),
        ball(d, v),
        ball(d - 1, u),
        edge(u, v)
    )

    return usp, boundary


def compute_uw(g: Graph, Source, Target, max_length):
    # Computes the Union of Walks (UW) up to a given length from a source set to a destination set

    edge = g.Edge
    Node = g.Node

    n = Integer.ref()
    tgt, u, v, w = Node.ref(), g.Node.ref(), g.Node.ref(), g.Node.ref()

    ball = ball_with_repetition(g, Source, max_length)
    uw = g.model.Relationship(f"uw {{{Node}}} {{Integer}} {{{Node}}}")
    boundary = g.model.Relationship(f"boundary {{{Node}}} {{Integer}}")

    define(uw(u, n, tgt)).where(
        Target(tgt),
        ball(n + 1, tgt),
        ball(n, u),
        edge(u, tgt)
    )

    define(uw(u, n, v)).where(
        uw(v, n + 1, w),
        ball(n, u),
        edge(u, v)
    )

    define(boundary(tgt, n)).where(
        Target(tgt),
        ball(n, tgt),
        not_(uw(tgt, n, u))
    )

    return uw, boundary


def compute_nsp_from_usp(g: Graph, usp, Source, Target, Boundary):
    Node = g.Node

    n = Integer.ref()
    tgt, u, v = Node.ref(), Node.ref(), Node.ref()

    nsp = g.model.Relationship(f"num_shortest {{{Node}}} {{Integer}}")

    define(nsp(tgt, 1)).where(
        Boundary(tgt)
    )

    define(nsp(tgt, 1)).where(
        Target(tgt),
        Source(tgt)
    )

    define(nsp(u, sum(v, n).per(u))).where(
        nsp(v, n),
        usp(u, v)
    )

    return nsp


def compute_nw_from_uw(g: Graph, usp, Target, Boundary):
    Node = g.Node

    n, m = Integer.ref(), Integer.ref()
    tgt, u, v = Node.ref(), Node.ref(), Node.ref()

    nw = g.model.Relationship(f"num_walks {{{Node}}} {{Integer}} {{Integer}}")

    define(nw(tgt, n, 1)).where(
        Boundary(tgt, n)
    )

    define(nw(u, n, sum(v, n + 1, m).per(u, n))).where(
        nw(v, n + 1, m),
        usp(u, n, v),
        not_(Target(u))
    )

    define(nw(u, n, 1 + sum(v, n + 1, m).per(u, n))).where(
        nw(v, n + 1, m),
        usp(u, n, v),
        Target(u),
        not_(Boundary(u, n))
    )

    return nw


def compute_nsp(g: Graph, Source, Target):
    # Computes the number of shortest paths (NSP) from a source set to a destination set

    usp, Boundary  = compute_usp(g, Source, Target)
    nsp = compute_nsp_from_usp(g, usp, Source, Target, Boundary)

    return nsp


def compute_nw(g: Graph, Source, Target, max_length):
    # Computes the number of shortest paths (NSP) from a source set to a destination set

    uw, Boundary  = compute_uw(g, Source, Target, max_length)
    nw = compute_nw_from_uw(g, uw, Target, Boundary)

    return nw
