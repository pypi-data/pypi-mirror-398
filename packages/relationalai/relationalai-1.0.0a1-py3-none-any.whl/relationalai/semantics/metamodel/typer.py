from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Union, Iterable, TypeVar, Tuple

from ...util import tracing
from ...util.error import err, exc, Source, Part
from ...util.naming import sanitize
from ...util.structures import OrderedSet

from . import metamodel as mm, builtins as bt
from .rewriter import Walker, Rewriter, NO_WALK
from .builtins import builtins as b

#--------------------------------------------------
# Typer
#--------------------------------------------------

T = TypeVar("T", bound=mm.Model | mm.Task)

class Typer:
    def __init__(self, enforce=False):
        self.enforce = enforce
        self.model_net: Optional[PropagationNetwork] = None
        # TODO: remove this once we are using spans for the debugger
        self.last_net: Optional[PropagationNetwork] = None

    def infer_model(self, model: mm.Model) -> mm.Model:
        """
        Infer types for the given model, returning a new model with updated types and
        storing the results within this typer so that subsequent calls can reuse them.
        """
        # create a brand new network with data from this model
        self.model_net = PropagationNetwork(model)
        return self._infer(model, self.model_net)

    def infer_query(self, query: mm.Task) -> mm.Task:
        """
        Infer types for the given query, returning a new query with updated types. If the
        typer was used to infer a model previously, the information from that model analysis
        will be reused.
        """
        if self.model_net is not None:
            net = PropagationNetwork(self.model_net.model)
            net.load_types(self.model_net.resolved_types)
        else:
            net = PropagationNetwork(mm.Model(root=query))
        self.last_net = net
        return self._infer(query, net)

    #--------------------------------------------------
    # Internal implementation
    #--------------------------------------------------

    def _infer(self, node: T, net: PropagationNetwork) -> T:
        # build the propagation network by analyzing the model
        with tracing.span("typer.analyze"):
            Analyzer(net).analyze(node)

        # propagate the types through the network
        with tracing.span("typer.propagate") as span:
            net.propagate()
            # span["type_graph"] = net.to_mermaid()

        # replace the fields in the model with the new types
        with tracing.span("typer.replace"):
            replacer = Replacer(net)
            final = replacer.rewrite(node)

        # report any errors found during typing
        if net.errors:
            for error in net.errors:
                error.report()
            if self.enforce:
                exc("TyperError", "Type errors detected during type inference.")
        return final


#--------------------------------------------------
# Propagation Network
#--------------------------------------------------

# The core idea of the typer is to build a propagation network where nodes
# are vars, fields, or overloaded lookups/updates/aggregates. The intuition
# is that _all_ types in the IR ultimately flow from relation fields, so if
# we figure those out we just need to propagate their types to unknown vars, which
# may then flow into other fields and so on.

# This means the network only needs to contain nodes that either directly flow into
# an abstract node or are themselves abstract. We need to track overloads because
# their arguments effectively act like abstract vars until we've resolved the final types.

Node = Union[mm.Var, mm.Field, mm.Literal, mm.Lookup, mm.Update, mm.Aggregate]

