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
define(Target_1(n3_3))

paths_1 = find_shortest_paths(grid, Source_1, Target_1, num_paths=1)
iter_path_1 = select(k, v.row, v.col).where(paths_1(path_num, k, v)).to_df()
tuple_path_1 = tuple(sorted([row for row in iter_path_1.itertuples(index = False, name = None)]))

expected_path_1 = (
    (0, 1, 1), (1, 1, 2), (2, 1, 3), (3, 2, 3), (4, 3, 3)
)

expected_path_2 = (
    (0, 1, 1), (1, 1, 2), (2, 2, 2), (3, 2, 3), (4, 3, 3)
)

expected_path_3 = (
    (0, 1, 1), (1, 1, 2), (2, 2, 2), (3, 3, 2), (4, 3, 3)
)

expected_path_4 = (
    (0, 1, 1), (1, 2, 1), (2, 2, 2), (3, 2, 3), (4, 3, 3)
)

expected_path_5 = (
    (0, 1, 1), (1, 2, 1), (2, 2, 2), (3, 3, 2), (4, 3, 3)
)

expected_path_6 = (
    (0, 1, 1), (1, 2, 1), (2, 3, 1), (3, 3, 2), (4, 3, 3)
)

assert (
    tuple_path_1 == expected_path_1 or
    tuple_path_1 == expected_path_2 or
    tuple_path_1 == expected_path_3 or
    tuple_path_1 == expected_path_4 or
    tuple_path_1 == expected_path_5 or
    tuple_path_1 == expected_path_6
)



# Second test with grid graph
paths_2 = find_shortest_paths(grid, Source_1, Target_1, num_paths=3)

assert select(count(path_num)).where(paths_2(path_num, k, v)).to_df().iloc[0,0] == 3



# Third test with grid graph
paths_3 = find_shortest_paths(grid, Source_1, Target_1, num_paths=6)
iter_path_3 = select(path_num, k, v.row, v.col).where(paths_3(path_num, k, v)).to_df()
list_path_3 = sorted([row for row in iter_path_3.itertuples(index = False, name = None)])
set_path_3 = set()
for i in range(6):
    set_path_3.add(tuple((tup[1], tup[2], tup[3]) for tup in list_path_3[5*i:5*(i+1)]))

assert (
    set_path_3 == {
        expected_path_1, expected_path_2, expected_path_3, expected_path_4, expected_path_5, expected_path_6
    }
)


# Fourth test with grid graph
paths_4 = find_shortest_paths(grid, Source_1, Target_1)
iter_path_4 = select(path_num, k, v.row, v.col).where(paths_4(path_num, k, v)).to_df()
list_path_4 = sorted([row for row in iter_path_4.itertuples(index = False, name = None)])
set_path_4 = set()
for i in range(6):
    set_path_4.add(tuple((tup[1], tup[2], tup[3]) for tup in list_path_4[5*i:5*(i+1)]))

assert (
    len(list_path_4) == 30 and
    set_path_4 == {
        expected_path_1, expected_path_2, expected_path_3, expected_path_4, expected_path_5, expected_path_6
    }
)
