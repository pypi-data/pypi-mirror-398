# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-12-XX

Initial stable release of Universal String Encoder.

### Features
- **13 encoders**: base16, base32, base64, url, doubleurl, hex, unicode, cstring, html, md5, sha1, sha256, hash
- **CLI tool**: Flexible input/output with stdin/files, character selection, customizable output, shell completion
- **Python API**: Simple `encode()` and `decode()` functions with full type hints
- **100% test coverage**: 192 tests across all encoders
- **Documentation**: Complete guides and API reference at https://crashoz.github.io/usenc/

### Technical
- Python 3.8+ support
- Zero runtime dependencies
- Extensible plugin architecture
- MIT License

[1.0.0]: https://github.com/crashoz/usenc/releases/tag/v1.0.0
