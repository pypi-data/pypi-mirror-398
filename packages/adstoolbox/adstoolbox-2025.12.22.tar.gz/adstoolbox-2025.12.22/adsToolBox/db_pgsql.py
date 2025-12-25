"""
Module db_pgsql.

Fournit la classe `DbMysql` pour interagir avec une base MySQL.
"""
from __future__ import annotations

import io
from typing import TYPE_CHECKING

import psycopg2

from .data_factory import DataFactory
from .timer import timer

if TYPE_CHECKING:
    import polars as pl

    from .logger import Logger

class DbPgsql(DataFactory):
    """
    Classe de connection et d'intéraction avec une base Postgre.

    Cette classe hérite de 'DataFactory' et fournit des méthodes pour:
    - Se connecter à une base Postgre.
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
        if self.logger is not None:
            self.logger.info("Tentative de connexion avec la base de données.")
        try:
            self.connection = psycopg2.connect(
                database=self.__database,
                user=self.__user,
                password=self.__password,
                port=self.__port,
                host=self.__host,
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
        buffer = io.StringIO()
        batch.write_csv(buffer, include_header=False)
        buffer.seek(0)
        columns = ", ".join(cols)
        query = f"COPY {full_table} ({columns}) FROM STDIN WITH CSV DELIMITER ',';"
        with self.connection.cursor() as cursor:
            cursor.copy_expert(query, buffer)

    def _upsert_query(self, full_table: str, cols: list, conflict_cols: list) -> str:
        """
        Méthode héritée de DataFactory qui sert à générer la requête pour effectuer un upsert.

        :param full_table: Le nom complet de la table 'schema.table'
        :param cols: Les colonnes dans lequelles insérer
        :param conflict_cols: Les colonnes pour détecter les conflits
        """
        placeholders = ", ".join(["%s"] * len(cols))
        update_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in cols if col not in conflict_cols])
        conflict_clause = ", ".join(conflict_cols)
        return f"""
        INSERT INTO {full_table} ({', '.join(cols)})
        VALUES ({placeholders})
        ON CONFLICT ({conflict_clause}) DO UPDATE
        SET {update_clause};"""

    def _create_temp_table(self, schema: str, table: str, temp_table: str, cols: list) -> None:  # noqa: ARG002
        """
        Méthode héritée de DataFactory qui crée une table temporaire pour un upsert en bulk.

        :param schema: Le schema dans lequel se trouve la table
        :param table: La table à copier
        :param temp_table: Le nom de la table temporaire à créer
        :param cols: Les colonnes nécessaires pour créer la table temporaire
        """
        table_full = f"{schema}.{table}" if schema else table
        full_temp_table = f"{schema}.{temp_table}" if schema else temp_table
        query = f"CREATE TEMP TABLE {full_temp_table} (LIKE {table_full} INCLUDING DEFAULTS)"
        self.logger.debug(f"Création de la table temporaire {full_temp_table}")
        self.sql_exec(query)
        self.logger.info(f"Table temporaire {full_temp_table} créée.")

    def _upsert_bulk_query(self, full_table: str, full_temp_table: str, cols: list, conflict_cols: list) -> str:
        """
        Méthode héritée de DataFactory qui sert à générer la requête pour effectuer un upsert en bulk.

        :param full_table: Le nom complet de la table 'schema.table'
        :param full_temp_table: Le nom complet de la table temporaire
        :param cols: Les colonnes dans lequelles insérer
        :param conflict_cols: Les colonnes pour détecter les conflits
        """
        conflict_clause = ", ".join(conflict_cols)
        update_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in cols if col not in conflict_cols])
        return f"""
        INSERT INTO {full_table} ({', '.join(cols)})
        SELECT {', '.join(cols)} FROM {full_temp_table}
        ON CONFLICT ({conflict_clause}) DO UPDATE
        SET {update_clause};
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
        WHERE data_type IN ('character varying', 'varchar', 'character', 'char', 'text')
            AND table_schema NOT IN ('information_schema', 'pg_catalog')"""
        if not include_views:
            query += " AND table_name IN (SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE')"
        if schema:
            query += f" AND table_schema = '{schema}'"
        if table:
            query += f" AND table_name = '{table}'"
        return query
