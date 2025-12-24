from v0.relationalai.semantics import Model, Integer, select, String, define
from v0.relationalai.experimental.paths.graph import Graph
from v0.relationalai.experimental.paths.api import path, star, match

# Create an automaton that matches paths with pattern: A(A*)B:
pattern = path("A", star("A"), "B")
edge_list = [(1, 2, "A"), (2, 3, "A"), (3, 4, "A"), (4, 5, "B"), (1, 5, "A")]

sources = [1]
targets = [5]

model = Model("my_paths")

# create the graph:
graph = Graph.from_edge_list(model, edge_list)
Node = graph.Node

# create source and target sets:
Source = model.Relationship("source3 {Node}")
Target = model.Relationship("target3 {Node}")

for src in sources:
    define(Source(graph.Node.new(id=src)))

for tgt in targets:
    define(Target(graph.Node.new(id=tgt)))

paths = match(graph, pattern, Source, Target)

i, k = Integer.ref(), Integer.ref()
graph_node = graph.Node.ref()
label = String.ref()

result = select(i, k, label, graph_node.id).where(
    paths(i, k, label, graph_node)
)

result.inspect()

# print(result)
