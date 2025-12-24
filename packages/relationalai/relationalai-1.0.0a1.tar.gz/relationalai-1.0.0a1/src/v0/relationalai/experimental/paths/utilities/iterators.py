from v0.relationalai.semantics import Integer, define, max


def setup_iteration(model, condition, initial = 0, final = 50):
    iter = model.Relationship("iter1 {Integer}")
    next = model.Relationship("next1 {Integer}")

    m, n = Integer.ref(), Integer.ref()

    define(next(initial))

    define(next(n)).where(
        iter(n)
    )

    define(next(n)).where(
        iter(m),
        n == m + 1,
        condition(m),
        n <= final
    )

    define(iter(max(n))).where(
        next(n)
    )

    return iter