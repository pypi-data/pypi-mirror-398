from v0.relationalai.semantics import Model, Integer, define, select
from v0.relationalai.experimental.paths.graph import Graph
from v0.relationalai.experimental.paths.path_algorithms.one_sided_ball_repetition import ball_with_repetition


# Test with grid graph
model_grid = Model("tests_one_sided_ball_repetition grid", dry_run=False)

grid = Graph.construct_grid(model_grid, 3)

n = Integer.ref()
u = grid.Node.ref()

source_1 = grid.Node.new(row = 1, col = 2)

Source_1 = model_grid.Concept("Source_1", extends=[grid.Node])

define(Source_1(source_1))

source_ball_1 = ball_with_repetition(grid, Source_1, 3)
iter_set_1 = select(n, u.row, u.col).where(source_ball_1(n, u)).to_df()
set_ball_1 = set(row for row in iter_set_1.itertuples(index = False, name = None))

expected_ball_1 = {
    (0, 1, 2), (1, 2, 2), (1, 1, 3), (2, 3, 2), (2, 2, 3), (3, 3, 3)
}

assert set_ball_1 == expected_ball_1


# First test with diamond graph
model_diamond = Model("tests_one_sided_ball_repetition diamond", dry_run=False)

diamond = Graph.construct_diamond(model_diamond, 3)

v = diamond.Node.ref()

source_2 = diamond.Node.new(id = 2)

Source_2 = model_diamond.Concept("Source_2", extends=[diamond.Node])

define(Source_2(source_2))

source_ball_2 = ball_with_repetition(diamond, Source_2, 4)
iter_set_2 = select(n, v.id).where(source_ball_2(n, v)).to_df()
set_ball_2 = set(row for row in iter_set_2.itertuples(index = False, name = None))

expected_ball_2 = {
    (0, 2), (1, 4), (2, 5), (2, 6), (3, 7), (4, 8), (4, 9)
}

assert set_ball_2 == expected_ball_2


# Second test with diamond graph
source_ball_3 = ball_with_repetition(diamond, Source_2, 0)
iter_set_3 = select(n, v.id).where(source_ball_3(n, v)).to_df()
set_ball_3 = set(row for row in iter_set_3.itertuples(index = False, name = None))

expected_ball_3 = {
    (0, 2)
}

assert set_ball_3 == expected_ball_3