class PropagationNetwork():
    def __init__(self, model: mm.Model):
        # the model that is either being analyzed or that is the context for a query
        self.model = model

        # the resolved types of nodes in the network
        self.resolved_types: dict[Node, mm.Type] = {}

        # map from unresolved placeholder relations to their potential target replacements
        self.potential_targets: dict[mm.Relation, list[mm.Relation]] = {}

        # track the set of nodes that represent entry points into the network
        self.roots = OrderedSet()
        # we separately want to track nodes that were loaded from a previous run
        # so that even if we have edges to them, we _still_ consider them roots
        # and properly propagate types from them at the beginning
        self.loaded_roots = set()

        # edges in the propagation network, from one node to potentially many
        self.edges:dict[Node, OrderedSet[Node]] = defaultdict(lambda: OrderedSet())
        self.back_edges:dict[Node, OrderedSet[Node]] = defaultdict(lambda: OrderedSet())
        # all nodes that are the target of an edge (to find roots)
        self.has_incoming = set()

        # type requirements: for a var with abstract declared type, the set of fields that
        # it must match the type of because it flows into them
        self.type_requirements:dict[mm.Var, OrderedSet[mm.Field]] = defaultdict(lambda: OrderedSet())

        # all errors collected during inference
        self.errors:list[TyperError] = []

        # overloads resolved for a lookup/update/aggregate, by node id. This is only for
        # relations that declare overloads
        self.resolved_overload:dict[int, mm.Overload] = {}
        # placeholders resolved for a lookup, by node id. This is only for relations that
        # are placeholders (i.e. only Any fields) and will be replaced by references to
        # these concrete relations. E.g. a query for "name(Any, Any)" may be replaced by
        # the union of "name(Dog, String)" and name(Cat, String)".
        self.resolved_placeholder:dict[int, list[mm.Relation]] = {}
        # for a given lookup/update/aggregate that involves numbers, the specific number
        # type resolved for it.
        self.resolved_number:dict[int, mm.NumberType] = {}
        # keep track of nodes already resolved to avoid re-resolving
        self.resolved_nodes:set[int] = set()

    #--------------------------------------------------
    # Error reporting
    #--------------------------------------------------

    def type_mismatch(self, node: Node, expected: mm.Type, actual: mm.Type):
        self.errors.append(TypeMismatch(node, expected, actual))

    def invalid_type(self, node: Node, type: mm.Type):
        self.errors.append(InvalidType(node, type))

    def unresolved_overload(self, node: mm.Lookup|mm.Aggregate):
        # TODO - consider renaming this to UnresolvedReference
        self.errors.append(UnresolvedOverload(node, [self.resolve(a) for a in node.args]))

    def unresolved_type(self, node: Node):
        self.errors.append(UnresolvedType(node))

    def has_errors(self, node: Node) -> bool:
        for mismatch in self.errors:
            if mismatch.node == node:
                return True
        return False

    #--------------------------------------------------
    # Types and Edges
    #--------------------------------------------------

    def add_edge(self, source: Node, target: Node):
        # manage roots
        if target in self.roots and target not in self.loaded_roots:
            self.roots.remove(target)
        if source not in self.has_incoming:
            self.roots.add(source)
        # register edge
        self.edges[source].add(target)
        self.back_edges[target].add(source)
        self.has_incoming.add(target)

    def add_resolved_type(self, node: Node, type: mm.Type):
        """ Register that this node was resolved to have this type. """
        if node in self.resolved_types:
            self.resolved_types[node] = merge_types(self.resolved_types[node], type)
        else:
            self.resolved_types[node] = type

    def add_type_requirement(self, source: mm.Var, field: mm.Field):
        """ Register that this var, which has an abstract declared type, must match the type
        of this field as it flows into it.. """
        self.type_requirements[source].add(field)

    #--------------------------------------------------
    # Load previous types
    #--------------------------------------------------

    def load_types(self, type_dict: dict[Node, mm.Type]):
        for node, type in type_dict.items():
            if isinstance(node, (mm.Field)):
                self.add_resolved_type(node, type)
                self.loaded_roots.add(node)
                self.roots.add(node)

    #--------------------------------------------------
    # Resolve Values
    #--------------------------------------------------

    def resolve(self, value: Node|mm.Value) -> mm.Type:
        if isinstance(value, (mm.Var, mm.Field, mm.Literal)):
            return self.resolved_types.get(value) or to_type(value)
        assert not isinstance(value, (mm.Lookup, mm.Update, mm.Aggregate)), "Should never try to resolve a task"
        return to_type(value)

    #--------------------------------------------------
    # Resolve References
    #--------------------------------------------------

    def resolve_reference(self, op: mm.Lookup|mm.Aggregate) -> Optional[mm.Overload|list[mm.Relation]]:
        # check if all dependencies required to resolve this reference are met
        if not self.all_dependencies_resolved(op):
            return None

        relation = get_relation(op)
        if bt.is_placeholder(relation):
            # when replacing a placeholder, we may have multiple matches
            matches = []
            resolved_args = [self.resolve(arg) for arg in op.args]
            for target in self.potential_targets.get(relation, []):
                fields = get_relation_fields(target, relation.name)
                if all(type_matches(arg, self.resolve(field))
                        for arg, field in zip(resolved_args, fields)):
                    matches.append(target)

            return matches

        elif relation.overloads:
            # when resolving an overload for a concrete relation, we can only have one
            resolved_args = [self.resolve(arg) for arg in op.args]
            is_function = bt.is_function(relation)
            for overload in relation.overloads:
                # note that for functions we only consider input fields when matching
                if all(type_matches(arg, field_type) or conversion_allowed(arg, field_type)
                       for arg, field, field_type in zip(resolved_args, relation.fields, overload.types)
                       if field.input or not is_function):
                    self.resolved_overload[op.id] = overload
                    return overload
            return []  # no matches found
        else:
            # this is a relation with type vars or numbers that needs to be specialized
            return [relation]


    def all_dependencies_resolved(self, op:mm.Lookup|mm.Aggregate):
        # if this is a placeholder, we need assume all possible args were resolved
        if bt.is_placeholder(get_relation(op)):
            return True
        # else, find whether all back-edges were resolved
        for node in self.back_edges[op]:
            if isinstance(node, (mm.Var, mm.Field, mm.Literal)):
                node_type = self.resolve(node)
                if bt.is_abstract(node_type):
                    return False
        return True


    #--------------------------------------------------
    # Propagation
    #--------------------------------------------------

    def propagate(self):
        edges = self.edges
        work_list = []

        # go through all the roots and find any that are not abstract, they'll be the first
        # nodes to push types through the network
        unhandled_roots = OrderedSet()
        for node in self.roots:
            if not isinstance(node, (mm.Var, mm.Field, mm.Literal)):
                continue
            node_type = self.resolve(node)
            if not bt.is_abstract(node_type):
                work_list.append(node)
            else:
                unhandled_roots.add(node)

        # push known type nodes through the edges
        while work_list:
            source = work_list.pop(0)
            self.resolved_nodes.add(source.id)
            if source in unhandled_roots:
                unhandled_roots.remove(source)
            source_type = self.resolve(source)
            # check to see if the source has ended up with a set of types that
            # aren't valid, e.g. a union of primitives
            if invalid_type(source_type):
                self.invalid_type(source, source_type)

            # propagate our type to each outgoing edge
            for out in edges.get(source, []):
                # if this is an overload then we need to try and resolve it
                if isinstance(out, (mm.Lookup, mm.Aggregate)):
                    if not out.id in self.resolved_nodes:
                        found = self.resolve_reference(out)
                        if found is not None:
                            self.resolved_nodes.add(out.id)
                            self.propagate_reference(out, found)
                            for arg in out.args:
                                if arg not in work_list:
                                    work_list.append(arg)
                # otherwise, we just add to the outgoing node's type and if it
                # changes we add it to the work list
                elif start := self.resolve(out):
                    self.add_resolved_type(out, source_type)
                    if out not in work_list and (start != self.resolve(out) or not out.id in self.resolved_nodes):
                        work_list.append(out)

        for source in unhandled_roots:
            self.unresolved_type(source)

        # now that we've pushed all the types through the network, we need to validate
        # that all type requirements of those nodes are met
        for node, fields in self.type_requirements.items():
            node_type = self.resolve(node)
            for field in fields:
                field_type = self.resolve(field)
                if not type_matches(node_type, field_type) and not conversion_allowed(node_type, field_type):
                    self.type_mismatch(node, field_type, node_type)


    def propagate_reference(self, task:mm.Lookup|mm.Aggregate, references:mm.Overload|list[mm.Relation]):
        # TODO: distinguish between overloads and placeholders better when raising errors
        if not references:
            return self.unresolved_overload(task)

        resolved_args = [self.resolve(arg) for arg in task.args]

        # we need to determine the final types of our args by taking all the references
        # and adding the type of their fields back to the args.
        relation = get_relation(task)

        if bt.is_placeholder(relation):
            assert(references and isinstance(references, list))
            # we've resolved the placeholder, so store that
            self.resolved_placeholder[task.id] = references

            # we need to determine the final types of our args by taking all the references
            # and adding the type of their fields back to the args.
            for reference in references:
                resolved_fields = [self.resolve(f) for f in get_relation_fields(reference, relation.name)]
                for field_type, arg_type, arg in zip(resolved_fields, resolved_args, task.args):
                    if bt.is_abstract(arg_type) and isinstance(arg, mm.Var):
                        self.add_resolved_type(arg, field_type)
        else:
            if isinstance(references, mm.Overload):
                # we resolved an overload, use its types
                types = list(references.types)
            else:
                # we resolved to a single concrete relation that contains type vars or needs
                # number specialization, so use that relation's field types
                types = list([self.resolve(f) for f in relation.fields])

            # if our overload preserves types, we check to see if there's a preserved
            # output type given the inputs and if so, shadow the field's type with the
            # preserved type
            resolved_fields = types
            if bt.is_function(relation) and len(set(resolved_fields)) == 1:
                input_types = set([arg_type for field, arg_type
                                    in zip(relation.fields, resolved_args) if field.input])
                if out_type := self.try_preserve_type(input_types):
                    resolved_fields = [field_type if field.input else out_type
                                        for field, field_type in zip(relation.fields, types)]

            # TODO - we also need to make sure the type vars are constently resolved here
            # i.e. if types contain typevars, check that the args that are bound to those
            # typevars are consistent
            if b.core.Number in types or (b.core.TypeVar in types and any(bt.is_number(t) for t in resolved_args)):
                # this overload contains generic numbers or typevars bound to numbers, so
                # find which specific type of number to use given the arguments being passed
                number, resolved_fields = self.specialize_number(relation, resolved_fields, resolved_args)
                self.resolved_number[task.id] = number
                # push the specialized number to the outputs
                for field, field_type, arg in zip(relation.fields, resolved_fields, task.args):
                    if not field.input and isinstance(arg, mm.Var):
                        self.add_resolved_type(arg, field_type)
            else:
                for field_type, arg, arg_type in zip(resolved_fields, task.args, resolved_args):
                    if bt.is_abstract(arg_type) and isinstance(arg, mm.Var):
                        self.add_resolved_type(arg, field_type)


    def try_preserve_type(self, types:set[mm.Type]) -> Optional[mm.Type]:
        # we keep the input type as the output type if either all inputs
        # are the exact same type or there's one nominal and its base primitive
        # type, e.g. USD + Decimal
        if len(types) == 1:
            return next(iter(types))
        if len(types) == 2:
            t1, t2 = types
            t1_base = bt.get_primitive_supertype(t1)
            t2_base = bt.get_primitive_supertype(t2)
            if t1_base is None or t2_base is None:
                base_equivalent = type_matches(t1, t2, accept_expected_super_types=True)
            else:
                base_equivalent = type_matches(t1_base, t2_base)
            if base_equivalent:
                # as long as one of the types is a base primitive, we can use the
                # other type as final preserved type
                if bt.is_primitive(t1):
                    return t2
                elif bt.is_primitive(t2):
                    return t1
        return None

    def specialize_number(self, op, field_types:list[mm.Type], arg_types:list[mm.Type]) -> Tuple[mm.NumberType, list[mm.Type]]:
        """
        Find the number type to use for an overload that has Number in its field_types,
        and which is being referred to with these arg_types.

        Return a tuple where the first element is the specialized number type, and the second
        element is a new list that contains the same types as field_types but with
        Number replaced by this specialized number.
        """
        if op == b.core.div:
            # see https://docs.snowflake.com/en/sql-reference/operators-arithmetic#division
            numerator, denominator = get_number_type(arg_types[0]), get_number_type(arg_types[1])
            s = max(numerator.scale, min(numerator.scale + 6, 12))
            number = mm.NumberType(name=f"Number(38,{s})", precision=38, scale=s, source=op.source, super_types=(b.core.Numeric,))
            return number, [numerator, denominator, number]
        elif op == b.core.mul:
            # see https://docs.snowflake.com/en/sql-reference/operators-arithmetic#multiplication
            t1, t2 = get_number_type(arg_types[0]), get_number_type(arg_types[1])
            S1 = t1.scale
            S2 = t2.scale
            s = min(S1 + S2, max(S1, S2, 12))
            number = mm.NumberType(name=f"Number(38,{s})", precision=38, scale=s, source=op.source, super_types=(b.core.Numeric,))
            return number, [t1, t2, number]
        elif op == b.aggregates.avg:
            # TODO!! - implement proper avg specialization
            pass

        number = None
        for arg_type in arg_types:
            x = bt.get_number_supertype(arg_type)
            if isinstance(x, mm.NumberType):
                # the current specialization policy is to select the number with largest
                # scale and, if there multiple with the largest scale, the one with the
                # largest precision. This is safe because when converting a number to the
                # specialized number, we never truncate fractional digits (because we
                # selected the largest scale) and, if the non-fractional digits are too
                # large to fit the specialized number, we will have a runtime overflow,
                # which should alert the user of the problem.
                #
                # In the future we can implement more complex policies. For example,
                # snowflake has well documented behavior for how the output of operations
                # behave in face of different number types, and we may use that:
                # https://docs.snowflake.com/en/sql-reference/operators-arithmetic#scale-and-precision-in-arithmetic-operations
                if number is None or x.scale > number.scale or (x.scale == number.scale and x.precision > number.precision):
                    number = x
        if number is None:
            number = b.core.DefaultNumber
        # assert(isinstance(number, mm.NumberType))
        return number, [number if bt.is_number(field_type) else field_type
                for field_type in field_types]


    #--------------------------------------------------
    # Display
    #--------------------------------------------------

    # draw the network as a mermaid graph for the debugger
    def to_mermaid(self, max_edges=500) -> str:

        # add links for edges while collecting nodes
        nodes = OrderedSet()
        link_strs = []
        # edges
        for src, dsts in self.edges.items():
            nodes.add(src)
            for dst in dsts:
                if len(link_strs) > max_edges:
                    break
                nodes.add(dst)
                link_strs.append(f"n{src.id} --> n{dst.id}")
            if len(link_strs) > max_edges:
                break
        # type requirements
        for src, dsts in self.type_requirements.items():
            nodes.add(src)
            for dst in dsts:
                if len(link_strs) > max_edges:
                    break
                nodes.add(dst)
                link_strs.append(f"n{src.id} -.-> n{dst.id}")
            if len(link_strs) > max_edges:
                break

        def type_span(t:mm.Type) -> str:
            type_str = t.name if isinstance(t, mm.ScalarType) else str(t)
            return f"<span style='color:cyan;'>{type_str.strip()}</span>"

        def reference_span(rel:mm.Relation, arg_types:list[mm.Type], root:str) -> str:
            args = []
            for field, arg_type in zip(rel.fields, arg_types):
                field_type = self.resolve(field)
                if not type_matches(arg_type, field_type) and not conversion_allowed(arg_type, field_type) and not bt.is_abstract(field_type):
                    args.append(f"<span style='color:yellow;'>{str(arg_type).strip()} -> {str(field_type).strip()}</span>")
                elif isinstance(arg_type, mm.UnionType):
                    args.append(type_span(field_type))
                else:
                    args.append(type_span(arg_type))
            return f'{rel.name}{root}({", ".join(args)})'

        resolved = self.resolved_types
        node_strs = []
        for node in nodes:
            klass = ""
            root = "(*)" if node in self.roots else ""
            if isinstance(node, mm.Var):
                ir_type = resolved.get(node) or self.resolve(node)
                type_str = type_span(ir_type)
                label = f'(["{node.name}{root}:{type_str}"])'
            elif isinstance(node, mm.Literal):
                ir_type = resolved.get(node) or self.resolve(node)
                type_str = type_span(ir_type)
                klass = ":::literal"
                label = f'[/"{node.value}{root}: {type_str}"\\]'
            elif isinstance(node, mm.Field):
                ir_type = resolved.get(node) or self.resolve(node)
                type_str = type_span(ir_type)
                klass = ":::field"
                rel = node._relation
                if rel is not None:
                    rel = str(node._relation)
                    label = f'{{{{"{node.name}{root}:{type_str}\nfrom {rel}"}}}}'
                else:
                    label = f'{{{{"{node.name}{root}:\n{type_str}"}}}}'
            elif isinstance(node, (mm.Lookup, mm.Update, mm.Aggregate)):
                arg_types = [self.resolve(arg) for arg in node.args]
                if node.id in self.resolved_placeholder:
                    overloads = self.resolved_placeholder[node.id]
                    content = "<br/>".join([reference_span(o, arg_types, root) for o in overloads])
                else:
                    content = reference_span(get_relation(node), arg_types, root)
                label = f'[/"{content}"/]'
            # elif isinstance(node, mm.Relation):
            #     label = f'[("{node}")]'
            else:
                raise NotImplementedError(f"Unknown node type: {type(node)}")
            if self.has_errors(node):
                klass = ":::error"
            node_strs.append(f'n{node.id}{label}{klass}')

        node_str = "\n                ".join(node_strs)
        link_str = "\n                ".join(link_strs)
        template = f"""
            %%{{init: {{'theme':'dark', 'flowchart':{{'useMaxWidth':false, 'htmlLabels': true}}}}}}%%
            flowchart TD
                linkStyle default stroke:#666
                classDef field fill:#245,stroke:#478
                classDef literal fill:#452,stroke:#784
                classDef error fill:#624,stroke:#945,color:#f9a
                classDef default stroke:#444,stroke-width:2px, font-size:12px

                %% nodes
                {node_str}

                %% edges
                {link_str}
        """
        return template

