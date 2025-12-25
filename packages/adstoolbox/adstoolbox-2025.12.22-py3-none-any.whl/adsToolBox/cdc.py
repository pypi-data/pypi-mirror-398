"""
Module de gestion du Change Data Capture (CDC).

Ce module contient les classes et fonctions nécessaires pour valider,
charger et synchroniser les données entre tables de staging et tables
persistentes selon différents modes (append, scd1, scd2, scd4).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any, ClassVar

import sqlalchemy as sa
from jsonschema import ValidationError, validate
from sqlalchemy import ColumnElement, Connection, Engine, Table, true

from .ddl_operations import create_ddl_operations
from .dml_generator import create_dml_generator
from .timer import timer

if TYPE_CHECKING:
    from sqlalchemy.sql.selectable import Alias, Join, NamedFromClause, Subquery

    from .logger import Logger

class ConfigurationError(ValueError):
    """Custom exception for configuration errors."""


class _Configuration:
    CONFIG_SCHEMA: ClassVar[dict] = {
        "type": "object",
        "properties": {
            "staging_area": {
                "type": "object",
                "properties": {
                    "table": {"$ref": "#/definitions/db_object"},
                    "pk_table": {"$ref": "#/definitions/db_object"},
                    "view": {"$ref": "#/definitions/db_object"},
                    "cdc_table": {"$ref": "#/definitions/db_object"},
                },
                "required": ["table", "view"],
            },
            "persistent_area": {
                "type": "object",
                "properties": {
                    "table": {"$ref": "#/definitions/db_object"},
                    "history_table": {"$ref": "#/definitions/db_object"},
                    "view": {"$ref": "#/definitions/db_object"},
                },
                "required": ["table"],
            },
            "mapping": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "position": {"type": "integer"},
                        "persistent_column": {"type": "string"},
                        "staging_column_or_expression": {"type": "string"},
                        "datatype": {"type": ["string", "null"]},
                        "is_pk": {"type": ["boolean", "null"]},
                        "use_for_cdc": {"type": ["boolean", "null"]},
                    },
                    "required": ["position", "persistent_column", "staging_column_or_expression"],
                },
            },
            "sync": {
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["append", "scd1", "scd2", "scd4"],
                    },
                    "action_on_table": {
                        "type": "object",
                        "properties": {
                            "truncate": {"type": ["boolean", "null"]},
                            "delete_rows": {"type": ["boolean", "null"]},
                            "delete_rows_condition": {"type": ["string", "null"]},
                        },
                        "required": [],
                    },
                    "persistent_table_filter_expression": {"type": ["string", "null"]},
                    "deleted_rows": {
                        "type": "object",
                        "properties": {
                            "ignore": {"type": ["boolean", "null"]},
                            "soft_delete": {"type": ["boolean", "null"]},
                            "use_pk_table": {"type": ["boolean", "null"]},
                        },
                        "required": [],
                    },
                    "technical_columns": {
                        "type": "object",
                        "properties": {
                            "pk_hash": {"$ref": "#/definitions/tech_col"},
                            "row_hash": {"$ref": "#/definitions/tech_col"},
                            "first_change_date": {"$ref": "#/definitions/tech_col"},
                            "last_change_date": {"$ref": "#/definitions/tech_col"},
                            "is_active": {"$ref": "#/definitions/tech_col"},
                        },
                        "required": [],
                    },
                    "distinct_rows": {
                        "type": "boolean",
                        "default": False,
                    },
                    "end_of_time_is_null": {
                        "type": "boolean",
                        "default": False,
                    },
                },
                "required": ["mode"],
            },
        },
        "required": ["staging_area", "persistent_area", "mapping", "sync"],
        "definitions": {
            "db_object": {
                "type": "object",
                "properties": {
                    "schema": {"type": "string"},
                    "name": {"type": "string"},
                },
                "required": ["schema", "name"],
            },
            "tech_col": {
                "type": "object",
                "properties": {
                    "persistent_column": {"type": "string"},
                },
                "required": ["persistent_column"],
            },
        },
    }
    date_exec = datetime.now(timezone.utc)

    def __init__(self, config_json_string: str, logger: Logger) -> None:
        # Attributes initialization
        #    Staging area
        self.staging_table_schema = None
        self.staging_table_name = None
        self.staging_pk_table_schema = None
        self.staging_pk_table_name = None
        self.staging_view_schema = None
        self.staging_view_name = None
        self.staging_cdc_table_schema = None
        self.staging_cdc_table_name = None

        #    Persistent area
        self.persistent_table_schema = None
        self.persistent_table_name = None
        self.persistent_history_table_schema = None
        self.persistent_history_table_name = None
        self.persistent_view_schema = None
        self.persistent_view_name = None

        #    Mapping
        self.business_columns = None
        self.pk_columns = None
        self.cdc_columns = None

        #    Sync Options
        self.sync_mode = None
        self.persistent_table_truncate = None
        self.persistent_table_delete_rows = None
        self.persistent_table_delete_rows_condition = None
        self.persistent_table_filter = None
        self.ignore_deleted_rows = None
        self.soft_delete_rows = None
        self.delete_using_pk_table = None
        self.distinct_rows = None
        self.end_of_time = None

        #    Technical Columns
        self.pk_hash_col = None
        self.row_hash_col = None
        self.first_change_date_col = None
        self.last_change_date_col = None
        self.is_active_col = None

        self.logger = logger

        # Load, validate and parse configuration JSON
        self.config_json = self._load_and_validate_json(config_json_string, self.CONFIG_SCHEMA)
        self._parse_config()
        self._validate_business_rules()

        self.logger.info("Configuration loaded and validated successfully.")

    def _load_and_validate_json(self, config_json_string: str, schema: dict) -> dict[str, Any]:
        try:
            data = json.loads(config_json_string)
            validate(instance=data, schema=schema)
        except json.JSONDecodeError as e:
            msg = f"Invalid ConfigurationJSON: {e}"
            self.logger.error(msg)
            raise ValueError(msg) from e
        except ValidationError as e:
            msg = f"Configuration JSON does not conform to schema: {e}"
            self.logger.error(msg)
            raise ValueError(msg) from e
        return data

    def _parse_config(self) -> None:
        """
        Parse the loaded configuration JSON into a more usable format.

        This method can be expanded to include any additional parsing logic needed.
        """
        # Staging area
        self.staging_table_schema = self.config_json.get("staging_area", {}).get("table", {}).get("schema")
        self.staging_table_name = self.config_json.get("staging_area", {}).get("table", {}).get("name")
        self.staging_pk_table_schema = self.config_json.get("staging_area", {}).get("pk_table", {}).get("schema")
        self.staging_pk_table_name = self.config_json.get("staging_area", {}).get("pk_table", {}).get("name")
        self.staging_view_schema = self.config_json.get("staging_area", {}).get("view", {}).get("schema")
        self.staging_view_name = self.config_json.get("staging_area", {}).get("view", {}).get("name")
        self.staging_cdc_table_schema = self.config_json.get("staging_area", {}).get("cdc_table", {}).get("schema")
        self.staging_cdc_table_name = self.config_json.get("staging_area", {}).get("cdc_table", {}).get("name")

        # Persistent area
        self.persistent_table_schema = self.config_json.get("persistent_area", {}).get("table", {}).get("schema")
        self.persistent_table_name = self.config_json.get("persistent_area", {}).get("table", {}).get("name")
        self.persistent_history_table_schema = self.config_json.get("persistent_area", {}).get("history_table", {}).get(
            "schema")
        self.persistent_history_table_name = self.config_json.get("persistent_area", {}).get("history_table", {}).get(
            "name")
        self.persistent_view_schema = self.config_json.get("persistent_area", {}).get("view", {}).get("schema")
        self.persistent_view_name = self.config_json.get("persistent_area", {}).get("view", {}).get("name")

        # Mapping
        self.business_columns = sorted(self.config_json.get("mapping", {}), key=lambda column: column["position"])
        self.pk_columns = [col for col in self.business_columns if col.get("is_pk", False) is True]
        self.cdc_columns = [col for col in self.business_columns if col.get("use_for_cdc", False) is True]

        # Sync Options
        sync_opts = self.config_json["sync"]
        self.sync_mode = sync_opts.get("mode")
        self.persistent_table_truncate = sync_opts.get("action_on_table", {}).get("truncate", False)
        self.persistent_table_delete_rows = sync_opts.get("action_on_table", {}).get("delete_rows", False)
        self.persistent_table_delete_rows_condition = sync_opts.get("action_on_table", {}).get("delete_rows_condition")
        self.persistent_table_filter = sync_opts.get("persistent_table_filter_expression")
        self.ignore_deleted_rows = sync_opts.get("deleted_rows", {}).get("ignore", False)
        self.soft_delete_rows = sync_opts.get("deleted_rows", {}).get("soft_delete", False)
        self.delete_using_pk_table = sync_opts.get("deleted_rows", {}).get("use_pk_table", False)
        self.distinct_rows = sync_opts.get("distinct_rows", False)
        self.end_of_time = (
                datetime.strptime("9999-12-31 23:59:59", "%Y-%m-%d %H:%M:%S")
                .replace(tzinfo=timezone.utc)
        ) if not sync_opts.get("end_of_time_is_null", False) else None

        # Technical Columns
        tech_cols = sync_opts.get("technical_columns", {})
        self.pk_hash_col = tech_cols.get("pk_hash", {}).get("persistent_column")
        self.row_hash_col = tech_cols.get("row_hash", {}).get("persistent_column")
        self.first_change_date_col = tech_cols.get("first_change_date", {}).get("persistent_column")
        self.last_change_date_col = tech_cols.get("last_change_date", {}).get("persistent_column")
        self.is_active_col = tech_cols.get("is_active", {}).get("persistent_column")

    def _validate_business_rules(self) -> None:
        """Perform logical validation based on sync mode and options."""
        generic_rules = [
            (self.pk_hash_col and not self.pk_columns,
             "pk_hash column requires at least one mapping column marked as 'is_pk: true'"),
            (self.row_hash_col and not self.cdc_columns,
             "row_hash column requires at least one mapping column marked as 'use_for_cdc: true'"),
            (self.row_hash_col and not self.pk_hash_col,
             "row_hash column requires pk_hash column to be defined"),
        ]
        for condition, message in generic_rules:
            if condition:
                raise ConfigurationError(message)

        if not self.ignore_deleted_rows and self.delete_using_pk_table:
            missing = []
            if not self.staging_pk_table_name:
                missing.append("staging_area.pk_table")
            if not self.pk_hash_col:
                missing.append("technical_columns.pk_hash")
            if missing:
                msg = f"use_pk_table: true' requires {', '.join(missing)} to be defined"
                raise ConfigurationError(msg)
        mode_validators = {
            "append": self._validate_append_mode,
            "scd1": self._validate_scd1_mode,
            "scd2": self._validate_scd2_mode,
            "scd4": self._validate_scd4_mode,
        }
        validator = mode_validators.get(self.sync_mode)
        if validator:
            validator()
        else:
            msg = f"Invalid sync_mode: {self.sync_mode}"
            raise ConfigurationError(msg)

    # --- Mode Specific Validation Helpers ---
    def _validate_append_mode(self) -> None:
        """Validate configuration consistency for append mode."""
        conditional_warnings = [
            (
                self.persistent_table_delete_rows and not self.persistent_table_delete_rows_condition,
                "'delete_rows' is true but no condition specified. ALL rows will be deleted.",
            ),
            (
                not self.persistent_table_truncate and not self.persistent_table_delete_rows,
                "No rows will be deleted. Data will be appended to the existing table.",
            ),
            (
                self.persistent_table_truncate and self.persistent_table_delete_rows,
                "'truncate' and 'delete_rows' are both set. Only 'truncate' will be applied.",
            ),
            (
                not self.persistent_table_delete_rows and self.persistent_table_delete_rows_condition,
                "'delete_rows_condition' is set but 'delete_rows' is false. Condition will be ignored.",
            ),
        ]
        unused_items = [
            (self.staging_pk_table_name, "staging_area.pk_table is not used in Append mode"),
            (self.staging_cdc_table_name, "staging_area.cdc_table is not used in Append mode"),
            (self.persistent_history_table_name, "persistent_area.history_table is not used in Append mode"),
            (self.row_hash_col, "row_hash column is not used in Append mode"),
            (self.first_change_date_col, "first_change_date column is not used in Append mode"),
            (self.last_change_date_col, "last_change_date column is not used in Append mode"),
            (self.is_active_col, "is_active column is not used in Append mode"),
            (self.ignore_deleted_rows, "ignore_deleted_rows is not used in Append mode"),
            (self.soft_delete_rows, "soft_delete_rows is not used in Append mode"),
            (self.delete_using_pk_table, "delete_using_pk_table is not used in Append mode"),
        ]
        for condition, message in conditional_warnings + unused_items:
            if condition:
                self.logger.warning(f"Append Mode: {message}")

    def _validate_scd1_mode(self) -> None:
        # Errors
        required_fields = {
            "staging_cdc_table_name": "staging_area.cdc_table",
            "pk_hash_col": "technical_columns.pk_hash",
            "row_hash_col": "technical_columns.row_hash",
        }
        if self.soft_delete_rows and not self.ignore_deleted_rows:
            required_fields["is_active_col"] = "technical_columns.is_active"
        for attr, desc in required_fields.items():
            if not getattr(self, attr):
                msg = f"SCD1 mode requires {desc}"
                raise ConfigurationError(msg)

        # Warnings
        warnings = [
            (self.persistent_history_table_name, "persistent_area.history_table is not used in SCD1 mode."),
            (self.ignore_deleted_rows and not self.soft_delete_rows and self.is_active_col,
             "is_active is not used in hard-delete mode"),
            (not self.persistent_table_filter, "No filter on persistent_table. All rows will be considered in the CDC."),
            (self.persistent_table_truncate, "'truncate' is not used in SCD1 mode."),
            (self.persistent_table_delete_rows, "'delete_rows' is not used in SCD1 mode."),
        ]
        for cond, message in warnings:
            if cond:
                msg = f"SCD1 Mode: {message}"
                self.logger.warning(msg)

    def _validate_scd2_mode(self) -> None:
        """Validate configuration consistency for SCD2 mode."""
        required_fields = {
            "staging_cdc_table_name": "staging_area.cdc_table",
            "pk_hash_col": "technical_columns.pk_hash",
            "row_hash_col": "technical_columns.row_hash",
            "is_active_col": "technical_columns.is_active",
            "first_change_date_col": "technical_columns.first_change_date",
            "last_change_date_col": "technical_columns.last_change_date",
        }
        for attr, desc in required_fields.items():
            if not getattr(self, attr):
                msg = f"SCD2 mode requires {desc}"
                raise ConfigurationError(msg)

        warnings = [
            (self.persistent_history_table_name, "persistent_history_table is not used in SCD2 mode."),
            (
            not self.persistent_table_filter, "No filter on persistent_table. All rows will be considered in the CDC."),
            (self.persistent_table_truncate, "'truncate' is not used in SCD2 mode."),
            (self.persistent_table_delete_rows, "'delete_rows' is not used in SCD2 mode."),
        ]
        for condition, message in warnings:
            if condition:
                msg = f"SCD2 Mode: {message}"
                self.logger.warning(msg)

    def _validate_scd4_mode(self) -> None:
        # Errors
        required_attrs = [
            ("staging_cdc_table_name", "SCD4 mode requires staging_area.cdc_table"),
            ("persistent_history_table_name", "SCD4 mode requires persistent_area.history_table"),
            ("pk_hash_col", "SCD4 mode requires technical_columns.pk_hash"),
            ("row_hash_col", "SCD4 mode requires technical_columns.row_hash"),
            ("first_change_date_col", "SCD4 mode requires technical_columns.first_change_date"),
            ("last_change_date_col", "SCD4 mode requires technical_columns.last_change_date"),
        ]
        for attr_name, msg in required_attrs:
            if not getattr(self, attr_name):
                raise ConfigurationError(msg)


class _Metadata:
    # Datatype SA colonnes techniques
    pk_hash_satype = sa.CHAR(64)
    row_hash_satype = sa.CHAR(32)
    first_change_date_satype = sa.DateTime()
    last_change_date_satype = sa.DateTime()
    is_active_satype = sa.Boolean()

    def __init__(self, config: _Configuration, engine: Engine) -> None:
        self.metadata = sa.MetaData()

        # Techical columns
        self.pk_hash_col = sa.Column(config.pk_hash_col, self.pk_hash_satype)
        self.row_hash_col = sa.Column(config.row_hash_col, self.row_hash_satype)
        self.first_change_date_col = sa.Column(config.first_change_date_col, self.first_change_date_satype)
        self.last_change_date_col = sa.Column(config.last_change_date_col, self.last_change_date_satype)
        self.is_active_col = sa.Column(config.is_active_col, self.is_active_satype)

        # staging_table
        self.staging_table = sa.Table(
            config.staging_table_name,
            self.metadata,
            schema=config.staging_table_schema,
            autoload_with=engine,
        )

        # staging_pk_table
        if config.staging_pk_table_name:
            self.staging_pk_table = sa.Table(
                config.staging_pk_table_name,
                self.metadata,
                schema=config.staging_pk_table_schema,
                autoload_with=engine,
            )
        else:
            self.staging_pk_table = None

        # staging_view
        self.staging_view = sa.Table(
            config.staging_view_name,
            self.metadata,
            schema=config.staging_view_schema,
        )

        # persistent_table
        self.persistent_table = sa.Table(
            config.persistent_table_name,
            self.metadata,
            schema=config.persistent_table_schema,
        )

        # persistent_history_table
        if config.persistent_history_table_name:
            self.persistent_history_table = sa.Table(
                config.persistent_history_table_name,
                self.metadata,
                schema=config.persistent_history_table_schema,
            )
        else:
            self.persistent_history_table = None

        # persistent_view
        if config.persistent_view_name:
            self.persistent_view = sa.Table(
                config.persistent_view_name,
                self.metadata,
                schema=config.persistent_view_schema,
            )
        else:
            self.persistent_view = None

        # staging_cdc_table
        if config.staging_cdc_table_name:
            self.staging_cdc_table = sa.Table(
                config.staging_cdc_table_name,
                self.metadata,
                schema=config.staging_cdc_table_schema,
            )
        else:
            self.staging_cdc_table = None


class _SchemaManager:
    def __init__(self, config: _Configuration, engine: Engine, meta: _Metadata, logger: Logger) -> None:
        self.config = config
        self.meta = meta
        self.logger = logger
        self.ddl = create_ddl_operations(engine, self.logger)
        self.engine = engine

    def alter_staging_table(self) -> None:
        # Adding the pk_hash column to the staging table
        if self.config.pk_hash_col:
            pk_hash_col = self.meta.pk_hash_col
            self.ddl.add_column(self.meta.staging_table, pk_hash_col.copy())

        # Adding the row_hash column to the staging table
        if self.config.row_hash_col:
            row_hash_col = self.meta.row_hash_col
            self.ddl.add_column(self.meta.staging_table, row_hash_col.copy())

        # Adding the pk_hash column to the staging_pk_table
        if not self.config.ignore_deleted_rows and self.config.delete_using_pk_table:
            pk_hash_col = self.meta.pk_hash_col
            self.ddl.add_column(self.meta.staging_pk_table, pk_hash_col.copy())

    def create_staging_view(self) -> None:
        # Generate the columns for the view based on the mapping configuration
        columns = [
            sa.literal_column(f"CAST({column['staging_column_or_expression']} AS {column['datatype']})").label(
                column["persistent_column"])
            if column.get("datatype") else
            sa.literal_column(column["staging_column_or_expression"]).label(column["persistent_column"])
            for column in self.config.business_columns
        ]

        # Add technical columns to the view if they are defined in the config
        if self.config.pk_hash_col:
            columns.append(self.meta.pk_hash_col.label(self.config.pk_hash_col))
        if self.config.row_hash_col:
            columns.append(self.meta.row_hash_col.label(self.config.row_hash_col))

        # Generate the view definition
        if self.config.distinct_rows:
            definition = sa.select(*columns).select_from(self.meta.staging_table).distinct()
        else:
            definition = sa.select(*columns).select_from(self.meta.staging_table)
        self.ddl.create_view(self.meta.staging_view, definition, or_replace=True)

    def add_missing_datatypes(self) -> None:
        """
        Add missing datatypes to the business_columns, pk_columns, and cdc_columns.

        This is necessary for the hash computation in the _compute_hashes method.
        """

        def add_missing_datatype(columns: list[dict[str, Any]]) -> None:
            for column in columns:
                if column.get("datatype") is None:
                    staging_view_column = self.meta.staging_view.c[column["persistent_column"]].copy()
                    # If the datatype is a string, remove collation
                    if isinstance(staging_view_column.type, sa.String):
                        staging_view_column.type.collation = None
                    column["datatype"] = staging_view_column.type.compile(self.ddl.engine.dialect)
                    self.logger.debug(f"Found datatype for column {column['persistent_column']} : {column['datatype']}.")

        add_missing_datatype(self.config.business_columns)
        add_missing_datatype(self.config.pk_columns)
        add_missing_datatype(self.config.cdc_columns)

    def index_staging_table(self) -> None:
        # Create indexes on staging table
        if self.config.pk_hash_col:
            self.ddl.create_index(self.meta.staging_table, [self.config.pk_hash_col],
                                  f"ix_{self.config.staging_table_schema}_{self.config.staging_table_name}_pk_hash",
                                  unique=True)
        if self.config.row_hash_col:
            self.ddl.create_index(self.meta.staging_table, [self.config.pk_hash_col, self.config.row_hash_col],
                                  f"ix_{self.config.staging_table_schema}_{self.config.staging_table_name}_cdc",
                                  unique=True)
        # Create indexes on staging pk table
        if not self.config.ignore_deleted_rows and self.config.delete_using_pk_table:
            self.ddl.create_index(self.meta.staging_pk_table, [self.config.pk_hash_col],
                                  f"ix_{self.config.staging_pk_table_schema}_{self.config.staging_pk_table_name}_pk_hash",
                                  unique=True)

    def drop_and_create_cdc_table(self) -> None:
        # Create the cdc table if it doesn't exist
        if self.config.sync_mode == "append":
            self.logger.warning("CDC table is not used in Append mode. Skipping creation.")
            return

        # Drop the cdc table if it exists
        self.ddl.drop_table(self.meta.staging_cdc_table)

        # Add the technical columns to the cdc table
        pk_hash_col = self.meta.pk_hash_col
        self.meta.staging_cdc_table.append_column(pk_hash_col.copy())
        if self.config.sync_mode == "scd1":
            first_change_date_col = self.meta.first_change_date_col
            self.meta.staging_cdc_table.append_column(first_change_date_col.copy())
        self.meta.staging_cdc_table.append_column(sa.Column("operation", sa.String(1)))

        self.ddl.create_table(self.meta.staging_cdc_table)

    def create_persistent_table(self) -> None:
        def create_persistent_table(table: Table) -> None:
            # Add the technical columns to the persistent table
            if self.config.pk_hash_col:
                pk_hash_col = self.meta.pk_hash_col
                table.append_column(pk_hash_col.copy())
            if self.config.row_hash_col:
                row_hash_col = self.meta.row_hash_col
                table.append_column(row_hash_col.copy())
            if self.config.first_change_date_col:
                first_change_date_col = self.meta.first_change_date_col
                table.append_column(first_change_date_col.copy())
            if self.config.last_change_date_col:
                last_change_date_col = self.meta.last_change_date_col
                table.append_column(last_change_date_col.copy())
            if self.config.is_active_col:
                is_active_col = self.meta.is_active_col
                table.append_column(is_active_col.copy())

            # Add the business columns to the persistent table
            for column in self.config.business_columns:
                # Get column name and datatype from staging view definition
                business_column = self.meta.staging_view.c[column["persistent_column"]]
                # Add the column to the persistent table
                table.append_column(business_column.copy())

            self.ddl.create_table(table)

        # Create the persistent table and history table if they don't exist
        create_persistent_table(self.meta.persistent_table)
        if self.config.persistent_history_table_name:
            create_persistent_table(self.meta.persistent_history_table)

    def index_persistent_table(self) -> None:
        # Create indexes on persistent table
        indexed_columns = []
        if self.config.pk_hash_col:
            indexed_columns.append(self.config.pk_hash_col)
        if self.config.row_hash_col:
            indexed_columns.append(self.config.row_hash_col)
        if self.config.is_active_col:
            indexed_columns.append(self.config.is_active_col)

        if indexed_columns:
            self.ddl.create_index(self.meta.persistent_table, indexed_columns,
                                  f"ix_{self.config.persistent_table_schema}_{self.config.persistent_table_name}_cdc",
                                  unique=False)

    def create_persistent_view(self) -> None:
        if not self.config.persistent_view_name:
            return  # Persistent view not defined

        # Generate the columns for the view based on the mapping configuration
        columns = [
            sa.literal_column(f"{column['persistent_column']}").label(column["persistent_column"])
            for column in self.config.business_columns
        ]

        # Generate the view definition
        if self.config.is_active_col:
            definition = sa.select(*columns).select_from(self.meta.persistent_table).where(
                self.meta.persistent_table.c[self.config.is_active_col] == true())
        else:
            definition = sa.select(*columns).select_from(self.meta.persistent_table)
        self.ddl.create_view(self.meta.persistent_view, definition, or_replace=True)


class _DataManager:
    def __init__(self, config: _Configuration, engine: Engine, meta: _Metadata, logger: Logger) -> None:
        self.config = config
        self.engine = engine
        self.meta = meta
        self.logger = logger
        self.ddl = create_ddl_operations(engine, self.logger)
        self.dml = create_dml_generator(engine)

    def _check_hash_computed(self, table: Table, hash_column: str) -> bool:
        # Check if a hash column is already computed in a table by checking for null values
        hash_null_exists = sa.select(true()).where(
            sa.select(true()).select_from(table).where(sa.literal_column(hash_column).is_(None)).exists(),
        )
        with self.engine.begin() as connection:
            hash_has_null = connection.execute(hash_null_exists).scalar()
        if not hash_has_null:
            self.logger.warning(
                f"{hash_column} already computed on table {table.schema}.{table.name}. No need to compute again.")
            return True
        return False

    def _columns_to_json(self, columns: list[dict[str, str]]) -> str:
        # Generate json to hash from the columns
        col_list = [
            sa.literal_column(f"CAST({column['staging_column_or_expression']} AS {column['datatype']})").label(
                column["persistent_column"]) for column in columns]
        return self.dml.to_json(col_list)

    def _update_staging_tables(self) -> tuple[dict[str, ColumnElement], dict[str, ColumnElement]]:
        # Update the staging table with the computed hashes
        # Check if the hash columns are already computed in the staging table
        # If not, compute them and update the table
        # If the hash columns are already computed, skip the computation
        update_values = {}
        if self.config.pk_hash_col and not self._check_hash_computed(self.meta.staging_table, self.config.pk_hash_col):
            json_pk_columns = self._columns_to_json(self.config.pk_columns)
            pk_hash_expr = self.dml.to_sha2_256(json_pk_columns)
            update_values[self.config.pk_hash_col] = sa.literal_column(pk_hash_expr)

        if self.config.row_hash_col and not self._check_hash_computed(self.meta.staging_table, self.config.row_hash_col):
            json_cdc_columns = self._columns_to_json(self.config.cdc_columns)
            row_hash_expr = self.dml.to_md5(json_cdc_columns)
            update_values[self.config.row_hash_col] = sa.literal_column(row_hash_expr)

        # Idem for staging pk table
        update_values_pk_table = {}
        if (
            not self.config.ignore_deleted_rows
            and self.config.delete_using_pk_table
            and self.config.pk_hash_col
            and not self._check_hash_computed(self.meta.staging_pk_table, self.config.pk_hash_col)
        ):
            # Check if hashes are already computed in the pk_table
            json_pk_columns = self._columns_to_json(self.config.pk_columns)
            pk_hash_expr = self.dml.to_sha2_256(json_pk_columns)
            update_values_pk_table[self.config.pk_hash_col] = sa.literal_column(pk_hash_expr)

        return update_values, update_values_pk_table

    def compute_hashes(self) -> None:
        # Compute the hashes for the staging table

        update_values, update_values_pk_table = self._update_staging_tables()

        # Run the update statements
        with self.engine.begin() as connection:
            if update_values:
                update_stmt = self.meta.staging_table.update().values(update_values)
                self.logger.debug(f"Compute staging table hashes statement: {update_stmt}")
                connection.execute(update_stmt)
                self.logger.info(
                    f"Computed hashes {', '.join(update_values.keys())} in staging table {self.meta.staging_table.schema}.{self.meta.staging_table.name}.")
            if update_values_pk_table:
                update_stmt = self.meta.staging_pk_table.update().values(update_values_pk_table)
                self.logger.debug(f"Compute staging pk table hashes statement: {update_stmt}")
                connection.execute(update_stmt)
                self.logger.info(
                    f"Computed hashes {', '.join(update_values_pk_table.keys())} in staging table {self.meta.staging_pk_table.schema}.{self.meta.staging_pk_table.name}.")

    def _build_persistent_table_subquery(self) -> Subquery:
        # Persistent table subquery
        per = self.meta.persistent_table
        per_subquery_where = []
        if self.config.persistent_table_filter:
            per_subquery_where.append(sa.text(self.config.persistent_table_filter))
        if self.config.is_active_col:
            per_subquery_where.append(per.c[self.config.is_active_col])
        per_subquery_select = [per.c[self.config.pk_hash_col], per.c[self.config.row_hash_col]]
        if self.config.sync_mode == "scd1":
            per_subquery_select.append(per.c[self.config.first_change_date_col])
        return sa.select(*per_subquery_select).where(sa.and_(*per_subquery_where)).subquery()

    def _build_from_clause(self, s: NamedFromClause, p: NamedFromClause, s_pk: Alias | None) -> Join:
        # From clause
        from_clause = sa.join(s, p, s.c[self.config.pk_hash_col] == p.c[self.config.pk_hash_col], full=True)
        if not self.config.ignore_deleted_rows and self.config.delete_using_pk_table:
            from_clause = sa.outerjoin(from_clause, s_pk,
                                       p.c[self.config.pk_hash_col] == s_pk.c[self.config.pk_hash_col])
        return from_clause

    def _build_where_conditions(self, s: NamedFromClause, p: NamedFromClause, s_pk: Alias | None) -> ColumnElement:
        # Where clause
        where_conditions = []
        if not self.config.ignore_deleted_rows and not self.config.delete_using_pk_table:
            where_conditions.append(s.c[self.config.pk_hash_col].is_(None))
        where_conditions.append(p.c[self.config.pk_hash_col].is_(None))
        where_conditions.append(s.c[self.config.row_hash_col] != p.c[self.config.row_hash_col])
        if not self.config.ignore_deleted_rows and self.config.delete_using_pk_table:
            where_conditions.append(s_pk.c[self.config.pk_hash_col].is_(None))
        return sa.or_(*where_conditions)

    def _build_select_clause(self, s: NamedFromClause, p: NamedFromClause, s_pk: Alias | None) -> list[ColumnElement]:
        # Select clause
        col_operation_rules = []
        if not self.config.ignore_deleted_rows and not self.config.delete_using_pk_table:
            col_operation_rules.append((s.c[self.config.pk_hash_col].is_(None), "D"))
        col_operation_rules.append((p.c[self.config.pk_hash_col].is_(None), "I"))
        col_operation_rules.append((s.c[self.config.row_hash_col] != p.c[self.config.row_hash_col], "U"))
        if not self.config.ignore_deleted_rows and self.config.delete_using_pk_table:
            col_operation_rules.append((s_pk.c[self.config.pk_hash_col].is_(None), "D"))
        selected_columns = [
            sa.func.coalesce(s.c[self.config.pk_hash_col], p.c[self.config.pk_hash_col]).label(self.config.pk_hash_col)]
        if self.config.sync_mode == "scd1":
            selected_columns.append(
                sa.func.coalesce(p.c[self.config.first_change_date_col], self.config.date_exec).label(
                    self.config.first_change_date_col))
        selected_columns.append(sa.case(*col_operation_rules).label("operation"))
        return selected_columns

    def capture_data_change(self) -> None:
        # Capture data changes from the staging table to the persistent table
        if self.config.sync_mode == "append":
            return  # Append mode does not require data capture

        sta = self.meta.staging_table

        per_subquery = self._build_persistent_table_subquery()

        # Tables aliases
        p = sa.alias(per_subquery, name="p")
        s = sa.alias(sta, name="s")
        s_pk = sa.alias(self.meta.staging_pk_table, name="s_pk") if self.config.staging_pk_table_name else None

        from_clause = self._build_from_clause(s, p, s_pk)
        where_clause = self._build_where_conditions(s, p, s_pk)
        selected_columns = self._build_select_clause(s, p, s_pk)

        # Select statement
        select_stmt = sa.select(*selected_columns).select_from(from_clause).where(where_clause)

        # Insert columns
        insert_columns = []
        insert_columns.append(self.config.pk_hash_col)
        if self.config.sync_mode == "scd1":
            insert_columns.append(self.config.first_change_date_col)
        insert_columns.append("operation")

        # Insert statement
        insert_stmt = self.meta.staging_cdc_table.insert().from_select([*insert_columns], select_stmt)

        try:
            with self.engine.begin() as connection:
                # Insert into the cdc table
                self.logger.debug(f"CDC statement: {insert_stmt}")
                connection.execute(insert_stmt)
                self.logger.info(
                    f"Inserted data into cdc table {self.meta.staging_cdc_table.schema}.{self.meta.staging_cdc_table.name}.")
        except Exception as e:
            self.logger.error(f"An error occurred during the data change capture: {e}")
            raise

    def _append(self) -> None:

        per = self.meta.persistent_table
        v_sta = self.meta.staging_view

        insert_columns = []
        select_columns = []
        # Add technical columns to the insert and select statements
        if self.config.pk_hash_col:
            insert_columns.append(per.c[self.config.pk_hash_col])
            select_columns.append(v_sta.c[self.config.pk_hash_col])
        if self.config.row_hash_col:
            insert_columns.append(per.c[self.config.row_hash_col])
            select_columns.append(v_sta.c[self.config.row_hash_col])
        if self.config.first_change_date_col:
            insert_columns.append(per.c[self.config.first_change_date_col])
            select_columns.append(sa.literal(self.config.date_exec).label(self.config.first_change_date_col))
        if self.config.last_change_date_col:
            insert_columns.append(per.c[self.config.last_change_date_col])
            select_columns.append(sa.literal(self.config.date_exec).label(self.config.last_change_date_col))
        if self.config.is_active_col:
            insert_columns.append(per.c[self.config.is_active_col])
            select_columns.append(
                sa.literal("1").label(self.config.is_active_col))  # Default value for is_active column
        # Add business columns to the insert and select statements
        for column in self.config.business_columns:
            insert_columns.append(per.c[column["persistent_column"]])
            select_columns.append(v_sta.c[column["persistent_column"]])

        # Select statement
        select_stmt = sa.select(*select_columns).select_from(self.meta.staging_view)
        self.logger.debug(f"Append SELECT statement: {select_stmt}")

        # Insert statement
        insert_stmt = self.meta.persistent_table.insert().from_select([*insert_columns], select_stmt)

        try:
            with self.engine.begin() as connection:
                # Truncate the persistent table if specified
                if self.config.persistent_table_truncate:
                    self.ddl.truncate_table(self.meta.persistent_table)
                # Delete rows from the persistent table if specified
                if self.config.persistent_table_delete_rows:
                    delete_stmt = self.meta.persistent_table.delete().where(
                        sa.text(self.config.persistent_table_delete_rows_condition or "1=1"))
                    # If no condition is specified, delete all rows
                    self.logger.debug(f"Append DELETE statement: {delete_stmt}")
                    connection.execute(delete_stmt)
                    self.logger.info(
                        f"Deleted rows from persistent table {self.meta.persistent_table.schema}.{self.meta.persistent_table.name} with condition: {self.config.persistent_table_delete_rows_condition}.")
                # Insert into the persistent table
                self.logger.debug(f"Append INSERT statement: {insert_stmt}")
                connection.execute(insert_stmt)
                self.logger.info(
                    f"Data loaded into persistent table {self.meta.persistent_table.schema}.{self.meta.persistent_table.name}.")
        except Exception as e:
            self.logger.error(f"An error occurred during the append operation: {e}")
            raise

    def _scd(self) -> None: # noqa: C901, PLR0915
        def hard_delete(connection: Connection, table: Table, operations: list[str])  -> None:
            # Perform a physical delete on the persistent table based on the change types
            hard_delete_stmt = table.delete().where(
                sa.select(true()).select_from(self.meta.staging_cdc_table).where(
                    sa.and_(
                        sa.literal_column("operation").in_(operations),
                        sa.literal_column(self.config.pk_hash_col) == table.c[self.config.pk_hash_col],
                    ),
                ).exists(),
            )
            self.logger.debug(f"SCD HARD DELETE statement: {hard_delete_stmt}")
            connection.execute(hard_delete_stmt)

        def soft_delete(
            connection: Connection,
            table: Table,
            operations: list[str],
            last_change_date: datetime | date,
        ) -> None:
            # Perform a soft delete on the persistent table based on the change types
            where_conditions = []
            where_conditions.append(sa.literal_column("operation").in_(operations))
            where_conditions.append(sa.literal_column(self.config.pk_hash_col) == table.c[self.config.pk_hash_col])
            if self.config.is_active_col:
                where_conditions.append(table.c[self.config.is_active_col])

            soft_delete_stmt = table.update().values(
                {self.config.is_active_col: 0, self.config.last_change_date_col: last_change_date}).where(
                sa.select(true()).select_from(self.meta.staging_cdc_table).where(
                    sa.and_(*where_conditions),
                ).exists(),
            )
            self.logger.debug(f"SCD SOFT DELETE statement: {soft_delete_stmt}")
            connection.execute(soft_delete_stmt)

        def insert(
                connection: Connection,
                destination_table: Table,
                source_table: Table,
                cdc_table: NamedFromClause,
                operations: list[str],
                insert_columns: list[ColumnElement],
                select_columns: list[ColumnElement],
        ) -> None:
            # Insert new rows into the persistent table
            select_stmt = sa.select(*select_columns).select_from(sa.join(cdc_table, source_table,
                                                                         cdc_table.c[self.config.pk_hash_col] ==
                                                                         source_table.c[
                                                                             self.config.pk_hash_col])).where(
                cdc_table.c["operation"].in_(operations))

            insert_stmt = destination_table.insert().from_select([*insert_columns], select_stmt)
            self.logger.debug(f"SCD INSERT statement: {insert_stmt}")
            connection.execute(insert_stmt)

        def scd1(connection: Connection) -> None:
            # Perform SCD1 operation

            # Soft delete rows in persistent table
            # Operations :
            # D : Deleted rows -> in soft delete mode
            operations = ["D"]
            if not self.config.ignore_deleted_rows and self.config.soft_delete_rows:
                soft_delete(connection, self.meta.persistent_table, operations, self.config.date_exec)

            # Hard delete rows in persistent table
            # Operations :
            # D : Deleted rows -> in hard delete mode
            # U : Updated rows -> update is done by deleting the old row and inserting a new one
            # I : Inserted rows -> hard delete previously soft deleted rows
            operations = ["I", "U"]
            if not self.config.ignore_deleted_rows and not self.config.soft_delete_rows:
                operations.append("D")
            hard_delete(connection, self.meta.persistent_table, operations)

            # Insert new rows into the persistent table
            # Operations :
            # I : Inserted rows -> insert new rows
            # U : Updated rows -> update is done by deleting the old row and inserting a new one
            operations = ["I", "U"]
            per = self.meta.persistent_table
            v_sta = self.meta.staging_view
            cdc = sa.alias(self.meta.staging_cdc_table, name="cdc")

            insert_columns = []
            select_columns = []
            # Add technical columns to the insert and select statements
            if self.config.pk_hash_col:
                insert_columns.append(per.c[self.config.pk_hash_col])
                select_columns.append(v_sta.c[self.config.pk_hash_col])
            if self.config.row_hash_col:
                insert_columns.append(per.c[self.config.row_hash_col])
                select_columns.append(v_sta.c[self.config.row_hash_col])
            if self.config.first_change_date_col:
                insert_columns.append(per.c[self.config.first_change_date_col])
                select_columns.append(cdc.c[self.config.first_change_date_col])
            if self.config.last_change_date_col:
                insert_columns.append(per.c[self.config.last_change_date_col])
                select_columns.append(sa.literal(self.config.date_exec).label(self.config.last_change_date_col))
            if self.config.is_active_col:
                insert_columns.append(per.c[self.config.is_active_col])
                select_columns.append(
                    sa.literal("1").label(self.config.is_active_col))  # Default value for is_active column
            # Add business columns to the insert and select statements
            for column in self.config.business_columns:
                insert_columns.append(per.c[column["persistent_column"]])
                select_columns.append(v_sta.c[column["persistent_column"]])

            insert(connection, per, v_sta, cdc, operations, insert_columns, select_columns)

        def scd2(connection: Connection) -> None:
            # Perform SCD2 operation

            # Hard delete rows in persistent table
            # Operations :
            # D : Deleted rows -> in hard delete mode
            operations = ["D"]
            if not self.config.ignore_deleted_rows and not self.config.soft_delete_rows:
                hard_delete(connection, self.meta.persistent_table, operations)

            # Soft delete rows in persistent table
            # Operations :
            # D : Deleted rows -> in soft delete mode
            # U : Updated rows -> update is done by soft deleting the old row and inserting a new one
            operations = ["U"]
            if not self.config.ignore_deleted_rows and self.config.soft_delete_rows:
                operations.append("D")
            soft_delete(connection, self.meta.persistent_table, operations, self.config.date_exec)

            # Insert new rows into the persistent table
            # Operations :
            # I : Inserted rows -> insert new rows
            # U : Updated rows -> update is done by deleting the old row and inserting a new one
            operations = ["I", "U"]
            per = self.meta.persistent_table
            v_sta = self.meta.staging_view
            cdc = sa.alias(self.meta.staging_cdc_table, name="cdc")

            insert_columns = []
            select_columns = []
            # Add technical columns to the insert and select statements
            if self.config.pk_hash_col:
                insert_columns.append(per.c[self.config.pk_hash_col])
                select_columns.append(v_sta.c[self.config.pk_hash_col])
            if self.config.row_hash_col:
                insert_columns.append(per.c[self.config.row_hash_col])
                select_columns.append(v_sta.c[self.config.row_hash_col])
            if self.config.first_change_date_col:
                insert_columns.append(per.c[self.config.first_change_date_col])
                select_columns.append(sa.literal(self.config.date_exec).label(self.config.first_change_date_col))
            if self.config.last_change_date_col:
                insert_columns.append(per.c[self.config.last_change_date_col])
                select_columns.append(sa.literal(self.config.end_of_time).label(self.config.last_change_date_col))
            if self.config.is_active_col:
                insert_columns.append(per.c[self.config.is_active_col])
                select_columns.append(
                    sa.literal("1").label(self.config.is_active_col))  # Default value for is_active column
            # Add business columns to the insert and select statements
            for column in self.config.business_columns:
                insert_columns.append(per.c[column["persistent_column"]])
                select_columns.append(v_sta.c[column["persistent_column"]])

            insert(connection, per, v_sta, cdc, operations, insert_columns, select_columns)

        def _hard_delete_rows() -> None:
            # Hard delete rows in persistent table and persistent history table
            # Operations :
            # D : Deleted rows -> in hard delete mode
            operations = ["D"]
            if not self.config.ignore_deleted_rows and not self.config.soft_delete_rows:
                hard_delete(connection, self.meta.persistent_table, operations)
                hard_delete(connection, self.meta.persistent_history_table, operations)

        def _archive_rows(per: Table, cdc: NamedFromClause) -> None:
            # Archive rows from persistent table to persistent history table
            # Operations :
            # D : Deleted rows -> in soft delete mode
            # U : Updated rows -> update is done by archiving the old row and inserting a new one
            operations = ["U"]
            if not self.config.ignore_deleted_rows and self.config.soft_delete_rows:
                operations.append("D")

            per_h = self.meta.persistent_history_table

            insert_columns = []
            select_columns = []
            # Add technical columns to the insert and select statements
            if self.config.pk_hash_col:
                insert_columns.append(per_h.c[self.config.pk_hash_col])
                select_columns.append(per.c[self.config.pk_hash_col])
            if self.config.row_hash_col:
                insert_columns.append(per_h.c[self.config.row_hash_col])
                select_columns.append(per.c[self.config.row_hash_col])
            if self.config.first_change_date_col:
                insert_columns.append(per_h.c[self.config.first_change_date_col])
                select_columns.append(per.c[self.config.first_change_date_col])
            if self.config.last_change_date_col:
                insert_columns.append(per_h.c[self.config.last_change_date_col])
                select_columns.append(sa.literal(self.config.date_exec).label(self.config.last_change_date_col))
            if self.config.is_active_col:
                insert_columns.append(per_h.c[self.config.is_active_col])
                select_columns.append(sa.literal("0").label(self.config.is_active_col))
            # Add business columns to the insert and select statements
            for column in self.config.business_columns:
                insert_columns.append(per_h.c[column["persistent_column"]])
                select_columns.append(per.c[column["persistent_column"]])

            insert(connection, per_h, per, cdc, operations, insert_columns, select_columns)
            # Hard delete archived rows from persistent table
            hard_delete(connection, self.meta.persistent_table, operations)

        def _insert_new_rows(per: Table, v_sta: Table, cdc: NamedFromClause) -> None:
            # Insert new rows into the persistent table
            # Operations :
            # I : Inserted rows -> insert new rows
            # U : Updated rows -> update is done by archiving the old row and inserting a new one
            operations = ["I", "U"]
            insert_columns, select_columns = [], []
            # Add technical columns to the insert and select statements
            if self.config.pk_hash_col:
                insert_columns.append(per.c[self.config.pk_hash_col])
                select_columns.append(v_sta.c[self.config.pk_hash_col])
            if self.config.row_hash_col:
                insert_columns.append(per.c[self.config.row_hash_col])
                select_columns.append(v_sta.c[self.config.row_hash_col])
            if self.config.first_change_date_col:
                insert_columns.append(per.c[self.config.first_change_date_col])
                select_columns.append(sa.literal(self.config.date_exec).label(self.config.first_change_date_col))
            if self.config.last_change_date_col:
                insert_columns.append(per.c[self.config.last_change_date_col])
                select_columns.append(sa.literal(self.config.end_of_time).label(self.config.last_change_date_col))
            if self.config.is_active_col:
                insert_columns.append(per.c[self.config.is_active_col])
                select_columns.append(
                    sa.literal("1").label(self.config.is_active_col))  # Default value for is_active column
            # Add business columns to the insert and select statements
            for column in self.config.business_columns:
                insert_columns.append(per.c[column["persistent_column"]])
                select_columns.append(v_sta.c[column["persistent_column"]])

            insert(connection, per, v_sta, cdc, operations, insert_columns, select_columns)

        def scd4() -> None:
            # Perform SCD4 operation
            per = self.meta.persistent_table
            v_sta = self.meta.staging_view
            cdc = sa.alias(self.meta.staging_cdc_table, name="cdc")

            _hard_delete_rows()
            _archive_rows(per, cdc)
            _insert_new_rows(per, v_sta, cdc)

        # Exécution des requêtes
        try:
            with self.engine.begin() as connection:
                if self.config.sync_mode == "scd1":
                    scd1(connection)
                elif self.config.sync_mode == "scd2":
                    scd2(connection)
                elif self.config.sync_mode == "scd4":
                    scd4()
            self.logger.info(
                f"Data loaded into persistent table {self.meta.persistent_table.schema}.{self.meta.persistent_table.name}.")
        except Exception as e:
            self.logger.error(f"An error occurred during the SCD operation: {e}")
            raise

    def synchronize(self) -> None:
        if self.config.sync_mode == "append":
            self._append()
        else:
            self._scd()

class ChangeDataCapture:
    """Classe principale gérant la logique de Change Data Capture."""

    def __init__(self, config_json_string: str, connection_string: str, logger: Logger) -> None:
        """Initialise les composants nécessaires au CDC."""
        self.logger = logger
        self.config = _Configuration(config_json_string, self.logger)
        self.engine = sa.create_engine(connection_string)
        self.meta = _Metadata(self.config, self.engine)
        self.schema_manager = _SchemaManager(self.config, self.engine, self.meta, self.logger)
        self.data_manager = _DataManager(self.config, self.engine, self.meta, self.logger)

    @timer
    def run(self) -> None:
        """Exécute le processus complet de synchronisation CDC."""
        try:
            # Prepare staging table and view
            self.schema_manager.alter_staging_table()
            self.schema_manager.create_staging_view()
            self.schema_manager.add_missing_datatypes()
            self.data_manager.compute_hashes()
            self.schema_manager.index_staging_table()

            # Create persistent table and view
            self.schema_manager.create_persistent_table()
            self.schema_manager.index_persistent_table()
            self.schema_manager.create_persistent_view()

            # CDC
            self.schema_manager.drop_and_create_cdc_table()
            self.data_manager.capture_data_change()

            # Insert into persistent table
            self.data_manager.synchronize()

        except Exception as e:
            self.logger.error(f"An unexpected error occurred during the synchronization run: {e}")
            raise
        finally:
            # Dispose engine to close connection pools cleanly
            if hasattr(self, "engine"):
                self.engine.dispose()
                self.logger.debug("Database engine disposed.")
