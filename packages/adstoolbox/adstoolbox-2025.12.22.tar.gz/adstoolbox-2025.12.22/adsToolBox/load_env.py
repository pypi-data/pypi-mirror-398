"""
Module de gestion et de chargement automatique des fichiers .env.

Ce module fournit la classe `Env`, qui recherche et charge un fichier .env
à partir du répertoire courant ou de ses répertoires parents,
afin de centraliser la configuration des variables d'environnement.
"""
from __future__ import annotations

import inspect
import os
from pathlib import Path
from typing import TYPE_CHECKING

import dotenv

if TYPE_CHECKING:
    from .logger import Logger


class Env:
    """Classe responsable de la détection et du chargement du fichier .env."""

    def __init__(self, logger: Logger, file: str | None = None) -> None:
        """
        Recherche et charge un fichier .env.

        - Si 'file' est fourni : charge ce fichier s'il existe.
        - Sinon : cherche automatiquement le .env le plus proche en remontant
          depuis le dossier du script exécuté.
        """
        self.logger = logger
        loaded = False

        if file:
            path = Path(file)
            if path.is_file():
                dotenv_file = path.resolve()
                dotenv.load_dotenv(dotenv_file, override=True)
                self.logger.debug(f"Fichier .env spécifié trouvé et chargé : {dotenv_file}")
                loaded = True

        if not loaded:
            caller_file = Path(inspect.stack()[1].filename).resolve()
            caller_dir = caller_file.parent
            dotenv_file = self._find_env_upwards(caller_dir)
            if dotenv_file:
                dotenv.load_dotenv(dotenv_file, override=True)
                self.logger.debug(f"Fichier .env trouvé automatiquement : {dotenv_file}")
            else:
                self.logger.warning("Aucun fichier .env trouvé en remontant depuis le script.")
                self.logger.warning("Veuillez créer un fichier .env à la racine du projet ou en spécifier un manuellement.")

        for key, value in os.environ.items():
            setattr(self, key, value)

    def _find_env_upwards(self, start_path: Path) -> str | None:
        """Recherche récursivement un fichier .env en remontant les dossiers."""
        current_dir = start_path.resolve()
        while True:
            self.logger.debug(f"Recherche d'un fichier .env dans : {current_dir}")
            candidate = current_dir / ".env"
            if candidate.is_file():
                return str(candidate)
            parent_dir = current_dir.parent
            if parent_dir == current_dir:
                break
            current_dir = parent_dir
        return None
