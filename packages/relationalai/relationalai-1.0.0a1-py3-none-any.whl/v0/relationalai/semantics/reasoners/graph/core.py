"""
Core functionality for the graphs package.
"""

import warnings

from decimal import Decimal
from functools import cached_property
from numbers import Number, Real
from typing import Optional, Type, Union

import gravis
import numpy

from v0.relationalai.semantics import (
    Model, Concept, Relationship,
    Error, Integer, Float,
    where, define, union, not_, select,
    min, max, rank, desc,
    count, sum, avg,
)
from v0.relationalai.docutils import include_in_docs
from v0.relationalai.semantics.internal import annotations, AnyEntity
from v0.relationalai.semantics.internal import internal as builder_internal # For primitive graph algorithms.
from v0.relationalai.semantics.std.math import abs, isnan, isinf, maximum, natural_log, sqrt
from v0.relationalai.semantics.std.integers import int64

Numeric = Union[int, float, Decimal]
NumericType = Type[Union[Numeric, Number]]


# Preliminary graph library exception types,
# and associated standardized input validation functions.

class DirectedGraphNotApplicable(ValueError):
    def __init__(self, name: str):
        super().__init__(name)
        self.name = f"algorithm `{name}` is not applicable to directed graphs"

class DirectedGraphNotSupported(ValueError):
    def __init__(self, name: str, message_addendum: str = ""):
        message = f"algorithm `{name}` does not currently support directed graphs{'' if not message_addendum else f'. {message_addendum}'}"
        super().__init__(message)


class ParameterTypeMismatch(ValueError):
    def __init__(self, name: str, type_, value):
        super().__init__(name)
        self.name = (
            f"parameter `{name}` must be of type {type_.__name__.lower()}, "
            f"but its value {value!r} is of type {type(value)}"
        )

def _assert_type(name: str, value: Numeric, type_: NumericType):
    if not isinstance(value, type_):
        raise ParameterTypeMismatch(name, type_, value)


class ParameterBoundBelowInclusive(ValueError):
    def __init__(self, name: str, value, minimum):
        super().__init__(name)
        self.name = f"parameter `{name}` must be greater than or equal to {minimum}, but is {value!r}"

class ParameterBoundAboveInclusive(ValueError):
    def __init__(self, name: str, value, maximum):
        super().__init__(name)
        self.name = f"parameter `{name}` must be less than or equal to {maximum}, but is {value!r}"

class ParameterBoundBelowExclusive(ValueError):
    def __init__(self, name: str, value, minimum):
        super().__init__(name)
        self.name = f"parameter `{name}` must be strictly greater than {minimum}, but is {value!r}"

class ParameterBoundAboveExclusive(ValueError):
    def __init__(self, name: str, value, maximum):
        super().__init__(name)
        self.name = f"parameter `{name}` must be strictly less than {maximum}, but is {value!r}"

def _assert_inclusive_lower_bound(name: str, value: Numeric, minimum: Numeric):
    if value < minimum:
        raise ParameterBoundBelowInclusive(name, value, minimum)

def _assert_inclusive_upper_bound(name: str, value: Numeric, maximum: Numeric):
    if value > maximum:
        raise ParameterBoundAboveInclusive(name, value, maximum)

def _assert_exclusive_lower_bound(name: str, value: Numeric, minimum: Numeric):
    if value <= minimum:
        raise ParameterBoundBelowExclusive(name, value, minimum)

def _assert_exclusive_upper_bound(name: str, value: Numeric, maximum: Numeric):
    if value >= maximum:
        raise ParameterBoundAboveExclusive(name, value, maximum)


