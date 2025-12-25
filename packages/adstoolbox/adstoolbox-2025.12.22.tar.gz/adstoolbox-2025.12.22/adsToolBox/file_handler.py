"""
Module file_handler.

Ce module fournit la classe `FileHandler` pour gérer les opérations sur les fichiers
en local et via des partages SMB ou FTP. Il inclut la lecture et l'écriture en batchs,
la vérification de l'existence de fichiers et de dossiers, la suppression et la création
de fichiers vides, ainsi que le calcul de la taille des fichiers et des répertoires.
"""
from __future__ import annotations

import functools
import hashlib
import time
import timeit
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Callable, TypeVar
from uuid import uuid4

try:
    from typing import ParamSpec  # Python ≥ 3.10
except ImportError:
    from typing_extensions import ParamSpec  # Python 3.9

import fsspec

from adsToolBox import DbMssql, DbMysql, DbPgsql

from .timer import get_timer, timer

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from .data_factory import DataFactory
    from .logger import Logger

OCTETS_PAR_KO = 1024.0
ASCII_MAX = 127

P = ParamSpec("P")
R = TypeVar("R")

def retry_on_failure(func: Callable) -> Callable:
    """
    Décorateur qui réessaie une méthode plusieurs fois en cas d'erreur.

    La classe appelante doit définir :
        - retry_count (int)
        - retry_delay (float)
        - logger (Logger ads)
    """
    @functools.wraps(func)
    def wrapper(self: FileHandler, *args: P.args, **kwargs: P.kwargs) -> R:
        inf = self.retry_count == 0
        max_att = float("inf") if inf else self.retry_count
        att = 0
        while att < max_att:
            att += 1
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                self.logger.warning(
                    f"Tentative {att}/{self.retry_count} échouée : {e}",
                )
                if not inf and att >= self.retry_count:
                    self.logger.error(
                        f"Échec définitif après {self.retry_count} tentatives ({int(self.retry_count * self.retry_delay)}s).",
                    )
                    raise
                time.sleep(self.retry_delay)
        msg = "Erreur interne de retry_on_failure."
        raise RuntimeError(msg)
    return wrapper

