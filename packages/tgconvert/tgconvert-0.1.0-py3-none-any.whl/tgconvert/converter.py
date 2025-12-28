"""Main converter class for session format conversion"""

from pathlib import Path
from typing import Union, Type, Optional
from .base import SessionFormat, SessionData
from .formats import TelethonSession, PyrogramSession, TdataSession, AuthKeySession


class SessionConverter:
    """Universal session converter supporting multiple Telegram formats"""
    
    # Registry of all supported formats
    FORMATS = {
        "telethon": TelethonSession,
        "pyrogram": PyrogramSession,
        "tdata": TdataSession,
        "authkey": AuthKeySession,
    }
    
    def __init__(self):
        """Initialize converter"""
        self._format_instances = {
            name: format_class() 
            for name, format_class in self.FORMATS.items()
        }
    
    def detect_format(self, path: str) -> Optional[str]:
        """
        Auto-detect session format from path
        
        Args:
            path: Path to session file/directory or auth key string
            
        Returns:
            Format name or None if not detected
        """
        for name, format_instance in self._format_instances.items():
            if format_instance.__class__.detect(path):
                return name
        return None
    
    def load(self, path: str, format_name: Optional[str] = None) -> SessionData:
        """
        Load session from file/directory
        
        Args:
            path: Path to session file/directory or auth key string
            format_name: Format name (auto-detect if None)
            
        Returns:
            SessionData object
            
        Raises:
            ValueError: If format not detected or invalid
        """
        if format_name is None:
            format_name = self.detect_format(path)
            if format_name is None:
                raise ValueError(
                    f"Could not detect session format for: {path}\n"
                    f"Supported formats: {', '.join(self.FORMATS.keys())}"
                )
        
        if format_name not in self.FORMATS:
            raise ValueError(
                f"Unknown format: {format_name}\n"
                f"Supported formats: {', '.join(self.FORMATS.keys())}"
            )
        
        format_instance = self._format_instances[format_name]
        return format_instance.load(path)
    
    def save(
        self, 
        session_data: SessionData, 
        path: str, 
        format_name: str
    ) -> None:
        """
        Save session to file/directory
        
        Args:
            session_data: Session data to save
            path: Output path
            format_name: Target format name
            
        Raises:
            ValueError: If format unknown
        """
        if format_name not in self.FORMATS:
            raise ValueError(
                f"Unknown format: {format_name}\n"
                f"Supported formats: {', '.join(self.FORMATS.keys())}"
            )
        
        format_instance = self._format_instances[format_name]
        format_instance.save(session_data, path)
    
    def convert(
        self,
        input_path: str,
        output_path: str,
        input_format: Optional[str] = None,
        output_format: Optional[str] = None,
    ) -> SessionData:
        """
        Convert session from one format to another
        
        Args:
            input_path: Input session path
            output_path: Output session path
            input_format: Input format (auto-detect if None)
            output_format: Output format (required)
            
        Returns:
            SessionData object that was converted
            
        Raises:
            ValueError: If formats invalid or conversion fails
        """
        # Load source session
        session_data = self.load(input_path, input_format)
        
        # Detect output format if not specified
        if output_format is None:
            # Try to guess from extension or path
            output_path_lower = output_path.lower()
            if output_path_lower.endswith('.session'):
                # Ambiguous - could be Telethon or Pyrogram
                # Default to Telethon
                output_format = "telethon"
            elif 'tdata' in output_path_lower or Path(output_path).is_dir():
                output_format = "tdata"
            elif ':' in output_path or output_path_lower.endswith('.txt'):
                output_format = "authkey"
            else:
                raise ValueError(
                    "Could not detect output format. Please specify output_format parameter.\n"
                    f"Supported formats: {', '.join(self.FORMATS.keys())}"
                )
        
        # Save to target format
        self.save(session_data, output_path, output_format)
        
        return session_data
    
    def get_info(self, path: str, format_name: Optional[str] = None) -> dict:
        """
        Get information about a session without converting
        
        Args:
            path: Path to session
            format_name: Format name (auto-detect if None)
            
        Returns:
            Dictionary with session information
        """
        session_data = self.load(path, format_name)
        
        info = {
            "format": format_name or self.detect_format(path),
            "dc_id": session_data.dc_id,
            "user_id": session_data.user_id,
            "is_bot": session_data.is_bot,
            "api_id": session_data.api_id,
            "server": session_data.server_address,
            "port": session_data.port,
            "auth_key_hash": session_data.auth_key[:16].hex() if session_data.auth_key else None,
        }
        
        return info
    
    @classmethod
    def list_formats(cls) -> list:
        """Get list of supported format names"""
        return list(cls.FORMATS.keys())
    
    @classmethod
    def get_format_info(cls, format_name: str) -> dict:
        """Get information about a specific format"""
        if format_name not in cls.FORMATS:
            raise ValueError(f"Unknown format: {format_name}")
        
        format_class = cls.FORMATS[format_name]
        return {
            "name": format_name,
            "display_name": format_class.FORMAT_NAME,
            "class": format_class.__name__,
        }
