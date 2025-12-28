"""Auth key string format handler (auth_key_hex:dc_id)"""

from pathlib import Path
from typing import Optional
from ..base import SessionFormat, SessionData


class AuthKeySession(SessionFormat):
    """Handler for auth key string format: auth_key_hex:dc_id"""
    
    FORMAT_NAME = "AuthKey"
    
    def load(self, path: str) -> SessionData:
        """Load session from auth key string file or direct string"""
        # Check if it's a file
        if Path(path).exists() and Path(path).is_file():
            with open(path, 'r') as f:
                auth_string = f.read().strip()
        else:
            # Treat as direct string
            auth_string = path.strip()
        
        # Parse format: auth_key_hex:dc_id
        try:
            if ':' not in auth_string:
                raise ValueError("Invalid format. Expected: auth_key_hex:dc_id")
            
            parts = auth_string.split(':', 1)
            auth_key_hex = parts[0].strip()
            dc_id = int(parts[1].strip())
            
            # Validate DC ID
            if not 1 <= dc_id <= 5:
                raise ValueError(f"Invalid DC ID: {dc_id}. Must be 1-5")
            
            # Convert hex to bytes
            auth_key = bytes.fromhex(auth_key_hex)
            
            # Validate auth key length (should be 256 bytes)
            if len(auth_key) != 256:
                raise ValueError(f"Invalid auth key length: {len(auth_key)}. Expected 256 bytes")
            
            return SessionData(
                auth_key=auth_key,
                dc_id=dc_id,
            )
            
        except ValueError as e:
            raise ValueError(f"Failed to parse auth key string: {e}")
    
    def save(self, session_data: SessionData, path: str) -> None:
        """Save session to auth key string format"""
        auth_string = f"{session_data.auth_key.hex()}:{session_data.dc_id}"
        
        # Save to file
        with open(path, 'w') as f:
            f.write(auth_string)
    
    @classmethod
    def detect(cls, path: str) -> bool:
        """Detect if path/string is in auth key format"""
        # Check if it's a file
        if Path(path).exists() and Path(path).is_file():
            try:
                with open(path, 'r') as f:
                    content = f.read().strip()
                return cls._is_valid_format(content)
            except:
                return False
        else:
            # Check if string matches format
            return cls._is_valid_format(path)
    
    @staticmethod
    def _is_valid_format(s: str) -> bool:
        """Check if string matches auth_key_hex:dc_id format"""
        try:
            if ':' not in s:
                return False
            
            parts = s.split(':', 1)
            if len(parts) != 2:
                return False
            
            # Check if first part is valid hex
            auth_key_hex = parts[0].strip()
            try:
                auth_key = bytes.fromhex(auth_key_hex)
                if len(auth_key) != 256:
                    return False
            except ValueError:
                return False
            
            # Check if second part is valid DC ID
            try:
                dc_id = int(parts[1].strip())
                if not 1 <= dc_id <= 5:
                    return False
            except ValueError:
                return False
            
            return True
            
        except:
            return False