#--------------------------------------------------
# Analyzer
#--------------------------------------------------

class Analyzer(Walker):
    """ Walks the metamodel and builds the propagation network. """

    def __init__(self, net:PropagationNetwork):
        super().__init__()
        self.net = net

    def analyze(self, node: mm.Node):
        self(node)

    # TODO - ignoring requires for now because the typing of constraints seems incorrect
    def enter_require(self, require: mm.Require):
        return NO_WALK

    def compute_potential_targets(self, relation: mm.Relation):
        # register potential targets for placeholders
        if bt.is_placeholder(relation):
            self.net.potential_targets[relation] = get_potential_targets(self.net.model, relation)

    #--------------------------------------------------
    # Walk Update
    #--------------------------------------------------

    def update(self, node: mm.Update):
        rel = node.relation
        self.compute_potential_targets(rel)

        # if this is a type relation, the update is asserting that the argument is of that
        # type; so, it's fine to pass a super-type in to the population e.g. Employee(Person)
        # should be a valid way to populate that a particular Person is also an Employee.
        is_type_relation = isinstance(rel, mm.TypeNode)
        for arg, field in zip(node.args, rel.fields):
            field_type = field.type
            arg_type = self.net.resolve(arg)

            # if the arg is abstract, but the field isn't, then we need to make sure that
            # once the arg is resolved we check that it matches the field type
            if isinstance(arg, mm.Var) and bt.is_abstract(arg_type) and bt.is_concrete(field_type):
                self.net.add_type_requirement(arg, field)

            if bt.is_abstract(field_type) and isinstance(arg, (mm.Var, mm.Literal)):
                # if the field is abstract, then eventually this arg will help determine
                # the field's type, so add an edge from the arg to the field
                self.net.add_edge(arg, field)
            elif not type_matches(arg_type, field_type, accept_expected_super_types=is_type_relation):
                if not conversion_allowed(arg_type, field_type):
                    self.net.type_mismatch(node, field_type, arg_type)

    #--------------------------------------------------
    # Walk Lookups + Aggregates
    #--------------------------------------------------

    def lookup(self, node: mm.Lookup):
        self.compute_potential_targets(node.relation)
        self.visit_rel_op(node)

    def aggregate(self, node: mm.Aggregate):
        self.visit_rel_op(node)

    def visit_rel_op(self, node: mm.Lookup|mm.Aggregate):
        rel = get_relation(node)

        # special case eq lookups
        if isinstance(node, mm.Lookup) and rel == b.core.eq:
            # if both args for an eq are abstract, link them, otherwise do normal processing
            (left, right) = node.args
            left_type = self.net.resolve(left)
            right_type = self.net.resolve(right)
            if bt.is_abstract(left_type) and bt.is_abstract(right_type):
                assert isinstance(left, mm.Var) and isinstance(right, mm.Var)
                # if both sides are abstract, then whatever we find out about
                # either should propagate to the other
                self.net.add_edge(left, right)
                self.net.add_edge(right, left)
                return

        # special case when the relation needs to be resolved as there are overloads, placeholders,
        # type vars or it needs number specialization
        if self.requires_resolution(rel):
            return self.visit_unresolved_reference(node)

        # if this is a population check, then it's fine to pass a subtype in to do the check
        # e.g. Employee(Person) is a valid way to check if a person is an employee
        is_population_lookup = isinstance(rel, mm.TypeNode)
        for arg, field in zip(node.args, rel.fields):
            field_type = self.net.resolve(field)
            arg_type = self.net.resolve(arg)
            if not type_matches(arg_type, field_type, is_population_lookup):
                # Do not complain if we can convert the arg to the field type.
                if not conversion_allowed(arg_type, field_type):
                    # if the arg is a var and it matches when allowing for super types of
                    # the expected we can expect to refine it later; but we add a type
                    # requirement to check at the end
                    if isinstance(arg, mm.Var) and type_matches(arg_type, field_type, True):
                        self.net.add_type_requirement(arg, field)
                    else:
                        self.net.type_mismatch(node, field_type, arg_type)
            # if we have an abstract var then this field will ultimately propagate to that
            # var's type; also, if this is a population lookup, the type of the population
            # being looked up will flow back to the var
            if isinstance(arg, mm.Var):
                if not field.input:
                    self.net.add_edge(field, arg)
                else:
                    self.net.add_type_requirement(arg, field)


    def requires_resolution(self, rel: mm.Relation) -> bool:
        # has overloads or is a placeholder relation that needs replacement
        if rel.overloads or bt.is_placeholder(rel):
            return True
        # there are type vars or numbers in the fields that need specialization
        for field in rel.fields:
            t = self.net.resolve(field)
            if bt.is_type_var(t) or t == b.core.Number:
                return True
        return False


    def visit_unresolved_reference(self, node: mm.Lookup|mm.Aggregate):
        relation = get_relation(node)
        # functions have their outputs determined by their inputs
        is_function = bt.is_function(relation)
        is_placeholder = bt.is_placeholder(relation)
        # add edges between args and the relation based on input/output
        for field, arg in zip(relation.fields, node.args):
            if isinstance(arg, (mm.Var, mm.Literal)):
                if field.input:
                    # the arg type will flow into the input
                    self.net.add_edge(arg, node)
                else:
                    if is_function:
                        # this is an output of a function, so the field type will flow to the arg
                        self.net.add_edge(node, arg)
                    else:
                        if is_placeholder:
                            self.net.add_edge(arg, node)
                        if bt.is_abstract(field.type) and not is_placeholder:
                            self.net.add_edge(field, node)

                        if bt.is_abstract(self.net.resolve(arg)):
                            self.net.add_edge(node, arg)


