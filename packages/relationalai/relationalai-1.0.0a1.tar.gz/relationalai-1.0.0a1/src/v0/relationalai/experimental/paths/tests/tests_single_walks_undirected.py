from v0.relationalai.semantics import Model, Integer, define, select
from v0.relationalai.experimental.paths.graph import Graph
from v0.relationalai.experimental.paths.path_algorithms.single import single_walk


model = Model("test_single_paths", dry_run=False)


# First test with grid graph
grid = Graph.construct_grid(model, 3, 'undirected')

n = Integer.ref()
u = grid.Node.ref()

n_1_1 = grid.Node.new(row = 1, col = 1)
n_1_2 = grid.Node.new(row = 1, col = 2)
n_1_3 = grid.Node.new(row = 1, col = 3)
n_2_1 = grid.Node.new(row = 2, col = 1)
n_2_2 = grid.Node.new(row = 2, col = 2)
n_2_3 = grid.Node.new(row = 2, col = 3)
n_3_1 = grid.Node.new(row = 3, col = 1)
n_3_2 = grid.Node.new(row = 3, col = 2)
n_3_3 = grid.Node.new(row = 3, col = 3)

Source_1 = model.Concept("Source_1", extends=[grid.Node])
Target_1 = model.Concept("Target_1", extends=[grid.Node])

define(Source_1(n_1_1))
define(Target_1(n_2_2))

path_1 = single_walk(grid, Source_1, Target_1, 2)
iter_path_1 = select(n, u.row, u.col).where(path_1(n, u)).to_df()
set_path_1 = set(row for row in iter_path_1.itertuples(index = False, name = None))

expected_path_1_1 = {
    (0, 1, 1), (1, 1, 2), (2, 2, 2)
}

expected_path_1_2 = {
    (0, 1, 1), (1, 2, 1), (2, 2, 2)
}

assert(
    set_path_1 == expected_path_1_1 or
    set_path_1 == expected_path_1_2
)


# Second test with grid graph
Target_2 = model.Concept("Target_2", extends=[grid.Node])

define(Target_2(n_3_3))

path_2 = single_walk(grid, Source_1, Target_2, 4)
iter_path_2 = select(n, u.row, u.col).where(path_2(n, u)).to_df()
set_path_2 = set(row for row in iter_path_2.itertuples(index = False, name = None))

expected_path_2_1 = {
    (0, 1, 1), (1, 2, 1), (2, 3, 1), (3, 3, 2), (4, 3, 3)
}

expected_path_2_2 = {
    (0, 1, 1), (1, 2, 1), (2, 2, 2), (3, 3, 2), (4, 3, 3)
}

expected_path_2_3 = {
    (0, 1, 1), (1, 2, 1), (2, 2, 2), (3, 2, 3), (4, 3, 3)
}

expected_path_2_4 = {
    (0, 1, 1), (1, 1, 2), (2, 2, 2), (3, 3, 2), (4, 3, 3)
}

expected_path_2_5 = {
    (0, 1, 1), (1, 1, 2), (2, 2, 2), (3, 2, 3), (4, 3, 3)
}

expected_path_2_6 = {
    (0, 1, 1), (1, 1, 2), (2, 1, 3), (3, 2, 3), (4, 3, 3)
}


assert(
    set_path_2 == expected_path_2_1 or
    set_path_2 == expected_path_2_2 or
    set_path_2 == expected_path_2_3 or
    set_path_2 == expected_path_2_4 or
    set_path_2 == expected_path_2_5 or
    set_path_2 == expected_path_2_6
)


# Third test with grid graph
Source_3 = model.Concept("Source_3", extends=[grid.Node])
Target_3 = model.Concept("Target_3", extends=[grid.Node])

define(Source_3(n_1_1))
define(Source_3(n_1_2))
define(Target_3(n_3_2))
define(Target_3(n_3_3))

path_3 = single_walk(grid, Source_3, Target_3, 2)
iter_path_3 = select(n, u.row, u.col).where(path_3(n, u)).to_df()
set_path_3 = set(row for row in iter_path_3.itertuples(index = False, name = None))

expected_path_3 = {
    (0, 1, 2), (1, 2, 2), (2, 3, 2)
}

assert(
    set_path_3 == expected_path_3
)


# Fourth test with grid graph
Source_4 = model.Concept("Source_4", extends=[grid.Node])
Target_4 = model.Concept("Target_4", extends=[grid.Node])

define(Source_4(n_1_1))
define(Source_4(n_2_2))
define(Target_4(n_2_2))
define(Target_4(n_3_3))

path_4 = single_walk(grid, Source_4, Target_4, 0)
iter_path_4 = select(n, u.row, u.col).where(path_4(n, u)).to_df()
set_path_4 = set(row for row in iter_path_4.itertuples(index = False, name = None))

expected_path_4 = {
    (0, 2, 2)
}

assert(
    set_path_4 == expected_path_4
)


# Fifth test with grid graph
Target_5 = model.Concept("Target_5", extends=[grid.Node])

n_4_4 = grid.Node.new(row = 4, col = 4)

define(Target_5(n_4_4))

path_5 = single_walk(grid, Source_1, Target_5, 4)
iter_path_5 = select(n, u.row, u.col).where(path_5(n, u)).to_df()
set_path_5 = set(row for row in iter_path_5.itertuples(index = False, name = None))

expected_path_5 = set()

