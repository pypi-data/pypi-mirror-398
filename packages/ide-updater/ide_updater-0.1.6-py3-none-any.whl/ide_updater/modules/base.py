from abc import ABC, abstractmethod
from typing import Optional, Tuple
import requests
from pathlib import Path

class BaseUpdater(ABC):
    def __init__(self, config: dict):
        self.config = config
        self.install_dir = Path(config["install_dir"])
        self.temp_dir = Path(config["temp_dir"])

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the IDE"""
        pass

    @abstractmethod
    def get_latest_version(self) -> str:
        """Return the latest version string."""
        pass

    def get_current_version(self) -> str:
        """Return the currently installed version string."""
        return "not installed"


    @abstractmethod
    def get_download_url(self) -> str:
        """Return the download URL for the latest version."""
        pass

    def get_local_version(self) -> Optional[str]:
        """
        Check the locally installed version.
        This might verify a version file or run the executable with --version.
        """
        # Default implementation could assume a standard location
        # But IDEs vary wildly.
        return None
    
    def find_existing_installation(self) -> Optional[Path]:
        """
        Find where the IDE is currently installed.
        Returns the path to the existing installation or None if not found.
        Subclasses should override this to implement IDE-specific detection.
        """
        return None

    def download(self, url: str, dest: Path) -> Path:
        """Download file to destination with progress bar."""
        from rich.progress import Progress
        
        if not dest.parent.exists():
            dest.parent.mkdir(parents=True)
            
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            with Progress() as progress:
                task = progress.add_task(f"[cyan]Downloading {self.name}...", total=total_size)
                with open(dest, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))
        return dest
