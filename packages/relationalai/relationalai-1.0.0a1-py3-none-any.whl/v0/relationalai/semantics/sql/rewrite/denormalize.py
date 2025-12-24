from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple, Union
from typing import cast

from v0.relationalai.semantics.metamodel import ir, compiler as c, factory as f, types, visitor
from v0.relationalai.semantics.metamodel.util import FrozenOrderedSet, OrderedSet, ordered_set, group_by, split_by

class Denormalize(c.Pass):
    """
    Pass to denormalize relations, grouping relations that have the same entity as key.

    General algorithm:

    1. when handling the Model, go to its relations and find the ones that have common
    entity keys. They will be denormalized (joined together as a single "table").
    2. when handling lookups and updates that refer to one of these relations that were
    denormalized, change the reference to be to the new relation and fill the blanks with
    Nones, which represent NULLs.
    3. finally, when handling Logical nodes, try to group together lookups and updates that
    are refering to the same denormalized relation. This may remove some of the NULLs.
    """
    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        return OldDenormalize().walk(model)

@dataclass
class OldDenormalize(visitor.Rewriter):

    denormalized: dict[ir.Relation, ir.Relation] = field(default_factory=dict, init=False, hash=False, compare=False)

    def reset(self):
        self.context = dict()
        self.denormalized = dict()

    def handle_model(self, model: ir.Model, parent: None):
        # denormalize some relations in the model, set it in the context, and then push
        # that context to the root traversal so that references to the denormalized
        # relations are adjusted.

        # denormalize the relations
        relations, self.denormalized = self._denormalize_relations(model.relations)

        # rewrite tasks to refer to denormalized relations
        return ir.Model(
            self.walk_set(model.engines, model),
            relations,
            self.walk_set(model.types, model),
            self.walk(model.root, model),
        )

    def handle_update(self, node: ir.Update, parent: ir.Node):
        # if the relation to be updated was denormalized, denormalize the reference

        if node.relation not in self.denormalized:
            return super().handle_update(node, parent)

        denormalized_relation = self.denormalized[node.relation]
        args = self._denormalize_reference(
            denormalized_relation, node.relation, node.args
        )

        return ir.Update(
            node.engine,
            denormalized_relation,
            args,
            node.effect,
            node.annotations
        )

    def handle_lookup(self, node: ir.Lookup, parent: ir.Node):
        # if the relation to be looked up was denormalized, denormalize the reference

        if node.relation not in self.denormalized:
            return super().handle_lookup(node, parent)

        denormalized_relation = self.denormalized[node.relation]
        args = self._denormalize_reference(
            denormalized_relation, node.relation, node.args
        )

        return ir.Lookup(
            node.engine,
            denormalized_relation,
            args
        )

    def handle_logical(self, node: ir.Logical, parent: ir.Node):
        # denormalize the body first
        body = self.walk_list(node.body, node)

        # Unwrap single lookups from the logical
        # for example we may have this IR to say that `adult` may not have a `name`
        # Logical ⇑[name=None]
        #     name(adult, name)
        updated_body = [
            t.body[0] if isinstance(t, ir.Logical) and len(t.body) == 1 else t
            for t in body
        ]

        # function to compute a key to group Lookups or Updates that can be merged
        def task_key(t: ir.Task):
            assert isinstance(t, (ir.Lookup, ir.Update))
            return (t.kind, t.relation, t.args[0])

        # now group references
        tasks, new_body = split_by(updated_body, lambda t: isinstance(t, (ir.Lookup, ir.Update)))
        for _, grouped_tasks in group_by(tasks, task_key).items():
            grouped_tasks = cast(OrderedSet[Union[ir.Lookup, ir.Update]], grouped_tasks)

            # get some of the tasks as a representative
            some = grouped_tasks.some()

            if len(grouped_tasks) == 1:
                new_body.append(some)
                continue

            # now join the arguments of the multiple references
            # TODO: this will fail if we have multiple tasks on the same arg
            new_args = []
            i = 0
            for _ in some.relation.fields:
                # note that we are still using None to indicate we don't care about the column
                v = None
                for t in grouped_tasks:
                    if t.args[i] is not None:
                        v = t.args[i]
                        break
                new_args.append(v)
                i += 1

            # finally, create a rewritten task for the whole group
            if isinstance(some, ir.Lookup):
                new_body.append(ir.Lookup(some.engine, some.relation, tuple(new_args)))
            else:
                new_body.append(ir.Update(some.engine, some.relation, tuple(new_args), some.effect, some.annotations)) # TODO maybe merge annos?
        return ir.Logical(
            node.engine,
            node.hoisted,
            tuple(new_body)
        )


    def _denormalize_reference(self, denormalized_relation, relation, args) -> Tuple[ir.Value, ...]:
        """ Adjust arguments to a denormalized reference.

            A reference to `relation` was used with `args`. But `relation` was denormalized
            into `denormalized_relation`. This method returns a new tuple of adjusted args
            to account for the denormalization, filling Nones as appropriate.
        """

        # the first arg is always the entity
        new_args = [args[0]]
        # for the rest of the denormalized relation columns, lookup only if the field came
        # from this relation, otherwise use None
        i = 1
        for fld in denormalized_relation.fields[1:]:
            if fld in relation.fields:
                new_args.append(args[i])
                i += 1
            else:
                new_args.append(None)
        return tuple(new_args)

    def _denormalize_relations(self, relations: FrozenOrderedSet[ir.Relation]) -> \
        Tuple[FrozenOrderedSet[ir.Relation], dict[ir.Relation, ir.Relation]]:

        """ Denormalize the relations that can be denormalized.

        Group together relations that are keyed by the same "entity". This method defines
        entities as being types that have a unary relation containing only that type. All
        relations whose first argument is this type are grouped together.

        Returns a tuple with 2 elements:
        1. The new set of relations after denormalization
        2. A dict from relations that were denormalized away to the new relation that took its place.
        """
        new_relations = ordered_set()
        denormalized: dict[ir.Relation, ir.Relation] = dict()

        # entities are non-builtin types that have a unary relation
        entity_types: OrderedSet[ir.Type] = ordered_set()
        entity_relations: dict[ir.Type, ir.Relation] = dict()

        for r in relations:
            if len(r.fields) == 1 and not types.is_builtin(r.fields[0].type) and not r.name == 'Error':
                e = r.fields[0].type
                entity_types.add(e)
                entity_relations[e] = r

        # filter out relations that don't have an entity as a key
        with_entity, unaffected = split_by(
            relations,
            lambda r:
                r.fields[0].type in entity_types # the first element is an entity
                # TODO - we need to account for wide relations that have multis
        )
        new_relations.update(unaffected)

        # group relations by entity, they will be denormalized
        by_entity = group_by(with_entity, lambda r: cast(ir.ScalarType, r.fields[0].type))
        for e_type, group in by_entity.items():
            r = entity_relations[e_type]
            fields = []
            # the first column of the denormalized relation is the "id"
            fields.append(r.fields[0])
            for relation in group:
                # add all fields except the first entity field
                # TODO - we may have multiple relations with the same name
                fields.extend(relation.fields[1:])

            # create the new denormalized relation, add it to the new_relations set
            denormalized_relation = f.relation(
                e_type.name,
                fields
            )
            new_relations.add(denormalized_relation)

            # make sure the original relations point to the new relation
            for g in group:
                denormalized[g] = denormalized_relation

        return new_relations.frozen(), denormalized
