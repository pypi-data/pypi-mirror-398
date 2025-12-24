# Find shortest paths and walks in a graph

from v0.relationalai.semantics import std, Integer, where, define, rank, sum, not_
from v0.relationalai.semantics.std.integers import int64



from ..graph import Graph
from ..utilities.prefix_sum import linear_prefix_sum_with_groupby
from .usp import compute_usp, compute_nsp_from_usp, compute_uw, compute_nw_from_uw



def range_int64(start, stop, step=1):
    """Helper for std.range with int64 arguments."""
    return std.range(int64(start), int64(stop), int64(step))


def find_shortest_paths(g: Graph, Source, Target, max_length=None, num_paths=None):
    Node = g.Node

    u, v, src = Node.ref(), Node.ref(), Node.ref()
    i, val, lo, hi = Integer.ref(), Integer.ref(), Integer.ref(), Integer.ref()
    level, n, m, path_num = Integer.ref(), Integer.ref(), Integer.ref(), Integer.ref()
    d, r, s, tot = Integer.ref(), Integer.ref(), Integer.ref(), Integer.ref()

    ord_source = g.model.Relationship(f"ord_source {{Integer}}th source node {{{Node}}}")
    total_paths = g.model.Relationship("total_paths {Integer}")
    int_source = g.model.Relationship(f"int_source paths from {{{Node}}} numbered {{Integer}} to {{Integer}}")
    paths_listing = g.model.Relationship(f"paths_listing {{{Node}}} {{Integer}} {{Integer}} {{Integer}}")
    paths = g.model.Relationship(f"paths {{{Integer}}} has {{{Integer}}}th node {{{Node}}}")
    neighbor = g.model.Relationship(f"neighbor {{{Node}}} neighbor {{Integer}} is {{{Node}}}")
    edge_nsp = g.model.Relationship(f"edge_nsp num shortest from {{{Node}}} through {{Integer}} neighbor {{Integer}}")
    acc_nsp = g.model.Relationship(f"acc_nsp num shortest from {{{Node}}} neighbor from 1 to {{Integer}} is {{Integer}}")
    nsp_interval = g.model.Relationship(f"nsp_interval {{{Node}}} {{Integer}} {{Integer}} {{Integer}}")
    path_routing = g.model.Relationship(f"path_routing {{{Node}}} {{Integer}} {{{Node}}} {{Integer}}")

    usp, Boundary = compute_usp(g, Source, Target, max_length)

    where(usp(u, v), r == rank(v).per(u)).define(neighbor(u, r, v))

    nsp = compute_nsp_from_usp(g, usp, Source, Target, Boundary)

    define(edge_nsp(u, i, val)).where(
        neighbor(u, i, v),
        nsp(v, val)
    )

    acc_nsp = linear_prefix_sum_with_groupby(edge_nsp)

    define(nsp_interval(u, i, lo, hi)).where(
        i == 1,
        lo == 1,
        acc_nsp(u, i, hi)
    )
    define(nsp_interval(u, i, lo, hi)).where(
        acc_nsp(u, i - 1, lo - 1),
        acc_nsp(u, i, hi)
    )

    define(ord_source(r, u)).where(
        Source(u),
        usp(u, v),
        r == rank(u)
    )

    define(ord_source(r, u)).where(
        Source(u),
        Target(u),
        r == rank(u)
    )

    if num_paths is not None:
        define(total_paths(num_paths))
    else:
        define(total_paths(sum(src, n))).where(nsp(src, n))

    define(int_source(src, n, m)).where(
        total_paths(tot),
        ord_source(1, src),
        n == 1,
        nsp(src, level),
        n <= tot,
        tot <= level,
        m == tot
    )

    define(int_source(src, n, m)).where(
        total_paths(tot),
        ord_source(1, src),
        n == 1,
        nsp(src, level),
        level < tot,
        m == level
    )

    define(int_source(src, n, m)).where(
        total_paths(tot),
        ord_source(d, src),
        ord_source(d-1, u),
        int_source(u, r, s),
        n == s + 1,
        nsp(src, level),
        n <= tot,
        tot <= s + level,
        m == tot
    )

    define(int_source(src, n, m)).where(
        total_paths(tot),
        ord_source(d, src),
        ord_source(d-1, u),
        int_source(u, r, s),
        n == s + 1,
        nsp(src, level),
        s + level < tot,
        m == s + level
    )

    where(
        int_source(src, n, m),
        path_num == range_int64(n, m + 1, 1),
        r == path_num - n + 1,
    ).define(paths_listing(src, r, 0, path_num))

    where(
        paths_listing(u, m, level - 1, path_num),
        path_routing(u, m, v, n)
    ).define(paths_listing(v, n, level, path_num))

    where(
        nsp_interval(u, i, lo, hi),
        m == range_int64(lo, hi + 1, 1),
        neighbor(u, i, v),
        n == m - lo + 1
    ).define(path_routing(u, m, v, n))

    define(paths(path_num, level, v)).where(
        paths_listing(v, n, level, path_num)
    )

    return paths


