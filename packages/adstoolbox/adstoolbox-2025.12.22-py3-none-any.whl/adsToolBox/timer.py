"""Module timer pour la mesure du temps d'exécution des fonctions et gestion du fuseau horaire global."""
from __future__ import annotations

import os
import time
import timeit
from datetime import datetime
from typing import Callable, TypeVar
from zoneinfo import ZoneInfo

try:
    from typing import ParamSpec  # Python ≥ 3.10
except ImportError:
    from typing_extensions import ParamSpec  # Python 3.9

from .global_config import get_timer

P = ParamSpec("P")
R = TypeVar("R")

_GLOBAL: dict[str, ZoneInfo | None] = {"tz": None}

def timer(func: Callable[P, R]) -> Callable[P, R]:
    """
    Décorateur pour mesurer le temps d'exécution d'une fonction et enregistrer ce temps dans un logger si activé.

    :param func: La fonction à décorer pour mesurer et enregistrer son temps d'exécution.
    :raises ValueError: Si aucun logger n'est défini dans les arguments de la fonction appelée.
    :return: La fonction décorée qui mesure le temps d'exécution.
    """
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if get_timer():
            logger = kwargs.get("logger")
            if logger is None and args and hasattr(args[0], "logger"):
                logger = args[0].logger
            if logger is None:
                msg = "Pas de logger défini."
                raise ValueError(msg)
            start_time = timeit.default_timer()
            result = func(*args, **kwargs)
            elapsed_time = timeit.default_timer() - start_time
            if logger is not None:
                logger.info(f"Temps d'exécution de {func.__name__}: {elapsed_time:.4f} secondes.")
            return result
        return func(*args, **kwargs)
    return wrapper

def set_timezone(tz: str="Europe/Paris") -> None:
    """Définit le fuseau horaire global du processus."""
    os.environ["TZ"] = tz
    if hasattr(time, "tzset"):
        time.tzset()
        print(f"[INFO] Fuseau horaire défini globalement sur {tz} (via time.tzset)") # noqa: T201
    else:
        _GLOBAL["tz"] = ZoneInfo(tz)
        print(f"[WARNING] Fuseau horaire simulé sur {tz} (Windows n'a pas tzset())") # noqa: T201
        print(f"Appeler ads.now() pour avoir l'heure simulée sur {tz}") # noqa: T201

def now() -> datetime:
    """Renvoie l'heure actuelle dans le fuseau global défini."""
    tz = _GLOBAL.get("tz")
    if tz:
        return datetime.now(tz)
    return datetime.now().astimezone()
