"""
Module db_mysql.

Fournit la classe `DbMysql` pour interagir avec une base MySQL.
"""
from __future__ import annotations

import json
import pathlib
import tempfile
from typing import TYPE_CHECKING

import pymysql

from .data_factory import DataFactory
from .timer import timer

if TYPE_CHECKING:
    import polars as pl

    from .logger import Logger

class DbMysql(DataFactory):
    """
    Classe de connection et d'intéraction avec une base MySQL.

    Cette classe hérite de 'DataFactory' et fournit des méthodes pour:
    - Se connecter à une base MySQL.
    - Exécuter des requêtes SQL
    - Insérer des données par batch en bulk
    - Réaliser des opérations upsert
    - Rechercher des valeurs textuelles dans toutes les colonnes de toutes les tables d'une base

    Les opération d'insertion et d'upsert utilisent des batchs pour améliorer les performances et le suivi des évènements
    """

    def __init__(self, dictionnary: dict, logger: Logger, batch_size: int=10_000) -> None:
        """
        Instancie la classe DbMYsql, qui hérite de dataFactory.

        :param dictionnary: Un dictionnaire contenant tous les paramètres nécéssaires pour lancer une connexion sql server
        - host: nom ou ip du server
        - port: port du serveur
        - database: nom de la base
        - user: nom d'utilisateur
        - password: mot de passe
        :param logger: un logger ads qui va gérer les logs des actions de la classe
        :param batch_size: la taille des batchs en lecture et écriture
        """
        self.connection = None
        self.logger = logger
        self.__database = dictionnary.get("database")
        self.__user = dictionnary.get("user")
        self.__password = dictionnary.get("password")
        self.__port = dictionnary.get("port")
        self.__host = dictionnary.get("host")
        self.batch_size = batch_size
        super().__init__(logger, batch_size)

    @timer
    def connect(self) -> None:
        """
        Lance la connexion avec les identifiants passés à l'initialisation de la classe.

        Toutes les méthodes de la classe nécéssitent une connexion active
        """
        if self.logger:
            self.logger.info("Tentative de connexion avec la base de données.")
        try:
            self.connection = pymysql.connect(
                host=self.__host,
                port=int(self.__port),
                user=self.__user,
                password=self.__password,
                database=self.__database,
                autocommit=False,
                local_infile=True,
            )
            if self.logger:
                self.logger.info("Connexion établie avec la base de données.")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Échec de la connexion à la base de données: {e}")
            raise

    def _bulk_execute_batch(self, full_table: str, cols: list, batch: pl.DataFrame) -> None:
        """
        Méthode héritée de DataFactory qui sert à insérer un batch en bulk.

        :param full_table: Le nom complet de la table 'schema.table'
        :param cols: Les colonnes dans lequelles insérer
        :param batch: Le batch à insérer
        """
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", encoding="utf-8") as tmp_file:
            temp_file = pathlib.Path(tmp_file.name).as_posix()
            for row in batch.rows(named=True):
                safe_row = {k: (None if v is None else str(v).replace("\\", "\\\\").replace('"', '\\"')) for k, v in row.items()}
                tmp_file.write(json.dumps(safe_row, default=str) + "\n")
        query = f"""
        LOAD DATA LOCAL INFILE '{temp_file}'
        INTO TABLE {full_table}
        LINES TERMINATED BY '\n'
        (@json)
        SET {', '.join(
            f"{col}=NULLIF(JSON_UNQUOTE(JSON_EXTRACT(@json,'$.{col}')), 'null')" for col in cols
        )}"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SET SESSION sql_mode = 'STRICT_ALL_TABLES,ERROR_FOR_DIVISION_BY_ZERO';")
                cursor.execute(query)
                cursor.execute("SHOW WARNINGS;")
                warnings = cursor.fetchall()
                if warnings:
                    msg = f"MySQL a rencontré des erreurs lors du chargement: {warnings}"
                    raise RuntimeError(msg)
        finally:
            path = pathlib.Path(temp_file)
            if path.exists():
                path.unlink()

    def _upsert_query(self, full_table: str, cols: list, conflict_cols: list) -> str:
        """
        Méthode héritée de DataFactory qui sert à générer la requête pour effectuer un upsert.

        :param full_table: Le nom complet de la table 'schema.table'
        :param cols: Les colonnes dans lequelles insérer
        :param conflict_cols: Les colonnes pour détecter les conflits
        """
        columns = ", ".join([f"`{col}`" for col in cols])
        placeholders = ", ".join(["%s"] * len(cols))
        update_clause = ", ".join([f"`{col}` = VALUES(`{col}`)" for col in cols if col not in conflict_cols])
        return f"""
        INSERT INTO {full_table} ({columns})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {update_clause};"""

    def _create_temp_table(self, schema: str, table: str, temp_table: str, cols: list) -> None: # noqa: ARG002
        """
        Méthode héritée de DataFactory qui crée une table temporaire pour un upsert en bulk.

        :param schema: Le schema dans lequel se trouve la table
        :param table: La table à copier
        :param temp_table: Le nom de la table temporaire à créer
        :param cols: Les colonnes nécessaires pour créer la table temporaire
        """
        full_table = f"{schema}.{table}" if schema else table
        full_temp_table = f"{schema}.{temp_table}" if schema else temp_table
        self.logger.debug(f"Création de la table temporaire {full_temp_table}")
        self.sql_exec(f"CREATE TEMPORARY TABLE {full_temp_table} LIKE {full_table}")
        self.logger.info(f"Table temporaire {full_temp_table} créée.")

    def _upsert_bulk_query(self, full_table: str, full_temp_table: str, cols: list, conflict_cols: list) -> str:
        """
        Méthode héritée de DataFactory qui sert à générer la requête pour effectuer un upsert en bulk.

        :param full_table: Le nom complet de la table 'schema.table'
        :param full_temp_table: Le nom complet de la table temporaire
        :param cols: Les colonnes dans lequelles insérer
        :param conflict_cols: Les colonnes pour détecter les conflits
        """
        columns = ", ".join(cols)
        update_clause = ", ".join([f"{col} = VALUES({col})" for col in cols if col not in conflict_cols])
        return f"""
        INSERT INTO {full_table} ({columns})
        SELECT {columns} FROM {full_temp_table}
        ON DUPLICATE KEY UPDATE {update_clause};
        """

    def _get_text_columns_query(self, schema: str, table: str, *, include_views: bool) -> str:
        """
        Méthode à surcharger dans chaque sous-classe qui génère la requête qui récupère la liste des colonnes textuelles à scanner.

        :param schema: Le schema sur lequel filtrer
        :param table: La table sur laquelle filtrer
        :param include_views: Booléen qui indique si on inclut les vues dans la recherche
        """
        query = """
        SELECT table_schema, table_name, column_name
        FROM information_schema.columns
        WHERE data_type IN ('char', 'varchar', 'text', 'tinytext', 'mediumtext', 'longtext')
            AND table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')"""
        if not include_views:
            query += " AND table_name IN (SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE')"
        if schema:
            query += f" AND table_schema = '{schema}'"
        if table:
            query += f" AND table_name = '{table}'"
        return query
