# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-12-24

### Added
- Initial release of tgconvert
- Support for Telethon session format (.session SQLite)
- Support for Pyrogram session format (.session SQLite)
- Support for Telegram Desktop tdata format (read and write)
- Support for auth_key string format (hex:dc_id)
- Universal SessionConverter with auto-detection
- CLI interface with `tgconvert` command
- Python API for programmatic use
- Session information extraction
- Batch conversion support
- Comprehensive documentation
- PyPI publishing guide
- Integration with opentele for proper tdata handling

### Features
- Auto-detection of input formats
- Conversion between all supported formats
- Encryption/decryption for tdata format
- SQLite handling for Telethon/Pyrogram
- Command-line interface
- Python library interface
- Session data structure (SessionData)
- Format detection
- Info command for session inspection
- Full tdata write support with template-based approach
- Preserves all session metadata (DC ID, User ID, API credentials)

### Technical
- Uses opentele for robust tdata parsing and creation
- Template-based tdata generation for maximum compatibility
- Support for both old and new Telethon session formats
- Proper handling of Pyrogram session metadata
- Private field access for tdata modification

### Security
- Dependencies: cryptography, tgcrypto, opentele
- Local processing only
- Proper handling of auth keys
- Secure file operations
- No data sent to external servers

## [Unreleased]

### Planned
- Support for additional session formats
- Session validation and verification
- Migration tools between libraries
- GUI interface
- Session backup/restore
- Multi-account management
- Session encryption at rest
- Cloud storage integration
