"""
Module google_calendar pour l'interaction avec l'API Google Calendar.

Ce module fournit la classe `GoogleCalendarConnector`, permettant :
- d'établir une connexion à l'API Google Calendar ;
- de récupérer les événements des calendriers configurés ;
- et de sauvegarder ces événements dans un fichier CSV.
"""
from __future__ import annotations

import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import polars as pl
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient import discovery

if TYPE_CHECKING:
    from .logger import Logger

from .timer import timer


class GoogleCalendarConnector:
    """
    Classe pour gérer la connexion et l'interaction avec l'API Google Calendar.

    Cette classe permet :
    - d'établir la connexion à l'API à l'aide d'identifiants OAuth2 ;
    - de récupérer les événements des calendriers configurés ;
    - et d'enregistrer ces événements dans un fichier CSV via Polars.

    :param dictionnary: Un dictionnaire contenant les paramètres requis
                        (calendriers, fichiers de jeton et d'identifiants, etc.).
    :param logger: Une instance de logger utilisée pour journaliser les opérations.
    """

    def __init__(self, dictionnary: dict, logger: Logger) -> None:
        """
        Classe pour se connecter à l'API Google Calendar et récupérer des événements de calendrier.

        :param dictionnary: Un dictionnaire contenant les paramètres requis (comme les calendriers des collègues).
        :param logger: Un logger pour gérer les logs d'actions de la classe.
        """
        self.logger = logger
        self.scopes = dictionnary.get("scopes", ["https://www.googleapis.com/auth/calendar.readonly"])
        self.calendar_ids = dictionnary["calendar_ids"]
        self.token_file = dictionnary.get("token_file", "token.json")
        self.credentials_file = dictionnary.get("credentials_file", "credentials.json")
        self.service = None

    def __str__(self) -> str:
        """Retourne une représentation textuelle de l'objet GoogleCalendarConnector."""
        return f"Connexion Google Calendar avec les calendriers: {', '.join(self.calendar_ids)}"

    @timer
    def connect(self) -> None:
        """Etablit la connexion à l'API Google Calendar."""
        try:
            self.logger.info("Tentative de connexion à Google Calendar...")
            creds = None
            token_path = Path(self.token_file)
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.scopes)
                    creds = flow.run_local_server(port=0)
                with token_path.open("w") as token:
                    token.write(creds.to_json())
            self.service = discovery.build("calendar", "v3", credentials=creds)
            self.logger.info("Connexion à Google Calendar réussie.")
        except Exception as e:
            self.logger.error(f"Erreur lors de la connexion à Google Calendar: {e}")
            raise

    @timer
    def get_events(self, max_results: int=10) -> dict:
        """
        Récupère les événelents des calendriers des collègues spécifiés.

        :param max_results: Le nombre maximal d'événements à récupérer par calendrier
        :return: Un dictionnaire des événements pour chaque calendrier
        """
        try:
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            events_data = {}
            for calendar_id in self.calendar_ids:
                self.logger.info(f"Récupération des événements du calendrier: {calendar_id}")
                events_results = self.service.events().list(
                    calendarId=calendar_id,
                    timeMin=now,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                ).execute()
                events = events_results.get("items", [])
                events_data[calendar_id] = events
                self.logger.info(f"{len(events)} événement(s) récupéré(s) pour {calendar_id}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des événements: {e}")
            raise
        return events_data

    @timer
    def save_events_to_csv(self, events_data: dict, csv_filename: str="calendar_events.csv") -> None:
        """
        Enregistre les événements dans un fichier csv en utilisant polars.

        :param events_data: Un dictionnaire contenant les événements par calendrier
        :param csv_filename: Le nom du csv
        """
        try:
            self.logger.info(f"Sauvegarde des événements dans le fichier CSV: {csv_filename}")
            data = {
                "Event Date": [],
                "Event Summary": [],
                "Owner Email": [],
                "Calendar Name": [],
            }
            for events in events_data.values():
                for event in events:
                    data["Event Date"].append(event["start"].get("dateTime", event["start"].get("date")))
                    data["Event Summary"].append(event.get("summary", "No Summary"))
                    data["Owner Email"].append(event.get("organizer", {}).get("email", "No Email Provided"))
                    data["Calendar Name"].append(event.get("organizer", {}).get("displayName", "No Name Provided"))
            df = pl.DataFrame(data)
            df.write_csv(csv_filename)
            self.logger.info(f"Les événements ont été sauvegardés dans {csv_filename}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde des événements dans le CSV: {e}")
            raise