def find_walks(g: Graph, Source, Target, max_length, num_paths=None):
    Node = g.Node

    u, v, src = Node.ref(), Node.ref(), Node.ref()
    i, val, lo, hi = Integer.ref(), Integer.ref(), Integer.ref(), Integer.ref()
    level, n, m, path_num = Integer.ref(), Integer.ref(), Integer.ref(), Integer.ref()
    d, r, s, tot = Integer.ref(), Integer.ref(), Integer.ref(), Integer.ref()

    ord_source = g.model.Relationship(f"ord_source {{Integer}}th source node {{{Node}}}")
    total_paths = g.model.Relationship("total_paths {Integer}")
    int_source = g.model.Relationship(f"int_source paths from {{{Node}}} numbered {{Integer}} to {{Integer}}")
    paths_listing = g.model.Relationship(f"paths_listing {{{Node}}} {{Integer}} {{Integer}} {{Integer}}")
    paths = g.model.Relationship(f"paths {{{Integer}}} has {{{Integer}}}th node {{{Node}}}")
    neighbor = g.model.Relationship(f"neighbor pair {{{Node}}} {{Integer}} neighbor {{Integer}} is {{{Node}}}")
    edge_nsp = g.model.Relationship(f"edge_nsp num shortest from pair {{{Node}}} {{Integer}} through {{Integer}} neighbor {{Integer}}")
    acc_nsp = g.model.Relationship(f"acc_nsp num shortest from {{{Node}}} neighbor from 1 to {{Integer}} is {{Integer}}")
    nsp_interval = g.model.Relationship(f"nsp_interval {{{Node}}} {{Integer}} {{Integer}} {{Integer}} {{Integer}}")
    path_routing = g.model.Relationship(f"path_routing {{{Node}}} {{Integer}} {{Integer}} {{{Node}}} {{Integer}}")

    uw, Boundary = compute_uw(g, Source, Target, max_length)


    where(uw(u, n, v), r == rank(v).per(u, n)).define(neighbor(u, n, r, v))

    nw = compute_nw_from_uw(g, uw, Target, Boundary)

    define(edge_nsp(u, n, i, val)).where(
        neighbor(u, n, i, v),
        nw(v, n + 1, val)
    )

    acc_nsp = linear_prefix_sum_with_groupby(edge_nsp)

    define(nsp_interval(u, n, i, lo, hi)).where(
        i == 1,
        lo == 1,
        acc_nsp(u, n, i, hi)
    )
    define(nsp_interval(u, n, i, lo, hi)).where(
        acc_nsp(u, n, i - 1, lo - 1),
        acc_nsp(u, n, i, hi)
    )

    define(ord_source(r, u)).where(
        Source(u),
        uw(u, 0, v),
        r == rank(u)
    )

    define(ord_source(r, u)).where(
        Source(u),
        Target(u),
        r == rank(u)
    )

    if num_paths is not None:
        define(total_paths(num_paths))
    else:
        define(total_paths(sum(src, 0, n))).where(nw(src, 0, n))

    define(int_source(src, n, m)).where(
        total_paths(tot),
        ord_source(1, src),
        n == 1,
        nw(src, 0, level),
        n <= tot,
        tot <= level,
        m == tot
    )

    define(int_source(src, n, m)).where(
        total_paths(tot),
        ord_source(1, src),
        n == 1,
        nw(src, 0, level),
        level < tot,
        m == level
    )

    define(int_source(src, n, m)).where(
        total_paths(tot),
        ord_source(d, src),
        ord_source(d-1, u),
        int_source(u, r, s),
        n == s + 1,
        nw(src, 0, level),
        n <= tot,
        tot <= s + level,
        m == tot
    )

    define(int_source(src, n, m)).where(
        total_paths(tot),
        ord_source(d, src),
        ord_source(d-1, u),
        int_source(u, r, s),
        n == s + 1,
        nw(src, 0, level),
        s + level < tot,
        m == s + level
    )

    where(
        int_source(src, n, m),
        path_num == range_int64(n, m + 1, 1),
        r == path_num - n + 1,
    ).define(paths_listing(src, r, 0, path_num))

    where(
        paths_listing(u, m, level - 1, path_num),
        path_routing(u, level - 1, m, v, n),
        not_(Target(u))
    ).define(paths_listing(v, n, level, path_num))

    where(
        paths_listing(u, m, level - 1, path_num),
        path_routing(u, level - 1, m - 1, v, n),
        Target(u),
        m >= 2
    ).define(paths_listing(v, n, level, path_num))

    where(
        nsp_interval(u, level, i, lo, hi),
        m == range_int64(lo, hi + 1, 1),
        neighbor(u, level, i, v),
        n == m - lo + 1
    ).define(path_routing(u, level, m, v, n))

    define(paths(path_num, level, v)).where(
        paths_listing(v, n, level, path_num)
    )

    return paths

# Explicitly export relevant classes and functions
__all__ = []
