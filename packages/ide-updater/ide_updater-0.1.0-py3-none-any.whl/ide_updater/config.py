import json
import os
from pathlib import Path
from typing import Dict, Any, List

APP_NAME = "ide-updater"
DEFAULT_CONFIG_DIR = Path.home() / ".config" / APP_NAME
CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "install_dir": str(Path.home() / "Applications"),
    "temp_dir": str(Path.home() / ".cache" / APP_NAME),
    "ides": {
        "vscode": {"enabled": True, "channel": "stable"},
        "cursor": {"enabled": True},
        "kiro": {"enabled": True}
    }
}

def load_config() -> Dict[str, Any]:
    """Load configuration from file or return defaults."""
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, "r") as f:
            user_config = json.load(f)
            # Merge with defaults (shallow merge for top-level keys)
            config = DEFAULT_CONFIG.copy()
            config.update(user_config)
            return config
    except Exception as e:
        print(f"Error loading config: {e}. Using defaults.")
        return DEFAULT_CONFIG

def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file."""
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def ensure_dirs(config: Dict[str, Any]) -> None:
    """Ensure necessary directories exist."""
    Path(config["install_dir"]).mkdir(parents=True, exist_ok=True)
    Path(config["temp_dir"]).mkdir(parents=True, exist_ok=True)
