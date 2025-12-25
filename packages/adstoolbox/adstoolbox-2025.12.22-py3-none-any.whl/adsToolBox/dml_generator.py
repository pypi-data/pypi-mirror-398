"""
Module providing database DML (Data Manipulation Language) SQL generators.

This module defines abstract and concrete classes to generate SQL expressions
for manipulating and transforming data, including:

- Converting columns to JSON representations
- Computing hashes (SHA2-256, MD5) for columns or expressions
- Supporting both Microsoft SQL Server and PostgreSQL dialects

The module also provides a factory function to instantiate the appropriate
DML generator class based on the database engine.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import Engine


class DmlGenerator(ABC):
    """Abstract base class for DML Generator."""

    def __init__(self, engine: Engine) -> None:
        """Initialize the DML generator with a SQLAlchemy engine."""
        self.engine = engine

    def quote(self, name: str) -> str:
        """Quote database object names."""
        return self.engine.dialect.identifier_preparer.quote(name)

    @abstractmethod
    def to_json(self, columns:list) -> str:
        """Generate SQL for columns to json conversion."""

    @abstractmethod
    def to_sha2_256(self, string: str) -> str:
        """Generate SQL for SHA2-256 hash."""

    @abstractmethod
    def to_md5(self, string: str) -> str:
        """Generate SQL for MD5 hash."""

class MssqlDmlGenerator(DmlGenerator):
    """Concrete class for MSSQL DML Generator."""

    def to_json(self, columns: list) -> str:
        """Generate SQL for columns to json conversion."""
        columns_expression = ", ".join([f"{col.expression!s} AS {self.quote(col.name)}" for col in columns])
        return f"(SELECT {columns_expression} FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)"

    def to_sha2_256(self, string: str) -> str:
        """Generate SQL for SHA2-256 hash."""
        return f"CONVERT(varchar(64), HASHBYTES('SHA2_256', {string}), 2)"

    def to_md5(self, string: str) -> str:
        """Generate SQL for MD5 hash."""
        return f"CONVERT(varchar(32), HASHBYTES('MD5', {string}), 2)"

class PostgresqlDmlGenerator(DmlGenerator):
    """Concrete class for PostgreSQL DML Generator."""

    def to_json(self, columns: list) -> str:
        """Generate SQL for columns to json conversion."""
        columns_expression = ", ".join([f"{self.quote(col.name)}, {col.expression!s}" for col in columns])
        return f"json_build_object({columns_expression})::text"

    def to_sha2_256(self, string: str) -> str:
        """Generate SQL for SHA2-256 hash."""
        return f"encode(digest({string}, 'sha256'), 'hex')"

    def to_md5(self, string: str) -> str:
        """Generate SQL for MD5 hash."""
        return f"md5({string})"

def create_dml_generator(engine: Engine) -> MssqlDmlGenerator | PostgresqlDmlGenerator:
    """Create the appropriate DML Generator class."""
    dialect = engine.dialect.name
    if dialect == "mssql":
        return MssqlDmlGenerator(engine)
    if dialect == "postgresql":
        return PostgresqlDmlGenerator(engine)
    msg = f"DML Generator for database type '{dialect}' are not implemented."
    raise NotImplementedError(msg)
