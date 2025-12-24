from io import StringIO
from typing import Optional, Hashable

import numpy as np
import pandas as pd

from v0.relationalai.semantics import define, where
from v0.relationalai.semantics.std import decimals
from v0.relationalai.semantics.internal import internal as b
from v0.relationalai.early_access.dsl.bindings.common import BindableColumn, AbstractBindableTable
from v0.relationalai.early_access.dsl.snow.common import CsvColumnMetadata
from v0.relationalai.early_access.dsl.utils import normalize


class BindableCsvColumn(BindableColumn, b.Relationship):
    _metadata: CsvColumnMetadata
    _column_basic_type: str

    def __init__(self, metadata: CsvColumnMetadata, source: 'CsvTable', model):
        BindableColumn.__init__(self, metadata.name, metadata.datatype, source, model)
        fqn, fields, field_refs = self._relationship_ctor_inputs(metadata, source)
        b.Relationship.__init__(self, fqn, model=model.qb_model(), fields=fields, field_refs=field_refs)
        self._metadata = metadata
        self._column_basic_type = "Int64" if metadata.datatype._name == b.Integer._name else "string"

    @staticmethod
    def _relationship_ctor_inputs(metadata: CsvColumnMetadata, source: 'CsvTable'):
        """
        Handles the construction of the Relationship name components.

        We use a separate QB relationship per source column, as this allows proper typing.
        """
        col_name = metadata.name
        col_type = metadata.datatype
        source_name = source.physical_name()
        fqn = f"{source_name}_{col_name}"
        fields = [source._row_field, b.Field(name=col_name, type_str=str(col_type), type=col_type)]
        field_refs = [source._ref, col_type.ref()]
        return fqn, fields, field_refs

    def __call__(self, *args):
        """
        Allows the column to be called as a function, which is handy for manual data weaving.

        Example:
            row = Integer.ref()
            where(
                {source}.ID(row, id),
                {source}.NAME(row, name),
                person := Person.new(id=id)
            ).define(
                person,
                Person.name(person, name)
            )
        """
        if len(args) != 2:
            raise ValueError(f'Expected 2 arguments passed to a call to BindableColumn, got {len(args)}')
        return b.Relationship.__call__(self, *args)

    @property
    def metadata(self):
        return self._metadata

    def basic_type(self):
        return self._column_basic_type

    def decimal_scale(self) -> Optional[int]:
        typ = self.type()
        if decimals.is_decimal(typ):
            return decimals.scale(typ)
        else:
            return None

    def __repr__(self):
        return f"CSV:{self._source.physical_name()}.{self.physical_name()}"


class CsvTable(AbstractBindableTable[BindableCsvColumn]):
    _basic_type_schema: dict[Hashable, str]
    _csv_data: list[pd.DataFrame]
    _num_rows: int

    def __init__(self, fqn: str, schema: dict[str, b.Concept], model):
        AbstractBindableTable.__init__(self, fqn, model, set())
        self._initialize(schema, model)

    def _initialize(self, schema: dict[str, b.Concept], model):
        self._concept = b.Concept(self._fqn, extends=[b.Concept.builtins["RowId"]])
        b.Concept.globals[self._fqn.lower()] = self._concept
        ref = self._concept.ref("row_id")
        assert isinstance(ref, b.Ref)
        self._ref = ref
        self._row_field = b.Field(name="row_id", type_str=self._fqn, type=self._concept)
        self._csv_data = list()
        self._num_rows = 0
        self._cols = {column_name: BindableCsvColumn(CsvColumnMetadata(column_name, column_type), self, model)
                      for column_name, column_type in schema.items()}
        self._basic_type_schema = {col.metadata.name: col.basic_type() for col in self._cols.values()}

    def _compile_lookup(self, compiler:b.Compiler, ctx:b.CompilerContext):
        return compiler.lookup(self._ref, ctx)

    def _to_keys(self) -> list[b.Ref]:
        assert isinstance( self._ref, b.Ref)
        return [self._ref]

    def __str__(self):
        # returns the name of the table, as well as the columns and their types
        return self.physical_name() + ':\n' + '\n'.join(
            [f' {col.metadata.name} {col.metadata.datatype}' for _, col in self._cols.items()]
        ) + '\n' + '\n'.join(
            [f' {fk.source_columns} -> {fk.target_columns}' for fk in self._foreign_keys]
        )

    @property
    def csv_data(self) -> list[pd.DataFrame]:
        return self._csv_data

    def physical_name(self) -> str:
        return self._fqn.lower()

    def data(self, csv_data: str):
        csv_df = pd.read_csv(StringIO(normalize(csv_data)), dtype=self._basic_type_schema)
        self._csv_data.append(csv_df)
        CsvSourceModule.generate(self, csv_df, row_offset=self._num_rows)
        # update offset now that we generated the rules
        self._num_rows += len(csv_df)

class CsvSourceModule:

    @staticmethod
    def generate(table: CsvTable, data: pd.DataFrame, row_offset: int = 0):
        for local_index, row in enumerate(data.itertuples(index=False)):
            row_index = row_offset + local_index
            for column_name in data.columns:
                value = getattr(row, column_name)
                if pd.notna(value):
                    column = table.__getattr__(column_name)
                    column_type = column.type()
                    if column_type._name == b.Date._name:
                        CsvSourceModule._row_to_date_value_rule(column, row_index, value)
                    elif column_type._name == b.DateTime._name:
                        CsvSourceModule._row_to_date_time_value_rule(column, row_index, value)
                    elif b.is_decimal(column_type):
                        CsvSourceModule._row_to_decimal_value_rule(column, row_index, value)
                    else:
                        CsvSourceModule._row_to_value_rule(column, row_index, value)

    @staticmethod
    def _row_to_value_rule(column, row, value):
        # if numpy scalar, convert to a native Python type
        if isinstance(value, np.generic):
            value = value.item()
        define(column(row, value))

    @staticmethod
    def _row_to_date_value_rule(column, row, value):
        parse_date = b.Relationship.builtins['parse_date']
        rez = b.Date.ref()
        where(parse_date(value, 'yyyy-mm-dd', rez)).define(column(row, rez))

    @staticmethod
    def _row_to_date_time_value_rule(column, row, value):
        parse_datetime = b.Relationship.builtins['parse_datetime']
        rez = b.DateTime.ref()
        where(parse_datetime(value, 'yyy-mm-dd HH:MM:SS z', rez)).define(column(row, rez))

    @staticmethod
    def _row_to_decimal_value_rule(column, row, value):
        define(column(row, decimals.parse(value, column.type())))
