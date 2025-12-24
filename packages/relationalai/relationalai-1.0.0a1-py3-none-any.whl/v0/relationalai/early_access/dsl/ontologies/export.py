from v0.relationalai.early_access.dsl import Namespace
from v0.relationalai.early_access.dsl.core.types import Type
from v0.relationalai.semantics.metamodel.util import OrderedSet
from v0.relationalai.early_access.dsl.core.relations import ExportRelation, RelationSignature


class Export:

    def __init__(self, key: list[Type], target_table: str) -> None:
        self.key = key
        self.target_table = target_table
        self.columns = OrderedSet[ExportRelation]()
        self.labels = OrderedSet[str]()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def column(self, name: str, *sig: Type, functional: bool = False):
        rel_name = f'output:col{len(self.columns):03d}'
        rel = ExportRelation(
            Namespace.top,
            rel_name,
            RelationSignature(*(self.key + list(sig)), functional=functional)
        )
        self.columns.add(rel)
        self.labels.add(name)
        return rel