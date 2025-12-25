"""
Module global_config pour la configuration globale d'adsToolBox.

Fournit des fonctions utilitaires pour:
- Activer/désactiver le timer
- Récupérer l'état du timer
- Obtenir l'adresse IP publique de la machine
"""
from __future__ import annotations

import requests
from requests import Response

HTTP_OK = 200

class TimerConfig:
    """Singleton pour stocker l'état du timer."""

    _enabled: bool = False

    @classmethod
    def set(cls, *, state: bool) -> None:
        """
        Active ou désactive le timer.

        :param state: détermine l'état du timer
        """
        cls._enabled = state

    @classmethod
    def get(cls) -> bool:
        """
        Récupère l'état du timer.

        :return: l'état du timer
        """
        return cls._enabled

def set_timer(*, state: bool) -> None:
    """Wrapper pour activer ou désactiver le timer.""" # noqa: D401
    TimerConfig.set(state=state)

def get_timer() -> bool:
    """Wrapper pour récupérer l'état du timer.""" # noqa: D401
    return TimerConfig.get()

def _safe_get(url: str, timeout: int) -> Response | None:
    """Effectue une requête GET et capture l'exception."""
    try:
        return requests.get(url, timeout=timeout)
    except requests.RequestException:
        return None

def get_public_ip(timeout: int = 5) -> str:
    """
    Récupère l'adresse IP publique de la machine.

    :param timeout: Délai max de la requête http en secondes
    """
    urls = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://checkup.amazonaws.com",
    ]
    e_msg = "Impossible de récupérer l'adresse IP publique"

    for url in urls:
        response = _safe_get(url, timeout=timeout)
        if response is not None and response.status_code == HTTP_OK:
            return response.text.strip()
    raise RuntimeError(e_msg)
