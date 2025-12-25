"""
Module de logger.

Contient la classe Logger pour la gestion des logs avec :
- affichage coloré en console,
- écriture dans un fichier rotatif,
- insertion optionnelle dans une base de données.

Inclut également CustomFormatter pour la coloration des logs en console.
"""
from __future__ import annotations

import logging
import sys
import traceback
from datetime import datetime, timezone
from logging import LogRecord
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from .db_mssql import DbMssql
from .db_mysql import DbMysql
from .db_pgsql import DbPgsql

if TYPE_CHECKING:
    from .data_factory import DataFactory

class CustomFormatter(logging.Formatter):
    """
    Un formateur personnalisé pour les logs permettant l'affichage en différentes couleurs.

    - DEBUG : vert
    - INFO : gris
    - WARNING : jaune
    - ERROR : rouge
    Seuls les messages print dans la console ont leurs couleurs changées
    """

    grey = "\x1b[37m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    light_green = "\x1b[92m"
    blue = "\x1b[94m"
    reset = "\x1b[0m"

    def __init__(self, base_format: str) -> None:
        """
        Initialise le CustomFormatter avec un format spécifique.

        :param base_format: Format de base pour les logs
        """
        super().__init__()
        self.base_format = base_format
        self.FORMATS = {
            logging.DEBUG: self.light_green + self.base_format + self.reset,
            logging.INFO: self.blue + self.base_format + self.reset,
            logging.WARNING: self.yellow + self.base_format + self.reset,
            logging.ERROR: self.red + self.base_format + self.reset,
            logging.CRITICAL: self.bold_red + self.base_format + self.reset,
            None: base_format,
        }

    def format(self, record: LogRecord) -> str:
        """Renvoie le message formaté avec les couleurs en fonction du niveau de log."""
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[None])
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class Logger:
    """
     Classe `Logger` pour gérer la journalisation dans les fichiers, la console et une base de données PostgreSQL ou MSSQL.

    Elle permet d'écrire les logs dans un fichier rotatif, dans la console avec des couleurs personnalisées,
    et également de les stocker dans une base de données, si spécifié.
    """

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    def __init__(
            self,
            log_level: int=INFO,
            logger_name: str= "AdsLogger",
            table_log_name: str= "LOGS",
            table_log_details_name: str="LOGS_details",
            *, timestamp_display: bool=True, name_display: bool=True,
    ) -> None:
        """
        Logger gère la journalisation dans les fichiers, la console et en base de données.

        Écrit dans la console avec des couleurs différentes, en fichier avec un backup de 10 jours et en base avec une
        connexion spécifiée
        :param log_level: le niveau de log courant, un message de debug ne sera pas affiché si le logger a un niveau info
        :param logger_name: le nom du logger
        :param table_log_name: le nom de la table de log
        :param table_log_details_name: le nom de la seconde table de log
        :param timestamp_display: booléen qui indique si l'horodatage doit être affiché
        :param name_display: booléen qui indique si le nom du logger doit être affiché
        """
        self.log_level_global = log_level
        self.log_level_base = log_level
        self.logger = self.__setup_logger(logger_name, timestamp_display=timestamp_display, name_display=name_display)
        self.connection = None
        self.db_logging_enabled = False
        self.table_log_name = table_log_name
        self.table_log_details_name = table_log_details_name
        self.creation_date = datetime.now(timezone.utc)
        self.job_key = uuid4()

    def __setup_logger(self, logger_name: str, *, timestamp_display: bool, name_display: bool) -> logging.Logger:
        """
        Configure le logger avec un gestionnaire pour les fichiers et un pour la console.

        :param logger_name: le nom du logger à configurer
        :return: le logger configuré
        """
        logger = logging.getLogger(logger_name)
        logger.setLevel(self.log_level_global)

        # Construire le format en fonction des paramètres
        base_format = "%(levelname)s - %(message)s"
        if name_display:
            base_format = "%(name)s - " + base_format
        if timestamp_display:
            base_format = "%(asctime)s - " + base_format

        file_handler = TimedRotatingFileHandler(filename="log.txt", when="D", interval=1, backupCount=10)
        file_handler.setLevel(self.log_level_global)
        file_handler.setFormatter(logging.Formatter(base_format))

        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level_global)
        console_handler.setFormatter(CustomFormatter(base_format))

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def set_connection(self, ads_connection: DataFactory, log_level: int) -> None:
        """
        Attribue la connexion passée en paramètre au logger.

        :param log_level: Le niveau de log pour l'insertion en base
        :param ads_connection: La connexion ads en question
        """
        self.connection = ads_connection
        self.db_logging_enabled = True
        self.log_level_base = log_level

    def _get_connection(self): # noqa: ANN202
        """
        Récupère la connexion associée au logger si elle existe.

        :return: la connexion
        """
        if isinstance(self.connection, (DbMssql, DbMysql, DbPgsql)):
            return self.connection.connection
        return self.connection

    def create_logs_tables(self) -> None:
        """
        Crée les tables de logs dans la base de données.

        Les tables créées sont :
        - `table_log_name` : Contient les logs principaux.
        - `table_log_details_name` : Contient les détails des logs.
        """
        if not self.connection or not self.db_logging_enabled:
            return
        if isinstance(self.connection, DbPgsql):
            logs_query = f"""
            CREATE TABLE {self.table_log_name} (
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                job_key UUID PRIMARY KEY,
                full_path VARCHAR(4000),
                status VARCHAR(50),
                message VARCHAR(4000)
            );"""
            details_query = f"""
            CREATE TABLE {self.table_log_details_name} (
                date TIMESTAMP,
                job_key UUID,
                log_level VARCHAR(20),
                message VARCHAR(4000),
                PRIMARY KEY (job_key, date)
            );"""
        elif isinstance(self.connection, DbMssql):
            logs_query = f"""
            CREATE TABLE {self.table_log_name} (
                start_time DATETIME,
                end_time DATETIME,
                job_key UNIQUEIDENTIFIER PRIMARY KEY,
                full_path NVARCHAR(4000),
                status NVARCHAR(50),
                message NVARCHAR(4000)
            );"""
            details_query = f"""
            CREATE TABLE {self.table_log_details_name} (
                date DATETIME,
                job_key UNIQUEIDENTIFIER,
                log_level NVARCHAR(20),
                message NVARCHAR(4000),
                PRIMARY KEY (job_key, date)
            );"""
        elif isinstance(self.connection, DbMysql):
            logs_query = f"""
            CREATE TABLE {self.table_log_name} (
                start_time DATETIME,
                end_time DATETIME,
                job_key CHAR(36) PRIMARY KEY,
                full_path VARCHAR(4000),
                status VARCHAR(50),
                message VARCHAR(4000)
            );"""
            details_query = f"""
            CREATE TABLE {self.table_log_details_name} (
                date DATETIME,
                job_key CHAR(36),
                log_level VARCHAR(20),
                message VARCHAR(4000),
                PRIMARY KEY (job_key, date)
            );"""
        else:
            msg = "Connexion à une base de données non supportée pour la création de tables."
            self.error(msg)
            raise NotImplementedError(msg)
        try:
            with self._get_connection().cursor() as cursor:
                cursor.execute(logs_query)
                cursor.execute(details_query)
                self._get_connection().commit()
                self.info(f"Table {self.table_log_name} et {self.table_log_details_name} créées.", insert=False)
        except Exception as e: # noqa: BLE001
            self._get_connection().rollback()
            self.error(f"Erreur lors de la création des tables de logs: {e}")

    def log_close(self, status: str, message: str) -> None:
        """
        Lance l'insertion dans la table de log principale et désactive les logs.

        :param status: Le statut du log à insérer
        :param message: Le message à insérer
        """
        self.info("Fermeture des logs en cours...", insert=False)
        self._insert_logs_table(status, message)
        self.disable()

    def _insert_logs_table(self, status: str, message: str) -> None:
        """
        Insère les données dans la table de logs principales.

        :param status: Statut de l'évènement
        :param message: Message de log
        """
        if not self.connection or not self.db_logging_enabled:
            self.warning("Pas de connexion valide ou logs désactivés.")
            return
        full_path = str(Path(sys.argv[0]).resolve().relative_to(Path.cwd().parent))
        try:
            with self._get_connection().cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO {self.table_log_name} (job_key, start_time, end_time, full_path, status, message)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                    (
                        str(self.job_key),
                        self.creation_date,
                        datetime.now(timezone.utc),
                        full_path,
                        status,
                        message[:4_000],
                    ),
                )
                self._get_connection().commit()
                self.info(f"Logs insérés dans la table de {self.table_log_name}.", insert=False)
        except Exception as e:
            self._get_connection().rollback()
            self.error(f"Échec de l'insertion dans la table de logs {self.table_log_name}: {e}",
                       insert=False)
            raise


    def _insert_logs_table_details(self, message: str, log_level: int) -> None:
        """
        Insère les données dans la table de logs détails.

        :param message: Message de log
        :param log_level: Le niveau de log
        """
        if not self.connection or not self.db_logging_enabled:
            return
        try:

            with self._get_connection().cursor() as cursor:

                cursor.execute(
                    f"""
                    INSERT INTO {self.table_log_details_name} (job_key, date, log_level, message)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        str(self.job_key),
                        datetime.now(timezone.utc),
                        log_level,
                        message[:4_000],
                    ),
                )
                self._get_connection().commit()
        except Exception as e:
            self._get_connection().rollback()
            self.error(f"Échec de l'insertion dans la table de détails {self.table_log_details_name}: {e}",
                       insert=False)
            raise

    def info(self, message: str, *, insert: bool=True) -> None:
        """
        Log un message avec le niveau info.

        :param insert: True si le message est à insérer en base
        :param message: le message à logguer
        """
        if self.log_level_global <= self.INFO:
            self.logger.info(message)
        if self.log_level_base <= self.INFO and insert:
            self._insert_logs_table_details(message, self.INFO)

    def error(self, message: str, *, insert: bool=True) -> None:
        """
        Log un message avec le niveau erreur.

        :param insert: True si le message est à insérer en base
        :param message: le message à logguer
        """
        if self.log_level_global <= self.ERROR:
            self.logger.error("*"*50)
            self.logger.error(message.replace("\n", " "))
            self.logger.error("*"*50)
        if self.log_level_base <= self.ERROR and insert:
            trace = traceback.format_exc()
            full_msg = f"{message}\nTraceback: {trace}" if "NoneType: None" not in trace else message
            self._insert_logs_table_details(full_msg, self.ERROR)

    def debug(self, message: str) -> None:
        """
        Log un message avec le niveau debug.

        :param message: le message à logguer
        """
        if self.log_level_global <= self.DEBUG:
            self.logger.debug(message)
        if self.log_level_base <= self.DEBUG:
            self._insert_logs_table_details(message, self.DEBUG)

    def warning(self, message: str) -> None:
        """
        Log un message avec le niveau warning.

        :param message: le message à logguer
        """
        if self.log_level_global <= self.WARNING:
            self.logger.warning(message)
        if self.log_level_base <= self.WARNING:
            self._insert_logs_table_details(message, self.WARNING)

    def custom_log(self, log_level: int, message: str) -> None:
        """
        Log un message avec un niveau custom.

        :param log_level: le niveau de log
        :param message: le message
        """
        if log_level >= self.log_level_global:
            self.logger.log(log_level, message)
        if log_level >= self.log_level_base:
            self._insert_logs_table_details(message, log_level)

    def enable(self, level_logger: int=INFO, level_for_base: int=INFO, *, generate_new_key: bool=False) -> None:
        """
        Active la journalisation et définit le niveau de log.

        :param generate_new_key: True si on doit définir un nouveau job_key
        :param level_for_base: Le niveau de log pour l'insertion en base
        :param level_logger: Le niveau de log pour l'affichage en console/fichier
        """
        self.logger.setLevel(level_logger)
        self.log_level_global = level_logger
        self.log_level_base = level_for_base
        self.db_logging_enabled = True
        if generate_new_key:
            self.job_key = uuid4()

    def disable(self) -> tuple[int, int]:
        """
        Désactive la journalisation en réglant le niveau de log au niveau CRITICAL et en désactivant l'insertion en base.

        :return : Les anciens niveaux de logs avant la désactivation
        """
        old_global = self.log_level_global
        old_base = self.log_level_base
        self.logger.setLevel(self.CRITICAL)
        self.log_level_global = self.CRITICAL
        self.log_level_base = self.CRITICAL
        self.db_logging_enabled = False
        return old_global, old_base
