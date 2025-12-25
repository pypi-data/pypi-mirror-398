"""
Module `git_handler` pour gérer les dépôts Git et les environnements virtuels.

Ce module fournit la classe `GitHandler` permettant de :
- Cloner ou mettre à jour des dépôts GitHub à l'aide d'un token d'accès.
- Vérifier les permissions d'accès à un chemin donné.
- Créer et configurer un environnement virtuel Python dans un dépôt, avec installation
  des dépendances et droits d'exécution sur un script de lancement.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from git import Repo
from github import Github

if TYPE_CHECKING:
    from .logger import Logger
from .timer import timer


class GitHandler:
    """
    Classe pour gérer les dépôts GitHub et les environnements virtuels Python.

    Attributs:
        token (str): Token d'accès GitHub utilisé pour l'authentification.
        github (Github): Instance de la bibliothèque PyGithub pour les interactions avec GitHub.
        logger (Logger): Objet Logger pour la journalisation.
    """

    def __init__(self, token: str, logger: Logger) -> None:
        """
        Initialise le gestionnaire GitHandler avec un token GitHub et un logger.

        :param token: Token d'accès GitHub.
        :param logger: Objet Logger pour journaliser les actions et les erreurs.
        """
        self.token = token
        self.github = Github(token)
        self.logger = logger

    def check_permissions(self, path: str) -> None:
        """Vérifie que le script dispose des permissions nécessaires sur le chemin spécifié."""
        if not os.access(path, os.R_OK):
            msg = f"Le script n'a pas la permission de lecture sur le chemin: {path}"
            raise PermissionError(msg)

    @timer
    def clone_or_update(self, destination_path: str, repository: str, branch: str | None = None) -> None:
        """Clone le repo s'il existe pas localement, sinon pull la dernière version."""
        self.logger.info(f"Connexion au repo {repository}")
        url = f"https://{self.token}@github.com/{repository}.git"
        try:
            path = Path(destination_path)
            if path.exists():
                self.check_permissions(destination_path)
                repo = Repo(destination_path)

                self.logger.debug("Mise à jour du remote origin avec le token.")
                repo.remotes.origin.set_url(url)

                repo.remotes.origin.fetch()
                if branch:
                    self.logger.debug(f"Changement de branche : {branch}")
                    repo.git.checkout(branch)
                repo.remotes.origin.pull()
                self.logger.info(f"Le repo {repository} a été mis à jour.")
            else:
                self.logger.info(f"Clonage du repo {repository} dans {destination_path}...")
                if branch:
                    Repo.clone_from(url, destination_path, branch=branch)
                else:
                    Repo.clone_from(url, destination_path)
                self.logger.info(f"Le repo {repository} a été cloné avec succès.")
        except Exception as e:
            self.logger.error(f"Erreur lors du clonage du repo {repository}: {e}")
            raise

    @timer
    def setup_virtualenv(self, repo_path: str) -> None:
        """Crée et installe d'un environnement virtuel dans le repo."""
        repo = Path(repo_path)
        venv_path = repo / "venv"
        requirements_path = repo / "requirements.txt"
        launch_path = repo / "launch.sh"

        self.logger.info(f"Création de l'environnement virtuel dans {venv_path}...")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True) # noqa: S603
        except Exception as e:
            self.logger.error(f"Erreur lors de la création du venv: {e}")
            raise
        if requirements_path.exists():
            self.logger.info("Installation des dépendances à partir de requirements.txt...")
            pip_executable = venv_path / (Path("Scripts") / "pip.exe" if os.name == "nt" else Path("bin") / "pip")
            subprocess.run([str(pip_executable), "install", "-r", str(requirements_path)], check=True) # noqa: S603
        else:
            self.logger.warning("Aucun fichier requirements.txt trouvé, installation ignorée.")

        # Attribution des droits d exécution au script launch.sh (si présent)
        if launch_path.exists():
            self.logger.info("Attribution des droits d'exécution sur launch.sh...")
            try:
                launch_path.chmod(0o755)
                self.logger.info("Droits d'exécution appliqués avec succès sur launch.sh.")
            except PermissionError as e:
                self.logger.error(f"Impossible de modifier les permissions de launch.sh : {e}")
        else:
            self.logger.warning("Aucun fichier launch.sh trouvé dans le dépôt.")
        self.logger.info("Environnement virtuel configuré avec succès.")
