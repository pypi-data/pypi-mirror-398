from __future__ import annotations
from v0.relationalai.semantics.internal import snowflake as sf, internal as b
from v0.relationalai.early_access.dsl.bindings.common import BindableColumn, AbstractBindableTable


#=
# Bindable classes and interfaces.
#=

class BindableSnowflakeColumn(BindableColumn, sf.Column):
    _metadata: b.Field

    def __init__(self, metadata: b.Field, table: 'SnowflakeTable', model):
        col_name = metadata.name
        col_type = b.field_to_type(model.qb_model(), metadata)
        sf.Column.__init__(self, table, col_name)
        BindableColumn.__init__(self, col_name, col_type, table, model)
        self._metadata = metadata

    @property
    def metadata(self):
        return self._metadata

    def __repr__(self):
        return f"Snowflake:{super().__repr__()}"


class SnowflakeTable(AbstractBindableTable[BindableSnowflakeColumn], sf.Table):

    def __init__(self, fqn: str, model, schema:dict[str, str|b.Concept]|None=None):
        sf.Table.__init__(self, fqn, schema=schema)
        AbstractBindableTable.__init__(self, fqn, model, set())
        self._initialize(model)

    def _initialize(self, model):
        self._lazy_init()
        self._model = model
        schema_info = self._schemas[(self._database, self._schema)]
        table_info = schema_info.tables[self._table]
        self._cols = {field.name: BindableSnowflakeColumn(field, self, model) for field in table_info.fields}
        self._generate_declare()

    def _generate_declare(self):
        src = f"declare {self.physical_name()}"
        self._model.qb_model().define(b.RawSource('rel', src))

    def _to_type(self) -> b.Concept:
        return self._concept

    def _to_keys(self) -> list[b.Ref]:
        return [self._rel._field_refs[0]]

    def _compile_lookup(self, compiler:b.Compiler, ctx:b.CompilerContext):
        sf.Table._used_sources.add(self)
        compiler.lookup(self._rel, ctx)
        return compiler.lookup(b.RelationshipFieldRef(None, self._rel, 0), ctx)

    def __str__(self):
        # returns the name of the table, as well as the columns and their types
        return f"SnowflakeTable({self.physical_name()}"

    def physical_name(self):
        # physical relation name is always in the form of `{database}_{schema}_{table}
        return f"{self._fqn.lower()}".replace('.', '_')
