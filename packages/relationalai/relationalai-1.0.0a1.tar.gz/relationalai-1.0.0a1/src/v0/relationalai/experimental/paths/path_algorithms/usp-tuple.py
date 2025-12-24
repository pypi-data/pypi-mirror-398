# For builder components.
from v0.relationalai.semantics import Model, Integer, define, max, sum, select, not_
from v0.relationalai.experimental.paths.graph import Graph
from v0.relationalai.experimental.paths.path_algorithms.one_sided_ball_upto import ball_upto
from v0.relationalai.experimental.paths.path_algorithms.one_sided_ball_repetition import ball_with_repetition


def compute_usp(g: Graph, Source, Target, max_length = None):
    # Computes the Union of Shortest Paths (USP) from a source set to a destination set
    # USP is a subgraph of the original graph

    edge = g.Edge
    Node = g.Node

    n, d = Integer.ref(), Integer.ref()
    tgt, u, v = Node.ref(), g.Node.ref(), g.Node.ref()

    if max_length is None:
        ball = ball_upto(g, Source, Target)
        usp_nodes = g.model.Relationship(f"usp_nodes1 {{{Node}}}")
        usp = g.model.Relationship(f"usp1 {{{Node}}} {{{Node}}}")
        boundary = g.model.Relationship(f"boundary1 {{{Node}}}")

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
        max_dist = g.model.Relationship("max_dist1 {Integer}")
        NodeDist = g.model.Concept("NodeDist")
        usp = g.model.Relationship(f"usp2 {{{NodeDist}}} {{{NodeDist}}}")
        boundary = g.model.Relationship(f"boundary2 {{{NodeDist}}}")

        define(NodeDist.new(node = u, layer = n)).where(
            ball(n, u)
        )

        define(max_dist(max(n))).where(
            ball(n, tgt),
            Target(tgt)
        )

        uu, vv, ww = NodeDist.ref(), NodeDist.ref(), NodeDist.ref()

        define(boundary(uu)).where(
            NodeDist(uu),
            max_dist(n),
            Target(tgt),
            ball(n, tgt),
            uu.node == tgt,
            uu.layer == n
        )

        define(usp(uu, vv)).where(
            boundary(vv),
            NodeDist(uu),
            vv.node == v,
            vv.layer == n + 1,
            uu.node == u,
            uu.layer == n,
            ball(n, u),
            edge(u, v)
        )

        define(usp(uu, vv)).where(
            usp(vv, ww),
            vv.node == v,
            vv.layer == n + 1,
            uu.node == u,
            uu.layer == n,
            ball(n, u),
            edge(u, v)
        )


    return usp, boundary




def compute_nsp_from_usp(g: Graph, usp, Source, Target, Boundary):
    Node = g.Node

    n, m = Integer.ref(), Integer.ref()
    tgt, u, v = Node.ref(), Node.ref(), Node.ref()

    """if max_dist is None:
        nsp = g.model.Relationship(f"nsp2 {{{Node}}} {{Integer}}")
        define(nsp(tgt, 1)).where(
            Target(tgt),
            usp(u, tgt)
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
    """
    nsp = g.model.Relationship(f"nsp1 {{{Node}}} {{Integer}} {{Integer}}")

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

    if max_length is None:
        usp, Boundary = compute_usp(g, Source, Target)
        nsp = compute_nsp_from_usp(g, usp, Source, Target, Boundary)
    else:
        usp, Boundary  = compute_usp(g, Source, Target, max_length)
        nsp = compute_nsp_from_usp(g, usp, Source, Target, Boundary)

    return nsp


model = Model("test_usp_nsp_single", dry_run=False)

grid1 = Graph.construct_grid(model, 2, "undirected")

source1 = grid1.Node.new(row = 1, col = 1)
target1 = grid1.Node.new(row = 2, col = 2)

Source1 = model.Concept("Source1", extends=[grid1.Node])
Target1 = model.Concept("Target1", extends=[grid1.Node])

define(Source1(source1))
define(Target1(target1))
define(Target1(source1))

usp, boundary = compute_usp(grid1, Source1, Target1, 4)

usp.inspect()
#nsp = compute_nsp(grid1, Source1, Target1, 4)


u, v = grid1.Node.ref(), grid1.Node.ref(),
n, m = Integer.ref(), Integer.ref()

select(u, v).where(usp(u, v)).inspect()


# select(u.row, u.col, n, m).where(nsp(u, n, m)).inspect()