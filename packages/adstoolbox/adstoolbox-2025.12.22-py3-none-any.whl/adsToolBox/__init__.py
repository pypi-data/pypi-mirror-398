"""
Package adsToolBox.

Contient les modules pour :
- Gestion des bases de données et pipeline
- Gestion des fichiers
- Logging
- Outils Odoo
- Gestion Repo Git
- Journalisation et Chronomètre
- Gestion de l'environnement
- Objet de lecture de mail
"""

from .cdc import ChangeDataCapture
from .data_comparator import DataComparator
from .data_factory import DataFactory
from .db_mssql import DbMssql
from .db_mysql import DbMysql
from .db_pgsql import DbPgsql
from .file_handler import FileHandler
from .git_handler import GitHandler
from .global_config import get_public_ip, set_timer
from .google_calendar import GoogleCalendarConnector
from .load_env import Env
from .logger import Logger
from .mail_reader import MailReader
from .odoo import OdooConnector
from .pipeline import Pipeline
from .timer import get_timer, now, set_timezone, timer

__all__ = [
    "ChangeDataCapture",
    "DataComparator",
    "DataFactory",
    "DbMssql",
    "DbMysql",
    "DbPgsql",
    "Env",
    "FileHandler",
    "GitHandler",
    "GoogleCalendarConnector",
    "Logger",
    "MailReader",
    "OdooConnector",
    "Pipeline",
    "get_public_ip",
    "get_timer",
    "now",
    "set_timer",
    "set_timezone",
    "timer",
]
