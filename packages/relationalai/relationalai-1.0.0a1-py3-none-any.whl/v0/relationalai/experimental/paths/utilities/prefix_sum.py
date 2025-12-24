from v0.relationalai.semantics import Integer, define, max

from .utilities import clone_relation

def linear_prefix_sum(list):
    result = list._model.Relationship("result1 {Integer} {Integer}")

    i, val, val1, val2 = Integer.ref(), Integer.ref(), Integer.ref(), Integer.ref()

    define(result(i, val)).where(
        list(i, val),
        i == 1
    )

    define(result(i, val)).where(
        result(i - 1, val1),
        list(i, val2),
        val == val1 + val2
    )

    return result

def linear_prefix_sum_with_groupby(r):
    result = clone_relation(r)
    i, n, val, val1, val2 = Integer.ref(), Integer.ref(), Integer.ref(), Integer.ref(), Integer.ref()

    if r._arity() == 3:
        u = r._field_refs[0]  # Assuming the first field is the grouping field

        define(result(u, 1, val)).where(
            r(u, 1, val)
        )

        define(result(u, i, val)).where(
            result(u, i - 1, val1),
            r(u, i, val2),
            val == val1 + val2
        )
    else:
        # Assuming the first two fields are the grouping fields
        u = r._field_refs[0]
        n = r._field_refs[1]

        define(result(u, n, 1, val)).where(
            r(u, n, 1, val)
        )

        define(result(u, n, i, val)).where(
            result(u, n, i - 1, val1),
            r(u, n, i, val2),
            val == val1 + val2
        )
        
    return result


def dynamic_prefix_sum(list):
    result = list._model.Relationship("result2 {Integer} {Integer}")
    L = list._model.Relationship("L1 {Integer} {Integer} {Integer}")
    B = list._model.Relationship("B1 {Integer} {Integer} {Integer}")
    B_max = list._model.Relationship("B_max1 {Integer} {Integer}")

    i, j, k = Integer.ref(), Integer.ref(), Integer.ref()
    val, val1, val2 = Integer.ref(), Integer.ref(), Integer.ref()

    define(B(i, 1, val)).where(list(i, val))
    define(B(i, j, val)).where(
        B(i, k, val1),
        B(i - k, k, val2),
        val == val1 + val2,
        j == 2 * k,
        i % j == 0
    )

    define(L(i, j, val)).where(
        B_max(i, j),
        B(i, j, val),
    )

    define(B_max(i, max(j).per(i))).where(
        B(i, j, k)
    )

    define(result(i, val)).where(L(i, i, val))
    define(result(i, val)).where(
        L(i, j, val1),
        result(i - j, val2),
        val == val1 + val2
    )

    return result