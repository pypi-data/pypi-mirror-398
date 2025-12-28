# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2025-12-23

### Added
- Better error messages with detailed validation feedback
- Support for more flexible CLI argument parsing
- Enhanced configuration merging capabilities

### Changed
- Improved type checking and validation error reporting
- Better handling of optional configuration fields
- More robust file loading and error handling

### Fixed
- Fixed type hints for configuration file paths
- Improved YAML/JSON parsing consistency

---

## [0.1.4] - 2025-12-21

### Improved
- Upgraded minimum Python version to 3.9+ for better stability
- Enhanced error handling for missing configuration files
- Improved code quality and type safety

---

## [0.1.2] - 2025-12-21

### Added
- Type-safe configuration with Pydantic V2
- Multi-source configuration (file/env/CLI)
- Nested field access with dot notation
- File reference support (@file:, @config:)
- Configuration inheritance with override_with()
- Strict/non-strict validation modes
- Auto help generation with --help flag
- Bilingual documentation (English & Korean)

### Features
- YAML/JSON auto-detection
- Environment variable override with custom prefix
- CLI argument parsing with flexible syntax
- Nested configuration support
- Color-coded terminal output
- Comprehensive error messages


---

## Format

This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

Versions follow [Semantic Versioning](https://semver.org/) (Major.Minor.Patch).

