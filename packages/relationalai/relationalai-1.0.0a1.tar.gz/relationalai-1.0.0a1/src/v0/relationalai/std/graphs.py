from __future__ import annotations
from collections import defaultdict
from copy import deepcopy
from decimal import Decimal
from numbers import Number, Real
import textwrap
from typing import Any, Type, Union
import warnings

import numpy
from ..errors import (
    DirectedGraphNotApplicable, DirectedGraphNotSupported,
    ParameterBoundBelowInclusive, ParameterBoundAboveInclusive,
    ParameterBoundBelowExclusive, ParameterBoundAboveExclusive,
    ParameterTypeMismatch, UnsupportedVisualizationError,
)
from .. import dsl, metamodel as mm
from ..environments import runtime_env, SnowbookEnvironment
from . import rel, Vars

rel_sv = rel._tagged(mm.Builtins.SingleValued)

Numeric = Union[int, float, Decimal]
NumericType = Type[Union[Numeric, Number]]

#--------------------------------------------------
# Standardized input validation functions
#--------------------------------------------------

def assert_type(name: str, value: Numeric, type_: NumericType):
    if not isinstance(value, type_):
        raise ParameterTypeMismatch(name, type_, value)

def assert_inclusive_lower_bound(name: str, value: Numeric, minimum: Numeric):
    if value < minimum:
        raise ParameterBoundBelowInclusive(name, value, minimum)

def assert_inclusive_upper_bound(name: str, value: Numeric, maximum: Numeric):
    if value > maximum:
        raise ParameterBoundAboveInclusive(name, value, maximum)

def assert_exclusive_lower_bound(name: str, value: Numeric, minimum: Numeric):
    if value <= minimum:
        raise ParameterBoundBelowExclusive(name, value, minimum)

def assert_exclusive_upper_bound(name: str, value: Numeric, maximum: Numeric):
    if value >= maximum:
        raise ParameterBoundAboveExclusive(name, value, maximum)


#--------------------------------------------------
# Helpers
#--------------------------------------------------

def unwrap(v):
    if v is None:
        return None
    return rel_sv.pyrel_default(rel_sv.pyrel_unwrap, v, v)


#--------------------------------------------------
# Algos
#--------------------------------------------------