#--------------------------------------------------
# Replacer
#--------------------------------------------------

# Once we've pushed all the types through the network, we need to replace the types of
# fields and vars that we may have discovered. We also need to replace placeholder lookups
# with the chosen relations and do any conversions that are needed.
class Replacer(Rewriter):
    def __init__(self, net:PropagationNetwork):
        super().__init__()
        self.net = net

    def rewrite(self, model: T) -> T:
        return self(model) # type: ignore

    def logical(self, logical: mm.Logical):
        if len(logical.body) == 0:
            return logical
        # inline logicals that are just there to group other nodes during rewrite
        body = []
        for child in logical.body:
            if isinstance(child, mm.Logical) and not child.optional and not child.scope:
                body.extend(child.body)
            else:
                body.append(child)
        return logical.mut(body = tuple(body))

    #--------------------------------------------------
    # Rewriter handlers
    #--------------------------------------------------

    def field(self, node: mm.Field):
        # TODO - this is only modifying the relation in the model, but then we have a new
        # relation there, which is different than the object referenced by tasks.
        if node in self.net.resolved_types:
            return mm.Field(node.name, self.net.resolved_types[node], node.input)
        return node

    def var(self, node: mm.Var):
        if node in self.net.resolved_types:
            return mm.Var(self.net.resolved_types[node], node.name)
        return node

    def literal(self, node: mm.Literal):
        if node in self.net.resolved_types:
            return mm.Literal(self.net.resolved_types[node], node.value)
        return node

    def update(self, node: mm.Update):
        return self.convert_arguments(node, node.relation)

    def lookup(self, node: mm.Lookup):
        # We need to handle eq specially because its arguments can be converted symmetrically
        if node.relation == b.core.eq:
            return self.visit_eq_lookup(node)

        args = types = None
        if node.id in self.net.resolved_placeholder:
            resolved_relations = self.net.resolved_placeholder[node.id]
            args = get_lookup_args(node, resolved_relations[0])
            types = [f.type for f in resolved_relations[0].fields]
        elif node.id in self.net.resolved_overload:
            resolved_relations = [node.relation]
            types = self.net.resolved_overload[node.id].types
        else:
            resolved_relations = [node.relation]

        if len(resolved_relations) == 1:
            x = self.convert_arguments(node, resolved_relations[0], args, types)
            if isinstance(x, mm.Logical) and len(x.body) == 1:
                return x.body[0]
            else:
                return x

        branches:list = []
        for target in resolved_relations:
            args = get_lookup_args(node, target)
            types = [f.type for f in get_relation_fields(resolved_relations[0], node.relation.name)]
            # adding this logical to avoid issues in the old backend
            branches.append(mm.Logical((self.convert_arguments(node, target, args, types=types),)))
        return mm.Union(tuple(branches))

    def convert_arguments(self, node: mm.Lookup|mm.Update, relation: mm.Relation, args: Iterable[mm.Value]|None=None, types: Iterable[mm.Type]|None=None) -> mm.Logical|mm.Lookup|mm.Update:
        args = args or node.args
        types = types or [self.net.resolve(f) for f in relation.fields]
        number_type = self.net.resolved_number.get(node.id)
        is_function = bt.is_function(relation)
        tasks = []
        final_args = []
        for arg, field, field_type in zip(args, relation.fields, types):
            if isinstance(arg, (mm.Var, mm.Literal)) and (not is_function or field.input):
                arg_type = to_type(arg)
                if number_type and bt.is_number(arg_type) and not arg_type == b.core.ScaledNumber:
                    field_type = number_type
                # the typer previously made sure that this should be valid so a type mismatch
                # means we need to convert
                if not type_matches(arg_type, field_type):
                    final_args.append(convert(arg, field_type, tasks))
                else:
                    final_args.append(arg)
            else:
                final_args.append(arg)
        if isinstance(node, mm.Lookup):
            tasks.append(node.mut(relation = relation, args = tuple(final_args)))
        else:
            tasks.append(node.mut(relation = relation, args = tuple(final_args)))
        if len(tasks) == 1:
            return tasks[0]
        return mm.Logical(tuple(tasks))


    def visit_eq_lookup(self, node: mm.Lookup):
        (left, right) = node.args
        left_type = to_type(left)
        right_type = to_type(right)

        if type_matches(left_type, right_type):
            return node

        assert isinstance(left, (mm.Var, mm.Literal)) and isinstance(right, (mm.Var, mm.Literal))
        final_args = []
        tasks = []
        if conversion_allowed(left_type, right_type):
            final_args = [convert(left, right_type, tasks), right]
        elif conversion_allowed(right_type, left_type):
            final_args = [left, convert(right, left_type, tasks)]
        else:
            self.net.type_mismatch(node, left_type, right_type)
            return node

        tasks.append(mm.Lookup(b.core.eq, tuple(final_args)))
        return mm.Logical(tuple(tasks))

