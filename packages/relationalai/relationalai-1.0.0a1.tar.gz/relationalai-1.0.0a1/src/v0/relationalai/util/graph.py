from typing import List, Optional, Tuple, TypeVar
from collections import defaultdict

T = TypeVar('T')

def topological_sort(nodes: List[T], edges: List[Tuple[T, T]]) -> List[T]:
    order = _topological_sort(nodes, edges)
    if order is None:
        raise ValueError("The graph contains a cycle")
    return order

def is_acyclic_graph(nodes: List[T], edges: List[Tuple[T, T]]) -> bool:
    return _topological_sort(nodes, edges) is not None

def _topological_sort(nodes: List[T], edges: List[Tuple[T, T]]) -> Optional[List[T]]:
    order = []

    # simple implementation of Kahn's Algorithm

    # index edges
    edge_list = defaultdict(list)
    for src, tgt in edges:
        edge_list[src].append(tgt)

    # compute in_degree of nodes
    in_degree = dict()
    for _, tgt in edges:
        if tgt in in_degree:
            in_degree[tgt] = in_degree[tgt] + 1
        else:
            in_degree[tgt] = 1

    # start the working list with nodes that don't have incoming edges
    work = list(filter(lambda n: n not in in_degree, nodes))
    while work:
        n = work.pop()
        order.append(n)
        for neighbour in edge_list[n]:
            new_in_degree = in_degree[neighbour] - 1
            in_degree[neighbour] = new_in_degree
            if new_in_degree == 0:
                work.append(neighbour)

    # all nodes sorted, return the order
    if len(order) == len(nodes):
        return order

    # some nodes were not sorted, graph is acyclic, return None
    return None
