"""
py-pokernow: A Python library for interacting with pokernow.club
"""

from ._version import __version__

__author__ = "Your Name"
__license__ = "AGPL-3.0"

from .pokernow import (
    PokerNowClub,
    PokerNowGame,
    PokerNowPlayer,
    PokerNowSession,
    PokerNowTransaction,
    PokerGameConfig,
    login,
)

__all__ = [
    "PokerNowClub",
    "PokerNowGame",
    "PokerNowPlayer",
    "PokerNowSession",
    "PokerNowTransaction",
    "PokerGameConfig",
    "login",
    "__version__",
]