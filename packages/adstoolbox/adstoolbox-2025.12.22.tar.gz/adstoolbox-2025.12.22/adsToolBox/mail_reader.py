"""
Module mail_reader.

Contient la classe MailReader pour se connecter à un serveur IMAP et lire, filtrer et gérer les emails.
"""
from __future__ import annotations

import email
import imaplib
import mimetypes
import re
from email import policy
from http import HTTPStatus
from typing import TYPE_CHECKING

import chardet
import requests

if TYPE_CHECKING:
    from mailbox import Message

    from .logger import Logger

class MailReader:
    """Classe pour se connecter à un serveur IMAP et lire, filtrer et gérer les emails."""

    def __init__(self, configuration: dict, logger: Logger, auth_mode: str) -> None:
        """
        Instancie la classe MailReader.

        :param configuration: Un dictionnaire contenant tous les paramètres nécéssaires pour lancer une connexion imap
        :param logger: Un logger ads qui va gérer les logs des actions de la classe
        :param auth_mode: Le mode d'authentification 'oauth2' ou 'credentials'
        """
        self.logger = logger
        self.__url=configuration.get("url")
        self.__clientId=configuration.get("clientId")
        self.__clientSecret=configuration.get("clientSecret")
        self.__email=configuration.get("email")
        self.__emailFrom=configuration.get("emailFrom")
        self.__subject=configuration.get("subject")
        self.__scope=configuration.get("scope")
        self.__server=configuration.get("server")
        self.__login=configuration.get("login")
        self.__password=configuration.get("password")
        self.__token=None
        self.__connection=None
        if auth_mode == "oauth2":
            self.__connect_with_token()
        elif auth_mode == "credentials":
            self.__connect_with_credentials()
        else:
            msg = f"Le mode d'authentification {auth_mode} n'est pas reconnu. Utiliser 'oauth2' ou 'credentials'"
            self.logger.error(msg)
            raise ValueError(msg)

    def __connect_with_credentials(self) -> None:
        """Se connecte à un server imap et récupère le token."""
        self.logger.info("Tentative de connexion avec le serveur mail.")
        try:
            imap_conn = imaplib.IMAP4_SSL(self.__server)
            imap_conn.login(self.__login, self.__password)
            self.__connection = imap_conn
            self.logger.info("Connexion établie.")
        except Exception as e:
            self.logger.error(f"La tentative de connexion a échoué: {e!s}")
            raise

    def __connect_with_token(self) -> None:
        """Se connecte à un server imap et récupère le token."""
        self.logger.info("Tentative de connexion avec le server mail.")
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.__clientId,
            "client_secret": self.__clientSecret,
            "scope": self.__scope,
        }
        response = requests.post(self.__url, data=payload, timeout=(5, 15))
        if response.status_code == HTTPStatus.OK:
            self.logger.info("Connexion établie")
            self.logger.debug("Tentative de récupération du token.")
            token_data = response.json()
            if "access_token" in token_data:
                self.logger.debug("Token récupéré avec succès !")
                self.__token = token_data["access_token"]
                imap_conn = imaplib.IMAP4_SSL(self.__server)
                auth_string = f"user={self.__email}\1auth=Bearer {self.__token}\1\1"
                imap_conn.authenticate("XOAUTH2", lambda _: auth_string.encode("utf-8"))
                self.__connection = imap_conn
            else:
                msg = f"Le token n'a pas pu être récupéré {response.reason}."
                self.logger.error(msg)
                raise RuntimeError(msg)

        else:
            msg = f"La tentative de connexion a échoué: {response.reason}"
            self.logger.error(msg)
            raise RuntimeError(msg)

    def mark_as_seen(self, e_id: str) -> None:
        """Marque le mail identifié comme lu."""
        imap_conn: imaplib.IMAP4_SSL = self.__connection
        self.logger.info(f"Changement du flag du mail {e_id} à 'Seen'.")
        try:
            imap_conn.store(e_id, "+FLAGS", "\\Seen")
        except Exception as e:
            self.logger.error(f"Le changement de flag vers 'Seen' du mail {e_id} a échoué: {e!s}.")
            raise

    def mark_as_un_seen(self, e_id: str) -> None:
        """Marque le mail identifié comme non-lu."""
        imap_conn: imaplib.IMAP4_SSL = self.__connection
        self.logger.info(f"Changement du flag du mail {e_id} à 'UnSeen'.")
        try:
            imap_conn.store(e_id, "-FLAGS", "\\Seen")
        except Exception as e:
            self.logger.error(f"Le changement de flag vers 'UnSeen' du mail {e_id} a échoué: {e!s}.")
            raise

    def delete(self, e_id: str) -> None:
        """Supprime l'email correspondant à l'identifiant."""
        imap_conn: imaplib.IMAP4_SSL = self.__connection
        self.logger.info(f"Suppression du mail {e_id}.")
        try:
            imap_conn.store(e_id, "+FLAGS", "\\Deleted")
        except Exception as e:
            self.logger.error(f"La suppression du mail {e_id} a échoué: {e!s}.")
            raise

    def _validate_flag(self, flag: str) -> None:
        valid_flags = {
            "ALL", "SEEN", "UNSEEN", "FLAGGED", "UNFLAGGED", "ANSWERED", "UNANSWERED", "DELETED", "UNDELETED", "DRAFT",
        }
        if flag.upper() not in valid_flags:
            msg = f"Flag incorrect: {sorted(valid_flags)}"
            self.logger.error(msg)
            raise ValueError(msg)

    def _search_emails(
            self,
            imap_conn: imaplib.IMAP4_SSL,
            flag: str,
            email_from: str | None,
            charset: str | None,
    ) -> tuple[str, list[str]]:
        self.logger.info("Tentative de récupération des mails.")
        if email_from:
            return imap_conn.search(charset, f'{flag} FROM "{email_from}"')
        return imap_conn.search(charset, flag)

    def _filter_by_subject(self, imap_conn: imaplib.IMAP4_SSL, email_ids: list[str], email_subject: str) -> list[str]:
        matching_emails: list[str] = []
        for e_id in email_ids:
            status, msg_data = imap_conn.fetch(e_id, "(RFC822)")
            if status != "OK":
                msg = f"Erreur lors du filtrage par sujet, {status, email_ids[0]}"
                self.logger.error(msg)
                raise RuntimeError(msg)
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = msg.get("Subject", "")
                    if re.search(email_subject, subject, re.IGNORECASE):
                        matching_emails.append(e_id)
        return matching_emails

    def get_email(
        self,
        mailbox: str = "INBOX",
        email_from: str | None = None,
        email_subject: str | None = None,
        flag: str = "UnSeen",
        charset: str | None = None,
        *,
        readonly: bool = False,
    ) -> list[str]:
        """
        Récupère les mails selon les paramètres renseignés.

        :param mailbox: Dossier IMAP à lire (ex: INBOX)
        :param email_from: Filtrer sur l'expéditeur
        :param email_subject: Filtrer sur le sujet
        :param flag: Critère IMAP (ALL, SEEN, UNSEEN, etc.)
        :param charset: Jeu de caractères pour la recherche (ex: UTF-8)
        :param readonly: Si False, les mails seront marqués comme lus
        :return: Liste des identifiants d'emails correspondants
        """
        self._validate_flag(flag)
        imap_conn = self.__connection
        imap_conn.select(mailbox.upper(), readonly=readonly)
        status, email_ids = self._search_emails(imap_conn, flag, email_from, charset)
        if status != "OK":
            msg = f"Erreur lors de la récupération des emails, {status, email_ids[0]}"
            self.logger.error(msg)
            raise RuntimeError(msg)
        if not email_ids[0]:
            self.logger.warning("Aucun email n'a été trouvé.")
            return []
        email_ids = email_ids[0].split()
        if email_subject:
            matching_emails = self._filter_by_subject(imap_conn, email_ids, email_subject)
        else:
            matching_emails = email_ids
        self.logger.info(f"{len(email_ids)} mail(s) trouvé(s)")
        return matching_emails

    def _decode_email_body(self, msg: Message) -> str:
        """Extrait et décode le texte de l'email."""
        body = ""
        for part in msg.walk():
            if part.get_content_type() in ["text/plain", "text/html"]:
                raw = part.get_payload(decode=True)
                encoding = chardet.detect(raw)["encoding"] or part.get_content_charset() or "utf-8"
                self.logger.debug(f"Encodage détecté: {encoding} pour {part.get_content_type()}")
                try:
                    body = raw.decode(encoding, errors="replace")
                except LookupError:
                    body = raw.decode("iso-8859-1", errors="replace")
        return body

    def __get_attachment(self, msg: Message) -> list[dict]:
        """Récupère les pièces jointes d'un email et renvoie une liste de dictionnaires."""
        def _decode_text(raw: bytes, filename: str) -> tuple[str, str]:
            """Décode le contenu texte et renvoie (content, encoding)."""
            encoding = chardet.detect(raw)["encoding"] or "uft-8"
            try:
                return raw.decode(encoding), encoding
            except UnicodeDecodeError:
                self.logger.error(f"Échec du décodage avec {encoding} pour {filename}. Enregistrement en binaire.")
                return raw.decode("iso-8859-1", errors="replace"), "iso-8859-1"

        def _process_part(part: Message) -> dict | None:
            if part.get_content_disposition() != "attachment":
                return None
            filename = part.get_filename()
            if not filename:
                return None
            self.logger.info(f"Téléchargement de la pièce jointe: {filename}.")
            raw = part.get_payload(decode=True)
            mime_type, _ = mimetypes.guess_type(filename)
            is_text = mime_type and mime_type.startswith("text")
            content: bytes | str = raw
            encoding: str | None = None
            binary = not is_text
            if is_text:
                content, encoding = _decode_text(raw, filename)
                binary = False
            return {
                "filename": filename,
                "content": content,
                "binary": binary,
                "encoding": encoding if not binary else "binary",
            }
        attachments = [att for part in msg.walk() if (att := _process_part(part))]
        if self.logger and not attachments:
            self.logger.info("Aucune pièce jointe n'a été trouvée.")
        return attachments

    def read_email(self, email_id: str, *, get_attachment: bool=False) -> dict:
        """Lit un email à partir de son ID et retourne son contenu."""
        self.logger.info(f"Tentative de lecture de l'email {email_id}.")
        imap_conn = self.__connection
        status, msg_data = imap_conn.fetch(email_id, "(RFC822)")
        if status != "OK":
            msg = f"Erreur lors de la lecture de l'email {email_id}."
            self.logger.error(msg)
            raise RuntimeError(msg)
        if not msg_data[0]:
            self.logger.warning(f"Le contenu du mail {email_id} est vide.")
            return {"message": ""}
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email, policy=policy.default)
        self.logger.info(f"Contenu de l'email {email_id} correctement lu.")
        message = self._decode_email_body(msg)
        if not get_attachment:
            return {"message": message}
        attachments = self.__get_attachment(msg)
        return {"message": message, "attachment": attachments}

    def logout(self) -> None:
        """Ferme la connexion avec le serveur mail."""
        self.__connection.logout()
