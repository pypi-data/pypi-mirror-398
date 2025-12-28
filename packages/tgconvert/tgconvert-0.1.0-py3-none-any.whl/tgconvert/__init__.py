"""
tgconvert - Universal Telegram session converter
Supports: tdata, Telethon, Pyrogram, auth_key formats
"""

__version__ = "0.1.0"
__author__ = "tgconvert"

from .converter import SessionConverter
from .base import SessionData
from .formats import (
    TelethonSession,
    PyrogramSession,
    TdataSession,
    AuthKeySession,
)

__all__ = [
    "SessionConverter",
    "SessionData",
    "TelethonSession",
    "PyrogramSession",
    "TdataSession",
    "AuthKeySession",
]