#--------------------------------------------------
# Helpers
#--------------------------------------------------

def get_relation(node: mm.Lookup|mm.Update|mm.Aggregate) -> mm.Relation:
    if isinstance(node, mm.Aggregate):
        return node.aggregation
    return node.relation

def get_name(type: mm.Type) -> str:
    if isinstance(type, mm.ScalarType):
        return type.name
    elif isinstance(type, mm.UnionType):
        return '|'.join([get_name(t) for t in type.types])
    elif isinstance(type, mm.ListType):
        return f'List[{get_name(type.element_type)}]'
    elif isinstance(type, mm.TupleType):
        return f'Tuple[{", ".join([get_name(t) for t in type.element_types])}]'
    else:
        raise TypeError(f"Unknown type: {type}")

#--------------------------------------------------
# Type and Relation helpers
#--------------------------------------------------

def get_relation_fields(relation: mm.Relation, name: str) -> Iterable[mm.Field]:
    """ Get the fields of this relation, potentially reordered to match the reading with the given name."""
    if name == relation.name:
        return relation.fields
    for reading in relation.readings:
        if reading.name == name:
            # reorder the fields to match the correct ordering
            fields = []
            for idx in reading.field_order:
                fields.append(relation.fields[idx])
            return fields
    return []

def get_lookup_args(node: mm.Lookup, target: mm.Relation):
    """ Get the args of this lookup, potentially reordered to match the reading with the given name."""
    for reading in target.readings:
        if reading.name == node.relation.name:
            # reorder the args to match the correct ordering
            args = []
            for idx in reading.field_order:
                args.append(node.args[idx])
            return args
    return node.args

