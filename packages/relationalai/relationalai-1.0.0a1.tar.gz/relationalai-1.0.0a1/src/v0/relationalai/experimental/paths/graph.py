from v0.relationalai.semantics import Integer, define, Concept, Relationship, std


class Graph:
    def __init__(self, model, Node:Concept, Edge:Relationship):
        """
        Initialize a Graph instance with Node and Edge concepts.
        """
        self.Node = Node
        self.Edge = Edge
        self.model = model


    @classmethod
    def from_edge_list(cls, model, edge_list):
        """
        Create a Graph instance from a Model.
        The Model should have Node and Edge concepts defined.
        """

        Node = model.Concept("Node")

        if len(edge_list[0]) == 2:
            Edge = model.Relationship(f"edge4 {{{Node}}} {{{Node}}}")

            for src, dst, in edge_list:
                u = Node.new(id=src)
                v = Node.new(id=dst)

                define(u)
                define(v)
                define(Edge(u, v))
        else:
            Edge = model.Relationship(f"edge5 {{{Node}}} {{{Node}}} {{String}}")

            for src, dst, label in edge_list:
                u = Node.new(id=src)
                v = Node.new(id=dst)

                define(u)
                define(v)
                define(Edge(u, v, label))

        return cls(model, Node, Edge)


    @classmethod
    def construct_grid(cls, model, side, tp = 'directed'):
        """
        Create a grid Graph instance from a Model. The length of the side of the grid
        is given by the parameter `side`.
        The Model should have Node and Edge concepts defined.
        """
        Node = model.Concept("Node")
        Edge = model.Relationship(f"edge6 {{{Node}}} {{{Node}}}")

        n, m = Integer.ref(), Integer.ref()
        u, v = Node.ref(), Node.ref()

        define(Node.new(row = n, col = m)).where(
            n == std.range(1, side + 1, 1),
            m == std.range(1, side + 1, 1)
        )

        define(Edge(u, v)).where(
            Node(u),
            Node(v),
            u.row == v.row,
            v.col == u.col + 1
        )

        define(Edge(u, v)).where(
            Node(u),
            Node(v),
            u.col == v.col,
            v.row == u.row + 1
        )

        if tp == 'undirected':
            define(Edge(u, v)).where(Edge(v, u))

        return cls(model, Node, Edge)


    @classmethod
    def construct_diamond(cls, model, diamonds, tp = 'directed'):
        """
        Create a diamond Graph instance from a Model. The number of diamonds in the graph
        is given by the parameter `diamonds`.
        The Model should have Node and Edge concepts defined.
        """
        Node = model.Concept("Node")
        Edge = model.Relationship(f"edge7 {{{Node}}} {{{Node}}}")

        n = Integer.ref()
        u, v = Node.ref(), Node.ref()

        define(Node.new(id = n)).where(
            n == std.range(1, 3*diamonds + 2, 1)
        )

        define(Edge(u, v)).where(
            n == std.range(1, diamonds + 1, 1),
            Node(u),
            Node(v),
            u.id == 3*(n-1) + 1,
            v.id == 3*(n-1) + 2
        )

        define(Edge(u, v)).where(
            n == std.range(1, diamonds + 1, 1),
            Node(u),
            Node(v),
            u.id == 3*(n-1) + 1,
            v.id == 3*(n-1) + 3
        )

        define(Edge(u, v)).where(
            n == std.range(1, diamonds + 1, 1),
            Node(u),
            Node(v),
            u.id == 3*(n-1) + 2,
            v.id == 3*n + 1
        )

        define(Edge(u, v)).where(
            n == std.range(1, diamonds + 1, 1),
            Node(u),
            Node(v),
            u.id == 3*(n-1) + 3,
            v.id == 3*n + 1
        )

        if tp == 'undirected':
            define(Edge(u, v)).where(Edge(v, u))

        return cls(model, Node, Edge)


    @classmethod
    def construct_rake(cls, model, length, fan_out, tp = 'directed'):
        """
        Create a grid Graph instance from a Model. The length of the side of the grid
        is given by the parameter `side`.
        The Model should have Node and Edge concepts defined.
        """
        Node = model.Concept("Node")
        Edge = model.Relationship(f"edge8 {{{Node}}} {{{Node}}}")

        start, i = Integer.ref(), Integer.ref()
        u, v = Node.ref(), Node.ref()

        define(Node.new(id = i)).where(
            i == std.range(0,  (length + 1) * (fan_out + 1), 1)
        )

        define(Edge(u, v)).where(
            i == std.range(0, length, 1),
            Node(u),
            Node(v),
            u.id == i,
            v.id == i + 1
        )

        define(Edge(u, v)).where(
            i == std.range(length + 1, (length + 1) * fan_out + 1, length + 1),
            Node(u),
            Node(v),
            u.id == length,
            v.id == i
        )

        define(Edge(u, v)).where(
            start == std.range(length + 1, (length + 1) * fan_out + 2, length + 1),
            i == std.range(start, start + length, 1),
            Node(u),
            Node(v),
            u.id == i,
            v.id == i + 1
        )

        if tp == 'undirected':
            define(Edge(u, v)).where(Edge(v, u))

        return cls(model, Node, Edge)
