from __future__ import annotations
from typing import Tuple

from v0.relationalai.semantics.metamodel import builtins, ir, factory as f, types, visitor
from v0.relationalai.semantics.metamodel.compiler import Pass, group_tasks
from v0.relationalai.semantics.metamodel.util import OrderedSet
from v0.relationalai.semantics.metamodel.util import FrozenOrderedSet
from v0.relationalai.semantics.metamodel.typer.typer import is_primitive

class FormatOutputs(Pass):
    def __init__(self, handle_outputs: bool=True):
        super().__init__()
        self._handle_outputs = handle_outputs

    #--------------------------------------------------
    # Public API
    #--------------------------------------------------
    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        wide_outputs = options.get("wide_outputs", False)
        return self.OutputRewriter(wide_outputs).walk(model)

    class OutputRewriter(visitor.Rewriter):
        def __init__(self, wide_outputs: bool = False):
            super().__init__()
            self.wide_outputs = wide_outputs

        def handle_logical(self, node: ir.Logical, parent: ir.Node):
            # Rewrite children first
            node = super().handle_logical(node, parent)

            groups = group_tasks(node.body, {
                "outputs": ir.Output,
            })

            # If no outputs, return as is
            if not groups["outputs"]:
                return node

            return adjust_outputs(node, groups["outputs"], self.wide_outputs)

#--------------------------------------------------
# GNF vs wide output support
#--------------------------------------------------
def adjust_outputs(task: ir.Logical, outputs: OrderedSet[ir.Task], wide_outputs: bool = False):

    body = list(task.body)

    # For wide outputs, only adjust the output task to include the keys.
    if wide_outputs:
        for output in outputs:
            assert(isinstance(output, ir.Output))
            if output.keys:
                body.remove(output)
                body.append(rewrite_wide_output(output))
        return ir.Logical(task.engine, task.hoisted, tuple(body), task.annotations)

    # For GNF outputs we need to generate a rule for each "column" in the output
    else:
        # First split outputs in potentially multiple outputs, one for each "column"
        for output in outputs:
            assert(isinstance(output, ir.Output))
            if output.keys:
                # Remove the original output. This is replaced by per-column outputs below
                body.remove(output)

                is_export = builtins.export_annotation in output.annotations

                # Generate an output for each "column"
                # output looks like def output(:cols, :col000, key0, key1, value):
                original_cols = OrderedSet()
                for idx, alias in enumerate(output.aliases):
                    # Skip None values which are used as a placeholder for missing values
                    if alias[1] is None:
                        continue
                    original_cols.add(alias[1])
                    body.extend(_generate_output_column(output, idx, alias, is_export))

                idx = len(output.aliases)
                for key in output.keys:
                    if key not in original_cols:
                        body.extend(_generate_output_column(output, idx, (key.name, key), is_export))
                        idx += 1

        return ir.Logical(task.engine, task.hoisted, tuple(body), task.annotations)

# TODO: return non list?
def _generate_output_column(output: ir.Output, idx: int, alias: tuple[str, ir.Value], is_export: bool):
    if not output.keys:
        return [output]

    aliases = [("cols", f.literal("cols", types.Symbol))] if not is_export else []
    aliases.append(("col", f.literal(f"col{idx:03}", types.Symbol)))

    # Append all keys at the start
    for k in output.keys:
        aliases.append((f"key_{k.name}_{idx}", k))

    if (is_export and
        isinstance(alias[1], ir.Var) and
        (not is_primitive(alias[1].type) or alias[1].type == types.Hash)):

        uuid = f.var(f"{alias[0]}_{idx}_uuid", types.String)
        aliases.append((uuid.name, uuid))

        return [
            ir.Lookup(None, builtins.uuid_to_string, (alias[1], uuid)),
            ir.Output(
                output.engine,
                FrozenOrderedSet.from_iterable(aliases),
                output.keys,
                output.annotations
            )
        ]
    else:
        aliases.append(alias)

        return [
            ir.Output(
                output.engine,
                FrozenOrderedSet.from_iterable(aliases),
                output.keys,
                output.annotations
            )
        ]

def rewrite_wide_output(output: ir.Output):
    assert(output.keys)

    # Only append keys that are not already in the output
    suffix_keys = []
    for key in output.keys:
        if all([val is not key for _, val in output.aliases]):
            suffix_keys.append(key)

    aliases: OrderedSet[Tuple[str, ir.Value]] = OrderedSet()

    # Add the remaining args, unless it is already a key
    for name, val in output.aliases:
        if not isinstance(val, ir.Var) or val not in suffix_keys:
            aliases.add((name, val))

    # Add the keys to the output
    for key in suffix_keys:
        aliases.add((key.name, key))

    # TODO - we are assuming that the Rel compiler will translate nullable lookups
    # properly, returning a `Missing` if necessary, like this:
    # (nested_192(_adult, _adult_name) or (not nested_192(_adult, _) and _adult_name = Missing)) and
    return ir.Output(
        output.engine,
        aliases.frozen(),
        output.keys,
        output.annotations
    )

    # TODO: in the rel compiler, see if we can do this outer join
    # 1. number of keys
    # 2. each relation
    # 3. each variable, starting with the keys
    # 4. tag output with @arrow

    # @arrow def output(_book, _book_title, _author_name):
    #   rel_primitive_outer_join(#1, book_title, author_name, _book, _book_title, _author_name)
    # def output(p, n, c):
    #     rel_primitive_outer_join(#1, name, coolness, p, n, c)
