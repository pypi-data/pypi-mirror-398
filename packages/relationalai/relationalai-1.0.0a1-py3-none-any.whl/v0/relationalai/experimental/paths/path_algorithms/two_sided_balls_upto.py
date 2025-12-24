# For builder components.
from v0.relationalai.semantics import Integer, define, not_, count
from v0.relationalai.experimental.paths.graph import Graph
from v0.relationalai.experimental.paths.utilities.iterators import setup_iteration


def two_balls_upto(g:Graph, Source, Target, max_length=None):
    edge = g.Edge
    Node = g.Node

    source_ball = g.model.Relationship(f"source_ball2 {{Integer}} {{{Node}}}")
    target_ball = g.model.Relationship(f"target_ball2 {{Integer}} {{{Node}}}")
    source_condition = g.model.Relationship("source_condition1 {Integer}")
    target_condition = g.model.Relationship("target_condition1 {Integer}")
    source_surface = g.model.Relationship("source_surface1 {Integer}")
    target_surface = g.model.Relationship("target_surface1 {Integer}")

    if max_length is None:
        radius_S = setup_iteration(g.model, source_condition, 0, 1000000)
        radius_T = setup_iteration(g.model, target_condition, 0, 1000000)
    else:
        half_radius = max_length//2
        radius_S = setup_iteration(g.model, source_condition, 0, half_radius)
        radius_T = setup_iteration(g.model, target_condition, 0, max_length - half_radius)

    u, v, w, src, tgt = Node.ref(), Node.ref(), Node.ref(), Node.ref(), Node.ref()
    m, n, k, l1, l2 = Integer.ref(), Integer.ref(), Integer.ref(), Integer.ref(), Integer.ref()

    # Ball around src contains src at distance 0:
    define(source_ball(0, src)).where(Source(src))

    # Recursive case:
    define(source_ball(k, u)).where(
        radius_S(k),
        source_ball(k - 1, v),
        edge(v, u),
        not_(
            source_ball(n, u),
            n < k
        )
    )

    define(source_ball(k, u)).where(
        source_ball(k, u)
    )

    # Ball around dst contains dst at distance 0:
    define(target_ball(0, tgt)).where(Target(tgt))

    # Recursive case:
    define(target_ball(k, u)).where(
        radius_T(k),
        target_ball(k - 1, v),
        edge(u, v),
        not_(
            target_ball(n, u),
            n < k
        )
    )

    define(target_ball(k, u)).where(
        target_ball(k, u)
    )

    define(source_condition(n)).where(
        radius_S(n),
        source_ball(n, u),
        radius_T(m),
        target_ball(m, v),
        not_(
            source_ball(n, w),
            target_ball(m, w)
        ),
        source_surface(l1),
        target_surface(l2),
        l1 < l2
    )

    define(target_condition(m)).where(
        radius_S(n),
        source_ball(n, u),
        radius_T(m),
        target_ball(m, v),
        not_(
            source_ball(n, w),
            target_ball(m, w)
        ),
        source_surface(l1),
        target_surface(l2),
        l1 >= l2
    )

    define(target_surface(count(u))).where(
        radius_T(n),
        target_ball(n, u)
    )

    define(source_surface(count(u))).where(
        radius_S(n),
        source_ball(n, u)
    )

    return source_ball, target_ball