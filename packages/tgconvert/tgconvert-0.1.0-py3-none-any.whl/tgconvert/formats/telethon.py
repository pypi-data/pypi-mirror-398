"""Telethon session format handler (.session files - SQLite)"""

import sqlite3
import struct
from pathlib import Path
from typing import Optional
from ..base import SessionFormat, SessionData


class TelethonSession(SessionFormat):
    """Handler for Telethon .session files (SQLite format)"""
    
    FORMAT_NAME = "Telethon"
    
    # DC addresses for Telegram
    DC_ADDRESSES = {
        1: ("149.154.175.53", 443),
        2: ("149.154.167.51", 443),
        3: ("149.154.175.100", 443),
        4: ("149.154.167.91", 443),
        5: ("91.108.56.130", 443),
    }
    
    def load(self, path: str) -> SessionData:
        """Load Telethon session from SQLite file"""
        if not path.endswith('.session'):
            path = f"{path}.session"
        
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        try:
            # Get main session data
            # Try with server_address first (newer format)
            try:
                cursor.execute(
                    "SELECT dc_id, server_address, port, auth_key, takeout_id FROM sessions"
                )
                row = cursor.fetchone()
                
                if not row:
                    raise ValueError("No session data found in database")
                
                dc_id, server_address, port, auth_key, takeout_id = row
            except sqlite3.OperationalError:
                # Fallback to old format without server_address
                cursor.execute(
                    "SELECT dc_id, auth_key FROM sessions"
                )
                row = cursor.fetchone()
                
                if not row:
                    raise ValueError("No session data found in database")
                
                dc_id, auth_key = row
                server_address = None
                port = None
                takeout_id = None
            
            # Try to get user_id from entities table
            user_id = None
            try:
                cursor.execute(
                    "SELECT id FROM entities WHERE id > 0 AND id < 1000000000000 LIMIT 1"
                )
                user_row = cursor.fetchone()
                if user_row:
                    user_id = user_row[0]
            except sqlite3.OperationalError:
                pass
            
            # Get version info if available
            api_id = None
            try:
                cursor.execute("SELECT value FROM version WHERE name = 'api_id'")
                api_row = cursor.fetchone()
                if api_row:
                    api_id = int(api_row[0])
            except (sqlite3.OperationalError, ValueError):
                pass
            
            conn.close()
            
            return SessionData(
                auth_key=auth_key,
                dc_id=dc_id,
                user_id=user_id,
                server_address=server_address,
                port=port,
                takeout_id=takeout_id,
                api_id=api_id,
            )
            
        except Exception as e:
            conn.close()
            raise ValueError(f"Failed to load Telethon session: {e}")
    
    def save(self, session_data: SessionData, path: str) -> None:
        """Save session to Telethon SQLite format"""
        if not path.endswith('.session'):
            path = f"{path}.session"
        
        # Remove existing file
        Path(path).unlink(missing_ok=True)
        
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        try:
            # Create sessions table
            cursor.execute("""
                CREATE TABLE sessions (
                    dc_id INTEGER PRIMARY KEY,
                    server_address TEXT,
                    port INTEGER,
                    auth_key BLOB,
                    takeout_id INTEGER
                )
            """)
            
            # Create entities table
            cursor.execute("""
                CREATE TABLE entities (
                    id INTEGER PRIMARY KEY,
                    hash INTEGER NOT NULL,
                    username TEXT,
                    phone INTEGER,
                    name TEXT,
                    date INTEGER
                )
            """)
            
            # Create sent_files table
            cursor.execute("""
                CREATE TABLE sent_files (
                    md5_digest BLOB,
                    file_size INTEGER,
                    type INTEGER,
                    id INTEGER,
                    hash INTEGER,
                    PRIMARY KEY(md5_digest, file_size, type)
                )
            """)
            
            # Create update_state table
            cursor.execute("""
                CREATE TABLE update_state (
                    id INTEGER PRIMARY KEY,
                    pts INTEGER,
                    qts INTEGER,
                    date INTEGER,
                    seq INTEGER
                )
            """)
            
            # Create version table
            cursor.execute("""
                CREATE TABLE version (
                    name TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Get server address and port
            server_address = session_data.server_address
            port = session_data.port
            
            if not server_address:
                server_address, port = self.DC_ADDRESSES.get(
                    session_data.dc_id, 
                    ("149.154.167.50", 443)
                )
            
            # Insert session data
            cursor.execute(
                "INSERT INTO sessions VALUES (?, ?, ?, ?, ?)",
                (
                    session_data.dc_id,
                    server_address,
                    port or 443,
                    session_data.auth_key,
                    session_data.takeout_id,
                )
            )
            
            # Insert version info
            cursor.execute("INSERT INTO version VALUES ('version', '1')")
            if session_data.api_id:
                cursor.execute(
                    "INSERT INTO version VALUES ('api_id', ?)",
                    (str(session_data.api_id),)
                )
            
            conn.commit()
            
        finally:
            conn.close()
    
    @classmethod
    def detect(cls, path: str) -> bool:
        """Detect if path is a Telethon session file"""
        if not path.endswith('.session'):
            path = f"{path}.session"
        
        if not Path(path).exists():
            return False
        
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
            )
            result = cursor.fetchone() is not None
            conn.close()
            return result
        except:
            return False
