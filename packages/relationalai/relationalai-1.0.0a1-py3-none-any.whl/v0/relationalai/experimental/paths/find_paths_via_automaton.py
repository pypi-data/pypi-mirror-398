"""
Main functionality for finding paths through automaton.
"""

from v0.relationalai.semantics import define, where, Integer

from .product_graph import create_product_graph #, find_path_in_product_graph
# from .product_graph import project_product_graph_path_to_original_graph

from .path_algorithms.find_paths import find_shortest_paths, find_walks

def find_paths_via_automaton(graph, automaton, Source, Target,
                             num_paths = None, max_length = 1000,
                             type = "shortest"):
    """
    Find a path in the graph allowed by the automaton from Source nodes to Target nodes.

    Args:
        graph: The user's input graph
        automaton: Automaton object representing the pattern to match
        Source: Source node entities
        Target: Target node entities
        num_paths: Optional
          - if specified, limit the number of paths returned
          - if None, all paths are returned.

    Returns:
        product_graph: The product graph
        paths: Relationship of arity 4 encoding paths in the original graph
    """
    model = graph.model
    Node = graph.Node

    # Create product graph:
    product_graph = create_product_graph(graph, automaton)
    ProductGraphNode = product_graph.Node

    # automaton states:
    init_state = 0  # assumes single initial state labeled 0 of the automaton

    FinalState = model.Relationship("final_state1 {Integer}")
    for state in automaton.get_final_states():
        define(FinalState(state))

    # FinalState.inspect()

    # Product graph source and target sets:
    ProductGraphSource = model.Relationship(f"pg_source {{{ProductGraphNode}}}")
    ProductGraphTarget = model.Relationship(f"pg_target {{{ProductGraphNode}}}")

    st = Integer.ref() # state in the automaton
    src, tgt = Node.ref(), Node.ref()

    where(Source(src)).define(
        product_graph_src := ProductGraphNode.new(
            state=init_state, orig_node=src
        ),
        ProductGraphSource(product_graph_src)
    )

    where(Target(tgt), FinalState(st)).define(
        product_graph_dst := ProductGraphNode.new(
            state=st, orig_node=tgt
        ),
        ProductGraphTarget(product_graph_dst)
    )

    # ProductGraphSource.inspect()
    # ProductGraphTarget.inspect()

    if type == "shortest":
        # Find shortest paths in the product graph:
        find_paths_function = find_shortest_paths

    elif type == "walks":
        find_paths_function = find_walks
    else:
        raise ValueError(f"Unknown type of path search: {type}")

    paths = find_paths_function(
        product_graph, ProductGraphSource, ProductGraphTarget,
        num_paths=num_paths, max_length=max_length
    )

    return product_graph, paths