@include_in_docs
class Graph():
    """
    A graph object.

    Parameters
    ----------
    model : Model
        The model to use for the graph.
    directed : bool
        Whether the graph is directed.
    weighted : bool
        Whether the graph is weighted.
    aggregator : str | None
        The aggregation function to use for multi-edges.
    node_concept : Concept | None
        The concept to use for the nodes in the graph.
    edge_concept : Concept | None
        The concept to use for the edges in the graph.
    edge_src_relationship : Relationship | None
        The relationship to use for the source nodes in the graph.
    edge_dst_relationship : Relationship | None
        The relationship to use for the destination nodes in the graph.
    edge_weight_relationship : Relationship | None
        The relationship to use for the edge weights in the graph.

    Attributes
    ----------
    directed : bool
        Whether the graph is directed.
    weighted : bool
        Whether the graph is weighted.
    Node : Concept
        The nodes of the graph.
    Edge : Concept
        The edges of the graph.
    EdgeSrc : Relationship
        The relationship that determines source nodes for edges in the graph.
    EdgeDst : Relationship
        The relationship that determines destination nodes for edges in the graph.
    EdgeWeight : Relationship
        The relationship that determines edge weights in the graph.
    """
    def __init__(self,
            model,
            *,
            directed: bool,
            weighted: bool,
            aggregator: Optional[str] = None,
            node_concept: Optional[Concept] = None,
            edge_concept: Optional[Concept] = None,
            edge_src_relationship: Optional[Relationship] = None,
            edge_dst_relationship: Optional[Relationship] = None,
            edge_weight_relationship: Optional[Relationship] = None,
        ):
        # Validate the required `directed`, `weighted`, and `model` arguments (type).
        assert isinstance(directed, bool), (
            "The `directed` argument must be `True` or `False`, "
            f"but is a `{type(directed).__name__}`."
        )
        assert isinstance(weighted, bool), (
            "The `weighted` argument must be `True` or `False`, "
            f"but is a `{type(weighted).__name__}`."
        )
        assert isinstance(model, Model), (
            "The `model` argument must be a `relationalai.semantics.Model`, "
            f"but is a `{type(model).__name__}`."
        )
        self.directed = directed
        self.weighted = weighted
        self._model = model

        # Validate the optional `aggregator` argument.
        assert aggregator in (None, "sum"), (
            "The `aggregator` argument must be either `None` or 'sum', "
            f"but is {aggregator!r}."
        )
        # Store aggregator mode.
        self._aggregator = aggregator


        # Validate that the optional `node_concept`, `edge_concept`, and related
        # relationship arguments appear in valid combinations:

        if self.weighted:
            edge_args = (edge_concept, edge_src_relationship, edge_dst_relationship, edge_weight_relationship)
        else: # not self.weighted
            edge_args = (edge_concept, edge_src_relationship, edge_dst_relationship)
        any_edge_args = any(arg is not None for arg in edge_args)
        all_edge_args = all(arg is not None for arg in edge_args)

        # If the user provides any of the edge arguments,
        # they must provide a `node_concept`.
        assert not any_edge_args or isinstance(node_concept, Concept), \
            "The `node_concept` argument must be provided when providing `edge_...` arguments."

        # If the graph is weighted, and the user provides any of
        # the edge_ arguments, they must provide all four such arguments.
        if self.weighted:
            assert not any_edge_args or all_edge_args, (
                "For weighted graphs, if any of the `edge_concept`, `edge_src_relationship`, "
                "`edge_dst_relationship`, or `edge_weight_relationship` arguments "
                "is provided, all four such arguments must be provided."
            )
        # If the graph is unweighted, the user may not provide
        # the `edge_weight_relationship` argument, and if they provide
        # any of the edge_ arguments, they must provide all three such arguments.
        else: # not self.weighted
            assert edge_weight_relationship is None, (
                "For unweighted graphs, the `edge_weight_relationship` "
                "argument must not be provided."
            )
            assert not any_edge_args or all_edge_args, (
                "For unweighted graphs, if any of the `edge_concept`, "
                "`edge_src_relationship`, or `edge_dst_relationship` arguments "
                "are provided, all three such arguments must be provided."
            )


        # Now that we know we have a valid combination of the `node_concept`,
        # `edge_concept`, and related relationship arguments,
        # validate their types, models, and schemas:

        # Validate the optional `node_concept` argument's type and model.
        assert isinstance(node_concept, (type(None), Concept)), (
            "The `node_concept` argument must be either a `Concept` or `None`, "
            f"but is a `{type(node_concept).__name__}`."
        )
        assert isinstance(node_concept, type(None)) or (node_concept._model is model), \
            "The given `node_concept` argument must be attached to the given `model` argument."
        self._user_node_concept = node_concept

        # Validate the optional `edge_concept` argument's type and model.
        assert isinstance(edge_concept, (type(None), Concept)), (
            "The `edge_concept` argument must be either a `Concept` or `None`, "
            f"but is a `{type(edge_concept).__name__}`."
        )
        assert edge_concept is None or (edge_concept._model is model), \
            "The given `edge_concept` argument must be attached to the given `model` argument."

        # Validate the `edge_src_relationship` argument's type, model, and schema.
        assert isinstance(edge_src_relationship, (type(None), Relationship)), (
            "The `edge_src_relationship` argument must be either a `Relationship` or `None`, "
            f"but is a `{type(edge_src_relationship).__name__}`."
        )
        assert edge_src_relationship is None or (edge_src_relationship._model is model), \
            "The given `edge_src_relationship` argument must be attached to the given `model` argument."
        if isinstance(edge_src_relationship, Relationship):
            # The combination of assertions above guarantee that `edge_concept`
            # and `node_concept` are not `None` at this point, but the linter
            # can't figure that out. To make the linter happy, re-assert:
            assert edge_concept is not None and node_concept is not None

            assert len(edge_src_relationship._fields) == 2, (
                "The `edge_src_relationship` argument must be a binary relationship, "
                f"but it has {len(edge_src_relationship._fields)} fields."
            )
            assert edge_src_relationship._fields[0].type_str == edge_concept._name, (
                "The first field of the `edge_src_relationship` relationship "
                f"must match the edge concept ('{edge_concept._name}'), "
                f"but is '{edge_src_relationship._fields[0].type_str}'."
            )
            assert edge_src_relationship._fields[1].type_str == node_concept._name, (
                "The second field of the `edge_src_relationship` relationship "
                f"must match the node concept ('{node_concept._name}'), "
                f"but is '{edge_src_relationship._fields[1].type_str}'."
            )

        # Validate the `edge_dst_relationship` argument's type, model, and schema.
        assert isinstance(edge_dst_relationship, (type(None), Relationship)), (
            "The `edge_dst_relationship` argument must be either a `Relationship` or `None`, "
            f"but is a `{type(edge_dst_relationship).__name__}`."
        )
        assert edge_dst_relationship is None or (edge_dst_relationship._model is model), \
            "The given `edge_dst_relationship` argument must be attached to the given `model` argument."
        if isinstance(edge_dst_relationship, Relationship):
            # The combination of assertions above guarantee that `edge_concept`
            # and `node_concept` are not `None` at this point, but the linter
            # can't figure that out. To make the linter happy, re-assert:
            assert edge_concept is not None and node_concept is not None

            assert len(edge_dst_relationship._fields) == 2, (
                "The `edge_dst_relationship` argument must be a binary relationship, "
                f"but it has {len(edge_dst_relationship._fields)} fields."
            )
            assert edge_dst_relationship._fields[0].type_str == edge_concept._name, (
                "The first field of the `edge_dst_relationship` relationship "
                f"must match the edge concept ('{edge_concept._name}'), "
                f"but is '{edge_dst_relationship._fields[0].type_str}'."
            )
            assert edge_dst_relationship._fields[1].type_str == node_concept._name, (
                "The second field of the `edge_dst_relationship` relationship "
                f"must match the node concept ('{node_concept._name}'), "
                f"but is '{edge_dst_relationship._fields[1].type_str}'."
            )

        # Validate the `edge_weight_relationship` argument's type, model, and schema.
        assert isinstance(edge_weight_relationship, (type(None), Relationship)), (
            "The `edge_weight_relationship` argument must be either a `Relationship` or `None`, "
            f"but is a `{type(edge_weight_relationship).__name__}`."
        )
        assert edge_weight_relationship is None or (edge_weight_relationship._model is model), \
            "The given `edge_weight_relationship` argument must be attached to the given `model` argument."
        if isinstance(edge_weight_relationship, Relationship):
            # The combination of assertions above guarantee that `edge_concept`
            # and `node_concept` are not `None` at this point, but the linter
            # can't figure that out. To make the linter happy, re-assert:
            assert edge_concept is not None and node_concept is not None

            assert len(edge_weight_relationship._fields) == 2, (
                "The `edge_weight_relationship` argument must be a binary relationship, "
                f"but it has {len(edge_weight_relationship._fields)} fields."
            )
            assert edge_weight_relationship._fields[0].type_str == edge_concept._name, (
                "The first field of the `edge_weight_relationship` relationship "
                f"must match the edge concept ('{edge_concept._name}'), "
                f"but is '{edge_weight_relationship._fields[0].type_str}'."
            )
            assert edge_weight_relationship._fields[1].type_str == "Float", (
                "The second field of the `edge_weight_relationship` relationship "
                f"must have type 'Float', but is '{edge_weight_relationship._fields[1].type_str}'."
            )

        # Finally store any user-provided node concept,
        # edge concept, and associated relationship arguments.
        self._user_node_concept = node_concept
        self._user_edge_concept = edge_concept
        self._user_edge_src_relationship = edge_src_relationship
        self._user_edge_dst_relationship = edge_dst_relationship
        self._user_edge_weight_relationship = edge_weight_relationship


        # Unless the user passes in existing `Concept`s to serve as
        # the graph's `Node` and/or `Edge` `Concept`s, this class generates
        # new `Node` and/or `Edge` concepts with quasi-unique name-strings,
        # attempting to avoid name-string collisions while retaining
        # as much determinism, consistency, and readability as possible:
        #
        # The following counter tracks the number of graphs attached to the model,
        # initialized to zero but immediately incremented to start from one.
        # (`setattr` and `getattr` are used to make linting happy.)
        if not hasattr(model, "_graph_counter"):
            setattr(model, "_graph_counter", 0)
        setattr(model, "_graph_counter", getattr(model, "_graph_counter", 0) + 1)
        #
        # The generated `Node` and `Edge` `Concept` name-strings incorporate
        # this counter to allow coexistence of multiple graphs in the same model.
        # (`getattr` is used to make linting happy.)
        self._graph_id = getattr(model, "_graph_counter")
        self._NodeConceptStr = node_concept._name if node_concept else f"graph{self._graph_id}_Node"
        self._EdgeConceptStr = edge_concept._name if edge_concept else f"graph{self._graph_id}_Edge"

        # Initialize cache for visualization data.
        self._last_visualization_fetch = None

        # The remainder of the library is lazily defined and attached
        # to the model through cached-property member fields of this class.


    @cached_property
    def Node(self) -> Concept:
        """Lazily define and cache the self.Node concept."""
        _Node = self._user_node_concept or self._model.Concept(self._NodeConceptStr, extends=[AnyEntity])
        _Node.annotate(annotations.track("graphs", "Node"))
        return _Node

    @cached_property
    def Edge(self):
        """Lazily define and cache the self.Edge concept and friends,
        by passing through to self._EdgeComplex."""
        _Edge, _, _, _ = self._EdgeComplex
        _Edge.annotate(annotations.track("graphs", "Edge"))
        return _Edge

    @cached_property
    def EdgeSrc(self):
        """Lazily define and cache the self.EdgeSrc relationship and friends,
        by passing through to self._EdgeComplex."""
        _, _EdgeSrc, _, _ = self._EdgeComplex
        return _EdgeSrc

    @cached_property
    def EdgeDst(self):
        """Lazily define and cache the self.EdgeDst relationship and friends,
        by passing through to self._EdgeComplex."""
        _, _, _EdgeDst, _ = self._EdgeComplex
        return _EdgeDst

    @cached_property
    def EdgeWeight(self):
        """Lazily define and cache the self.EdgeWeight relationship and friends,
        by passing through to self._EdgeComplex."""
        _, _, _, _EdgeWeight = self._EdgeComplex
        return _EdgeWeight

    @cached_property
    def _EdgeComplex(self):
        """
        Lazily define and cache self._EdgeComplex, which consists of
        what becomes the self.Edge concept, the self.EdgeSrc relationship,
        the self.EdgeDst relationship, the self.EdgeWeight relationship,
        and all associated logic. Each of the preceding properties
        passes through to this property, such that all of the above
        are lazily defined and cached together, once.
        """
        if self._user_edge_concept:
            # The validations in __init__ guarantee that if the user provided
            # an edge concept, they must have provided all associated edge
            # relationships appropriate for their (un/weighted) graph type.
            assert self._user_edge_src_relationship is not None  # appease linter
            assert self._user_edge_dst_relationship is not None  # appease linter
            # In this case, use the provided concept and relationships
            # rather than generating new ones.
            _Edge = self._user_edge_concept
            _EdgeSrc = self._user_edge_src_relationship
            _EdgeDst = self._user_edge_dst_relationship
            if self.weighted:
                assert self._user_edge_weight_relationship is not None  # appease linter
                _EdgeWeight = self._user_edge_weight_relationship
            else: # not self.weighted
                # For unweighted graphs, generate a weight relationship
                # to simplify the logic below.
                _EdgeWeight = self._model.Relationship(f"{{edge:{self._EdgeConceptStr}}} has weight {{weight:Float}}")

            # Define diagnostic messages specialized for this case.
            _edge_must_have_source_message = (
                f"Every edge (`Graph.Edge`, bound to the `{_Edge._name}` concept "
                f"via the `edge_concept` argument), must have a source (`Graph.EdgeSrc`, "
                f"bound to the `edge_src_relationship` argument)."
            )
            _edge_must_have_destination_message = (
                f"Every edge (`Graph.Edge`, bound to the `{_Edge._name}` concept "
                f"via the `edge_concept` argument), must have a destination (`Graph.EdgeDst`, "
                f"bound to the `edge_dst_relationship` argument)."
            )
            _edge_must_have_weight_message = (
                f"For weighted graphs, every edge (`Graph.Edge`, bound to the `{_Edge._name}` concept "
                f"via the `edge_concept` argument), must have a weight (`Graph.EdgeWeight`, "
                f"bound to the `edge_weight_relationship` argument)."
            )

        else: # not self._user_edge_concept
            # The user did not provide an edge concept and associated relationships,
            # so generate that concept and those relationships.
            _Edge = self._model.Concept(self._EdgeConceptStr)
            # In this case we can safely make the associated relationships
            # properties of the edge concept, improving user experience.
            _Edge.src = self._model.Relationship(f"{{edge:{self._EdgeConceptStr}}} has source {{src:{self._NodeConceptStr}}}")
            _Edge.dst = self._model.Relationship(f"{{edge:{self._EdgeConceptStr}}} has destination {{dst:{self._NodeConceptStr}}}")
            _Edge.weight = self._model.Relationship(f"{{edge:{self._EdgeConceptStr}}} has weight {{weight:Float}}")
            # Nonetheless we must bind them as follows to share the downstream logic.
            _EdgeSrc = _Edge.src
            _EdgeDst = _Edge.dst
            _EdgeWeight = _Edge.weight

            # Define diagnostic messages specialized for this case.
            _edge_must_have_source_message = \
                "Every edge (`Graph.Edge`) must have a source (`Graph.Edge.src`)."
            _edge_must_have_destination_message = \
                "Every edge (`Graph.Edge`) must have a destination (`Graph.Edge.dst`)."
            _edge_must_have_weight_message = \
                "Every edge (`Graph.Edge`) must have a weight (`Graph.Edge.weight`)."

        # All `Edge`s must have a `src`:
        where(_Edge, not_(_EdgeSrc(_Edge, self.Node))).define(
            Error.new(message=_edge_must_have_source_message, edge=_Edge)
        )

        # All `Edge`s must have a `dst`:
        where(_Edge, not_(_EdgeDst(_Edge, self.Node))).define(
            Error.new(message=_edge_must_have_destination_message, edge=_Edge)
        )

        # If weighted, ...
        if self.weighted:
            src, dst = self.Node.ref(), self.Node.ref()
            # ... all `Edge`s must have a `weight`:
            where(
                _Edge, not_(_EdgeWeight(_Edge, Float)), # Necessary for check.
                _EdgeSrc(_Edge, src), _EdgeDst(_Edge, dst), # Solely for message.
            ).define(
                Error.new(
                    message=_edge_must_have_weight_message,
                    edge=_Edge, source=src, destination=dst,
                )
            )
            # ... edge weights must not be NaN:
            where(
                _Edge, _EdgeWeight(_Edge, Float), isnan(Float), # Necessary for check.
                _EdgeSrc(_Edge, src), _EdgeDst(_Edge, dst), # Solely for message.
            ).define(
                Error.new(
                    message="Edge weights must not be NaN.",
                    edge=_Edge, source=src, destination=dst, weight=Float,
                )
            )
            # ... edge weights must not be infinite:
            where(
                _Edge, _EdgeWeight(_Edge, Float), isinf(Float), # Necessary for check.
                _EdgeSrc(_Edge, src), _EdgeDst(_Edge, dst), # Solely for message.
            ).define(
                Error.new(
                    message="Edge weights must not be infinite.",
                    edge=_Edge, source=src, destination=dst, weight=Float,
                )
            )
            # ... and edge weights must not be negative:
            where(
                _Edge, _EdgeWeight(_Edge, Float), Float < 0.0, # Necessary for check.
                _EdgeSrc(_Edge, src), _EdgeDst(_Edge, dst), # Solely for message.
                not_(isnan(Float)), # To work around https://relationalai.atlassian.net/browse/RAI-40437
            ).define(
                Error.new(
                    message="Edge weights must not be negative.",
                    edge=_Edge, source=src, destination=dst, weight=Float,
                )
            )
        # If not weighted, no `Edge`s may have a `weight`:
        else: # not self.weighted:
            # Note that the message for this error is a bit lighter than
            # for the error where the user must, but did not, provide a weight,
            # as other argument validation more or less prevents this case from
            # occurring when the user provides their own concepts/relationships.
            src, dst = self.Node.ref(), self.Node.ref()
            where(
                _Edge, _EdgeWeight(_Edge, Float), # Necessary for check.
                _EdgeSrc(_Edge, src), _EdgeDst(_Edge, dst), # Solely for message.
            ).define(
                Error.new(
                    message=(
                        "In an unweighted graph, no edge (`Graph.Edge`) "
                        "may have a weight (`Graph.Edge.weight`)."
                    ),
                    edge=_Edge, source=src, destination=dst, weight=Float,
                )
            )

        # If the aggregator is None and the graph is directed,
        # no multi-edges are allowed; i.e., distinct edges
        # may not have the same source and destination.
        if self._aggregator is None and self.directed:
            edge_a, edge_b = _Edge.ref(), _Edge.ref()
            edge_a_src, edge_a_dst = self.Node.ref(), self.Node.ref()
            edge_b_src, edge_b_dst = self.Node.ref(), self.Node.ref()
            where(
                edge_a, edge_b,
                edge_a < edge_b, # implies edge_a != edge_b
                _EdgeSrc(edge_a, edge_a_src), _EdgeDst(edge_a, edge_a_dst),
                _EdgeSrc(edge_b, edge_b_src), _EdgeDst(edge_b, edge_b_dst),
                edge_a_src == edge_b_src, edge_a_dst == edge_b_dst,
            ).define(
                Error.new(
                    message=(
                        "Multi-edges are not allowed when `aggregator=None`. "
                        "(I.e., distinct edges may not have the same source and destination.)"
                    ),
                    edge_a=edge_a,
                    edge_b=edge_b,
                    common_source=edge_a_src,
                    common_destination=edge_a_dst,
                )
            )
        # If the aggregator is None and the graph is undirected,
        # no multi-edges (express or implied) are allowed; i.e.
        # 1) distinct edges may not have the same source and destination; and
        # 2) distinct edges may not have one node's source matching
        # the other node's destination and vice versa.
        elif self._aggregator is None and not self.directed:
            edge_a, edge_b = _Edge.ref(), _Edge.ref()
            edge_a_src, edge_a_dst = self.Node.ref(), self.Node.ref()
            edge_b_src, edge_b_dst = self.Node.ref(), self.Node.ref()
            where(
                edge_a, edge_b,
                edge_a < edge_b, # implies edge_a != edge_b
                _EdgeSrc(edge_a, edge_a_src), _EdgeDst(edge_a, edge_a_dst),
                _EdgeSrc(edge_b, edge_b_src), _EdgeDst(edge_b, edge_b_dst),
                where(edge_a_src == edge_b_src, edge_a_dst == edge_b_dst) |
                where(edge_a_src == edge_b_dst, edge_a_dst == edge_b_src)
            ).define(
                Error.new(
                    message=(
                        "Multi-edges are not allowed when `aggregator=None`. "
                        "(I.e., distinct edges may not have the same source and destination, "
                        "nor one node's source matching the other node's destination "
                        "and vice versa."
                    ),
                    edge_a=edge_a,
                    edge_b=edge_b,
                    edge_a_src=edge_a_src,
                    edge_b_src=edge_b_src,
                    edge_a_dst=edge_a_dst,
                    edge_b_dst=edge_b_dst,
                )
            )

        return _Edge, _EdgeSrc, _EdgeDst, _EdgeWeight


    @cached_property
    def _edge(self):
        """
        Lazily define and cache the `self._edge` relationship,
        consuming the `Edge` concept's `EdgeSrc` and `EdgeDst` relationships.
        """
        _edge_rel = self._model.Relationship(f"{{src:{self._NodeConceptStr}}} has edge to {{dst:{self._NodeConceptStr}}}")
        _edge_rel.annotate(annotations.track("graphs", "_edge"))

        Edge, EdgeSrc, EdgeDst = self.Edge, self.EdgeSrc, self.EdgeDst
        src, dst = self.Node.ref(), self.Node.ref()
        if self.directed:
            where(
                Edge, EdgeSrc(Edge, src), EdgeDst(Edge, dst)
            ).define(
                _edge_rel(src, dst)
            )
        elif not self.directed:
            where(
                Edge, EdgeSrc(Edge, src), EdgeDst(Edge, dst)
            ).define(
                _edge_rel(src, dst),
                _edge_rel(dst, src)
            )

        return _edge_rel

    @cached_property
    def _weight(self):
        """
        Lazily define and cache the `self._weight` relationship,
        consuming the `Edge` concept's `EdgeSrc`, `EdgeDst`, and `EdgeWeight` relationships.
        """
        _weight_rel = self._model.Relationship(f"{{src:{self._NodeConceptStr}}} has edge to {{dst:{self._NodeConceptStr}}} with weight {{weight:Float}}")
        _weight_rel.annotate(annotations.track("graphs", "_weight"))

        Edge, EdgeSrc, EdgeDst, EdgeWeight = self.Edge, self.EdgeSrc, self.EdgeDst, self.EdgeWeight
        src, dst, weight = self.Node.ref(), self.Node.ref(), Float.ref()
        if self.directed and self.weighted:
            if self._aggregator == "sum":
                # Sum-aggregate multi-edge weights per (src, dst).
                summed_weight = Float.ref()
                where(
                    summed_weight := \
                        sum(
                            Edge, weight
                        ).per(
                            src, dst
                        ).where(
                            Edge, EdgeSrc(Edge, src), EdgeDst(Edge, dst), EdgeWeight(Edge, weight)
                        )
                ).define(
                    _weight_rel(src, dst, summed_weight)
                )
            else: # No aggregation; simply enumerate weights.
                where(
                    Edge, EdgeSrc(Edge, src), EdgeDst(Edge, dst), EdgeWeight(Edge, weight)
                ).define(
                    _weight_rel(src, dst, weight)
                )
        elif self.directed and not self.weighted:
            where(
                Edge, EdgeSrc(Edge, src), EdgeDst(Edge, dst)
            ).define(
                _weight_rel(src, dst, 1.0)
            )
        elif not self.directed and self.weighted:
            if self._aggregator == "sum":
                # Canonicalize unordered pairs.
                a, b, w = self.Node.ref(), self.Node.ref(), Float.ref()
                canon_edge, canon_src, canon_dst, canon_weight = \
                    self.Edge.ref(), self.Node.ref(), self.Node.ref(), Float.ref()
                canon_edge, canon_src, canon_dst, canon_weight = union(
                    where(Edge, EdgeSrc(Edge, a), EdgeDst(Edge, b), EdgeWeight(Edge, w), a <= b).select(Edge, a, b, w),
                    where(Edge, EdgeSrc(Edge, a), EdgeDst(Edge, b), EdgeWeight(Edge, w), b < a).select(Edge, b, a, w),
                )
                # The above could be replaced with the following simpler/cleaner
                # version once support for minimum/maximum/friends over concepts lands:
                # canon_edge, canon_src, canon_dst, canon_weight = select(
                #     Edge, minimum(a, b), maximum(a, b), w
                # ).where(
                #     EdgeSrc(Edge, a), EdgeDst(Edge, b), EdgeWeight(Edge, w)
                # )

                # Sum weights per pair, then emit both orientations.
                summed_weight = Float.ref()
                where(
                    summed_weight := \
                        sum(
                            canon_edge, canon_weight
                        ).per(
                            canon_src, canon_dst
                        ).where(
                            canon_edge, canon_src, canon_dst, canon_weight
                        )
                ).define(
                    _weight_rel(canon_src, canon_dst, summed_weight),
                    _weight_rel(canon_dst, canon_src, summed_weight),
                )
            else: # No aggregation; enumerate and emit both orientations.
                where(
                    Edge, EdgeSrc(Edge, src), EdgeDst(Edge, dst), EdgeWeight(Edge, weight)
                ).define(
                    _weight_rel(src, dst, weight),
                    _weight_rel(dst, src, weight)
                )
        elif not self.directed and not self.weighted:
            where(
                Edge, EdgeSrc(Edge, src), EdgeDst(Edge, dst)
            ).define(
                _weight_rel(src, dst, 1.0),
                _weight_rel(dst, src, 1.0)
            )

        return _weight_rel


    # Begin Visualization ------------------------------------------------------

    def _fetch_for_visualization(self):
        """
        This method fetches (that is, collects client-side) all nodes, edges,
        and their public binary properties, for visualization. It caches that
        information in self._last_visualization_fetch for downstream use.
        """
        # `output`, cached in `self._last_visualization_fetch`, is
        # a nested dictionary. At the top level it contains
        # keys `nodes` and `edges` that map to dictionaries.
        #
        # The `nodes` dictionary contains a key for each node hash,
        # which maps to a dictionary. That dictionary contains a key for
        # each public binary property the node has a value for,
        # mapped to that value.
        #
        # The `edges` dictionary contains a key for each edge hash,
        # which maps to a dictionary. That dictionary contains a 'src'
        # key, which maps to the source node of the edge, and a 'dst'
        # key, which maps to the destination node of the edge. It also contains
        # a key for each public binary property the edge has a value for,
        # mapped to its value for that edge. This structure captures multiedges.
        #
        # TODO: When bandwidth allows, also need special handling for 'weight',
        #   in the case that the user provided a weight relationship that
        #   isn't a property of the edge concept.
        output = {
            "nodes": dict(),
            "edges": dict()
        }

        # Fetch all node hashes, and store in `output`.
        for (node_hash,) in select(self.Node):
            output["nodes"][node_hash] = {}

        # Fetch all public binary properties for those nodes, and store in `output`.
        node_properties = self.Node._relationships
        for prop_name, prop_relationship in node_properties.items():
            # Properties with names beginning with an underscore are private,
            # and should not be visualized; skip fetching them.
            if prop_name.startswith('_'):
                continue

            # Handle only binary properties; skip fetching all others.
            if len(prop_relationship._field_refs) != 2:
                continue

            # The property should have structure
            # `prop_relationship(node_var, prop_var)`;
            # construct a select query to retrieve all such two-tuples.
            node_var = self.Node.ref()
            prop_var = prop_relationship._field_refs[1].ref()
            prop_query = select(node_var, prop_var).where(prop_relationship(node_var, prop_var))

            # Wrap evaluation of the query into a try-except,
            # as the property may not be populated for all nodes,
            # or the query might otherwise fail; IOW this is best effort.
            try:
                for (node_hash, prop_value) in prop_query:
                    output["nodes"][node_hash][prop_name] = prop_value
            except Exception:
                continue # Best effort.

        # Fetch all edge hashes, sources, and destinations, and store in `output`.
        src, dst = self.Node.ref(), self.Node.ref()
        edges_query = \
            select(
                self.Edge, src, dst,
            ).where(
                self.EdgeSrc(self.Edge, src),
                self.EdgeDst(self.Edge, dst),
            )
        for (edge_hash, src_hash, dst_hash) in edges_query:
            output["edges"][edge_hash] = {
                "src": src_hash,
                "dst": dst_hash
            }

        # Fetch all public binary properties for those edges, and store in `output`.
        edge_properties = self.Edge._relationships
        for prop_name, prop_relationship in edge_properties.items():
            # Properties with names beginning with an underscore are private,
            # and should not be visualized; skip fetching them.
            if prop_name.startswith('_'):
                continue

            # Handle only binary properties; skip fetching all others.
            if len(prop_relationship._field_refs) != 2:
                continue

            # The source and destination for each edge were extracted above.
            # If the source and destination relationships also happen to be
            # properties of the edge concept, they should not be visualized;
            # skip fetching them.
            if prop_relationship is self.EdgeSrc or prop_relationship is self.EdgeDst:
                continue

            # The property should have structure
            # `prop_relationship(edge_var, prop_var)`;
            # construct a select query to retrieve all such two-tuples.
            edge_var = self.Edge.ref()
            prop_var = prop_relationship._field_refs[1].ref()
            prop_query = select(edge_var, prop_var).where(prop_relationship(edge_var, prop_var))

            # Wrap evaluation of the query into a try-except,
            # as the property may not be populated for all nodes,
            # or the query might otherwise fail; IOW this is best effort.
            try:
                for (edge_hash, prop_value) in prop_query:
                    output["edges"][edge_hash][prop_name] = prop_value
            except Exception:
                continue # Best effort.

        self._last_visualization_fetch = output
        return output


    # Helper for the _build_gJGF_dictionary method below.
    def _props_to_gJGF_metadata(self, style_props, node_or_edge_props_copy):
        """
        This method takes a copy of a set of node or edge properties, and
        a set of gravis style directives, and combines them into gJGF metadata
        for nodes and edges.
        """
        # Given this method receives a copy, it can be mutated and returned.
        metadata = node_or_edge_props_copy

        # Apparently values for style properties can be callables,
        # in which case the right thing to do is to add the style
        # property's key to the metadata, populating its value
        # with the application of the callable to the full metadata.
        for style_prop_key, style_prop_value in style_props.items():
            if callable(style_prop_value):
                metadata[style_prop_key] = style_prop_value(metadata)

        # Some property value types aren't supported by JSON;
        # convert them appropriately here.
        for prop_key, prop_value in metadata.items():
            # Decimals are not supported, convert to floats.
            if isinstance(prop_value, Decimal):
                metadata[prop_key] = float(prop_value)
            # NumPy integers are not supported, convert to ints.
            if isinstance(prop_value, numpy.integer):
                metadata[prop_key] = int(prop_value)

        # For some reason, the existence of "id" in the metadata
        # results in edges not getting displayed in the visualization,
        # so we remove it.
        if "id" in metadata:
            del metadata["id"]

        return metadata


    def _build_gJGF_dictionary(
            self,
            graph_data: dict,
            user_style: Optional[dict] = None,
        ) -> dict:
        """
        From graph data in the format produced by `_fetch_visualization_data`,
        and any user-provided gravis style directives, build a gJGF (i.e.,
        "graph in JSON Graph Format") representation of the graph and styling,
        as a dictionary. (gJGF is the format used by the gravis library.)
        """

        # Define default visual properties for nodes and edges.
        default_visual_properties = {
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

        # If the user provided gravis styling directives, merge them into
        # the default style, with user directives winning collisions.
        merged_style = default_visual_properties
        if user_style:
            for category in ["node", "edge"]:
                for style_prop_key, style_prop_value in user_style.get(category, {}).items():
                    if not callable(style_prop_value):
                        merged_style[category][style_prop_key] = style_prop_value

        # merged_style is a nested dictionary structure. At the top level,
        # it maps "node" and "edge" keys to values that are dictionaries.
        # Those dictionary values map style property keys to style property values.
        #
        # Here we build a flattened form of that dictionary. Specifically,
        # the top-level "node" and "edge" keys are flattened away, pushed
        # into prefixes on the style property keys in the corresponding
        # original value dictionaries. E.g., merged_style["node"]["style_prop"]
        # becomes flat_style["node_style_prop"].
        #
        # There is one wrinkle: the "arrow" properties are special and need to be
        # handled differently. Specifically, we do not want to add the "node"
        # or "edge" prefixes to them.
        _prefix_exclusion_map = {
            "arrow_size": "arrow_size",
            "arrow_color": "arrow_color",
        }
        flat_style = {}
        for prefix, style_props in merged_style.items():
            for style_prop_key, style_prop_value in style_props.items():
                if style_prop_key in _prefix_exclusion_map:
                    new_style_prop_key = _prefix_exclusion_map[style_prop_key]
                else:
                    new_style_prop_key = f"{prefix}_{style_prop_key}"
                flat_style[new_style_prop_key] = style_prop_value

        # Finally build and return the gJGF dictionary.
        return {
            "graph": {
                "directed": self.directed,
                "metadata": flat_style,
                "nodes": {
                    node_hash: {
                        **({"label": str(node_props["label"])} if "label" in node_props else {}),
                        "metadata": self._props_to_gJGF_metadata(
                            merged_style["node"],
                            node_props.copy()
                        ),
                    }
                    for (node_hash, node_props) in graph_data["nodes"].items()
                },
                "edges": [
                    {
                        "source": edge_props["src"],
                        "target": edge_props["dst"],
                        "metadata": self._props_to_gJGF_metadata(
                            merged_style["edge"],
                            # Exclude the source and destination from
                            # the properties sent through as metadata.
                            {k: v for k, v in edge_props.items() if k not in ("src", "dst")}
                        )
                    }
                    for (edge_hash, edge_props) in graph_data["edges"].items()
                ],
            }
        }


    def visualize(
            self,
            gravis_style=None,
            use_fetch_cache=False,
            use_gravis_three=False,
            **user_kwargs_for_gravis,
        ):
        """
        Visualize the graph with `gravis`.

        Set the `gravis_style` keyword argument, a dictionary containing
        gravis styling directives for nodes and edges, to customize
        the appearance of the graph.

        By default, this method will fetch all necessary (node, edge, and
        node/edge property) data and cache it locally. To use the most
        recently cached data instead of fetching fresh data, set
        the `use_fetch_cache` argument to `True`; this is useful
        to tighten the iteration loop when customizing the visualization.

        By default, this method uses the `gravis.vis(...)` method for visualization.
        `vis` builds an interactive, two-dimensional graph view using `vis.js`
        (DOM/canvas). This method is simple and lightweight, but lacks some
        styling features (e.g., separate arrow colors and per-element opacity),
        so those options are ignored. Alternatively, set the `use_gravis_three`
        argument to `True` to use `gravis.three(...)`, which builds an interactive,
        three-dimensional graph view using `3d-force-graph`, which in turn uses
        `three.js`/WebGL. You get a draggable three-dimensional scene with
        force-layout physics; some features (e.g., node borders, edge labels)
        aren’t available compared to other back-ends.

        Any other keyword arguments will be passed through to `gravis`, merged
        with the following default keyword arguments.
        ```
            "node_label_data_source": "label",
            "edge_label_data_source": "label",
            "show_edge_label": True,
            "edge_curvature": 0.4,
        ```
        Colliding keyword arguments will override these defaults.

        TODO: Clean up / format-normalize this docstring at some point.
        """
        # TODO: The present implementation is woefully poorly exercised,
        #   to be improved when bandwidth allows.

        # Confirm necessary conditions for visualization support in Snowbook environments,
        # and bail if those conditions are not met.
        from v0.relationalai.environments import runtime_env, SnowbookEnvironment
        if isinstance(runtime_env, SnowbookEnvironment) and runtime_env.runner != "container":
            from v0.relationalai.errors import UnsupportedVisualizationError
            raise UnsupportedVisualizationError()

        # By default, freshly fetch all necessary node, edge, and
        # node/edge property data (and cache it locally). If the user
        # specified `use_fetch_cache`, use the most recently cached data
        # instead of fetching fresh data.
        graph_data = self._last_visualization_fetch if use_fetch_cache else None
        if not graph_data:
            graph_data = self._fetch_for_visualization()

        # From the fetched graph data any user-provided style directives
        # (via `gravis_style`), build a gJGF ("graph in JSON Graph Format",
        # the format that gravis understands) dictionary describing
        # the graph and how to style/visualize it.
        gJGF_dictionary = self._build_gJGF_dictionary(
            graph_data=graph_data,
            user_style=gravis_style,
        )

        # If the user provided additional keyword arguments to pass through
        # to gravis, merge those with the following default keyword arguments.
        # (The user's keyword arguments win collisions.)
        kwargs_for_gravis = {
            "node_label_data_source": "label",
            "edge_label_data_source": "label",
            "show_edge_label": True,
            "edge_curvature": 0.4,
        } | user_kwargs_for_gravis

        # By default, visualize with `gravis.vis`. If the user specified
        # `use_gravis_three`, visualize with `gravis.three` instead.
        gravis_method = gravis.vis if not use_gravis_three else gravis.three

        # Finally call gravis.
        gravis_rendering = gravis_method(
            gJGF_dictionary,
            **kwargs_for_gravis
        )

        return gravis_rendering

    # End Visualization --------------------------------------------------------

    # The following three helper methods validate
    # `from_`, `to`, and `between`
    # parameters to public methods that accept them.

    def _validate_domain_constraint_parameters(
            self,
            method_name: str,
            symmetric: bool,
            full: Optional[bool],
            from_: Optional[Relationship],
            to: Optional[Relationship],
            between: Optional[Relationship],
        ):
        """
        Validate the domain constraint parameters for methods that accept
        `full`, `from_`, `to`, and `between` parameters.

        Parameters
        ----------
        method_name : str
            The name of the method being validated (for error messages).
        symmetric : bool
            Whether the relationship is symmetric in its first two positions.
            If True, enforces that 'to' can only be used with 'from_' (since
            'to' alone would be redundant for symmetric relations).
            If False, allows 'to' without 'from_' (for asymmetric relations).
        full : bool, optional
            The full parameter value.
        from_ : Relationship, optional
            The from_ parameter value.
        to : Relationship, optional
            The to parameter value.
        between : Relationship, optional
            The between parameter value.

        Raises
        ------
        ValueError
            If parameter combinations are invalid.
        """
        # Confirm that `full` was not provided with any other parameter.
        if (
            full is not None
            and (
                from_ is not None or
                to is not None or
                between is not None
            )
        ):
            raise ValueError(
                "The 'full' parameter is mutually exclusive with 'from_', 'to', and 'between'. "
                f"Use 'full=True' to compute {method_name} for all node pairs, "
                "or use 'from_'/'to'/'between' to constrain computation to "
                "specific nodes or pairs."
            )

        # Confirm that `between` was not provided with any other parameter.
        if (between is not None
            and (
                from_ is not None or
                to is not None
                # `full` is implied by the preceding check.
            )
        ):
            raise ValueError(
                "The 'between' parameter is mutually exclusive with 'from_' and 'to'. "
                "Use 'between' to constrain computation to specific node pairs, "
                "or use 'from_'/'to' to constrain by position."
            )

        # Confirm that 'to' is only used with 'from_' for symmetric relations.
        # For asymmetric relations, 'to' without 'from_' is meaningful.
        if symmetric and to is not None and from_ is None:
            raise ValueError(
                "The 'to' parameter can only be used together with the 'from_' parameter. "
                f"The 'from_' parameter constrains the first position in {method_name} tuples, "
                f"while 'to' constrains the second position. Since {method_name} is symmetric "
                "in its first two positions, 'to' without 'from_' would be functionally redundant. "
                "Please either provide both 'from_' and 'to' parameters, or only 'from_'."
            )

        # If no parameters are provided, raise an exception
        # to avoid unintentional, potentially expensive full computation.
        if (
            full is None and
            from_ is None and
            to is None and
            between is None
        ):
            raise ValueError(
                f"Computing {method_name} for all pairs of nodes can be expensive. "
                f"To compute the full {method_name} relationship, "
                f"please call `{method_name}(full=True)`. To constrain computation to specific nodes, "
                f"please use `{method_name}(from_=node_subset)`, "
                f"`{method_name}(from_=node_subset_a, to=node_subset_b)`, "
                f"or `{method_name}(between=node_pairs)`."
            )

        # Validate that full is True (not just not None).
        # This check is only reached if full is not None
        # and no other parameters are provided.
        if full is not None and full is not True:
            raise ValueError(
                f"Invalid value (`{full}`) for 'full' parameter. Use `full=True` "
                f"to compute the full {method_name} relationship, or use 'from_', "
                "'from_' and 'to', or 'between' to constrain computation."
            )

    def _validate_node_subset_parameter(
            self,
            parameter_name: str,
            node_subset_relation: Relationship,
        ):
        """
        Validate that a parameter identifying a subset of nodes of interest is
        is a unary relationship, of nodes, attached to the same model
        that the graph is attached to.
        """
        # Validate that the parameter is a relationship.
        assert isinstance(node_subset_relation, Relationship), (
            f"The '{parameter_name}' parameter must be a `Relationship`, "
            f"but is a `{type(node_subset_relation).__name__}`."
        )

        # Validate that the relationship is attached to the same model as the graph.
        assert node_subset_relation._model is self._model, (
            f"The given '{parameter_name}' relationship must "
            "be attached to the same model as the graph."
        )

        # Validate that it's a unary relationship (has exactly one field).
        assert len(node_subset_relation._fields) == 1, (
            f"The '{parameter_name}' parameter must be a unary relationship, "
            f"but it has {len(node_subset_relation._fields)} fields."
        )

        # Validate that the concept type matches the graph's Node concept.
        assert node_subset_relation._fields[0].type_str == self.Node._name, (
            f"The '{parameter_name}' relationship must be over "
            f"the graph's Node concept ('{self.Node._name}'), "
            f"but is over '{node_subset_relation._fields[0].type_str}'."
        )

    # No parameter name at this time, as pertains only to `between` for now.
    def _validate_pair_subset_parameter(self, pairs_relation):
        """
        Validate that a parameter identifying pairs of nodes of interest is
        a binary relationship, of pairs of nodes, attached to the same model
        that the graph is attached to.
        """
        # Validate that the parameter is a relationship.
        assert isinstance(pairs_relation, Relationship), (
            "The 'between' parameter must be a `Relationship`, "
            f"but is a `{type(pairs_relation).__name__}`."
        )

        # Validate that the relationship is attached to the same model as the graph.
        assert pairs_relation._model is self._model, (
            "The given 'between' relationship must be "
            "attached to the same model as the graph."
        )

        # Validate that it's a binary relationship (has exactly two fields).
        assert len(pairs_relation._fields) == 2, (
            "The 'between' parameter must be a binary relationship, "
            f"but it has {len(pairs_relation._fields)} fields."
        )

        # Validate that both fields are typed as the graph's Node concept.
        assert pairs_relation._fields[0].type_str == self.Node._name, (
            "The 'between' relationship's first field must be "
            f"the graph's Node concept ('{self.Node._name}'), "
            f"but is '{pairs_relation._fields[0].type_str}'."
        )
        assert pairs_relation._fields[1].type_str == self.Node._name, (
            f"The 'between' relationship's second field must be "
            f"the graph's Node concept ('{self.Node._name}'), "
            f"but is '{pairs_relation._fields[1].type_str}'."
        )


    # The following three `_count_[in,out]neighbor` relationships are
    # primarily for internal consumption. They differ from corresponding
    # `_[in,out]degree` relationships in that they yield empty
    # rather than zero absent [in,out]neighbors.

    @cached_property
    def _count_neighbor(self):
        """Lazily define and cache the self._count_neighbor relationship."""
        return self._create_count_neighbor_relationship(node_subset=None)

    def _count_neighbor_of(self, node_subset: Relationship):
        """
        Create a _count_neighbor relationship constrained to the subset of nodes
        in `node_subset`. Note this relationship is not cached; it is
        specific to the callsite.
        """
        return self._create_count_neighbor_relationship(node_subset=node_subset)

    def _create_count_neighbor_relationship(self, *, node_subset: Optional[Relationship]):
        _count_neighbor_rel = self._model.Relationship(f"{{src:{self._NodeConceptStr}}} has neighbor count {{count:Integer}}")

        # Choose the appropriate neighbor relationship based on whether we have constraints
        if node_subset is None:
            # No constraint - use cached neighbor relationship
            neighbor_rel = self._neighbor
        else:
            # Constrained to nodes in the subset - use constrained neighbor relationship
            neighbor_rel = self._neighbor_of(node_subset)

        # Apply the same counting logic for both cases
        src, dst = self.Node.ref(), self.Node.ref()
        where(neighbor_rel(src, dst)).define(_count_neighbor_rel(src, count(dst).per(src)))

        return _count_neighbor_rel

    @cached_property
    def _count_inneighbor(self):
        """Lazily define and cache the self._count_inneighbor relationship."""
        return self._create_count_inneighbor_relationship(node_subset=None)

    def _count_inneighbor_of(self, node_subset: Relationship):
        """
        Create a _count_inneighbor relationship constrained to the subset of nodes
        in `node_subset`. Note this relationship is not cached; it is
        specific to the callsite.
        """
        return self._create_count_inneighbor_relationship(node_subset=node_subset)

    def _create_count_inneighbor_relationship(self, *, node_subset: Optional[Relationship]):
        _count_inneighbor_rel = self._model.Relationship(f"{{dst:{self._NodeConceptStr}}} has inneighbor count {{count:Integer}}")

        # Choose the appropriate inneighbor relationship based on whether we have constraints
        if node_subset is None:
            # No constraint - use cached inneighbor relationship
            inneighbor_rel = self._inneighbor
        else:
            # Constrained to nodes in the subset - use constrained inneighbor relationship
            inneighbor_rel = self._inneighbor_of(node_subset)

        # Apply the same counting logic for both cases
        dst, src = self.Node.ref(), self.Node.ref()
        where(inneighbor_rel(dst, src)).define(_count_inneighbor_rel(dst, count(src).per(dst)))

        return _count_inneighbor_rel

    @cached_property
    def _count_outneighbor(self):
        """Lazily define and cache the self._count_outneighbor relationship."""
        return self._create_count_outneighbor_relationship(node_subset=None)

    def _count_outneighbor_of(self, node_subset: Relationship):
        """
        Create a _count_outneighbor relationship constrained to the subset of nodes
        in `node_subset`. Note this relationship is not cached; it is
        specific to the callsite.
        """
        return self._create_count_outneighbor_relationship(node_subset=node_subset)

    def _create_count_outneighbor_relationship(self, *, node_subset: Optional[Relationship]):
        _count_outneighbor_rel = self._model.Relationship(f"{{src:{self._NodeConceptStr}}} has outneighbor count {{count:Integer}}")

        # Choose the appropriate outneighbor relationship based on whether we have constraints
        if node_subset is None:
            # No constraint - use cached outneighbor relationship
            outneighbor_rel = self._outneighbor
        else:
            # Constrained to nodes in the subset - use constrained outneighbor relationship
            outneighbor_rel = self._outneighbor_of(node_subset)

        # Apply the same counting logic for both cases
        src, dst = self.Node.ref(), self.Node.ref()
        where(outneighbor_rel(src, dst)).define(_count_outneighbor_rel(src, count(dst).per(src)))

        return _count_outneighbor_rel


    # The following fragments are primarily for internal consumption,
    # presently in use by the `cosine_similarity` and
    # `jaccard_similarity` relationships.

    def _wu_dot_wv_fragment(self, node_u, node_v):
        """
        Helper for cosine_similarity that returns a fragment that produces an
        un-normalized inner product between the outneighbor vectors of given
        nodes `node_u` and `node_v`.
        """
        node_k, wu, wv = self.Node.ref(), Float.ref(), Float.ref()
        return (
            sum(node_k, wu * wv)
            .per(node_u, node_v)
            .where(
                self._weight(node_u, node_k, wu),
                self._weight(node_v, node_k, wv),
            )
        )


    @include_in_docs
    def num_nodes(self) -> Relationship:
        """Returns a unary relationship containing the number of nodes in the graph.

        Returns
        -------
        Relationship
            A unary relationship containing the number of nodes in the graph.

        Relationship Schema
        -------------------
        ``num_nodes(count)``

        * **count** (*Integer*): The number of nodes in the graph.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                |
        | :--------- | :-------- | :------------------- |
        | Undirected | Yes       |                      |
        | Directed   | Yes       |                      |
        | Weighted   | Yes       | Weights are ignored. |

        Examples
        --------
        >>> from relationalai.semantics import Model, define
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up the graph and concepts
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define some nodes
        >>> node1, node2, node3, node4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(node1, node2, node3, node4)
        >>>
        >>> # 3. Define the full set of edges
        >>> define(
        ...     Edge.new(src=node1, dst=node2),
        ...     Edge.new(src=node2, dst=node3),
        ...     Edge.new(src=node3, dst=node3),
        ...     Edge.new(src=node2, dst=node4),
        ... )
        >>>
        >>> # 4. The relationship contains the number of nodes
        >>> graph.num_nodes().inspect()
        ▰▰▰▰ Setup complete
           int
        0    4

        See Also
        --------
        num_edges

        """
        return self._num_nodes

    @cached_property
    def _num_nodes(self):
        """Lazily define and cache the self._num_nodes relationship."""
        _num_nodes_rel = self._model.Relationship("The graph has {num_nodes:Integer} nodes")
        _num_nodes_rel.annotate(annotations.track("graphs", "num_nodes"))

        define(_num_nodes_rel(count(self.Node) | 0))
        return _num_nodes_rel


    @include_in_docs
    def num_edges(self):
        """Returns a unary relationship containing the number of edges in the graph.

        Returns
        -------
        Relationship
            A unary relationship containing the number of edges in the graph.

        Relationship Schema
        -------------------
        ``num_edges(count)``

        * **count** (*Integer*): The number of edges in the graph.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                |
        | :--------- | :-------- | :------------------- |
        | Undirected | Yes       |                      |
        | Directed   | Yes       |                      |
        | Weighted   | Yes       | Weights are ignored. |

        Examples
        --------
        >>> from relationalai.semantics import Model, define
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up the graph and concepts
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define some nodes
        >>> node1, node2, node3, node4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(node1, node2, node3, node4)
        >>>
        >>> # 3. Define the edges
        >>> define(
        ...     Edge.new(src=node1, dst=node2),
        ...     Edge.new(src=node2, dst=node3),
        ...     Edge.new(src=node3, dst=node3),
        ...     Edge.new(src=node2, dst=node4),
        ... )
        >>>
        >>> # 4. The relationship contains the number of edges
        >>> graph.num_edges().inspect()
        ▰▰▰▰ Setup complete
           int
        0    4

        See Also
        --------
        num_nodes

        """
        return self._num_edges

    @cached_property
    def _num_edges(self):
        """Lazily define and cache the self._num_edges relationship."""
        _num_edges_rel = self._model.Relationship("The graph has {num_edges:Integer} edges")
        _num_edges_rel.annotate(annotations.track("graphs", "num_edges"))

        src, dst = self.Node.ref(), self.Node.ref()
        if self.directed:
            define(_num_edges_rel(count(src, dst, self._edge(src, dst)) | 0))
        elif not self.directed:
            define(_num_edges_rel(count(src, dst, self._edge(src, dst), src <= dst) | 0))

        return _num_edges_rel


    @include_in_docs
    def neighbor(self, *, of: Optional[Relationship] = None):
        """Returns a binary relationship containing all neighbor pairs in the graph.

        For directed graphs, a node's neighbors include both its in-neighbors
        and out-neighbors.

        Parameters
        ----------
        of : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the domain of the neighbor computation: only
            neighbors of nodes in this relationship are computed and returned.

        Returns
        -------
        Relationship
            A binary relationship where each tuple represents a node and one
            of its neighbors.

        Relationship Schema
        -------------------
        ``neighbor(node, neighbor_node)``

        * **node** (*Node*): A node in the graph.
        * **neighbor_node** (*Node*): A neighbor of the node.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                                           |
        | :--------- | :-------- | :---------------------------------------------- |
        | Undirected | Yes       |                                                 |
        | Directed   | Yes       | Same as the union of `inneighbor` and `outneighbor`. |
        | Weighted   | Yes       | Weights are ignored.                            |

        Examples
        --------
        >>> from relationalai.semantics import Model, define, select, where
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n2, dst=n4),
        ... )
        >>>
        >>> # 3. Select the IDs from the neighbor relationship and inspect
        >>> u, v = Node.ref("u"), Node.ref("v")
        >>> neighbor = graph.neighbor()
        >>> select(u.id, v.id).where(neighbor(u, v)).inspect()
        ▰▰▰▰ Setup complete
        id  id2
        0   1    2
        1   2    1
        2   2    3
        3   2    4
        4   3    2
        5   3    3
        6   4    2

        >>> # 4. Use 'of' parameter to constrain the set of nodes to compute neighbors of
        >>> # Define a subset containing only nodes 2 and 3
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(union(node.id == 2, node.id == 3)).define(subset(node))
        >>>
        >>> # Get neighbors only of nodes in the subset
        >>> constrained_neighbor = graph.neighbor(of=subset)
        >>> select(u.id, v.id).where(constrained_neighbor(u, v)).inspect()
        ▰▰▰▰ Setup complete
        id  id2
        0   2    1
        1   2    3
        2   2    4
        3   3    2
        4   3    3

        Notes
        -----
        The ``neighbor()`` method, called with no parameters, computes and caches
        the full neighbor relationship, providing efficient reuse across multiple
        calls to ``neighbor()``. In contrast, ``neighbor(of=subset)`` computes a
        constrained relationship specific to the passed-in ``subset`` and that
        call site. When a significant fraction of the neighbor relation is needed
        across a program, ``neighbor()`` is typically more efficient; this is the
        typical case. Use ``neighbor(of=subset)`` only when small subsets of the
        neighbor relationship are needed collectively across the program.

        See Also
        --------
        inneighbor
        outneighbor

        """
        if of is None:
            return self._neighbor
        else:
            # Validate the 'of' parameter
            self._validate_node_subset_parameter('of', of)
            return self._neighbor_of(of)

    @cached_property
    def _neighbor(self):
        """Lazily define and cache the self._neighbor relationship."""
        _neighbor_rel = self._create_neighbor_relationship(node_subset=None)
        _neighbor_rel.annotate(annotations.track("graphs", "neighbor"))
        return _neighbor_rel

    def _neighbor_of(self, node_subset: Relationship):
        """
        Create a neighbor relationship constrained to the subset of nodes
        in `node_subset`. Note this relationship is not cached; it is
        specific to the callsite.
        """
        _neighbor_rel = self._create_neighbor_relationship(node_subset=node_subset)
        _neighbor_rel.annotate(annotations.track("graphs", "neighbor_of"))
        return _neighbor_rel

    def _create_neighbor_relationship(self, *, node_subset: Optional[Relationship]):
        _neighbor_rel = self._model.Relationship(f"{{src:{self._NodeConceptStr}}} has neighbor {{dst:{self._NodeConceptStr}}}")
        src, dst = self.Node.ref(), self.Node.ref()

        if self.directed:
            # If the graph is directed, the _edge relation is not symmetric,
            # requiring separate rules to capture out-neighbors and in-neighbors.
            #
            # Capture out-neighbors.
            where(
                self._edge(src, dst),
                *([node_subset(src)] if node_subset else [])
            ).define(
                _neighbor_rel(src, dst)
            )
            # Capture in-neighbors.
            where(
                self._edge(src, dst),
                *([node_subset(dst)] if node_subset else [])
            ).define(
                _neighbor_rel(dst, src)
            )
        elif not self.directed:
            # If the graph is undirected, the _edge relation is symmetric,
            # so a single rule suffices to capture all neighbors.
            where(
                self._edge(src, dst),
                *([node_subset(src)] if node_subset else [])
            ).define(
                _neighbor_rel(src, dst)
            )

        return _neighbor_rel


    @include_in_docs
    def inneighbor(self, *, of: Optional[Relationship] = None):
        """Returns a binary relationship of all nodes and their in-neighbors.

        An in-neighbor of a node `u` is any node `v` where an edge from `v`
        to `u` exists. For undirected graphs, this is identical to `neighbor`.

        Parameters
        ----------
        of : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the domain of the inneighbor computation: only
            in-neighbors of nodes in this relationship are computed and returned.

        Returns
        -------
        Relationship
            A binary relationship where each tuple represents a destination node
            and one of its in-neighbors.

        Relationship Schema
        -------------------
        ``inneighbor(node, inneighbor_node)``

        * **node** (*Node*): The destination node.
        * **inneighbor_node** (*Node*): The in-neighbor of the node (i.e., the source of an incoming edge).

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes               |
        | :--------- | :-------- | :------------------ |
        | Undirected | Yes       | Same as `neighbor`. |
        | Directed   | Yes       |                     |
        | Weighted   | Yes       | Weights are ignored.|

        Examples
        --------
        >>> from relationalai.semantics import Model, define, select, where
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a directed graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n2, dst=n4),
        ... )
        >>>
        >>> # 3. Select the IDs from the in-neighbor relationship and inspect
        >>> node, inneighbor_node = Node.ref("node"), Node.ref("inneighbor_node")
        >>> inneighbor = graph.inneighbor()
        >>> select(
        ...     node.id,
        ...     inneighbor_node.id
        ... ).where(
        ...     inneighbor(node, inneighbor_node)
        ... ).inspect()
        ▰▰▰▰ Setup complete
        id  id2
        0   2    1
        1   3    2
        2   3    3
        3   4    2

        >>> # 4. Use 'of' parameter to constrain the set of nodes to compute in-neighbors of
        >>> # Define a subset containing only nodes 2 and 3
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(union(node.id == 2, node.id == 3)).define(subset(node))
        >>>
        >>> # Get in-neighbors only of nodes in the subset
        >>> constrained_inneighbor = graph.inneighbor(of=subset)
        >>> select(node.id, inneighbor_node.id).where(constrained_inneighbor(node, inneighbor_node)).inspect()
        ▰▰▰▰ Setup complete
        id  id2
        0   2    1
        1   3    2
        2   3    3

        Notes
        -----
        The ``inneighbor()`` method, called with no parameters, computes and caches
        the full inneighbor relationship, providing efficient reuse across multiple
        calls to ``inneighbor()``. In contrast, ``inneighbor(of=subset)`` computes a
        constrained relationship specific to the passed-in ``subset`` and that
        call site. When a significant fraction of the inneighbor relation is needed
        across a program, ``inneighbor()`` is typically more efficient; this is the
        typical case. Use ``inneighbor(of=subset)`` only when small subsets of the
        inneighbor relationship are needed collectively across the program.

        See Also
        --------
        neighbor
        outneighbor

        """
        if of is None:
            return self._inneighbor
        else:
            # Validate the 'of' parameter
            self._validate_node_subset_parameter('of', of)
            return self._inneighbor_of(of)

    @cached_property
    def _inneighbor(self):
        """Lazily define and cache the self._inneighbor relationship."""
        _inneighbor_rel = self._create_inneighbor_relationship(node_subset=None)
        _inneighbor_rel.annotate(annotations.track("graphs", "inneighbor"))
        return _inneighbor_rel

    def _inneighbor_of(self, node_subset: Relationship):
        """
        Create an inneighbor relationship constrained to the subset of nodes
        in `node_subset`. Note this relationship is not cached; it is
        specific to the callsite.
        """
        _inneighbor_rel = self._create_inneighbor_relationship(node_subset=node_subset)
        _inneighbor_rel.annotate(annotations.track("graphs", "inneighbor_of"))
        return _inneighbor_rel

    def _create_inneighbor_relationship(self, *, node_subset: Optional[Relationship]):
        _inneighbor_rel = self._model.Relationship(f"{{dst:{self._NodeConceptStr}}} has inneighbor {{src:{self._NodeConceptStr}}}")
        src, dst = self.Node.ref(), self.Node.ref()

        if self.directed:
            # For directed graphs, in-neighbors are simply source nodes that
            # have an edge to the destination nodes in our subset.
            where(
                self._edge(src, dst),
                *([node_subset(dst)] if node_subset else [])
            ).define(
                _inneighbor_rel(dst, src)
            )
        elif not self.directed:
            # For undirected graphs, the _edge relation is symmetric,
            # so neighbors and in-neighbors are the same.
            where(
                self._edge(src, dst),
                *([node_subset(dst)] if node_subset else [])
            ).define(
                _inneighbor_rel(dst, src)
            )
            # TODO: This likely isn't the most efficient way to formulate
            #   this logic, but it's good enough for now.

        return _inneighbor_rel


    @include_in_docs
    def outneighbor(self, *, of: Optional[Relationship] = None):
        """Returns a binary relationship of all nodes and their out-neighbors.

        An out-neighbor of a node `u` is any node `v` where an edge from `u`
        to `v` exists. For undirected graphs, this is identical to `neighbor`.

        Parameters
        ----------
        of : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the domain of the outneighbor computation: only
            out-neighbors of nodes in this relationship are computed and returned.

        Returns
        -------
        Relationship
            A binary relationship where each tuple represents a source node
            and one of its out-neighbors.

        Relationship Schema
        -------------------
        ``outneighbor(node, outneighbor_node)``

        * **node** (*Node*): The source node.
        * **outneighbor_node** (*Node*): The out-neighbor of the node (i.e., the destination of an outgoing edge).

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes               |
        | :--------- | :-------- | :------------------ |
        | Undirected | Yes       | Same as `neighbor`. |
        | Directed   | Yes       |                     |
        | Weighted   | Yes       | Weights are ignored.|

        Examples
        --------
        >>> from relationalai.semantics import Model, define, select, where
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a directed graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n2, dst=n4)
        ... )
        >>>
        >>> # 3. Select the IDs from the out-neighbor relationship and inspect
        >>> node, outneighbor_node = Node.ref("node"), Node.ref("outneighbor_node")
        >>> outneighbor = graph.outneighbor()
        >>> select(
        ...     node.id,
        ...     outneighbor_node.id
        ... ).where(
        ...     outneighbor(node, outneighbor_node)
        ... ).inspect()
        ▰▰▰▰ Setup complete
        id  id2
        0   1    2
        1   2    3
        2   2    4
        3   3    3

        >>> # 4. Use 'of' parameter to constrain the set of nodes to compute out-neighbors of
        >>> # Define a subset containing only nodes 2 and 3
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(union(node.id == 2, node.id == 3)).define(subset(node))
        >>>
        >>> # Get out-neighbors only of nodes in the subset
        >>> constrained_outneighbor = graph.outneighbor(of=subset)
        >>> select(node.id, outneighbor_node.id).where(constrained_outneighbor(node, outneighbor_node)).inspect()
        ▰▰▰▰ Setup complete
        id  id2
        0   2    3
        1   2    4
        2   3    3

        Notes
        -----
        The ``outneighbor()`` method, called with no parameters, computes and caches
        the full outneighbor relationship, providing efficient reuse across multiple
        calls to ``outneighbor()``. In contrast, ``outneighbor(of=subset)`` computes a
        constrained relationship specific to the passed-in ``subset`` and that
        call site. When a significant fraction of the outneighbor relation is needed
        across a program, ``outneighbor()`` is typically more efficient; this is the
        typical case. Use ``outneighbor(of=subset)`` only when small subsets of the
        outneighbor relationship are needed collectively across the program.

        See Also
        --------
        neighbor
        inneighbor

        """
        if of is None:
            return self._outneighbor
        else:
            # Validate the 'of' parameter
            self._validate_node_subset_parameter('of', of)
            return self._outneighbor_of(of)

    @cached_property
    def _outneighbor(self):
        """Lazily define and cache the self._outneighbor relationship."""
        _outneighbor_rel = self._create_outneighbor_relationship(node_subset=None)
        _outneighbor_rel.annotate(annotations.track("graphs", "outneighbor"))
        return _outneighbor_rel

    def _outneighbor_of(self, node_subset: Relationship):
        """
        Create an outneighbor relationship constrained to the subset of nodes
        in `node_subset`. Note this relationship is not cached; it is
        specific to the callsite.
        """
        _outneighbor_rel = self._create_outneighbor_relationship(node_subset=node_subset)
        _outneighbor_rel.annotate(annotations.track("graphs", "outneighbor_of"))
        return _outneighbor_rel

    def _create_outneighbor_relationship(self, *, node_subset: Optional[Relationship]):
        _outneighbor_rel = self._model.Relationship(f"{{src:{self._NodeConceptStr}}} has outneighbor {{dst:{self._NodeConceptStr}}}")
        src, dst = self.Node.ref(), self.Node.ref()

        if self.directed:
            # For directed graphs, out-neighbors are simply destination nodes that
            # have an edge from the source nodes in our subset.
            where(
                self._edge(src, dst),
                *([node_subset(src)] if node_subset else [])
            ).define(
                _outneighbor_rel(src, dst)
            )
        elif not self.directed:
            # For undirected graphs, the _edge relation is symmetric,
            # so neighbors and out-neighbors are the same.
            where(
                self._edge(src, dst),
                *([node_subset(src)] if node_subset else [])
            ).define(
                _outneighbor_rel(src, dst)
            )

        return _outneighbor_rel


    @include_in_docs
    def common_neighbor(self,
            *,
            full: Optional[bool] = None,
            from_: Optional[Relationship] = None,
            to: Optional[Relationship] = None,
            between: Optional[Relationship] = None,
        ):
        """Returns a ternary relationship of common neighbor triplets.

        A node `w` is a common neighbor of a pair of nodes `u` and `v` if
        `w` is a neighbor of both `u` and `v`.

        Parameters
        ----------
        full : bool, optional
            If ``True``, computes common neighbors for all pairs of nodes in
            the graph. This computation can be expensive for large graphs, as the
            result can scale quadratically in the number of edges or cubically in
            the number of nodes. Mutually exclusive with other parameters.
            Default is ``None``.
        from_ : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the domain of the common neighbor computation: only
            common neighbors of node pairs where the first node is in this relationship
            are computed and returned. Mutually exclusive with ``full`` and ``between``.
            Default is ``None``.
        to : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. Can only
            be used together with the ``from_`` parameter. When provided with ``from_``,
            constrains the domain of the common neighbor computation: only common
            neighbors of node pairs where the first node is in ``from_`` and the
            second node is in ``to`` are computed and returned.
            Default is ``None``.
        between : Relationship, optional
            A binary relationship containing pairs of nodes. When provided,
            constrains the domain of the common neighbor computation: only common
            neighbors for the specific node pairs in this relationship are computed
            and returned. Mutually exclusive with other parameters.
            Default is ``None``.

        Returns
        -------
        Relationship
            A ternary relationship where each tuple represents a pair of nodes
            and one of their common neighbors.

        Raises
        ------
        ValueError
            If ``full`` is provided with any other parameter.
            If ``between`` is provided with any other parameter.
            If ``from_`` is provided with any parameter other than ``to``.
            If none of ``full``, ``from_``, or ``between`` is provided.
            If ``full`` is not ``True`` or ``None``.
        AssertionError
            If ``from_``, ``to``, or ``between`` is not a ``Relationship``.
            If ``from_``, ``to``, or ``between`` is not attached to the same model as the graph.
            If ``from_``, ``to``, or ``between`` does not contain the graph's ``Node`` concept.
            If ``from_`` or ``to`` is not a unary relationship.
            If ``between`` is not a binary relationship.

        Relationship Schema
        -------------------
        ``common_neighbor(node_u, node_v, common_neighbor_node)``

        * **node_u** (*Node*): The first node in the pair.
        * **node_v** (*Node*): The second node in the pair.
        * **common_neighbor_node** (*Node*): The common neighbor of the pair.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                |
        | :--------- | :-------- | :------------------- |
        | Undirected | Yes       |                      |
        | Directed   | Yes       |                      |
        | Weighted   | Yes       | Weights are ignored. |

        Notes
        -----
        The ``common_neighbor(full=True)`` method computes and caches the full common
        neighbor relationship for all pairs of nodes, providing efficient reuse across
        multiple calls. This can be expensive as the result can contain O(|E|²) or
        O(|V|³) tuples depending on graph density.

        Calling ``common_neighbor()`` without arguments raises a ``ValueError``,
        to ensure awareness and explicit acknowledgement (``full=True``) of this cost.

        In contrast, ``common_neighbor(from_=subset)`` constrains the computation to
        tuples with the first position in the passed-in ``subset``. The result is
        not cached; it is specific to the call site. When a significant fraction of
        the common neighbor relation is needed across a program, ``common_neighbor(full=True)``
        is typically more efficient. Use ``common_neighbor(from_=subset)`` only
        when small subsets of the common neighbor relationship are needed
        collectively across the program.

        The ``to`` parameter can be used together with ``from_`` to further
        constrain the computation: ``common_neighbor(from_=subset_a, to=subset_b)``
        computes common neighbors only for node pairs where the first node is in
        ``subset_a`` and the second node is in ``subset_b``. (Since ``common_neighbor``
        is symmetric in its first two positions, using ``to`` without ``from_`` would
        be functionally redundant, and is not allowed.)

        The ``between`` parameter provides another way to constrain the computation:
        Unlike ``from_`` and ``to``, which allow you to independently constrain the first
        and second positions in ``common_neighbor`` tuples to sets of nodes, ``between``
        allows you to constrain the first and second positions, jointly, to specific pairs
        of nodes.

        Examples
        --------
        >>> from relationalai.semantics import Model, define, select
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n2, dst=n4),
        ...     Edge.new(src=n4, dst=n3),
        ... )
        >>>
        >>> # 3. Select the IDs from the common_neighbor relationship and inspect
        >>> u, v, w = Node.ref("u"), Node.ref("v"), Node.ref("w")
        >>> common_neighbor = graph.common_neighbor(full=True)
        >>> select(
        ...     u.id, v.id, w.id
        ... ).where(
        ...     common_neighbor(u, v, w)
        ... ).inspect()
        ▰▰▰▰ Setup complete
            id  id2  id3
        0    1    1    2
        1    1    3    2
        2    1    4    2
        3    2    2    1
        4    2    2    3
        5    2    2    4
        6    2    3    3
        7    2    3    4
        8    2    4    3
        9    3    1    2
        10   3    2    3
        11   3    2    4
        12   3    3    2
        13   3    3    3
        14   3    3    4
        15   3    4    2
        16   3    4    3
        17   4    1    2
        18   4    2    3
        19   4    3    2
        20   4    3    3
        21   4    4    2
        22   4    4    3

        >>> # 4. Use 'from_' parameter to constrain the set of nodes to compute common neighbors for
        >>> # Define a subset containing only node 1
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(node.id == 1).define(subset(node))
        >>>
        >>> # Get common neighbors only for pairs where first node is in subset
        >>> constrained_common_neighbor = graph.common_neighbor(from_=subset)
        >>> select(u.id, v.id, w.id).where(constrained_common_neighbor(u, v, w)).inspect()
        ▰▰▰▰ Setup complete
           id  id2  id3
        0   1    1    2
        1   1    3    2
        2   1    4    2

        >>> # 5. Use both 'from_' and 'to' parameters to constrain the first two positions
        >>> subset_a = model.Relationship(f"{{node:{Node}}} is in subset_a")
        >>> subset_b = model.Relationship(f"{{node:{Node}}} is in subset_b")
        >>> where(node.id == 1).define(subset_a(node))
        >>> where(node.id == 3).define(subset_b(node))
        >>>
        >>> # Get common neighbors only where the first node is in subset_a and the second node is in subset_b
        >>> constrained_common_neighbor = graph.common_neighbor(from_=subset_a, to=subset_b)
        >>> select(u.id, v.id, w.id).where(constrained_common_neighbor(u, v, w)).inspect()
        ▰▰▰▰ Setup complete
           id  id2  id3
        0   1    3    2

        >>> # 6. Use 'between' parameter to constrain to specific pairs of nodes
        >>> pairs = model.Relationship(f"{{node_a:{Node}}} and {{node_b:{Node}}} are a pair")
        >>> node_a, node_b = Node.ref(), Node.ref()
        >>> where(node_a.id == 1, node_b.id == 3).define(pairs(node_a, node_b))
        >>> where(node_a.id == 2, node_b.id == 4).define(pairs(node_a, node_b))
        >>>
        >>> # Get common neighbors only for the specific pairs (1, 3) and (2, 4)
        >>> constrained_common_neighbor = graph.common_neighbor(between=pairs)
        >>> select(u.id, v.id, w.id).where(constrained_common_neighbor(u, v, w)).inspect()
        ▰▰▰▰ Setup complete
           id  id2  id3
        0   1    3    2
        1   2    4    3

        """
        # Validate domain constraint parameters (common_neighbor is symmetric).
        symmetric = True
        self._validate_domain_constraint_parameters(
            'common_neighbor', symmetric, full, from_, to, between
        )

        # At this point, exactly one of `full`, `from_`, or `between`
        # has been provided, and if `to` is provided, `from_` is also provided.

        # Handle `between`.
        if between is not None:
            self._validate_pair_subset_parameter(between)
            return self._common_neighbor_between(between)

        # Handle `from_` (and potentially `to`).
        if from_ is not None:
            self._validate_node_subset_parameter('from_', from_)
            if to is not None:
                self._validate_node_subset_parameter('to', to)
                return self._common_neighbor_from_to(from_, to)
            return self._common_neighbor_from(from_)

        # Handle `full`.
        return self._common_neighbor

    @cached_property
    def _common_neighbor(self):
        """Lazily define and cache the full common_neighbor relationship."""
        _common_neighbor_rel = self._create_common_neighbor_relationship()
        _common_neighbor_rel.annotate(annotations.track("graphs", "common_neighbor"))
        return _common_neighbor_rel

    def _common_neighbor_from(self, node_subset_from: Relationship):
        """
        Create a common_neighbor relationship, with the first position in each
        tuple constrained to be in the given subset of nodes. Note this relationship
        is not cached; it is specific to the callsite.
        """
        _common_neighbor_rel = self._create_common_neighbor_relationship(
            node_subset_from=node_subset_from
        )
        _common_neighbor_rel.annotate(annotations.track("graphs", "common_neighbor_from"))
        return _common_neighbor_rel

    def _common_neighbor_from_to(self, node_subset_from: Relationship, node_subset_to: Relationship):
        """
        Create a common_neighbor relationship, with the first position in each
        tuple constrained to be in `node_subset_from`, and the second position in
        each tuple constrained to be in `node_subset_to`. Note this relationship
        is not cached; it is specific to the callsite.
        """
        _common_neighbor_rel = self._create_common_neighbor_relationship(
            node_subset_from=node_subset_from,
            node_subset_to=node_subset_to
        )
        _common_neighbor_rel.annotate(annotations.track("graphs", "common_neighbor_from_to"))
        return _common_neighbor_rel

    def _common_neighbor_between(self, pair_subset: Relationship):
        """
        Create a common_neighbor relationship, with the first and second position
        in each tuple jointly constrained to be in the given set of pairs
        of nodes. Note this relationship is not cached;
        it is specific to the callsite.
        """
        _common_neighbor_rel = self._create_common_neighbor_relationship(
            pair_subset_between=pair_subset
        )
        _common_neighbor_rel.annotate(annotations.track("graphs", "common_neighbor_between"))
        return _common_neighbor_rel

    def _create_common_neighbor_relationship(
        self,
        *,
        node_subset_from: Optional[Relationship] = None,
        node_subset_to: Optional[Relationship] = None,
        pair_subset_between: Optional[Relationship] = None,
    ):
        """
        Create common_neighbor relationship, optionally constrained by the provided
        node subsets or pair subset.
        """
        _common_neighbor_rel = self._model.Relationship(
            f"{{node_a:{self._NodeConceptStr}}} and {{node_b:{self._NodeConceptStr}}} "
            f"have common neighbor {{neighbor_node:{self._NodeConceptStr}}}"
        )
        node_a, node_b, neighbor_node = self.Node.ref(), self.Node.ref(), self.Node.ref()

        # Handle the `between` case.
        if pair_subset_between is not None:
            # Extract all nodes that appear in any position of the pairs relationship
            # into a unary relation that we can use to constrain the neighbor computation.
            nodes_in_pairs = self._model.Relationship(f"{{node:{self._NodeConceptStr}}} is in pairs subset")
            node_x, node_y = self.Node.ref(), self.Node.ref()
            where(
                pair_subset_between(node_x, node_y)
            ).define(
                nodes_in_pairs(node_x),
                nodes_in_pairs(node_y)
            )

            # Create a neighbor relation constrained to the nodes that appear in the pairs.
            neighbor_rel = self._neighbor_of(nodes_in_pairs)
            neighbor_a_rel = neighbor_rel
            neighbor_b_rel = neighbor_rel

            # The constraint fragment ensures we only compute common neighbors for the
            # specific pairs provided, not for all combinations of nodes in those pairs.
            node_constraint = [pair_subset_between(node_a, node_b)]

        # Handle the `from_` case.
        elif node_subset_from is not None and node_subset_to is None:
            # Note that in this case we must compute all of `_neighbor` anyway,
            # as the second position in each tuple is unconstrained. Given that,
            # computing `_neighbor_of` for `node_subset_from` to constrain the
            # first position that way would be less efficient than using
            # `_neighbor` and joining the relevant variable with `node_subset_from`.
            neighbor_a_rel = self._neighbor
            neighbor_b_rel = self._neighbor
            node_constraint = [node_subset_from(node_a)]
            # TODO: Nice observation from @rygao: We can instead implement this
            #   as a depth-2 traversal starting from `node_subset_from`. Candidate code:

                # neighbor_a_rel = self._neighbor_of(node_subset_from)
                #
                # domain_w = Relationship(f"{{node:{self._NodeConceptStr}}} is the domain of `w` in `common_neighbor(u, v, w)`")
                # where(neighbor_a_rel(node_a, node_b)).define(domain_w(node_b))
                # neighbor_b_rel = self._neighbor_of(domain_w)
                #
                # node_constraint = []
                #
                # # For this case only, we reverse the args of `neighbor_b_rel()`, which
                # # is allowed by the symmetry of `neighbor`, in order to take advantage
                # # of domain constraint on `neighbor_b_rel()`.
                # where(
                #     *node_constraint,
                #     neighbor_a_rel(node_a, neighbor_node),
                #     neighbor_b_rel(neighbor_node, node_b)
                # ).define(_common_neighbor_rel(node_a, node_b, neighbor_node))

        # Handle the `from_`/`to` case.
        elif node_subset_from is not None and node_subset_to is not None:
            # There are two cases:
            #
            # NOTE: For both of the following branches, spiritually we are applying
            #   `node_constraint = [node_subset_from(node_a), node_subset_to(node_b)]`,
            #   but these are already enforced by the use of the constrained
            #   `_neighbor_of` relationships, so we don't need to include them
            #   again in `node_constraint`.
            if node_subset_from is node_subset_to:
                # If `node_subset_from` and `node_subset_to` are object-identical,
                # we can compute `_neighbor_of` once, use it for both positions,
                # and apply no further constraint.
                neighbor_rel = self._neighbor_of(node_subset_from)
                neighbor_a_rel = neighbor_rel
                neighbor_b_rel = neighbor_rel
                node_constraint = []
            else:
                # Otherwise, we have two options: 1) compute `_neighbor_of` twice,
                # once for each node subset; or 2) compute `_neighbor` once, over
                # the union of both subsets, and apply constraints to each position.
                # Which of these is more efficient depends on the detailed nature
                # of the subsets, which we don't have knowledge of here. Here
                # we choose the simpler/cleaner of the two options (1) as such:
                neighbor_a_rel = self._neighbor_of(node_subset_from)
                neighbor_b_rel = self._neighbor_of(node_subset_to)
                node_constraint = []

        # Handle the `full` case.
        else:
            neighbor_a_rel = self._neighbor
            neighbor_b_rel = self._neighbor
            node_constraint = []

        # Define the common neighbor relationship using the neighbor relations and
        # constraints determined above. This logic is shared across all constraint types.
        where(
            *node_constraint,
            neighbor_a_rel(node_a, neighbor_node),
            neighbor_b_rel(node_b, neighbor_node)
        ).define(_common_neighbor_rel(node_a, node_b, neighbor_node))

        return _common_neighbor_rel


    @include_in_docs
    def degree(self, *, of: Optional[Relationship] = None):
        """Returns a binary relationship containing the degree of each node.

        For directed graphs, a node's degree is the sum of its indegree and
        outdegree. For undirected graphs, a self-loop contributes +2 to the
        node's degree.

        Parameters
        ----------
        of : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the domain of the degree computation: only
            degrees of nodes in this relationship are computed and returned.

        Returns
        -------
        Relationship
            A binary relationship where each tuple represents a node and its
            degree.

        Relationship Schema
        -------------------
        ``degree(node, node_degree)``

        * **node** (*Node*): The node.
        * **node_degree** (*Integer*): The degree of the node.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                          |
        | :--------- | :-------- | :----------------------------- |
        | Undirected | Yes       | A self-loop contributes +2.    |
        | Directed   | Yes       |                                |
        | Weighted   | Yes       | Weights are ignored.           |

        Examples
        --------
        **Undirected Graph Example**

        >>> from relationalai.semantics import Model, define, select, where, Integer, union
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n2, dst=n4)
        ... )
        >>>
        >>> # 3. Select the degree of each node and inspect
        >>> node, node_degree = Node.ref("node"), Integer.ref("node_degree")
        >>> degree = graph.degree()
        >>> select(node.id, node_degree).where(degree(node, node_degree)).inspect()
        ▰▰▰▰ Setup complete
           id  node_degree
        0   1            1
        1   2            3
        2   3            3
        3   4            1

        >>> # 4. Use 'of' parameter to constrain the set of nodes to compute degree of
        >>> # Define a subset containing only nodes 2 and 3
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(union(node.id == 2, node.id == 3)).define(subset(node))
        >>>
        >>> # Get degrees only of nodes in the subset
        >>> constrained_degree = graph.degree(of=subset)
        >>> select(node.id, node_degree).where(constrained_degree(node, node_degree)).inspect()
        ▰▰▰▰ Setup complete
           id  node_degree
        0   2            3
        1   3            3

        **Directed Graph Example**

        >>> from relationalai.semantics import define, select, Integer
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>> # 1. Set up a directed graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define the same nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n2, dst=n4)
        ... )
        >>>
        >>> # 3. Select the degree of each node and inspect
        >>> node, node_degree = Node.ref("node"), Integer.ref("node_degree")
        >>> degree = graph.degree()
        >>> select(node.id, node_degree).where(degree(node, node_degree)).inspect()
        ▰▰▰▰ Setup complete
           id  node_degree
        0   1            1
        1   2            3
        2   3            3
        3   4            1

        >>> # 4. Use 'of' parameter to constrain the set of nodes to compute degree of
        >>> # Define a subset containing only nodes 1 and 4
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(union(node.id == 1, node.id == 4)).define(subset(node))
        >>>
        >>> # Get degrees only of nodes in the subset
        >>> constrained_degree = graph.degree(of=subset)
        >>> select(node.id, node_degree).where(constrained_degree(node, node_degree)).inspect()
        ▰▰▰▰ Setup complete
           id  node_degree
        0   1            1
        1   4            1

        Notes
        -----
        The ``degree()`` method, called with no parameters, computes and caches
        the full degree relationship, providing efficient reuse across multiple
        calls to ``degree()``. In contrast, ``degree(of=subset)`` computes a
        constrained relationship specific to the passed-in ``subset`` and that
        call site. When a significant fraction of the degree relation is needed
        across a program, ``degree()`` is typically more efficient; this is the
        typical case. Use ``degree(of=subset)`` only when small subsets of the
        degree relationship are needed collectively across the program.

        See Also
        --------
        indegree
        outdegree

        """
        if of is None:
            return self._degree
        else:
            # Validate the 'of' parameter
            self._validate_node_subset_parameter('of', of)
            return self._degree_of(of)

    @cached_property
    def _degree(self):
        """Lazily define and cache the self._degree relationship."""
        _degree_rel = self._create_degree_relationship(node_subset=None)
        _degree_rel.annotate(annotations.track("graphs", "degree"))
        return _degree_rel

    def _degree_of(self, node_subset: Relationship):
        """
        Create a degree relationship constrained to the subset of nodes
        in `node_subset`. Note this relationship is not cached; it is
        specific to the callsite.
        """
        _degree_rel = self._create_degree_relationship(node_subset=node_subset)
        _degree_rel.annotate(annotations.track("graphs", "degree_of"))
        return _degree_rel

    def _create_degree_relationship(self, *, node_subset: Optional[Relationship]):
        _degree_rel = self._model.Relationship(f"{{node:{self._NodeConceptStr}}} has degree {{count:Integer}}")

        node = self.Node.ref()
        if self.directed:
            # For directed graphs, degree is the sum of indegree and outdegree.
            if node_subset is None:
                indegree_rel = self._indegree
                outdegree_rel = self._outdegree
            else:
                indegree_rel = self._indegree_of(node_subset)
                outdegree_rel = self._outdegree_of(node_subset)

            incount, outcount = Integer.ref(), Integer.ref()
            where(
                indegree_rel(node, incount),
                outdegree_rel(node, outcount),
            ).define(_degree_rel(node, incount + outcount))
        else:
            # For undirected graphs, degree counts each non-loop edge once and each
            # self-loop twice. Self-loops can be computed as the difference between
            # count_neighbor and degree_no_self, where degree_no_self counts neighbors
            # excluding self-loops.

            # _self_loop_count := _neighbor_count - _degree_no_self
            # _degree := _degree_no_self + 2 * _self_loop_count
            # Therefore:
            # _degree := 2 * _neighbor_count - _degree_no_self

            if node_subset is None:
                count_neighbor_rel = self._count_neighbor
                degree_no_self_rel = self._degree_no_self
            else:
                count_neighbor_rel = self._count_neighbor_of(node_subset)
                degree_no_self_rel = self._degree_no_self_of(node_subset)

            _degree_no_self = Integer.ref()
            where(
                # No explicit node constraint needed here, as `_degree_no_self_of`
                # relation is constrained to `node_subset`.
                _neighbor_count := where(count_neighbor_rel(node, Integer)).select(Integer) | 0,
                degree_no_self_rel(node, _degree_no_self),
                _degree := 2 * _neighbor_count - _degree_no_self
            ).define(_degree_rel(node, _degree))

        return _degree_rel


    @include_in_docs
    def indegree(self, *, of: Optional[Relationship] = None):
        """Returns a binary relationship containing the indegree of each node.

        A node's indegree is the number of incoming edges. For undirected
        graphs, a node's indegree is identical to its degree, except self-loops
        contribute only +1 to a node's indegree.

        Parameters
        ----------
        of : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the domain of the indegree computation: only
            indegrees of nodes in this relationship are computed and returned.

        Returns
        -------
        Relationship
            A binary relationship where each tuple represents a node and its
            indegree.

        Relationship Schema
        -------------------
        ``indegree(node, node_indegree)``

        * **node** (*Node*): The node.
        * **node_indegree** (*Integer*): The indegree of the node.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                                         |
        | :--------- | :-------- | :-------------------------------------------- |
        | Undirected | Yes       | Identical to `degree`, except for self-loops. |
        | Directed   | Yes       |                                               |
        | Weighted   | Yes       | Weights are ignored.                          |

        Examples
        --------
        **Undirected Graph Example**

        >>> from relationalai.semantics import Model, define, select, where, union, Integer
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n3, dst=n4),
        ... )
        >>> # 3. Select the indegree of each node and inspect
        >>> node, node_indegree = Node.ref("node"), Integer.ref("node_indegree")
        >>> indegree = graph.indegree()
        >>> select(node.id, node_indegree).where(indegree(node, node_indegree)).inspect()
        ▰▰▰▰ Setup complete
            id  node_indegree
        0   1              1
        1   2              2
        2   3              3
        3   4              1
        >>>
        >>> # 4. Use 'of' parameter to constrain the set of nodes to compute indegree of
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(union(node.id == 2, node.id == 3)).define(subset(node))
        >>> constrained_indegree = graph.indegree(of=subset)
        >>> select(node.id, node_indegree).where(constrained_indegree(node, node_indegree)).inspect()
        ▰▰▰▰ Setup complete
            id  node_indegree
        0   2              2
        1   3              3

        **Directed Graph Example**

        >>> from relationalai.semantics import Model, define, select, where, union, Integer
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a directed graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define the same nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n3, dst=n4)
        ... )
        >>>
        >>> # 3. Select the indegree of each node and inspect
        >>> node, node_indegree = Node.ref("node"), Integer.ref("node_indegree")
        >>> indegree = graph.indegree()
        >>> select(node.id, node_indegree).where(indegree(node, node_indegree)).inspect()
        ▰▰▰▰ Setup complete
            id  node_indegree
        0   1              0
        1   2              1
        2   3              2
        3   4              1
        >>>
        >>> # 4. Use 'of' parameter to constrain the set of nodes to compute indegree of
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(union(node.id == 2, node.id == 3)).define(subset(node))
        >>> constrained_indegree = graph.indegree(of=subset)
        >>> select(node.id, node_indegree).where(constrained_indegree(node, node_indegree)).inspect()
        ▰▰▰▰ Setup complete
            id  node_indegree
        0   2              1
        1   3              2

        Notes
        -----
        The ``indegree()`` method, called with no parameters, computes and caches
        the full indegree relationship, providing efficient reuse across multiple
        calls to ``indegree()``. In contrast, ``indegree(of=subset)`` computes a
        constrained relationship specific to the passed-in ``subset`` and that
        call site. When a significant fraction of the indegree relation is needed
        across a program, ``indegree()`` is typically more efficient; this is the
        typical case. Use ``indegree(of=subset)`` only when small subsets of the
        indegree relationship are needed collectively across the program.

        See Also
        --------
        degree
        outdegree

        """
        if of is None:
            return self._indegree
        else:
            # Validate the 'of' parameter
            self._validate_node_subset_parameter('of', of)
            return self._indegree_of(of)

    @cached_property
    def _indegree(self):
        """Lazily define and cache the self._indegree relationship."""
        _indegree_rel = self._create_indegree_relationship(node_subset=None)
        _indegree_rel.annotate(annotations.track("graphs", "indegree"))
        return _indegree_rel

    def _indegree_of(self, node_subset: Relationship):
        """
        Create an indegree relationship constrained to the subset of nodes
        in `node_subset`. Note this relationship is not cached; it is
        specific to the callsite.
        """
        _indegree_rel = self._create_indegree_relationship(node_subset=node_subset)
        _indegree_rel.annotate(annotations.track("graphs", "indegree_of"))
        return _indegree_rel

    def _create_indegree_relationship(self, *, node_subset: Optional[Relationship]):
        _indegree_rel = self._model.Relationship(f"{{node:{self._NodeConceptStr}}} has indegree {{count:Integer}}")

        # Choose the appropriate count_inneighbor relationship and node set
        if node_subset is None:
            # No constraint - use cached count_inneighbor relationship and all nodes
            count_inneighbor_rel = self._count_inneighbor
            node_constraint = []
        else:
            # Constrained to nodes in the subset - use constrained count_inneighbor relationship
            count_inneighbor_rel = self._count_inneighbor_of(node_subset)
            node_constraint = [node_subset(self.Node)]

        # Apply the same indegree logic for both cases
        where(
            *node_constraint,
            _indegree := where(count_inneighbor_rel(self.Node, Integer)).select(Integer) | 0,
        ).define(_indegree_rel(self.Node, _indegree))

        return _indegree_rel


    @include_in_docs
    def outdegree(self, *, of: Optional[Relationship] = None):
        """Returns a binary relationship containing the outdegree of each node.

        A node's outdegree is the number of outgoing edges. For undirected
        graphs, a node's outdegree is identical to its degree, except self-loops
        contribute only +1 to a node's outdegree.

        Parameters
        ----------
        of : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the domain of the outdegree computation: only
            outdegrees of nodes in this relationship are computed and returned.

        Returns
        -------
        Relationship
            A binary relationship where each tuple represents a node and its
            outdegree.

        Relationship Schema
        -------------------
        ``outdegree(node, node_outdegree)``

        * **node** (*Node*): The node.
        * **node_outdegree** (*Integer*): The outdegree of the node.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                                         |
        | :--------- | :-------- | :-------------------------------------------- |
        | Undirected | Yes       | Identical to `degree`, except for self-loops. |
        | Directed   | Yes       |                                               |
        | Weighted   | Yes       | Weights are ignored.                          |

        Examples
        --------
        **Undirected Graph Example**

        >>> from relationalai.semantics import Model, define, select, where, union, Integer
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n2, dst=n4)
        ... )
        >>>
        >>> # 3. Select the outdegree of each node and inspect
        >>> node, node_outdegree = Node.ref("node"), Integer.ref("node_outdegree")
        >>> outdegree = graph.outdegree()
        >>> select(node.id, node_outdegree).where(outdegree(node, node_outdegree)).inspect()
        ▰▰▰▰ Setup complete
            id  node_outdegree
        0   1               1
        1   2               3
        2   3               2
        3   4               1
        >>>
        >>> # 4. Use 'of' parameter to constrain the set of nodes to compute outdegree of
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(union(node.id == 2, node.id == 3)).define(subset(node))
        >>> constrained_outdegree = graph.outdegree(of=subset)
        >>> select(node.id, node_outdegree).where(constrained_outdegree(node, node_outdegree)).inspect()
        ▰▰▰▰ Setup complete
            id  node_outdegree
        0   2               3
        1   3               2

        **Directed Graph Example**

        >>> from relationalai.semantics import Model, define, select, where, union, Integer
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a directed graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define the same nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n2, dst=n4)
        ... )
        >>>
        >>> # 3. Select the outdegree of each node and inspect
        >>> node, node_outdegree = Node.ref("node"), Integer.ref("node_outdegree")
        >>> outdegree = graph.outdegree()
        >>> select(node.id, node_outdegree).where(outdegree(node, node_outdegree)).inspect()
        ▰▰▰▰ Setup complete
            id  node_outdegree
        0   1               1
        1   2               2
        2   3               1
        3   4               0
        >>>
        >>> # 4. Use 'of' parameter to constrain the set of nodes to compute outdegree of
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(union(node.id == 2, node.id == 3)).define(subset(node))
        >>> constrained_outdegree = graph.outdegree(of=subset)
        >>> select(node.id, node_outdegree).where(constrained_outdegree(node, node_outdegree)).inspect()
        ▰▰▰▰ Setup complete
            id  node_outdegree
        0   2               2
        1   3               1

        Notes
        -----
        The ``outdegree()`` method, called with no parameters, computes and caches
        the full outdegree relationship, providing efficient reuse across multiple
        calls to ``outdegree()``. In contrast, ``outdegree(of=subset)`` computes a
        constrained relationship specific to the passed-in ``subset`` and that
        call site. When a significant fraction of the outdegree relation is needed
        across a program, ``outdegree()`` is typically more efficient; this is the
        typical case. Use ``outdegree(of=subset)`` only when small subsets of the
        outdegree relationship are needed collectively across the program.

        See Also
        --------
        degree
        indegree

        """
        if of is None:
            return self._outdegree
        else:
            # Validate the 'of' parameter
            self._validate_node_subset_parameter('of', of)
            return self._outdegree_of(of)

    @cached_property
    def _outdegree(self):
        """Lazily define and cache the self._outdegree relationship."""
        _outdegree_rel = self._create_outdegree_relationship(node_subset=None)
        _outdegree_rel.annotate(annotations.track("graphs", "outdegree"))
        return _outdegree_rel

    def _outdegree_of(self, node_subset: Relationship):
        """
        Create an outdegree relationship constrained to the subset of nodes
        in `node_subset`. Note this relationship is not cached; it is
        specific to the callsite.
        """
        _outdegree_rel = self._create_outdegree_relationship(node_subset=node_subset)
        _outdegree_rel.annotate(annotations.track("graphs", "outdegree_of"))
        return _outdegree_rel

    def _create_outdegree_relationship(self, *, node_subset: Optional[Relationship]):
        _outdegree_rel = self._model.Relationship(f"{{node:{self._NodeConceptStr}}} has outdegree {{count:Integer}}")

        # Choose the appropriate count_outneighbor relationship and node set
        if node_subset is None:
            # No constraint - use cached count_outneighbor relationship and all nodes
            count_outneighbor_rel = self._count_outneighbor
            node_constraint = []
        else:
            # Constrained to nodes in the subset - use constrained count_outneighbor relationship
            count_outneighbor_rel = self._count_outneighbor_of(node_subset)
            node_constraint = [node_subset(self.Node)]

        # Apply the same outdegree logic for both cases
        where(
            *node_constraint,
            _outdegree := where(count_outneighbor_rel(self.Node, Integer)).select(Integer) | 0,
        ).define(_outdegree_rel(self.Node, _outdegree))

        return _outdegree_rel


    @include_in_docs
    def weighted_degree(self, *, of: Optional[Relationship] = None):
        """Returns a binary relationship containing the weighted degree of each node.

        A node's weighted degree is the sum of the weights of all edges
        connected to it. For directed graphs, this is the sum of the weights
        of both incoming and outgoing edges. For undirected graphs, the weights
        of self-loops contribute twice to the node's weighted degree. For
        unweighted graphs, all edge weights are considered to be 1.0.

        Parameters
        ----------
        of : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the domain of the weighted degree computation: only
            weighted degrees of nodes in this relationship are computed and returned.

        Returns
        -------
        Relationship
            A binary relationship where each tuple represents a node and its
            weighted degree.

        Relationship Schema
        -------------------
        ``weighted_degree(node, node_weighted_degree)``

        * **node** (*Node*): The node.
        * **node_weighted_degree** (*Float*): The weighted degree of the node.

        Supported Graph Types
        ---------------------
        | Graph Type   | Supported | Notes                                  |
        | :----------- | :-------- | :------------------------------------- |
        | Undirected   | Yes       | A self-loop contributes twice.         |
        | Directed     | Yes       |                                        |
        | Weighted     | Yes       |                                        |
        | Unweighted   | Yes       | Edge weights are considered to be 1.0. |

        Examples
        --------
        >>> from relationalai.semantics import Model, define, select, where, union, Float
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a directed, weighted graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=True)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges with weights
        >>> n1, n2, n3 = [Node.new(id=i) for i in range(1, 4)]
        >>> define(n1, n2, n3)
        >>> define(
        ...     Edge.new(src=n1, dst=n2, weight=1.0),
        ...     Edge.new(src=n2, dst=n1, weight=0.0),
        ...     Edge.new(src=n2, dst=n3, weight=1.0),
        ... )
        >>>
        >>> # 3. Select the weighted degree of each node and inspect
        >>> node, node_weighted_degree = Node.ref("node"), Float.ref("node_weighted_degree")
        >>> weighted_degree = graph.weighted_degree()
        >>> select(
        ...     node.id, node_weighted_degree
        ... ).where(
        ...     weighted_degree(node, node_weighted_degree)
        ... ).inspect()
        ▰▰▰▰ Setup complete
            id  node_weighted_degree
        0   1                   1.0
        1   2                   2.0
        2   3                   1.0
        >>>
        >>> # 4. Use 'of' parameter to constrain the set of nodes to compute weighted degree of
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(union(node.id == 2, node.id == 3)).define(subset(node))
        >>> constrained_weighted_degree = graph.weighted_degree(of=subset)
        >>> select(
        ...     node.id, node_weighted_degree
        ... ).where(
        ...     constrained_weighted_degree(node, node_weighted_degree)
        ... ).inspect()
        ▰▰▰▰ Setup complete
            id  node_weighted_degree
        0   2                   2.0
        1   3                   1.0

        Notes
        -----
        The ``weighted_degree()`` method, called with no parameters, computes and caches
        the full weighted degree relationship, providing efficient reuse across multiple
        calls to ``weighted_degree()``. In contrast, ``weighted_degree(of=subset)`` computes a
        constrained relationship specific to the passed-in ``subset`` and that
        call site. When a significant fraction of the weighted degree relation is needed
        across a program, ``weighted_degree()`` is typically more efficient; this is the
        typical case. Use ``weighted_degree(of=subset)`` only when small subsets of the
        weighted degree relationship are needed collectively across the program.

        See Also
        --------
        weighted_indegree
        weighted_outdegree

        """
        if of is None:
            return self._weighted_degree
        else:
            # Validate the 'of' parameter
            self._validate_node_subset_parameter('of', of)
            return self._weighted_degree_of(of)

    @cached_property
    def _weighted_degree(self):
        """Lazily define and cache the self._weighted_degree relationship."""
        _weighted_degree_rel = self._create_weighted_degree_relationship(node_subset=None)
        _weighted_degree_rel.annotate(annotations.track("graphs", "weighted_degree"))
        return _weighted_degree_rel

    def _weighted_degree_of(self, node_subset: Relationship):
        """
        Create a weighted degree relationship constrained to the subset of nodes
        in `node_subset`. Note this relationship is not cached; it is
        specific to the callsite.
        """
        _weighted_degree_rel = self._create_weighted_degree_relationship(node_subset=node_subset)
        _weighted_degree_rel.annotate(annotations.track("graphs", "weighted_degree_of"))
        return _weighted_degree_rel

    def _create_weighted_degree_relationship(self, *, node_subset: Optional[Relationship]):
        _weighted_degree_rel = self._model.Relationship(f"{{node:{self._NodeConceptStr}}} has weighted degree {{weight:Float}}")

        if self.directed:
            # For directed graphs, weighted degree is the sum of weighted indegree and weighted outdegree.
            if node_subset is None:
                weighted_indegree_rel = self._weighted_indegree
                weighted_outdegree_rel = self._weighted_outdegree
            else:
                weighted_indegree_rel = self._weighted_indegree_of(node_subset)
                weighted_outdegree_rel = self._weighted_outdegree_of(node_subset)

            inweight, outweight = Float.ref(), Float.ref()
            where(
                weighted_indegree_rel(self.Node, inweight),
                weighted_outdegree_rel(self.Node, outweight),
            ).define(_weighted_degree_rel(self.Node, inweight + outweight))
        elif not self.directed:
            # For undirected graphs, weighted degree counts each non-loop edge weight once
            # and each self-loop edge weight twice.
            node, neighbor, weight = self.Node.ref(), self.Node.ref(), Float.ref()

            if node_subset is None:
                node_constraint = []  # No constraint on nodes.
            else:
                node_constraint = [node_subset(node)]  # Nodes constrained to given subset.

            where(
                *node_constraint,
                weighted_degree_no_loops := sum(neighbor, weight).per(node).where(
                    self._weight(node, neighbor, weight),
                    node != neighbor,
                ) | 0.0,
                weighted_degree_self_loops := sum(neighbor, weight).per(node).where(
                    self._weight(node, neighbor, weight),
                    node == neighbor,
                ) | 0.0,
            ).define(_weighted_degree_rel(node, weighted_degree_no_loops + 2 * weighted_degree_self_loops))

        return _weighted_degree_rel


    @include_in_docs
    def weighted_indegree(self, *, of: Optional[Relationship] = None):
        """Returns a binary relationship containing the weighted indegree of each node.

        A node's weighted indegree is the sum of the weights of all incoming
        edges. For undirected graphs, this is identical to `weighted_degree`,
        except for self-loops. For weighted graphs, we assume edge weights are
        non-negative. For unweighted graphs, all edge weights are considered
        to be 1.0.

        Parameters
        ----------
        of : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the domain of the weighted indegree computation: only
            weighted indegrees of nodes in this relationship are computed and returned.

        Returns
        -------
        Relationship
            A binary relationship where each tuple represents a node and its
            weighted indegree.

        Relationship Schema
        -------------------
        ``weighted_indegree(node, node_weighted_indegree)``

        * **node** (*Node*): The node.
        * **node_weighted_indegree** (*Float*): The weighted indegree of the node.

        Supported Graph Types
        ---------------------
        | Graph Type   | Supported | Notes                                                  |
        | :----------- | :-------- | :----------------------------------------------------- |
        | Undirected   | Yes       | Identical to `weighted_degree`, except for self-loops. |
        | Directed     | Yes       |                                                        |
        | Weighted     | Yes       | Assumes non-negative weights.                          |
        | Unweighted   | Yes       | Edge weights are considered to be 1.0.                 |

        Examples
        --------
        >>> from relationalai.semantics import Model, define, select, where, union, Float
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a directed, weighted graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=True)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges with weights
        >>> n1, n2, n3 = [Node.new(id=i) for i in range(1, 4)]
        >>> define(n1, n2, n3)
        >>> define(
        ...     Edge.new(src=n1, dst=n2, weight=1.0),
        ...     Edge.new(src=n2, dst=n1, weight=0.0),
        ...     Edge.new(src=n2, dst=n3, weight=1.0),
        ... )
        >>>
        >>> # 3. Select the weighted indegree of each node and inspect
        >>> node, node_weighted_indegree = Node.ref("node"), Float.ref("node_weighted_indegree")
        >>> weighted_indegree = graph.weighted_indegree()
        >>> select(
        ...     node.id, node_weighted_indegree
        ... ).where(
        ...     weighted_indegree(node, node_weighted_indegree)
        ... ).inspect()
        ▰▰▰▰ Setup complete
            id  node_weighted_indegree
        0   1                     0.0
        1   2                     1.0
        2   3                     1.0
        >>>
        >>> # 4. Use 'of' parameter to constrain the set of nodes to compute weighted indegree of
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(union(node.id == 2, node.id == 3)).define(subset(node))
        >>> constrained_weighted_indegree = graph.weighted_indegree(of=subset)
        >>> select(node.id, node_weighted_indegree).where(constrained_weighted_indegree(node, node_weighted_indegree)).inspect()
        ▰▰▰▰ Setup complete
            id  node_weighted_indegree
        0   2                     1.0
        1   3                     1.0

        Notes
        -----
        The ``weighted_indegree()`` method, called with no parameters, computes and caches
        the full weighted indegree relationship, providing efficient reuse across multiple
        calls to ``weighted_indegree()``. In contrast, ``weighted_indegree(of=subset)`` computes a
        constrained relationship specific to the passed-in ``subset`` and that
        call site. When a significant fraction of the weighted indegree relation is needed
        across a program, ``weighted_indegree()`` is typically more efficient; this is the
        typical case. Use ``weighted_indegree(of=subset)`` only when small subsets of the
        weighted indegree relationship are needed collectively across the program.

        See Also
        --------
        weighted_degree
        weighted_outdegree

        """
        if of is None:
            return self._weighted_indegree
        else:
            # Validate the 'of' parameter
            self._validate_node_subset_parameter('of', of)
            return self._weighted_indegree_of(of)

    @cached_property
    def _weighted_indegree(self):
        """Lazily define and cache the self._weighted_indegree relationship."""
        _weighted_indegree_rel = self._create_weighted_indegree_relationship(node_subset=None)
        _weighted_indegree_rel.annotate(annotations.track("graphs", "weighted_indegree"))
        return _weighted_indegree_rel

    def _weighted_indegree_of(self, node_subset: Relationship):
        """
        Create a weighted indegree relationship constrained to the subset of nodes
        in `node_subset`. Note this relationship is not cached; it is
        specific to the callsite.
        """
        _weighted_indegree_rel = self._create_weighted_indegree_relationship(node_subset=node_subset)
        _weighted_indegree_rel.annotate(annotations.track("graphs", "weighted_indegree_of"))
        return _weighted_indegree_rel

    def _create_weighted_indegree_relationship(self, *, node_subset: Optional[Relationship]):
        _weighted_indegree_rel = self._model.Relationship(f"{{node:{self._NodeConceptStr}}} has weighted indegree {{weight:Float}}")

        # Choose the appropriate node set
        if node_subset is None:
            # No constraint - use all nodes
            node_constraint = []
        else:
            # Constrained to nodes in the subset
            node_constraint = [node_subset(self.Node)]

        # Apply the weighted indegree logic for both cases
        src, inweight = self.Node.ref(), Float.ref()
        where(
            *node_constraint,
            _weighted_indegree := sum(src, inweight).per(self.Node).where(self._weight(src, self.Node, inweight)) | 0.0,
        ).define(_weighted_indegree_rel(self.Node, _weighted_indegree))

        return _weighted_indegree_rel


    @include_in_docs
    def weighted_outdegree(self, *, of: Optional[Relationship] = None):
        """Returns a binary relationship containing the weighted outdegree of each node.

        A node's weighted outdegree is the sum of the weights of all outgoing
        edges. For undirected graphs, this is identical to `weighted_degree`,
        except for self-loops. For unweighted graphs, all edge weights are
        considered to be 1.0.

        Parameters
        ----------
        of : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the domain of the weighted outdegree computation: only
            weighted outdegrees of nodes in this relationship are computed and returned.

        Returns
        -------
        Relationship
            A binary relationship where each tuple represents a node and its
            weighted outdegree.

        Relationship Schema
        -------------------
        ``weighted_outdegree(node, node_weighted_outdegree)``

        * **node** (*Node*): The node.
        * **node_weighted_outdegree** (*Float*): The weighted outdegree of the node.

        Supported Graph Types
        ---------------------
        | Graph Type   | Supported | Notes                                                  |
        | :----------- | :-------- | :----------------------------------------------------- |
        | Undirected   | Yes       | Identical to `weighted_degree`, except for self-loops. |
        | Directed     | Yes       |                                                        |
        | Weighted     | Yes       |                                                        |
        | Unweighted   | Yes       | Edge weights are considered to be 1.0.                 |

        Examples
        --------
        >>> from relationalai.semantics import Model, define, select, where, union, Float
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a directed, weighted graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=True)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges with weights
        >>> n1, n2, n3 = [Node.new(id=i) for i in range(1, 4)]
        >>> define(n1, n2, n3)
        >>> define(
        ...     Edge.new(src=n1, dst=n2, weight=1.0),
        ...     Edge.new(src=n2, dst=n1, weight=0.0),
        ...     Edge.new(src=n2, dst=n3, weight=1.0),
        ... )
        >>>
        >>> # 3. Select the weighted outdegree of each node and inspect
        >>> node, node_weighted_outdegree = Node.ref("node"), Float.ref("node_weighted_outdegree")
        >>> weighted_outdegree = graph.weighted_outdegree()
        >>> select(
        ...     node.id, node_weighted_outdegree
        ... ).where(
        ...     weighted_outdegree(node, node_weighted_outdegree)
        ... ).inspect()
        ▰▰▰▰ Setup complete
            id  node_weighted_outdegree
        0   1                      1.0
        1   2                      1.0
        2   3                      0.0
        >>>
        >>> # 4. Use 'of' parameter to constrain the set of nodes to compute weighted outdegree of
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(union(node.id == 1, node.id == 2)).define(subset(node))
        >>> constrained_weighted_outdegree = graph.weighted_outdegree(of=subset)
        >>> select(
        ...     node.id, node_weighted_outdegree
        ... ).where(
        ...     constrained_weighted_outdegree(node, node_weighted_outdegree)
        ... ).inspect()
        ▰▰▰▰ Setup complete
            id  node_weighted_outdegree
        0   1                      1.0
        1   2                      1.0

        Notes
        -----
        The ``weighted_outdegree()`` method, called with no parameters, computes and caches
        the full weighted outdegree relationship, providing efficient reuse across multiple
        calls to ``weighted_outdegree()``. In contrast, ``weighted_outdegree(of=subset)`` computes a
        constrained relationship specific to the passed-in ``subset`` and that
        call site. When a significant fraction of the weighted outdegree relation is needed
        across a program, ``weighted_outdegree()`` is typically more efficient; this is the
        typical case. Use ``weighted_outdegree(of=subset)`` only when small subsets of the
        weighted outdegree relationship are needed collectively across the program.

        See Also
        --------
        weighted_degree
        weighted_indegree

        """
        if of is None:
            return self._weighted_outdegree
        else:
            # Validate the 'of' parameter
            self._validate_node_subset_parameter('of', of)
            return self._weighted_outdegree_of(of)

    @cached_property
    def _weighted_outdegree(self):
        """Lazily define and cache the self._weighted_outdegree relationship."""
        _weighted_outdegree_rel = self._create_weighted_outdegree_relationship(node_subset=None)
        _weighted_outdegree_rel.annotate(annotations.track("graphs", "weighted_outdegree"))
        return _weighted_outdegree_rel

    def _weighted_outdegree_of(self, node_subset: Relationship):
        """
        Create a weighted outdegree relationship constrained to the subset of nodes
        in `node_subset`. Note this relationship is not cached; it is
        specific to the callsite.
        """
        _weighted_outdegree_rel = self._create_weighted_outdegree_relationship(node_subset=node_subset)
        _weighted_outdegree_rel.annotate(annotations.track("graphs", "weighted_outdegree_of"))
        return _weighted_outdegree_rel

    def _create_weighted_outdegree_relationship(self, *, node_subset: Optional[Relationship]):
        _weighted_outdegree_rel = self._model.Relationship(f"{{node:{self._NodeConceptStr}}} has weighted outdegree {{weight:Float}}")

        # Choose the appropriate node set
        if node_subset is None:
            # No constraint - use all nodes
            node_constraint = []
        else:
            # Constrained to nodes in the subset
            node_constraint = [node_subset(self.Node)]

        # Apply the weighted outdegree logic for both cases
        dst, outweight = self.Node.ref(), Float.ref()
        where(
            *node_constraint,
            _weighted_outdegree := sum(dst, outweight).per(self.Node).where(self._weight(self.Node, dst, outweight)) | 0.0,
        ).define(_weighted_outdegree_rel(self.Node, _weighted_outdegree))

        return _weighted_outdegree_rel


    @include_in_docs
    def degree_centrality(self, *, of: Optional[Relationship] = None):
        """Returns a binary relationship containing the degree centrality of each node.

        Degree centrality is a measure of a node's importance, defined as its
        degree (or weighted degree for weighted graphs) divided by the number
        of other nodes in the graph.

        For unweighted graphs without self-loops, this value will be at most 1.0;
        unweighted graphs with self-loops might have nodes with a degree centrality
        greater than 1.0. Weighted graphs may have degree centralities
        greater than 1.0 as well.

        Parameters
        ----------
        of : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the domain of the degree centrality computation: only
            degree centralities of nodes in this relationship are computed and returned.

        Returns
        -------
        Relationship
            A binary relationship where each tuple represents a node and its
            degree centrality.

        Relationship Schema
        -------------------
        ``degree_centrality(node, centrality)``

        * **node** (*Node*): The node.
        * **centrality** (*Float*): The degree centrality of the node.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                                         |
        | :--------- | :-------- | :-------------------------------------------- |
        | Undirected | Yes       |                                               |
        | Directed   | Yes       |                                               |
        | Weighted   | Yes       | The calculation uses the node's weighted degree. |

        Examples
        --------
        **Unweighted Graph Example**

        >>> from relationalai.semantics import Model, define, select, Float, where, union
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an unweighted graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n2, dst=n4),
        ... )
        >>>
        >>> # 3. Select the degree centrality of each node and inspect
        >>> node, centrality = Node.ref("node"), Float.ref("centrality")
        >>> degree_centrality = graph.degree_centrality()
        >>> select(node.id, centrality).where(degree_centrality(node, centrality)).inspect()
        ▰▰▰▰ Setup complete
           id centrality
        0   1   0.333333
        1   2   1.000000
        2   3   1.000000
        3   4   0.333333

        >>> # 4. Use 'of' parameter to constrain the set of nodes to compute degree centrality of
        >>> # Define a subset containing only nodes 2 and 3
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(union(node.id == 2, node.id == 3)).define(subset(node))
        >>>
        >>> # Get degree centralities only of nodes in the subset
        >>> constrained_degree_centrality = graph.degree_centrality(of=subset)
        >>> select(node.id, centrality).where(constrained_degree_centrality(node, centrality)).inspect()
        ▰▰▰▰ Setup complete
           id centrality
        0   2        1.0
        1   3        1.0

        **Weighted Graph Example**

        >>> from relationalai.semantics import Model, define, select, Float
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a weighted graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=True)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges with weights
        >>> n1, n2, n3 = [Node.new(id=i) for i in range(1, 4)]
        >>> define(n1, n2, n3)
        >>> define(
        ...     Edge.new(src=n1, dst=n2, weight=2.0),
        ...     Edge.new(src=n1, dst=n3, weight=0.5),
        ...     Edge.new(src=n2, dst=n3, weight=1.5),
        ... )
        >>>
        >>> # 3. Select the degree centrality using weighted degrees
        >>> node, centrality = Node.ref("node"), Float.ref("centrality")
        >>> degree_centrality = graph.degree_centrality()
        >>> select(node.id, centrality).where(degree_centrality(node, centrality)).inspect()
        ▰▰▰▰ Setup complete
            id  centrality
        0   1        1.25
        1   2        1.75
        2   3        1.00

        Notes
        -----
        The ``degree_centrality()`` method, called with no parameters, computes and caches
        the full degree centrality relationship, providing efficient reuse across multiple
        calls to ``degree_centrality()``. In contrast, ``degree_centrality(of=subset)`` computes a
        constrained relationship specific to the passed-in ``subset`` and that
        call site. When a significant fraction of the degree centrality relation is needed
        across a program, ``degree_centrality()`` is typically more efficient; this is the
        typical case. Use ``degree_centrality(of=subset)`` only when small subsets of the
        degree centrality relationship are needed collectively across the program.

        See Also
        --------
        degree
        weighted_degree

        """
        if of is None:
            return self._degree_centrality
        else:
            # Validate the 'of' parameter
            self._validate_node_subset_parameter('of', of)
            return self._degree_centrality_of(of)

    @cached_property
    def _degree_centrality(self):
        """Lazily define and cache the self._degree_centrality relationship."""
        _degree_centrality_rel = self._create_degree_centrality_relationship(node_subset=None)
        _degree_centrality_rel.annotate(annotations.track("graphs", "degree_centrality"))
        return _degree_centrality_rel

    def _degree_centrality_of(self, node_subset: Relationship):
        """
        Create a degree centrality relationship constrained to the subset of nodes
        in `node_subset`. Note this relationship is not cached; it is
        specific to the callsite.
        """
        _degree_centrality_rel = self._create_degree_centrality_relationship(node_subset=node_subset)
        _degree_centrality_rel.annotate(annotations.track("graphs", "degree_centrality_of"))
        return _degree_centrality_rel

    def _create_degree_centrality_relationship(self, *, node_subset: Optional[Relationship]):
        """Create a degree centrality relationship, optionally constrained to a subset of nodes."""
        _degree_centrality_rel = self._model.Relationship(f"{{node:{self._NodeConceptStr}}} has {{degree_centrality:Float}}")

        if node_subset is None:
            degree_rel = self._degree
            node_constraint = [] # No constraint on nodes.
        else:
            degree_rel = self._degree_of(node_subset)
            node_constraint = [node_subset(self.Node)]  # Nodes constrained to given subset.

        degree = Integer.ref()

        # A single isolated node has degree centrality zero.
        where(
            self._num_nodes(1),
            *node_constraint,
            degree_rel(self.Node, 0)
        ).define(_degree_centrality_rel(self.Node, 0.0))

        # A single non-isolated node has degree centrality one.
        where(
            self._num_nodes(1),
            *node_constraint,
            degree_rel(self.Node, degree),
            degree > 0
        ).define(_degree_centrality_rel(self.Node, 1.0))

        # General case, i.e. with more than one node.
        if self.weighted:
            maybe_weighted_degree = Float.ref()
            if node_subset is None:
                maybe_weighted_degree_rel = self._weighted_degree
            else:
                maybe_weighted_degree_rel = self._weighted_degree_of(node_subset)
        else: # not self.weighted
            maybe_weighted_degree = Integer.ref()
            maybe_weighted_degree_rel = degree_rel

        num_nodes = Integer.ref()

        where(
            self._num_nodes(num_nodes),
            num_nodes > 1,
            *node_constraint,
            maybe_weighted_degree_rel(self.Node, maybe_weighted_degree)
        ).define(_degree_centrality_rel(self.Node, maybe_weighted_degree / (num_nodes - 1.0)))

        return _degree_centrality_rel


    def eigenvector_centrality(self):
        """Returns a binary relationship containing the eigenvector centrality of each node.

        Returns
        -------
        Relationship
            A binary relationship where each tuple represents a node and its
            eigenvector centrality.

        Relationship Schema
        -------------------
        ``eigenvector_centrality(node, centrality)``

        * **node** (*Node*): The node.
        * **centrality** (*Float*): The eigenvector centrality of the node.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                                     |
        | :--------- | :-------- | :---------------------------------------- |
        | Undirected | Yes       | See Notes for convergence criteria.       |
        | Directed   | No        | Will not converge.                        |
        | Weighted   | Yes       | Assumes non-negative weights.             |

        Notes
        -----
        Eigenvector centrality is a measure of the centrality or importance
        of a node in a graph based on finding the eigenvector associated
        with the top eigenvalue of the adjacency matrix. We use the power
        method to compute the eigenvector in our implementation. Note that
        the power method `requires the adjacency matrix to be diagonalizable <https://en.wikipedia.org/wiki/Power_iteration>`_
        and will only converge if the absolute value of the top 2
        eigenvalues is distinct. Thus, if the graph you are using has an
        adjacency matrix that is not diagonalizable or the top two
        eigenvalues are not distinct, this method will not converge.

        In the case of weighted graphs, weights are assumed to be non-negative.

        Examples
        --------
        **Unweighted Graph Example**

        >>> from relationalai.semantics import Model, define, select, Float
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an unweighted, undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n4)
        ... )
        >>>
        >>> # 3. Select the eigenvector centrality for each node and inspect
        >>> node, centrality = Node.ref("node"), Float.ref("centrality")
        >>> eigenvector_centrality = graph.eigenvector_centrality()
        >>> select(node.id, centrality).where(eigenvector_centrality(node, centrality)).inspect()
        # The output will show the resulting scores, for instance:
        # (1, 0.3717480344601844)
        # (2, 0.6015009550075456)
        # (3, 0.6015009550075456)
        # (4, 0.3717480344601844)

        **Weighted Graph Example**

        >>> # 1. Set up a weighted, undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=True)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges with weights
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2, weight=0.8),
        ...     Edge.new(src=n2, dst=n3, weight=0.7),
        ...     Edge.new(src=n3, dst=n3, weight=2.0),
        ...     Edge.new(src=n2, dst=n4, weight=1.5)
        ... )
        >>>
        >>> # 3. Select the eigenvector centrality for each node and inspect
        >>> node, centrality = Node.ref("node"), Float.ref("centrality")
        >>> eigenvector_centrality = graph.eigenvector_centrality()
        >>> select(node.id, centrality).where(eigenvector_centrality(node, centrality)).inspect()
        # The output will show the resulting scores, for instance:
        # (1, 0.15732673092171892)
        # (2, 0.4732508189314368)
        # (3, 0.8150240891426493)
        # (4, 0.2949876204782229)

        """
        raise NotImplementedError("`eigenvector_centrality` is not yet implemented")

    def betweenness_centrality(self):
        """Returns a binary relationship containing the betweenness centrality of each node.

        Betweenness centrality measures how important a node is based on how many times that
        node appears in a shortest path between any two nodes in the graph. Nodes with high
        betweenness centrality represent bridges between different parts of the graph. For
        example, in a network representing airports and flights between them, nodes with high
        betweenness centrality may identify "hub" airports that connect flights to different
        regions.

        Returns
        -------
        Relationship
            A binary relationship where each tuple represents a node and its
            betweenness centrality.

        Relationship Schema
        -------------------
        ``betweenness_centrality(node, centrality)``

        * **node** (*Node*): The node.
        * **centrality** (*Float*): The betweenness centrality of the node.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                |
        | :--------- | :-------- | :------------------- |
        | Undirected | Yes       |                      |
        | Directed   | Yes       |                      |
        | Weighted   | Yes       | Weights are ignored. |

        Notes
        -----

        Calculating betweenness centrality involves computing all of the shortest paths between
        every pair of nodes in a graph and can be expensive to calculate exactly. The
        `betweenness_centrality` relation gives an approximation using the
        [Brandes-Pich](https://www.worldscientific.com/doi/abs/10.1142/S0218127407018403)
        algorithm, which samples nodes uniformly at random and performs single-source
        shortest-path computations from those nodes.

        This implementation nominally samples 100 nodes, yielding time complexity of
        `100 * O(|V|+|E|))`. If the graph has fewer than 100 nodes, it reduces to the
        [Brandes algorithm](http://snap.stanford.edu/class/cs224w-readings/brandes01centrality.pdf),
        with time complexity `O(|V|(|V|+|E|))` for unweighted graphs.

        Examples
        --------
        >>> from relationalai.semantics import Model, define, select, Float
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n2, dst=n4)
        ... )
        >>>
        >>> # 3. Select the betweenness centrality for each node and inspect
        >>> node, centrality = Node.ref("node"), Float.ref("centrality")
        >>> betweenness_centrality = graph.betweenness_centrality()
        >>> select(node.id, centrality).where(betweenness_centrality(node, centrality)).inspect()
        # The output will show the resulting scores, for instance:
        # (1, 0.0)
        # (2, 3.0)
        # (3, 0.0)
        # (4, 0.0)

        """
        raise NotImplementedError("`betweenness_centrality` is not implemented.")

    def pagerank(
            self,
            damping_factor:float = 0.85,
            tolerance:float = 1e-6,
            max_iter:int = 20,
    ):
        """Returns a binary relationship containing the PageRank score of each node.

        Parameters
        ----------
        damping_factor : float, optional
            The damping factor for the PageRank calculation. Must be in the
            range [0, 1). Default is 0.85.
        tolerance : float, optional
            The convergence tolerance for the PageRank calculation. Must be
            a non-negative float. Default is 1e-6.
        max_iter : int, optional
            The maximum number of iterations for PageRank to run. Must be a
            positive integer. Default is 20.

        Returns
        -------
        Relationship
            A binary relationship where each tuple represents a node and its
            PageRank score.

        Relationship Schema
        -------------------
        ``pagerank(node, score)``

        * **node** (*Node*): The node.
        * **score** (*Float*): The PageRank score of the node.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                              |
        | :--------- | :-------- | :--------------------------------- |
        | Undirected | Yes       |                                    |
        | Directed   | Yes       |                                    |
        | Weighted   | Yes       | Only non-negative weights supported. |
        | Unweighted | Yes       |                                    |

        Examples
        --------
        **Unweighted Graph Example**

        >>> from relationalai.semantics import Model, define, select, Float
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an unweighted, undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n2, dst=n4)
        ... )
        >>>
        >>> # 3. Compute PageRank with default parameters and inspect
        >>> node, score = Node.ref("node"), Float.ref("score")
        >>> pagerank = graph.pagerank()
        >>> select(node.id, score).where(pagerank(node, score)).inspect()
        # The output will show the PageRank score for each node:
        # (1, 0.155788...)
        # (2, 0.417487...)
        # (3, 0.270935...)
        # (4, 0.155788...)

        **Weighted Graph Example with Configuration**

        >>> # 1. Set up a weighted, directed graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=True)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges with weights
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2, weight=1.0),
        ...     Edge.new(src=n1, dst=n3, weight=2.0),
        ...     Edge.new(src=n3, dst=n4, weight=3.0)
        ... )
        >>>
        >>> # 3. Compute PageRank with custom parameters and inspect
        >>> node, score = Node.ref("node"), Float.ref("score")
        >>> pagerank = graph.pagerank(damping_factor=0.85, tolerance=1e-6, max_iter=20)
        >>> select(node.id, score).where(pagerank(node, score)).inspect()
        # The output will show the PageRank score for each node:
        # (1, 0.264904)
        # (2, 0.112556)
        # (3, 0.387444)
        # (4, 0.235096)

        **Example with Diagnostics (Hypothetical)**

        The following example is hypothetical, and requires replacement
        once this method is implemented in full, illustrating however
        the implemented diagnostics mechanism works.

        >>> # 1. Set up graph as above
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=True)
        >>> Node, Edge = graph.Node, graph.Edge
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2, weight=1.0),
        ...     Edge.new(src=n1, dst=n3, weight=2.0),
        ...     Edge.new(src=n3, dst=n4, weight=3.0)
        ... )
        >>>
        >>> # 2. Hypothetical call to get results and diagnostics
        >>> pagerank_info = graph.pagerank(diagnostics=True)
        >>>
        >>> # 3. Select the results
        >>> # select(pagerank_info.result).inspect()
        # The output would show the PageRank scores:
        # (1, 0.161769)
        # (2, 0.207603)
        # (3, 0.253438)
        # (4, 0.377191)
        >>>
        >>> # 4. Select the number of iterations from diagnostics
        >>> # select(pagerank_info.diagnostics.num_iterations).inspect()
        # The output would show the number of iterations:
        # 13
        >>>
        >>> # 5. Select the termination status from diagnostics
        >>> # select(pagerank_info.diagnostics.termination_status).inspect()
        # The output would show the termination status:
        # :converged

        """
        _assert_type("pagerank:tolerance", tolerance, Real)
        _assert_exclusive_lower_bound("pagerank:tolerance", tolerance, 0.0)

        _assert_type("pagerank:max_iter", max_iter, int)
        _assert_exclusive_lower_bound("pagerank:max_iter", max_iter, 0)

        _assert_type("pagerank:damping_factor", damping_factor, Real)
        _assert_inclusive_lower_bound("pagerank:damping_factor", damping_factor, 0.0)
        _assert_exclusive_upper_bound("pagerank:damping_factor", damping_factor, 1.0)

        raise NotImplementedError("`pagerank` is not yet implemented.")


    @include_in_docs
    def triangle(self, *, full: Optional[bool] = None):
        """Returns a ternary relationship containing all triangles in the graph.

        Unlike `unique_triangle`, this relationship contains all permutations
        of the nodes for each triangle found.

        Parameters
        ----------
        full : bool, optional
            If ``True``, computes triangles for all triplets of nodes in the graph.
            This computation can be expensive for large graphs. Must be set to ``True``
            to compute the full triangle relationship.
            Default is ``None``.

        Returns
        -------
        Relationship
            A ternary relationship where each tuple represents a triangle.

        Raises
        ------
        ValueError
            If ``full`` is not provided.
            If ``full`` is not ``True``.

        Relationship Schema
        -------------------
        ``triangle(node_a, node_b, node_c)``

        * **node_a** (*Node*): The first node in the triangle.
        * **node_b** (*Node*): The second node in the triangle.
        * **node_c** (*Node*): The third node in the triangle.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                |
        | :--------- | :-------- | :------------------- |
        | Undirected | Yes       |                      |
        | Directed   | Yes       |                      |
        | Weighted   | Yes       | Weights are ignored. |

        Examples
        --------
        **Directed Graph Example**

        >>> from relationalai.semantics import Model, define, select
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a directed graph with a 3-cycle
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3 = [Node.new(id=i) for i in range(1, 4)]
        >>> define(n1, n2, n3)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n1),
        ... )
        >>>
        >>> # 3. Select all triangles and inspect
        >>> a,b,c = Node.ref("a"), Node.ref("b"), Node.ref("c")
        >>> triangle = graph.triangle(full=True)
        >>> select(a.id, b.id, c.id).where(triangle(a, b, c)).inspect()
        ▰▰▰▰ Setup complete
           id  id2  id3
        0   1    2    3
        1   2    3    1
        2   3    1    2

        **Undirected Graph Example**

        >>> from relationalai.semantics import Model, define, select
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an undirected graph with a triangle
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define the same nodes and edges
        >>> n1, n2, n3 = [Node.new(id=i) for i in range(1, 4)]
        >>> define(n1, n2, n3)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n1),
        ... )
        >>>
        >>> # 3. Select all triangles and inspect
        >>> a,b,c = Node.ref("a"), Node.ref("b"), Node.ref("c")
        >>> triangle = graph.triangle(full=True)
        >>> select(a.id, b.id, c.id).where(triangle(a, b, c)).inspect()
        ▰▰▰▰ Setup complete
           id  id2  id3
        0   1    2    3
        1   1    3    2
        2   2    1    3
        3   2    3    1
        4   3    1    2
        5   3    2    1

        See Also
        --------
        unique_triangle
        num_triangles
        triangle_count

        """
        # Validate full parameter
        if full is None:
            raise ValueError(
                "Computing triangle for all triplets can be expensive. To confirm "
                "that you would like to compute the full triangle relationship, "
                "please call `triangle(full=True)`. "
                "(Domain constraints are not available for `triangle` at this time. "
                "If you need domain constraints for `triangle`, please reach out.)"
            )

        if full is not True:
            raise ValueError(
                f"Invalid value (`{full}`) for 'full' parameter. Use `full=True` "
                "to compute the full triangle relationship. "
            )

        return self._triangle

    @cached_property
    def _triangle(self):
        """Lazily define and cache the self._triangle relationship."""
        _triangle_rel = self._model.Relationship(f"{{node_a:{self._NodeConceptStr}}} and {{node_b:{self._NodeConceptStr}}} and {{node_c:{self._NodeConceptStr}}} form a triangle")
        _triangle_rel.annotate(annotations.track("graphs", "triangle"))

        a, b, c = self.Node.ref(), self.Node.ref(), self.Node.ref()

        if self.directed:
            where(self._unique_triangle(a, b, c)).define(_triangle_rel(a, b, c))
            where(self._unique_triangle(b, c, a)).define(_triangle_rel(a, b, c))
            where(self._unique_triangle(c, a, b)).define(_triangle_rel(a, b, c))
        else:
            where(self._unique_triangle(a, b, c)).define(_triangle_rel(a, b, c))
            where(self._unique_triangle(a, c, b)).define(_triangle_rel(a, b, c))
            where(self._unique_triangle(b, a, c)).define(_triangle_rel(a, b, c))
            where(self._unique_triangle(b, c, a)).define(_triangle_rel(a, b, c))
            where(self._unique_triangle(c, a, b)).define(_triangle_rel(a, b, c))
            where(self._unique_triangle(c, b, a)).define(_triangle_rel(a, b, c))

        return _triangle_rel


    @include_in_docs
    def unique_triangle(self, *, full: Optional[bool] = None):
        """Returns a ternary relationship containing all unique triangles in the graph.

        Parameters
        ----------
        full : bool, optional
            If ``True``, computes unique triangles for all triplets of nodes in the graph.
            This computation can be expensive for large graphs. Must be set to ``True``
            to compute the full unique_triangle relationship.
            Default is ``None``.

        Returns
        -------
        Relationship
            A ternary relationship where each tuple represents a unique
            triangle.

        Raises
        ------
        ValueError
            If ``full`` is not provided.
            If ``full`` is not ``True``.

        Relationship Schema
        -------------------
        ``unique_triangle(node_a, node_b, node_c)``

        * **node_a** (*Node*): The first node in the triangle.
        * **node_b** (*Node*): The second node in the triangle.
        * **node_c** (*Node*): The third node in the triangle.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                |
        | :--------- | :-------- | :------------------- |
        | Undirected | Yes       |                      |
        | Directed   | Yes       |                      |
        | Weighted   | Yes       | Weights are ignored. |

        Notes
        -----
        This relationship contains triples of nodes `(a, b, c)` representing
        unique triangles.

        For **undirected graphs**, uniqueness of each triangle is guaranteed
        because the relationship only contains triples where `a < b < c`.

        For **directed graphs**, the triple `(a, b, c)` represents a triangle
        with directed edges `(a, b)`, `(b, c)`, and `(c, a)`, and is unique up
        to ordering of the nodes and direction of the edges. `unique_triangle`
        only contains triples such that `a < b`, `a < c`, and `b != c`. For
        example, the triples `(1, 2, 3)` and `(1, 3, 2)` represent two unique
        directed triangles.

        Examples
        --------
        **Directed Graph Example**

        >>> from relationalai.semantics import Model, define, select
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a directed graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n3),
        ...     Edge.new(src=n2, dst=n1),
        ...     Edge.new(src=n3, dst=n2),
        ...     Edge.new(src=n3, dst=n4),
        ...     Edge.new(src=n2, dst=n4),
        ... )
        >>>
        >>> # 3. Select the unique triangles and inspect
        >>> a,b,c = Node.ref("a"), Node.ref("b"), Node.ref("c")
        >>> unique_triangle = graph.unique_triangle(full=True)
        >>> select(a.id, b.id, c.id).where(unique_triangle(a, b, c)).inspect()
        ▰▰▰▰ Setup complete
           id  id2  id3
        0   1    3    2

        **Undirected Graph Example**

        >>> from relationalai.semantics import Model, define, select
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges forming two triangles
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n1), # Forms triangle (1,2,3)
        ...     Edge.new(src=n2, dst=n4),
        ...     Edge.new(src=n3, dst=n4),  # Forms triangle (2,3,4)
        ... )
        >>>
        >>> # 3. Select the unique triangles and inspect
        >>> a,b,c = Node.ref("a"), Node.ref("b"), Node.ref("c")
        >>> unique_triangle = graph.unique_triangle(full=True)
        >>> select(a.id, b.id, c.id).where(unique_triangle(a, b, c)).inspect()
        ▰▰▰▰ Setup complete
           id  id2  id3
        0   1    2    3
        1   2    3    4

        See Also
        --------
        triangle
        num_triangles
        triangle_count

        """
        # Validate full parameter
        if full is None:
            raise ValueError(
                "Computing unique_triangle for all triplets can be expensive. To confirm "
                "that you would like to compute the full unique_triangle relationship, "
                "please call `unique_triangle(full=True)`. "
                "(Domain constraints are not available for `unique_triangle` at this time. "
                "If you need domain constraints for `unique_triangle`, please reach out.)"
            )

        if full is not True:
            raise ValueError(
                f"Invalid value (`{full}`) for 'full' parameter. Use `full=True` "
                "to compute the full unique_triangle relationship."
            )

        return self._unique_triangle

    @cached_property
    def _unique_triangle(self):
        """Lazily define and cache the self._unique_triangle relationship."""
        _unique_triangle_rel = self._model.Relationship(f"{{node_a:{self._NodeConceptStr}}} and {{node_b:{self._NodeConceptStr}}} and {{node_c:{self._NodeConceptStr}}} form unique triangle")
        _unique_triangle_rel.annotate(annotations.track("graphs", "unique_triangle"))

        node_a, node_b, node_c = self.Node.ref(), self.Node.ref(), self.Node.ref()

        where(
            self._unique_triangle_fragment(node_a, node_b, node_c)
        ).define(_unique_triangle_rel(node_a, node_b, node_c))

        return _unique_triangle_rel

    def _unique_triangle_fragment(self, node_a, node_b, node_c):
        """
        Helper function that returns a fragment, specifically a where clause
        constraining the given triplet of nodes to unique triangles in the graph.
        """
        if self.directed:
            return where(
                self._oriented_edge(node_a, node_b),
                self._no_loop_edge(node_b, node_c),
                self._reversed_oriented_edge(node_c, node_a)
            )
        else:
            return where(
                self._oriented_edge(node_a, node_b),
                self._oriented_edge(node_b, node_c),
                self._oriented_edge(node_a, node_c)
            )

    @cached_property
    def _no_loop_edge(self):
        """Lazily define and cache the self._no_loop_edge (helper, non-public) relationship."""
        _no_loop_edge_rel = self._model.Relationship(f"{{src:{self._NodeConceptStr}}} has nonloop edge to {{dst:{self._NodeConceptStr}}}")

        src, dst = self.Node.ref(), self.Node.ref()
        where(
            self._edge(src, dst),
            src != dst
        ).define(_no_loop_edge_rel(src, dst))

        return _no_loop_edge_rel

    @cached_property
    def _oriented_edge(self):
        """Lazily define and cache the self._oriented_edge (helper, non-public) relationship."""
        _oriented_edge_rel = self._model.Relationship(f"{{src:{self._NodeConceptStr}}} has oriented edge to {{dst:{self._NodeConceptStr}}}")

        src, dst = self.Node.ref(), self.Node.ref()
        where(
            self._edge(src, dst),
            src < dst
        ).define(_oriented_edge_rel(src, dst))

        return _oriented_edge_rel

    @cached_property
    def _reversed_oriented_edge(self):
        """Lazily define and cache the self._reversed_oriented_edge (helper, non-public) relationship."""
        _reversed_oriented_edge_rel = self._model.Relationship(f"{{src:{self._NodeConceptStr}}} has reversed oriented edge to {{dst:{self._NodeConceptStr}}}")

        src, dst = self.Node.ref(), self.Node.ref()
        where(
            self._edge(src, dst),
            src > dst
        ).define(_reversed_oriented_edge_rel(src, dst))

        return _reversed_oriented_edge_rel


    @include_in_docs
    def num_triangles(self):
        """Returns a unary relationship containing the total number of unique triangles in the graph.

        This method counts the number of unique triangles as defined by the
        `unique_triangle` relationship, which has different uniqueness
        constraints for directed and undirected graphs.

        Returns
        -------
        Relationship
            A unary relationship containing the total number of unique
            triangles in the graph.

        Relationship Schema
        -------------------
        ``num_triangles(count)``

        * **count** (*Integer*): The total number of unique triangles in the graph.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                |
        | :--------- | :-------- | :------------------- |
        | Undirected | Yes       |                      |
        | Directed   | Yes       |                      |
        | Weighted   | Yes       | Weights are ignored. |

        Examples
        --------
        >>> from relationalai.semantics import Model, define
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a directed graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n3),
        ...     Edge.new(src=n2, dst=n1),
        ...     Edge.new(src=n3, dst=n2),
        ...     Edge.new(src=n3, dst=n4),
        ...     Edge.new(src=n1, dst=n4),
        ... )
        >>>
        >>> # 3. Inspect the number of unique triangles
        >>> graph.num_triangles().inspect()
        ▰▰▰▰ Setup complete
           int
        0    1

        See Also
        --------
        triangle
        unique_triangle
        triangle_count

        """
        return self._num_triangles

    @cached_property
    def _num_triangles(self):
        """Lazily define and cache the self._num_triangles relationship."""
        _num_triangles_rel = self._model.Relationship("The graph has {num_triangles:Integer} triangles")
        _num_triangles_rel.annotate(annotations.track("graphs", "num_triangles"))

        _num_triangles = Integer.ref()
        node_a, node_b, node_c = self.Node.ref(), self.Node.ref(), self.Node.ref()

        where(
            _num_triangles := count(
                node_a, node_b, node_c
            ).where(
                self._unique_triangle_fragment(node_a, node_b, node_c)
            ) | 0,
        ).define(_num_triangles_rel(_num_triangles))

        return _num_triangles_rel


    @include_in_docs
    def triangle_count(self, *, of: Optional[Relationship] = None):
        """Returns a binary relationship containing the number of unique triangles each node belongs to.

        A triangle is a set of three nodes where each node has a directed
        or undirected edge to the other two nodes, forming a 3-cycle.

        Parameters
        ----------
        of : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the domain of the triangle count computation: only
            triangle counts of nodes in this relationship are computed and returned.

        Returns
        -------
        Relationship
            A binary relationship where each tuple represents a node and the
            number of unique triangles it is a part of.

        Relationship Schema
        -------------------
        ``triangle_count(node, count)``

        * **node** (*Node*): The node.
        * **count** (*Integer*): The number of unique triangles the node belongs to.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                |
        | :--------- | :-------- | :------------------- |
        | Undirected | Yes       |                      |
        | Directed   | Yes       |                      |
        | Weighted   | Yes       | Weights are ignored. |

        Examples
        --------
        >>> from relationalai.semantics import Model, define, select, Integer
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a directed graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4, n5 = [Node.new(id=i) for i in range(1, 6)]
        >>> define(n1, n2, n3, n4, n5)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n2, dst=n4),
        ...     Edge.new(src=n3, dst=n1),
        ...     Edge.new(src=n3, dst=n4),
        ...     Edge.new(src=n5, dst=n1),
        ... )
        >>>
        >>> # 3. Select the triangle count for each node and inspect
        >>> node, count = Node.ref("node"), Integer.ref("count")
        >>> triangle_count = graph.triangle_count()
        >>> select(node.id, count).where(triangle_count(node, count)).inspect()
        ▰▰▰▰ Setup complete
           id  count
        0   1      1
        1   2      1
        2   3      1
        3   4      0
        4   5      0

        >>> # 4. Use 'of' parameter to constrain the set of nodes to compute triangle counts of
        >>> # Define a subset containing only nodes 1 and 3
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(union(node.id == 1, node.id == 3)).define(subset(node))
        >>>
        >>> # Get triangle counts only of nodes in the subset
        >>> constrained_triangle_count = graph.triangle_count(of=subset)
        >>> select(node.id, count).where(constrained_triangle_count(node, count)).inspect()
        ▰▰▰▰ Setup complete
           id  count
        0   1      1
        1   3      1

        Notes
        -----
        The ``triangle_count()`` method, called with no parameters, computes and caches
        the full triangle count relationship, providing efficient reuse across multiple
        calls to ``triangle_count()``. In contrast, ``triangle_count(of=subset)`` computes a
        constrained relationship specific to the passed-in ``subset`` and that
        call site. When a significant fraction of the triangle count relation is needed
        across a program, ``triangle_count()`` is typically more efficient; this is the
        typical case. Use ``triangle_count(of=subset)`` only when small subsets of the
        triangle count relationship are needed collectively across the program.

        See Also
        --------
        triangle
        unique_triangle
        num_triangles

        """
        if of is not None:
            self._validate_node_subset_parameter('of', of)
            return self._triangle_count_of(of)
        return self._triangle_count

    @cached_property
    def _triangle_count(self):
        """Lazily define and cache the self._triangle_count relationship."""
        _triangle_count_rel = self._create_triangle_count_relationship(node_subset=None)
        _triangle_count_rel.annotate(annotations.track("graphs", "triangle_count"))
        return _triangle_count_rel

    def _triangle_count_of(self, node_subset: Relationship):
        """
        Create a triangle count relationship constrained to the subset of nodes
        in `node_subset`. Note this relationship is not cached; it is
        specific to the callsite.
        """
        _triangle_count_rel = self._create_triangle_count_relationship(node_subset=node_subset)
        _triangle_count_rel.annotate(annotations.track("graphs", "triangle_count_of"))
        return _triangle_count_rel

    def _create_triangle_count_relationship(self, *, node_subset: Optional[Relationship]):
        """Create a triangle count relationship, optionally constrained to a subset of nodes."""
        _triangle_count_rel = self._model.Relationship(f"{{node:{self._NodeConceptStr}}} belongs to {{count:Integer}} triangles")

        if node_subset is None:
            node_constraint = [] # No constraint on nodes.
        else:
            node_constraint = [node_subset(self.Node)]  # Nodes constrained to given subset.

        where(
            *node_constraint,
            _count := self._nonzero_triangle_count_fragment(self.Node) | 0
        ).define(_triangle_count_rel(self.Node, _count))

        return _triangle_count_rel

    def _nonzero_triangle_count_fragment(self, node):
        """
        Helper function that returns a fragment, specifically a count
        of the number of triangles containing the given node.
        """
        node_a, node_b = self.Node.ref(), self.Node.ref()

        if self.directed:
            # For directed graphs, count triangles with any circulation.
            # For example, count both (1-2-3-1) and (1-3-2-1) as triangles.
            return count(node_a, node_b).per(node).where(
                self._no_loop_edge(node, node_a),
                self._no_loop_edge(node_a, node_b),
                self._no_loop_edge(node_b, node)
            )
        else:
            # For undirected graphs, count triangles with a specific circulation.
            # For example, count (1-2-3-1) but not (1-3-2-1) as a triangle.
            return count(node_a, node_b).per(node).where(
                self._no_loop_edge(node, node_a),
                self._oriented_edge(node_a, node_b),
                self._no_loop_edge(node, node_b)
            )


    def triangle_community(self):
        """Returns a binary relationship that partitions nodes into communities based on the graph's triangle structure.

        This method finds K-clique communities (with K=3) using the
        percolation method.

        Returns
        -------
        Relationship
            A binary relationship where each tuple represents a node and its
            community assignment.

        Relationship Schema
        -------------------
        ``triangle_community(node, community_label)``

        * **node** (*Node*): The node.
        * **community_label** (*Integer*): The node's community assignment.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                |
        | :--------- | :-------- | :------------------- |
        | Undirected | Yes       |                      |
        | Directed   | No        |                      |
        | Weighted   | Yes       | Weights are ignored. |

        Notes
        -----
        This method finds K-clique communities (with `K = 3`) using the
        `percolation method <https://en.wikipedia.org/wiki/Clique_percolation_method>`_.
        A triangle community is the union of nodes of all triangles that can
        be reached from one another by adjacent triangles---that is,
        triangles that share exactly two nodes.

        For a given undirected graph `G`, the algorithm works as follows:
        First, all triangles in `G` are enumerated and assigned a unique
        label, each of which becomes a node in a new graph called the
        **clique-graph** of `G`, where two nodes in this new graph are
        connected by an edge if the corresponding triangles share exactly two
        nodes, i.e., the corresponding triangles are adjacent in `G`. Next,
        the connected components of the clique-graph of `G` are computed and
        then assigned community labels. Finally, each node in the original
        graph is assigned the community label of the triangle to which it
        belongs. Nodes that are not contained in any triangle are not
        assigned a community label. This algorithm is not supported for
        directed graphs since adjacency is not defined for directed
        triangles.

        Examples
        --------
        >>> from relationalai.semantics import Model, define, select, Integer
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4, n5, n6 = [Node.new(id=i) for i in range(1, 7)]
        >>> define(n1, n2, n3, n4, n5, n6)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n1, dst=n3),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n4),
        ...     Edge.new(src=n4, dst=n5),
        ...     Edge.new(src=n4, dst=n6),
        ...     Edge.new(src=n5, dst=n6)
        ... )
        >>>
        >>> # 3. Select the community label for each node and inspect
        >>> node, label = Node.ref("node"), Integer.ref("label")
        >>> triangle_community = graph.triangle_community()
        >>> select(node.id, label).where(triangle_community(node, label)).inspect()
        # The output will show each node in a triangle mapped to a community:
        # (1, 1)
        # (2, 1)
        # (3, 1)
        # (4, 2)
        # (5, 2)
        # (6, 2)

        """
        raise NotImplementedError("`triangle_community` is not yet implemented")


    @include_in_docs
    def local_clustering_coefficient(self, *, of: Optional[Relationship] = None):
        """Returns a binary relationship containing the local clustering coefficient of each node.

        The local clustering coefficient quantifies how close a node's neighbors
        are to forming a clique (a complete subgraph). The coefficient ranges
        from 0.0 to 1.0, where 0.0 indicates none of the neighbors have edges
        directly connecting them, and 1.0 indicates all neighbors have edges
        directly connecting them.

        Parameters
        ----------
        of : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the domain of the local clustering coefficient
            computation: only coefficients of nodes in this relationship are
            computed and returned.

        Returns
        -------
        Relationship
            A binary relationship where each tuple represents a node and its
            local clustering coefficient.

        Raises
        ------
        NotImplementedError
            If the graph is directed.

        Relationship Schema
        -------------------
        ``local_clustering_coefficient(node, coefficient)``

        * **node** (*Node*): The node.
        * **coefficient** (*Float*): The local clustering coefficient of the node.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes              |
        | :--------- | :-------- | :----------------- |
        | Undirected | Yes       |                    |
        | Directed   | No        | Undirected only.   |
        | Weighted   | Yes       | Weights are ignored. |

        Examples
        --------
        >>> from relationalai.semantics import Model, define, select, Float
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4, n5 = [Node.new(id=i) for i in range(1, 6)]
        >>> define(n1, n2, n3, n4, n5)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n1, dst=n3),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n4),
        ...     Edge.new(src=n4, dst=n5),
        ...     Edge.new(src=n2, dst=n4),
        ...     Edge.new(src=n3, dst=n5),
        ... )
        >>>
        >>> # 3. Select the local clustering coefficient for each node
        >>> node, coeff = Node.ref("node"), Float.ref("coeff")
        >>> lcc = graph.local_clustering_coefficient()
        >>> select(node.id, coeff).where(lcc(node, coeff)).inspect()
        ▰▰▰▰ Setup complete
           id     coeff
        0   1  1.000000
        1   2  0.666667
        2   3  0.666667
        3   4  0.333333
        4   5  0.000000

        >>> # 4. Use 'of' parameter to constrain the set of nodes to compute local clustering coefficients of
        >>> # Define a subset containing only nodes 1 and 3
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(union(node.id == 1, node.id == 3)).define(subset(node))
        >>>
        >>> # Get local clustering coefficients only of nodes in the subset
        >>> constrained_lcc = graph.local_clustering_coefficient(of=subset)
        >>> select(node.id, coeff).where(constrained_lcc(node, coeff)).inspect()
        ▰▰▰▰ Setup complete
           id     coeff
        0   1  1.000000
        1   3  0.666667

        Notes
        -----
        The local clustering coefficient for node `v` is::

            (2 * num_neighbor_edges(v)) / (ext_degree(v) * (ext_degree(v) - 1))

        where `num_neighbor_edges(v)` is the number of edges between
        the neighbors of node `v`, and `ext_degree(v)` is the degree of the
        node excluding self-loops. If `ext_degree(v)` is less than 2,
        the local clustering coefficient is 0.0.

        The ``local_clustering_coefficient()`` method, called with no parameters, computes
        and caches the full local clustering coefficient relationship, providing efficient
        reuse across multiple calls to ``local_clustering_coefficient()``. In contrast,
        ``local_clustering_coefficient(of=subset)`` computes a constrained relationship
        specific to the passed-in ``subset`` and that call site. When a significant fraction
        of the local clustering coefficient relation is needed across a program,
        ``local_clustering_coefficient()`` is typically more efficient; this is the typical
        case. Use ``local_clustering_coefficient(of=subset)`` only when small subsets of the
        local clustering coefficient relationship are needed collectively across the program.


        See Also
        --------
        average_clustering_coefficient

        """
        if self.directed:
            # TODO: Eventually make this error more similar to
            #   the corresponding error emitted from the pyrel graphlib wrapper.
            raise NotImplementedError(
                "`local_clustering_coefficient` is not applicable to directed graphs"
            )

        if of is not None:
            self._validate_node_subset_parameter('of', of)
            return self._local_clustering_coefficient_of(of)
        return self._local_clustering_coefficient

    @cached_property
    def _local_clustering_coefficient(self):
        """Lazily define and cache the self._local_clustering_coefficient relationship."""
        _local_clustering_coefficient_rel = self._create_local_clustering_coefficient_relationship(node_subset=None)
        _local_clustering_coefficient_rel.annotate(annotations.track("graphs", "local_clustering_coefficient"))
        return _local_clustering_coefficient_rel

    def _local_clustering_coefficient_of(self, node_subset: Relationship):
        """
        Create a local clustering coefficient relationship constrained to the subset of nodes
        in `node_subset`. Note this relationship is not cached; it is
        specific to the callsite.
        """
        _local_clustering_coefficient_rel = self._create_local_clustering_coefficient_relationship(node_subset=node_subset)
        _local_clustering_coefficient_rel.annotate(annotations.track("graphs", "local_clustering_coefficient_of"))
        return _local_clustering_coefficient_rel

    def _create_local_clustering_coefficient_relationship(self, *, node_subset: Optional[Relationship]):
        """Create a local clustering coefficient relationship, optionally constrained to a subset of nodes."""
        _local_clustering_coefficient_rel = self._model.Relationship(f"{{node:{self._NodeConceptStr}}} has local clustering coefficient {{coefficient:Float}}")

        node = self.Node.ref()

        if node_subset is None:
            degree_no_self_rel = self._degree_no_self
            triangle_count_rel = self._triangle_count
            node_constraint = []  # No constraint on nodes.
        else:
            degree_no_self_rel = self._degree_no_self_of(node_subset)
            triangle_count_rel = self._triangle_count_of(node_subset)
            node_constraint = [node_subset(node)]  # Nodes constrained to given subset.

        degree_no_self = Integer.ref()
        triangle_count = Integer.ref()
        where(
            *node_constraint,
            _lcc := where(
                degree_no_self_rel(node, degree_no_self),
                triangle_count_rel(node, triangle_count),
                degree_no_self > 1
            ).select(
                2.0 * triangle_count / (degree_no_self * (degree_no_self - 1.0))
            ) | 0.0,
        ).define(_local_clustering_coefficient_rel(node, _lcc))

        return _local_clustering_coefficient_rel

    @cached_property
    def _degree_no_self(self):
        """
        Lazily define and cache the self._degree_no_self relationship,
        a non-public helper for degree and local_clustering_coefficient.
        """
        return self._create_degree_no_self_relationship(node_subset=None)

    def _degree_no_self_of(self, node_subset: Relationship):
        """
        Create a self-loop-exclusive degree relationship constrained to
        the subset of nodes in `node_subset`. Note this relationship
        is not cached; it is specific to the callsite.
        """
        return self._create_degree_no_self_relationship(node_subset=node_subset)

    def _create_degree_no_self_relationship(self, *, node_subset: Optional[Relationship]):
        """
        Create a self-loop-exclusive degree relationship,
        optionally constrained to a subset of nodes.
        """
        _degree_no_self_rel = self._model.Relationship(f"{{node:{self._NodeConceptStr}}} has degree excluding self loops {{num:Integer}}")

        node, neighbor = self.Node.ref(), self.Node.ref()

        if node_subset is None:
            node_constraint = []  # No constraint on nodes.
        else:
            node_constraint = [node_subset(node)]  # Nodes constrained to given subset.

        where(
            *node_constraint,
            _dns := count(neighbor).per(node).where(self._no_loop_edge(node, neighbor)) | 0,
        ).define(_degree_no_self_rel(node, _dns))

        return _degree_no_self_rel


    @include_in_docs
    def average_clustering_coefficient(self):
        """Returns a unary relationship containing the average clustering coefficient of the graph.

        The average clustering coefficient is the average of the local
        clustering coefficients of the nodes in a graph.

        Returns
        -------
        Relationship
            A unary relationship containing the average clustering coefficient
            of the graph.

        Raises
        ------
        NotImplementedError
            If the graph is directed.

        Relationship Schema
        -------------------
        ``average_clustering_coefficient(coefficient)``

        * **coefficient** (*Float*): The average clustering coefficient of the graph.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes              |
        | :--------- | :-------- | :----------------- |
        | Undirected | Yes       |                    |
        | Directed   | No        | Undirected only.   |
        | Weighted   | Yes       | Weights are ignored. |

        Examples
        --------
        >>> from relationalai.semantics import Model, define
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4, n5 = [Node.new(id=i) for i in range(1, 6)]
        >>> define(n1, n2, n3, n4, n5)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n1, dst=n3),
        ...     Edge.new(src=n1, dst=n4),
        ...     Edge.new(src=n1, dst=n5),
        ...     Edge.new(src=n2, dst=n3),
        ... )
        >>>
        >>> # 3. Inspect the average clustering coefficient
        >>> graph.average_clustering_coefficient().inspect()
        ▰▰▰▰ Setup complete
              float
        0  0.433333

        See Also
        --------
        local_clustering_coefficient

        """
        if self.directed:
            raise NotImplementedError(
                "`average_clustering_coefficient` is not applicable to directed graphs"
            )
        return self._average_clustering_coefficient

    @cached_property
    def _average_clustering_coefficient(self):
        """
        Lazily define and cache the self._average_clustering_coefficient relationship,
        which only applies to undirected graphs.
        """
        _average_clustering_coefficient_rel = self._model.Relationship("The graph has average clustering coefficient {{coefficient:Float}}")
        _average_clustering_coefficient_rel.annotate(annotations.track("graphs", "average_clustering_coefficient"))

        if self.directed:
            raise NotImplementedError(
                "`average_clustering_coefficient` is not defined for directed graphs."
            )

        node = self.Node.ref()
        coefficient = Float.ref()
        where(
            _avg_coefficient := avg(node, coefficient).where(
                    self._local_clustering_coefficient(node, coefficient)
                ) | 0.0
        ).define(_average_clustering_coefficient_rel(_avg_coefficient))

        return _average_clustering_coefficient_rel


    @include_in_docs
    def reachable_from(self):
        """Returns a binary relationship of all pairs of nodes (u, v) where v is reachable from u.

        .. deprecated::
            The ``reachable_from`` method is deprecated and will be removed in a
            future release. Please use :meth:`reachable` instead, which provides
            the same functionality with additional domain constraint options.

        A node `v` is considered reachable from a node `u` if there is a path
        of edges from `u` to `v`.

        Returns
        -------
        Relationship
            A binary relationship where each tuple represents a start node and a
            node that is reachable from it.

        Relationship Schema
        -------------------
        ``reachable_from(start_node, end_node)``

        * **start_node** (*Node*): The node from which the path originates.
        * **end_node** (*Node*): The node that is reachable from the start node.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                |
        | :--------- | :-------- | :------------------- |
        | Undirected | Yes       |                      |
        | Directed   | Yes       |                      |
        | Weighted   | Yes       | Weights are ignored. |

        Notes
        -----
        There is a slight difference between `transitive closure` and
        `reachable_from`. The transitive closure of a binary relation E is the
        smallest relation that contains E and is transitive. When E is the
        edge set of a graph, the transitive closure of E does not include
        (u, u) if u is isolated. `reachable_from` is a different binary
        relation in which any node u is always reachable from u. In
        particular, `transitive closure` is a more general concept than
        `reachable_from`.

        Examples
        --------
        **Directed Graph Example**

        >>> from relationalai.semantics import Model, define, select
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a directed graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3 = [Node.new(id=i) for i in range(1, 4)]
        >>> define(n1, n2, n3)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n3, dst=n2),
        ... )
        >>>
        >>> # 3. Select all reachable pairs and inspect
        >>> start_node, end_node = Node.ref("start"), Node.ref("end")
        >>> reachable_from = graph.reachable_from()
        >>> select(start_node.id, end_node.id).where(reachable_from(start_node, end_node)).inspect()
        ▰▰▰▰ Setup complete
           id  id2
        0   1    1
        1   1    2
        2   2    2
        3   3    2
        4   3    3


        **Undirected Graph Example**

        >>> from relationalai.semantics import Model, define, select
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define the same nodes and edges
        >>> n1, n2, n3 = [Node.new(id=i) for i in range(1, 4)]
        >>> define(n1, n2, n3)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n3, dst=n2),
        ... )
        >>>
        >>> # 3. Select all reachable pairs and inspect
        >>> start_node, end_node = Node.ref("start"), Node.ref("end")
        >>> reachable_from = graph.reachable_from()
        >>> select(start_node.id, end_node.id).where(reachable_from(start_node, end_node)).inspect()
        ▰▰▰▰ Setup complete
           id  id2
        0   1    1
        1   1    2
        2   1    3
        3   2    1
        4   2    2
        5   2    3
        6   3    1
        7   3    2
        8   3    3

        See Also
        --------
        reachable

        """
        warnings.warn(
            "The 'reachable_from' method is deprecated and will be removed in a future release. "
            "Please use 'reachable' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.reachable(full=True)


    @include_in_docs
    def reachable(
        self,
        *,
        full: Optional[bool] = None,
        from_: Optional[Relationship] = None,
        to: Optional[Relationship] = None,
        between: Optional[Relationship] = None,
    ):
        """Returns a binary relationship of pairs of nodes (u, v) where v is reachable from u.

        A node `v` is considered reachable from a node `u` if there is a path
        of edges from `u` to `v`.

        Parameters
        ----------
        full : bool, optional
            If ``True``, computes reachability for all pairs of nodes in the graph.
            This computation can be expensive for large graphs. Must be set to
            ``True`` to compute the full reachable relationship. Cannot be used
            with other parameters.
        from_ : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the first position of the reachable
            computation: only reachability from nodes in this relationship are
            returned. Cannot be used with other parameters.
        to : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the second position of the reachable
            computation: only reachability to nodes in this relationship are
            returned. Cannot be used with other parameters.
        between : Relationship, optional
            Not yet supported for reachable. If provided, raises an error. If you
            need this capability, please reach out.

        Returns
        -------
        Relationship
            A binary relationship where each tuple represents a node and a
            node that is reachable from it.

        Relationship Schema
        -------------------
        ``reachable(from_node, to_node)``

        * **from_node** (*Node*): The node from which the path originates.
        * **to_node** (*Node*): The node that is reachable from the first node.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                |
        | :--------- | :-------- | :------------------- |
        | Undirected | Yes       |                      |
        | Directed   | Yes       |                      |
        | Weighted   | Yes       | Weights are ignored. |

        Notes
        -----
        The ``reachable(full=True)`` method computes and caches the full
        reachable relationship, providing efficient reuse across multiple calls. In
        contrast, ``reachable(from_=subset)`` or ``reachable(to=subset)``
        compute constrained relationships specific to the passed-in subset and call
        site. When a significant fraction of the reachable relation is needed,
        ``reachable(full=True)`` is typically more efficient. Use constrained
        variants only when small subsets are needed.

        In directed graphs, the ``reachable`` relationship is asymmetric: node B
        may be reachable from node A without node A being reachable from node B. This
        asymmetry means that ``from_`` and ``to`` parameters have distinct,
        non-interchangeable meanings.

        **Important:** Simultaneous use of ``from_`` and ``to`` parameters is not
        yet supported. The ``between`` parameter is also not yet supported. If
        you need these capabilities, please reach out.

        There is a slight difference between `transitive closure` and
        `reachable`. The transitive closure of a binary relation E is the
        smallest relation that contains E and is transitive. When E is the
        edge set of a graph, the transitive closure of E does not include
        (u, u) if u is isolated. `reachable` is a different binary
        relation in which any node u is always reachable from u. In
        particular, `transitive closure` is a more general concept than
        `reachable`.

        Examples
        --------
        **Directed Graph Example**

        >>> from relationalai.semantics import Model, define, select
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a directed graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3 = [Node.new(id=i) for i in range(1, 4)]
        >>> define(n1, n2, n3)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n3, dst=n2),
        ... )
        >>>
        >>> # 3. Select all reachable pairs and inspect
        >>> from_node, to_node = Node.ref("start"), Node.ref("end")
        >>> reachable = graph.reachable(full=True)
        >>> select(from_node.id, to_node.id).where(reachable(from_node, to_node)).inspect()
        ▰▰▰▰ Setup complete
           id  id2
        0   1    1
        1   1    2
        2   2    2
        3   3    2
        4   3    3

        >>> # 4. Use 'from_' parameter to get reachability from specific nodes
        >>> # Define a subset containing nodes 1 and 3
        >>> from relationalai.semantics import union, where
        >>> subset = model.Relationship(f"{{node:{Node}}} is in from subset")
        >>> node = Node.ref()
        >>> where(union(node.id == 1, node.id == 3)).define(subset(node))
        >>>
        >>> # Get reachability from nodes in the subset to all other nodes
        >>> reachable_from = graph.reachable(from_=subset)
        >>> select(from_node.id, to_node.id).where(
        ...     reachable_from(from_node, to_node)
        ... ).inspect()
        ▰▰▰▰ Setup complete
           id  id2
        0   1    1
        1   1    2
        2   3    2
        3   3    3

        >>> # 5. Use 'to' parameter to get reachability to specific nodes
        >>> # Define a different subset containing node 2
        >>> to_subset = model.Relationship(f"{{node:{Node}}} is in to subset")
        >>> node = Node.ref()
        >>> where(node.id == 2).define(to_subset(node))
        >>>
        >>> # Get reachability from all nodes to node 2
        >>> reachable_to = graph.reachable(to=to_subset)
        >>> select(from_node.id, to_node.id).where(
        ...     reachable_to(from_node, to_node)
        ... ).inspect()
        ▰▰▰▰ Setup complete
           id  id2
        0   1    2
        1   2    2
        2   3    2


        **Undirected Graph Example**

        >>> from relationalai.semantics import Model, define, select
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define the same nodes and edges
        >>> n1, n2, n3 = [Node.new(id=i) for i in range(1, 4)]
        >>> define(n1, n2, n3)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n3, dst=n2),
        ... )
        >>>
        >>> # 3. Select all reachable pairs and inspect
        >>> from_node, to_node = Node.ref("start"), Node.ref("end")
        >>> reachable = graph.reachable(full=True)
        >>> select(from_node.id, to_node.id).where(reachable(from_node, to_node)).inspect()
        ▰▰▰▰ Setup complete
           id  id2
        0   1    1
        1   1    2
        2   1    3
        3   2    1
        4   2    2
        5   2    3
        6   3    1
        7   3    2
        8   3    3

        """
        # Validate domain constraint parameters (reachable is asymmetric).
        symmetric = False
        self._validate_domain_constraint_parameters(
            'reachable', symmetric, full, from_, to, between
        )

        # Reachable-specific validation: between is not yet supported.
        if between is not None:
            raise ValueError(
                "The 'between' parameter is not yet supported for reachable. "
                "Use 'full=True' for all-pairs reachability, or 'from_'/'to' to "
                "constrain by position. If you need 'between' support for reachable, "
                "please reach out."
            )

        # Reachable-specific validation: from_+to combination is not yet supported.
        if from_ is not None and to is not None:
            raise ValueError(
                "Simultaneous use of 'from_' and 'to' is not yet supported for reachable. "
                "Use 'from_=subset' to constrain start nodes, 'to=subset' to constrain "
                "end nodes, or 'full=True' for all pairs. If you need the 'from_' and 'to' "
                "combination for reachable, please reach out."
            )

        # At this point, exactly one of `full`, `from_`, or `to` has been provided.

        if full is not None:
            return self._reachable

        if from_ is not None:
            self._validate_node_subset_parameter('from_', from_)
            return self._reachable_from(from_)

        if to is not None:
            self._validate_node_subset_parameter('to', to)
            return self._reachable_to(to)

    @cached_property
    def _reachable(self):
        """Lazily define and cache the self._reachable relationship."""
        _reachable_rel = self._create_reachable_relationship()
        _reachable_rel.annotate(annotations.track("graphs", "reachable"))
        return _reachable_rel

    def _reachable_from(self, node_subset_from: Relationship):
        """
        Create a reachable relationship with the first position constrained to
        nodes in `node_subset_from`. This computes reachability from nodes in
        the subset to all other nodes. Note this relationship
        is not cached; it is specific to the callsite.
        """
        _reachable_rel = self._create_reachable_relationship(
            node_subset_from=node_subset_from,
        )
        _reachable_rel.annotate(annotations.track("graphs", "reachable_from"))
        return _reachable_rel

    def _reachable_to(self, node_subset_to: Relationship):
        """
        Create a reachable relationship with the second position constrained to
        nodes in `node_subset_to`. This computes reachability from all nodes to
        nodes in the subset. Note this relationship
        is not cached; it is specific to the callsite.
        """
        _reachable_rel = self._create_reachable_relationship(
            node_subset_to=node_subset_to
        )
        _reachable_rel.annotate(annotations.track("graphs", "reachable_to"))
        return _reachable_rel

    def _create_reachable_relationship(
        self,
        *,
        node_subset_from: Optional[Relationship] = None,
        node_subset_to: Optional[Relationship] = None,
    ):
        """
        Create a reachable relationship, optionally constrained to node subsets.

        Parameters
        ----------
        node_subset_from : Relationship or None
            If provided, constrains the first position to this subset.
        node_subset_to : Relationship or None
            If provided, constrains the second position to this subset.

        Returns
        -------
        Relationship
            A binary relationship mapping (from_node, to_node).
        """
        # NOTE: In the constrained cases, we must compute over the full reach
        #   {from xor to}, depending on the constraint, the nodes in the provided subset,
        #   and _only_ over that reach.

        # A reach relation over the reach {from xor to} the nodes in the subset.
        _reachable_rel = self._model.Relationship(
            f"{{node_a:{self._NodeConceptStr}}} reaches {{node_b:{self._NodeConceptStr}}}"
        )

        # The logic below computes the reach by repeatedly extending
        # known reachability to neighbors; this snippet drives that,
        # with propagation direction depending on the constraint mode.
        node_a, node_b, node_c = self.Node.ref(), self.Node.ref(), self.Node.ref()
        if node_subset_to is None:
            # Either of `full` or `from_` modes; propagate reach forward for both.
            # (`full` mode uses forward propagation as it may be slightly more efficient,
            # though backward propagation also works in principle.)
            extension_rule = where(
                _reachable_rel(node_a, node_b),
                self._edge(node_b, node_c),
            ).select(node_a, node_c)
        else:
            # `to` mode; propagate reach backward.
            extension_rule = where(
                _reachable_rel(node_b, node_c),
                self._edge(node_a, node_b),
            ).select(node_a, node_c)
            # NOTE: The optimizer may generate an index on _edge for the above;
            #   it may be best to use a cached reversed edge relationship instead,
            #   given it's useful elsewhere and that may yield reuse (and more reliably
            #   good query plans, possibly).

        # The set of nodes from which to propagate reach.
        node = self.Node.ref() # node is used (coupled) below.
        # Binding origin_nodes_constraint unconditionally for
        # the unconstrained case and then overriding if necessary
        # appeases the type checker, which otherwise thinks
        # it may be unbound below.
        origin_nodes_constraint = node
        if node_subset_from is not None:
            origin_nodes_constraint = node_subset_from(node)
        elif node_subset_to is not None:
            origin_nodes_constraint = node_subset_to(node)

        # Generate union of reach implications between node_x and node_y:
        node_x, node_y = union(
            # A node is always reachable from itself.
            where(origin_nodes_constraint).select(node, node),
            # Reachability can be extended to neighbors.
            # (Note that this part of the rule also drives the reach.)
            extension_rule,
        )
        # Define the reach relation recursively.
        define(
            _reachable_rel(node_x, node_y)
        )

        return _reachable_rel


    @include_in_docs
    def distance(
        self,
        *,
        full: Optional[bool] = None,
        from_: Optional[Relationship] = None,
        to: Optional[Relationship] = None,
        between: Optional[Relationship] = None,
    ):
        """Returns a ternary relationship containing
        the shortest path length between pairs of nodes.

        This method computes the shortest path length between all pairs of
        reachable nodes. The calculation depends on whether the graph is
        weighted:

        * For **unweighted** graphs, the length is the number of edges in the
            shortest path.
        * For **weighted** graphs, the length is the sum of edge weights
            along the shortest path. Edge weights are assumed to be non-negative.

        Parameters
        ----------
        full : bool, optional
            If ``True``, computes distances for all pairs of nodes in the graph.
            This computation can be expensive for large graphs. Must be set to
            ``True`` to compute the full distance relationship. Cannot be used
            with other parameters.
        from_ : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the first position (start_node) of the distance
            computation: only distances from nodes in this relationship are
            returned. Cannot be used with other parameters.
        to : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the second position (end_node) of the distance
            computation: only distances to nodes in this relationship are
            returned. Cannot be used with other parameters.
        between : Relationship, optional
            Not yet supported for distance. If provided, raises an error. If you
            need this capability, please reach out.

        Returns
        -------
        Relationship
            A ternary relationship where each tuple represents a pair of nodes
            and the shortest path length between them.

        Relationship Schema
        -------------------
        ``distance(start_node, end_node, length)``

        * **start_node** (*Node*): The start node of the path.
        * **end_node** (*Node*): The end node of the path.
        * **length** (*Integer* or *Float*): The shortest path length, returned
        as an Integer for unweighted graphs and a Float for weighted graphs.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                                      |
        | :--------- | :-------- | :----------------------------------------- |
        | Undirected | Yes       |                                            |
        | Directed   | Yes       |                                            |
        | Weighted   | Yes       | The calculation uses edge weights.         |

        Notes
        -----
        The ``distance(full=True)`` method computes and caches the full distance
        relationship, providing efficient reuse across multiple calls. In contrast,
        ``distance(from_=subset)`` or ``distance(to=subset)`` compute constrained
        relationships specific to the passed-in subset and call site. When a
        significant fraction of the distance relation is needed, ``distance(full=True)``
        is typically more efficient. Use constrained variants only when small
        subsets are needed.

        In directed graphs, the ``distance`` relationship is asymmetric: the
        distance from node A to node B may differ from the distance from node B
        to node A. This asymmetry means that ``from_`` and ``to`` parameters
        have distinct, non-interchangeable meanings.

        **Important:** Simultaneous use of ``from_`` and ``to`` parameters is not
        yet supported. The ``between`` parameter is also not yet supported. If
        you need these capabilities, please reach out.

        Examples
        --------
        **Unweighted Graph Example**

        >>> from relationalai.semantics import Model, define, select, union, where, Integer
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an unweighted, undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n2, dst=n4),
        ... )
        >>>
        >>> # 3. Select the shortest path length between all pairs of nodes
        >>> start, end = Node.ref("start"), Node.ref("end")
        >>> length = Integer.ref("length")
        >>> dist = graph.distance(full=True)
        >>> select(start.id, end.id, length).where(dist(start, end, length)).inspect()
        ▰▰▰▰ Setup complete
            id  id2  length
        0    1    1       0
        1    1    2       1
        2    1    3       2
        3    1    4       2
        4    2    1       1
        5    2    2       0
        6    2    3       1
        7    2    4       1
        8    3    1       2
        9    3    2       1
        10   3    3       0
        11   3    4       2
        12   4    1       2
        13   4    2       1
        14   4    3       2
        15   4    4       0

        >>> # 4. Use 'from_' parameter to get distances from specific nodes
        >>> # Define a subset containing nodes 1 and 3
        >>> subset = model.Relationship(f"{{node:{Node}}} is in from subset")
        >>> node = Node.ref()
        >>> where(union(node.id == 1, node.id == 3)).define(subset(node))
        >>>
        >>> # Get distances from nodes in the subset to all other nodes
        >>> dist_from = graph.distance(from_=subset)
        >>> select(start.id, end.id, length).where(
        ...     dist_from(start, end, length)
        ... ).inspect()
        ▰▰▰▰ Setup complete
            id  id2  length
        0    1    1       0
        1    1    2       1
        2    1    3       2
        3    1    4       2
        4    3    1       2
        5    3    2       1
        6    3    3       0
        7    3    4       2

        >>> # 5. Use 'to' parameter to get distances to specific nodes
        >>> # Define a different subset containing node 4
        >>> to_subset = model.Relationship(f"{{node:{Node}}} is in to subset")
        >>> node = Node.ref()
        >>> where(node.id == 4).define(to_subset(node))
        >>>
        >>> # Get distances from all nodes to node 4
        >>> dist_to = graph.distance(to=to_subset)
        >>> select(start.id, end.id, length).where(
        ...     dist_to(start, end, length)
        ... ).inspect()
        ▰▰▰▰ Setup complete
            id  id2  length
        0    1    4       2
        1    2    4       1
        2    3    4       2
        3    4    4       0


        **Weighted Graph Example**

        >>> from relationalai.semantics import Model, define, select, Float
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a weighted, directed graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=True)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3 = [Node.new(id=i) for i in range(1, 4)]
        >>> define(n1, n2, n3)
        >>> define(
        ...     Edge.new(src=n1, dst=n2, weight=2.0),
        ...     Edge.new(src=n1, dst=n3, weight=0.5),
        ...     Edge.new(src=n2, dst=n1, weight=1.5),
        ... )
        >>>
        >>> # 3. Select the shortest path length between all pairs of nodes
        >>> start, end = Node.ref("start"), Node.ref("end")
        >>> length = Float.ref("length")
        >>> dist = graph.distance(full=True)
        >>> select(start.id, end.id, length).where(dist(start, end, length)).inspect()
        ▰▰▰▰ Setup complete
           id  id2  length
        0   1    1     0.0
        1   1    2     2.0
        2   1    3     0.5
        3   2    1     1.5
        4   2    2     0.0
        5   2    3     2.0
        6   3    3     0.0

        """
        # Validate domain constraint parameters (distance is asymmetric).
        symmetric = False
        self._validate_domain_constraint_parameters(
            'distance', symmetric, full, from_, to, between
        )

        # Distance-specific validation: between is not yet supported.
        if between is not None:
            raise ValueError(
                "The 'between' parameter is not yet supported for distance. "
                "Use 'full=True' for all-pairs distances, or 'from_'/'to' to "
                "constrain by position. If you need 'between' support for distance, "
                "please reach out."
            )

        # Distance-specific validation: from_+to combination is not yet supported.
        if from_ is not None and to is not None:
            raise ValueError(
                "Simultaneous use of 'from_' and 'to' is not yet supported for distance. "
                "Use 'from_=subset' to constrain start nodes, 'to=subset' to constrain "
                "end nodes, or 'full=True' for all pairs. If you need the 'from_' and 'to' "
                "combination for distance, please reach out."
            )

        # At this point, exactly one of `full`, `from_`, or `to` has been provided.

        if full is not None:
            return self._distance

        if from_ is not None:
            self._validate_node_subset_parameter('from_', from_)
            return self._distance_from(from_)

        if to is not None:
            self._validate_node_subset_parameter('to', to)
            return self._distance_to(to)

    @cached_property
    def _distance(self):
        """Lazily define and cache the self._distance relationship."""
        _distance_rel = self._create_distance_relationship()
        _distance_rel.annotate(annotations.track("graphs", "distance"))
        return _distance_rel

    def _distance_from(self, node_subset_from: Relationship):
        """
        Create a distance relationship with the first position constrained to
        nodes in `node_subset_from`. This computes distances from nodes in
        the subset to all other nodes. Note this relationship
        is not cached; it is specific to the callsite.
        """
        _distance_rel = self._create_distance_relationship(
            node_subset_from=node_subset_from,
        )
        _distance_rel.annotate(annotations.track("graphs", "distance_from"))
        return _distance_rel

    def _distance_to(self, node_subset_to: Relationship):
        """
        Create a distance relationship with the second position constrained to
        nodes in `node_subset_to`. This computes distances from all nodes to
        nodes in the subset. Note this relationship
        is not cached; it is specific to the callsite.
        """
        _distance_rel = self._create_distance_relationship(
            node_subset_to=node_subset_to
        )
        _distance_rel.annotate(annotations.track("graphs", "distance_to"))
        return _distance_rel

    def _create_distance_relationship(
        self,
        *,
        node_subset_from: Optional[Relationship] = None,
        node_subset_to: Optional[Relationship] = None,
        weighted: Optional[bool] = None,
    ):
        """
        Create a distance relationship, weighted or unweighted per the graph,
        and optionally constrained to node subsets.

        Parameters
        ----------
        node_subset_from : Relationship or None
            If provided, constrains the first position to this subset.
        node_subset_to : Relationship or None
            If provided, constrains the second position to this subset.

        Returns
        -------
        Relationship
            A ternary relationship mapping (from_node, to_node, distance).
        """
        # NOTE: In the constrained cases, we must compute over the full reach
        #   from xor to (depending on the constraint) the nodes in the provided subset,
        #   and _only_ over that reach. To do so, the logic below simultaneously
        #   computes the appropriate reach of the nodes in the provided subset
        #   (in `_distance_reach_rel`) while computing distances.

        if weighted is None:
            weighted = self.weighted

        dist_type = Float if weighted else Integer

        # A distance relation over the appropriate reach of the nodes in the subset.
        _distance_reach_rel = self._model.Relationship(
            f"{{node_u:{self._NodeConceptStr}}} and {{node_v:{self._NodeConceptStr}}} have a distance of {{d:{dist_type}}}"
        )

        # The logic below computes the reach and distances by repeatedly extending
        # known distances to neighbors; this snippet drives that, with propagation
        # direction depending on the constraint mode.
        node_u, node_v, neighbor = self.Node.ref(), self.Node.ref(), self.Node.ref()
        uv_dist, step_dist, neighbor_dist = dist_type.ref(), dist_type.ref(), dist_type.ref()
        if node_subset_to is None:
            # Either of `full` or `from` modes; propagate reach forward for both.
            # (`full` mode uses forward propagation as it may be slightly more efficient,
            # though backward propagation also works in principle.)
            extension_rule = where(
                _distance_reach_rel(node_u, node_v, uv_dist),
                *(
                    (
                        self._weight(node_v, neighbor, step_dist),
                        neighbor_dist == uv_dist + abs(step_dist),
                    )
                    if weighted else
                    (
                        self._edge(node_v, neighbor),
                        neighbor_dist == uv_dist + 1,
                    )
                ),
            ).select(node_u, neighbor, neighbor_dist)
        else:
            # `to` mode; propagate reach backward.
            extension_rule = where(
                _distance_reach_rel(node_u, node_v, uv_dist),
                *(
                    (
                        self._weight(neighbor, node_u, step_dist),
                        neighbor_dist == uv_dist + abs(step_dist),
                    )
                    if weighted else
                    (
                        self._edge(neighbor, node_u),
                        neighbor_dist == uv_dist + 1,
                    )
                ),
            ).select(neighbor, node_v, neighbor_dist)
            # NOTE: The optimizer may generate an index on _edge for the above;
            #   it may be best to use a cached reversed edge/weight relationship instead,
            #   given it's useful elsewhere and that may yield reuse (and more reliably
            #   good query plans, possibly).

        # The set of nodes from which to propagate reach and distances.
        node = self.Node.ref() # node is used (coupled) below.
        # Binding origin_nodes_constraint unconditionally for
        # the unconstrained case and then overriding if necessary
        # appeases the type checker, which otherwise thinks
        # it may be unbound below.
        origin_nodes_constraint = node
        if node_subset_from is not None:
            origin_nodes_constraint = node_subset_from(node)
        elif node_subset_to is not None:
            origin_nodes_constraint = node_subset_to(node)

        # Generate union of possible distances between node_a and node_b:
        node_a, node_b, ab_dist = union(
            # The distance from a node to itself is zero.
            where(origin_nodes_constraint).select(node, node, 0),
            # The distance from one node to another can be extended to its neighbors.
            # (Note that this part of the rule also drives the reach.)
            extension_rule,
        )
        # From the union of possible distances between node_a and node_b,
        # select the minimum as the distance.
        define(
            _distance_reach_rel(node_a, node_b, min(ab_dist).per(node_a, node_b))
        )

        return _distance_reach_rel


    @include_in_docs
    def weakly_connected_component(self, *, of: Optional[Relationship] = None):
        """Returns a binary relationship that maps each node to its weakly connected component.

        A weakly connected component is a subgraph where for every pair of
        nodes, there is a path between them in the underlying undirected graph.
        For undirected graphs, this is equivalent to finding the connected
        components.

        Parameters
        ----------
        of : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the domain of the weakly connected component
            computation: only component memberships of nodes in this relationship
            are returned.

        Returns
        -------
        Relationship
            A binary relationship where each tuple represents a node and the
            identifier of the component it belongs to.

        Relationship Schema
        -------------------
        ``weakly_connected_component(node, component_id)``

        * **node** (*Node*): The node.
        * **component_id** (*Node*): The identifier for the component.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                |
        | :--------- | :-------- | :------------------- |
        | Undirected | Yes       |                      |
        | Directed   | Yes       |                      |
        | Weighted   | Yes       | Weights are ignored. |

        Notes
        -----
        The ``component_id`` is the node with the minimum ID within each
        component.

        The ``weakly_connected_component()`` method, called with no parameters,
        computes and caches the full weakly connected component relationship,
        providing efficient reuse across multiple calls to
        ``weakly_connected_component()``.

        In contrast, ``weakly_connected_component(of=subset)`` computes a constrained
        relationship specific to the passed-in ``subset`` and that call site.

        Note that the constrained computation requires working over all nodes
        in the components containing the nodes in ``subset``. When that set
        of nodes constitutes an appreciable fraction of the graph, the constrained
        computation may be less efficient than computing the full relationship.
        Use ``weakly_connected_component(of=subset)`` only when small subsets of
        the weakly connected component relationship are needed collectively
        across the program, and the associated components cover only a small
        part of the graph.

        Examples
        --------
        >>> from relationalai.semantics import Model, define, select, union, where
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a directed graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3 = [Node.new(id=i) for i in range(1, 4)]
        >>> define(n1, n2, n3)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n3, dst=n2),
        ... )
        >>>
        >>> # 3. Select the component ID for each node and inspect
        >>> node, component_id = Node.ref("node"), Node.ref("component_id")
        >>> wcc = graph.weakly_connected_component()
        >>> select(node.id, component_id.id).where(wcc(node, component_id)).inspect()
        ▰▰▰▰ Setup complete
           id  id2
        0   1    1
        1   2    1
        2   3    1

        >>> # 4. Use 'of' parameter to constrain computation to subset of nodes
        >>> # Define a subset containing only nodes 1 and 3
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(union(node.id == 1, node.id == 3)).define(subset(node))
        >>>
        >>> # Get component membership only for nodes in the subset
        >>> constrained_wcc = graph.weakly_connected_component(of=subset)
        >>> select(node.id, component_id.id).where(
        ...     constrained_wcc(node, component_id)
        ... ).inspect()
        ▰▰▰▰ Setup complete
           id  id2
        0   1    1
        1   3    1

        """
        if of is None:
            return self._weakly_connected_component
        else:
            # Validate the 'of' parameter
            self._validate_node_subset_parameter('of', of)
            return self._weakly_connected_component_of(of)

    @cached_property
    def _weakly_connected_component(self):
        """Lazily define and cache the self._weakly_connected_component relationship."""
        _weakly_connected_component_rel = self._create_weakly_connected_component_relationship(
            node_subset=None
        )
        _weakly_connected_component_rel.annotate(annotations.track("graphs", "weakly_connected_component"))
        return _weakly_connected_component_rel

    def _weakly_connected_component_of(self, node_subset: Relationship):
        """
        Create a weakly_connected_component relationship constrained to the
        subset of nodes in `node_subset`. Note this relationship is not cached;
        it is specific to the callsite.
        """
        _weakly_connected_component_rel = self._create_weakly_connected_component_relationship(
            node_subset=node_subset
        )
        _weakly_connected_component_rel.annotate(annotations.track("graphs", "weakly_connected_component_of"))
        return _weakly_connected_component_rel

    def _create_weakly_connected_component_relationship(
            self, *, node_subset: Optional[Relationship]
        ):
        """
        Create a weakly_connected_component relationship, optionally constrained
        to a subset of nodes.

        Parameters
        ----------
        node_subset : Relationship or None
            If provided, a unary relationship defining the subset of nodes to
            compute component membership for. If None, compute for all nodes.

        Returns
        -------
        Relationship
            A binary relationship mapping nodes to their weakly connected component IDs.
        """
        # NOTE: In the constrained case, we must compute over the full of
        #   the weakly connected components containing the nodes in the
        #   provided subset, and _only_ over those weakly connected components.
        #   To do so, the logic below simultaneously computes the (weak) reach from
        #   the nodes in the provided subset (in `_weakly_connected_component_reach_rel``)
        #   while computing component membership.

        # A weakly connected component relation over
        # those components reachable from the nodes in the subset.
        _weakly_connected_component_reach_rel = self._model.Relationship(
            f"{{node:{self._NodeConceptStr}}} is in the connected component {{id:{self._NodeConceptStr}}}"
        )

        node, neighbor, component, dummy = \
            self.Node.ref(), self.Node.ref(), self.Node.ref(), self.Node.ref()

        # `discovered_nodes` reflects the (weak) reach from the nodes in the provided
        # subset known at a given point in the recursion. In the unconstrained
        # case, the subset is implicitly the set of all nodes, and starting with
        # all such nodes "discovered" accelerates the computation.
        if node_subset is None:
            discovered_nodes = node
        else:
            discovered_nodes = union(
                node_subset(node),
                _weakly_connected_component_reach_rel(node, dummy)
            )

        where(
            # Generate union of possible component identifiers for a given node:
            union(
                # A node's component identifier may be itself.
                where(discovered_nodes, component == node),
                # A node's component identifier may be those of its neighbors.
                # (Note that this part of the rule also drives the (weak) reach.)
                where(
                    self._neighbor(neighbor, node),
                    _weakly_connected_component_reach_rel(neighbor, component)
                )
            )
        ).define(
            # From the union of possible component identifiers for a given node,
            # select the minimum as the component identifier.
            _weakly_connected_component_reach_rel(node, min(component).per(node))
        )
        # NOTE: This logic, including in the constrained case, consumes
        #   the (unconstrained, cached) self._neighbor relation, which is
        #   ~O(nodes) to compute. Note that this seems to be about the best we can do:
        #   To compute the (weak) reach, we either need: a) the edge relation, and
        #   O(nodes) scans over the edge relation; b) the edge relation and
        #   reverse edge relation, forming which is O(nodes); or c) the neighbor
        #   relation over all nodes in the (weak) reach, computing which requires
        #   one of (a) or (b) above. Given that, for simplicity here we use (c),
        #   as there's a reasonable likelihood of re-/shared-use.

        if node_subset is None:
            # The reach relation from all nodes is the full relation.
            return _weakly_connected_component_reach_rel
        else:
            # A weakly connected component relation constrained to
            # nodes in the subset (filtered from the reach relation above).
            _weakly_connected_component_constrained_rel = self._model.Relationship(
                f"{{node:{self._NodeConceptStr}}} is in the connected component {{id:{self._NodeConceptStr}}}"
            )

            where(
                node_subset(node),
                _weakly_connected_component_reach_rel(node, component)
            ).define(_weakly_connected_component_constrained_rel(node, component))

            return _weakly_connected_component_constrained_rel


    @include_in_docs
    def diameter_range(self):
        """Estimates the graph diameter and returns it as a minimum and maximum bound.

        Returns
        -------
        (Relationship, Relationship)
            A tuple containing two unary `Relationship` objects:
            (`min_bound`, `max_bound`).

            * ``min_bound``: A relationship of the form ``min_bound(value)``
                where ``value`` (*Integer*) is the lower bound of the
                estimated diameter.
            * ``max_bound``: A relationship of the form ``max_bound(value)``
                where ``value`` (*Integer*) is the upper bound of the
                estimated diameter.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                |
        | :--------- | :-------- | :------------------- |
        | Undirected | Yes       |                      |
        | Directed   | Yes       |                      |
        | Weighted   | Yes       | Weights are ignored. |

        Notes
        -----
        This method is used to determine the range of possible diameter
        values in the graph. This is done by selecting a number of random
        nodes in the graph and taking the maximum of all shortest paths
        lengths to the rest of the graph. This gives a range per node.
        Then, the intersection of these ranges is taken and the final range
        is returned.

        For disconnected graphs, `diameter_range` returns the diameter range
        of the largest (weakly) connected component. This behavior deviates
        from many graph theory resources, which typically define the diameter
        of a disconnected graph as infinity.

        Examples
        --------
        **Connected Graph Example**

        >>> from relationalai.semantics import Model, define
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a connected, undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n3, dst=n2),
        ...     Edge.new(src=n4, dst=n3),
        ... )
        >>>
        >>> # 3. Get the diameter range and inspect each bound
        >>> min_bound, max_bound = graph.diameter_range()
        >>> min_bound.inspect()
        ▰▰▰▰ Setup complete
           int
        0    3
        >>> max_bound.inspect()
           int
        0    4

        **Disconnected Graph Example**

        >>> from relationalai.semantics import Model, define
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a disconnected, undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4, n5 = [Node.new(id=i) for i in range(1, 6)]
        >>> define(n1, n2, n3, n4, n5)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n3, dst=n4),
        ...     Edge.new(src=n4, dst=n5),
        ... )
        >>>
        >>> # 3. The range reflects the largest component {3, 4, 5}
        >>> min_bound, max_bound = graph.diameter_range()
        >>> min_bound.inspect()
        ▰▰▰▰ Setup complete
           int
        0    2
        >>> max_bound.inspect()
           int
        0    2

        """
        return self._diameter_range

    @cached_property
    def _diameter_range(self):
        """
        Lazily define and cache self._diameter_range, a two-tuple of relationships
        of the form `(_diameter_range_min_rel, _diameter_range_max_rel)`.
        """
        _diameter_range_min_rel = self._model.Relationship("The graph has a min diameter range of {value:Integer}")
        _diameter_range_max_rel = self._model.Relationship("The graph has a max diameter range of {value:Integer}")
        _diameter_range_min_rel.annotate(annotations.track("graphs", "diameter_range_min"))
        _diameter_range_max_rel.annotate(annotations.track("graphs", "diameter_range_max"))

        component_node_pairs = self._model.Relationship(f"component id {{cid:{self._NodeConceptStr}}} has node id {{nid:{self._NodeConceptStr}}}")
        nodeid, cid, degreevalue = self.Node.ref(), self.Node.ref(), Integer.ref()
        where(self._degree(nodeid, degreevalue),
              self._weakly_connected_component(nodeid, cid),
              # This is `bottom[10, ...]` in Rel.
              r := (rank(desc(degreevalue, nodeid))), r <= 10)\
              .define(component_node_pairs(cid, nodeid))

        component_node_length = self._model.Relationship(f"component id {{cid:{self._NodeConceptStr}}} and node id {{nid:{self._NodeConceptStr}}} have max distance {{mdist:Integer}}")

        cid, nid = self.Node.ref(), self.Node.ref()

        if self.directed:
            where(component_node_pairs(cid, nid),
                  # Weights are ignored!
                  max_forward := max(self._distance_non_weighted(nid, self.Node.ref(), Integer.ref())).per(nid),
                  max_reversed := max(self._distance_reversed_non_weighted(nid, self.Node.ref(), Integer.ref())).per(nid),
                  max_sp := maximum(max_forward, max_reversed))\
                .define(component_node_length(cid, nid, max_sp))
        else:
            where(component_node_pairs(cid, nid),
                  # Weights are ignored!
                  max_sp := max(self._distance_non_weighted(nid, self.Node, Integer)).per(nid))\
                .define(component_node_length(cid, nid, max_sp))

        component_of_interest = self._model.Relationship(f"component id {{cid:{self._NodeConceptStr}}} is of interest")

        v = Integer.ref()
        where(v == max(component_node_length(self.Node.ref(), self.Node.ref(), Integer)),
              component_node_length(cid, self.Node.ref(), v)
              ).define(component_of_interest(cid))

        candidates = self._model.Relationship(f"node with id {{nodeid:{self._NodeConceptStr}}} and length {{value:Integer}} are candidates")
        nodeid, value = self.Node.ref(), Integer.ref()
        where(component_node_length(cid, nodeid, value),
              component_of_interest(cid))\
              .define(candidates(nodeid, value))

        where(v := min(candidates(nodeid, Integer))).define(_diameter_range_max_rel(2 * v))
        where(v := max(candidates(nodeid, Integer))).define(_diameter_range_min_rel(v))

        return (_diameter_range_min_rel, _diameter_range_max_rel)

    @cached_property
    def _reachable_from_min_node(self):
        """Lazily define and cache the self._reachable_from_min_node relationship, a non-public helper."""
        _reachable_from_min_node_rel = self._model.Relationship(f"{{node:{self._NodeConceptStr}}} is reachable from the minimal node")

        node_v, node_w = self.Node.ref(), self.Node.ref()
        define(_reachable_from_min_node_rel(min(node_v)))
        where(_reachable_from_min_node_rel(node_w), self._edge(node_w, node_v)).define(_reachable_from_min_node_rel(node_v))
        # We discard directions for `is_connected`.
        where(_reachable_from_min_node_rel(node_w), self._edge(node_v, node_w)).define(_reachable_from_min_node_rel(node_v))

        return _reachable_from_min_node_rel

    @cached_property
    def _distance_non_weighted(self):
        """Lazily define and cache the self._distance relationship."""
        if not self.weighted:
            return self._distance
        else:
            return self._create_distance_relationship(weighted=False)

    @cached_property
    def _distance_reversed_non_weighted(self):
        """Lazily define and cache the self._distance_reversed_non_weighted relationship, a non-public helper."""
        _distance_reversed_non_weighted_rel = self._model.Relationship(f"{{node_u:{self._NodeConceptStr}}} and {{node_v:{self._NodeConceptStr}}} have a reversed distance of {{d:Integer}}")
        node_u, node_v, node_n, d1 = self.Node.ref(), self.Node.ref(), self.Node.ref(), Integer.ref()
        node_u, node_v, d = union(
            where(node_u == node_v, d1 == 0).select(node_u, node_v, d1), # Base case.
            where(self._edge(node_v, node_n),
                  d2 := _distance_reversed_non_weighted_rel(node_u, node_n, Integer) + 1).select(node_u, node_v, d2) # Recursive case.
        )
        define(_distance_reversed_non_weighted_rel(node_u, node_v, min(d).per(node_u, node_v)))

        return _distance_reversed_non_weighted_rel


    @include_in_docs
    def is_connected(self):
        """Returns a unary relationship containing whether the graph is connected.

        A graph is considered connected if every node is reachable from every
        other node in the underlying undirected graph.

        Returns
        -------
        Relationship
            A unary relationship containing a boolean indicator of whether the graph
            is connected.

        Relationship Schema
        -------------------
        ``is_connected(connected)``

        * **connected** (*Boolean*): Whether the graph is connected.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                |
        | :--------- | :-------- | :------------------- |
        | Undirected | Yes       |                      |
        | Directed   | Yes       |                      |
        | Weighted   | Yes       | Weights are ignored. |

        Notes
        -----
        An empty graph is considered connected.

        Examples
        --------
        **Connected Graph Example**

        >>> from relationalai.semantics import Model, define, select
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a connected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n3, dst=n2),
        ...     Edge.new(src=n4, dst=n3),
        ... )
        >>>
        >>> # 3. Select and inspect the relation
        >>> select(graph.is_connected()).inspect()
        ▰▰▰▰ Setup complete
           is_connected
        0          True

        **Disconnected Graph Example**

        >>> from relationalai.semantics import Model, define, select
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a disconnected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4, n5 = [Node.new(id=i) for i in range(1, 6)]
        >>> define(n1, n2, n3, n4, n5)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n3, dst=n2),
        ...     Edge.new(src=n4, dst=n5),  # This edge creates a separate component
        ... )
        >>>
        >>> # 3. Select and inspect the relation
        >>> select(graph.is_connected()).inspect()
        ▰▰▰▰ Setup complete
           is_connected
        0         False

        """
        return self._is_connected

    @cached_property
    def _is_connected(self):
        """Lazily define and cache the self._is_connected relationship."""
        _is_connected_rel = self._model.Relationship("'The graph is connected' is {is_connected:Boolean}")
        _is_connected_rel.annotate(annotations.track("graphs", "is_connected"))

        where(
            self._num_nodes(0) |
            count(self._reachable_from_min_node(self.Node.ref())) == self._num_nodes(Integer.ref())
        ).define(_is_connected_rel(True))

        where(
            not_(_is_connected_rel(True))
        ).define(_is_connected_rel(False))

        return _is_connected_rel


    @include_in_docs
    def jaccard_similarity(
            self,
            *,
            full: Optional[bool] = None,
            from_: Optional[Relationship] = None,
            to: Optional[Relationship] = None,
            between: Optional[Relationship] = None,
        ):
        """Returns a ternary relationship containing
        the Jaccard similarity for pairs of nodes.

        The Jaccard similarity is a measure between two nodes that ranges from
        0.0 to 1.0, where higher values indicate greater similarity.

        Parameters
        ----------
        full : bool, optional
            If ``True``, computes the Jaccard similarity for all pairs
            of nodes in the graph. This computation can be expensive for large graphs,
            as the result can scale quadratically in the number of nodes. Mutually exclusive
            with other parameters.
            Default is ``None``.
        from_ : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the domain of the Jaccard similarity computation: only
            Jaccard similarity scores for node pairs where the first node is
            in this relationship are computed and returned. Mutually exclusive with
            ``full`` and ``between``.
            Default is ``None``.
        to : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. Can only
            be used together with the ``from_`` parameter. When provided with ``from_``,
            constrains the domain of the Jaccard similarity computation: only
            Jaccard similarity scores for node pairs where the first node is
            in ``from_`` and the second node is in ``to`` are computed and returned.
            Default is ``None``.
        between : Relationship, optional
            A binary relationship containing pairs of nodes. When provided,
            constrains the domain of the Jaccard similarity computation: only
            Jaccard similarity scores for the specific node pairs in
            this relationship are computed and returned. Mutually exclusive
            with other parameters.
            Default is ``None``.

        Returns
        -------
        Relationship
            A ternary relationship where each tuple represents a pair of nodes
            and their Jaccard similarity.

        Raises
        ------
        ValueError
            If ``full`` is provided with any other parameter.
            If ``between`` is provided with any other parameter.
            If ``from_`` is provided with any parameter other than ``to``.
            If none of ``full``, ``from_``, or ``between`` is provided.
            If ``full`` is not ``True`` or ``None``.
        AssertionError
            If ``from_``, ``to``, or ``between`` is not a ``Relationship``.
            If ``from_``, ``to``, or ``between`` is not attached to the same model as the graph.
            If ``from_``, ``to``, or ``between`` does not contain the graph's ``Node`` concept.
            If ``from_`` or ``to`` is not a unary relationship.
            If ``between`` is not a binary relationship.

        Relationship Schema
        -------------------
        ``jaccard_similarity(node_u, node_v, score)``

        * **node_u** (*Node*): The first node in the pair.
        * **node_v** (*Node*): The second node in the pair.
        * **score** (*Float*): The Jaccard similarity of the pair.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                                      |
        | :--------- | :-------- | :----------------------------------------- |
        | Undirected | Yes       |                                            |
        | Directed   | Yes       | Based on out-neighbors.                    |
        | Weighted   | Yes       |                                            |
        | Unweighted | Yes       | Each edge weight is taken to be 1.0.       |

        Notes
        -----
        The **unweighted** Jaccard similarity between two nodes is the ratio of
        the size of the intersection to the size of the union of their
        neighbors (or out-neighbors for directed graphs).

        The **weighted** Jaccard similarity considers the weights of the edges.
        The definition used here is taken from the reference noted below. It is
        the ratio between two quantities:

        1.  **Numerator**: For every other node `w` in the graph, find the
            minimum of the edge weights `(u, w)` and `(v, w)`, and sum these
            minimums.
        2.  **Denominator**: For every other node `w` in the graph, find the
            maximum of the edge weights `(u, w)` and `(v, w)`, and sum these
            maximums.

        If an edge does not exist, its weight is considered 0.0. This can be
        better understood via the following calculation for the weighted
        example below.

        | node id | edge weights to node 1 | edge weights to node 2 | min  | max  |
        | :------ | :--------------------- | :--------------------- | :--- | :--- |
        | 1       | 0.0                    | 1.6                    | 0.0  | 1.6  |
        | 2       | 1.6                    | 0.0                    | 0.0  | 1.6  |
        | 3       | 1.4                    | 0.46                   | 0.46 | 1.4  |
        | 4       | 0.0                    | 0.0                    | 0.0  | 0.0  |

        The weighted Jaccard similarity between node 1 and 2 is then:
        `0.46 / (1.6 + 1.6 + 1.4) = 0.1`.

        Edge weights are assumed to be non-negative, so the neighborhood
        vectors contain only non-negative elements. Therefore, the Jaccard
        similarity score is always between 0.0 and 1.0, inclusive.

        The ``jaccard_similarity(full=True)`` method computes and caches
        the full Jaccard similarity relationship for all pairs of nodes,
        providing efficient reuse across multiple calls. This can be expensive
        as the result can contain O(|V|²) tuples.

        Calling ``jaccard_similarity()`` without arguments raises a ``ValueError``,
        to ensure awareness and explicit acknowledgement (``full=True``) of this cost.

        In contrast, ``jaccard_similarity(from_=subset)`` constrains the computation to
        tuples with the first position in the passed-in ``subset``. The result is
        not cached; it is specific to the call site. When a significant fraction of
        the Jaccard similarity relation is needed across a program,
        ``jaccard_similarity(full=True)`` is typically more efficient. Use
        ``jaccard_similarity(from_=subset)`` only when small subsets of
        the Jaccard similarity relationship are needed
        collectively across the program.

        The ``to`` parameter can be used together with ``from_`` to further
        constrain the computation: ``jaccard_similarity(from_=subset_a, to=subset_b)``
        computes Jaccard similarity scores only for node pairs where the first node is in
        ``subset_a`` and the second node is in ``subset_b``. (Since ``jaccard_similarity``
        is symmetric in its first two positions, using ``to`` without ``from_`` would
        be functionally redundant, and is not allowed.)

        The ``between`` parameter provides another way to constrain the computation.
        Unlike ``from_`` and ``to``, which allow you to independently constrain the first
        and second positions in ``jaccard_similarity`` tuples to sets of nodes, ``between``
        allows you constrain the first and second positions, jointly, to specific pairs
        of nodes.

        Examples
        --------
        **Unweighted Graph Examples**

        *Undirected Graph*
        >>> from relationalai.semantics import Model, define, select, Float
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n2, dst=n4),
        ...     Edge.new(src=n4, dst=n3),
        ... )
        >>> u, v, score = Node.ref("u"), Node.ref("v"), Float.ref("score")
        >>> jaccard_similarity = graph.jaccard_similarity(full=True)
        >>> select(score).where(jaccard_similarity(u, v, score), u.id == 2, v.id == 4).inspect()
        ▰▰▰▰ Setup complete
           score
        0   0.25

        *Directed Graph*
        >>> from relationalai.semantics import Model, define, select, Float
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n2, dst=n4),
        ...     Edge.new(src=n4, dst=n3),
        ... )
        >>> u, v, score = Node.ref("u"), Node.ref("v"), Float.ref("score")
        >>> jaccard_similarity = graph.jaccard_similarity(full=True)
        >>> select(score).where(jaccard_similarity(u, v, score), u.id == 2, v.id == 4).inspect()
        ▰▰▰▰ Setup complete
           score
        0    0.5

        **Weighted Graph Example**

        >>> from relationalai.semantics import Model, define, select, Float
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up a weighted, undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=True)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges with weights
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2, weight=1.6),
        ...     Edge.new(src=n1, dst=n3, weight=1.4),
        ...     Edge.new(src=n2, dst=n3, weight=0.46),
        ...     Edge.new(src=n3, dst=n4, weight=2.5),
        ... )
        >>>
        >>> # 3. Select the weighted Jaccard similarity for the pair (1, 2)
        >>> u, v, score = Node.ref("u"), Node.ref("v"), Float.ref("score")
        >>> jaccard_similarity = graph.jaccard_similarity(full=True)
        >>> select(score).where(jaccard_similarity(u, v, score), u.id == 1, v.id == 2).inspect()
        ▰▰▰▰ Setup complete
           score
        0    0.1

        **Domain Constraint Examples**

        >>> # Use 'from_' parameter to constrain the set of nodes for the first position
        >>> # Using the same undirected unweighted graph from above
        >>> from relationalai.semantics import where
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(node.id == 2).define(subset(node))
        >>>
        >>> # Get Jaccard similarity scores only for pairs where first node is in subset
        >>> constrained_jaccard_similarity = graph.jaccard_similarity(from_=subset)
        >>> select(u.id, v.id, score).where(constrained_jaccard_similarity(u, v, score)).inspect()
        ▰▰▰▰ Setup complete
           id  id2  score
        0   2    2   1.00
        1   2    3   0.50
        2   2    4   0.25

        >>> # Use both 'from_' and 'to' parameters to constrain both positions
        >>> from_subset = model.Relationship(f"{{node:{Node}}} is in from_subset")
        >>> to_subset = model.Relationship(f"{{node:{Node}}} is in to_subset")
        >>> where(node.id == 2).define(from_subset(node))
        >>> where(node.id == 4).define(to_subset(node))
        >>>
        >>> # Get Jaccard similarity scores only where first node is in from_subset and second node is in to_subset
        >>> constrained_jaccard_similarity = graph.jaccard_similarity(from_=from_subset, to=to_subset)
        >>> select(u.id, v.id, score).where(constrained_jaccard_similarity(u, v, score)).inspect()
        ▰▰▰▰ Setup complete
           id  id2  score
        0   2    4   0.25

        >>> # Use 'between' parameter to constrain to specific pairs of nodes
        >>> pairs = model.Relationship(f"{{node_a:{Node}}} and {{node_b:{Node}}} are a pair")
        >>> node_a, node_b = Node.ref(), Node.ref()
        >>> where(node_a.id == 2, node_b.id == 4).define(pairs(node_a, node_b))
        >>> where(node_a.id == 3, node_b.id == 4).define(pairs(node_a, node_b))
        >>>
        >>> # Get Jaccard similarity scores only for the specific pairs (2, 4) and (3, 4)
        >>> constrained_jaccard_similarity = graph.jaccard_similarity(between=pairs)
        >>> select(u.id, v.id, score).where(constrained_jaccard_similarity(u, v, score)).inspect()
        ▰▰▰▰ Setup complete
           id  id2  score
        0   2    4   0.25
        1   3    4   0.50

        References
        ----------
        Frigo M, Cruciani E, Coudert D, Deriche R, Natale E, Deslauriers-Gauthier S.
        Network alignment and similarity reveal atlas-based topological differences
        in structural connectomes. Netw Neurosci. 2021 Aug 30;5(3):711-733.
        doi: 10.1162/netn_a_00199. PMID: 34746624; PMCID: PMC8567827.

        """
        # Validate domain constraint parameters (jaccard_similarity is symmetric).
        symmetric = True
        self._validate_domain_constraint_parameters(
            'jaccard_similarity', symmetric, full, from_, to, between
        )

        # At this point, exactly one of `full`, `from_`, or `between`
        # has been provided, and if `to` is provided, `from_` is also provided.

        # Handle `between`.
        if between is not None:
            self._validate_pair_subset_parameter(between)
            return self._jaccard_similarity_between(between)

        # Handle `from_` (and potentially `to`).
        if from_ is not None:
            self._validate_node_subset_parameter('from_', from_)
            if to is not None:
                self._validate_node_subset_parameter('to', to)
                return self._jaccard_similarity_from_to(from_, to)
            return self._jaccard_similarity_from(from_)

        # Handle `full`.
        return self._jaccard_similarity

    @cached_property
    def _jaccard_similarity(self):
        """Lazily define and cache the full jaccard_similarity relationship."""
        _jaccard_similarity_rel = self._create_jaccard_similarity_relationship()
        _jaccard_similarity_rel.annotate(annotations.track("graphs", "jaccard_similarity"))
        return _jaccard_similarity_rel

    def _jaccard_similarity_from(self, node_subset_from: Relationship):
        """
        Create a jaccard_similarity relationship, with the first position in each
        tuple constrained to be in the given subset of nodes. Note this relationship
        is not cached; it is specific to the callsite.
        """
        _jaccard_similarity_rel = self._create_jaccard_similarity_relationship(
            node_subset_from=node_subset_from
        )
        _jaccard_similarity_rel.annotate(annotations.track("graphs", "jaccard_similarity_from"))
        return _jaccard_similarity_rel

    def _jaccard_similarity_from_to(self, node_subset_from: Relationship, node_subset_to: Relationship):
        """
        Create a jaccard_similarity relationship, with the first position in each
        tuple constrained to be in `node_subset_from`, and the second position in
        each tuple constrained to be in `node_subset_to`. Note this relationship
        is not cached; it is specific to the callsite.
        """
        _jaccard_similarity_rel = self._create_jaccard_similarity_relationship(
            node_subset_from=node_subset_from,
            node_subset_to=node_subset_to
        )
        _jaccard_similarity_rel.annotate(annotations.track("graphs", "jaccard_similarity_from_to"))
        return _jaccard_similarity_rel

    def _jaccard_similarity_between(self, pair_subset_between: Relationship):
        """
        Create a jaccard_similarity relationship, with the first and second position
        in each tuple jointly constrained to be in the given set of pairs
        of nodes. Note this relationship is not cached;
        it is specific to the callsite.
        """
        _jaccard_similarity_rel = self._create_jaccard_similarity_relationship(
            pair_subset_between=pair_subset_between
        )
        _jaccard_similarity_rel.annotate(annotations.track("graphs", "jaccard_similarity_between"))
        return _jaccard_similarity_rel

    def _create_jaccard_similarity_relationship(
        self,
        *,
        node_subset_from: Optional[Relationship] = None,
        node_subset_to: Optional[Relationship] = None,
        pair_subset_between: Optional[Relationship] = None,
    ):
        """
        Create jaccard_similarity relationship, optionally constrained by
        the provided node subsets or pair subset.
        """
        _jaccard_similarity_rel = self._model.Relationship(
            f"{{node_u:{self._NodeConceptStr}}} has a Jaccard similarity to "
            f"{{node_v:{self._NodeConceptStr}}} of {{score:Float}}"
        )

        # Branch by case to select appropriate count_outneighbor,
        # outneighbor, and weighted_outdegree relationships, and build
        # appropriate constraints on the domain of the nodes.
        node_u, node_v = self.Node.ref(), self.Node.ref()

        # TODO: Optimization opportunity. In a number of branches below,
        #   we compute _count_outneighbor_of, which transitively computes
        #   _outneighbor_of, and then compute _outneighbor_of directly;
        #   the present code structure makes this a developer-time-efficient
        #   way to get this off the ground, but of course involves redundant
        #   work. In future this redundant work could be eliminated.

        # Handle the `between` case.
        if pair_subset_between is not None:
            # Extract first-position and second-position nodes.
            first_position_subset = self._model.Relationship(f"{{node:{self._NodeConceptStr}}}")
            second_position_subset = self._model.Relationship(f"{{node:{self._NodeConceptStr}}}")
            node_x, node_y = self.Node.ref(), self.Node.ref()
            where(
                pair_subset_between(node_x, node_y)
            ).define(
                first_position_subset(node_x),
                second_position_subset(node_y)
            )

            if not self.weighted:
                count_outneighbor_u_rel = self._count_outneighbor_of(first_position_subset)
                count_outneighbor_v_rel = self._count_outneighbor_of(second_position_subset)
                outneighbor_u_rel = self._outneighbor_of(first_position_subset)
                outneighbor_v_rel = self._outneighbor_of(second_position_subset)
            else: # self.weighted
                weighted_outdegree_u_rel = self._weighted_outdegree_of(first_position_subset)
                weighted_outdegree_v_rel = self._weighted_outdegree_of(second_position_subset)

            node_constraints = [pair_subset_between(node_u, node_v)]

        # Handle the `from_` case.
        elif node_subset_from is not None and node_subset_to is None:
            if not self.weighted:
                count_outneighbor_u_rel = self._count_outneighbor_of(node_subset_from)
                count_outneighbor_v_rel = self._count_outneighbor
                outneighbor_u_rel = self._outneighbor_of(node_subset_from)
                outneighbor_v_rel = self._outneighbor
            else: # self.weighted
                weighted_outdegree_u_rel = self._weighted_outdegree_of(node_subset_from)
                weighted_outdegree_v_rel = self._weighted_outdegree

            # TODO: Implement depth-two traversal strategy for better performance.
            #   See similar comments on related similarity metrics.

            node_constraints = [node_subset_from(node_u)]

        # Handle the `from_`/`to` case.
        elif node_subset_from is not None and node_subset_to is not None:
            # Check for object identity optimization.
            if node_subset_from is node_subset_to:
                if not self.weighted:
                    count_outneighbor_u_rel = self._count_outneighbor_of(node_subset_from)
                    count_outneighbor_v_rel = count_outneighbor_u_rel
                    outneighbor_u_rel = self._outneighbor_of(node_subset_from)
                    outneighbor_v_rel = outneighbor_u_rel
                else: # self.weighted
                    weighted_outdegree_u_rel = self._weighted_outdegree_of(node_subset_from)
                    weighted_outdegree_v_rel = weighted_outdegree_u_rel
            else:
                if not self.weighted:
                    count_outneighbor_u_rel = self._count_outneighbor_of(node_subset_from)
                    count_outneighbor_v_rel = self._count_outneighbor_of(node_subset_to)
                    outneighbor_u_rel = self._outneighbor_of(node_subset_from)
                    outneighbor_v_rel = self._outneighbor_of(node_subset_to)
                else: # self.weighted
                    weighted_outdegree_u_rel = self._weighted_outdegree_of(node_subset_from)
                    weighted_outdegree_v_rel = self._weighted_outdegree_of(node_subset_to)

            node_constraints = [node_subset_from(node_u), node_subset_to(node_v)]

        # Handle the `full` case.
        else:
            if not self.weighted:
                count_outneighbor_u_rel = self._count_outneighbor
                count_outneighbor_v_rel = self._count_outneighbor
                outneighbor_u_rel = self._outneighbor
                outneighbor_v_rel = self._outneighbor
            else: # self.weighted
                weighted_outdegree_u_rel = self._weighted_outdegree
                weighted_outdegree_v_rel = self._weighted_outdegree

            node_constraints = []

        # Define Jaccard similarity logic for weighted and unweighted cases.
        if not self.weighted:
            num_u_outneigbor, num_v_outneigbor = Integer.ref(), Integer.ref()
            common_outneighbor_node = self.Node.ref()
            num_union_outneighbors = Integer.ref()
            score = Float.ref()

            where(
                *node_constraints,
                count_outneighbor_u_rel(node_u, num_u_outneigbor),  # type: ignore[possibly-unbound]
                count_outneighbor_v_rel(node_v, num_v_outneigbor),  # type: ignore[possibly-unbound]
                num_common_outneighbor := count(common_outneighbor_node).per(node_u, node_v).where(
                    outneighbor_u_rel(node_u, common_outneighbor_node),  # type: ignore[possibly-unbound]
                    outneighbor_v_rel(node_v, common_outneighbor_node),  # type: ignore[possibly-unbound]
                ),
                num_union_outneighbors := num_u_outneigbor + num_v_outneigbor - num_common_outneighbor,
                score := num_common_outneighbor / num_union_outneighbors,
            ).define(
                _jaccard_similarity_rel(node_u, node_v, score)
            )
        else:
            # (1) The numerator: For every node `k` in the graph, find the minimum weight of
            #     the out-edges from `u` and `v` to `k`, and sum those minimum weights.

            #     Note that for any node `k` that is not a common out-neighbor of nodes `u` and `v`,
            #     the minimum weight of the out-edges from `u` and `v` to `k` is zero/empty,
            #     so the sum here reduces to a sum over the common out-neighbors of `u` and `v`.
            min_weight_to_common_outneighbor = self._model.Relationship(
                f"{{node_u:{self._NodeConceptStr}}} and {{node_v:{self._NodeConceptStr}}} "
                f"have common outneighbor {{node_k:{self._NodeConceptStr}}} "
                f"with minimum weight {{minweight:Float}}"
            )

            node_k, w1, w2 = self.Node.ref(), Float.ref(), Float.ref()
            w = union(
                where(self._weight(node_u, node_k, w1)).select(w1),
                where(self._weight(node_v, node_k, w2)).select(w2)
            )
            where(
                *node_constraints,
                self._edge(node_u, node_k),
                self._edge(node_v, node_k)
            ).define(
                min_weight_to_common_outneighbor(
                    node_u, node_v, node_k, min(w).per(node_u, node_v, node_k)
                )
            )

            sum_of_min_weights_to_common_outneighbors = self._model.Relationship(
                f"{{node_u:{self._NodeConceptStr}}} and {{node_v:{self._NodeConceptStr}}} "
                f"have a sum of minweights of {{minsum:Float}}"
            )

            minweight = Float.ref()
            where(
                min_weight_to_common_outneighbor(node_u, node_v, node_k, minweight)
            ).define(
                sum_of_min_weights_to_common_outneighbors(
                    node_u, node_v, sum(node_k, minweight).per(node_u, node_v)
                )
            )

            # (2) The denominator: For every node `k` in the graph, find the maximum weight of
            #     the out-edges from `u` and `v` to `k`, and sum those maximum weights.
            #
            #     Note that in general the sum of the maximum of two quantities,
            #     say \sum_i max(a_i, b_i), can be reexpressed via the following identity
            #     \sum_i max(a_i, b_i) = \sum_i a_i + \sum_i b_i - \sum_i min(a_i, b_i).
            #     This identity allows us to reexpress the sum here:
            #
            #     \sum_{k in self.Node} max(self._weight(u, k), self._weight(v, k)) =
            #         \sum_{k in self.Node} self._weight(u, k) +
            #         \sum_{k in self.Node} self._weight(v, k) -
            #         \sum_{k in self.Node} min(self._weight(u, k), self._weight(v, k))
            #
            #     To simplify this expression, note that `self._weight(u, k)` is zero/empty
            #     for all `k` that aren't out-neighbors of `u`. It follows that
            #
            #     \sum_{k in self.Node} self._weight(u, k)
            #         = \sum_{k in self._outneighbor(u)} self._weight(u, k)
            #         = self._weighted_outdegree(u)
            #
            #     and similarly
            #
            #     \sum_{k in self.Node} self._weight(v, k) = self._weighted_outdegree(v)
            #
            #     Additionally, observe that `min(self._weight(u, k), self._weight(v, k))` is zero/empty
            #     for all `k` that aren't out-neighbors of both `u` and `v`. It follows that
            #
            #     \sum_{k in self.Node} min(self._weight(u, k), self._weight(v, k))
            #         = \sum_{k in self._common_outneighbor(u, v)} min(self._weight(u, k), self._weight(v, k))
            #
            #     which is _sum_of_min_weights_to_common_outneighbors above, which we
            #     can reuse to avoid computation. Finally:
            #
            #     \sum_{k in self.Node} max(self._weight(u, k), self._weight(v, k)) =
            #         self._weighted_outdegree(u) +
            #         self._weighted_outdegree(v) -
            #         _sum_of_min_weights_to_common_outneighbors(u, v)
            sum_of_max_weights_to_other_nodes = self._model.Relationship(
                f"{{node_u:{self._NodeConceptStr}}} and {{node_v:{self._NodeConceptStr}}} "
                f"have a maxsum of {{maxsum:Float}}"
            )

            u_outdegree, v_outdegree, maxsum, minsum = Float.ref(), Float.ref(), Float.ref(), Float.ref()
            where(
                *node_constraints,
                weighted_outdegree_u_rel(node_u, u_outdegree),  # type: ignore[possibly-unbound]
                weighted_outdegree_v_rel(node_v, v_outdegree),  # type: ignore[possibly-unbound]
                sum_of_min_weights_to_common_outneighbors(node_u, node_v, minsum),
                maxsum == u_outdegree + v_outdegree - minsum
            ).define(
                sum_of_max_weights_to_other_nodes(node_u, node_v, maxsum)
            )

            # Combination of (1) and (2) to produce score.
            score = Float.ref()
            where(
                sum_of_min_weights_to_common_outneighbors(node_u, node_v, minsum),
                sum_of_max_weights_to_other_nodes(node_u, node_v, maxsum),
                score == minsum / maxsum
            ).define(
                _jaccard_similarity_rel(node_u, node_v, score)
            )

        return _jaccard_similarity_rel


    @include_in_docs
    def cosine_similarity(
            self,
            *,
            full: Optional[bool] = None,
            from_: Optional[Relationship] = None,
            to: Optional[Relationship] = None,
            between: Optional[Relationship] = None,
        ):
        """Returns a ternary relationship containing
        the cosine similarity for pairs of nodes.

        The cosine similarity measures the similarity between two nodes based
        on the angle between their neighborhood vectors. The score ranges from
        0.0 to 1.0, inclusive, where 1.0 indicates identical sets of neighbors.

        Parameters
        ----------
        full : bool, optional
            If ``True``, computes the cosine similarity for all pairs
            of nodes in the graph. This computation can be expensive for large graphs,
            as the result can scale quadratically in the number of nodes. Mutually exclusive
            with other parameters.
            Default is ``None``.
        from_ : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the domain of the cosine similarity computation: only
            cosine similarity scores for node pairs where the first node is
            in this relationship are computed and returned. Mutually exclusive with
            ``full`` and ``between``.
            Default is ``None``.
        to : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. Can only
            be used together with the ``from_`` parameter. When provided with ``from_``,
            constrains the domain of the cosine similarity computation: only
            cosine similarity scores for node pairs where the first node is
            in ``from_`` and the second node is in ``to`` are computed and returned.
            Default is ``None``.
        between : Relationship, optional
            A binary relationship containing pairs of nodes. When provided,
            constrains the domain of the cosine similarity computation: only
            cosine similarity scores for the specific node pairs in
            this relationship are computed and returned. Mutually exclusive
            with other parameters.
            Default is ``None``.

        Returns
        -------
        Relationship
            A ternary relationship where each tuple represents a pair of nodes
            and their cosine similarity.

        Raises
        ------
        ValueError
            If ``full`` is provided with any other parameter.
            If ``between`` is provided with any other parameter.
            If ``from_`` is provided with any parameter other than ``to``.
            If none of ``full``, ``from_``, or ``between`` is provided.
            If ``full`` is not ``True`` or ``None``.
        AssertionError
            If ``from_``, ``to``, or ``between`` is not a ``Relationship``.
            If ``from_``, ``to``, or ``between`` is not attached to the same model as the graph.
            If ``from_``, ``to``, or ``between`` does not contain the graph's ``Node`` concept.
            If ``from_`` or ``to`` is not a unary relationship.
            If ``between`` is not a binary relationship.

        Relationship Schema
        -------------------
        ``cosine_similarity(node_u, node_v, score)``

        * **node_u** (*Node*): The first node in the pair.
        * **node_v** (*Node*): The second node in the pair.
        * **score** (*Float*): The cosine similarity of the pair.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                                      |
        | :--------- | :-------- | :----------------------------------------- |
        | Undirected | Yes       |                                            |
        | Directed   | Yes       | Based on out-neighbors.                    |
        | Weighted   | Yes       |                                            |
        | Unweighted | Yes       | Each edge weight is taken to be 1.0.       |

        Notes
        -----
        The cosine similarity is defined as the normalized inner product of
        two vectors representing the neighborhoods of the nodes `u` and `v`.
        For directed graphs, only out-neighbors are considered.

        * For **unweighted** graphs, the vector for a node `u` contains a 1
            for each neighbor and a 0 for each non-neighbor.
        * For **weighted** graphs, the vector for a node `u` contains the
            edge weight for each neighbor and a 0 for each non-neighbor.

        Edge weights are assumed to be non-negative, so the neighborhood
        vectors contain only non-negative elements. Therefore, the cosine
        similarity score is always between 0.0 and 1.0, inclusive.

        The ``cosine_similarity(full=True)`` method computes and caches
        the full cosine similarity relationship for all pairs of nodes,
        providing efficient reuse across multiple calls. This can be expensive
        as the result can contain O(|V|²) tuples.

        Calling ``cosine_similarity()`` without arguments raises a ``ValueError``,
        to ensure awareness and explicit acknowledgement (``full=True``) of this cost.

        In contrast, ``cosine_similarity(from_=subset)`` constrains the computation to
        tuples with the first position in the passed-in ``subset``. The result is
        not cached; it is specific to the call site. When a significant fraction of
        the cosine similarity relation is needed across a program,
        ``cosine_similarity(full=True)`` is typically more efficient. Use
        ``cosine_similarity(from_=subset)`` only when small subsets of
        the cosine similarity relationship are needed
        collectively across the program.

        The ``to`` parameter can be used together with ``from_`` to further
        constrain the computation: ``cosine_similarity(from_=subset_a, to=subset_b)``
        computes cosine similarity scores only for node pairs where the first node is in
        ``subset_a`` and the second node is in ``subset_b``. (Since ``cosine_similarity``
        is symmetric in its first two positions, using ``to`` without ``from_`` would
        be functionally redundant, and is not allowed.)

        The ``between`` parameter provides another way to constrain the computation.
        Unlike ``from_`` and ``to``, which allow you to independently constrain the first
        and second positions in ``cosine_similarity`` tuples to sets of nodes, ``between``
        allows you constrain the first and second positions, jointly, to specific pairs
        of nodes.

        Examples
        --------
        **Unweighted Graph Examples**

        *Undirected Graph*
        >>> from relationalai.semantics import Model, define, select, Float
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n2, dst=n4),
        ...     Edge.new(src=n4, dst=n3),
        ... )
        >>> u, v, score = Node.ref("u"), Node.ref("v"), Float.ref("score")
        >>> cosine_similarity = graph.cosine_similarity(full=True)
        >>> select(score).where(cosine_similarity(u, v, score), u.id == 2, v.id == 4).inspect()
        ▰▰▰▰ Setup complete
              score
        0  0.408248

        *Directed Graph*
        >>> from relationalai.semantics import Model, define, select, Float
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n2, dst=n4),
        ...     Edge.new(src=n4, dst=n3),
        ... )
        >>> u, v, score = Node.ref("u"), Node.ref("v"), Float.ref("score")
        >>> cosine_similarity = graph.cosine_similarity(full=True)
        >>> select(score).where(cosine_similarity(u, v, score), u.id == 2, v.id == 4).inspect()
        ▰▰▰▰ Setup complete
              score
        0  0.707107

        **Weighted Graph Examples**

        *Undirected Graph*
        >>> from relationalai.semantics import Model, define, select, Float
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=True)
        >>> Node, Edge = graph.Node, graph.Edge
        >>> n1, n2, n3, n4, n13, n14 = [Node.new(id=i) for i in [1, 2, 3, 4, 13, 14]]
        >>> define(n1, n2, n3, n4, n13, n14)
        >>> define(
        ...     Edge.new(src=n1, dst=n2, weight=1.6),
        ...     Edge.new(src=n1, dst=n3, weight=1.4),
        ...     Edge.new(src=n2, dst=n3, weight=1.2),
        ...     Edge.new(src=n3, dst=n4, weight=2.5),
        ...     Edge.new(src=n14, dst=n13, weight=1.0),
        ... )
        >>> u, v, score = Node.ref("u"), Node.ref("v"), Float.ref("score")
        >>> cosine_similarity = graph.cosine_similarity(full=True)
        >>> select(score).where(cosine_similarity(u, v, score), u.id == 1, v.id == 2).inspect()
        ▰▰▰▰ Setup complete
              score
        0  0.395103

        *Directed Graph*
        >>> from relationalai.semantics import Model, define, select, Float
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=True, weighted=True)
        >>> Node, Edge = graph.Node, graph.Edge
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in [1, 2, 3, 4]]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n3, weight=2.0),
        ...     Edge.new(src=n1, dst=n4, weight=3.0),
        ...     Edge.new(src=n2, dst=n3, weight=4.0),
        ...     Edge.new(src=n2, dst=n4, weight=5.0),
        ... )
        >>> u, v, score = Node.ref("u"), Node.ref("v"), Float.ref("score")
        >>> cosine_similarity = graph.cosine_similarity(full=True)
        >>> select(score).where(cosine_similarity(u, v, score), u.id == 1, v.id == 2).inspect()
        ▰▰▰▰ Setup complete
              score
        0  0.996241

        **Domain Constraint Examples**

        >>> # Use 'from_' parameter to constrain the set of nodes for the first position
        >>> # Using the same undirected unweighted graph from above
        >>> from relationalai.semantics import where
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(node.id == 2).define(subset(node))
        >>>
        >>> # Get cosine similarity scores only for pairs where first node is in subset
        >>> constrained_cosine_similarity = graph.cosine_similarity(from_=subset)
        >>> select(u.id, v.id, score).where(constrained_cosine_similarity(u, v, score)).inspect()
        ▰▰▰▰ Setup complete
           id  id2     score
        0   2    2  1.000000
        1   2    3  0.707107
        2   2    4  0.408248

        >>> # Use both 'from_' and 'to' parameters to constrain both positions
        >>> from_subset = model.Relationship(f"{{node:{Node}}} is in from_subset")
        >>> to_subset = model.Relationship(f"{{node:{Node}}} is in to_subset")
        >>> where(node.id == 2).define(from_subset(node))
        >>> where(node.id == 4).define(to_subset(node))
        >>>
        >>> # Get cosine similarity scores only where first node is in from_subset and second node is in to_subset
        >>> constrained_cosine_similarity = graph.cosine_similarity(from_=from_subset, to=to_subset)
        >>> select(u.id, v.id, score).where(constrained_cosine_similarity(u, v, score)).inspect()
        ▰▰▰▰ Setup complete
           id  id2     score
        0   2    4  0.408248

        >>> # Use 'between' parameter to constrain to specific pairs of nodes
        >>> pairs = model.Relationship(f"{{node_a:{Node}}} and {{node_b:{Node}}} are a pair")
        >>> node_a, node_b = Node.ref(), Node.ref()
        >>> where(node_a.id == 2, node_b.id == 4).define(pairs(node_a, node_b))
        >>> where(node_a.id == 3, node_b.id == 4).define(pairs(node_a, node_b))
        >>>
        >>> # Get cosine similarity scores only for the specific pairs (2, 4) and (3, 4)
        >>> constrained_cosine_similarity = graph.cosine_similarity(between=pairs)
        >>> select(u.id, v.id, score).where(constrained_cosine_similarity(u, v, score)).inspect()
        ▰▰▰▰ Setup complete
           id  id2     score
        0   2    4  0.408248
        1   3    4  0.707107

        """
        # Validate domain constraint parameters (cosine_similarity is symmetric).
        symmetric = True
        self._validate_domain_constraint_parameters(
            'cosine_similarity', symmetric, full, from_, to, between
        )

        # At this point, exactly one of `full`, `from_`, or `between`
        # has been provided, and if `to` is provided, `from_` is also provided.

        # Handle `between`.
        if between is not None:
            self._validate_pair_subset_parameter(between)
            return self._cosine_similarity_between(between)

        # Handle `from_` (and potentially `to`).
        if from_ is not None:
            self._validate_node_subset_parameter('from_', from_)
            if to is not None:
                self._validate_node_subset_parameter('to', to)
                return self._cosine_similarity_from_to(from_, to)
            return self._cosine_similarity_from(from_)

        # Handle `full`.
        return self._cosine_similarity

    @cached_property
    def _cosine_similarity(self):
        """Lazily define and cache the full cosine_similarity relationship."""
        _cosine_similarity_rel = self._create_cosine_similarity_relationship()
        _cosine_similarity_rel.annotate(annotations.track("graphs", "cosine_similarity"))
        return _cosine_similarity_rel

    def _cosine_similarity_from(self, node_subset_from: Relationship):
        """
        Create a cosine_similarity relationship, with the first position in each
        tuple constrained to be in the given subset of nodes. Note this relationship
        is not cached; it is specific to the callsite.
        """
        _cosine_similarity_rel = self._create_cosine_similarity_relationship(
            node_subset_from=node_subset_from
        )
        _cosine_similarity_rel.annotate(annotations.track("graphs", "cosine_similarity_from"))
        return _cosine_similarity_rel

    def _cosine_similarity_from_to(self, node_subset_from: Relationship, node_subset_to: Relationship):
        """
        Create a cosine_similarity relationship, with the first position in each
        tuple constrained to be in `node_subset_from`, and the second position in
        each tuple constrained to be in `node_subset_to`. Note this relationship
        is not cached; it is specific to the callsite.
        """
        _cosine_similarity_rel = self._create_cosine_similarity_relationship(
            node_subset_from=node_subset_from,
            node_subset_to=node_subset_to
        )
        _cosine_similarity_rel.annotate(annotations.track("graphs", "cosine_similarity_from_to"))
        return _cosine_similarity_rel

    def _cosine_similarity_between(self, pair_subset_between: Relationship):
        """
        Create a cosine_similarity relationship, with the first and second position
        in each tuple jointly constrained to be in the given set of pairs
        of nodes. Note this relationship is not cached;
        it is specific to the callsite.
        """
        _cosine_similarity_rel = self._create_cosine_similarity_relationship(
            pair_subset_between=pair_subset_between
        )
        _cosine_similarity_rel.annotate(annotations.track("graphs", "cosine_similarity_between"))
        return _cosine_similarity_rel

    def _create_cosine_similarity_relationship(
        self,
        *,
        node_subset_from: Optional[Relationship] = None,
        node_subset_to: Optional[Relationship] = None,
        pair_subset_between: Optional[Relationship] = None,
    ):
        """
        Create cosine_similarity relationship, optionally constrained by
        the provided node subsets or pair subset.
        """
        _cosine_similarity_rel = self._model.Relationship(
            f"{{node_u:{self._NodeConceptStr}}} has a cosine similarity to "
            f"{{node_v:{self._NodeConceptStr}}} of {{score:Float}}"
        )

        # TODO: Optimization opportunity. In a number of branches below,
        #   we compute _count_outneighbor_of, which transitively computes
        #   _outneighbor_of, and then compute _outneighbor_of directly;
        #   the present code structure makes this a developer-time-efficient
        #   way to get this off the ground, but of course involves redundant
        #   work. In future this redundant work could be eliminated.

        # TODO: Optimization opportunity. In some of the cases below
        #   (unweighted in particular), the node_constraint is redundant with
        #   the constraints baked into the _count_outneighbor_of and
        #   _outneighbor_of relationships. The join with node_constraint
        #   could be eliminated in those cases. Possibly also relevant to
        #   other domain-constrained relations.

        # Branch by case to select appropriate count_outneighbor and
        # outneighbor relationships, and build appropriate constraints
        # on the domain of the nodes.
        node_u, node_v = self.Node.ref(), self.Node.ref()

        # Handle the `between` case.
        if pair_subset_between is not None:
            # Extract first-position and second-position nodes.
            first_position_subset = self._model.Relationship(f"{{node:{self._NodeConceptStr}}}")
            second_position_subset = self._model.Relationship(f"{{node:{self._NodeConceptStr}}}")
            node_x, node_y = self.Node.ref(), self.Node.ref()
            where(
                pair_subset_between(node_x, node_y)
            ).define(
                first_position_subset(node_x),
                second_position_subset(node_y)
            )

            count_outneighbor_u_rel = self._count_outneighbor_of(first_position_subset)
            count_outneighbor_v_rel = self._count_outneighbor_of(second_position_subset)
            outneighbor_u_rel = self._outneighbor_of(first_position_subset)
            outneighbor_v_rel = self._outneighbor_of(second_position_subset)

            node_constraints = [pair_subset_between(node_u, node_v)]

        # Handle the `from_` case.
        elif node_subset_from is not None and node_subset_to is None:
            count_outneighbor_u_rel = self._count_outneighbor_of(node_subset_from)
            count_outneighbor_v_rel = self._count_outneighbor
            outneighbor_u_rel = self._outneighbor_of(node_subset_from)
            outneighbor_v_rel = self._outneighbor
            # TODO: This case could be optimized via an analog of
            #   the depth-2 traversal strategy suggested for the equivalent
            #   case of common_neighbor, but for another day.

            node_constraints = [node_subset_from(node_u)]

        # Handle the `from_`/`to` case.
        elif node_subset_from is not None and node_subset_to is not None:
            # Check for object identity optimization.
            if node_subset_from is node_subset_to:
                count_outneighbor_u_rel = self._count_outneighbor_of(node_subset_from)
                count_outneighbor_v_rel = count_outneighbor_u_rel
                outneighbor_u_rel = self._outneighbor_of(node_subset_from)
                outneighbor_v_rel = outneighbor_u_rel
            else:
                count_outneighbor_u_rel = self._count_outneighbor_of(node_subset_from)
                count_outneighbor_v_rel = self._count_outneighbor_of(node_subset_to)
                outneighbor_u_rel = self._outneighbor_of(node_subset_from)
                outneighbor_v_rel = self._outneighbor_of(node_subset_to)

            node_constraints = [node_subset_from(node_u), node_subset_to(node_v)]

        # Handle the `full` case.
        else:
            count_outneighbor_u_rel = self._count_outneighbor
            count_outneighbor_v_rel = self._count_outneighbor
            outneighbor_u_rel = self._outneighbor
            outneighbor_v_rel = self._outneighbor

            node_constraints = []

        # Define cosine similarity logic for both weighted and unweighted cases.
        if not self.weighted:
            # Unweighted case: use count of common outneighbors.
            count_outneighbor_u, count_outneighbor_v = Integer.ref(), Integer.ref()
            common_outneighbor_node = self.Node.ref()

            where(
                *node_constraints,
                count_outneighbor_u_rel(node_u, count_outneighbor_u),
                count_outneighbor_v_rel(node_v, count_outneighbor_v),
                c_common := count(common_outneighbor_node).per(node_u, node_v).where(
                    outneighbor_u_rel(node_u, common_outneighbor_node),
                    outneighbor_v_rel(node_v, common_outneighbor_node),
                ),
                score := c_common / sqrt(count_outneighbor_u * count_outneighbor_v),
            ).define(
                _cosine_similarity_rel(node_u, node_v, score)
            )
        else:
            # Weighted case: use dot product and norms.
            node_uk, node_vk = self.Node.ref(), self.Node.ref()
            wu, wv = Float.ref(), Float.ref()

            where(
                *node_constraints,
                squared_norm_wu := sum(node_uk, wu * wu).per(node_u).where(self._weight(node_u, node_uk, wu)),
                squared_norm_wv := sum(node_vk, wv * wv).per(node_v).where(self._weight(node_v, node_vk, wv)),
                wu_dot_wv := self._wu_dot_wv_fragment(node_u, node_v),
                score := wu_dot_wv / sqrt(squared_norm_wu * squared_norm_wv),
            ).define(
                _cosine_similarity_rel(node_u, node_v, score)
            )

        return _cosine_similarity_rel


    @include_in_docs
    def adamic_adar(
            self,
            *,
            full: Optional[bool] = None,
            from_: Optional[Relationship] = None,
            to: Optional[Relationship] = None,
            between: Optional[Relationship] = None,
        ):
        """Returns a ternary relationship containing the Adamic-Adar index for pairs of nodes.

        The Adamic-Adar index is a similarity measure between two nodes based
        on the amount of shared neighbors between them, giving more weight to
        common neighbors that are less connected.

        Parameters
        ----------
        full : bool, optional
            If ``True``, computes the Adamic-Adar index for all pairs of nodes in
            the graph. This computation can be expensive for large graphs, as
            dependencies can scale quadratically in the number of edges or cubically
            in the number of nodes. Mutually exclusive with other parameters.
            Default is ``None``.
        from_ : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the domain of the Adamic-Adar computation: only
            Adamic-Adar indices for node pairs where the first node is in this relationship
            are computed and returned. Mutually exclusive with ``full`` and ``between``.
            Default is ``None``.
        to : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. Can only
            be used together with the ``from_`` parameter. When provided with ``from_``,
            constrains the domain of the Adamic-Adar computation: only Adamic-Adar
            indices for node pairs where the first node is in ``from_`` and the
            second node is in ``to`` are computed and returned.
            Default is ``None``.
        between : Relationship, optional
            A binary relationship containing pairs of nodes. When provided,
            constrains the domain of the Adamic-Adar computation: only Adamic-Adar
            indices for the specific node pairs in this relationship are computed
            and returned. Mutually exclusive with other parameters.
            Default is ``None``.

        Returns
        -------
        Relationship
            A ternary relationship where each tuple represents a pair of nodes
            and their Adamic-Adar index.

        Raises
        ------
        ValueError
            If ``full`` is provided with any other parameter.
            If ``between`` is provided with any other parameter.
            If ``from_`` is provided with any parameter other than ``to``.
            If none of ``full``, ``from_``, or ``between`` is provided.
            If ``full`` is not ``True`` or ``None``.
        AssertionError
            If ``from_``, ``to``, or ``between`` is not a ``Relationship``.
            If ``from_``, ``to``, or ``between`` is not attached to the same model as the graph.
            If ``from_``, ``to``, or ``between`` does not contain the graph's ``Node`` concept.
            If ``from_`` or ``to`` is not a unary relationship.
            If ``between`` is not a binary relationship.

        Relationship Schema
        -------------------
        ``adamic_adar(node_u, node_v, score)``

        * **node_u** (*Node*): The first node in the pair.
        * **node_v** (*Node*): The second node in the pair.
        * **score** (*Float*): The Adamic-Adar index of the pair.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                |
        | :--------- | :-------- | :------------------- |
        | Undirected | Yes       |                      |
        | Directed   | Yes       |                      |
        | Weighted   | Yes       | Weights are ignored. |

        Notes
        -----
        The Adamic-Adar index for nodes `u` and `v` is defined as the sum of
        the inverse logarithmic degree of their common neighbors `w`::

            AA(u,v) = Σ (1 / log(degree(w)))

        The ``adamic_adar(full=True)`` method computes and caches the full Adamic-Adar
        relationship for all pairs of nodes, providing efficient reuse across
        multiple calls. This can be expensive as dependencies can contain O(|E|²) or
        O(|V|³) tuples depending on graph density.

        Calling ``adamic_adar()`` without arguments raises a ``ValueError``,
        to ensure awareness and explicit acknowledgement (``full=True``) of this cost.

        In contrast, ``adamic_adar(from_=subset)`` constrains the computation to
        tuples with the first position in the passed-in ``subset``. The result is
        not cached; it is specific to the call site. When a significant fraction of
        the Adamic-Adar relation is needed across a program, ``adamic_adar(full=True)``
        is typically more efficient. Use ``adamic_adar(from_=subset)`` only
        when small subsets of the Adamic-Adar relationship are needed
        collectively across the program.

        The ``to`` parameter can be used together with ``from_`` to further
        constrain the computation: ``adamic_adar(from_=subset_a, to=subset_b)``
        computes Adamic-Adar indices only for node pairs where the first node is in
        ``subset_a`` and the second node is in ``subset_b``. (Since ``adamic_adar``
        is symmetric in its first two positions, using ``to`` without ``from_`` would
        be functionally redundant, and is not allowed.)

        The ``between`` parameter provides another way to constrain the computation.
        Unlike ``from_`` and ``to``, which allow you to independently constrain the first
        and second positions in ``adamic_adar`` tuples to sets of nodes, ``between``
        allows you constrain the first and second positions, jointly, to specific pairs
        of nodes.

        Examples
        --------
        >>> from relationalai.semantics import Model, define, select, where, Float
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n2, dst=n4),
        ...     Edge.new(src=n4, dst=n3),
        ... )
        >>>
        >>> # 3. Select the Adamic-Adar indices from the full relationship
        >>> u, v = Node.ref("u"), Node.ref("v")
        >>> score = Float.ref("score")
        >>> adamic_adar = graph.adamic_adar(full=True)
        >>> select(
        ...     u.id, v.id, score,
        ... ).where(
        ...     adamic_adar(u, v, score),
        ...     u.id == 2,
        ...     v.id == 4,
        ... ).inspect()
        ▰▰▰▰ Setup complete
           id  id2     score
        0   2    4  0.910239

        >>> # 4. Use 'from_' parameter to constrain the set of nodes for the first position
        >>> # Define a subset containing only node 1
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(node.id == 1).define(subset(node))
        >>>
        >>> # Get Adamic-Adar indices only for pairs where first node is in subset
        >>> constrained_adamic_adar = graph.adamic_adar(from_=subset)
        >>> select(u.id, v.id, score).where(constrained_adamic_adar(u, v, score)).inspect()
        ▰▰▰▰ Setup complete
           id  id2     score
        0   1    1  2.885390
        1   1    4  2.885390

        >>> # 5. Use both 'from_' and 'to' parameters to constrain both positions
        >>> subset_a = model.Relationship(f"{{node:{Node}}} is in subset_a")
        >>> subset_b = model.Relationship(f"{{node:{Node}}} is in subset_b")
        >>> where(node.id == 1).define(subset_a(node))
        >>> where(node.id == 4).define(subset_b(node))
        >>>
        >>> # Get Adamic-Adar indices only where first node is in subset_a and second node is in subset_b
        >>> constrained_adamic_adar = graph.adamic_adar(from_=subset_a, to=subset_b)
        >>> select(u.id, v.id, score).where(constrained_adamic_adar(u, v, score)).inspect()
        ▰▰▰▰ Setup complete
           id  id2     score
        0   1    4  2.885390

        >>> # 6. Use 'between' parameter to constrain to specific pairs of nodes
        >>> pairs = model.Relationship(f"{{node_a:{Node}}} and {{node_b:{Node}}} are a pair")
        >>> node_a, node_b = Node.ref(), Node.ref()
        >>> where(node_a.id == 1, node_b.id == 4).define(pairs(node_a, node_b))
        >>> where(node_a.id == 2, node_b.id == 3).define(pairs(node_a, node_b))
        >>>
        >>> # Get Adamic-Adar indices only for the specific pairs (1, 4) and (2, 3)
        >>> constrained_adamic_adar = graph.adamic_adar(between=pairs)
        >>> select(u.id, v.id, score).where(constrained_adamic_adar(u, v, score)).inspect()
        ▰▰▰▰ Setup complete
           id  id2     score
        0   1    4  2.885390
        1   2    3  1.442695

        """
        # Validate domain constraint parameters (adamic_adar is symmetric).
        symmetric = True
        self._validate_domain_constraint_parameters(
            'adamic_adar', symmetric, full, from_, to, between
        )

        # At this point, exactly one of `full`, `from_`, or `between`
        # has been provided, and if `to` is provided, `from_` is also provided.

        # Handle `between`.
        if between is not None:
            self._validate_pair_subset_parameter(between)
            return self._adamic_adar_between(between)

        # Handle `from_` (and potentially `to`).
        if from_ is not None:
            self._validate_node_subset_parameter('from_', from_)
            if to is not None:
                self._validate_node_subset_parameter('to', to)
                return self._adamic_adar_from_to(from_, to)
            return self._adamic_adar_from(from_)

        # Handle `full`.
        return self._adamic_adar

    @cached_property
    def _adamic_adar(self):
        """Lazily define and cache the full adamic_adar relationship."""
        _adamic_adar_rel = self._create_adamic_adar_relationship()
        _adamic_adar_rel.annotate(annotations.track("graphs", "adamic_adar"))
        return _adamic_adar_rel

    def _adamic_adar_from(self, node_subset_from: Relationship):
        """
        Create an adamic_adar relationship, with the first position in each
        tuple constrained to be in the given subset of nodes. Note this relationship
        is not cached; it is specific to the callsite.
        """
        _adamic_adar_rel = self._create_adamic_adar_relationship(
            node_subset_from=node_subset_from
        )
        _adamic_adar_rel.annotate(annotations.track("graphs", "adamic_adar_from"))
        return _adamic_adar_rel

    def _adamic_adar_from_to(self, node_subset_from: Relationship, node_subset_to: Relationship):
        """
        Create an adamic_adar relationship, with the first position in each
        tuple constrained to be in `node_subset_from`, and the second position in
        each tuple constrained to be in `node_subset_to`. Note this relationship
        is not cached; it is specific to the callsite.
        """
        _adamic_adar_rel = self._create_adamic_adar_relationship(
            node_subset_from=node_subset_from,
            node_subset_to=node_subset_to
        )
        _adamic_adar_rel.annotate(annotations.track("graphs", "adamic_adar_from_to"))
        return _adamic_adar_rel

    def _adamic_adar_between(self, pair_subset_between: Relationship):
        """
        Create an adamic_adar relationship, with the first and second position
        in each tuple jointly constrained to be in the given set of pairs
        of nodes. Note this relationship is not cached;
        it is specific to the callsite.
        """
        _adamic_adar_rel = self._create_adamic_adar_relationship(
            pair_subset_between=pair_subset_between
        )
        _adamic_adar_rel.annotate(annotations.track("graphs", "adamic_adar_between"))
        return _adamic_adar_rel

    def _create_adamic_adar_relationship(
        self,
        *,
        node_subset_from: Optional[Relationship] = None,
        node_subset_to: Optional[Relationship] = None,
        pair_subset_between: Optional[Relationship] = None,
    ):
        """
        Create adamic_adar relationship, optionally constrained by the provided
        node subsets or pair subset.
        """
        _adamic_adar_rel = self._model.Relationship(
            f"{{node_u:{self._NodeConceptStr}}} and {{node_v:{self._NodeConceptStr}}} "
            f"have adamic adar score {{score:Float}}"
        )

        # NOTE: Handling of the common_neighbor relation (`common_neighbor_rel`)
        #   differs in each case, whereas handling of the count_neighbor relation
        #   (`count_neighbor_rel`) is: a) the same among the constrained cases;
        #   and b) different in the unconstrained case. As such we handle
        #   `common_neighbor_rel` in the branches by case below, and handle
        #   `count_neighbor_rel` in a separate constrained/unconstrained branch later.

        # Handle the `between` case.
        if pair_subset_between is not None:
            # Get the appropriate common_neighbor relationship.
            common_neighbor_rel = self._common_neighbor_between(pair_subset_between)

        # Handle the `from_` case.
        elif node_subset_from is not None and node_subset_to is None:
            # Get the appropriate common_neighbor relationship.
            common_neighbor_rel = self._common_neighbor_from(node_subset_from)

        # Handle the `from_`/`to` case.
        elif node_subset_from is not None and node_subset_to is not None:
            common_neighbor_rel = self._common_neighbor_from_to(node_subset_from, node_subset_to)
            # Note that _common_neighbor_from_to handles optimization
            # when the from_ and to sets are object-identical.

        # Handle the `full` case.
        else:
            # Use cached full relationship.
            common_neighbor_rel = self._common_neighbor

        # Handle `count_neighbor_rel` for unconstrained versus constrained cases.
        if pair_subset_between is None and node_subset_from is None:
             # Unconstrained case.
            count_neighbor_rel = self._count_neighbor

        else:
            # Constrained cases.

            # Extract common neighbors that appear in
            # the constrained common_neighbor relationship.
            common_neighbors_subset = self._model.Relationship(
                f"{{node:{self._NodeConceptStr}}} is a relevant common neighbor"
            )
            node_x, node_y, neighbor_z = self.Node.ref(), self.Node.ref(), self.Node.ref()
            where(
                common_neighbor_rel(node_x, node_y, neighbor_z)
            ).define(
                common_neighbors_subset(neighbor_z)
            )

            # From those common neighbors,
            # build a constrained count_neighbor relationship.
            count_neighbor_rel = self._count_neighbor_of(common_neighbors_subset)

        # Define the Adamic-Adar aggregation using the selected relationships.
        node_u, node_v, common_neighbor = self.Node.ref(), self.Node.ref(), self.Node.ref()
        neighbor_count = Integer.ref()
        where(
            _score := sum(common_neighbor, 1.0 / natural_log(neighbor_count)).per(node_u, node_v).where(
                common_neighbor_rel(node_u, node_v, common_neighbor),
                count_neighbor_rel(common_neighbor, neighbor_count),
            )
        ).define(_adamic_adar_rel(node_u, node_v, _score))

        return _adamic_adar_rel


    @include_in_docs
    def preferential_attachment(
            self,
            *,
            full: Optional[bool] = None,
            from_: Optional[Relationship] = None,
            to: Optional[Relationship] = None,
            between: Optional[Relationship] = None,
        ):
        """Returns a ternary relationship containing
        the preferential attachment score for pairs of nodes.

        The preferential attachment score between two nodes `u` and `v` is the
        number of nodes adjacent to `u` multiplied by the number of nodes
        adjacent to `v`.

        Parameters
        ----------
        full : bool, optional
            If ``True``, computes the preferential attachment score for all pairs
            of nodes in the graph. This computation can be expensive for large graphs,
            as the result can scale quadratically in the number of nodes. Mutually exclusive
            with other parameters.
            Default is ``None``.
        from_ : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. When
            provided, constrains the domain of the preferential attachment computation: only
            preferential attachment scores for node pairs where the first node is
            in this relationship are computed and returned. Mutually exclusive with
            ``full`` and ``between``.
            Default is ``None``.
        to : Relationship, optional
            A unary relationship containing a subset of the graph's nodes. Can only
            be used together with the ``from_`` parameter. When provided with ``from_``,
            constrains the domain of the preferential attachment computation: only
            preferential attachment scores for node pairs where the first node is
            in ``from_`` and the second node is in ``to`` are computed and returned.
            Default is ``None``.
        between : Relationship, optional
            A binary relationship containing pairs of nodes. When provided,
            constrains the domain of the preferential attachment computation: only
            preferential attachment scores for the specific node pairs in
            this relationship are computed and returned. Mutually exclusive
            with other parameters.
            Default is ``None``.

        Returns
        -------
        Relationship
            A ternary relationship where each tuple represents a pair of nodes
            and their preferential attachment score.

        Raises
        ------
        ValueError
            If ``full`` is provided with any other parameter.
            If ``between`` is provided with any other parameter.
            If ``from_`` is provided with any parameter other than ``to``.
            If none of ``full``, ``from_``, or ``between`` is provided.
            If ``full`` is not ``True`` or ``None``.
        AssertionError
            If ``from_``, ``to``, or ``between`` is not a ``Relationship``.
            If ``from_``, ``to``, or ``between`` is not attached to the same model as the graph.
            If ``from_``, ``to``, or ``between`` does not contain the graph's ``Node`` concept.
            If ``from_`` or ``to`` is not a unary relationship.
            If ``between`` is not a binary relationship.

        Relationship Schema
        -------------------
        ``preferential_attachment(node_u, node_v, score)``

        * **node_u** (*Node*): The first node in the pair.
        * **node_v** (*Node*): The second node in the pair.
        * **score** (*Integer*): The preferential attachment score of the pair.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                |
        | :--------- | :-------- | :------------------- |
        | Undirected | Yes       |                      |
        | Directed   | Yes       |                      |
        | Weighted   | Yes       | Weights are ignored. |

        Notes
        -----
        The ``preferential_attachment(full=True)`` method computes and caches
        the full preferential attachment relationship for all pairs of nodes,
        providing efficient reuse across multiple calls. This can be expensive
        as the result contains O(|V|²) tuples.

        Calling ``preferential_attachment()`` without arguments raises a ``ValueError``,
        to ensure awareness and explicit acknowledgement (``full=True``) of this cost.

        In contrast, ``preferential_attachment(from_=subset)`` constrains the computation to
        tuples with the first position in the passed-in ``subset``. The result is
        not cached; it is specific to the call site. When a significant fraction of
        the preferential attachment relation is needed across a program,
        ``preferential_attachment(full=True)`` is typically more efficient. Use
        ``preferential_attachment(from_=subset)`` only when small subsets of
        the preferential attachment relationship are needed
        collectively across the program.

        The ``to`` parameter can be used together with ``from_`` to further
        constrain the computation: ``preferential_attachment(from_=subset_a, to=subset_b)``
        computes preferential attachment scores only for node pairs where the first node is in
        ``subset_a`` and the second node is in ``subset_b``. (Since ``preferential_attachment``
        is symmetric in its first two positions, using ``to`` without ``from_``would
        be functionally redundant, and is not allowed.)

        The ``between`` parameter provides another way to constrain the computation.
        Unlike ``from_`` and ``to``, which allow you to independently constrain the first
        and second positions in ``preferential_attachment`` tuples to sets of nodes, ``between``
        allows you constrain the first and second positions, jointly, to specific pairs
        of nodes.

        Examples
        --------
        >>> from relationalai.semantics import Model, define, select, Integer
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4 = [Node.new(id=i) for i in range(1, 5)]
        >>> define(n1, n2, n3, n4)
        >>> define(
        ...     Edge.new(src=n1, dst=n2),
        ...     Edge.new(src=n2, dst=n3),
        ...     Edge.new(src=n3, dst=n3),
        ...     Edge.new(src=n2, dst=n4),
        ...     Edge.new(src=n4, dst=n3),
        ... )
        >>>
        >>> # 3. Select the preferential attachment scores from the full relationship
        >>> u, v = Node.ref("u"), Node.ref("v")
        >>> score = Integer.ref("score")
        >>> preferential_attachment = graph.preferential_attachment(full=True)
        >>> select(
        ...     u.id, v.id, score,
        ... ).where(
        ...     preferential_attachment(u, v, score),
        ...     u.id == 1,
        ...     v.id == 3,
        ... ).inspect()
        ▰▰▰▰ Setup complete
           id  id2  score
        0   1    3      3

        >>> # 4. Use 'from_' parameter to constrain the set of nodes for the first position
        >>> # Define a subset containing only node 1
        >>> from relationalai.semantics import where
        >>> subset = model.Relationship(f"{{node:{Node}}} is in subset")
        >>> node = Node.ref()
        >>> where(node.id == 1).define(subset(node))
        >>>
        >>> # Get preferential attachment scores only for pairs where first node is in subset
        >>> constrained_preferential_attachment = graph.preferential_attachment(from_=subset)
        >>> select(u.id, v.id, score).where(constrained_preferential_attachment(u, v, score)).inspect()
        ▰▰▰▰ Setup complete
           id  id2  score
        0   1    1      1
        1   1    2      3
        2   1    3      3
        3   1    4      3

        >>> # 5. Use both 'from_' and 'to' parameters to constrain both positions
        >>> from_subset = model.Relationship(f"{{node:{Node}}} is in from_subset")
        >>> to_subset = model.Relationship(f"{{node:{Node}}} is in to_subset")
        >>> where(node.id == 1).define(from_subset(node))
        >>> where(node.id == 3).define(to_subset(node))
        >>>
        >>> # Get preferential attachment scores only where first node is in from_subset and second node is in to_subset
        >>> constrained_preferential_attachment = graph.preferential_attachment(from_=from_subset, to=to_subset)
        >>> select(u.id, v.id, score).where(constrained_preferential_attachment(u, v, score)).inspect()
        ▰▰▰▰ Setup complete
           id  id2  score
        0   1    3      3

        >>> # 6. Use 'between' parameter to constrain to specific pairs of nodes
        >>> pairs = model.Relationship(f"{{node_a:{Node}}} and {{node_b:{Node}}} are a pair")
        >>> node_a, node_b = Node.ref(), Node.ref()
        >>> where(node_a.id == 1, node_b.id == 3).define(pairs(node_a, node_b))
        >>> where(node_a.id == 2, node_b.id == 4).define(pairs(node_a, node_b))
        >>>
        >>> # Get preferential attachment scores only for the specific pairs (1, 3) and (2, 4)
        >>> constrained_preferential_attachment = graph.preferential_attachment(between=pairs)
        >>> select(u.id, v.id, score).where(constrained_preferential_attachment(u, v, score)).inspect()
        ▰▰▰▰ Setup complete
           id  id2  score
        0   1    3      3
        1   2    4      6

        """
        # Validate domain constraint parameters (preferential_attachment is symmetric).
        symmetric = True
        self._validate_domain_constraint_parameters(
            'preferential_attachment', symmetric, full, from_, to, between
        )

        # At this point, exactly one of `full`, `from_`, or `between`
        # has been provided, and if `to` is provided, `from_` is also provided.

        # Handle `between`.
        if between is not None:
            self._validate_pair_subset_parameter(between)
            return self._preferential_attachment_between(between)

        # Handle `from_` (and potentially `to`).
        if from_ is not None:
            self._validate_node_subset_parameter('from_', from_)
            if to is not None:
                self._validate_node_subset_parameter('to', to)
                return self._preferential_attachment_from_to(from_, to)
            return self._preferential_attachment_from(from_)

        # Handle `full`.
        return self._preferential_attachment

    @cached_property
    def _preferential_attachment(self):
        """Lazily define and cache the full preferential_attachment relationship."""
        _preferential_attachment_rel = self._create_preferential_attachment_relationship()
        _preferential_attachment_rel.annotate(annotations.track("graphs", "preferential_attachment"))
        return _preferential_attachment_rel

    def _preferential_attachment_from(self, node_subset_from: Relationship):
        """
        Create a preferential_attachment relationship, with the first position in each
        tuple constrained to be in the given subset of nodes. Note this relationship
        is not cached; it is specific to the callsite.
        """
        _preferential_attachment_rel = self._create_preferential_attachment_relationship(
            node_subset_from=node_subset_from
        )
        _preferential_attachment_rel.annotate(annotations.track("graphs", "preferential_attachment_from"))
        return _preferential_attachment_rel

    def _preferential_attachment_from_to(self, node_subset_from: Relationship, node_subset_to: Relationship):
        """
        Create a preferential_attachment relationship, with the first position in each
        tuple constrained to be in `node_subset_from`, and the second position in
        each tuple constrained to be in `node_subset_to`. Note this relationship
        is not cached; it is specific to the callsite.
        """
        _preferential_attachment_rel = self._create_preferential_attachment_relationship(
            node_subset_from=node_subset_from,
            node_subset_to=node_subset_to
        )
        _preferential_attachment_rel.annotate(annotations.track("graphs", "preferential_attachment_from_to"))
        return _preferential_attachment_rel

    def _preferential_attachment_between(self, pair_subset_between: Relationship):
        """
        Create a preferential_attachment relationship, with the first and second position
        in each tuple jointly constrained to be in the given set of pairs
        of nodes. Note this relationship is not cached;
        it is specific to the callsite.
        """
        _preferential_attachment_rel = self._create_preferential_attachment_relationship(
            pair_subset_between=pair_subset_between
        )
        _preferential_attachment_rel.annotate(annotations.track("graphs", "preferential_attachment_between"))
        return _preferential_attachment_rel

    def _create_preferential_attachment_relationship(
        self,
        *,
        node_subset_from: Optional[Relationship] = None,
        node_subset_to: Optional[Relationship] = None,
        pair_subset_between: Optional[Relationship] = None,
    ):
        """
        Create preferential_attachment relationship, optionally constrained by
        the provided node subsets or pair subset.
        """
        _preferential_attachment_rel = self._model.Relationship(
            f"{{node_u:{self._NodeConceptStr}}} and {{node_v:{self._NodeConceptStr}}} "
            f"have preferential attachment score {{score:Integer}}"
        )

        # Branch by case to select appropriate count_neighbor and isolated_node relationships,
        # and to define relevant constraints on the separate and joint domains of node_u and node_v.
        node_u, node_v = self.Node.ref(), self.Node.ref()

        # Handle the `between` case.
        if pair_subset_between is not None:
            # Collect nodes that appear in the subset by position.
            first_position_subset = self._model.Relationship(f"{{node:{self._NodeConceptStr}}}")
            second_position_subset = self._model.Relationship(f"{{node:{self._NodeConceptStr}}}")
            node_x, node_y = self.Node.ref(), self.Node.ref()
            where(
                pair_subset_between(node_x, node_y)
            ).define(
                first_position_subset(node_x),
                second_position_subset(node_y)
            )

            # Constituents of non-isolated-nodes rule.
            non_isolated_rule_uv_constraint = [pair_subset_between(node_u, node_v)]
            count_neighbor_u_rel = self._count_neighbor_of(first_position_subset)
            count_neighbor_v_rel = self._count_neighbor_of(second_position_subset)

            # Constituents of u-isolated rule.
            isolated_u_rel = self._isolated_node_of(first_position_subset)
            isolated_u_rule_uv_constraint = [pair_subset_between(node_u, node_v)]

            # Constituents of v-isolated rule.
            isolated_v_rel = self._isolated_node_of(second_position_subset)
            isolated_v_rule_uv_constraint = [pair_subset_between(node_u, node_v)]

        # Handle the `from_` case.
        elif node_subset_from is not None and node_subset_to is None:
            # NOTE: It isn't necessary to compute _count_neighbor_of
            #   and _isolated_node_of for node_subset_from, given
            #   we have to compute _count_neighbor and _isolated_node
            #   for the unconstrained second position anyway. That does
            #   require additional constraints as seen below, though.
            #
            #   It's not clear to this author that there is a more clever
            #   way to do this, given that in preferential attachment,
            #   constraining one position implies no constraint on the
            #   other position, unlike in, e.g., common neighbor?

            # Constituents of non-isolated-nodes rule.
            non_isolated_rule_uv_constraint = [node_subset_from(node_u)]
            count_neighbor_u_rel = self._count_neighbor
            count_neighbor_v_rel = self._count_neighbor

            # Constituents of u-isolated rule.
            isolated_u_rel = self._isolated_node
            isolated_u_rule_uv_constraint = [
                node_subset_from(node_u),
                self.Node(node_v)
            ]

            # Constituents of v-isolated rule.
            isolated_v_rel = self._isolated_node
            isolated_v_rule_uv_constraint = [node_subset_from(node_u)]

        # Handle the `from_`/`to` case.
        elif node_subset_from is not None and node_subset_to is not None:
            # Check for object identity optimization.
            if node_subset_from is node_subset_to:
                # Constituents of non-isolated-nodes rule.
                non_isolated_rule_uv_constraint = []
                count_neighbor_u_rel = self._count_neighbor_of(node_subset_from)
                count_neighbor_v_rel = count_neighbor_u_rel

                # Constituents of u-isolated rule.
                isolated_u_rel = self._isolated_node_of(node_subset_from)
                isolated_u_rule_uv_constraint = [node_subset_to(node_v)]

                # Constituents of v-isolated rule.
                isolated_v_rel = isolated_u_rel
                isolated_v_rule_uv_constraint = [node_subset_from(node_u)]
            else:
                # Constituents of non-isolated-nodes rule.
                non_isolated_rule_uv_constraint = []
                count_neighbor_u_rel = self._count_neighbor_of(node_subset_from)
                count_neighbor_v_rel = self._count_neighbor_of(node_subset_to)

                # Constituents of u-isolated rule.
                isolated_u_rel = self._isolated_node_of(node_subset_from)
                isolated_u_rule_uv_constraint = [node_subset_to(node_v)]

                # Constituents of v-isolated rule.
                isolated_v_rel = self._isolated_node_of(node_subset_to)
                isolated_v_rule_uv_constraint = [node_subset_from(node_u)]


        # Handle the `full` case.
        else:
            # Constituents of non-isolated-nodes rule.
            non_isolated_rule_uv_constraint = []
            count_neighbor_u_rel = self._count_neighbor
            count_neighbor_v_rel = self._count_neighbor

            # Constituents of u-isolated rule.
            isolated_u_rel = self._isolated_node
            isolated_u_rule_uv_constraint = [self.Node(node_v)]

            # Constituents of v-isolated rule.
            isolated_v_rel = self._isolated_node
            isolated_v_rule_uv_constraint = [self.Node(node_u)]

        # Define shared logic, which has three cases.
        count_u, count_v = Integer.ref(), Integer.ref()

        # Case where node u is isolated, and node v is any node (respecting constraints): score 0.
        where(
            isolated_u_rel(node_u),
            *isolated_u_rule_uv_constraint,
        ).define(_preferential_attachment_rel(node_u, node_v, 0))

        # Case where node u is any node (respecting constraints), and node v is isolated: score 0.
        where(
            *isolated_v_rule_uv_constraint,
            isolated_v_rel(node_v)
        ).define(_preferential_attachment_rel(node_u, node_v, 0))

        # Case where neither node is isolated: score is count_neighbor[u] * count_neighbor[v].
        where(
            *non_isolated_rule_uv_constraint,
            count_neighbor_u_rel(node_u, count_u),
            count_neighbor_v_rel(node_v, count_v)
        ).define(_preferential_attachment_rel(node_u, node_v, count_u * count_v))

        return _preferential_attachment_rel


    @cached_property
    def _isolated_node(self):
        """Lazily define and cache the self._isolated_node relationship."""
        return self._create_isolated_node_relationship()

    def _isolated_node_of(self, node_subset: Relationship):
        """
        Create an _isolated_node relationship constrained to the subset of nodes
        in `node_subset`. Note this relationship is not cached; it is
        specific to the callsite.
        """
        return self._create_isolated_node_relationship(node_subset=node_subset)

    def _create_isolated_node_relationship(
        self,
        *,
        node_subset: Optional[Relationship] = None,
    ):
        """
        Create _isolated_node relationship, optionally constrained by
        the provided node subset.
        """
        _isolated_node_rel = self._model.Relationship(f"{{node:{self._NodeConceptStr}}} is isolated")

        neighbor_node = self.Node.ref()
        if node_subset is not None:
            neighbor_rel = self._neighbor_of(node_subset)
            node_constraint = [node_subset(self.Node)]
        else:
            neighbor_rel = self._neighbor
            node_constraint = []

        where(
            *node_constraint,
            not_(neighbor_rel(self.Node, neighbor_node))
        ).define(_isolated_node_rel(self.Node))

        return _isolated_node_rel


    @cached_property
    def _non_isolated_node(self):
        """Lazily define and cache the self._non_isolated_node relationship."""
        # Primarily a helper for the primitive graph algorithms at this time.
        _non_isolated_node_rel = self._model.Relationship(f"{{node:{self._NodeConceptStr}}} is not isolated")

        node, neighbor = self.Node.ref(), self.Node.ref()
        where(node, self._neighbor(node, neighbor)).define(_non_isolated_node_rel(node))

        return _non_isolated_node_rel


    @cached_property
    def _primitive_node_to_index_rel(self):
        """
        The graph primitives operate over node indices, contiguous from one;
        compute a map from the identifier for each non-isolated node to such an index.
        Lazily define and cache that relationship for shared use across primitive algorithms.
        """
        _node_to_index_rel = self._model.Relationship(f"{{node:{self._NodeConceptStr}}} has {{index:Integer}}")

        node = self.Node.ref()
        where(
            self._non_isolated_node(node),
            index := rank(node)
        ).define(
            _node_to_index_rel(node, index)
        )

        return _node_to_index_rel

    @cached_property
    def _primitive_weight_list(self):
        """
        The graph primitives operate over a normalized weight list, where
        the nodes are represented by their contiguous indices as Int64s.
        Lazily define and cache that normalized weight list for shared use
        across primitive algorithms.
        """
        _normalized_weight_list = self._model.Relationship("{u:Int64} {v:Int64} {w:Float}")

        src_node, dst_node, weight = self.Node.ref(), self.Node.ref(), Float.ref()
        src_index, dst_index = Integer.ref(), Integer.ref()
        where(
            self._weight(src_node, dst_node, weight),
            self._primitive_node_to_index_rel(src_node, src_index),
            self._primitive_node_to_index_rel(dst_node, dst_index)
        ).define(
            _normalized_weight_list(int64(src_index), int64(dst_index), weight)
        )

        return _normalized_weight_list

    @cached_property
    def _primitive_node_count(self):
        """
        The graph primitives operate only over non-isolated nodes;
        compute the number of non-isolated nodes as an Int64.
        Lazily define and cache that count for shared use across primitive algorithms.
        """
        _normalized_node_count = self._model.Relationship("{node_count:Int64}")

        define(_normalized_node_count(
            int64(count(self.Node).where(self._non_isolated_node(self.Node)))
        ))

        return _normalized_node_count

    @cached_property
    def _primitive_edge_count(self):
        """
        The graph primitives operate over a normalized weight list;
        compute the number of normalized edges as an Int64.
        Lazily define and cache that count for shared use across primitive algorithms.

        (Note that the count of normalized edges does not in general match
        graph.num_edges(); it should match for directed graphs, but not for
        undirected graphs, where num_edges computes the number of
        undirected rather than directed edges.)
        """
        _normalized_edge_count = self._model.Relationship("{edge_count:Int64}")

        u_index, v_index = builder_internal.Int64.ref(), builder_internal.Int64.ref()
        define(_normalized_edge_count(
            int64(count(u_index, v_index).where(self._primitive_weight_list(u_index, v_index, Float)))
        ))

        return _normalized_edge_count

    def _create_primitive_algorithm_relationship(
        self,
        primitive_name: str,
        primitive_params: list,
    ):
        """
        Helper method for infomap, louvain, and label propagation,
        i.e. the graph algorithsm that exercise graph primitives.

        Create community assignment and diagnostic information relationships
        exercising the specified primitive algorithm with the provided parameters.
        """
        # Create relationship in which to store the final community assignments.
        _community_assignments_rel = self._model.Relationship(
            f"{{node:{self._NodeConceptStr}}} belongs to {{community:Integer}}")

        # The graph primitives operate over a normalized form of the graph.
        # Most of the logic below transforms from the graph, to that normalized
        # form, and back again.

        # The graph primitives operate over node indices, contiguous from one;
        # compute a map from the identifier for each non-isolated node to such an index.
        _primitive_node_to_index_rel = self._primitive_node_to_index_rel

        # The graph primitives operate over a normalized weight list, where
        # the nodes are represented by their contiguous indices as Int64s.
        _primitive_weight_list = self._primitive_weight_list

        # Compute the number of non-isolated nodes and normalized edges, as int64s.
        # (Note that the count of normalized edges does not in general match
        # graph.num_edges(); it should match for directed graphs, but not for
        # undirected graphs, where num_edges computes the number of
        # undirected rather than directed edges.)
        _primitive_node_count = self._primitive_node_count
        _primitive_edge_count = self._primitive_edge_count

        # Invoke the graph primitive over the normalized data.
        primitive_expr = builder_internal.Expression(
            builder_internal.Relationship.builtins[primitive_name],
            builder_internal.TypeRef(_primitive_weight_list),
            builder_internal.TypeRef(_primitive_node_count),
            builder_internal.TypeRef(_primitive_edge_count),
            *primitive_params,
            builder_internal.String.ref("diagnostic_info"),
            builder_internal.Int64.ref("node_index"),
            builder_internal.Int64.ref("community")
        )

        last_input_arg_offset = 3 + len(primitive_params) - 1
        prim_diagnostic_info = primitive_expr._arg_ref(last_input_arg_offset + 1)
        prim_node_index = primitive_expr._arg_ref(last_input_arg_offset + 2)
        prim_community = primitive_expr._arg_ref(last_input_arg_offset + 3)

        # Extract the primitive's community assignments for
        # non-isolated nodes into a relation, mapping from
        # Int64s to Integers for smoother consumption downstream.
        _primitive_assignments_rel = self._model.Relationship("{node_index:Integer} has {community:Integer}")
        define(_primitive_assignments_rel(prim_node_index, prim_community))
        # TODO: May be possible to remove this intermediate relationship,
        #    by directly mapping into `_infomap_result_rel` below.
        #    But if so, need to take care not to introduce recursion in rules below.

        # Transform the primitive's community assignments, which map
        # node indices to communities, to a map from nodes to communities.
        # Note that this covers only non-isolated nodes; isolated handled later.
        node = self.Node.ref()
        node_index = Integer.ref()
        community = Integer.ref()
        where(
            _primitive_node_to_index_rel(node, node_index),
            _primitive_assignments_rel(node_index, community),
        ).define(
            _community_assignments_rel(node, community)
        )

        # Each isolated node must be assigned to its own unique community.
        # The primitive's community assignments are contiguous integers from one,
        # so we can assign isolated nodes to communities by offsetting their
        # enumeration index by the maximum community assigned by the primitive.
        isolated_node = self.Node.ref()
        nonisolated_index = Integer.ref()
        nonisolated_comm = Integer.ref()
        where(
            self._isolated_node(isolated_node),
            isolated_node_rank := rank(isolated_node),
            max_nonisolated_comm := (
                max(nonisolated_index, nonisolated_comm).where(
                    _primitive_assignments_rel(nonisolated_index, nonisolated_comm)
                ) | 0
            ),
            isolated_comm := isolated_node_rank + max_nonisolated_comm
        ).define(_community_assignments_rel(isolated_node, isolated_comm))

        # Extract diagnostic information from the primitive.
        _diagnostic_info_rel = self._model.Relationship("{diagnostic_info:String}")
        define(_diagnostic_info_rel(prim_diagnostic_info))

        # Return both the community assignments and diagnostic information.
        return _community_assignments_rel, _diagnostic_info_rel


    @include_in_docs
    def infomap(
            self,
            max_levels: int = 1,
            max_sweeps: int = 20,
            level_tolerance: float = 0.01,
            sweep_tolerance: float = 0.0001,
            teleportation_rate: float = 0.15,
            visit_rate_tolerance: float = 1e-15,
            randomization_seed: int = 8675309,
            diagnostic_info: bool = False,
    ):
        """Partitions nodes into communities using a variant of the Infomap algorithm.

        This method maps nodes to community assignments based on the flow of
        information on the graph.

        Parameters
        ----------
        max_levels : int, optional
            The maximum number of levels at which to optimize. Must be a
            positive integer. Default is 1.
        max_sweeps : int, optional
            The maximum number of sweeps within each level. Must be a non-negative
            integer. Default is 20.
        level_tolerance : float, optional
            Map equation progress threshold to continue to the next level.
            Must be a non-negative float. Default is 0.01.
        sweep_tolerance : float, optional
            Map equation progress threshold to continue to the next sweep.
            Must be a non-negative float. Default is 0.0001.
        teleportation_rate : float, optional
            Teleportation rate for ergodic node visit rate calculation. Must be
            a float in (0, 1]. Default is 0.15.
        visit_rate_tolerance : float, optional
            Convergence tolerance for ergodic node visit rate calculation. Must
            be a positive float. Default is 1e-15.
        randomization_seed : int, optional
            The random number generator seed for the run. Must be a non-negative
            integer. Default is 8675309.
        diagnostic_info : bool, optional
            If ``True``, returns diagnostic information alongside
            community assignments. If ``False`` (default), returns only community
            assignments.

        Returns
        -------
        Relationship or tuple of Relationships
            If ``diagnostic_info`` is ``False`` (default), returns a binary
            relationship where each tuple represents a node and its community
            assignment.

            If ``diagnostic_info`` is ``True``, returns a tuple of
            ``(community_assignments, diagnostic_info)`` where:

            - ``community_assignments`` is the binary relationship described above
            - ``diagnostic_info`` is a unary relationship containing a diagnostic
              string describing the algorithm's convergence and termination behavior

        Relationship Schema
        -------------------
        When ``diagnostic_info=False`` (default):

        ``infomap(node, community_label)``

        * **node** (*Node*): The node.
        * **community_label** (*Integer*): The label of the community the node
          belongs to.

        When ``diagnostic_info=True``, returns two relationships:

        - ``infomap(node, community_label)`` as described above; and
        - ``diagnostic_info(diagnostic_string)``

        * **diagnostic_string** (*String*): A diagnostic string describing the
          algorithm's convergence and termination behavior.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                           |
        | :--------- | :-------- | :------------------------------ |
        | Undirected | Yes       |                                 |
        | Directed   | Yes       |                                 |
        | Weighted   | Yes       | Only positive weights supported.|
        | Unweighted | Yes       |                                 |

        Notes
        -----
        This implementation of Infomap minimizes the map equation via a
        Louvain-like optimization heuristic; this is often referred to as
        "core" Infomap in the literature. Computation of the ergodic node
        visit frequencies is done via regularized power iteration, with
        regularization via a uniform teleportation probability of 0.15,
        matching the nominal selection in the literature.

        Examples
        --------
        **Unweighted Graph Example**

        Compute community assignments for each node in an undirected graph. Here,
        an undirected dumbbell graph resolves into two communities, namely its
        two constituent three-cliques.

        >>> from relationalai.semantics import Model, define, select, Integer
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges for a dumbbell graph
        >>> n1, n2, n3, n4, n5, n6 = [Node.new(id=i) for i in range(1, 7)]
        >>> define(n1, n2, n3, n4, n5, n6)
        >>> define(
        ...     # The first three-clique.
        ...     Edge.new(src=n1, dst=n2), Edge.new(src=n1, dst=n3), Edge.new(src=n2, dst=n3),
        ...     # The second three-clique.
        ...     Edge.new(src=n4, dst=n5), Edge.new(src=n4, dst=n6), Edge.new(src=n5, dst=n6),
        ...     # The connection between the three-cliques.
        ...     Edge.new(src=n1, dst=n4)
        ... )
        >>>
        >>> # 3. Compute community assignments and inspect
        >>> node, label = Node.ref("node"), Integer.ref("label")
        >>> infomap = graph.infomap()
        >>> select(node.id, label).where(infomap(node, label)).inspect()
        # The output will show each node mapped to a community:
        # (1, 1)
        # (2, 1)
        # (3, 1)
        # (4, 2)
        # (5, 2)
        # (6, 2)

        **Weighted Graph Example**

        Compute community assignments for each node in an undirected weighted
        graph. Here, a six-clique has the edges forming a dumbbell graph
        within the six-clique strongly weighted, and the remaining edges
        weakly weighted. The graph resolves into two communities, namely the
        two three-cliques constituent of the dumbbell embedded in the six-clique.

        >>> # 1. Set up a weighted, undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=True)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4, n5, n6 = [Node.new(id=i) for i in range(1, 7)]
        >>> define(n1, n2, n3, n4, n5, n6)
        >>> define(
        ...     # First embedded three-clique.
        ...     Edge.new(src=n1, dst=n2, weight=1.0),
        ...     Edge.new(src=n1, dst=n3, weight=1.0),
        ...     Edge.new(src=n2, dst=n3, weight=1.0),
        ...     # Second embedded three-clique.
        ...     Edge.new(src=n4, dst=n5, weight=1.0),
        ...     Edge.new(src=n4, dst=n6, weight=1.0),
        ...     Edge.new(src=n5, dst=n6, weight=1.0),
        ...     # Slightly weaker connection between the embedded three-cliques.
        ...     Edge.new(src=n1, dst=n4, weight=0.5),
        ...     # Weaker edges connecting the six-clique in full.
        ...     Edge.new(src=n1, dst=n5, weight=0.1), Edge.new(src=n1, dst=n6, weight=0.1),
        ...     Edge.new(src=n2, dst=n4, weight=0.1), Edge.new(src=n2, dst=n5, weight=0.1),
        ...     Edge.new(src=n2, dst=n6, weight=0.1), Edge.new(src=n3, dst=n4, weight=0.1),
        ...     Edge.new(src=n3, dst=n5, weight=0.1), Edge.new(src=n3, dst=n6, weight=0.1)
        ... )
        >>>
        >>> # 3. Compute community assignments and inspect
        >>> node, label = Node.ref("node"), Integer.ref("label")
        >>> infomap = graph.infomap()
        >>> select(node.id, label).where(infomap(node, label)).inspect()
        # The output will show the two-community dumbbell structure:
        # (1, 1)
        # (2, 1)
        # (3, 1)
        # (4, 2)
        # (5, 2)
        # (6, 2)

        """
        _assert_type("infomap:max_levels", max_levels, int)
        _assert_type("infomap:max_sweeps", max_sweeps, int)
        _assert_exclusive_lower_bound("infomap:max_levels", max_levels, 0)
        _assert_inclusive_lower_bound("infomap:max_sweeps", max_sweeps, 0)

        _assert_type("infomap:level_tolerance", level_tolerance, Real)
        _assert_type("infomap:sweep_tolerance", sweep_tolerance, Real)
        _assert_inclusive_lower_bound("infomap:level_tolerance", level_tolerance, 0.0)
        _assert_inclusive_lower_bound("infomap:sweep_tolerance", sweep_tolerance, 0.0)

        _assert_type("infomap:teleportation_rate", teleportation_rate, Real)
        _assert_inclusive_lower_bound("infomap:teleportation_rate", teleportation_rate, 1e-4)
        _assert_exclusive_upper_bound("infomap:teleportation_rate", teleportation_rate, 1.0)

        _assert_type("infomap:visit_rate_tolerance", visit_rate_tolerance, Real)
        _assert_exclusive_lower_bound("infomap:visit_rate_tolerance", visit_rate_tolerance, 0.0)

        _assert_type("infomap:randomization_seed", randomization_seed, int)
        _assert_exclusive_lower_bound("infomap:randomization_seed", randomization_seed, 0)

        # Collect parameters to rel_primitive_infomap,
        # appropriately typed and ordered for the primitive.
        infomap_parameters = [
            float(teleportation_rate),
            float(visit_rate_tolerance),
            float(level_tolerance),
            float(sweep_tolerance),
            int(max_levels),
            int(max_sweeps),
            int(randomization_seed),
        ]

        # Create infomap community assignment and, if requested,
        # diagnostic information relationships.
        _infomap_assignments_rel, _infomap_diagnostic_rel = \
            self._create_primitive_algorithm_relationship(
                "infomap", infomap_parameters
            )

        # Attach tracking information to the community assignment relationship.
        _infomap_assignments_rel.annotate(annotations.track("graphs", "infomap"))

        # Return either just the community assignments, or both
        # the community assignments and diagnostic information, per request.
        if diagnostic_info:
            return _infomap_assignments_rel, _infomap_diagnostic_rel
        else:
            return _infomap_assignments_rel


    @include_in_docs
    def louvain(
            self,
            max_levels: int = 1,
            max_sweeps: int = 20,
            level_tolerance: float = 0.01,
            sweep_tolerance: float = 0.0001,
            randomization_seed: int = 8675309,
            diagnostic_info: bool = False,
    ):
        """Partitions nodes into communities using the Louvain algorithm.

        This method detects communities by maximizing a modularity score. It is
        only applicable to undirected graphs.

        Parameters
        ----------
        max_levels : int, optional
            The maximum number of levels at which to optimize. Must be a
            positive integer. Default is 1.
        max_sweeps : int, optional
            The maximum number of sweeps within each level. Must be a
            non-negative integer. Default is 20.
        level_tolerance : float, optional
            Modularity progress threshold to continue to the next level.
            Must be a non-negative float. Default is 0.01.
        sweep_tolerance : float, optional
            Modularity progress threshold to continue to the next sweep.
            Must be a non-negative float. Default is 0.0001.
        randomization_seed : int, optional
            The random number generator seed for the run. Must be a
            non-negative integer. Default is 8675309.
        diagnostic_info : bool, optional
            If ``True``, returns diagnostic information alongside community
            assignments. If ``False`` (default), returns only community assignments.

        Returns
        -------
        Relationship or tuple of Relationships
            If ``diagnostic_info`` is ``False`` (default), returns a binary
            relationship where each tuple represents a node and its community
            assignment.

            If ``diagnostic_info`` is ``True``, returns a tuple of
            ``(community_assignments, diagnostic_info)`` where:

            - ``community_assignments`` is the binary relationship described above
            - ``diagnostic_info`` is a unary relationship containing a diagnostic
              string describing the algorithm's termination behavior.

        Raises
        ------
        DirectedGraphNotSupported
            If the graph is directed.

        Relationship Schema
        -------------------
        When ``diagnostic_info=False`` (default):

        ``louvain(node, community_label)``

        * **node** (*Node*): The node.
        * **community_label** (*Integer*): The label of the community the node
          belongs to.

        When ``diagnostic_info=True``, returns two relationships:

        - ``louvain(node, community_lable)`` as described above; and
        - ``diagnostic_info(diagnostic_string)``

        * **diagnostic_string** (*String*): A diagnostic string describing the
          algorithm's convergence and termination behavior.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                           |
        | :--------- | :-------- | :------------------------------ |
        | Undirected | Yes       |                                 |
        | Directed   | No        | Not supported by this implementation. |
        | Weighted   | Yes       | Only positive weights supported.|
        | Unweighted | Yes       |                                 |

        Notes
        -----
        This implementation of the Louvain algorithm is consistent with the
        modularity definition (Eq. 1) in "Fast unfolding of communities in
        large networks", Blondel et al J. Stat. Mech. (2008) P10008.

        Examples
        --------
        **Unweighted Graph Example**

        Compute community assignments for each node in an undirected graph.
        Here, an undirected dumbbell graph resolves into two communities,
        namely its two constituent three-cliques.

        >>> from relationalai.semantics import Model, define, select, Integer
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges for a dumbbell graph
        >>> n1, n2, n3, n4, n5, n6 = [Node.new(id=i) for i in range(1, 7)]
        >>> define(n1, n2, n3, n4, n5, n6)
        >>> define(
        ...     # The first three-clique.
        ...     Edge.new(src=n1, dst=n2), Edge.new(src=n1, dst=n3), Edge.new(src=n2, dst=n3),
        ...     # The second three-clique.
        ...     Edge.new(src=n4, dst=n5), Edge.new(src=n4, dst=n6), Edge.new(src=n5, dst=n6),
        ...     # The connection between the three-cliques.
        ...     Edge.new(src=n1, dst=n4)
        ... )
        >>>
        >>> # 3. Compute community assignments and inspect
        >>> node, label = Node.ref("node"), Integer.ref("label")
        >>> louvain = graph.louvain()
        >>> select(node.id, label).where(louvain(node, label)).inspect()
        # The output will show each node mapped to a community:
        # (1, 1)
        # (2, 1)
        # (3, 1)
        # (4, 2)
        # (5, 2)
        # (6, 2)

        **Weighted Graph Example**

        Compute community assignments for each node in an undirected weighted
        graph. Here, a six-clique has the edges forming a dumbbell graph
        within the six-clique strongly weighted, and the remaining edges
        weakly weighted. The graph resolves into two communities, namely the
        two three-cliques constituent of the dumbbell embedded in the
        six-clique.

        >>> # 1. Set up a weighted, undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=True)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4, n5, n6 = [Node.new(id=i) for i in range(1, 7)]
        >>> define(n1, n2, n3, n4, n5, n6)
        >>> define(
        ...     # First embedded three-clique.
        ...     Edge.new(src=n1, dst=n2, weight=1.0),
        ...     Edge.new(src=n1, dst=n3, weight=1.0),
        ...     Edge.new(src=n2, dst=n3, weight=1.0),
        ...     # Second embedded three-clique.
        ...     Edge.new(src=n4, dst=n5, weight=1.0),
        ...     Edge.new(src=n4, dst=n6, weight=1.0),
        ...     Edge.new(src=n5, dst=n6, weight=1.0),
        ...     # Connection between the embedded three-cliques.
        ...     Edge.new(src=n1, dst=n4, weight=1.0),
        ...     # Weaker edges connecting the six-clique in full.
        ...     Edge.new(src=n1, dst=n5, weight=0.2), Edge.new(src=n1, dst=n6, weight=0.2),
        ...     Edge.new(src=n2, dst=n4, weight=0.2), Edge.new(src=n2, dst=n5, weight=0.2),
        ...     Edge.new(src=n2, dst=n6, weight=0.2), Edge.new(src=n3, dst=n4, weight=0.2),
        ...     Edge.new(src=n3, dst=n5, weight=0.2), Edge.new(src=n3, dst=n6, weight=0.2)
        ... )
        >>>
        >>> # 3. Compute community assignments and inspect
        >>> node, label = Node.ref("node"), Integer.ref("label")
        >>> louvain = graph.louvain()
        >>> select(node.id, label).where(louvain(node, label)).inspect()
        # The output will show the two-community dumbbell structure:
        # (1, 1)
        # (2, 1)
        # (3, 1)
        # (4, 2)
        # (5, 2)
        # (6, 2)

        """
        if self.directed:
            raise DirectedGraphNotSupported("louvain")

        _assert_type("louvain:max_levels", max_levels, int)
        _assert_type("louvain:max_sweeps", max_sweeps, int)
        _assert_exclusive_lower_bound("louvain:max_levels", max_levels, 0)
        _assert_inclusive_lower_bound("louvain:max_sweeps", max_sweeps, 0)

        _assert_type("louvain:level_tolerance", level_tolerance, Real)
        _assert_type("louvain:sweep_tolerance", sweep_tolerance, Real)
        _assert_inclusive_lower_bound("louvain:level_tolerance", level_tolerance, 0.0)
        _assert_inclusive_lower_bound("louvain:sweep_tolerance", sweep_tolerance, 0.0)

        _assert_type("louvain:randomization_seed", randomization_seed, int)
        _assert_exclusive_lower_bound("louvain:randomization_seed", randomization_seed, 0)

        # Collect parameters to rel_primitive_louvain,
        # appropriately typed and ordered for the primitive.
        louvain_parameters = [
            float(level_tolerance),
            float(sweep_tolerance),
            int(max_levels),
            int(max_sweeps),
            int(randomization_seed),
        ]

        # Create louvain community assignment and, if requested,
        # diagnostic information relationships.
        _louvain_assignments_rel, _louvain_diagnostic_rel = \
            self._create_primitive_algorithm_relationship(
                "louvain", louvain_parameters
            )

        # Attach tracking information to the community assignment relationship.
        _louvain_assignments_rel.annotate(annotations.track("graphs", "louvain"))

        # Return either just the community assignments, or both
        # the community assignments and diagnostic information, per request.
        if diagnostic_info:
            return _louvain_assignments_rel, _louvain_diagnostic_rel
        else:
            return _louvain_assignments_rel

    @include_in_docs
    def label_propagation(
            self,
            max_sweeps: int = 20,
            randomization_seed: int = 8675309,
            diagnostic_info: bool = False,
    ):
        """Partitions nodes into communities using the Label Propagation algorithm.

        This method maps nodes to community assignments via asynchronous
        label propagation.

        Parameters
        ----------
        max_sweeps : int, optional
            The maximum number of sweeps for label propagation to perform.
            Must be a positive integer. Default is 20.
        randomization_seed : int, optional
            The random number generator seed for the run. Must be a positive
            integer. Default is 8675309.
        diagnostic_info : bool, optional
            If ``True``, returns diagnostic information alongside
            community assignments. If ``False`` (default), returns only community
            assignments.

        Returns
        -------
        Relationship or tuple of Relationships
            If ``diagnostic_info`` is ``False`` (default), returns a binary
            relationship where each tuple represents a node and its community
            assignment.

            If ``diagnostic_info`` is ``True``, returns a tuple of
            ``(community_assignments, diagnostic_info)`` where:

            - ``community_assignments`` is the binary relationship described above
            - ``diagnostic_info`` is a unary relationship containing a diagnostic
              string describing the algorithm's termination behavior.

        Relationship Schema
        -------------------
        When ``diagnostic_info=False`` (default):

        ``label_propagation(node, community_label)``

        * **node** (*Node*): The node.
        * **community_label** (*Integer*): The label of the community the node
          belongs to.

        When ``diagnostic_info=True``, returns two relationships:

        - ``community_assignments(node, community_label)`` as described above; and
        - ``diagnostic_info(diganostic_string)``

        * **diagnostic_string** (*String*): A diagnostic string describing the
          algorithm's convergence and termination behavior.

        Supported Graph Types
        ---------------------
        | Graph Type | Supported | Notes                           |
        | :--------- | :-------- | :------------------------------ |
        | Undirected | Yes       |                                 |
        | Directed   | Yes       |                                 |
        | Weighted   | Yes       | Only positive weights supported.|
        | Unweighted | Yes       |                                 |

        Notes
        -----
        This implementation of asynchronous label propagation breaks ties
        between neighboring labels with equal cumulative edge weight (and
        frequency in the unweighted case) uniformly at random, but with a
        static seed.

        Examples
        --------
        **Unweighted Graph Example**

        Compute community assignments for each node in an undirected graph. Here,
        an undirected dumbbell graph resolves into two communities, namely its
        two constituent three-cliques.

        >>> from relationalai.semantics import Model, define, select, Integer
        >>> from relationalai.semantics.reasoners.graph import Graph
        >>>
        >>> # 1. Set up an undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=False)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges for a dumbbell graph
        >>> n1, n2, n3, n4, n5, n6 = [Node.new(id=i) for i in range(1, 7)]
        >>> define(n1, n2, n3, n4, n5, n6)
        >>> define(
        ...     # The first three-clique.
        ...     Edge.new(src=n1, dst=n2), Edge.new(src=n1, dst=n3), Edge.new(src=n2, dst=n3),
        ...     # The second three-clique.
        ...     Edge.new(src=n4, dst=n5), Edge.new(src=n4, dst=n6), Edge.new(src=n5, dst=n6),
        ...     # The connection between the three-cliques.
        ...     Edge.new(src=n1, dst=n4)
        ... )
        >>>
        >>> # 3. Compute community assignments and inspect
        >>> node, label = Node.ref("node"), Integer.ref("label")
        >>> label_propagation = graph.label_propagation()
        >>> select(node.id, label).where(label_propagation(node, label)).inspect()
        # The output will show each node mapped to a community:
        # (1, 1)
        # (2, 1)
        # (3, 1)
        # (4, 2)
        # (5, 2)
        # (6, 2)

        **Weighted Graph Example**

        Compute community assignments for each node in an undirected weighted
        graph. Here, a six-clique has the edges forming a dumbbell graph
        within the six-clique strongly weighted, and the remaining edges
        weakly weighted. The graph resolves into two communities, namely the
        two three-cliques constituent of the dumbbell embedded in the
        six-clique.

        >>> # 1. Set up a weighted, undirected graph
        >>> model = Model("test_model")
        >>> graph = Graph(model, directed=False, weighted=True)
        >>> Node, Edge = graph.Node, graph.Edge
        >>>
        >>> # 2. Define nodes and edges
        >>> n1, n2, n3, n4, n5, n6 = [Node.new(id=i) for i in range(1, 7)]
        >>> define(n1, n2, n3, n4, n5, n6)
        >>> define(
        ...     # First embedded three-clique.
        ...     Edge.new(src=n1, dst=n2, weight=1.0),
        ...     Edge.new(src=n1, dst=n3, weight=1.0),
        ...     Edge.new(src=n2, dst=n3, weight=1.0),
        ...     # Second embedded three-clique.
        ...     Edge.new(src=n4, dst=n5, weight=1.0),
        ...     Edge.new(src=n4, dst=n6, weight=1.0),
        ...     Edge.new(src=n5, dst=n6, weight=1.0),
        ...     # Slightly weaker connection between the embedded three-cliques.
        ...     Edge.new(src=n1, dst=n4, weight=0.5),
        ...     # Weaker edges connecting the six-clique in full.
        ...     Edge.new(src=n1, dst=n5, weight=0.1), Edge.new(src=n1, dst=n6, weight=0.1),
        ...     Edge.new(src=n2, dst=n4, weight=0.1), Edge.new(src=n2, dst=n5, weight=0.1),
        ...     Edge.new(src=n2, dst=n6, weight=0.1), Edge.new(src=n3, dst=n4, weight=0.1),
        ...     Edge.new(src=n3, dst=n5, weight=0.1), Edge.new(src=n3, dst=n6, weight=0.1)
        ... )
        >>>
        >>> # 3. Compute community assignments and inspect
        >>> node, label = Node.ref("node"), Integer.ref("label")
        >>> label_propagation = graph.label_propagation()
        >>> select(node.id, label).where(label_propagation(node, label)).inspect()
        # The output will show the two-community dumbbell structure:
        # (1, 1)
        # (2, 1)
        # (3, 1)
        # (4, 2)
        # (5, 2)
        # (6, 2)

        """
        _assert_type("label_propagation:max_sweeps", max_sweeps, int)
        _assert_inclusive_lower_bound("label_propagation:max_sweeps", max_sweeps, 0)

        _assert_type("label_propagation:randomization_seed", randomization_seed, int)
        _assert_exclusive_lower_bound("label_propagation:randomization_seed", randomization_seed, 0)

        # Collect parameters to rel_primitive_async_label_propagation,
        # appropriately typed and ordered for the primitive.
        label_propagation_parameters = [
            int(max_sweeps),
            int(randomization_seed),
        ]

        # Invoke the helper method that handles normalization,
        # primitive invocation, and result transformation.
        _label_propagation_assignments_rel, _label_propagation_diagnostic_rel = \
            self._create_primitive_algorithm_relationship("label_propagation", label_propagation_parameters)

        # Add tracking annotation.
        _label_propagation_assignments_rel.annotate(annotations.track("graphs", "label_propagation"))

        # Return based on whether diagnostic information was requested.
        if diagnostic_info:
            return _label_propagation_assignments_rel, _label_propagation_diagnostic_rel
        else:
            return _label_propagation_assignments_rel
