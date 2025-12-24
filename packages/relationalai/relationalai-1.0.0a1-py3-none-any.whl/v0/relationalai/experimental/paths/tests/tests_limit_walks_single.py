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
define(Target_1(n2_2))

paths_1 = find_walks(grid, Source_1, Target_1, 2, 1)
iter_path_1 = select(k, v.row, v.col).where(paths_1(path_num, k, v)).to_df()
tuple_path_1 = tuple(sorted([row for row in iter_path_1.itertuples(index = False, name = None)]))


expected_path_1 = (
    (0, 1, 1), (1, 1, 2), (2, 2, 2)
)

expected_path_2 = (
    (0, 1, 1), (1, 2, 1), (2, 2, 2)
)

assert (
    tuple_path_1 == expected_path_1 or
    tuple_path_1 == expected_path_2
)



# Second test with grid graph
paths_2 = find_walks(grid, Source_1, Target_1, 2, 20)

assert select(count(path_num)).where(paths_2(path_num, k, v)).to_df().iloc[0,0] == 2


# Third test with grid graph
paths_3 = find_walks(grid, Source_1, Target_1, 4, 20)

assert select(count(path_num)).where(paths_3(path_num, k, v)).to_df().iloc[0,0] == 10



# Fourth test with grid graph
paths_4 = find_walks(grid, Source_1, Target_1, 4, 20)
iter_path_4 = select(path_num, k, v.row, v.col).where(paths_4(path_num, k, v)).to_df()
list_path_4 = sorted([row for row in iter_path_4.itertuples(index = False, name = None)])
set_path_4 = set()
for i in range(1, max([t[0] for t in list_path_4]) + 1):
    set_path_4.add(tuple((t[1:] for t in list_path_4 if t[0] == i)))

expected_path_3 = (
    (0, 1, 1), (1, 1, 2), (2, 1, 1), (3, 1, 2), (4, 2, 2)
)

expected_path_4 = (
    (0, 1, 1), (1, 1, 2), (2, 1, 1), (3, 2, 1), (4, 2, 2)
)

expected_path_5 = (
    (0, 1, 1), (1, 1, 2), (2, 2, 2), (3, 1, 2), (4, 2, 2)
)

expected_path_6 = (
    (0, 1, 1), (1, 1, 2), (2, 2, 2), (3, 2, 1), (4, 2, 2)
)

expected_path_7 = (
    (0, 1, 1), (1, 2, 1), (2, 1, 1), (3, 1, 2), (4, 2, 2)
)

expected_path_8 = (
    (0, 1, 1), (1, 2, 1), (2, 1, 1), (3, 2, 1), (4, 2, 2)
)

expected_path_9 = (
    (0, 1, 1), (1, 2, 1), (2, 2, 2), (3, 1, 2), (4, 2, 2)
)

expected_path_10 = (
    (0, 1, 1), (1, 2, 1), (2, 2, 2), (3, 2, 1), (4, 2, 2)
)

assert (
    set_path_4 == {
        expected_path_1, expected_path_2, expected_path_3, expected_path_4, expected_path_5,
        expected_path_6, expected_path_7, expected_path_8, expected_path_9, expected_path_10
    }
)


# Fifth test with grid graph
Source_5 = model.Concept("Source_5", extends=[grid.Node])
Target_5 = model.Concept("Target_5", extends=[grid.Node])

define(Source_5(n1_1))
define(Target_5(n1_1))

paths_5 = find_walks(grid, Source_5, Target_5, 0, 10)
iter_path_5 = select(k, v.row, v.col).where(paths_5(path_num, k, v)).to_df()
list_path_5 = [row for row in iter_path_5.itertuples(index = False, name = None)]


expected_path_5_1 = [
    (0, 1, 1)
]

assert list_path_5 == expected_path_5_1


# Sixth test with grid graph
paths_6 = find_walks(grid, Source_5, Target_5, 2, 20)
iter_path_6 = select(path_num, k, v.row, v.col).where(paths_6(path_num, k, v)).to_df()
list_path_6 = sorted([row for row in iter_path_6.itertuples(index = False, name = None)])
set_path_6 = set()
for i in range(1, max([t[0] for t in list_path_6]) + 1):
    set_path_6.add(tuple((t[1:] for t in list_path_6 if t[0] == i)))

expected_path_6_1 = (
    (0, 1, 1),
)

expected_path_6_2 = (
    (0, 1, 1), (1, 2, 1), (2, 1, 1)
)

expected_path_6_3 = (
    (0, 1, 1), (1, 1, 2), (2, 1, 1)
)

assert (
    set_path_6 == {
        expected_path_6_1, expected_path_6_2, expected_path_6_3
    }
)
