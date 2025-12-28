# Example usage of tgconvert library

from tgconvert import SessionConverter, SessionData

def example_1_basic_conversion():
    """Basic conversion example"""
    print("=== Example 1: Basic Conversion ===\n")
    
    converter = SessionConverter()
    
    # Convert Telethon to Pyrogram (auto-detect input format)
    converter.convert(
        input_path="my_session.session",
        output_path="pyrogram_session.session",
        output_format="pyrogram"
    )
    
    print("✓ Converted Telethon → Pyrogram")


def example_2_all_formats():
    """Convert to all formats"""
    print("\n=== Example 2: Convert to All Formats ===\n")
    
    converter = SessionConverter()
    
    # Load once
    session_data = converter.load("my_session.session")
    
    # Save in multiple formats
    converter.save(session_data, "telethon.session", "telethon")
    print("✓ Saved as Telethon")
    
    converter.save(session_data, "pyrogram.session", "pyrogram")
    print("✓ Saved as Pyrogram")
    
    converter.save(session_data, "tdata/", "tdata")
    print("✓ Saved as tdata")
    
    converter.save(session_data, "authkey.txt", "authkey")
    print("✓ Saved as auth_key string")


def example_3_auth_key():
    """Working with auth key strings"""
    print("\n=== Example 3: Auth Key Format ===\n")
    
    # Create session from auth key
    auth_key_str = "a1b2c3d4..." + "ff" * 252 + ":2"  # 256 bytes hex + dc_id
    
    converter = SessionConverter()
    session_data = converter.load(auth_key_str, format_name="authkey")
    
    print(f"DC ID: {session_data.dc_id}")
    print(f"Auth Key (first 16 bytes): {session_data.auth_key[:16].hex()}")
    
    # Convert to any format
    converter.save(session_data, "from_authkey.session", "telethon")
    print("\n✓ Converted auth_key → Telethon")


def example_4_session_info():
    """Get session information"""
    print("\n=== Example 4: Session Info ===\n")
    
    converter = SessionConverter()
    
    # Get detailed info
    info = converter.get_info("my_session.session")
    
    print("Session Information:")
    print(f"  Format:      {info['format']}")
    print(f"  DC ID:       {info['dc_id']}")
    print(f"  User ID:     {info['user_id']}")
    print(f"  Is Bot:      {info['is_bot']}")
    print(f"  Server:      {info['server']}")
    print(f"  Port:        {info['port']}")


def example_5_batch_conversion():
    """Batch convert multiple sessions"""
    print("\n=== Example 5: Batch Conversion ===\n")
    
    import os
    
    converter = SessionConverter()
    
    # Find all .session files
    session_files = [f for f in os.listdir(".") if f.endswith(".session")]
    
    for session_file in session_files:
        output_name = f"pyrogram_{session_file}"
        
        try:
            converter.convert(
                input_path=session_file,
                output_path=output_name,
                output_format="pyrogram"
            )
            print(f"✓ {session_file} → {output_name}")
        except Exception as e:
            print(f"✗ {session_file}: {e}")


def example_6_manual_session_data():
    """Create SessionData manually"""
    print("\n=== Example 6: Manual SessionData ===\n")
    
    # Create session data from scratch
    session_data = SessionData(
        auth_key=b'\x00' * 256,  # 256-byte auth key
        dc_id=2,
        user_id=123456789,
        is_bot=False,
        api_id=12345,
        api_hash="abcdef1234567890",
    )
    
    # Save in any format
    converter = SessionConverter()
    converter.save(session_data, "custom.session", "telethon")
    
    print("✓ Created custom session")
    print(f"  DC ID: {session_data.dc_id}")
    print(f"  User ID: {session_data.user_id}")


def example_7_migration():
    """Migrate from Telethon to Pyrogram"""
    print("\n=== Example 7: Library Migration ===\n")
    
    converter = SessionConverter()
    
    # List of sessions to migrate
    sessions_to_migrate = [
        "user1.session",
        "user2.session",
        "bot.session",
    ]
    
    for session in sessions_to_migrate:
        new_name = f"pyrogram_{session}"
        
        try:
            # Convert with explicit formats
            converter.convert(
                input_path=session,
                output_path=new_name,
                input_format="telethon",
                output_format="pyrogram"
            )
            print(f"✓ Migrated {session}")
        except FileNotFoundError:
            print(f"✗ {session} not found")
        except Exception as e:
            print(f"✗ {session}: {e}")


if __name__ == "__main__":
    print("tgconvert - Usage Examples")
    print("=" * 50)
    
    # Run examples (commented out to avoid errors without actual session files)
    # Uncomment the ones you want to try
    
    # example_1_basic_conversion()
    # example_2_all_formats()
    # example_3_auth_key()
    # example_4_session_info()
    # example_5_batch_conversion()
    # example_6_manual_session_data()
    # example_7_migration()
    
    print("\nNote: Uncomment examples in the script to run them")
    print("Make sure you have actual session files to test with!")
