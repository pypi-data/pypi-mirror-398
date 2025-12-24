from v0.relationalai.semantics import Model, Integer, define, select
from v0.relationalai.experimental.paths.graph import Graph
from v0.relationalai.experimental.paths.path_algorithms.two_sided_balls_repetition import two_balls_repetition


# Test with diamond graph
model_grid = Model("test_two_balls_repetition grid", dry_run=False)

grid = Graph.construct_grid(model_grid, 4)

n = Integer.ref()
u = grid.Node.ref()

source_1_1 = grid.Node.new(row = 1, col = 1)
source_1_2 = grid.Node.new(row = 2, col = 2)
target_1_1 = grid.Node.new(row = 3, col = 3)
target_1_2 = grid.Node.new(row = 4, col = 4)

Source_1 = model_grid.Concept("Source_1", extends=[grid.Node])
Target_1 = model_grid.Concept("Target_1", extends=[grid.Node])

define(Source_1(source_1_1))
define(Source_1(source_1_2))
define(Target_1(target_1_1))
define(Target_1(target_1_2))

source_ball_1, target_ball_1 = two_balls_repetition(grid, Source_1, Target_1, 1)
iter_source_1 = select(n, u.row, u.col).where(source_ball_1(n, u)).to_df()
set_source_ball_1 = set(row for row in iter_source_1.itertuples(index = False, name = None))
iter_target_1 = select(n, u.row, u.col).where(target_ball_1(n, u)).to_df()
set_target_ball_1 = set(row for row in iter_target_1.itertuples(index = False, name = None))

expected_source_ball_1 = {
    (0, 1, 1), (0, 2, 2)
}

expected_target_ball_1 = {
    (0, 4, 4), (1, 3, 4), (1, 4, 3), (0, 3, 3), (1, 3, 2), (1, 2, 3)
}

assert (
    set_source_ball_1 == expected_source_ball_1 and
    set_target_ball_1 == expected_target_ball_1
)


# First test with diamond graph
model_diamond = Model("test_two_balls_repetition diamond", dry_run=False)

diamond = Graph.construct_diamond(model_diamond, 3)

v = diamond.Node.ref()

source_2_1 = diamond.Node.new(id = 1)
source_2_2 = diamond.Node.new(id = 2)
target_2_1 = diamond.Node.new(id = 9)
target_2_2 = diamond.Node.new(id = 10)

Source_2 = model_diamond.Concept("Source_2", extends=[diamond.Node])
Target_2 = model_diamond.Concept("Target_2", extends=[diamond.Node])

define(Source_2(source_2_1))
define(Source_2(source_2_2))
define(Target_2(target_2_1))
define(Target_2(target_2_2))

source_ball_2, target_ball_2 = two_balls_repetition(diamond, Source_2, Target_2, 20)
iter_source_2 = select(n, v.id).where(source_ball_2(n, v)).to_df()
set_source_ball_2 = set(row for row in iter_source_2.itertuples(index = False, name = None))
iter_target_2 = select(n, v.id).where(target_ball_2(n, v)).to_df()
set_target_ball_2 = set(row for row in iter_target_2.itertuples(index = False, name = None))

expected_source_ball_2 = {
    (0, 1), (1, 2), (1, 3), (2, 4), (3, 5), (3, 6), (4, 7), (5, 8), (5, 9), (6, 10),
    (0, 2), (1, 4), (2, 5), (2, 6), (3, 7), (4, 8), (4, 9), (5, 10)
}

expected_target_ball_2 = {
    (0, 10), (1, 9), (1, 8), (2, 7), (3, 5), (3, 6), (4, 4), (5, 2), (5, 3), (6, 1),
    (0, 9), (1, 7), (2, 5), (2, 6), (3, 4), (4, 2), (4, 3), (5, 1)
}

assert (
    set_source_ball_2 == expected_source_ball_2 and
    set_target_ball_2 == expected_target_ball_2
)


# Second test with diamond graph
source_ball_3, target_ball_3 = two_balls_repetition(diamond, Source_2, Target_2, 0)
iter_source_3 = select(n, v.id).where(source_ball_3(n, v)).to_df()
set_source_ball_3 = set(row for row in iter_source_3.itertuples(index = False, name = None))
iter_target_3 = select(n, v.id).where(target_ball_3(n, v)).to_df()
set_target_ball_3 = set(row for row in iter_target_3.itertuples(index = False, name = None))

expected_source_ball_3 = {
    (0, 1), (0, 2)
}

expected_target_ball_3 = {
    (0, 10), (0, 9)
}

assert (
    set_source_ball_3 == expected_source_ball_3 and
    set_target_ball_3 == expected_target_ball_3
)