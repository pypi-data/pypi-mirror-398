from ide_updater.modules.base import BaseUpdater
import requests

class KiroUpdater(BaseUpdater):
    @property
    def name(self) -> str:
        return "Kiro"

    def get_latest_version(self) -> str:
        """
        Get the latest Kiro IDE version (not CLI).
        The IDE uses a different versioning scheme (0.x.x) than the CLI (1.x.x).
        
        NOTE: Kiro downloads are currently unavailable due to access restrictions.
        The download URLs have changed or are behind authentication.
        This module is disabled until the download access is restored.
        """
        from rich.console import Console
        console = Console()
        console.print("[yellow]⚠ Kiro support is temporarily disabled[/yellow]")
        console.print("[dim]The download URLs are currently inaccessible (403 Forbidden)[/dim]")
        console.print("[dim]Please visit https://kiro.dev/downloads/ to download manually[/dim]")
        return "unavailable"
        
        # Disabled: Current implementation no longer works
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        import re
        from packaging.version import parse as parse_version
        
        # Method 1: Try to scrape the downloads page for IDE version
        try:
            resp = requests.get("https://kiro.dev/downloads/", headers=headers, timeout=10)
            if resp.status_code == 200:
                text = resp.text
                
                # Look for kiro-ide version patterns in download URLs and filenames
                patterns = [
                    r'kiro-ide-(\d+\.\d+\.\d+)',  # kiro-ide-0.8.0
                    r'kiro[_-]ide[_-](\d+\.\d+\.\d+)',  # kiro_ide_0.8.0
                    r'/(\d+\.\d+\.\d+)/kiro-ide',  # /0.8.0/kiro-ide
                    r'version["\s:=]+(\d+\.\d+\.\d+)',  # version: 0.8.0
                ]
                
                ide_versions = []
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        # Only consider IDE versions (starting with 0.)
                        if match.startswith('0.'):
                            ide_versions.append(match)
                
                # Also look for download URLs that contain version numbers
                download_urls = re.findall(r'https?://[^\s"\'<>]+\.(?:AppImage|tar\.gz|deb)', text, re.IGNORECASE)
                for url in download_urls:
                    version_match = re.search(r'(\d+\.\d+\.\d+)', url)
                    if version_match:
                        version = version_match.group(1)
                        if version.startswith('0.'):
                            ide_versions.append(version)
                
                if ide_versions:
                    # Remove duplicates and sort by version
                    unique_versions = list(set(ide_versions))
                    sorted_versions = sorted(unique_versions, 
                                           key=lambda v: parse_version(v), reverse=True)
                    return sorted_versions[0]
        except Exception:
            pass
        
        # Method 2: Try known version by testing AWS URLs directly
        # Since we know 0.8.0 exists, let's check for common versions
        try:
            base_url = "https://desktop-release.q.us-east-1.amazonaws.com"
            # Test versions in descending order (most recent first)
            test_versions = ["0.12.0", "0.11.0", "0.10.0", "0.9.0", "0.8.0", "0.7.0"]
            
            for version in test_versions:
                # Test if this version exists by checking the AppImage URL
                test_url = f"{base_url}/{version}/kiro-ide-{version}-stable-linux-x64.AppImage"
                try:
                    resp = requests.head(test_url, timeout=5, allow_redirects=True)
                    if resp.status_code == 200:
                        return version
                except:
                    continue
        except Exception:
            pass
        
        # Method 3: Fallback to known working version
        # If all else fails, return the version we know exists from the screenshot
        return "0.8.0"

    def get_download_url(self) -> str:
        """
        Get the download URL for the latest Kiro IDE (not CLI).
        
        NOTE: Kiro downloads are currently unavailable. 
        The download URLs have changed or are behind authentication.
        Users should visit https://kiro.dev/downloads/ to download manually.
        """
        return "https://kiro.dev/downloads/"

    def get_current_version(self) -> str:
        """
        Check for installed Kiro version.
        Checks PATH first (system-wide installations), then the configured install_dir.
        """
        import subprocess
        import shutil
        import re
        
        # First, try to find 'kiro' in PATH (system-wide installation)
        kiro_path = shutil.which("kiro")
        if kiro_path:
            try:
                result = subprocess.run([kiro_path, "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    out = result.stdout.strip()
                    # e.g. "kiro 1.23.0"
                    match = re.search(r"([0-9]+\.[0-9]+\.[0-9]+)", out)
                    if match:
                        return match.group(1)
            except:
                pass
        
        # Fallback: check the configured install_dir (tool-managed AppImage installation)
        try:
            appimage = self.install_dir / "Kiro.AppImage"
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
