# For builder components.
from v0.relationalai.semantics import Integer, define, max, sum, not_
from v0.relationalai.experimental.paths.graph import Graph
from v0.relationalai.experimental.paths.path_algorithms.one_sided_ball_upto import ball_upto
from v0.relationalai.experimental.paths.path_algorithms.one_sided_ball_repetition import ball_with_repetition


def compute_usp(g: Graph, Source, Target, max_length = None):
    # Computes the Union of Shortest Paths (USP) from a source set to a destination set
    # USP is a subgraph of the original graph

    edge = g.Edge
    Node = g.Node

    n, d = Integer.ref(), Integer.ref()
    tgt, u, v, w = Node.ref(), g.Node.ref(), g.Node.ref(), g.Node.ref()

    if max_length is None:
        ball = ball_upto(g, Source, Target)
        usp_nodes = g.model.Relationship(f"Node {{{Node}}} is in the USP")
        usp = g.model.Relationship(f"Edge {{{Node}}} to {{{Node}}} is in the USP")
        boundary = g.model.Relationship(f"Target node {{{Node}}} is in the boundary of the ball")

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
    else:
        ball = ball_with_repetition(g, Source, max_length)
        max_dist = g.model.Relationship("The maximum distance of a target node form the source nodes is {Integer}")
        usp = g.model.Relationship(f"{{{Node}}} at distance {{Integer}} from the source nodes is connected with {{{Node}}}")
        boundary = g.model.Relationship(f"Target pair {{{Node}}} {{Integer}} is in the boundary of the ball")

        define(max_dist(max(n))).where(
            ball(n, tgt),
            Target(tgt)
        )

        define(boundary(tgt, n)).where(
            max_dist(n),
            Target(tgt),
            ball(n, tgt)
        )

        define(usp(u, n, tgt)).where(
            boundary(tgt, n + 1),
            ball(n, u),
            edge(u, v)
        )

        define(usp(u, n, v)).where(
            usp(v, n + 1, w),
            ball(n, u),
            edge(u, v)
        )


    return usp, boundary




def compute_nsp_from_usp(g: Graph, usp, Source, Target, Boundary):
    Node = g.Node

    n, m = Integer.ref(), Integer.ref()
    tgt, u, v = Node.ref(), Node.ref(), Node.ref()

    if usp._arity() == 2:
        nsp = g.model.Relationship(f"Number of shortest paths from {{{Node}}} to destination is {{Integer}}")

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
    else:
        nsp = g.model.Relationship(f"Number of shortest paths from pair {{{Node}}} {{Integer}} to destination is {{Integer}}")

        define(nsp(tgt, n, 1)).where(
            Boundary(tgt, n)
        )

        define(nsp(u, n, sum(v, n + 1, m).per(u, n))).where(
            nsp(v, n + 1, m),
            usp(u, n, v),
            not_(Target(u))
        )

        define(nsp(u, n, 1 + sum(v, n + 1, m).per(u, n))).where(
            nsp(v, n + 1, m),
            usp(u, n, v),
            Target(u),
            not_(Boundary(u, n))
        )

    return nsp


def compute_nsp(g: Graph, Source, Target, max_length = None):
    # Computes the number of shortest paths (NSP) from a source set to a destination set

    usp, Boundary  = compute_usp(g, Source, Target, max_length)
    nsp = compute_nsp_from_usp(g, usp, Source, Target, Boundary)

    return nsp
