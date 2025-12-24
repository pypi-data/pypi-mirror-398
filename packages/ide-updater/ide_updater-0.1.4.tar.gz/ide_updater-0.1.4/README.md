# IDE Updater

A CLI tool to quickly update Linux IDEs (VS Code, Cursor, Kiro) with a simple command.

Keep your development environment fresh with automatic IDE updates!

## Features

- 🚀 **Multi-IDE Support**: VS Code, Cursor, and Kiro IDE
- 🔍 **Smart Version Detection**: Checks both system-wide and local installations
- 📦 **Automatic Downloads**: Fetches latest versions from official sources
- 🎯 **Clean Installation**: Manages AppImages and tar.gz files properly
- ⚙️ **Configurable**: Stores settings in `~/.config/ide-updater/`
- 🎨 **Beautiful Output**: Rich terminal interface with progress bars

## Installation

### Quick Install with pipx (Recommended)

**If you have pipx installed:**
```bash
pipx install ide-updater && pipx ensurepath
```

**If you don't have pipx yet (complete one-command install):**
```bash
python3 -m pip install --user pipx && python3 -m pipx ensurepath && pipx install ide-updater && pipx ensurepath
```

**After installation:** Restart your terminal or run `source ~/.bashrc` to make the command available immediately.

### Why pipx?

`pipx` is the recommended way to install Python CLI applications. It:
- ✅ Installs apps in isolated environments (no conflicts)
- ✅ Makes commands globally available
- ✅ Works on modern Linux systems (avoids "externally-managed-environment" errors)
- ✅ Easy to update: `pipx upgrade ide-updater`

### Alternative: Using pip in a virtual environment

```bash
python3 -m venv venv && source venv/bin/activate && pip install ide-updater
```

### From Source

```bash
git clone https://github.com/cosmah/ide-updater.git
cd ide-updater
pip install -e .
```

## Usage

```bash
# Check for updates
ide-updater check

# Update all IDEs
ide-updater update

# Update specific IDE
ide-updater update cursor
ide-updater update vscode
ide-updater update kiro

# Initialize configuration
ide-updater init
```

## Configuration

The tool stores configuration in `~/.config/ide-updater/config.json`:

```json
{
    "install_dir": "/home/user/Applications",
    "temp_dir": "/home/user/.cache/ide-updater",
    "ides": {
        "vscode": {"enabled": true, "channel": "stable"},
        "cursor": {"enabled": true},
        "kiro": {"enabled": true}
    }
}
```

## Supported IDEs

| IDE | Version Detection | Download Source | Installation |
|-----|------------------|-----------------|--------------|
| **VS Code** | Microsoft Update API | Official Microsoft | tar.gz extraction |
| **Cursor** | Changelog scraping | cursor.com API | AppImage |
| **Kiro** | Downloads page + AWS | AWS S3 bucket | AppImage/tar.gz |

## Requirements

- Linux (tested on Ubuntu, should work on other distributions)
- Python 3.8+
- Internet connection for downloads

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support the Project

If this tool saves you time and makes your development workflow easier, consider supporting its development:

Your support helps maintain and improve this tool for the entire Linux developer community!

## License

MIT License - see [LICENSE](LICENSE) file for details.
