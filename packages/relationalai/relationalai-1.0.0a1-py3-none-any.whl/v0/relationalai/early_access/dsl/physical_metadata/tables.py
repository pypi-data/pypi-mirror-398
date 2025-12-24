import re
from typing import Optional

from simple_ddl_parser import DDLParser

from v0.relationalai.early_access.dsl.core.types.standard import Integer, String, Date, Boolean, Decimal, Float, DateTime
from v0.relationalai.early_access.dsl.core.utils import generate_stable_uuid

_type_mapping = {
    'varchar': String,
    'char': String,
    'text': String,
    'int': Integer,
    'integer': Integer,
    'smallint': Integer,
    'bigint': Integer,
    'decimal': Decimal,
    'double': Float,
    'float': Float,
    'date': Date,
    'datetime': DateTime,
    'boolean': Boolean,
}

#=
# Deprecated old way to define a table via a DDL string.
#=

class Table:
    def __init__(self, name: Optional[str] = None, ddl_str: Optional[str] = None):
        if name and not ddl_str:
            super().__setattr__('name', name)
            super().__setattr__('columns', {})
        elif ddl_str:
            super().__setattr__('columns', {})
            parsed_dsl = self._parse_ddl(ddl_str)
            if name and name != parsed_dsl['table_name']:
                raise ValueError(
                    f'Provided table name {name} does not match the table name in the DDL'
                )
            else:
                super().__setattr__('name', parsed_dsl['table_name'])
            for col in parsed_dsl['columns']:
                self.columns[col['name']] = Column(
                    col['name'], _type_mapping[col['type'].lower()], self
                )
        else:
            raise ValueError('Either name or DDL must be provided')

    def __setattr__(self, key: str, value: 'Column') -> None:
        if key in self.__dict__:
            super().__setattr__(key, value)
        elif isinstance(value, Column):
            value.part_of = self
            self.columns[key] = value
            super().__setattr__(key, value)
        else:
           raise TypeError(
               f'Expected a Column instance for "{key}", got {type(value)}'
           )

    def __getattr__(self, key):
        if key in self.columns:
            return self.columns[key]
        else:
            raise AttributeError(f'Table {self.name} has no column named {key}')

    def pprint(self):
        return (
                f'Table: {self.name} ('
                + '\n'
                + ',\n'.join(
            [f' {col.name} {col.type.pprint()}' for _, col in self.columns.items()]
        )
                + '\n)'
        )

    @staticmethod
    def _parse_ddl(ddl: str):
        pattern = re.compile(r'constraint_[A-Za-z_]+')
        ddl_cleaned = pattern.sub('', ddl)
        ddl_json = DDLParser(ddl_cleaned, silent=False).run()
        return ddl_json[0]


class TemporalTable(Table):
    @property
    def temporal_col(self):
        return self._temporal_col

    def __init__(self, temporal_col_name: str, name: Optional[str] = None, ddl_str: Optional[str] = None):
        super().__init__(name, ddl_str)
        # no checks can be made here, as the columns are not yet necessarily defined
        self._temporal_col = Column(nm=temporal_col_name, type=DateTime, source=self)

    def pprint(self):
        return (
                f'Temporal Table: {self.name} ('
                + '\n'
                + ',\n'.join(
            [f' {col.name} {col.type.pprint()}' for _, col in filter(lambda kv: kv[0] != '_temporal_col', self.columns.items()) ]
        )
                + '\n)'
                + f'\ntemporal_col: {self._temporal_col.name}'
        )


class Column:
    _part_of: Table

    def __init__(self, nm, type, source=None):
        self.name = nm
        self.type = type
        if source:
            self._part_of = source

    @property
    def part_of(self):
        return self._part_of

    @part_of.setter
    def part_of(self, rel):
        if self._part_of is not None and self._part_of != rel:
            raise ValueError(
                f'Column is already part of another source: {self._part_of}'
            )
        self._part_of = rel

    def pprint(self):
        return f'{self.name} {self.type.pprint()}'

    def guid(self):
        return generate_stable_uuid(f'{self._part_of.name}_{self.name}')
