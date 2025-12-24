"""
Example usage of automaton-based pathfinding.
"""

import time
from v0.relationalai.semantics import Model, Integer, select, String, define
from v0.relationalai.experimental.paths.graph import Graph
from v0.relationalai.experimental.paths.api import node, path, match

import argparse


# def print_paths(path_node, path_label):
#     # Print nodes and labels in a readable format
#     l2 = String.ref()
#     k = Integer.ref()
#     m = Integer.ref()
#     print("\nNodes and labels in the path on the original graph:")
#     select(k, m, l2).where(
#         path_node(k, m),
#         path_label(k, label := String.ref()),
#         l2 == strings.concat("-[", label, "]->")
#     ).inspect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pathfinder example script.")
    parser.add_argument("--num_paths", type=int, default=None, help="Number of paths to find.")
    args = parser.parse_args()

    print("Number of paths to find:", args.num_paths)

    # Create an automaton that matches paths with pattern: A(A*)B:
    # pattern = path("-[A]->", star("-[A]->"), "-[B]->")
    # edge_list = [(1, 2, "A"), (2, 3, "A"), (3, 4, "A"), (4, 5, "B"), (1, 5, "A")]

    # 2 paths matching AB:
    # pattern = path("-[A]->", "-[B]->")
    # edge_list = [(1, 2, "A"), (2, 3, "B"), (1, 4, "A"), (4, 3, "B")]

    

    # pattern = path("-[A]->")
    # edge_list = [(1, 3, "A"), (2, 3, "A")]

    pattern = path("A")
    # edge_list = [(1, 3, "A"), (2, 3, "A"), (1, 4, "A"), (2, 4, "A")]
    edge_list = [(1, 2, "A")]


    sources = []
    targets = []

    sources = [1]
    targets = [2]

    # pattern = path("-[A]->")
    # edge_list = [(1, 3, "A"), (2, 3, "A"), (1, 4, "A"), (2, 4, "A")]

    # sources = [1, 2]
    # targets = [3, 4]
    # 2 paths from 2 different source nodes:
    # pattern = path("-[A]->")
    # edge_list = [(1, 3, "A"), (2, 3, "A")]

    # pattern = path("-[A]->")
    # edge_list = [(1, 3, "A"), (2, 3, "A"), (1, 4, "A"), (2, 4, "A")]

    timestamp = str(time.gmtime(0))

    print("\nEdge list:\n", edge_list)

    # Initialize the RelationalAI model
    model = Model(f"paths_{timestamp}", use_lqp=True) # , use_lqp=True)  # strict=True  # dry_run=False  # use_direct_access=True
    # use_lqp=True  # strict=True  # dry_run=False  # use_direct_access=True

    # model.define(
    #     RawSource("rel", "@span_no_threshold")
    # )

    graph = Graph.from_edge_list(model, edge_list)
    Node = graph.Node

    # Call the function to find the path

    Source = model.Relationship(f"source6 {{{Node}}}")
    Target = model.Relationship(f"target6 {{{Node}}}")

    for src in sources:
        define(Source(Node.new(id=src)))

    for tgt in targets:
        define(Target(Node.new(id=tgt)))

    src, tgt = Node.ref(), Node.ref()

    # select(graph.Node).inspect()

    graph.Edge.inspect()
    select(src).where(Source(src)).inspect()
    select(tgt).where(Target(tgt)).inspect()

    # print(f"\nFinding paths matching the automaton pattern from {src} to {dst}..."
    # projected_paths = match(graph, pattern, Source, Target, num_paths=args.num_paths)

    start = time.time()
    projected_paths = match(graph, pattern, Source, Target)

    i, k = Integer.ref(), Integer.ref()
    node = graph.Node.ref()
    label = String.ref()

    result = select(i, k, label, node.id).where(projected_paths(i, k, label, node)).inspect()
    end = time.time()

    print(f"Time taken to find paths: {end - start} seconds")
