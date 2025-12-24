from typing import cast, Optional

import v0.relationalai as rai
from v0.relationalai import Config
from v0.relationalai.early_access.dsl.snow.common import TabularMetadata, ColumnMetadata, SchemaMetadata, \
    ForeignKey, ColumnRef


class Executor:
    def __init__(self, config: Optional[Config] = None):
        self._provider = cast(rai.clients.snowflake.Provider, rai.Provider(config=config))
        self._table_meta_cache = {}
        self._schema_fk_cache = {}

    def table_metadata(self, name: str):
        self._validate_table_name(name)
        if name in self._table_meta_cache:
            return self._table_meta_cache[name]
        # name comes in the form of `{database_name}.{schema_name}.{table_name}`
        database_nm, schema_nm, table_nm = name.upper().split(".")
        query = f"""
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, NUMERIC_PRECISION, NUMERIC_PRECISION_RADIX, NUMERIC_SCALE
        FROM {database_nm}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema_nm}' AND TABLE_NAME = '{table_nm}'
        ORDER BY TABLE_NAME, COLUMN_NAME, DATA_TYPE
        """
        # execute SQL
        rez = self._provider.sql(query)
        meta = self._parse_table_metadata(name, rez)
        # supplement with FKs
        schema_nm = f"{database_nm}.{schema_nm}".lower()
        self._supplement_with_foreign_keys(meta, schema_nm)
        # cache before returning
        self._table_meta_cache[name] = meta
        return meta

    def _supplement_with_foreign_keys(self, tb_meta, schema_name: str):
        schema_fk_meta = self.schema_foreign_keys(schema_name)
        # suboptimal but works for now
        for fk in schema_fk_meta.foreign_keys:
            if tb_meta.name == fk.source_columns[0].table:
                tb_meta.foreign_keys.add(fk)

    @staticmethod
    def _parse_table_metadata(name, result):
        meta = TabularMetadata(name=name)
        for row in result:
            attr = ColumnMetadata(
                name=row['COLUMN_NAME'],
                datatype=row['DATA_TYPE'],
                is_nullable=row['IS_NULLABLE'] == 'YES',
                numeric_precision=row['NUMERIC_PRECISION'],
                numeric_precision_radix=row['NUMERIC_PRECISION_RADIX'],
                numeric_scale=row['NUMERIC_SCALE']
            )
            meta.columns.append(attr)
        return meta

    @staticmethod
    def _validate_table_name(name):
        # check if the table name is in the form of `{database_name}.{schema_name}.{table_name}`
        if len(name.split('.')) != 3:
            raise ValueError(f'Table name {name} is not in the correct format')

    def schema_foreign_keys(self, name):
        self._validate_schema_name(name)
        if name in self._schema_fk_cache:
            return self._schema_fk_cache[name]

        # name comes in the form of `{database_name}.{schema_name}`
        query = f"""
        SHOW IMPORTED KEYS IN SCHEMA {name};
        """
        rez = self._provider.sql(query)
        meta = self._parse_schema_foreign_keys(name, rez)
        self._schema_fk_cache[name] = meta
        return meta

    @staticmethod
    def _parse_schema_foreign_keys(name, results):
        metadata = SchemaMetadata(name=name)
        for row in results:
            fk_table_nm = f'{row["fk_database_name"]}.{row["fk_schema_name"]}.{row["fk_table_name"]}'.lower()
            pk_table_nm = f'{row["pk_database_name"]}.{row["pk_schema_name"]}.{row["pk_table_name"]}'.lower()
            # get columns refs, since FK may be composite, we need to handle multiple columns
            # TODO: implement multi-col FK support
            source_cols = [ColumnRef(fk_table_nm, row['fk_column_name'])]
            target_cols = [ColumnRef(pk_table_nm, row['pk_column_name'])]
            fk = ForeignKey(
                name=row['fk_name'],
                source_columns=source_cols,
                target_columns=target_cols
            )
            metadata.foreign_keys.append(fk)
        return metadata

    @staticmethod
    def _validate_schema_name(name):
        # check if the schema name is in the form of `{database_name}.{schema_name}`
        if len(name.split('.')) != 2:
            raise ValueError(f'Schema name {name} is not in the correct format')

    def provider(self):
        return self._provider
