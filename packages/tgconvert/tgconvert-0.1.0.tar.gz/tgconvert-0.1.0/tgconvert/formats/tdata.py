"""Tdata format handler (Telegram Desktop)"""

import struct
import os
import sys
from pathlib import Path
from typing import Optional, Tuple
from ..base import SessionFormat, SessionData
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
import hashlib


class TdataSession(SessionFormat):
    """Handler for Telegram Desktop tdata format"""
    
    FORMAT_NAME = "Tdata"
    
    LOCAL_KEY = b'\x00' * 32
    
    @staticmethod
    def _use_opentele_if_available(tdata_path: str) -> Optional[SessionData]:
        """Try to use opentele library if available"""
        try:
            from opentele.td import TDesktop
            
            td = TDesktop(tdata_path)
            
            if not td.isLoaded():
                return None
            
            if not td.accounts or len(td.accounts) == 0:
                return None
            
            account = td.accounts[0]
            
            dc_id = account.MainDcId
            user_id = account.UserId
            auth_key = account.authKey.key
            
            api_info = account.api
            api_id = api_info.api_id if hasattr(api_info, 'api_id') else None
            api_hash = api_info.api_hash if hasattr(api_info, 'api_hash') else None
            
            return SessionData(
                auth_key=auth_key,
                dc_id=dc_id,
                user_id=user_id,
                api_id=api_id,
                api_hash=api_hash
            )
        except ImportError:
            return None
        except Exception as e:
            return None
    
    def _decrypt_local(self, data: bytes, key: bytes = None) -> bytes:
        """Decrypt local Telegram Desktop data"""
        if key is None:
            key = self.LOCAL_KEY
        
        if len(data) < 16:
            raise ValueError("Data too short for decryption")
        
        encrypted_key = data[:16]
        encrypted_data = data[16:]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.ECB(),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt key info
        decrypted_key_info = decryptor.update(encrypted_key)
        
        # Extract actual key and IV
        data_key = decrypted_key_info[:16]
        
        # Decrypt data using CTR mode
        cipher = Cipher(
            algorithms.AES(key),
            modes.CTR(decrypted_key_info),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        return decryptor.update(encrypted_data) + decryptor.finalize()
    
    def _encrypt_local(self, data: bytes, key: bytes = None) -> bytes:
        """Encrypt data for Telegram Desktop"""
        if key is None:
            key = self.LOCAL_KEY
        
        # Generate random IV
        import os
        iv = os.urandom(16)
        
        # Create cipher for key info
        cipher = Cipher(
            algorithms.AES(key),
            modes.ECB(),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted_key_info = encryptor.update(iv)
        
        # Encrypt data
        cipher = Cipher(
            algorithms.AES(key),
            modes.CTR(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(data) + encryptor.finalize()
        
        return encrypted_key_info + encrypted_data
    
    def _find_key_file(self, tdata_path: str) -> Optional[str]:
        """Find the key_data or key_datas file"""
        tdata_dir = Path(tdata_path)
        
        # Check for key files
        for key_file in ['key_datas', 'key_data']:
            key_path = tdata_dir / key_file
            if key_path.exists():
                return str(key_path)
        
        return None
    
    def _parse_auth_key_file(self, file_path: str) -> Tuple[bytes, int]:
        """Parse auth key from tdata file"""
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Tdata files have a specific structure
        # Try to extract DC ID and auth key
        
        # Simple approach: look for patterns
        # DC ID is usually in the first bytes
        # Auth key is 256 bytes
        
        if len(data) < 260:
            raise ValueError("File too short to contain auth key")
        
        # Try to parse
        # Format: [header][dc_id:4][auth_key:256][...]
        try:
            # Skip magic bytes and find DC ID
            dc_id = None
            auth_key = None
            
            # Look for DC ID (1-5)
            for i in range(len(data) - 256):
                # Check if next 256 bytes could be auth key
                potential_dc = struct.unpack('<I', data[i:i+4])[0]
                if 1 <= potential_dc <= 5:
                    dc_id = potential_dc
                    if i + 4 + 256 <= len(data):
                        auth_key = data[i+4:i+4+256]
                        break
            
            if not auth_key or not dc_id:
                # Fallback: try to decrypt first
                try:
                    decrypted = self._decrypt_local(data)
                    # Retry parsing
                    for i in range(len(decrypted) - 256):
                        potential_dc = struct.unpack('<I', decrypted[i:i+4])[0]
                        if 1 <= potential_dc <= 5:
                            dc_id = potential_dc
                            if i + 4 + 256 <= len(decrypted):
                                auth_key = decrypted[i+4:i+4+256]
                                break
                except:
                    pass
            
            if not auth_key or not dc_id:
                raise ValueError("Could not extract auth key and DC ID")
            
            return auth_key, dc_id
            
        except Exception as e:
            raise ValueError(f"Failed to parse tdata file: {e}")
    
    def load(self, path: str) -> SessionData:
        """Load session from Telegram Desktop tdata directory"""
        tdata_path = Path(path)
        
        if not tdata_path.exists():
            raise ValueError(f"Tdata path does not exist: {path}")
        
        if not tdata_path.is_dir():
            raise ValueError(f"Tdata path is not a directory: {path}")
        
        # First try using opentele if available
        session_data = self._use_opentele_if_available(path)
        if session_data:
            return session_data
        
        # Fallback to manual parsing
        # Find key file
        key_file = self._find_key_file(path)
        if not key_file:
            raise ValueError("No key_data or key_datas file found in tdata directory")
        
        # Find data files (D877F783D5D3EF8C* pattern)
        data_files = list(tdata_path.glob("D877F783D5D3EF8C*"))
        
        auth_key = None
        dc_id = None
        
        # Try to parse key file
        try:
            auth_key, dc_id = self._parse_auth_key_file(key_file)
        except Exception as e:
            # Try data files
            for data_file in data_files:
                try:
                    auth_key, dc_id = self._parse_auth_key_file(str(data_file))
                    if auth_key and dc_id:
                        break
                except:
                    continue
        
        if not auth_key or not dc_id:
            raise ValueError("Could not extract session data from tdata. Install 'opentele' for better tdata support: pip install opentele")
        
        return SessionData(
            auth_key=auth_key,
            dc_id=dc_id,
        )
    
    def save(self, session_data: SessionData, path: str) -> None:
        """Save session to Telegram Desktop tdata format"""
        tdata_path = Path(path)
        
        # Try to use opentele for proper tdata creation
        try:
            from opentele.td import TDesktop
            from opentele.td.auth import AuthKey
            from opentele.api import API
            import shutil
            
            template_tdata = None
            
            package_dir = Path(__file__).parent.parent
            
            try:
                import sys
                for mod_name in sys.modules:
                    if 'editable' in mod_name and 'tgconvert' in mod_name and 'finder' in mod_name:
                        finder = sys.modules[mod_name]
                        if hasattr(finder, 'MAPPING') and 'tgconvert' in finder.MAPPING:
                            package_dir = Path(finder.MAPPING['tgconvert'])
                            break
            except Exception:
                pass
            
            possible_templates = [
                package_dir / "accs" / "tdata",
                Path.home() / "AppData" / "Roaming" / "Telegram Desktop" / "tdata",
                Path("accs/tdata"),
            ]
            
            for tmpl in possible_templates:
                if tmpl.exists() and tmpl.is_dir():
                    try:
                        td_test = TDesktop(str(tmpl))
                        if td_test.isLoaded() and len(td_test.accounts) > 0:
                            template_tdata = tmpl
                            break
                    except Exception:
                        continue
            
            if not template_tdata:
                raise Exception("No valid tdata template found")
            
            if tdata_path.exists():
                shutil.rmtree(tdata_path)
            shutil.copytree(template_tdata, tdata_path)
            
            td = TDesktop(str(tdata_path))
            
            if td.accounts and len(td.accounts) > 0:
                account = td.accounts[0]
                
                new_auth_key = AuthKey(
                    key=session_data.auth_key,
                    dcId=session_data.dc_id
                )
                
                account._Account__authKey = new_auth_key
                account._Account__MainDcId = session_data.dc_id
                
                if session_data.user_id:
                    try:
                        account._Account__UserId = session_data.user_id
                    except:
                        pass
                
                if session_data.api_id and session_data.api_hash:
                    try:
                        account._Account__api = API(
                            api_id=session_data.api_id,
                            api_hash=session_data.api_hash
                        )
                    except:
                        pass
                
                td.SaveTData()
                return
            
        except ImportError:
            pass
        except Exception as e:
            print(f"Warning: opentele save failed, using fallback: {e}")
        
        if not tdata_path.exists():
            tdata_path.mkdir(parents=True, exist_ok=True)
        
        key_file = tdata_path / "key_datas"
        
        magic = b'TGDT'
        dc_id_bytes = struct.pack('<I', session_data.dc_id)
        checksum_data = dc_id_bytes + session_data.auth_key
        checksum = hashlib.md5(checksum_data).digest()
        
        data = magic + dc_id_bytes + session_data.auth_key + checksum
        
        # Encrypt
        encrypted = self._encrypt_local(data)
        
        # Write to file
        with open(key_file, 'wb') as f:
            f.write(encrypted)
        
        # Create map files (placeholders)
        (tdata_path / "maps").touch()
        (tdata_path / "usertag").touch()
        (tdata_path / "settings0").touch()
        
        print("Note: Created minimal tdata structure. For full Telegram Desktop compatibility,")
        print("      install opentele and have a reference tdata folder available.")
    
    @classmethod
    def detect(cls, path: str) -> bool:
        """Detect if path is a tdata directory"""
        tdata_path = Path(path)
        
        if not tdata_path.exists() or not tdata_path.is_dir():
            return False
        
        # Check for characteristic files
        has_key_file = (
            (tdata_path / "key_datas").exists() or 
            (tdata_path / "key_data").exists()
        )
        
        has_data_files = len(list(tdata_path.glob("D877F783D5D3EF8C*"))) > 0
        
        return has_key_file or has_data_files
