"""
Module providing database DDL (Data Definition Language) operations.

This module defines abstract and concrete classes for managing DDL operations
such as creating, altering, truncating, and dropping tables and views,
as well as creating indexes for both Microsoft SQL Server and PostgreSQL databases.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from sqlalchemy import Column, Engine, Index, Selectable, Table, exc, schema, text

if TYPE_CHECKING:
    from .logger import Logger


class DdlOperations(ABC):
    """Abstract base class for DDL operations."""

    def __init__(self, engine: Engine, logger: Logger) -> None:
        """
        Initialize the DDL operations handler.

        :param engine: SQLAlchemy engine connected to the target database.
        :param logger: Logger instance.
        """
        self.engine = engine
        self.logger = logger

    def quote(self, name: str) -> str:
        """Quote database object names."""
        return self.engine.dialect.identifier_preparer.quote(name)

    def execute(self, query: str) -> None:
        """Execute a raw SQL query."""
        try:
            with self.engine.begin() as conn:
                conn.execute(text(query))
                self.logger.debug(f"Executed query: {query}")
        except exc.SQLAlchemyError as e:
            self.logger.debug(f"Error executing query: {query} : {e}")
            raise

    def create_table(self, table: Table) -> None:
        """Create a table."""
        if self.engine.dialect.has_table(self.engine.connect(), table.name, schema=table.schema):
            table.metadata.reflect(bind=self.engine, extend_existing=True, schema=table.schema, only=[table.name])
            self.logger.info(f"Table {table.schema}.{table.name} already exists.")
            return
        sql_statement = str(schema.CreateTable(table).compile(self.engine))
        try:
            self.execute(sql_statement)
            table.metadata.reflect(bind=self.engine, extend_existing=True, schema=table.schema, only=[table.name])
            self.logger.info(f"Created table {table.schema}.{table.name}.")
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error creating table {table.schema}.{table.name}: {e}.")
            raise

    def drop_table(self, table: Table) -> None:
        """Drop a table."""
        if not self.engine.dialect.has_table(self.engine.connect(), table.name, schema=table.schema):
            self.logger.info(f"Table {table.schema}.{table.name} does not exist.")
            return
        sql_statement = str(schema.DropTable(table).compile(self.engine))
        try:
            self.execute(sql_statement)
            self.logger.info(f"Dropped table {table.schema}.{table.name}.")
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error dropping table {table.schema}.{table.name}: {e}.")
            raise

    def truncate_table(self, table: Table) -> None:
        """Truncate a table."""
        if not self.engine.dialect.has_table(self.engine.connect(), table.name, schema=table.schema):
            self.logger.info(f"Table {table.schema}.{table.name} does not exist.")
            return
        sql_statement = f"TRUNCATE TABLE {self.quote(table.schema)}.{self.quote(table.name)}"
        try:
            self.execute(sql_statement)
            self.logger.info(f"Truncated table {table.schema}.{table.name}.")
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error truncating table {table.schema}.{table.name}: {e}.")
            raise

    @abstractmethod
    def _add_column_sql(self, table: Table, column: Column) -> str:
        """Generate SQL for adding a column."""

    def add_column(self, table: Table, column: Column) -> None:
        """Add a column to a table."""
        if column.name in table.c:
            self.logger.info(f"Column {column.name} already exists in table {table.schema}.{table.name}.")
            return
        sql_statement = self._add_column_sql(table, column)
        try:
            self.execute(sql_statement)
            table.append_column(column)
            self.logger.info(f"Added column {column.name} to table {table.schema}.{table.name}.")
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error adding column {column.name} to table {table.schema}.{table.name}: {e}.")
            raise

    @abstractmethod
    def _create_view_sql(self, view: Table, definition: Selectable, *, or_replace: bool=True) -> str:
        """Generate SQL for creating a view."""

    def create_view(self, view: Table, definition: Selectable, *, or_replace: bool=True) -> None:
        """Create a view."""
        if self.engine.dialect.has_table(self.engine.connect(), view.name, schema=view.schema) and not or_replace:
            view.metadata.reflect(bind=self.engine, views=True, extend_existing=True, schema=view.schema,
                                  only=[view.name])
            self.logger.info(f"View {view.schema}.{view.name} already exists")
            return
        sql_statement = self._create_view_sql(view, definition, or_replace)
        try:
            self.execute(sql_statement)
            view.metadata.reflect(bind=self.engine, views=True, extend_existing=True, schema=view.schema,
                                  only=[view.name])
            self.logger.info(f"Created view {view.schema}.{view.name}.")
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error creating view {view.schema}.{view.name}: {e}.")
            raise

    def create_index(self, table: Table, columns_name: list, index_name: str, *, unique: bool=False) -> None:
        """Create an index on multiple table columns."""
        if index_name in [idx.name for idx in table.indexes]:
            self.logger.info(f"Index {index_name} already exists on table {table.schema}.{table.name}.")
            return
        for column_name in columns_name:
            if column_name not in table.c:
                msg = f"Column {column_name} does not exist in table {table.schema}.{table.name}."
                raise ValueError(msg)
        index = Index(index_name, *[table.c[column_name] for column_name in columns_name], unique=unique)
        try:
            index.create(self.engine)
            self.logger.info(
                f"Created index {index_name} on columns {', '.join(columns_name)} of table {table.schema}.{table.name}.")
        except exc.SQLAlchemyError as e:
            self.logger.error(
                f"Error creating index {index_name} on columns {', '.join(columns_name)} of table {table.schema}.{table.name}: {e}.")
            raise

class MssqlDdlOperations(DdlOperations):
    """Concrete class for MSSQL DDL operations."""

    def _add_column_sql(self, table: Table, column: Column) -> str:
        column_definition = f"{self.quote(column.name)} {column.type.compile(self.engine.dialect)}"
        return f"ALTER TABLE {self.quote(table.schema)}.{self.quote(table.name)} ADD {column_definition}"

    def _create_view_sql(self, view: Table, definition: Selectable, *, or_replace: bool=True) -> str:
        if or_replace:
            sql_statement = f"CREATE OR ALTER VIEW {self.quote(view.schema)}.{self.quote(view.name)} AS {definition.compile(compile_kwargs={'literal_binds': True})}"
        else:
            sql_statement = f"CREATE VIEW {self.quote(view.schema)}.{self.quote(view.name)} AS {definition.compile(compile_kwargs={'literal_binds': True})}"
        return sql_statement

class PostgresqlDdlOperations(DdlOperations):
    """Concrete class for PostgreSQL DDL operations."""

    def _add_column_sql(self, table: Table, column: Column) -> str:
        column_definition = f"{self.quote(column.name)} {column.type.compile(self.engine.dialect)}"
        return f"ALTER TABLE {self.quote(table.schema)}.{self.quote(table.name)} ADD COLUMN {column_definition}"

    def _create_view_sql(self, view: Table, definition: Selectable, *, or_replace: bool=True) -> str:
        if or_replace:
            sql_statement = f"CREATE OR REPLACE VIEW {self.quote(view.schema)}.{self.quote(view.name)} AS {definition.compile(compile_kwargs={'literal_binds': True})}"
        else:
            sql_statement = f"CREATE VIEW {self.quote(view.schema)}.{self.quote(view.name)} AS {definition.compile(compile_kwargs={'literal_binds': True})}"
        return sql_statement

def create_ddl_operations(engine: Engine, logger: Logger) -> MssqlDdlOperations | PostgresqlDdlOperations:
    """Create the appropriate DDL operations class."""
    dialect = engine.dialect.name
    if dialect == "mssql":
        return MssqlDdlOperations(engine, logger)
    if dialect == "postgresql":
        return PostgresqlDdlOperations(engine, logger)
    msg = f"DDL operations for database type '{dialect}' are not implemented."
    raise NotImplementedError(msg)
