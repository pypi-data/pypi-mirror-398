from v0.relationalai.semantics import Integer, define, std
from ..graph import Graph

def create_labeled_grid(model, side_length, directed = True, label = "A"):
    """
    Create a grid Graph instance from a Model. The number of edges in each side of the grid
    is given by the parameter `side`.
    """
    Node = model.Concept("GridNode")
    Edge = model.Relationship(f"edge1 {{{Node}}} {{{Node}}} {{String}}")

    n, m = Integer.ref(), Integer.ref()
    u, v = Node.ref(), Node.ref()

    define(Node.new(row = n, col = m)).where(
        n == std.range(1, side_length + 2, 1),  # n + 1 nodes so n edges in each side
        m == std.range(1, side_length + 2, 1)
    )

    define(Edge(u, v, label)).where(
        Node(u),
        Node(v),
        u.row == v.row,
        v.col == u.col + 1
    )

    define(Edge(u, v, label)).where(
        Node(u),
        Node(v),
        u.col == v.col,
        v.row == u.row + 1
    )

    if not directed:
        define(Edge(u, v, label)).where(Edge(v, u, label))

    return Graph(model, Node, Edge)