def get_number_type(t: mm.Type) -> mm.NumberType:
    # Get a number type from the given type, if it is Number return the default number
    x = bt.get_number_supertype(t)
    if isinstance(x, mm.NumberType):
        return x
    return b.core.DefaultNumber

def is_potential_target(placeholder: mm.Relation, target: mm.Relation) -> bool:
    """ Whether this target is matches the placeholder signature and, thus, can be a potential target. """
    if placeholder != target and len(placeholder.fields) == len(target.fields) and not bt.is_placeholder(target):
        return placeholder.name == target.name or any(placeholder.name == reading.name for reading in target.readings)
    return False

def get_potential_targets(model: mm.Model, placeholder: mm.Relation) -> list[mm.Relation]:
    """ Get all potential target relations in the model that match the placeholder signature. """
    return list(filter(lambda r: is_potential_target(placeholder, r), model.relations))

def to_type(value: mm.Value|mm.Field|mm.Literal) -> mm.Type:
    if isinstance(value, (mm.Var, mm.Field, mm.Literal)):
        return value.type

    if isinstance(value, mm.Type):
        return b.core.Type

    if isinstance(value, tuple):
        return mm.TupleType(element_types=tuple(to_type(v) for v in value))

    raise TypeError(f"Cannot determine IR type for value: {value} of type {type(value).__name__}")


