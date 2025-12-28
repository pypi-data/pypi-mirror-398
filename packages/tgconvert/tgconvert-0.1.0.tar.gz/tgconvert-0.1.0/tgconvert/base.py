"""Base classes and data structures for session handling"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


@dataclass
class SessionData:
    """Universal session data structure"""
    
    # Core authentication data
    auth_key: bytes  # 256-byte authorization key
    dc_id: int  # Data center ID (1-5)
    
    # Optional user data
    user_id: Optional[int] = None
    is_bot: bool = False
    
    # API credentials (optional, for new sessions)
    api_id: Optional[int] = None
    api_hash: Optional[str] = None
    
    # Device info (optional)
    device_model: Optional[str] = None
    system_version: Optional[str] = None
    app_version: Optional[str] = None
    
    # Server info
    server_address: Optional[str] = None
    port: Optional[int] = None
    
    # Additional data
    date: Optional[int] = None  # Unix timestamp
    takeout_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "auth_key": self.auth_key.hex(),
            "dc_id": self.dc_id,
            "user_id": self.user_id,
            "is_bot": self.is_bot,
            "api_id": self.api_id,
            "api_hash": self.api_hash,
            "device_model": self.device_model,
            "system_version": self.system_version,
            "app_version": self.app_version,
            "server_address": self.server_address,
            "port": self.port,
            "date": self.date,
            "takeout_id": self.takeout_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        """Create from dictionary"""
        auth_key = data.get("auth_key")
        if isinstance(auth_key, str):
            auth_key = bytes.fromhex(auth_key)
        
        return cls(
            auth_key=auth_key,
            dc_id=data["dc_id"],
            user_id=data.get("user_id"),
            is_bot=data.get("is_bot", False),
            api_id=data.get("api_id"),
            api_hash=data.get("api_hash"),
            device_model=data.get("device_model"),
            system_version=data.get("system_version"),
            app_version=data.get("app_version"),
            server_address=data.get("server_address"),
            port=data.get("port"),
            date=data.get("date"),
            takeout_id=data.get("takeout_id"),
        )


class SessionFormat(ABC):
    """Abstract base class for session format handlers"""
    
    FORMAT_NAME: str = "Unknown"
    
    @abstractmethod
    def load(self, path: str) -> SessionData:
        """Load session from file/directory"""
        pass
    
    @abstractmethod
    def save(self, session_data: SessionData, path: str) -> None:
        """Save session to file/directory"""
        pass
    
    @classmethod
    @abstractmethod
    def detect(cls, path: str) -> bool:
        """Detect if the path contains this format"""
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.FORMAT_NAME}>"
