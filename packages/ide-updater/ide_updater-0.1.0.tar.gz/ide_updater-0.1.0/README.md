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

### From PyPI (Recommended)
```bash
pip install ide-updater
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

## License

MIT License - see [LICENSE](LICENSE) file for details.