def convert(value: mm.Var|mm.Literal, to_type: mm.Type, tasks: list[mm.Task]) -> mm.Value:
    # if the arg is a literal, we can just change its type
    # TODO - we may want to check that the value is actually convertible
    if isinstance(value, mm.Literal):
        return mm.Literal(to_type, value.value)

    # otherise we need to add a cast
    name = sanitize(value.name + "_" + get_name(to_type))
    to_type_base = bt.get_primitive_supertype(to_type) or to_type
    new_value = mm.Var(to_type_base, name)
    tasks.append(mm.Lookup(b.core.cast, (to_type_base, value, new_value)))
    return new_value


def conversion_allowed(from_type: mm.Type, to_type: mm.Type) -> bool:
    # value type conversion is allowed
    x = bt.get_primitive_supertype(from_type)
    y = bt.get_primitive_supertype(to_type)
    if x and y and (x != from_type or y != to_type) and conversion_allowed(x, y):
        return True

    # numbers can be converted to floats
    if bt.is_numeric(from_type) and to_type == b.core.Float:
        return True

    # a number can be converted to another number of larger scale
    if isinstance(from_type, mm.NumberType) and isinstance(to_type, mm.NumberType):
        if to_type.scale > from_type.scale:
            return True

    if from_type == b.core.Number and isinstance(to_type, mm.NumberType):
        return True

    return False

def type_matches(actual: mm.Type, expected: mm.Type, accept_expected_super_types=False) -> bool:
    """
    True iff we can use a value of the actual type when expecting the expected type, without
    conversions.

    Any super-type of `actual` can match `expected`. For example if we expect a `Person`, we
    can use an `Employee` if `Employee < Person`.

    In general, the other way around is not true: if we expect an `Employee` we cannot use a
    `Person` instead.

    However, when the relation is a Type (previsously known as "population relations"), it
    is valid to provide sub-types of the expected type. For example, `Employee(Person)` is
    a valid way to check that `Person` is an `Employee` on a `Lookup`, or to assert that a
    particular `Person` is an `Employee` on an `Update`.
    """
    # exact match
    if actual == expected:
        return True

    # any matches anything
    if actual == b.core.Any or expected == b.core.Any:
        return True

    # type vars match anything
    if expected == b.core.TypeVar:
        return True

    # TODO - remove this once we make them singletons per precision/scale
    if isinstance(actual, mm.NumberType) and isinstance(expected, mm.NumberType):
        if actual.precision == expected.precision and actual.scale == expected.scale:
            return True

    # if an entity type var or any entity is expected, it matches any actual entity type
    if (expected == b.core.EntityTypeVar or bt.extends(expected, b.core.AnyEntity)) and not bt.is_primitive(actual):
        return True

    # the abstract Number type and the number type variable match any number type
    if (expected == b.core.Number) and bt.is_number(actual):
        return True

    if (expected == b.core.Numeric) and bt.is_numeric(actual):
        return True

    # if actual is scalar, any of its parents may match the expected type
    if isinstance(actual, mm.ScalarType) and any([type_matches(parent, expected) for parent in actual.super_types]):
        return True

    # if expected is a value type or this is a check for a type relation, any of the expected type's parents may match the actual type
    if (accept_expected_super_types or bt.is_value_type(expected)) and isinstance(expected, mm.ScalarType) and any([type_matches(actual, parent, accept_expected_super_types) for parent in expected.super_types]):
        return True

    # if we expect a union, the actual can match any of its types
    if isinstance(expected, mm.UnionType):
        for t in expected.types:
            if type_matches(t, actual, accept_expected_super_types):
                return True

    # if actual is a union, every one of its types must match the expected type
    # if isinstance(actual, mm.UnionType):
    #     for t in actual.types:
    #         if not type_matches(t, expected, accept_expected_super_types):
    #             return False
    #     return True
    # TODO - we have to distinguish between when we are checking that a specific arg matches
    # a relation vs when we are selecting relations for the placeholders; then we have to
    # decide between the above and this.
    if isinstance(actual, mm.UnionType):
        for t in actual.types:
            if type_matches(t, expected, accept_expected_super_types):
                return True

    # a list type matches if their element types match
    if isinstance(actual, (mm.ListType, mm.TupleType)) and isinstance(expected, mm.ListType):
        if isinstance(actual, mm.TupleType):
            for et in actual.element_types:
                if not type_matches(et, expected.element_type):
                    return False
            return True
        return type_matches(actual.element_type, expected.element_type)

    # a tuple types match if any of all their types match
    if isinstance(actual, mm.TupleType) and isinstance(expected, mm.TupleType):
        return all([type_matches(ae, ee) for ae, ee in zip(actual.element_types, expected.element_types)])

    # accept tuples with a single element type to match a list with that type
    if isinstance(actual, mm.TupleType) and isinstance(expected, mm.ListType):
        if len(set(actual.element_types)) == 1:
            return type_matches(actual.element_types[0], expected.element_type)

    # otherwise no match
    return False


