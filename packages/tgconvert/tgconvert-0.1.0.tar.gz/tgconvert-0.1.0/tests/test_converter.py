"""Tests for tgconvert library"""

import os
import tempfile
import pytest
from pathlib import Path

from tgconvert import SessionConverter, SessionData
from tgconvert.formats import TelethonSession, PyrogramSession, AuthKeySession


class TestSessionData:
    """Test SessionData class"""
    
    def test_create_session_data(self):
        """Test creating SessionData"""
        auth_key = b'\x00' * 256
        dc_id = 2
        
        session = SessionData(auth_key=auth_key, dc_id=dc_id)
        
        assert session.auth_key == auth_key
        assert session.dc_id == dc_id
        assert session.user_id is None
        assert session.is_bot is False
    
    def test_to_dict(self):
        """Test converting to dict"""
        auth_key = b'\x00' * 256
        session = SessionData(
            auth_key=auth_key,
            dc_id=2,
            user_id=123456,
        )
        
        data = session.to_dict()
        
        assert data['auth_key'] == auth_key.hex()
        assert data['dc_id'] == 2
        assert data['user_id'] == 123456
    
    def test_from_dict(self):
        """Test creating from dict"""
        auth_key = b'\x00' * 256
        data = {
            'auth_key': auth_key.hex(),
            'dc_id': 2,
            'user_id': 123456,
        }
        
        session = SessionData.from_dict(data)
        
        assert session.auth_key == auth_key
        assert session.dc_id == 2
        assert session.user_id == 123456


class TestAuthKeyFormat:
    """Test AuthKey format"""
    
    def test_detect_valid_format(self):
        """Test detecting valid auth key format"""
        auth_key = 'a' * 512  # 256 bytes in hex
        auth_string = f"{auth_key}:2"
        
        assert AuthKeySession.detect(auth_string)
    
    def test_detect_invalid_format(self):
        """Test detecting invalid formats"""
        assert not AuthKeySession.detect("invalid")
        assert not AuthKeySession.detect("abc:2")
        assert not AuthKeySession.detect("abc123:10")
    
    def test_load_from_string(self):
        """Test loading from string"""
        auth_key = 'aa' * 256  # 256 bytes
        auth_string = f"{auth_key}:2"
        
        handler = AuthKeySession()
        session = handler.load(auth_string)
        
        assert session.dc_id == 2
        assert len(session.auth_key) == 256
    
    def test_save_and_load(self):
        """Test save and load cycle"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "authkey.txt")
            
            # Create session
            auth_key = b'\xaa' * 256
            session_data = SessionData(auth_key=auth_key, dc_id=2)
            
            # Save
            handler = AuthKeySession()
            handler.save(session_data, file_path)
            
            # Load
            loaded_session = handler.load(file_path)
            
            assert loaded_session.auth_key == auth_key
            assert loaded_session.dc_id == 2


class TestSessionConverter:
    """Test SessionConverter"""
    
    def test_list_formats(self):
        """Test listing supported formats"""
        formats = SessionConverter.list_formats()
        
        assert 'telethon' in formats
        assert 'pyrogram' in formats
        assert 'tdata' in formats
        assert 'authkey' in formats
    
    def test_detect_authkey_format(self):
        """Test auto-detection of auth key format"""
        auth_key = 'aa' * 256
        auth_string = f"{auth_key}:2"
        
        converter = SessionConverter()
        detected = converter.detect_format(auth_string)
        
        assert detected == 'authkey'
    
    def test_convert_authkey_to_telethon(self):
        """Test converting auth key to Telethon format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_str = ('aa' * 256) + ':2'
            output_path = os.path.join(tmpdir, "output.session")
            
            converter = SessionConverter()
            converter.convert(
                input_path=input_str,
                output_path=output_path,
                output_format='telethon'
            )
            
            assert os.path.exists(output_path)
    
    def test_get_info(self):
        """Test getting session info"""
        auth_key = 'aa' * 256
        auth_string = f"{auth_key}:2"
        
        converter = SessionConverter()
        info = converter.get_info(auth_string, 'authkey')
        
        assert info['dc_id'] == 2
        assert info['format'] == 'authkey'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
