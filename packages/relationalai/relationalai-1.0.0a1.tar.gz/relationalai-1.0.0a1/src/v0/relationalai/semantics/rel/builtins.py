
from __future__ import annotations
from v0.relationalai.semantics.metamodel import types, factory as f
from v0.relationalai.semantics.metamodel.util import OrderedSet
from v0.relationalai.semantics.metamodel import builtins

# Rel Annotations as IR Relations (to be used in IR Annotations)

# output in arrow
arrow = f.relation("arrow", [])
arrow_annotation = f.annotation(arrow, [])

# do not output diagnostics for this error
no_diagnostics = f.relation("no_diagnostics", [f.field("code", types.Symbol)])

# do not inline this definition
no_inline = f.relation("no_inline", [])
no_inline_annotation = f.annotation(no_inline, [])

# indicates to the rel engine that this relation is a function
function = f.relation("function", [f.input_field("code", types.Symbol)])
function_annotation = f.annotation(function, [])

inner_loop = f.relation("inner_loop", [])
inner_loop_annotation = f.annotation(inner_loop, [])

inner_loop_non_stratified = f.relation("inner_loop_non_stratified", [])
inner_loop_non_stratified_annotation = f.annotation(inner_loop_non_stratified, [])

# collect all supported builtin rel annotations
builtin_annotations = OrderedSet.from_iterable([
    arrow, no_diagnostics, no_inline, function, inner_loop, inner_loop_non_stratified,
    
    # annotations on relations that do not currently propagate into Rel
    # TODO: from Thiago, ensure annotation goes from the Logical into the proper declaration
    builtins.track,
    builtins.recursion_config,
])

builtin_annotation_names = OrderedSet.from_iterable([a.name for a in builtin_annotations])
