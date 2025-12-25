"""
Module data_factory.

Ce module définit la classe abstraite `DataFactory` qui pose le modèle de connexion et
d'interaction avec une base de données.

Il fournit les signatures des méthodes essentielles pour :
- se connecter à la base (`connect`)
- insérer des données (`insert`, `insert_bulk`)
- exécuter des requêtes (`sql_query`, `sql_exec`)

Certaines méthodes ont des logique identiques sur les trois technologies gérées (Postgre, SQL Server, MySQL) donc
les classes concernant ces technologies ne surchargent pas ces méthodes et les gardent telles qu'écrites dans DataFactory
"""
from __future__ import annotations

import timeit
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import polars as pl

from .global_config import get_timer
from .timer import timer

if TYPE_CHECKING:
    from collections.abc import Generator

    from .logger import Logger

class DataFactory(ABC):
    """Classe abstraite qui pose un modèle de connexion ads."""

    def __init__(self, logger: Logger, batch_size: int=10_000) -> None:
        """
        Initialise la factory avec un logger et un batch_size par défaut.

        Les class concrètes doivent définir toutes les méthodes abstraites
        """
        self.logger = logger
        self.batch_size = batch_size

    @abstractmethod
    def connect(self) -> None:
        """Lance la connexion avec les identifiants passés à l'initialisation de la classe."""
        raise NotImplementedError

    def sql_query(self, query: str, *, return_columns: bool = False) -> Generator[list[tuple], None, None]:
        """
        Lit la base de données avec la requête query.

        :param query: la requête
        :param return_columns: booléen qui indique si l'on veut aussi récupérer les noms des colonnes de la table
        :return: les données avec un yield
        """
        if not self.connection:
            msg = "La connexion n'est pas initialisée."
            raise RuntimeError(msg)

        self.logger.debug(f"Exécution de la requête de lecture: {query}")
        try:
            timer_start = timeit.default_timer()
            cpt_rows = 0
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                if return_columns:
                    yield list(cursor.description)
                self.logger.info("Requête exécutée avec succès, début de la lecture des résultats.")
                while True:
                    rows = cursor.fetchmany(self.batch_size)
                    if not rows:
                        break
                    yield rows
                    cpt_rows += len(rows)
                    self.logger.info(f"{cpt_rows} ligne(s) lue(s).")
            if get_timer():
                elapsed_time = timeit.default_timer() - timer_start
                self.logger.info(f"Temps d'exécution de sql_query: {elapsed_time:.4f} secondes.")
        except Exception as e:
            self.logger.error(f"Échec de la lecture des données: {e}")
            raise

    @timer
    def sql_exec(self, query: str) -> None:
        """
        Execute une requête sur la base de données, un create ou delete table par exemple.

        :param query: la requête
        """
        if not self.connection:
            msg = "La connexion n'est pas initialisée."
            raise RuntimeError(msg)
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                self.connection.commit()
                self.logger.info("Requête exécutée avec succès.")
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Échec de l'exécution de la requête: {e}")
            raise

    @timer
    def sql_scalaire(self, query: str) -> object | None:
        """Execute une requête et retourne le premier résultat."""
        if not self.connection:
            msg = "La connexion n'est pas initialisée."
            raise RuntimeError(msg)
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
            self.logger.info("Requête scalaire exécutée avec succès.")
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Échec de l'exécution de la requête: {e}")
            raise

    @staticmethod
    def _escape_value(value: str) -> str:
        if isinstance(value, str):
            return value.replace('"', '""').replace("'", "''")
        return value

    @timer
    def insert(self, schema: str, table: str, cols: list, row: list) -> tuple[str, list | str, list]:
        """
        Insère des données dans la base de données.

        :param schema: nom du schéma dans lequel insérer
        :param table: nom de la table dans laquelle insérer
        :param cols: liste des colonnes dans lesquelles insérer
        :param row: liste des valeurs à insérer
        """
        if not self.connection:
            msg = "La connexion n'est pas initialisée."
            raise RuntimeError(msg)
        placeholders = ", ".join(["%s"] * len(cols))
        table = f"{schema}.{table}" if schema else table
        query = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
        row = [self._escape_value(value) for value in row]
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, row)
                self.connection.commit()
                self.logger.info(f"{len(row)} valeur(s) insérée(s) avec succès dans la table {table}.")
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Erreur lors de l'insertion dans la table {table}: {e}")
            return "ERROR", str(e), row
        return "SUCCESS", [], []

    @timer
    def insert_many(self, schema: str, table: str, cols: list, rows: list[list]) \
            -> tuple[str, list[str] | str, list[list]]:
        """
        Insère des données par batch dans une table avec gestion des erreurs.

        :param schema: Nom du schéma dans lequel se trouve la table
        :param table: Nom de la table dans laquelle insérer
        :param cols: Liste des colonnes dans lesquelles insérer
        :param rows: Liste des lignes à insérer
        :return: Le résultat de l'opération, l'erreur, et le batch concerné
        """
        if not self.connection:
            msg = "La connexion n'est pas initialisée."
            raise RuntimeError(msg)
        failed_batches = []
        errors = []
        total_inserted = 0
        placeholders = ", ".join(["%s"] * len(cols))
        full_table = f"{schema}.{table}" if schema else table
        query = f"INSERT INTO {full_table} ({', '.join(cols)}) VALUES ({placeholders})"
        rows = [[self._escape_value(value) for value in row] for row in rows]
        size = len(rows)
        try:
            with self.connection.cursor() as cursor:
                for batch_index, start in enumerate(range(0, size, self.batch_size), start=1):
                    batch = rows[start: start + self.batch_size]
                    try:
                        cursor.executemany(query, batch)
                        self.connection.commit()
                        total_inserted += len(batch)
                        self.logger.info(
                            f"Batch {batch_index}: {len(batch)} ligne(s) insérée(s) avec succès dans la table {full_table}. "
                            f"Total inséré: {total_inserted}/{size} ligne(s).",
                        )
                    except Exception as batch_error:
                        self.connection.rollback()
                        self.logger.error(f"Erreur lors de l'insertion du batch {batch_index}: {batch_error}")
                        failed_batches.append(batch)
                        errors.append(str(batch_error))
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Erreur critique lors de l'insertion en batch des données: {e}")
            return "ERROR", str(e), rows
        return ("ERROR" if failed_batches else "SUCCESS"), errors, failed_batches

    def _get_df(self, rows: list[list], cols: list) -> pl.DataFrame:
        if isinstance(rows, list):
            df = pl.DataFrame(rows, schema=cols, orient="row", infer_schema_length=len(rows))
        elif isinstance(rows, pl.DataFrame):
            df = rows
        else:
            msg = "Les données doivent être une liste de tuples ou un DataFrame polars."
            raise TypeError(msg)
        return df

    @abstractmethod
    def _bulk_execute_batch(self, full_table: str, cols: list, batch: pl.DataFrame) -> None:
        raise NotImplementedError

    @timer
    def insert_bulk(self, schema: str, table: str, cols: list, rows: list[list]) \
            -> tuple[str, list[str] | str, list[pl.DataFrame] | list[list]]:
        """
        Similaire à insert_many, mais bien plus performant.

        :param schema: nom du schéma dans lequel insérer
        :param table: nom de la table dans laquelle insérer
        :param cols: liste des colonnes dans lesquelles insérer
        :param rows: liste des lignes à insérer
        """
        if not self.connection:
            msg = "La connexion n'est pas initialisée."
            raise RuntimeError(msg)
        failed_batches = []
        errors = []
        total_inserted = 0
        full_table = f"{schema}.{table}" if schema else table
        try:
            df = self._get_df(rows, cols)
            n_rows = df.height
            for batch_index, start in enumerate(range(0, n_rows, self.batch_size), start=1):
                batch = df.slice(start, self.batch_size)
                try:
                    self._bulk_execute_batch(full_table, cols, batch)
                    self.connection.commit()
                    total_inserted += batch.height
                    self.logger.info(
                        f"Batch {batch_index}: {len(batch)} ligne(s) insérée(s) avec succès dans la table {full_table}. "
                        f"Total inséré: {total_inserted}/{n_rows} ligne(s).",
                    )
                except Exception as batch_error:
                    self.connection.rollback()
                    self.logger.error(f"Erreur lors de l'insertion du batch {batch_index}: {batch_error}")
                    failed_batches.append(batch)
                    errors.append(str(batch_error))
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Erreur critique lors du bulk insert: {e}")
            return "ERROR", str(e), rows
        return ("ERROR" if failed_batches else "SUCCESS"), errors, failed_batches

    @abstractmethod
    def _upsert_query(self, full_table: str, cols: list, conflict_cols: list) -> str:
        raise NotImplementedError

    @timer
    def upsert(self, schema: str, table: str, cols: list, row: list, conflict_cols: list) \
            -> tuple[str, list | str , list]:
        """
        Réalise une opération upsert sur la base.

        :param schema: Le schéma de la table
        :param table: Le nom de la table
        :param cols: Liste des colonnes dans lequelles insérer
        :param row: Liste des valeurs à insérer ou mettre à jour
        :param conflict_cols: Colonnes à utiliser pour détecter les conflits (des clés primaires ou index)
        :return: Le résultat de l'opération, l'erreur et la ligne en cas d'erreur
        """
        if not self.connection:
            msg = "La connexion n'est pas initialisée."
            raise RuntimeError(msg)
        full_table = f"{schema}.{table}" if schema else table
        row = [self._escape_value(value) for value in row]
        query = self._upsert_query(full_table, cols, conflict_cols)
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, row)
                self.connection.commit()
                self.logger.info(f"{len(row)} valeurs insérées ou mises à jour dans la table {full_table}.")
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Erreur lors de l'upsert dans la table {full_table}: {e}")
            return "ERROR", str(e), row
        return "SUCCESS", [], []

    @timer
    def upsert_many(self, schema: str, table: str, cols: list, rows: list[list], conflict_cols: list)\
            -> tuple[str, str |list[str],  list[list[str]] | list[list[list]]]:
        """
        Réalise une opération upsert sur la base par batch.

        :param schema: Le schéma de la table
        :param table: Le nom de la table
        :param cols: Liste des colonnes dans lequelles insérer
        :param rows: Liste des lignes à insérer ou mettre à jour
        :param conflict_cols: Colonnes à utiliser pour détecter les conflits (des clés primaires ou index)
        :return: Le résultat de l'opération, l'erreur et la ligne en cas d'erreur
        """
        if not self.connection:
            msg = "La connexion n'est pas initialisée."
            raise RuntimeError(msg)
        failed_batches = []
        errors = []
        total_inserted = 0
        full_table = f"{schema}.{table}" if schema else table
        query = self._upsert_query(full_table, cols, conflict_cols)
        rows = [[self._escape_value(v) for v in row] for row in rows]
        size = len(rows)
        try:
            with self.connection.cursor() as cursor:
                for batch_index, start in enumerate(range(0, len(rows), self.batch_size), start=1):
                    batch = rows[start:start + self.batch_size]
                    size_batch = len(batch)
                    try:
                        cursor.executemany(query, batch)
                        self.connection.commit()
                        total_inserted += size_batch
                        self.logger.info(
                            f"Batch {batch_index}: {size_batch} ligne(s) insérée(s) ou mise(s) à jour dans la table {full_table}. "
                            f"Total inséré: {total_inserted}/{size} ligne(s).",
                        )
                    except Exception as batch_error:
                        self.connection.rollback()
                        self.logger.error(f"Erreur lors de l'upsert du batch {batch_index}: {batch_error}")
                        failed_batches.append(batch)
                        errors.append(str(batch_error))
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Erreur critique lors de l'upsert par batch: {e}")
            return "ERROR", str(e), rows
        return ("ERROR" if failed_batches else "SUCCESS"), errors, failed_batches

    @abstractmethod
    def _create_temp_table(self, schema: str, table: str, temp_table: str, cols: list) -> None:
        raise NotImplementedError

    @abstractmethod
    def _upsert_bulk_query(self, full_table: str, full_temp_table: str, cols: list, conflict_cols: list) -> str:
        raise NotImplementedError

    @timer
    def upsert_bulk(self, schema: str, table: str, cols: list, rows: list[list], conflict_cols: list) \
            -> tuple[str, list[str] | str, list[list] | list[pl.DataFrame]]:
        """
        Réalise une opération upsert sur la base par batch en bulk.

        :param schema: Le schéma de la table
        :param table: Le nom de la table
        :param cols: Liste des colonnes dans lequelles insérer
        :param rows: Liste des lignes à insérer ou mettre à jour
        :param conflict_cols: Colonnes à utiliser pour détecter les conflits (des clés primaires ou index)
        :return: Le résultat de l'opération, l'erreur et la ligne en cas d'erreur
        """
        if not self.connection:
            msg = "La connexion n'est pas initialisée."
            raise RuntimeError(msg)
        temp_table = f"{table}_temp"
        full_table = f"{schema}.{table}" if schema else table
        full_temp_table = f"{full_table}_temp"
        try:
            self._create_temp_table(schema, table, temp_table, cols)
            result, errors, failed_batches = self.insert_bulk(schema, temp_table, cols, rows)
            failed_rows = sum(b.height if hasattr(b, "height") else len(b) for b in failed_batches)
            if result == "ERROR":
                self.logger.warning(f"Insertion partielle dans {full_temp_table}: "
                                    f"{len(failed_batches)} batch(s) en erreur.")
            query = self._upsert_bulk_query(full_table, full_temp_table, cols, conflict_cols)
            self.sql_exec(query)
            self.logger.info(f"{len(rows) - failed_rows} lignes insérée(s) ou mise(s) à jour dans {full_table}.")
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Erreur critique lors de l'upsert bulk: {e}")
            return "ERROR", str(e), rows
        try:
            self.sql_exec(f"DROP TABLE IF EXISTS {full_temp_table}")
            self.logger.debug(f"Table temporaire {full_temp_table} supprimée.")
        except Exception as e:
            self.logger.warning(f"Impossible de supprimer la table temporaire {full_temp_table}: {e}")
        return result, errors, failed_batches

    @abstractmethod
    def _get_text_columns_query(self, schema: str, table: str, *, include_views: bool) -> str:
        raise NotImplementedError

    @timer
    def find_text_anywhere(self, search: str, schema: str | None = None, table: str | None = None,
                            log_every: int = 50, *, include_views: bool = False) -> list[dict[str, str | int]]:
        """
        Recherche une valeur textuelle dans toutes les colonnes textuelles de toutes les tables (et éventuellement vues) de tous les schémas.

        :param search: Texte à rechercher
        :param include_views: Inclure les vues dans la recherche (False par défaut)
        :param schema: Filtrer sur un schéma particulier
        :param table: Filtrer sur une table particulière
        :param log_every: Log de progression toutes les N colonnes
        """
        if not self.connection:
            msg = "La connexion n'est pas initialisée."
            raise RuntimeError(msg)
        results = []
        try:
            cols_query = self._get_text_columns_query(schema, table, include_views=include_views)
            cols = []
            for batch in self.sql_query(cols_query):
                cols.extend(batch)
            if not cols:
                self.logger.warning("Aucune colonne trouvée correspondant aux critères.")
                return results
            total = len(cols)
            total_schemas = len({s for s, _, _ in cols})
            total_tables = len({(s, t) for s, t, _ in cols})
            self.logger.info(f"Analyse de {total} colonnes(s) répartie(s) sur {total_tables} table(s) et {total_schemas} schéma(s)...")
            for i, (schema_name, table_name, column_name) in enumerate(cols, start=1):
                if i % log_every == 0 or i == total:
                    self.logger.debug(f"[{i}/{total}] Vérification de [{schema_name}].[{table_name}].[{column_name}].")
                full_table = f"{schema_name}.{table_name}" if schema_name else table_name
                log_level = self.logger.log_level_global
                self.logger.log_level_global = 30
                count = self.sql_scalaire(f"SELECT COUNT(*) FROM {full_table} WHERE {column_name} LIKE '{search}';")
                self.logger.log_level_global = log_level
                if int(str(count)) > 0:
                    results.append({
                        "schema": schema_name,
                        "table": table_name,
                        "column": column_name,
                        "count": count,
                        "query": f"SELECT * FROM {full_table} WHERE {column_name} LIKE '{search}';",
                    })
                    self.logger.info(f"{count} ligne(s) trouvée(s) dans {schema_name}.{table_name}.{column_name}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche du champ {search}: {e}")
            raise
        return results

    @timer
    def disconnect(self) -> None:
        """Ferme la connexion à la base de données si elle est ouverte."""
        if not self.connection:
            msg = "La connexion n'est pas initialisée."
            raise RuntimeError(msg)
        try:
            self.connection.close()
            self.connection = None
            if self.logger:
                self.logger.info("Connexion fermée.")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur lors de la fermeture de la connexion: {e}")
            raise
