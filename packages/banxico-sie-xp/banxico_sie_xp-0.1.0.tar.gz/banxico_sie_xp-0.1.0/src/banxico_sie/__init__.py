"""
banxico-sie: Cliente Python para la API de tipos de cambio del SIE de Banxico

Ejemplo de uso:
    >>> from banxico_sie import BanxicoSIEClient, Currency
    >>> client = BanxicoSIEClient("tu_token")
    >>> rate = client.get_rate(Currency.USD)
    >>> print(f"USD: ${rate['valor']}")
"""

from .client import BanxicoSIEClient
from .enums import Currency
from .exceptions import BanxicoAPIError, BanxicoRateLimitError, BanxicoAuthError

__version__ = "0.1.0"
__author__ = "Tu Nombre"
__all__ = [
    "BanxicoSIEClient",
    "Currency",
    "BanxicoAPIError",
    "BanxicoRateLimitError",
    "BanxicoAuthError",
]
