from v0.relationalai.semantics import Model, Integer, define, select
from v0.relationalai.experimental.paths.graph import Graph
from v0.relationalai.experimental.paths.path_algorithms.one_sided_ball_upto import ball_upto


# First test with grid graph and multiple source and target nodes
model_grid = Model("test_one_sided_ball_upto grid", dry_run=False)

grid = Graph.construct_grid(model_grid, 3)

n = Integer.ref()
u = grid.Node.ref()

source_1_1 = grid.Node.new(row = 1, col = 2)
source_1_2 = grid.Node.new(row = 2, col = 1)
target_1_1 = grid.Node.new(row = 3, col = 2)
target_1_2 = grid.Node.new(row = 2, col = 3)

Source_1 = model_grid.Concept("Source_1", extends=[grid.Node])
Target_1 = model_grid.Concept("Target_1", extends=[grid.Node])

define(Source_1(source_1_1))
define(Source_1(source_1_2))
define(Target_1(target_1_1))
define(Target_1(target_1_2))

source_ball_1 = ball_upto(grid, Source_1, Target_1)
iter_set_1 = select(n, u.row, u.col).where(source_ball_1(n, u)).to_df()
set_ball_1 = set(row for row in iter_set_1.itertuples(index = False, name = None))

expected_ball_1 = {
    (0, 1, 2), (0, 2, 1), (1, 3, 1), (1, 2, 2), (1, 1, 3), (2, 3, 2), (2, 2, 3)
}

assert set_ball_1 == expected_ball_1


# Second test with grid graph and multiple source and target nodes
target_2_1 = grid.Node.new(row = 3, col = 3)

Target_2 = model_grid.Concept("Target_2", extends=[grid.Node])

define(Target_2(target_1_1))
define(Target_2(target_1_2))
define(Target_2(target_2_1))

source_ball_2 = ball_upto(grid, Source_1, Target_2)
iter_set_2 = select(n, u.row, u.col).where(source_ball_2(n, u)).to_df()
set_ball_2 = set(row for row in iter_set_2.itertuples(index = False, name = None))

assert set_ball_2 == expected_ball_1


# First test with diamond graph and multiple source and target nodes
model_diamond = Model("test_one_sided_ball_upto diamond", dry_run=False)

diamond = Graph.construct_diamond(model_diamond, 3)

v = diamond.Node.ref()

source_3_1 = diamond.Node.new(id = 2)
source_3_2 = diamond.Node.new(id = 3)
target_3_1 = diamond.Node.new(id = 7)
target_3_2 = diamond.Node.new(id = 8)
target_3_3 = diamond.Node.new(id = 9)

Source_3 = model_diamond.Concept("Source_3", extends=[diamond.Node])
Target_3 = model_diamond.Concept("Target_3", extends=[diamond.Node])

define(Source_3(source_3_1))
define(Source_3(source_3_2))
define(Target_3(target_3_1))
define(Target_3(target_3_2))
define(Target_3(target_3_3))

source_ball_3 = ball_upto(diamond, Source_3, Target_3)
iter_set_3 = select(n, v.id).where(source_ball_3(n, v)).to_df()
set_ball_3 = set(row for row in iter_set_3.itertuples(index = False, name = None))

expected_ball_3 = {
    (0, 2), (0, 3), (1, 4), (2, 5), (2, 6), (3, 7)
}

assert set_ball_3 == expected_ball_3


# Second test with diamond graph and multiple source and target nodes
source_4_1 = diamond.Node.new(id = 1)
source_4_2 = diamond.Node.new(id = 2)
source_4_3 = diamond.Node.new(id = 4)
target_4_1 = diamond.Node.new(id = 2)
target_4_2 = diamond.Node.new(id = 4)
target_4_3 = diamond.Node.new(id = 5)

Source_4 = model_diamond.Concept("Source_4", extends=[diamond.Node])
Target_4 = model_diamond.Concept("Target_4", extends=[diamond.Node])

define(Source_4(source_4_1))
define(Source_4(source_4_2))
define(Source_4(source_4_3))
define(Target_4(target_4_1))
define(Target_4(target_4_2))
define(Target_4(target_4_3))

n = Integer.ref()

source_ball_4 = ball_upto(diamond, Source_4, Target_4)
iter_set_4 = select(n, v.id).where(source_ball_4(n, v)).to_df()
set_ball_4 = set(row for row in iter_set_4.itertuples(index = False, name = None))

expected_ball_4 = {
    (0, 1), (0, 2), (0, 4)
}

assert set_ball_4 == expected_ball_4
