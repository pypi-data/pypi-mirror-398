from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import cast, Optional

from v0.relationalai.semantics.metamodel import ir, compiler as c, factory as f
from v0.relationalai.semantics.metamodel.util import OrderedSet, ordered_set
from v0.relationalai.semantics.metamodel.visitor import Visitor


class RecursiveUnion(c.Pass):
    """
        Pass to rewrite recursive relations as unions of `ir.Logical` nodes.

        This pass identifies recursive relations by detecting `ir.Logical` nodes that both read from and write to the same `ir.Relation`.
        Once a recursive relation is found, all logicals that write to that relation are grouped together.
        These groups are then wrapped in an `ir.Union`, and the model's root task is reconstructed accordingly.
    """

    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        rpv = TopLogicalReadWriteVisitor()
        model.accept(rpv)

        reads: dict[ir.Logical, OrderedSet[int]] = rpv.reads()
        writes: dict[ir.Logical, OrderedSet[int]] = rpv.writes()

        # Step 1: Identify recursive relation IDs (read & write in same logical)
        recursive_rel_ids = {
            rel_id
            for logical, write_ids in writes.items()
            for rel_id in write_ids & reads.get(logical, OrderedSet())
        }

        # Step 2: Group ir.Logical nodes that write to any recursive relation
        recursive_groups: dict[int, OrderedSet[ir.Logical]] = defaultdict(OrderedSet)
        recursive_logicals: OrderedSet[ir.Logical] = OrderedSet()

        for logical, write_ids in writes.items():
            for rel_id in write_ids:
                if rel_id in recursive_rel_ids:
                    recursive_groups[rel_id].add(logical)
                    recursive_logicals.add(logical)

        if recursive_logicals:

            # Step 3: Construct the new logical body
            root_logical = cast(ir.Logical, model.root)
            new_body = [logical for logical in root_logical.body if logical not in recursive_logicals]

            # Step 4: Add unions for each recursive group
            for rel_id, logical_group in recursive_groups.items():
                split_group = ordered_set()

                for logical in logical_group:
                    # Count total ir.Update tasks in this logical
                    update_count = sum(isinstance(t, ir.Update) for t in logical.body)

                    # If there's only one, keep the original logical as-is
                    if update_count == 1:
                        split_group.add(logical)
                        continue

                    # Otherwise, keep only updates relevant to this relation (and non-update tasks)
                    filtered_body = [
                        t for t in logical.body
                        if not isinstance(t, ir.Update) or t.relation.id == rel_id
                    ]

                    if filtered_body:
                        split_group.add(f.logical(filtered_body))

                if split_group:
                    new_body.append(f.union(list(split_group)))

            return model.reconstruct(model.engines, model.relations, model.types, f.logical(new_body), model.annotations)

        return model

@dataclass
class TopLogicalReadWriteVisitor(Visitor):
    """
    Compute the set of reads and writes relation ids for top level Logical nodes.
    Skip unions, because we are using this pass to find recursive rule and union them.

    Note that reads are Lookups and writes are Updates. We don't consider Output a write
    because it is not targeting a relation.

    This visitor can be called from ir.Model.
    """

    _reads: dict[ir.Logical, OrderedSet[int]] = field(default_factory=dict)
    _writes: dict[ir.Logical, OrderedSet[int]] = field(default_factory=dict)

    def reads(self):
        return self._reads

    def writes(self):
        return self._writes

    _stack: list[ir.Logical] = field(default_factory=list)

    def visit_logical(self, node: ir.Logical, parent: Optional[ir.Node]):
        # We only track reads/writes for top-level Logical nodes and also skip top level program Logical node.
        if not isinstance(parent, ir.Model):
            self._stack.append(node)
        super().visit_logical(node, parent)
        if self._stack:
            self._stack.pop()

    def visit_lookup(self, node: ir.Lookup, parent: Optional[ir.Node]):
        for logical in self._stack:
            if logical not in self._reads:
                self._reads[logical] = ordered_set()
            self._reads[logical].add(node.relation.id)
        return super().visit_lookup(node, parent)

    def visit_update(self, node: ir.Update, parent: Optional[ir.Node]):
        for logical in self._stack:
            if logical not in self.writes():
                self._writes[logical] = ordered_set()
            self._writes[logical].add(node.relation.id)
        return super().visit_update(node, parent)

    def visit_union(self, node: ir.Union, parent: Optional[ir.Node]):
        # Skip unions, because we are using this pass to find recursive rule and union them.
        pass