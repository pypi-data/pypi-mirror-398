"""
Module db_mssql.

Fournit la classe `DbMssql` pour interagir avec une base Microsoft SQL Server.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pymssql

from .data_factory import DataFactory
from .timer import timer

if TYPE_CHECKING:
    import polars as pl

    from .logger import Logger

class DbMssql(DataFactory):
    """
    Classe de connection et d'intéraction avec une base Microsoft SQL Server.

    Cette classe hérite de 'DataFactory' et fournit des méthodes pour:
    - Se connecter à une base SQL Server.
    - Exécuter des requêtes SQL
    - Insérer des données par batch en bulk
    - Réaliser des opérations upsert
    - Rechercher des valeurs textuelles dans toutes les colonnes de toutes les tables d'une base

    Les opération d'insertion et d'upsert utilisent des batchs pour améliorer les performances et le suivi des évènements
    """

    def __init__(self, dictionnary: dict, logger: Logger, batch_size: int=10_000) -> None:
        """
        Instancie la classe DbMssql, qui hérite de dataFactory.

        :param dictionnary: Un dictionnaire contenant tous les paramètres nécéssaires pour lancer une connexion sql server
        - host: nom ou ip du server
        - port: port du serveur
        - database: nom de la base
        - user: nom d'utilisateur
        - password: mot de passe
        - charset: encodage de la connexion (par défaut UTF-8)
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
        self.__charset = dictionnary.get("charset", "UTF-8")
        self.batch_size = batch_size
        super().__init__(logger, batch_size)

    @timer
    def connect(self) -> None:
        """
        Lance la connexion avec les identifiants passés à l'initialisation de la classe.

        Toutes les méthodes de la classe nécéssitent une connexion active
        """
        if self.logger is not None:
            self.logger.info("Tentative de connexion avec la base de données.")
        try:
            server = f"{self.__host}:{self.__port}" if self.__port else self.__host
            self.connection = pymssql.connect(
                server=server,
                user=self.__user,
                password=self.__password,
                database=self.__database,
                charset=self.__charset,
            )
            if self.logger is not None:
                self.logger.info("Connexion établie avec la base de données.")
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Échec de la connexion à la base de données: {e}")
            raise

    def _bulk_execute_batch(self, full_table: str, cols: list, batch: pl.DataFrame) -> None:
        """
        Méthode héritée de DataFactory qui sert à insérer un batch en bulk.

        :param full_table: Le nom complet de la table 'schema.table'
        :param cols: Les colonnes dans lequelles insérer
        :param batch: Le batch à insérer
        """
        cols_def = ", ".join([f"[{col}]" for col in cols])
        openjson_defs = ", ".join([f"[{col}] NVARCHAR(MAX) '$.{col}'" for col in cols])
        query = f"""
        INSERT INTO {full_table} ({cols_def})
        SELECT {cols_def}
        FROM OPENJSON(%s)
        WITH ({openjson_defs});"""
        as_json = list(batch.iter_rows(named=True))
        json_data = json.dumps(as_json, default=str)
        with self.connection.cursor() as cursor:
            cursor.execute(query, (json_data,))

    def _upsert_query(self, full_table: str, cols: list, conflict_cols: list) -> str:
        """
        Méthode héritée de DataFactory qui sert à générer la requête pour effectuer un upsert.

        :param full_table: Le nom complet de la table 'schema.table'
        :param cols: Les colonnes dans lequelles insérer
        :param conflict_cols: Les colonnes pour détecter les conflits
        """
        target_cols = ", ".join(cols)
        source_cols = ", ".join([f"source.{col}" for col in cols])
        update_clause = ", ".join([f"target.{col} = source.{col}" for col in cols if col not in conflict_cols])
        conflict_cdt = " AND ".join([f"target.{col} = source.{col}" for col in conflict_cols])
        return f"""
        MERGE INTO {full_table} AS target
        USING (VALUES ({', '.join(['%s'] * len(cols))})) AS source ({', '.join(cols)})
        ON {conflict_cdt}
        WHEN MATCHED THEN
            UPDATE SET {update_clause}
        WHEN NOT MATCHED THEN
            INSERT ({target_cols})
            VALUES ({source_cols});"""

    def _create_temp_table(self, schema: str, table: str, temp_table: str, cols: list) -> None:
        """
        Méthode héritée de DataFactory qui crée une table temporaire pour un upsert en bulk.

        :param schema: Le schema dans lequel se trouve la table
        :param table: La table à copier
        :param temp_table: Le nom de la table temporaire à créer
        :param cols: Les colonnes nécessaires pour créer la table temporaire
        """
        schema = schema or "dbo"
        query = f"""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}'"""
        self.logger.debug(f"Récupération des colonnes depuis {schema}.{table}")
        log_level = self.logger.log_level_global
        self.logger.log_level_global = 30
        cols_def = next(iter(self.sql_query(query)))
        col_def_sql = []
        for col in cols:
            col_info = next((c for c in cols_def if c[0] == col), None)
            if col_info:
                col_name, data_type, char_length = col_info
                if char_length == -1:
                    col_def_sql.append(f"{col_name} {data_type.upper()}(MAX)")
                elif char_length and char_length > 0:
                    col_def_sql.append(f"{col_name} {data_type.upper()}({char_length})")
                else:
                    col_def_sql.append(f"{col_name} {data_type.upper()}")
            else:
                msg = f"Column {col} not found in {schema}.{table}"
                raise ValueError(msg)
        self.sql_exec(f"DROP TABLE IF EXISTS {schema}.{temp_table}")
        self.sql_exec(f"CREATE TABLE {schema}.{temp_table} ({', '.join(col_def_sql)})")
        self.logger.log_level_global = log_level
        self.logger.info(f"Table temporaire {schema}.{temp_table} créée.")

    def _upsert_bulk_query(self, full_table: str, full_temp_table: str, cols: list, conflict_cols: list) -> str:
        """
        Méthode héritée de DataFactory qui sert à générer la requête pour effectuer un upsert en bulk.

        :param full_table: Le nom complet de la table 'schema.table'
        :param full_temp_table: Le nom complet de la table temporaire
        :param cols: Les colonnes dans lequelles insérer
        :param conflict_cols: Les colonnes pour détecter les conflits
        """
        target_cols = ", ".join(cols)
        source_cols = ", ".join([f"source.{col}" for col in cols])
        update_clause = ", ".join(
            [f"target.{col} = source.{col}" for col in cols if col not in conflict_cols],
        )
        conflict_cdt = " AND ".join([f"target.{col} = source.{col}" for col in conflict_cols])
        return f"""
        MERGE INTO {full_table} AS target
        USING {full_temp_table} AS source
        ON {conflict_cdt}
        WHEN MATCHED THEN
            UPDATE SET {update_clause}
        WHEN NOT MATCHED BY TARGET THEN
            INSERT ({target_cols})
            VALUES ({source_cols});
        """

    def _get_text_columns_query(self, schema: str, table: str, *, include_views: bool) -> str:
        """
        Méthode à surcharger dans chaque sous-classe qui génère la requête qui récupère la liste des colonnes textuelles à scanner.

        :param schema: Le schema sur lequel filtrer
        :param table: La table sur laquelle filtrer
        :param include_views: Booléen qui indique si on inclut les vues dans la recherche
        """
        query = """
        SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE DATA_TYPE IN ('char', 'varchar', 'nchar', 'nvarchar', 'text', 'ntext')"""
        if not include_views:
            query += " AND TABLE_NAME IN (SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE')"
        if schema:
            query += f" AND TABLE_SCHEMA = '{schema}'"
        if table:
            query += f" AND TABLE_NAME = '{table}'"
        return query
