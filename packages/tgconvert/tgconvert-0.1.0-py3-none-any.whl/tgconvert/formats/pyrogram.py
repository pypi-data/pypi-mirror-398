"""Pyrogram session format handler (.session files - SQLite with different schema)"""

import sqlite3
import struct
from pathlib import Path
from typing import Optional
from ..base import SessionFormat, SessionData


class PyrogramSession(SessionFormat):
    """Handler for Pyrogram .session files (SQLite format)"""
    
    FORMAT_NAME = "Pyrogram"
    
    # DC addresses for Telegram
    DC_ADDRESSES = {
        1: "149.154.175.53",
        2: "149.154.167.51",
        3: "149.154.175.100",
        4: "149.154.167.91",
        5: "91.108.56.130",
    }
    
    TEST_DC_ADDRESSES = {
        1: "149.154.175.10",
        2: "149.154.167.40",
        3: "149.154.175.117",
    }
    
    def load(self, path: str) -> SessionData:
        """Load Pyrogram session from SQLite file"""
        if not path.endswith('.session'):
            path = f"{path}.session"
        
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        try:
            # Get main session data from sessions table
            cursor.execute(
                "SELECT dc_id, test_mode, auth_key, date, user_id, is_bot FROM sessions"
            )
            row = cursor.fetchone()
            
            if not row:
                raise ValueError("No session data found in database")
            
            dc_id, test_mode, auth_key, date, user_id, is_bot = row
            
            # Try to get API credentials
            api_id = None
            api_hash = None
            try:
                cursor.execute("SELECT api_id FROM sessions")
                api_row = cursor.fetchone()
                if api_row:
                    api_id = api_row[0]
            except:
                pass
            
            conn.close()
            
            # Determine server address
            if test_mode:
                server_address = self.TEST_DC_ADDRESSES.get(dc_id)
            else:
                server_address = self.DC_ADDRESSES.get(dc_id)
            
            return SessionData(
                auth_key=auth_key,
                dc_id=dc_id,
                user_id=user_id,
                is_bot=bool(is_bot),
                date=date,
                server_address=server_address,
                port=443,
                api_id=api_id,
                api_hash=api_hash,
            )
            
        except Exception as e:
            conn.close()
            raise ValueError(f"Failed to load Pyrogram session: {e}")
    
    def save(self, session_data: SessionData, path: str) -> None:
        """Save session to Pyrogram SQLite format"""
        if not path.endswith('.session'):
            path = f"{path}.session"
        
        # Remove existing file
        Path(path).unlink(missing_ok=True)
        
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        try:
            # Create sessions table (Pyrogram v2.x schema)
            cursor.execute("""
                CREATE TABLE sessions (
                    dc_id INTEGER PRIMARY KEY,
                    test_mode INTEGER,
                    auth_key BLOB,
                    date INTEGER NOT NULL,
                    user_id INTEGER,
                    is_bot INTEGER
                )
            """)
            
            # Create peers table
            cursor.execute("""
                CREATE TABLE peers (
                    id INTEGER PRIMARY KEY,
                    access_hash INTEGER,
                    type INTEGER NOT NULL,
                    username TEXT,
                    phone_number TEXT
                )
            """)
            
            # Create usernames table
            cursor.execute("""
                CREATE TABLE usernames (
                    id INTEGER,
                    username TEXT,
                    PRIMARY KEY (id, username)
                )
            """)
            
            # Create phone_numbers table
            cursor.execute("""
                CREATE TABLE phone_numbers (
                    id INTEGER PRIMARY KEY,
                    phone_number TEXT
                )
            """)
            
            # Create version table
            cursor.execute("""
                CREATE TABLE version (
                    number INTEGER PRIMARY KEY
                )
            """)
            
            # Insert session data
            cursor.execute(
                "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?)",
                (
                    session_data.dc_id,
                    0,  # test_mode = False
                    session_data.auth_key,
                    session_data.date or 0,
                    session_data.user_id,
                    1 if session_data.is_bot else 0,
                )
            )
            
            # Insert version (Pyrogram uses version 3)
            cursor.execute("INSERT INTO version VALUES (3)")
            
            conn.commit()
            
        finally:
            conn.close()
    
    @classmethod
    def detect(cls, path: str) -> bool:
        """Detect if path is a Pyrogram session file"""
        if not path.endswith('.session'):
            path = f"{path}.session"
        
        if not Path(path).exists():
            return False
        
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            
            # Check for Pyrogram-specific schema
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='peers'"
            )
            has_peers = cursor.fetchone() is not None
            
            cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='sessions'"
            )
            sessions_sql = cursor.fetchone()
            
            conn.close()
            
            # Pyrogram has 'peers' table and sessions table with 'test_mode' column
            if has_peers and sessions_sql:
                return 'test_mode' in sessions_sql[0].lower()
            
            return False
        except:
            return False
