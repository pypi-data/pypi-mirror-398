from __future__ import annotations

from typing import Optional, Sequence as PySequence, cast

from v0.relationalai.semantics.metamodel import ir, compiler as c, factory as f, util
from v0.relationalai.semantics.metamodel.helpers import collect_implicit_vars

class Splinter(c.Pass):
    """
    Splits multi-headed rules into multiple rules. Additionally, infers missing Exists tasks.
    """

    def __init__(self):
        super().__init__()
        self.name_cache = util.NameCache(start_from_one=True)

    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        if isinstance(model.root, ir.Logical):
            final = []
            new_relations:list[ir.Relation] = []
            new_relations.extend(model.relations)
            for child in model.root.body:
                new_logicals, relation = self.split(cast(ir.Logical, child))
                final.extend(new_logicals)
                if relation:
                    new_relations.append(relation)
            return ir.Model(
                    model.engines,
                    util.FrozenOrderedSet.from_iterable(new_relations),
                    model.types,
                    ir.Logical(
                        model.root.engine,
                        model.root.hoisted,
                        tuple(final)
                    )
                )
        return model

    def split(self, node: ir.Logical) -> tuple[list[ir.Logical], Optional[ir.Relation]]:
        # Split this logical, which represents a rule, into potentially many logicals, one
        # for each head (update or output)
        effects, body = self.split_items(node.body)

        if len(effects) > 1:
            effects_vars = collect_implicit_vars(*effects)
            final:list[ir.Logical] = []
            connection = None
            if body:
                # if the node has a body, create a connection, derive the body into the
                # connection, and then lookup this connection on the other logicals
                name = self.name_cache.get_name(node.id, "_intermediate")
                connection = f.relation(name, [f.field(f"f_{i+1}", v.type) for i, v in enumerate(effects_vars)])
                final.append(f.logical([*body, f.derive(connection, list(effects_vars))]))

            for effect in effects:
                if connection:
                    # there's a connection, create a logical that looks up from the connection
                    # and derives into the effect
                    lookup = f.lookup(connection, effects_vars.get_list())
                    final.append(f.logical([lookup, effect]))
                else:
                    # if there's no connection, the effect is self contained (probably literals)
                    final.append(f.logical([effect]))
            return final, connection
        return [node], None


    def split_items(self, items: PySequence[ir.Task]) -> tuple[list[ir.Task], list[ir.Task]]:
        effects = []
        body = []
        for item in items:
            if isinstance(item, (ir.Update, ir.Output)):
                effects.append(item)
            else:
                body.append(item)
        return effects, body