class FileHandler:
    """
    Gestionnaire de fichiers local et distant.

    Cette classe permet de manipuler des fichiers et des répertoires en supportant les opérations suivantes :

    - Lecture de fichiers en batchs (`read_file`)
    - Écriture de fichiers en batchs (`write_file`)
    - Transfert de fichier entre différents systèmes ('local', 'SMB', 'Azure', 'FTP', etc)
    - Vérification après transfert (tailles ou checksum via MD5)
    - Vérification de l'existence de fichiers et dossiers (`file_exists`, `directory_exists`)
    - Suppression et création de fichiers (`remove_file`, `create_empty_file`)
    - Nettoyage de texte (`clean_text`)
    - Calcul de la taille d'un répertoire (`_get_dir_size`)
    - Collecte et traitement des fichiers selon un filtre (`_collect_files`, `_process_files`, `disk_check`)
    - Attente de la présence d'un fichier avec retry (`wait_for_file`)

    Attributs :
        logger (Logger): Système de log injecté.
        fs (fsspec.AbstractFileSystem): Instance de système de fichiers (local, smb, sftp, etc.).
        batch_size (int): Taille maximale des chunks pour lecture/écriture.
        retry_count (int): Nombre de tentatives avant échec.
        retry_delay (float): Délai (en secondes) entre les tentatives.
    """

    def __init__(
            self,
            logger: Logger,
            fs_url: str | None = None,
            fs_kwargs: dict | None = None,
            batch_size: int = 4096,
            retry_count: int = 3,
            retry_delay: float = 2.0,
    )-> None:
        """
        Initialise le gestionnaire de fichiers universel basé sur fsspec.

        :param logger: Instance de Logger.
        :param fs_url: URL fsspec (ex: 'file:///', 'smb://server/share', 'sftp://user:pass@host/').
                       Si None, le backend local est utilisé.
        :param fs_kwargs: Paramètres optionnels pour fsspec (ex: credentials, host, port...).
        :param batch_size: Taille des chunks de lecture/écriture.
        :param retry_count: Nombre de tentatives avant échec.
        :param retry_delay: Délai entre tentatives (en secondes).
        """
        self.logger = logger
        self.batch_size = batch_size
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self._set_connection(fs_url or "file:///", fs_kwargs or {})

    @retry_on_failure
    def _set_connection(self, fs_url: str, fs_kwargs: dict) -> None:
        self.fs, self.root_url = fsspec.core.url_to_fs(fs_url, **fs_kwargs)
        self.logger.debug(f"FileHandler initialisé avec backend '{self.fs.protocol}' (url={fs_url})")

    def set_retry_params(self, retry_count: int, retry_delay: float) -> None:
        """Change les paramètres de nombre de retry et de délai."""
        self.retry_count = retry_count
        self.retry_delay = retry_delay

    @retry_on_failure
    def read_file(self, file_path: str, mode: str="rb", encoding: str | None = None) -> Generator[str | bytes, None, None]:
        """
        Lit un fichier distant ou local via fsspec, en streaming par blocs.

        Supporte ces modes : 'r', 'rb'.
        """
        timer_start = timeit.default_timer()
        try:
            with self.fs.open(file_path, mode=mode, encoding=encoding) as f:
                while True:
                    chunk = f.read(self.batch_size)
                    if not chunk:
                        break
                    yield chunk
            self.logger.info(f"Succès: lecture du fichier '{file_path}' ({self.fs.protocol})")
        except Exception as e:
            self.logger.error(f"Erreur lors de la lecture du fichier '{file_path}' via {self.fs.protocol}: {e}")
            raise
        finally:
            if get_timer():
                elapsed_time = timeit.default_timer() - timer_start
                self.logger.info(f"Temps d'exécution de read_file: {elapsed_time:.4f} secondes.")

    @retry_on_failure
    @timer
    def write_file(self, file_path: str, content: Iterable[str | bytes], mode: str="wb") -> None: # noqa: PLR0912, C901
        """
        Écrit du contenu dans un fichier local ou distant via fsspec.

        Supporte ces modes : 'w', 'wb', 'a', 'ab', 'x', 'xb'.
        """
        encoding = "utf-8" if "b" not in mode else None
        is_append = "a" in mode
        is_exclusive = "x" in mode
        sep = "/" if "/" in file_path else "\\"
        dir_part, _, _ = file_path.rpartition(sep)
        if is_exclusive:
            if self.fs.exists(file_path):
                msg = f"Le fichier '{file_path}' existe déjà (mode 'x')."
                self.logger.error(msg)
                raise FileExistsError(msg)
            if self.fs.protocol in ("abfs", "az", "azure", "azblob"):
                mode = "wb" if "b" in mode else "w"
        if is_append:
            target_path = file_path
            if self.fs.protocol in ("abfs", "az", "azure", "azblob") and self.fs.exists(file_path):
                self.logger.warning("Le fichier existe déjà, attention il faut que ce soit un appendblob.")
            elif self.fs.protocol == "ftp":
                self.logger.warning("Pas de mode append pour FTP.")
        else:
            temp_filename = f"tmp_{uuid4().hex}"
            target_path = f"{dir_part}{sep}{temp_filename}" if dir_part else temp_filename
        try:
            with self.fs.open(target_path, mode=mode, encoding=encoding) as f:
                for chunk in content:
                    data = chunk.encode(encoding or "utf-8") if isinstance(chunk, str) and "b" in mode else chunk
                    for i in range(0, len(data), self.batch_size):
                        f.write(data[i:i + self.batch_size])
            if not is_append:
                if self.fs.exists(file_path):
                    self.fs.rm(file_path)
                self.fs.mv(target_path, file_path)
            self.logger.info(f"Succès: contenu écrit dans '{file_path}' ({self.fs.protocol})")
        except Exception as e:
            if not is_append and self.fs.exists(target_path):
                try:
                    self.fs.rm(target_path)
                    self.logger.warning(f"Fichier temporaire supprimé après erreur: {target_path}.")
                except Exception as cleanup_error: # noqa: BLE001
                    self.logger.warning(f"Impossible de supprimer le fichier temporaire: {target_path}: {cleanup_error}.")
            self.logger.error(f"Erreur lors de l'écriture du fichier '{file_path}': {e}")
            raise

    def _read_with_checksum(self, path: str, mode: str="rb") -> tuple[Generator[bytes, None, None], Callable[[], str]]:
        """Lit un fichier en streaming et calcule le checksum en même temps."""
        h = hashlib.new("md5") # noqa: S324
        def gen() -> Generator[bytes, None, None]:
            with self.fs.open(path, mode=mode) as f:
                while True:
                    chunk = f.read(self.batch_size)
                    if not chunk:
                        break
                    h.update(chunk)
                    yield chunk
        def get_checksum() -> str:
            return h.hexdigest()
        return gen(), get_checksum

    def write_with_checksum(self, file_path: str, content: Iterable[bytes], mode: str= "wb") -> str: # noqa: C901
        """Écrit un fichier en streaming et calcule le checksum en même temps."""
        h = hashlib.new("md5") # noqa: S324
        is_append = "a" in mode
        is_exclusive = "x" in mode
        sep = "/" if "/" in file_path else "\\"
        dir_part, _, _ = file_path.rpartition(sep)
        if is_exclusive:
            if self.fs.exists(file_path):
                msg = f"Le fichier '{file_path}' existe déjà (mode 'x')."
                self.logger.error(msg)
                raise FileExistsError(msg)
            if self.fs.protocol in ("abfs", "az", "azure", "azblob"):
                mode = "wb" if "b" in mode else "w"
        if is_append:
            target_path = file_path
        else:
            temp_filename = f"tmp_{uuid4().hex}"
            target_path = f"{dir_part}{sep}{temp_filename}" if dir_part else temp_filename
        try:
            with self.fs.open(target_path, mode=mode) as f:
                for chunk in content:
                    h.update(chunk)
                    for i in range(0, len(chunk), self.batch_size):
                        f.write(chunk[i:i + self.batch_size])
            if not is_append:
                if self.fs.exists(file_path):
                    self.fs.rm(file_path)
                self.fs.mv(target_path, file_path)
        except Exception as e:
            if not is_append and self.fs.exists(target_path):
                try:
                    self.fs.rm(target_path)
                    self.logger.warning(f"Fichier temporaire supprimé après erreur: {target_path}.")
                except Exception as cleanup_error: # noqa: BLE001
                    self.logger.warning(f"Impossible de supprimer le fichier temporaire: {target_path}: {cleanup_error}.")
            self.logger.error(f"Erreur lors de l'écriture du fichier '{file_path}': {e}")
            raise
        return h.hexdigest()

    @timer
    @retry_on_failure
    def transfer_file(
            self,
            src_path: str,
            dst_path: str,
            dst_file_handler: FileHandler | None = None, # dst_file_handler doit se trouver ici si on veut garder sa valeur None par défaut
            mode: str="w",
            *, fastcheck: bool = True,
    ) -> bool:
        """
        Copie un fichier puis vérifie l'intégrité.

        Les modes disponibles sont 'w' qui écrase la destination, 'a' qui y ajoute le contenu et 'x' qui lève une erreur
        si la destination existe déjà.
        """ # noqa: D401
        dst_file_handler = dst_file_handler or self
        if "a" in mode:
            msg = "Le mode 'append' n'est pas implémenté dans file_transfer."
            raise NotImplementedError(msg)
        if "b" not in mode:
            mode += "b"
        self.logger.debug(f"Transfert de {src_path} vers {dst_path} (fastcheck={fastcheck}).")
        log_level, base_level = self.logger.log_level_global, self.logger.log_level_base
        try:
            if fastcheck:
                self.logger.disable()
                dst_file_handler.write_file(dst_path, self.read_file(src_path), mode)
                self.logger.enable(log_level, base_level)
                src_size = self.fs.info(src_path)["size"]
                dst_size = dst_file_handler.fs.info(dst_path)["size"]
                if src_size != dst_size:
                    self.logger.error(f"Transfert KO (fastcheck) - tailles différentes: {src_size} != {dst_size}")
                    return False
                self.logger.info(f"Transfert OK (fastcheck) - tailles identiques: {src_size} != {dst_size}")
                return True
            content, get_checksum_src = self._read_with_checksum(src_path)
            checksum_dst = dst_file_handler.write_with_checksum(dst_path, content, mode)
            checksum_src = get_checksum_src()
            if checksum_src != checksum_dst:
                self.logger.error(f"Transfert KO - checksum différent: {checksum_src} != {checksum_dst}")
                return False
            self.logger.info(f"Transfert OK - checksum identique: {checksum_src} != {checksum_dst}")
        except Exception as e:
            self.logger.enable(log_level, base_level)
            self.logger.error(f"Erreur lors du transfert {src_path} -> {dst_path}: {e}")
            raise
        return True

    @retry_on_failure
    @timer
    def list_dir(self, dir_path: str) -> list[str]:
        """Liste le contenu d'un dossier."""  # noqa: D401
        try:
            entries = self.fs.ls(dir_path, detail=False)
            return [Path(e).name for e in entries]
        except Exception as e:
            self.logger.error(f"Erreur lors du listage de '{dir_path}': {e}")
            raise

    @retry_on_failure
    @timer
    def file_exists(self, file_path: str) -> bool:
        """Vérifie si un fichier existe."""
        try:
            return self.fs.exists(file_path) and self.fs.isfile(file_path)
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification du fichier '{file_path}': {e}")
            raise

    @retry_on_failure
    @timer
    def directory_exists(self, dir_path: str) -> bool:
        """Vérifie si un répertoire existe."""
        try:
            return self.fs.exists(dir_path) and self.fs.isdir(dir_path)
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification du dossier '{dir_path}': {e}")
            raise

    @retry_on_failure
    @timer
    def remove_file(self, file_path: str) -> bool:
        """Supprime un fichier."""
        log_level, base_level = self.logger.disable()
        try:
            if self.file_exists(file_path):
                self.logger.enable(log_level, base_level)
                self.fs.rm(file_path)
                self.logger.info(f"Fichier supprimé: '{file_path}'")
                return True
        except Exception as e:
            self.logger.enable(log_level, base_level)
            self.logger.error(f"Erreur lors de la suppression de '{file_path}': {e}")
            raise
        self.logger.enable(log_level, base_level)
        self.logger.warning(f"Tentative de suppression d'un fichier inexistant: '{file_path}'")
        return False

    @retry_on_failure
    @timer
    def create_empty_file(self, file_path: str) -> None:
        """Crée un fichier vide au chemin spécifié (ou tronque s'il existe)."""
        try:
            existed = self.fs.exists(file_path)
            with self.fs.open(file_path, mode="wb"):
                pass
            if existed:
                self.logger.info(f"Fichier tronqué: '{file_path}'")
            else:
                self.logger.info(f"Fichier vide créé: '{file_path}'")
        except Exception as e:
            self.logger.error(f"Erreur lors de la création du fichier vide '{file_path}': {e}")
            raise

    def _convertir_octets(self, taille_octets: int) -> tuple[float, str]:
        """Convertit une taille en octets dans une unité lisible."""
        for unite in ["octets", "Ko", "Mo", "Go", "To"]:
            if taille_octets < OCTETS_PAR_KO:
                return round(taille_octets, 2), unite # noqa: RUF057 indique que c'est un entier mais pas forcément
            taille_octets /= OCTETS_PAR_KO
        return round(taille_octets, 2), "To"

    def _ensure_table_exists(self, db: DataFactory, schema: str, table: str) -> None:
        """Crée la table cible si elle n'existe pas encore."""
        cols = ["tenantname", "date", "taille", "unite", "fichier"]
        cols_def = ["VARCHAR(255)", "TIMESTAMP", "FLOAT", "VARCHAR(10)", "VARCHAR(255)"]
        if isinstance(db, DbMssql):
            cols_def[1] = "DATETIME2"
        columns = ", ".join(f"{col} {typ}" for col, typ in zip(cols, cols_def))
        full_table = f"{schema}.{table}" if schema else table
        if isinstance(db, (DbMysql, DbPgsql)):
            query = f"CREATE TABLE IF NOT EXISTS {full_table} ({columns});"
        elif isinstance(db, DbMssql):
            query = f"""
            IF OBJECT_ID('{full_table}', 'U') IS NULL
            CREATE TABLE {full_table} ({columns});
            """
        else:
            msg = f"Type de base de données non pris en charge: {type(db).__name__}"
            raise TypeError(msg)
        db.sql_exec(query)

    def _collect_files(self, base_path: str, file_filter: str) -> list[str]:
        """Retourne la liste complète des fichiers correspondant au filtre."""
        files = []
        def _walk(path: str) -> None:
            self.logger.debug(f"[COLLECT] Exploration du dossier : {path}")
            try:
                entries = self.fs.ls(path)
                for entry in entries:
                    fp = entry["name"] if isinstance(entry, dict) else entry
                    self.logger.debug(f"[COLLECT] Entrée trouvée : {fp}")
                    if self.fs.isfile(fp):
                        if file_filter in fp:
                            files.append(fp)
                        else:
                            self.logger.debug(f"[COLLECT] Fichier ignoré: {fp}")
                    elif self.fs.isdir(fp):
                        self.logger.debug(f"[COLLECT] Répertoire à explorer : {fp}")
                        _walk(fp)
            except Exception as e:
                self.logger.error(f"Erreur lors de la collecte des fichiers dans {path}: {e}")
                raise
        _walk(base_path)
        return files

    def _process_files(
            self,
            db: DataFactory,
            schema: str,
            table: str,
            fichiers: list[str],
            tenant_name: str,
            date: str,
            base_path: str,
    ) -> None:
        """Traite les fichiers, calcule les tailles et insère les résultats dans la base."""
        total_size = 0
        bulk_data = []
        cols = ["tenantname", "date", "taille", "unite", "fichier"]
        try:
            for fichier in fichiers:
                info = self.fs.info(fichier)
                size = int(info.get("size", info.get("Size", 0)))
                total_size += size
                value, unit = self._convertir_octets(size)
                bulk_data.append([tenant_name, date, str(value), unit, fichier])
        except Exception as e:
            self.logger.error(f"Erreur sur le fichier '{fichier}': {e}")
            raise
        if bulk_data:
            db.insert_bulk(schema, table, cols, bulk_data)

        total_value, total_unit = self._convertir_octets(total_size)
        total_data = [f"{tenant_name} TOTAL", date, str(total_value), total_unit, f"TOTAL {base_path}"]
        db.insert(schema, table, cols, total_data)

        self.logger.info(f"Taille totale: {total_value} {total_unit}")

    @retry_on_failure
    @timer
    def disk_check(
            self,
           db: DataFactory,
           schema: str,
           table: str,
           base_path: str,
           tenant_name: str = "DEFAULT",
           file_filter: str = "python-",
    ) -> None:
        """
        Calcule la taille des fichiers correspondant à un filtre dans un répertoire et enregistre les résultats dans une base.

        :param db: Instance de data_factory (dbMssql, dbPgsql, dbMysql)
        :param schema: Nom du schéma
        :param table: Nom de la table cible
        :param base_path: Répertoire racine à scanner
        :param tenant_name: Nom du tenant à enregistrer
        :param file_filter: Mot-clé à rechercher dans les fichiers
        """  # noqa: D401
        self.logger.info(f"Lancement du disk_check à partir de {base_path}")
        db.connect()
        today = datetime.now(timezone.utc).date()
        self._ensure_table_exists(db, schema, table)
        fichiers = self._collect_files(base_path, file_filter)
        if not fichiers:
            self.logger.warning(f"Aucun fichier contenant '{file_filter}' trouvé dans '{base_path}'.")
            return
        self._process_files(db, schema, table, fichiers, tenant_name, str(today), base_path)

    def wait_for_file(self, path: str, filename: str, retry: int | None = None, delay: int | None = None) -> bool:
        """Attend qu'un fichier spécifique soit disponible dans un répertoire donné."""
        retry = retry or self.retry_count
        delay = delay or self.retry_delay
        self.logger.info(f"Attente du fichier '{filename}' dans le répertoire '{path}'.")
        found = False
        if not self.directory_exists(path):
            msg = f"Le dossier {path} ne semble pas exister."
            self.logger.error(msg)
            raise FileNotFoundError(msg)
        attempt = 0
        for attempt in range(1, retry + 1): # noqa: B007
            found = self.fs.exists(f"{path}/{filename}")
            if found:
                break
            time.sleep(delay)
        if found:
            self.logger.info(f"Fichier '{filename}' trouvé après {attempt} tentatives(s), soit {attempt * delay}s.")
        else:
            self.logger.warning(f"Fichier '{filename}' introuvable après {attempt} tentatives(s), soit {retry * delay}s.")
        return found
