"""
Module odoo.

Contient la classe OdooConnector pour se connecter à Odoo via XML-RPC.
"""
import xmlrpc.client

from .logger import Logger


class OdooConnector:
    """Classe pour gérer la connexion à Odoo via XML-RPC."""

    def __init__(self, dictionnary: dict, logger: Logger) -> None:
        """
        Classe pour se connecter à Odoo via xmlrpc et exécuter des opérations CRUD.

        :param dictionnary: Un dictionnaire contenant tous les paramètres nécéssaires pour lancer une connexion Odoo
        :param logger: Un logger ads qui va gérer les logs des actions de la classe
        """
        self.models = None
        self.uid = None
        self.common = None
        self.name = dictionnary["name"]
        self.url = dictionnary["url"]
        self.db = dictionnary["db"]
        self.user = dictionnary["user"]
        self.password = dictionnary["password"]
        self.logger = logger

    def connect(self) -> None:
        """Lance la connection à Odoo."""
        def _raise_auth_error(msg: str) -> None:
            self.logger.error(msg)
            raise RuntimeError(msg)
        self.logger.info("Tentative de connexion à Odoo...")
        try:
            self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/common")
            self.uid = self.common.authenticate(self.db, self.user, self.password, {})
            if not self.uid:
                _raise_auth_error("Échec de l'authentification, identifiants incorrects.")
            self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        except (xmlrpc.client.Fault, xmlrpc.client.ProtocolError) as e:
            _raise_auth_error(f"Erreur lors de la connexion à Odoo : {e}")
        self.logger.info("Connexion à Odoo réussie.")
        self.logger.debug(f"Connecté en tant que {self.user} (UID: {self.uid})")

    def __str__(self) -> str:
        """Retourne le nom de la connexion Odoo."""
        return f"Connexion Odoo: {self.name}"

    def desc(self, table: str) -> list[dict[str, str]]:
        """
        Retourne la description des champs d'une table Odoo.

        :param table: Le nom du modèle
        :return: Un dictionnaire qui contient les informations sur les champs
        """
        try:
            self.logger.info(f"Récupération des informations de la table: {table}")
            fields = self.models.execute_kw(
                self.db, self.uid, self.password, table, "fields_get", [], {"attributes": ["string", "help", "type"]},
            )
            self.logger.info(f"Descriptions récupérées pour la table: {table}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des descriptions: {e}")
            raise
        return fields

    def get(self, table: str, fields: list[str], filtre: list) -> list[dict[str, str]]:
        """
        Récupère des enregistrements dans Odoo avec un filtre.

        :param table: Le nom du modèle Odoo
        :param fields: Une liste de champs à récupérer
        :param filtre: Un filtre Odoo
        :return: Une liste d'enregistrements correspondant au filtre
        """
        try:
            self.logger.info(f"Récupération des enregistrements depuis la table {table} avec le filtre: {filtre}")
            records = self.models.execute_kw(
                self.db, self.uid, self.password, table, "search_read", [filtre], {"fields": fields},
            )
            self.logger.info(f"{len(records)} enregistrement(s) récupérés depuis {table}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des enregistrements depuis {table}: {e}")
            raise
        return records

    def put(self, table: str, lines: list) -> list[int]:
        """
        Insère de nouveaux enregistrements dans Odoo.

        :param table: Le nom du modèle où insérer
        :param lines: Une liste contenant les données à insérer
        :return: Une liste d'IDs des enregistrements crées
        """
        try:
            self.logger.info(f"Insertion de {len(lines)} enregistrement(s) dans {table}")
            ids = []
            for line in lines:
                id_line = self.models.execute_kw(
                    self.db, self.uid, self.password, table, "create", [line],
                )
                ids.append(id_line)
                self.logger.info(f"Enregistrement(s) inséré(s) avec succès, ID: {id_line}")
        except Exception as e:
            self.logger.error(f"Erreur lors de l'insertion dans {table}: {e}")
            raise
        return ids