class Compute:
    def __init__(self, graph:'Graph'):
        self._graph = graph
        self._lib = dsl.global_ns.graphlib

    def _config(self, **kwargs):
        return dsl.InlineRelation(self._graph.model, [
            *[(dsl.Symbol(k), v) for k, v in kwargs.items()],
        ])

    def _lookup(self, v):
        res = dsl.create_var()
        lookup_rel = getattr(rel, f"{self._graph._graph_ref()}_lookup")
        rel_sv.pyrel_default(lookup_rel, v, v, res)
        return res

    # --------------------------------------------------
    # Degree
    # --------------------------------------------------

    def degree(self, node, weight=None):
        if not weight:
            return self._lib.degree(self._graph, unwrap(node))
        return self._lib.weighted_degree(self._graph, unwrap(node))

    def indegree(self, node):
        return self._lib.indegree(self._graph, unwrap(node))

    def outdegree(self, node):
        return self._lib.outdegree(self._graph, unwrap(node))

    # --------------------------------------------------
    # Basics
    # --------------------------------------------------

    def num_nodes(self):
        return self._lib.num_nodes(self._graph)

    def num_edges(self):
        return self._lib.num_edges(self._graph)

    # --------------------------------------------------
    # Distance
    # --------------------------------------------------

    def distance(self, node1, node2):
        if self._graph.weighted:
            return self._lib.weighted_distance(self._graph, unwrap(node1), unwrap(node2))
        return self._lib.distance(self._graph, unwrap(node1), unwrap(node2))

    def diameter_range(self):
        min, max = dsl.create_vars(2)
        self._lib.diameter_range(self._graph, "min", min)
        self._lib.diameter_range(self._graph, "max", max)
        return (min, max)

    # --------------------------------------------------
    # Connectivity
    # --------------------------------------------------

    def is_connected(self):
        dsl.tag(self._lib.is_connected, mm.Builtins.GlobalFilter)
        return self._lib.is_connected(self._graph)

    def reachable_from(self, node: dsl.Producer) -> dsl.Producer:
        reachable = self._lib.reachable_from(self._graph, unwrap(node))
        return self._lookup(reachable)

    # Class-level dictionary to track which models have had `full_reachable_from` installed.
    # This is shared across all instances of Compute.
    # Motivation: the class-level dict ensures that full_reachable_from gets installed once per model,
    # not once per Compute.
    _full_reachable_from_installed = {}

    def full_reachable_from(self, node: dsl.Producer) -> dsl.Producer:
        key = self._graph.model.name
        if not self._full_reachable_from_installed.get(key, False):
            query = """
                namespace graphlib
                    @track(:graphlib, :full_reachable_from)
                    @outline
                    def full_reachable_from({G}, u, v) : {
                        G(:node, u) and (u = v or (exists((w) | full_reachable_from(G, u, w) and G(:edge, w, v))))
                    }
                end
            """
            self._graph.model.install_raw(query)
            self._full_reachable_from_installed[key] = True
        return self._lib.full_reachable_from(self._graph, node)

    def is_reachable(self, node1: dsl.Producer, node2: dsl.Producer) -> dsl.Expression:
        return self._lib.reachable_from(self._graph, unwrap(node1), unwrap(node2))

    # --------------------------------------------------
    # Triangles
    # --------------------------------------------------

    def num_triangles(self, node=None):
        if node is None:
            return self._lib.num_triangles(self._graph)
        return self._lib.triangle_count(self._graph, unwrap(node))

    def is_triangle(self, node1, node2, node3):
        return self._lib.triangle(self._graph, unwrap(node1), unwrap(node2), unwrap(node3))

    def triangles(self, node=None):
        # If no node is provided, return all triangles in the graph,
        # unique up to ordering of the nodes.
        if node is None:
            x, y, z = dsl.create_vars(3)
            self._lib.unique_triangle(self._graph, x, y, z)
            lx = self._lookup(x)
            ly = self._lookup(y)
            lz = self._lookup(z)
            return (lx, ly, lz)
        # If a node is provided, return all triangles that include that node,
        # unique up to order of the nodes.
        x, y = dsl.create_vars(2)
        model = dsl.get_graph()
        node = unwrap(node)
        with model.union(dynamic=True) as t:
            for (a, b, c) in ([node, x, y], [x, node, y], [x, y, node]):
                with model.scope():
                    self._lib.unique_triangle(self._graph, a, b, c)
                    t.add(node, a=a, b=b, c=c)
        la = self._lookup(t.a)
        lb = self._lookup(t.b)
        lc = self._lookup(t.c)
        return (la, lb, lc)

    # --------------------------------------------------
    # Clustering
    # --------------------------------------------------

    def local_clustering_coefficient(self, node):
        if not self._graph.undirected:
            raise DirectedGraphNotApplicable("local_clustering_coefficient")
        return self._lib.local_clustering_coefficient(self._graph, unwrap(node))

    def avg_clustering_coefficient(self):
        if not self._graph.undirected:
            raise DirectedGraphNotApplicable("avg_clustering_coefficient")
        return self._lib.average_clustering_coefficient(self._graph)

    # --------------------------------------------------
    # Ego network
    # --------------------------------------------------
    def ego_network(self, node, hops):
        if not isinstance(hops, int):
            raise TypeError(f"'hops' must be an integer, got {type(hops).__name__} instead")
        elif hops < 0:
            raise ValueError(f"'hops' must be non-negative, got {hops}")

        a, b = dsl.create_vars(2)
        self._lib.ego_network(self._graph, unwrap(node), hops, a, b)
        la = self._graph.compute._lookup(a)
        lb = self._graph.compute._lookup(b)
        return (la, lb)


    # --------------------------------------------------
    # Link Prediction
    # --------------------------------------------------

    def adamic_adar(self, node1, node2):
        return self._lib.adamic_adar(self._graph, unwrap(node1), unwrap(node2))

    def preferential_attachment(self, node1, node2):
        return self._lib.preferential_attachment(self._graph, unwrap(node1), unwrap(node2))

    def common_neighbor(self, node1, node2):
        neighbor = self._lib.common_neighbor(self._graph, unwrap(node1), unwrap(node2))
        return self._lookup(neighbor)

    # --------------------------------------------------
    # Similarity
    # --------------------------------------------------

    def cosine_similarity(self, node1, node2):
        if self._graph.weighted:
            return self._lib.weighted_cosine_similarity(self._graph, unwrap(node1), unwrap(node2))
        return self._lib.cosine_similarity(self._graph, unwrap(node1), unwrap(node2))

    def jaccard_similarity(self, node1, node2):
        if self._graph.weighted:
            return self._lib.weighted_jaccard_similarity(self._graph, unwrap(node1), unwrap(node2))
        return self._lib.jaccard_similarity(self._graph, unwrap(node1), unwrap(node2))

    # --------------------------------------------------
    # Centrality
    # --------------------------------------------------

    def pagerank(self, node, damping_factor=0.85, tolerance=1e-6, max_iter=20):
        assert_type("pagerank:tolerance", tolerance, Real)
        assert_exclusive_lower_bound("pagerank:tolerance", tolerance, 0.0)

        assert_type("pagerank:max_iter", max_iter, int)
        assert_exclusive_lower_bound("pagerank:max_iter", max_iter, 0)

        assert_type("pagerank:damping_factor", damping_factor, Real)
        assert_inclusive_lower_bound("pagerank:damping_factor", damping_factor, 0.0)
        assert_exclusive_upper_bound("pagerank:damping_factor", damping_factor, 1.0)

        config = self._config(
            graph=self._graph,
            damping_factor=float(damping_factor),
            tolerance=float(tolerance),
            max_iter=max_iter,
        )

        return self._lib.pagerank(config, unwrap(node))

    def betweenness_centrality(self, node):
        return self._lib.betweenness_centrality(self._graph, unwrap(node))

    def degree_centrality(self, node):
        if self._graph.weighted:
            return self._lib.weighted_degree_centrality(self._graph, unwrap(node))
        return self._lib.degree_centrality(self._graph, unwrap(node))

    def eigenvector_centrality(self, node):
        if not self._graph.undirected:
            raise DirectedGraphNotSupported("eigenvector_centrality", message_addendum="Consider PageRank as an alternative.")
        return self._lib.eigenvector_centrality(self._graph, unwrap(node))


    # --------------------------------------------------
    # Community Detection
    # --------------------------------------------------

    def weakly_connected_component(self, node):
        component = self._lib.weakly_connected_component(self._graph, unwrap(node))
        return self._lookup(component)

    def triangle_community(self, node):
        if not self._graph.undirected:
            raise DirectedGraphNotApplicable("triangle_community")
        return self._lib.triangle_community(self._graph, unwrap(node))

    def infomap(
            self,
            node,
            max_levels: int = 1,
            max_sweeps: int = 20,
            level_tolerance: float = 0.01,
            sweep_tolerance: float = 0.0001,
            teleportation_rate: float = 0.15,
            visit_rate_tolerance: float = 1e-15,
            randomization_seed: int | None = None,
    ):
        assert_type("infomap:max_levels", max_levels, int)
        assert_type("infomap:max_sweeps", max_sweeps, int)
        assert_exclusive_lower_bound("infomap:max_levels", max_levels, 0)
        assert_inclusive_lower_bound("infomap:max_sweeps", max_sweeps, 0)

        assert_type("infomap:level_tolerance", level_tolerance, Real)
        assert_type("infomap:sweep_tolerance", sweep_tolerance, Real)
        assert_inclusive_lower_bound("infomap:level_tolerance", level_tolerance, 0.0)
        assert_inclusive_lower_bound("infomap:sweep_tolerance", sweep_tolerance, 0.0)

        assert_type("infomap:teleportation_rate", teleportation_rate, Real)
        assert_inclusive_lower_bound("infomap:teleportation_rate", teleportation_rate, 1e-4)
        assert_exclusive_upper_bound("infomap:teleportation_rate", teleportation_rate, 1.0)

        assert_type("infomap:visit_rate_tolerance", visit_rate_tolerance, Real)
        assert_exclusive_lower_bound("infomap:visit_rate_tolerance", visit_rate_tolerance, 0.0)

        _config_dict = {
            "graph": self._graph,
            "max_levels": max_levels,
            "max_sweeps": max_sweeps,
            "level_tolerance": float(level_tolerance),
            "sweep_tolerance": float(sweep_tolerance),
            "teleportation_rate": float(teleportation_rate),
            "visit_rate_tolerance": float(visit_rate_tolerance),
        }

        if randomization_seed is not None:
            assert_type("infomap:randomization_seed", randomization_seed, int)
            assert_exclusive_lower_bound("infomap:randomization_seed", randomization_seed, 0)
            _config_dict["randomization_seed"] = randomization_seed

        config = self._config(**_config_dict)
        return self._lib.infomap(config, unwrap(node))

    def louvain(
            self,
            node,
            max_levels: int = 1,
            max_sweeps: int = 20,
            level_tolerance: float = 0.01,
            sweep_tolerance: float = 0.0001,
            randomization_seed: int | None = None,
    ):
        if not self._graph.undirected:
            raise DirectedGraphNotSupported("louvain")

        assert_type("louvain:max_levels", max_levels, int)
        assert_type("louvain:max_sweeps", max_sweeps, int)
        assert_exclusive_lower_bound("louvain:max_levels", max_levels, 0)
        assert_inclusive_lower_bound("louvain:max_sweeps", max_sweeps, 0)

        assert_type("louvain:level_tolerance", level_tolerance, Real)
        assert_type("louvain:sweep_tolerance", sweep_tolerance, Real)
        assert_inclusive_lower_bound("louvain:level_tolerance", level_tolerance, 0.0)
        assert_inclusive_lower_bound("louvain:sweep_tolerance", sweep_tolerance, 0.0)

        _config_dict = {
            "graph": self._graph,
            "max_levels": max_levels,
            "max_sweeps": max_sweeps,
            "level_tolerance": float(level_tolerance),
            "sweep_tolerance": float(sweep_tolerance),
        }

        if randomization_seed is not None:
            assert_type("louvain:randomization_seed", randomization_seed, int)
            assert_exclusive_lower_bound("louvain:randomization_seed", randomization_seed, 0)
            _config_dict["randomization_seed"] = randomization_seed

        config = self._config(**_config_dict)
        return self._lib.louvain(config, unwrap(node))

    def label_propagation(self, node, max_sweeps: int = 20, randomization_seed: int | None = None):
        assert_type("label_propagation:max_sweeps", max_sweeps, int)
        assert_inclusive_lower_bound("label_propagation:max_sweeps", max_sweeps, 0)

        _config_dict = {
            "graph": self._graph,
            "max_sweeps": max_sweeps,
        }

        if randomization_seed is not None:
            assert_type("label_propagation:randomization_seed", randomization_seed, int)
            assert_exclusive_lower_bound("label_propagation:randomization_seed", randomization_seed, 0)
            _config_dict["randomization_seed"] = randomization_seed

        config = self._config(**_config_dict)
        return self._lib.label_propagation(config, unwrap(node))

