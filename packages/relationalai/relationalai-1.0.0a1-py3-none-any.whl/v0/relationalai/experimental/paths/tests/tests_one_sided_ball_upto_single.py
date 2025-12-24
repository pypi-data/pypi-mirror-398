from v0.relationalai.semantics import Model, Integer, define, select
from v0.relationalai.experimental.paths.graph import Graph
from v0.relationalai.experimental.paths.path_algorithms.one_sided_ball_upto import ball_upto


# First test with grid graph
model_grid = Model("test_one_sided_ball_upto grid", dry_run=False)
grid = Graph.construct_grid(model_grid, 3)

n = Integer.ref()
u = grid.Node.ref()

source_1 = grid.Node.new(row = 1, col = 1)
target_1 = grid.Node.new(row = 2, col = 2)

Source_1 = model_grid.Concept("Source_1", extends=[grid.Node])
Target_1 = model_grid.Concept("Target_1", extends=[grid.Node])

define(Source_1(source_1))
define(Target_1(target_1))

source_ball_1 = ball_upto(grid, Source_1, Target_1)
iter_set_1 = select(n, u.row, u.col).where(source_ball_1(n, u)).to_df()
set_ball_1 = set(row for row in iter_set_1.itertuples(index = False, name = None))

expected_ball_1 = {
    (0, 1, 1), (1, 2, 1), (1, 1, 2), (2, 3, 1), (2, 2, 2), (2, 1, 3)
}

assert set_ball_1 == expected_ball_1


# Second test with grid graph
target_2 = grid.Node.new(row = 3, col = 3)

Target_2 = model_grid.Concept("Target_2", extends=[grid.Node])

define(Target_2(target_2))

source_ball_2 = ball_upto(grid, Source_1, Target_2)
iter_set_2 = select(n, u.row, u.col).where(source_ball_2(n, u)).to_df()
set_ball_2 = set(row for row in iter_set_2.itertuples(index = False, name = None))

expected_ball_2 = {
    (0, 1, 1), (1, 2, 1), (1, 1, 2), (2, 3, 1), (2, 2, 2), (2, 1, 3), (3, 3, 2), (3, 2, 3), (4, 3, 3)
}

assert set_ball_2 == expected_ball_2


# Test with diamond graph
model_diamond = Model("test_one_sided_ball_upto diamond", dry_run=False)

diamond = Graph.construct_diamond(model_diamond, 3)

v = diamond.Node.ref()

source_3 = diamond.Node.new(id = 2)
target_3 = diamond.Node.new(id = 8)

Source_3 = model_diamond.Concept("Source_3", extends=[diamond.Node])
Target_3 = model_diamond.Concept("Target_3", extends=[diamond.Node])

define(Source_3(source_3))
define(Target_3(target_3))

source_ball_3 = ball_upto(diamond, Source_3, Target_3)
iter_set_3 = select(n, v.id).where(source_ball_3(n, v)).to_df()
set_ball_3 = set(row for row in iter_set_3.itertuples(index = False, name = None))

expected_ball_3 = {
    (0, 2), (1, 4), (2, 5), (2, 6), (3, 7), (4, 8), (4, 9)
}

assert set_ball_3 == expected_ball_3