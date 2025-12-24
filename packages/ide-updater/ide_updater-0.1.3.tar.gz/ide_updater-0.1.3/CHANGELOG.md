# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2025-12-19

### Added
- Initial release of IDE Updater
- Support for VS Code, Cursor, and Kiro IDE updates
- Automatic version detection and downloading
- CLI interface with `update`, `check`, and `init` commands
- Configuration management in `~/.config/ide-updater/`
- Progress bars for downloads
- Smart installation handling for AppImages and tar.gz files

### Features
- **VS Code**: Automatic updates from official Microsoft API
- **Cursor**: Version detection from changelog and download page
- **Kiro**: IDE version detection (0.x.x) separate from CLI (1.x.x)
- Cross-platform Linux support
- Rich terminal output with tables and colors

### Technical
- Built with Typer for CLI interface
- Uses Rich for beautiful terminal output
- Modular architecture with base updater class
- Configurable install and temp directories