"""
Product graph implementation for automaton-based path finding.
"""

from v0.relationalai.semantics import Integer, where, define, Relationship, String

from .graph import Graph


def create_product_graph(graph, automaton):
    """
    Create a product graph based on an automaton specification.

    Args:
        model: The RelationalAI model
        automaton_spec: List of automaton transitions (src_state, dst_state, label/filter)
        node: Node concept from the original graph
        edge: Edge relationship from the original graph

    Returns:
        Tuple of (ProductGraphNode, product_graph) representing the product graph concepts
    """
    model = graph.model
    Node = graph.Node
    Edge = graph.Edge

    # Define product graph for path finding
    ProductGraphNode = model.Concept("ProductNode")
    ProductGraphEdge = model.Relationship(f"pg_edge {{{ProductGraphNode}}} {{{ProductGraphNode}}}")

    ProductGraphNode.orig_node = Relationship(f"orig_node {{{ProductGraphNode}}} {{{Node}}}")
    ProductGraphNode.state = Relationship(f"state {{{ProductGraphNode}}} {{Integer}}")
    ProductGraphNode.identify_by(ProductGraphNode.state, ProductGraphNode.orig_node)

    # NB: Modifying `automaton` object
    # Add automaton transitions to the model
    automaton.transition = model.Relationship("automaton {Integer} {Integer} {String}")

    # Create references for use in rules
    state1, state2 = Integer.ref(), Integer.ref()
    node1, node2 = Node.ref(), Node.ref()

    # Create a rule for each automaton transition:
    for state1 in automaton.delta:  # delta is the dict containing automaton transitions
        for state2 in automaton.delta[state1]:
            for transition in automaton.delta[state1][state2]:
                label = transition.get_label().label

                define(automaton.transition(state1, state2, label))

                source_filters = transition.src_filters

                where(
                    ProductGraphNode.state == state1,
                    ProductGraphNode.orig_node == node1,
                    Edge(node1, node2, label),
                    *([f(node1) for f in source_filters])
                    ).define(
                        ProductGraphNode.new(state=state2, orig_node=node2),
                        ProductGraphEdge(ProductGraphNode, ProductGraphNode.new(state=state2, orig_node=node2))
                    )

    return Graph(model, ProductGraphNode, ProductGraphEdge)


def project_product_graph_paths_to_original_graph(product_graph, product_graph_paths, automaton):

    model = product_graph.model
    ProductGraphNode = product_graph.Node

    # extract Node type of original graph:
    Node = ProductGraphNode.orig_node._fields[1].type_str

    # print("Node type in original graph:", Node)


    # Project path down from product graph to original graph
    projected_paths = model.Relationship(f"projected {{Integer}} {{Integer}} {{String}} {{{Node}}}")

    k = Integer.ref()
    product_graph_node2 = ProductGraphNode.ref()
    label = String.ref()

    i = Integer.ref()

    define(projected_paths(i, 0, "", ProductGraphNode.orig_node)).where(product_graph_paths(i, 0, ProductGraphNode))
    define(projected_paths(i, k, label, product_graph_node2.orig_node)).where(
        product_graph_paths(i, k - 1, ProductGraphNode),
        product_graph_paths(i, k, product_graph_node2),
        automaton.transition(ProductGraphNode.state, product_graph_node2.state, label)
    )

    return projected_paths