#--------------------------------------------------
# Edge
#--------------------------------------------------

class EdgeInstance:
    def __init__(self, edge:'Edge', from_:Any, to:Any, kwargs:dict={}):
        self._edge = edge
        self._graph = edge._graph
        self.from_ = from_
        self.to = to
        for k, v in kwargs.items():
            self._edge._prop(k)(from_, to, v)

    def __getattr__(self, name:str):
        v = Vars(1)
        self._edge._prop(name)(self.from_, self.to, v)
        return v

    def set(self, **kwargs):
        for k, v in kwargs.items():
            self._edge._prop(k).add(self.from_, self.to, v)
        return self

    def _to_var(self):
        raise Exception("Edges can't be returned directly, you can return the from_ and to properties individually")

class Edge:
    def __init__(self, graph:'Graph'):
        self._graph = graph
        self._type = dsl.RawRelation(self._graph.model, f"graph{self._graph.id}_edges", 2)
        self._type._type.parents.append(mm.Builtins.EDB)
        self._props = {}

    def _prop(self, name:str):
        if name not in self._props:
            self._props[name] = dsl.RawRelation(self._graph.model, f"graph{self._graph.id}_edge_{name}", 3)
        return self._props[name]

    def _is_weighted(self):
        if self._graph.weighted and 'weight' not in self._props:
            warnings.warn(
            f"""Graph is marked as weighted, but 'weight' property doesn't exist in this Edge.
            The code will still treat it as weighted, with default weight {self.default_weight}""",
            category=UserWarning
        )
        # Return true if either the Edge explicitly has a 'weight' property
        # or the Graph is declared as weighted in general.
        return self._graph.weighted


    def extend(self, prop:'dsl.Property', **kwargs):
        type = prop._provider
        with self._graph.model.rule():
            t = type()
            self.add(t, getattr(t, prop._name), **kwargs)

    def add(self, from_: Any, to: Any, **kwargs):
        # If the graph is flagged as weighted but the user did not provide 'weight',
        # auto‐populate it with the default weight (e.g. 1.0).
        self._type.add(from_, to)
        for k, v in kwargs.items():
            self._prop(k).add(from_, to, v)
        if self._graph.weighted and 'weight' not in kwargs:
            self._prop('weight').add(from_, to, self._graph.default_weight)
            warnings.warn(f"Graph is weighted, but 'weight' property is not provided. "
                          f"Using default weight {self._graph.default_weight}.", category=UserWarning)
        return EdgeInstance(self, from_, to, {})


    def __call__(self, from_:Any=None, to:Any=None, **kwargs):
        if from_ is None:
            from_ = Vars(1)
        if to is None:
            to = Vars(1)
        self._type(from_, to)
        return EdgeInstance(self, from_, to, kwargs)

    def __getattribute__(self, __name: str) -> Any:
        if __name in ["add", "extend"] or __name.startswith("_"):
            return super().__getattribute__(__name)
        return self._props[__name]

