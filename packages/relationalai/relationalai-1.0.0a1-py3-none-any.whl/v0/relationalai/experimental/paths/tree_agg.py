# TODO: put this in another producer?
from io import StringIO
import sys
from typing import Union
from v0.relationalai.std import rel

import pandas as pd

from v0.relationalai import dsl
from v0.relationalai.dsl import Type, alias, next_id
from v0.relationalai.std import aggregates

def tree_agg(Path: Type, group_by: str):
    """
    Aggregate a set of paths into a weighted tree, based on the
    provided `group_by` attribute.
    """
    
    tree_agg_id = next_id()
    model = Path._graph
    
    # create a new type for this aggregation
    TreeAggNode = dsl.Type(model, f"TreeAggNode{tree_agg_id}", omit_intrinsic_type_in_hash=True)
    
    path = Path()
    
    # HACK: get `path` into head of intermediate
    # without this, we get references to an undefined, zero-arity intermediate.
    path.id+1
    
    # Mark end of each path
    with model.rule():
        path_node = path.nodes
        max_node_idx = aggregates.max(path_node.index, per=[path])
        path_node.index == max_node_idx
        agg_node = TreeAggNode()
        agg_node.nodes == path_node
        agg_node.ends.add(path)
    
    # base case: children of root node
    with model.rule():
        # create root node
        root_node = TreeAggNode.add(depth=0)
        node1 = path.nodes
        node1.index == 1
        group_val = getattr(rel, group_by)(node1.value)
        root_child_node = TreeAggNode.add(
            parent=root_node, group_val=group_val,
        )
        root_child_node.nodes.add(node1)
    
    # step case: next node in the path
    with model.rule():
        node2, node3 = path.nodes.choose(2, unique=False)
        node3.index == node2.index+1
        agg_node2 = TreeAggNode()
        node2 == agg_node2.nodes
        group_val3 = getattr(rel, group_by)(node3.value)
        agg_node3 = TreeAggNode.add(parent=agg_node2, group_val=group_val3)
        agg_node3.nodes.add(node3)

    return TreeAggNode()

def get_tree(TreeAggNode: Type, label_attr: Union[str,None]=None):
    model = TreeAggNode._graph
    with model.query(tag="tree_agg_nodes") as select:
        tree_node = TreeAggNode()
        with model.match() as value:
            with model.case():
                value.add(aggregates.count(tree_node.ends, per=[tree_node]))
            with model.case():
                value.add(0)
        label = tree_node.group_val
        if label_attr is not None:
            label = getattr(tree_node.group_val, label_attr)
        res = select(
            alias(tree_node, "id"), tree_node.parent, alias(value, "count"), alias(label, "group_val")
        )
    return res.results

# ==== tree aggregation output helpers ====

def build_tree(data_frame):
    """
    Given a data frame with columns `treeaggnode`, `parent`, `name`, and `count`,
    build a tree data structure which we can print.
    """
    
    root_node = {
        "name": "<root>",
        "self_count": 0,
        "children": []
    }
    nodes = {}
    root_id = None
    # first scan: insert the nodes
    for i, row in data_frame.iterrows():
        node_id = row["id"]
        group_val = row["group_val"]
        if not isinstance(row["parent"], str):
            root_id = node_id
            nodes[node_id] = root_node
        else:
            nodes[node_id] = {
                "name": str(group_val),
                "self_count": row["count"],
                "children": []
            }
    # second scan: insert children
    for i, row in data_frame.iterrows():
        node_id = row["id"]
        node = nodes[node_id]
        parent_id = row["parent"]
        # TODO: assert that all the parent ids are the same
        if node_id is root_id:
            continue
        if parent_id not in nodes:
            root_id = parent_id
            nodes[root_id] = root_node
        nodes[parent_id]["children"].append(node)

    # choose root
    if root_id is None:
        raise Exception("never found root node")
    root = nodes[root_id]
    return compute_total_counts(root)

def compute_total_counts(tree):
    def compute_total(node):
        total = node["self_count"]
        for child in node["children"]:
            total += compute_total(child)
        node["total_count"] = total
        # sort node children by total count
        node["children"] = sorted(node["children"], key=lambda x: x["total_count"], reverse=True)
        return total
    compute_total(tree)
    return tree

def tree_to_df(tree):
    rows = []

    def traverse(node, depth=0):
        row = {
            "name": ('  ' * depth) + node["name"],
            "depth": depth,
            "total_count": node.get("total_count", 0),
        }
        rows.append(row)
        for child in node["children"]:
            traverse(child, depth+1)

    traverse(tree)
    return pd.DataFrame(rows)

MAX_INITIAL_WIDTH = 50
def pretty_print_tree(tree, indent=0, file=sys.stdout):
    if indent == 0:
        print("node", " " * (MAX_INITIAL_WIDTH-len("node")), "total", file=file)
    initial = "  " * indent + tree['name']
    print(initial, " " * (MAX_INITIAL_WIDTH-len(initial)), tree["total_count"], file=file)
    for child in tree["children"]:
        pretty_print_tree(child, indent+1, file=file)

def pretty_print_tree_to_str(tree, indent=0):
    io = StringIO()
    pretty_print_tree(tree, indent, file=io)
    return io.getvalue()