assert(
    set_path_5 == expected_path_5
)


# Sixth test with grid graph
path_6 = single_walk(grid, Source_1, Target_1, 4)
iter_path_6 = select(n, u.row, u.col).where(path_6(n, u)).to_df()
set_path_6 = set(row for row in iter_path_6.itertuples(index = False, name = None))

expected_path_6_1 = {
    (0, 1, 1), (1, 2, 1), (2, 1, 1), (3, 2, 1), (4, 2, 2)
}

expected_path_6_2 = {
    (0, 1, 1), (1, 2, 1), (2, 1, 1), (3, 1, 2), (4, 2, 2)
}

expected_path_6_3 = {
    (0, 1, 1), (1, 2, 1), (2, 2, 2), (3, 2, 1), (4, 2, 2)
}

expected_path_6_4 = {
    (0, 1, 1), (1, 2, 1), (2, 2, 2), (3, 1, 2), (4, 2, 2)
}

expected_path_6_5 = {
    (0, 1, 1), (1, 2, 1), (2, 2, 2), (3, 3, 2), (4, 2, 2)
}

expected_path_6_6 = {
    (0, 1, 1), (1, 2, 1), (2, 2, 2), (3, 2, 3), (4, 2, 2)
}

expected_path_6_7 = {
    (0, 1, 1), (1, 1, 2), (2, 1, 1), (3, 2, 1), (4, 2, 2)
}

expected_path_6_8 = {
    (0, 1, 1), (1, 1, 2), (2, 1, 1), (3, 1, 2), (4, 2, 2)
}

expected_path_6_9 = {
    (0, 1, 1), (1, 1, 2), (2, 2, 2), (3, 2, 1), (4, 2, 2)
}

expected_path_6_10 = {
    (0, 1, 1), (1, 1, 2), (2, 2, 2), (3, 1, 2), (4, 2, 2)
}

expected_path_6_11 = {
    (0, 1, 1), (1, 1, 2), (2, 2, 2), (3, 3, 2), (4, 2, 2)
}

expected_path_6_12 = {
    (0, 1, 1), (1, 1, 2), (2, 2, 2), (3, 2, 3), (4, 2, 2)
}

expected_path_6_13 = {
    (0, 1, 1), (1, 2, 1), (2, 3, 1), (3, 2, 1), (4, 2, 2)
}

expected_path_6_14 = {
    (0, 1, 1), (1, 2, 1), (2, 3, 1), (3, 3, 2), (4, 2, 2)
}

expected_path_6_15 = {
    (0, 1, 1), (1, 1, 2), (2, 1, 3), (3, 1, 2), (4, 2, 2)
}

expected_path_6_16 = {
    (0, 1, 1), (1, 1, 2), (2, 1, 3), (3, 2, 3), (4, 2, 2)
}


assert(
    set_path_6 == expected_path_6_1 or
    set_path_6 == expected_path_6_2 or
    set_path_6 == expected_path_6_3 or
    set_path_6 == expected_path_6_4 or
    set_path_6 == expected_path_6_5 or
    set_path_6 == expected_path_6_6 or
    set_path_6 == expected_path_6_7 or
    set_path_6 == expected_path_6_8 or
    set_path_6 == expected_path_6_9 or
    set_path_6 == expected_path_6_10 or
    set_path_6 == expected_path_6_11 or
    set_path_6 == expected_path_6_12 or
    set_path_6 == expected_path_6_13 or
    set_path_6 == expected_path_6_14 or
    set_path_6 == expected_path_6_15 or
    set_path_6 == expected_path_6_16
)


# Seventh test with grid graph
path_7 = single_walk(grid, Source_1, Target_2, 3)
iter_path_7 = select(n, u.row, u.col).where(path_7(n, u)).to_df()
set_path_7 = set(row for row in iter_path_7.itertuples(index = False, name = None))

expected_path_7 = set()

assert set_path_7 == expected_path_7


# Eighth test with grid graph
path_8 = single_walk(grid, Source_1, Target_1, 1)
iter_path_8 = select(n, u.row, u.col).where(path_8(n, u)).to_df()
set_path_8 = set(row for row in iter_path_8.itertuples(index = False, name = None))

expected_path_8 = set()

assert set_path_8 == expected_path_8


# Ninth test with grid graph
Source_9 = model.Concept("Source_9", extends=[grid.Node])
Target_9 = model.Concept("Target_5", extends=[grid.Node])

define(Source_9(n_2_2))
define(Target_9(n_2_2))

path_9 = single_walk(grid, Source_9, Target_9, 2)
iter_path_9 = select(n, u.row, u.col).where(path_9(n, u)).to_df()
set_path_9 = set(row for row in iter_path_9.itertuples(index = False, name = None))

expected_path_9_1 = {
    (0, 2, 2), (1, 1, 2), (2, 2, 2)
}

expected_path_9_2 = {
    (0, 2, 2), (1, 2, 1), (2, 2, 2)
}

expected_path_9_3 = {
    (0, 2, 2), (1, 2, 3), (2, 2, 2)
}

expected_path_9_4 = {
    (0, 2, 2), (1, 3, 2), (2, 2, 2)
}

assert(
    set_path_9 == expected_path_9_1 or
    set_path_9 == expected_path_9_2 or
    set_path_9 == expected_path_9_3 or
    set_path_9 == expected_path_9_4
)