def merge_types(type1: mm.Type, type2: mm.Type) -> mm.Type:
    if type1 == type2:
        return type1
    types_to_process = [type1, type2]

    # if one of them is the abstract Number type, pick the other
    if type1 == b.core.Number and isinstance(type2, mm.NumberType):
        return type2
    if type2 == b.core.Number and isinstance(type1, mm.NumberType):
        return type1

    # if both are number types, pick the one with larger scale/precision
    if isinstance(type1, mm.NumberType) and isinstance(type2, mm.NumberType):
        if type1.scale > type2.scale or (type1.scale == type2.scale and type1.precision > type2.precision):
            return type1
        else:
            return type2

    # if we are overriding a number with a float, pick float
    if isinstance(type1, mm.NumberType) and type2 == b.core.Float:
        return type2

    # if one extends the other, pick the most specific one
    if bt.extends(type1, type2):
        return type1
    if bt.extends(type2, type1):
        return type2

    # give precedence to nominal types (e.g. merging USD(decimal) with decimal gives USD(decimal))
    base_primitive_type1 = bt.get_primitive_supertype(type1)
    base_primitive_type2 = bt.get_primitive_supertype(type2)
    if base_primitive_type1 == base_primitive_type2:
        if bt.is_primitive(type1):
            return type2
        elif bt.is_primitive(type2):
            return type1

    combined = OrderedSet()
    # Iterative flattening of union types
    while types_to_process:
        t = types_to_process.pop()
        if isinstance(t, mm.UnionType):
            types_to_process.extend(t.types)
        else:
            combined.add(t)

    # If we have multiple types and Any or AnyEntity is one of them, remove Any
    if len(combined) > 1:
        if b.core.Any in combined:
            combined.remove(b.core.Any)
        if b.core.AnyEntity in combined:
            combined.remove(b.core.AnyEntity)

    # If we still have multiple types, make sure supertypes are removed to keep only the
    # most specific types
    if len(combined) > 1:
        to_remove = set()
        for t1 in combined:
            for t2 in combined:
                if t1 != t2 and bt.extends(t1, t2):
                    to_remove.add(t2)
        for r in to_remove:
            combined.remove(r)

    # Return single type or create a union
    return next(iter(combined)) if len(combined) == 1 else mm.UnionType(types=tuple(combined))

def invalid_type(type:mm.Type) -> bool:
    if isinstance(type, mm.UnionType):
        # if there are multiple primitives, or a primitive and a non-primitive
        # then we have an invalid type
        if len(type.types) > 1:
            return any([bt.is_primitive(t) for t in type.types])
    return False


#--------------------------------------------------
# Type Errors
#--------------------------------------------------

@dataclass
class TyperError():
    node: mm.Node

    def report(self):
        err(self.name(), self.message(), self.parts())

    def name(self) -> str:
        return type(self).__name__

    def message(self) -> str:
        raise NotImplementedError()

    def parts(self) -> list[Part]:
        if self.node.source is None:
            return [str(self.node)]
        return [str(self.node), Source(self.node.source)]

@dataclass
class TypeMismatch(TyperError):
    expected: mm.Type
    actual: mm.Type

    def message(self) -> str:
        return f"Expected {get_name(self.expected)}, got {get_name(self.actual)}"

@dataclass
class InvalidType(TyperError):
    type: mm.Type

    def message(self) -> str:
        return f"Incompatible types infered: {get_name(self.type)}"

@dataclass
class UnresolvedOverload(TyperError):
    arg_types: list[mm.Type]

    def message(self) -> str:
        assert isinstance(self.node, (mm.Lookup, mm.Update, mm.Aggregate))
        rel = get_relation(self.node)
        types = ', '.join([get_name(t) for t in self.arg_types])
        return f"Unresolved overload: {rel.name}({types})"

@dataclass
class UnresolvedType(TyperError):

    def message(self) -> str:
        return "Unable to determine concrete type."
