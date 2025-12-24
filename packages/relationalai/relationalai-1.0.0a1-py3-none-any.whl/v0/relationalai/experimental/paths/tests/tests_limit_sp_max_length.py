from v0.relationalai.semantics import Model, Integer, define, select, count
from v0.relationalai.experimental.paths.graph import Graph
from v0.relationalai.experimental.paths.path_algorithms.find_paths import find_shortest_paths


# First test with grid graph
model = Model("test_all", dry_run=False)

grid = Graph.construct_grid(model, 3)

path_num, k = Integer.ref(), Integer.ref()
v = grid.Node.ref()

n1_1 = grid.Node.new(row = 1, col = 1)
n1_2 = grid.Node.new(row = 1, col = 2)
n1_3 = grid.Node.new(row = 1, col = 3)
n2_1 = grid.Node.new(row = 2, col = 1)
n2_2 = grid.Node.new(row = 2, col = 2)
n2_3 = grid.Node.new(row = 2, col = 3)
n3_1 = grid.Node.new(row = 3, col = 1)
n3_2 = grid.Node.new(row = 3, col = 2)
n3_3 = grid.Node.new(row = 3, col = 3)

Source_1 = model.Concept("Source_1", extends=[grid.Node])
Target_1 = model.Concept("Target_1", extends=[grid.Node])

define(Source_1(n1_1))
define(Source_1(n1_2))
define(Target_1(n3_2))
define(Target_1(n3_3))

paths_1 = find_shortest_paths(grid, Source_1, Target_1, num_paths=1, max_length=3)
iter_path_1 = select(k, v.row, v.col).where(paths_1(path_num, k, v)).to_df()
tuple_path_1 = tuple(sorted([row for row in iter_path_1.itertuples(index = False, name = None)]))

expected_path_1 = (
    (0, 1, 2), (1, 2, 2), (2, 3, 2)
)

assert tuple_path_1 == expected_path_1


# Second test with grid graph
paths_2 = find_shortest_paths(grid, Source_1, Target_1, num_paths=10, max_length=1)

assert select(k, v.row, v.col).where(paths_2(path_num, k, v)).to_df().empty


# Third test with grid graph
Source_3 = model.Concept("Source_3", extends=[grid.Node])
Target_3 = model.Concept("Target_3", extends=[grid.Node])

define(Source_3(n1_1))
define(Target_3(n3_3))

paths_3 = find_shortest_paths(grid, Source_3, Target_3, num_paths=10, max_length=4)

assert select(count(path_num)).where(paths_3(path_num, k, v)).to_df().iloc[0,0] == 6


# Fourth test with grid graph
paths_4 = find_shortest_paths(grid, Source_3, Target_3, num_paths=10, max_length=3)

assert select(k, v.row, v.col).where(paths_4(path_num, k, v)).to_df().empty


# Fifth test with grid graph
Source_5 = model.Concept("Source_5", extends=[grid.Node])
Target_5 = model.Concept("Target_5", extends=[grid.Node])

define(Source_5(n1_1))
define(Target_5(n1_1))

paths_5 = find_shortest_paths(grid, Source_5, Target_5, num_paths=10, max_length=0)

assert select(count(path_num)).where(paths_5(path_num, k, v)).to_df().iloc[0,0] == 1


# Sixth test with grid graph
Source_6 = model.Concept("Source_6", extends=[grid.Node])
Target_6 = model.Concept("Target_6", extends=[grid.Node])

define(Source_6(n1_1))
define(Source_6(n3_3))
define(Target_6(n1_1))
define(Target_6(n3_3))

paths_6 = find_shortest_paths(grid, Source_6, Target_6, num_paths=10, max_length=0)

assert select(count(path_num)).where(paths_6(path_num, k, v)).to_df().iloc[0,0] == 2