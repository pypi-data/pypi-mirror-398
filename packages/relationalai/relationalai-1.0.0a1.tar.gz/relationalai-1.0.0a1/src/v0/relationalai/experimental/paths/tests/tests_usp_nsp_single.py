from v0.relationalai.semantics import Model, Integer, define, select
from v0.relationalai.experimental.paths.graph import Graph
from v0.relationalai.experimental.paths.path_algorithms.usp import compute_usp, compute_nsp


# First test for usp with grid graph
model_grid = Model("test_usp_nsp_single grid", dry_run=False)

grid1 = Graph.construct_grid(model_grid, 3)

source1 = grid1.Node.new(row = 1, col = 1)
target1 = grid1.Node.new(row = 3, col = 3)

Source1 = model_grid.Concept("Source1", extends=[grid1.Node])
Target1 = model_grid.Concept("Target1", extends=[grid1.Node])

define(Source1(source1))
define(Target1(target1))

u, v = grid1.Node.ref(), grid1.Node.ref()
n = Integer.ref()

usp1, _ = compute_usp(grid1, Source1, Target1)
iter_usp1 = select(u.row, u.col, v.row, v.col).where(usp1(u, v)).to_df()
set_usp1 = set(row for row in iter_usp1.itertuples(index = False, name = None))

expected_usp1 = {
    (1, 1, 2, 1), (2, 1, 3, 1),
    (1, 2, 2, 2), (2, 2, 3, 2),
    (1, 3, 2, 3), (2, 3, 3, 3),
    (1, 1, 1, 2), (1, 2, 1, 3),
    (2, 1, 2, 2), (2, 2, 2, 3),
    (3, 1, 3, 2), (3, 2, 3, 3)
}

assert set_usp1 == expected_usp1


# Second test for usp with diamond graph
model_diamond = Model("test_usp_nsp_single diamond", dry_run=False)

diamond2 = Graph.construct_diamond(model_diamond, 3)

du, dv = diamond2.Node.ref(), diamond2.Node.ref()

source2 = diamond2.Node.new(id = 2)
target2 = diamond2.Node.new(id = 9)

Source2 = model_diamond.Concept("Source2", extends=[diamond2.Node])
Target2 = model_diamond.Concept("Target2", extends=[diamond2.Node])

define(Source2(source2))
define(Target2(target2))

usp2, _ = compute_usp(diamond2, Source2, Target2)
iter_usp2 = select(du.id, dv.id).where(usp2(du, dv)).to_df()
set_usp2 = set(row for row in iter_usp2.itertuples(index = False, name = None))

expected_usp2 = {
    (2, 4), (4, 5), (4, 6), (5, 7), (6, 7), (7, 9)
}

assert set_usp2 == expected_usp2


# First test for nsp with grid graph
nsp1 = compute_nsp(grid1, Source1, Target1)
iter_nsp1 = select(u.row, u.col, n).where(nsp1(u, n)).to_df()
set_nsp1 = set(row for row in iter_nsp1.itertuples(index = False, name = None))

expected_nsp1 = {
    (1, 1, 6), (1, 2, 3), (2, 1, 3), (3, 1, 1), (2, 2, 2), (1, 3, 1),
    (2, 3, 1), (3, 2, 1), (3, 3, 1)
}

assert set_nsp1 == expected_nsp1


"""# Second test for nsp with diamond graph
model_diamond_2 = Model("test_usp_nsp_single diamond_2", dry_run=False)

diamond3 = Graph.construct_diamond(model_diamond_2, 5)

dw = diamond3.Node.ref()

source3 = diamond3.Node.new(id = 1)
target3 = diamond3.Node.new(id = 16)

Source3 = model_diamond_2.Concept("Source3", extends=[diamond3.Node])
Target3 = model_diamond_2.Concept("Target3", extends=[diamond3.Node])

define(Source3(source3))
define(Target3(target3))

nsp3 = compute_nsp(diamond3, Source3, Target3)
iter_nsp3 = select(dw.id, n).where(nsp3(dw, n)).to_df()
set_nsp3 = set(row for row in iter_nsp3.itertuples(index = False, name = None))

expected_nsp3 = {
    (1, 32),
    (2, 16), (3, 16), (4, 16),
    (5, 8), (6, 8), (7, 8),
    (8, 4), (9, 4), (10, 4),
    (11, 2), (12, 2), (13, 2),
    (14, 1), (15, 1), (16, 1)
}

assert set_nsp3 == expected_nsp3"""