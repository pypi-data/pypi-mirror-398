from ide_updater.modules.base import BaseUpdater
import requests
from packaging.version import parse as parse_version
import re

class CursorUpdater(BaseUpdater):
    @property
    def name(self) -> str:
        return "Cursor"

    def get_latest_version(self) -> str:
        """
        Get the latest Cursor version.
        First tries to extract from the download page JSON data.
        Falls back to scraping the changelog page.
        """
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        
        # Method 1: Try to get version from download page
        try:
            resp = requests.get("https://cursor.com/download", headers=headers, timeout=10)
            if resp.status_code == 200:
                # Look for versionNumber in the page's JSON/script data
                version_match = re.search(r'"versionNumber"\s*:\s*"([^"]+)"', resp.text)
                if version_match:
                    version = version_match.group(1)
                    # Validate it's a reasonable version
                    try:
                        parts = version.split('.')
                        if len(parts) >= 2 and 0 <= int(parts[0]) <= 10:
                            parse_version(version)
                            return version
                    except:
                        pass
        except Exception:
            pass
        
        # Method 2: Scrape changelog page for versions in HTML tags
        try:
            resp = requests.get("https://cursor.com/changelog", headers=headers, timeout=10)
            if resp.status_code == 200:
                # Look for versions inside HTML tags (like headings)
                # This avoids matching CSS values and other numbers
                matches = re.findall(r'<[^>]*>(\d{1,2}\.\d{1,2}(?:\.\d{1,2})?)</[^>]*>', resp.text)
                
                if matches:
                    valid_versions = []
                    for v in set(matches):
                        try:
                            parts = v.split('.')
                            # Filter to reasonable version ranges (0-10 for major)
                            if len(parts) >= 2 and 0 <= int(parts[0]) <= 10:
                                parse_version(v)
                                valid_versions.append(v)
                        except:
                            continue
                    
                    if valid_versions:
                        # Sort by version number (highest first)
                        sorted_versions = sorted(valid_versions, key=lambda v: parse_version(v), reverse=True)
                        return sorted_versions[0]
        except Exception:
            pass

        return "unknown"

    def get_download_url(self) -> str:
        """
        Get the download URL for the latest Cursor AppImage.
        Uses api2.cursor.sh with the version number.
        """
        # First, get the latest version
        version = self.get_latest_version()
        
        if version != "unknown":
            # Construct URL using the correct API endpoint
            # Format: https://api2.cursor.sh/updates/download/golden/linux-x64/cursor/{version}
            return f"https://api2.cursor.sh/updates/download/golden/linux-x64/cursor/{version}"
        else:
            # Fallback: try to get version from download page
            try:
                headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
                resp = requests.get("https://cursor.com/download", headers=headers, timeout=10)
                if resp.status_code == 200:
                    # Try to find version in the page
                    version_match = re.search(r'"versionNumber":\s*"([^"]+)"', resp.text)
                    if version_match:
                        version = version_match.group(1)
                        return f"https://api2.cursor.sh/updates/download/golden/linux-x64/cursor/{version}"
            except:
                pass
        
        # Ultimate fallback - this might not work but it's better than nothing
        return "https://api2.cursor.sh/updates/download/golden/linux-x64/cursor/latest"

    def get_current_version(self) -> str:
        """
        Check for installed Cursor version.
        Checks PATH first (system-wide installations), then the configured install_dir.
        """
        import subprocess
        import shutil
        
        # First, try to find 'cursor' in PATH (system-wide installation)
        cursor_path = shutil.which("cursor")
        if cursor_path:
            try:
                result = subprocess.run([cursor_path, "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # e.g. "Cursor 0.4.0" or just "0.4.0"
                    out = result.stdout.strip()
                    match = re.search(r"([0-9]+\.[0-9]+\.[0-9]+)", out)
                    if match:
                        return match.group(1)
            except:
                pass
        
        # Fallback: check the configured install_dir (tool-managed AppImage installation)
        try:
            appimage = self.install_dir / "Cursor.AppImage"
            if appimage.exists():
                result = subprocess.run([str(appimage), "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    out = result.stdout.strip()
                    match = re.search(r"([0-9]+\.[0-9]+\.[0-9]+)", out)
                    if match:
                        return match.group(1)
        except:
            pass
        
        return "not installed"
    
    def find_existing_installation(self):
        """
        Find where Cursor is currently installed.
        Checks PATH first, then the configured install_dir.
        Returns the Path to the AppImage file.
        """
        from pathlib import Path
        import shutil
        
        # First, try to find 'cursor' in PATH
        cursor_path = shutil.which("cursor")
        if cursor_path:
            cursor_path = Path(cursor_path).resolve()
            # If it's a symlink to an AppImage, return the AppImage location
            if cursor_path.exists():
                return cursor_path
        
        # Check configured install_dir for AppImage
        appimage = self.install_dir / "Cursor.AppImage"
        if appimage.exists():
            return appimage
        
        return None
