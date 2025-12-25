"""
Module pipeline.

Contient la classe Pipeline pour extraire et charger les données depuis différentes sources vers des bases de données.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Generator, Mapping

    from .data_factory import DataFactory

import polars as pl

from .db_mssql import DbMssql
from .db_mysql import DbMysql
from .logger import Logger
from .timer import timer


class Pipeline:
    """
    Classe représentant un pipeline ETL.

    Cette classe fait le lien entre une source de données et une destination, avec gestion des batches,
    typage dynamique et génération de hash pour les lignes.
    """

    SQL_TO_POLARS: ClassVar[dict[str, pl.DataType]] = {
        "int": pl.Int64,
        "integer": pl.Int64,
        "bigint": pl.Int64,
        "smallint": pl.Int32,
        "varchar": pl.Utf8,
        "text": pl.Utf8,
        "char": pl.Utf8,
        "time": pl.Time,
        "timestamp": pl.Datetime,
        "datetime": pl.Datetime,
        "datetime2": pl.Datetime,
        "date": pl.Date,
        "float": pl.Float64,
        "double": pl.Float64,
        "boolean": pl.Boolean,
    }

    def __init__(self, dictionnary: dict, logger: Logger) -> None:
        """
        Initialise un pipeline avec les informations de connexions aux bases de données.

        :param dictionnary: le dictionnaire qui contient les informations du pipeline
            - 'db_source': la base de données source
            - 'query_source': la requête à envoyer à la source
            - 'tableau': les données sous forme de tableau (source alternative)
            - 'db_destination': la base de données destination
            - 'executemany' ou 'bulk'
            - 'batch_size': la taille des lots pour le traitement en batch
        :param logger: le logger pour gérer la journalisation des évènements du pipeline
        """
        self.logger = logger
        self.__db_source: DataFactory = dictionnary.get("db_source")
        self.__query_source: str = dictionnary.get("query_source")
        self.__tableau = dictionnary.get("tableau")
        self.db_destination: dict = dictionnary.get("db_destination")
        self.operation_type: str = dictionnary.get("operation_type", "insert")
        self.insert_method: str = dictionnary.get("insert_method", "bulk")
        self.batch_size: int = dictionnary.get("batch_size", 10_000)
        self.db_destination.get("db").batch_size = self.batch_size
        if self.__db_source:
            self.__db_source.batch_size = self.batch_size

    def _generate_hash(self, row: dict, cols: list[str]) -> str:
        """Génère un hash MD5 pour une ligne de valeurs donnée."""
        concat_cols = "|".join(str(row[col]) if row[col] is not None else "null" for col in cols)
        return hashlib.md5(concat_cols.encode("utf-8")).hexdigest() # noqa: S324

    def sql_defs_to_polars_schema(self, cols: list[str], cols_def: list[str]) -> dict:
        """Convertit les définitions de colonnes SQL en types compatibles avec Polars."""
        schema = {}
        for col, sql_type in zip(cols, cols_def):
            base_type = sql_type.split("(")[0].lower()
            if isinstance(self.__db_source, DbMysql) and sql_type.lower() == "time":
                pl_type = pl.Utf8
            else:
                pl_type = Pipeline.SQL_TO_POLARS.get(base_type)
                if not pl_type:
                    self.logger.debug(f"Type SQL non reconnu '{sql_type}', fallback en Utf8 pour la colonne '{col}'.")
                    pl_type = pl.Utf8
            schema[col] = pl_type
        return schema

    def _update_schema(self, old_schema: Mapping[str, pl.DataType], new_schema: Mapping[str, pl.DataType]) -> Mapping[str, pl.DataType]:
        """
        Mets à jour l'ancien schéma en remplaçant les colonnes encore identifiées comme NULL.

        :param old_schema: L'ancien schéma
        :param new_schema: Le nouveau schéma du batch en cours
        :return: Le schéma mis à jour
        """
        updated_schema = dict(old_schema)
        for col, dtype in old_schema.items():
            if dtype == pl.Null and col in dict(new_schema):
                updated_schema[col] = dict(new_schema)[col]
        return updated_schema

    def _process_batch(
            self,
            batch: list | pl.DataFrame,
            cols: list[str],
            cols_def: list[str],
            *, apply_hash: bool,
    ) -> pl.DataFrame:
        if isinstance(batch, pl.DataFrame):
            return batch
        schema: dict[str, pl.DataType] | None = getattr(self, "_schema_cache", None)
        batch_dicts = [dict(zip(cols, row)) for row in batch]
        if apply_hash:
            hash_col = self.db_destination.get("hash")
            for row in batch_dicts:
                cols_to_hash = [col for col in cols if col != hash_col]
                row[hash_col] = self._generate_hash(row, cols_to_hash)
        if schema is None:
            if cols_def and all(t is not None for t in cols_def):
                schema = self.sql_defs_to_polars_schema(cols, cols_def)
                df = pl.DataFrame(batch_dicts, schema=schema, orient="row", strict=False)
            else:
                self.logger.debug("Inférence des types sur le premier batch.")
                df = pl.DataFrame(batch_dicts, orient="row", strict=False, infer_schema_length=len(batch_dicts))
                schema = df.schema
        else:
            if any(dtype == pl.Null for dtype in schema.values()):
                self.logger.debug("Réinférence partielle des types.")
                df_temp = pl.DataFrame(batch_dicts, orient="row", strict=False, infer_schema_length=len(batch_dicts))
                schema = self._update_schema(schema, df_temp.schema)
            df = pl.DataFrame(batch_dicts, schema=schema, orient="row", strict=False)
        self._schema_cache = schema
        return df

    def _yield_with_handling(
            self,
            batch: list | pl.DataFrame,
            cols: list[str],
            cols_def: list[str],
            *, apply_hash: bool,
    ) -> Generator[pl.DataFrame | tuple]:
        try:
            yield self._process_batch(batch, cols, cols_def, apply_hash=apply_hash)
        except Exception as e: # noqa: BLE001
            msg = f"Échec de la création du dataframe: {e}"
            if self.__db_source:
                if isinstance(self.__db_source, DbMysql):
                    msg += "\n(Pour MySQL, pensez à TIME_FORMAT(col, '%H:%i:%s'))"
                elif isinstance(self.__db_source, DbMssql):
                    msg += "\n(Pour SQL Server, CAST(uuid_col AS NVARCHAR(36)))"
            for line in msg.split("\n("):
                self.logger.error(line)
            yield None, batch

    def _process_tableau_batches(self) -> Generator[pl.DataFrame | tuple]:
        cols = self.db_destination.get("cols", [])
        cols_def = self.db_destination.get("cols_def", [])
        hash_col = self.db_destination.get("hash")
        apply_hash = hash_col in cols if hash_col else False
        for start in range(0, len(self.__tableau), self.batch_size):
            batch = self.__tableau[start:start + self.batch_size]
            yield from self._yield_with_handling(batch, cols, cols_def, apply_hash=apply_hash)

    def _process_db_batches(self) -> Generator[pl.DataFrame | tuple]:
        cols = self.db_destination.get("cols", [])
        cols_def = self.db_destination.get("cols_def", [])
        hash_col = self.db_destination.get("hash")
        apply_hash = hash_col in cols if hash_col else False
        log_level, log_base = self.logger.disable()
        self.__db_source.connect()
        self.logger.enable(log_level, log_base)
        for batch in self.__db_source.sql_query(self.__query_source):
            yield from self._yield_with_handling(batch, cols, cols_def, apply_hash=apply_hash)

    def _data_generator(self) -> Generator[pl.DataFrame | tuple]:
        """
        Générateur de données qui itère sur les données sources et les renvoie en DataFrame polars.

        :return: Yield un DataFrame Polars contenant un batch de données.
        :raises ValueError: Si deux sources de données sont spécifiées (tableau et base de données)
        ou si aucune source de données valide n'est définie.
        """
        self.logger.info("Chargement des données depuis la source...")
        if self.__tableau is not None and self.__db_source is not None:
            msg = ("On veut tous le beurre et l'argent du beurre...\n"
                   "Deux sources de données différentes sont définies, veuillez n'en choisir qu'une.")
            self.logger.error(msg)
            raise ValueError(msg)
        if self.__tableau:
            yield from self._process_tableau_batches()
        elif self.__db_source and self.__query_source:
            yield from self._process_db_batches()
        else:
            msg = "Aucune source de données choisie."
            raise ValueError(msg)

    @timer
    def create_destination_table(self, *, drop: bool=False) -> None:
        """Supprime et crée la table de destination du pipeline."""
        dst = self.db_destination.get("db")
        schema = self.db_destination.get("schema")
        table = self.db_destination.get("table")
        full_table = f"{schema}.{table}" if schema else table
        cols = self.db_destination.get("cols")
        cols_def = self.db_destination.get("cols_def")
        if len(cols) != len(cols_def):
            msg = f"Le nombre de colonnes (cols = {len(cols)}) ne correspond pas au nombre de définitions (cols_def = {len(cols_def)})"
            raise ValueError(msg)
        columns = ", ".join([f"{col} {defn}" for col, defn in zip(cols, cols_def)])
        dst.connect()
        self.logger.info("Création de la table de destination...")
        try:
            if drop:
                dst.sql_exec(f"DROP TABLE IF EXISTS {full_table}")
            dst.sql_exec(f"CREATE TABLE {full_table} ({columns})")
            self.logger.info("Table de destination créée.")
        except Exception as e:
            self.logger.error(f"Erreur lors de la création de la table de destination: {e}")
            raise

    def _insert(self, rows: list[list]) -> tuple[str, list[str] | str, list[pl.DataFrame] | list[list]]:
        """Insère par bulk ou executemany."""
        if self.insert_method == "bulk":
            return self.db_destination.get("db").insert_bulk(
                schema=self.db_destination.get("schema"),
                table=self.db_destination.get("table"),
                rows=rows,
                cols=self.db_destination.get("cols"),
            )
        if self.insert_method == "executemany":
            return self.db_destination.get("db").insertMany(
                schema=self.db_destination.get("schema"),
                table=self.db_destination.get("table"),
                rows=rows,
                cols=self.db_destination.get("cols"),
            )
        msg = f"{self.insert_method} n'est pas implémentée. 'bulk' ou 'executemany'."
        raise NotImplementedError(msg)

    def _upsert(self, rows: list[list]) -> tuple[str, list[str] | str, list[pl.DataFrame] | list[list]]:
        """Upsert par bulk ou executemany."""
        if self.insert_method == "bulk":
            return self.db_destination.get("db").upsertBulk(
                schema=self.db_destination.get("schema"),
                table=self.db_destination.get("table"),
                rows=rows,
                cols=self.db_destination.get("cols"),
                conflict_cols=self.db_destination.get("conflict_cols"),
            )
        if self.insert_method == "executemany":
            return self.db_destination.get("db").upsertMany(
                schema=self.db_destination.get("schema"),
                table=self.db_destination.get("table"),
                rows=rows,
                cols=self.db_destination.get("cols"),
                conflict_cols=self.db_destination.get("conflict_cols"),
            )
        msg = f"{self.insert_method} n'est pas implémentée. 'bulk' ou 'executemany'."
        raise NotImplementedError(msg)

    def _perform_insertion(self, rows: list[list]) -> tuple[str, list[str] | str, list[pl.DataFrame] | list[list]]:
        """Effectue l'insertion ou l'upsert des données."""
        if self.operation_type == "insert":
            return self._insert(rows)
        if self.operation_type == "upsert":
            return self._upsert(rows)
        msg = f"L'opération {self.operation_type} n'est pas implémentée. 'insert' ou 'upsert'."
        raise NotImplementedError(msg)

    @timer
    def run(self) ->  dict[str, int | list[tuple]]:
        """
        Exécute le pipeline en insérant des données depuis la source vers la destination définie.

        :return: Une liste des lots rejetés contenant les erreurs lors de l'insertion.
        :raises Exception: Si une erreur autre qu'une erreur d'insertion survient pendant l'exécution du pipeline
        """
        def _raise_invalid_op() -> None:
            msg = "Aucune opération n'a été réalisée, vérifiez les operation_type et insert_method."
            raise ValueError(msg)
        rejects = []
        res = {"nb_lines_success": 0, "nb_lines_error": 0, "errors": rejects}
        batch_cpt = 1
        total = 0
        total_inserted = 0
        schema = self.db_destination.get("schema")
        table = self.db_destination.get("table")
        table_full = f"{schema}.{table}" if schema else table
        log_level, base_level = self.logger.disable()
        try:
            self.db_destination["db"].connect()
            self.logger.enable(log_level, base_level)
            name = self.db_destination.get("name", "bdd")
            self.logger.info(f"Connexion à {name} réussie.")
            for batch_df in self._data_generator():
                taille = len(batch_df)
                total += taille
                if isinstance(batch_df, tuple) and batch_df[0] is None:
                    rejects.append((name, "Échec création dataframe", batch_df[1]))
                    res["nb_lines_error"] += len(batch_df[1])
                    continue
                rows = batch_df.rows()
                old_global, old_base = self.logger.disable()
                self.logger.enable(Logger.ERROR, Logger.ERROR)
                insert_result = self._perform_insertion(rows)
                self.logger.enable(old_global, old_base)
                if not insert_result:
                    _raise_invalid_op()
                if insert_result[0] == "ERROR":
                    rejects.append((name, insert_result, rows))
                    res["nb_lines_error"] += taille
                else:
                    total_inserted += taille
                    res["nb_lines_success"] += taille
                    self.logger.info(
                        f"Batch {batch_cpt}: {taille} ligne(s) insérée(s) avec succès dans la table {table_full}. "
                        f"Total inséré: {total_inserted}/{total} ligne(s).")
                    batch_cpt += 1
        except Exception as e:
                self.logger.enable(log_level, base_level)
                self.logger.error(f"Échec de l'exécution du pipeline: {e}")
                raise
        return res
