from v0.relationalai.semantics import Model, Integer, define, select
from v0.relationalai.experimental.paths.graph import Graph
from v0.relationalai.experimental.paths.path_algorithms.usp import compute_usp, compute_nsp


# First test for usp with grid graph
model_grid = Model("test_usp_nsp_multiple grid", dry_run=False)

grid1 = Graph.construct_grid(model_grid, 3)

source1_1 = grid1.Node.new(row = 1, col = 1)
source1_2 = grid1.Node.new(row = 1, col = 2)
target1_1 = grid1.Node.new(row = 3, col = 2)
target1_2 = grid1.Node.new(row = 3, col = 3)

Source1 = model_grid.Concept("Source1", extends=[grid1.Node])
Target1 = model_grid.Concept("Target1", extends=[grid1.Node])

define(Source1(source1_1))
define(Source1(source1_2))
define(Target1(target1_1))
define(Target1(target1_2))

u, v = grid1.Node.ref(), grid1.Node.ref()
n = Integer.ref()

usp1, _ = compute_usp(grid1, Source1, Target1)
iter_usp1 = select(u.row, u.col, v.row, v.col).where(usp1(u, v)).to_df()
set_usp1 = set(row for row in iter_usp1.itertuples(index = False, name = None))

expected_usp1 = {
    (1, 2, 2, 2), (2, 2, 3, 2)
}

assert set_usp1 == expected_usp1


# Second test for usp with grid graph
Target2 = model_grid.Concept("Target2", extends=[grid1.Node])

define(Target2(target1_2))

u, v = grid1.Node.ref(), grid1.Node.ref()
n = Integer.ref()

usp2, _ = compute_usp(grid1, Source1, Target2)
iter_usp2 = select(u.row, u.col, v.row, v.col).where(usp2(u, v)).to_df()
set_usp2 = set(row for row in iter_usp2.itertuples(index = False, name = None))

expected_usp2 = {
    (1, 2, 2, 2), (2, 2, 3, 2),
    (1, 3, 2, 3), (2, 3, 3, 3),
    (1, 2, 1, 3), (2, 2, 2, 3), (3, 2, 3, 3)
}

assert set_usp2 == expected_usp2


# First test for usp with diamond graph
model_diamond = Model("test_usp_nsp_multiple diamond", dry_run=False)

diamond3 = Graph.construct_diamond(model_diamond, 3)

du, dv = diamond3.Node.ref(), diamond3.Node.ref()

source3_1 = diamond3.Node.new(id = 2)
source3_2 = diamond3.Node.new(id = 3)
target3_1 = diamond3.Node.new(id = 8)
target3_2 = diamond3.Node.new(id = 9)

Source3 = model_diamond.Concept("Source3", extends=[diamond3.Node])
Target3 = model_diamond.Concept("Target3", extends=[diamond3.Node])

define(Source3(source3_1))
define(Source3(source3_2))
define(Target3(target3_1))
define(Target3(target3_2))

usp3, _ = compute_usp(diamond3, Source3, Target3)
iter_usp3 = select(du.id, dv.id).where(usp3(du, dv)).to_df()
set_usp3 = set(row for row in iter_usp3.itertuples(index = False, name = None))

expected_usp3 = {
    (2, 4), (3, 4), (4, 5), (4, 6), (5, 7), (6, 7), (7, 9), (7, 8)
}

assert set_usp3 == expected_usp3


# First test for nsp with grid graph
nsp1 = compute_nsp(grid1, Source1, Target1)
iter_nsp1 = select(u.row, u.col, n).where(nsp1(u, n)).to_df()
set_nsp1 = set(row for row in iter_nsp1.itertuples(index = False, name = None))

expected_nsp1 = {
    (1, 2, 1), (2, 2, 1), (3, 2, 1)
}

assert set_nsp1 == expected_nsp1


# Second test for nsp with diamond graph
model_diamond_2 = Model("test_usp_nsp_multiple diamond_2", dry_run=False)

diamond4 = Graph.construct_diamond(model_diamond_2, 5)

dw = diamond4.Node.ref()

source4_1 = diamond4.Node.new(id = 4)
source4_2 = diamond4.Node.new(id = 5)
source4_3 = diamond4.Node.new(id = 7)
target4_1 = diamond4.Node.new(id = 7)
target4_2 = diamond4.Node.new(id = 9)
target4_3 = diamond4.Node.new(id = 10)