#--------------------------------------------------
# Graph
#--------------------------------------------------

class Graph:
    def __init__(self, model:dsl.Graph, undirected=False, weighted=False, default_weight=1.0, with_isolated_nodes=True):
        self.model = model
        self.id = dsl.next_id()
        self.compute = Compute(self)
        self.Node = dsl.Type(model, "nodes", scope=f"graph{self.id}_", omit_intrinsic_type_in_hash=True)
        self.Edge = Edge(self)
        self._undirected = undirected
        self._weighted = weighted
        self.default_weight=default_weight
        self._last_fetch = None

        create_graph_lines = []
        graph_type = "::graphlib::undirected_graph" if undirected else "::graphlib::directed_graph"
        if weighted:
            unwrapped = f"""
            def {self.Edge._prop("weight")._name}_unwrapped(au, bu, w): {{
                exists((a, b) |
                    {self.Edge._prop("weight")._name}(a, b, w) and
                    pyrel_default(pyrel_unwrap, a, a, au) and
                    pyrel_default(pyrel_unwrap, b, b, bu)
                )
            }}
            """
            create_graph_lines.extend([
                f"""{graph_type}[{{""",
                f"""  (:edge, {self.Edge._prop("weight")._name}_unwrapped);"""
            ])
        else:
            unwrapped = f"""
            def {self.Edge._type._name}_unwrapped(au, bu): {{
                exists((a, b) |
                    {self.Edge._type._name}(a, b) and
                    pyrel_default(pyrel_unwrap, a, a, au) and
                    pyrel_default(pyrel_unwrap, b, b, bu)
                )
            }}
            """
            create_graph_lines.extend([
                f"""{graph_type}[{{""",
                f"""  (:edge, {self.Edge._type._name}_unwrapped);"""
            ])

        if with_isolated_nodes:
            create_graph_lines.append(
                f"  (:node, pyrel_unwrap[{self.Node._type.name}]);"
            )
        create_graph_lines.extend([
            "  (:diagnostics)",
            "}]"
        ])
        create_graph = "\n".join(create_graph_lines)

        self.model.install_raw(textwrap.dedent(f"""
        declare {self.Node._type.name}
        declare {self.Edge._type._name}
        {unwrapped}
        @inline
        def {self._graph_ref()}_lookup(uw, orig): {{ {self.Node._type.name}(orig) and pyrel_unwrap(orig, uw) }}

        {f"declare {self.Edge._prop('weight')._name}" if weighted else ""}
        def {self._graph_ref()} {{{create_graph}}}
        def {self._graph_result_ref()} {{{self._graph_ref()}[:result]}}
        ic graphlib_edge_error(x...) requires not {self._graph_ref()}(:error, x...)
        """))

        # Add a rule that makes all nodes used in edges are also added to
        # the nodes relation
        with model.rule():
            a, b = dsl.create_vars(2)
            self.Edge._type(a, b)
            self.Node.add(a)
            self.Node.add(b)

    def _graph_ref(self):
        return f"graph{self.id}"

    def _graph_result_ref(self):
        return f"graph{self.id}_result"

    def _to_var(self):
        return getattr(rel, self._graph_result_ref())._to_var()

    def _is_weighted(self):
        return self.weighted
        # return self.edges._is_weighted()

    @property
    def undirected(self):
        return self._undirected

    @property
    def weighted(self):
        return self._weighted

    #--------------------------------------------------
    # Fetch
    #--------------------------------------------------

    def fetch(self):
        code = []
        code.append(f"def output(:nodes, n): {self.Node._type.name}(n)")
        for prop in self.Node._type.properties:
            scope = self.Node._scope
            code.append(f"def output(:nodes, :{prop.name.removeprefix(scope)}, n, v): {prop.name}(n, v)")
        code.append(f"def output(:edges, a,b): {self.Edge._type._name}(a,b)")
        for name, prop in self.Edge._props.items():
            code.append(f"def output(:edges, :{name}, a, b, v): {prop._name}(a, b, v)")

        output = {"nodes": defaultdict(dict), "edges": defaultdict(dict)}
        results = self.model.exec_raw("\n".join(code), raw_results=True)
        for set_ in results.results:
            path = [v[1:] for v in set_["relationId"].split("/")[2:] if v[0] == ":"]
            if path[0] not in ["nodes", "edges"]:
                continue
            cur = output[path[0]]
            if path[0] == "nodes":
                if len(path) == 1:
                    for (n,) in set_["table"].itertuples(index=False):
                        cur[n]
                else:
                    for (n, v) in set_["table"].itertuples(index=False):
                        cur[n][path[1]] = v
            elif path[0] == "edges":
                if len(path) == 1:
                    for (a, b) in set_["table"].itertuples(index=False):
                        # If the graph is undirected, normalize the order of
                        # the source and target nodes.
                        if self.undirected and a > b:
                            a, b = b, a
                        cur[(a, b)]
                else:
                    for (a, b, v) in set_["table"].itertuples(index=False):
                        if self.undirected and a > b:
                            a, b = b, a
                        cur[(a, b)][path[1]] = v
            else:
                raise Exception(f"Unexpected path: {path}")
        self._last_fetch = output
        return output

    #--------------------------------------------------
    # Visualize
    #--------------------------------------------------

    default_visual_props = {
        "node": {
            "color": "black",
            "opacity": 1,
            "size": 10,
            "shape": "circle",
            "border_color": "black",
            "border_size": 1,
            "label_color": "black",
            "label_size": 10,
        },
        "edge": {
            "color": "#999",
            "opacity": 1,
            "size": 2,
            "shape": "circle",
            "border_color": "#999",
            "border_size": 1,
            "label_color": "black",
            "label_size": 10,
            "arrow_size": 4,
            "arrow_color": "#999",
        }
    }

    _style_map = {
        "arrow_size": "arrow_size",
        "arrow_color": "arrow_color",
    }

    def _visual_props(self, prop_def, metadata):
        for k, v in prop_def.items():
            if callable(v):
                metadata[k] = v(metadata)

        # adjust some types as needed by JSON
        for k, v in metadata.items():
            # decimals are not supported, convert to floats
            if isinstance(v, Decimal):
                metadata[k] = float(v)
            # numpy specific ints also not supported, convert to int
            if isinstance(v, numpy.integer):
                metadata[k] = int(v)

        # For some reason, the existance of "id" in the metadata
        # results in edges not getting displayed in the visualization,
        # so we remove it.
        if "id" in metadata:
            del metadata["id"]
        return metadata

    def _visual_dict(self, style: dict, use_cache = False) -> dict:
        data = self._last_fetch if use_cache else None
        if not data:
            data = self.fetch()
        style = deepcopy(style)
        if "node" not in style:
            style["node"] = {}
        if "edge" not in style:
            style["edge"] = {}
        merged_style = deepcopy(self.default_visual_props)
        for category in ["node", "edge"]:
            for k, v in style.get(category, {}).items():
                if not callable(v):
                    merged_style[category][k] = v
        flat_style = {
            self._style_map.get(k, f"{type}_{k}"): v
            for type, category in merged_style.items()
            for k, v in category.items()
        }

        return {
            "graph": {
                "directed": not self.undirected,
                "metadata": flat_style,
                "nodes": {
                    node_id: {
                        **({"label": str(info["label"])} if "label" in info else {}),
                        "metadata": self._visual_props(style["node"], info.copy()),
                    }
                    for (node_id, info) in data["nodes"].items()
                },
                "edges": [
                    {"source": source, "target": target, "metadata": self._visual_props(style["edge"], info.copy())}
                    for ((source, target), info) in data["edges"].items()
                ],
            }
        }

    def visualize(self, three=False, style: dict | None = None, use_cache = False, **kwargs):
        if isinstance(runtime_env, SnowbookEnvironment) and runtime_env.runner != "container":
            raise UnsupportedVisualizationError()
        import gravis as gv
        style = style if style is not None else {"node": {}, "edge": {}}
        vis = gv.vis if not three else gv.three
        graph_dict = self._visual_dict(style=style, use_cache=use_cache)
        # Use defaults for the following kwargs if not provided
        new_kwargs = {
            "node_label_data_source": "label",
            "edge_label_data_source": "label",
            "show_edge_label": True,
            "edge_curvature": 0.4,
        } | kwargs
        fig = vis(graph_dict, **new_kwargs)
        return fig

#--------------------------------------------------
# Path
#--------------------------------------------------

class Path:
    def __init__(self, *args):
        self.edges = []
        self.nodes = []
        pass

    def __getitem__(self, item):
        return self

#--------------------------------------------------
# Exports
#--------------------------------------------------

__all__ = ["Graph", "Path"]
