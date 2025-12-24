from v0.relationalai.semantics import Model, Integer, define, select, count
from v0.relationalai.experimental.paths.graph import Graph
from v0.relationalai.experimental.paths.path_algorithms.find_paths import find_walks


# First test with grid graph
model = Model("tests_find_walks_single", dry_run=False)

grid = Graph.construct_grid(model, 2, "undirected")

path_num, k = Integer.ref(), Integer.ref()
v = grid.Node.ref()

n1_1 = grid.Node.new(row = 1, col = 1)
n1_2 = grid.Node.new(row = 1, col = 2)
n2_1 = grid.Node.new(row = 2, col = 1)
n2_2 = grid.Node.new(row = 2, col = 2)

Source_1 = model.Concept("Source_1", extends=[grid.Node])
Target_1 = model.Concept("Target_1", extends=[grid.Node])

define(Source_1(n1_1))
define(Source_1(n2_2))
define(Target_1(n1_1))
define(Target_1(n2_2))

paths_1 = find_walks(grid, Source_1, Target_1, 0, 20)
iter_path_1 = select(path_num, k, v.row, v.col).where(paths_1(path_num, k, v)).to_df()
list_path_1 = sorted([row for row in iter_path_1.itertuples(index = False, name = None)])
set_path_1 = set()
for i in range(1, max([t[0] for t in list_path_1]) + 1):
    set_path_1.add(tuple((t[1:] for t in list_path_1 if t[0] == i)))

expected_path_1_1 = (
    (0, 1, 1),
)

expected_path_1_2 = (
    (0, 2, 2),
)

assert (
    set_path_1 == {
        expected_path_1_1, expected_path_1_2
    }
)


# Second test with grid graph
paths_2 = find_walks(grid, Source_1, Target_1, 2, 20)
iter_path_2 = select(path_num, k, v.row, v.col).where(paths_2(path_num, k, v)).to_df()
list_path_2 = sorted([row for row in iter_path_2.itertuples(index = False, name = None)])
set_path_2 = set()
for i in range(1, max([t[0] for t in list_path_2]) + 1):
    set_path_2.add(tuple((t[1:] for t in list_path_2 if t[0] == i)))

expected_path_2_1 = (
    (0, 1, 1), (1, 1, 2), (2, 1, 1)
)

expected_path_2_2 = (
    (0, 1, 1), (1, 1, 2), (2, 2, 2)
)

expected_path_2_3 = (
    (0, 1, 1), (1, 2, 1), (2, 1, 1)
)

expected_path_2_4 = (
    (0, 1, 1), (1, 2, 1), (2, 2, 2)
)

expected_path_2_5 = (
    (0, 2, 2), (1, 1, 2), (2, 1, 1)
)

expected_path_2_6 = (
    (0, 2, 2), (1, 1, 2), (2, 2, 2)
)

expected_path_2_7 = (
    (0, 2, 2), (1, 2, 1), (2, 1, 1)
)

expected_path_2_8 = (
    (0, 2, 2), (1, 2, 1), (2, 2, 2)
)

assert (
    set_path_2 == {
        expected_path_1_1, expected_path_1_2,
        expected_path_2_1, expected_path_2_2, expected_path_2_3, expected_path_2_4,
        expected_path_2_5, expected_path_2_6, expected_path_2_7, expected_path_2_8
    }
)


# Third test with grid graph
paths_3 = find_walks(grid, Source_1, Target_1, 4, 20)

assert select(count(path_num)).where(paths_3(path_num, k, v)).to_df().iloc[0,0] == 20


# Fourth test with grid graph
paths_4 = find_walks(grid, Source_1, Target_1, 4, 100)

assert select(count(path_num)).where(paths_4(path_num, k, v)).to_df().iloc[0,0] == 42


# Fifth test with grid graph
paths_5 = find_walks(grid, Source_1, Target_1, 4)

assert select(count(path_num)).where(paths_5(path_num, k, v)).to_df().iloc[0,0] == 42