Source4 = model_diamond_2.Concept("Source4", extends=[diamond4.Node])
Target4 = model_diamond_2.Concept("Target4", extends=[diamond4.Node])

define(Source4(source4_1))
define(Source4(source4_2))
define(Source4(source4_3))
define(Target4(target4_1))
define(Target4(target4_2))
define(Target4(target4_3))

nsp4 = compute_nsp(diamond4, Source4, Target4)
iter_nsp4 = select(dw.id, n).where(nsp4(dw, n)).to_df()
set_nsp4 = set(row for row in iter_nsp4.itertuples(index = False, name = None))

expected_nsp4 = {
    (7, 1)
}

assert set_nsp4 == expected_nsp4


# First test with cyclic graph
model_cyclic = Model("test_usp_nsp_multiple cyclic", dry_run=False)

cyclic5 = Graph.from_edge_list(model_cyclic, [(1, 2), (2, 3), (3, 4), (2, 5), (5, 2), (5, 6)])

cu, cv = cyclic5.Node.ref(), cyclic5.Node.ref()

source5 = cyclic5.Node.new(id = 1)
target5_1 = cyclic5.Node.new(id = 4)
target5_2 = cyclic5.Node.new(id = 6)

Source5 = model_cyclic.Concept("Source5", extends=[cyclic5.Node])
Target5 = model_cyclic.Concept("Target5", extends=[cyclic5.Node])

define(Source5(source5))
define(Target5(target5_1))
define(Target5(target5_2))

usp5, _ = compute_usp(cyclic5, Source5, Target5)
iter_usp5 = select(cu.id, cv.id).where(usp5(cu, cv)).to_df()
set_usp5 = set(row for row in iter_usp5.itertuples(index = False, name = None))

nsp5 = compute_nsp(cyclic5, Source5, Target5)
iter_nsp5 = select(cu.id, n).where(nsp5(cu, n)).to_df()
set_nsp5 = set(row for row in iter_nsp5.itertuples(index = False, name = None))

expected_usp5 = {
    (1, 2), (2, 3), (3, 4), (2, 5), (5, 6)
}

expected_nsp5 = {
    (1, 2), (2, 2), (3, 1), (4, 1), (5, 1), (6, 1)
}

assert (
    set_usp5 == expected_usp5 and
    set_nsp5 == expected_nsp5
)


# First test for usp and nsp with undirected diamond graph
model_und = Model("test_usp_nsp_multiple und", dry_run=False)

diamond6 = Graph.construct_diamond(model_und, 5, "undirected")

uu, uv = diamond6.Node.ref(), diamond6.Node.ref()

source6_1 = diamond6.Node.new(id = 7)
source6_2 = diamond6.Node.new(id = 10)
target6_1 = diamond6.Node.new(id = 4)
target6_2 = diamond6.Node.new(id = 13)

Source6 = model_und.Concept("Source6", extends=[diamond6.Node])
Target6 = model_und.Concept("Target6", extends=[diamond6.Node])

define(Source6(source6_1))
define(Source6(source6_2))
define(Target6(target6_1))
define(Target6(target6_2))

usp6, _ = compute_usp(diamond6, Source6, Target6)
iter_usp6 = select(uu.id, uv.id).where(usp6(uu, uv)).to_df()
set_usp6 = set(row for row in iter_usp6.itertuples(index = False, name = None))

nsp6 = compute_nsp(diamond6, Source6, Target6)
iter_nsp6 = select(uu.id, n).where(nsp6(uu, n)).to_df()
set_nsp6 = set(row for row in iter_nsp6.itertuples(index = False, name = None))

expected_usp6 = {
    (7, 6), (7, 5), (6, 4), (5, 4),
    (10, 11), (10, 12), (11, 13), (12, 13)
}

expected_nsp6 = {
    (4, 1), (5, 1), (6, 1), (7, 2),
    (13, 1), (12, 1), (11, 1), (10, 2)
}

assert (
    set_usp6 == expected_usp6 and
    set_nsp6 == expected_nsp6
)


# First test for usp and nsp with grid graph
target7 = grid1.Node.new(row = 4, col = 4)

Target7 = model_grid.Concept("Target7", extends=[grid1.Node])

usp7, _ = compute_usp(grid1, Source1, Target7)
nsp7 = compute_nsp(grid1, Source1, Target7)

assert usp7.to_df().empty and nsp7.to_df().empty
