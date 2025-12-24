from ide_updater.modules.base import BaseUpdater
import requests
import json
from pathlib import Path

class VSCodeUpdater(BaseUpdater):
    @property
    def name(self) -> str:
        return "Visual Studio Code"

    def get_latest_version(self) -> str:
        try:
            url = "https://update.code.visualstudio.com/api/update/linux-x64/stable/latest"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            # The API returns JSON with "name" as the version string e.g. "1.85.1"
            data = response.json()
            return data.get("name", "unknown")
        except Exception as e:
            return "unknown"

    def get_current_version(self) -> str:
        """
        Check for installed VS Code version.
        Checks PATH first (system-wide installations), then the configured install_dir.
        """
        import subprocess
        import shutil
        
        # First, try to find 'code' in PATH (system-wide installation)
        code_path = shutil.which("code")
        if code_path:
            try:
                result = subprocess.run([code_path, "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Output is typically:
                    # 1.85.1
                    # 890... (commit hash)
                    # x64
                    return result.stdout.splitlines()[0]
            except:
                pass
        
        # Fallback: check the configured install_dir (tool-managed installation)
        try:
            code_bin = self.install_dir / "VSCode" / "bin" / "code"
            if code_bin.exists():
                result = subprocess.run([str(code_bin), "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return result.stdout.splitlines()[0]
        except:
            pass
        
        return "not installed"
    
    def find_existing_installation(self):
        """
        Find where VS Code is currently installed.
        Checks PATH first, then the configured install_dir.
        Returns the Path to the VS Code installation directory.
        """
        from pathlib import Path
        import shutil
        
        # First, try to find 'code' in PATH
        code_path = shutil.which("code")
        if code_path:
            code_path = Path(code_path).resolve()
            # If it's in a bin/ directory, get the parent (installation root)
            if code_path.parent.name == "bin":
                return code_path.parent.parent
            return code_path.parent
        
        # Check configured install_dir
        vscode_dir = self.install_dir / "VSCode" / "bin" / "code"
        if vscode_dir.exists():
            return self.install_dir / "VSCode"
        
        # Also check for VisualStudioCode variant
        vscode_dir = self.install_dir / "VisualStudioCode" / "bin" / "code"
        if vscode_dir.exists():
            return self.install_dir / "VisualStudioCode"
        
        return None

    def get_download_url(self) -> str:
        # We can either return the static link or the one from the JSON
        # JSON usually has "url" field
        try:
            url = "https://update.code.visualstudio.com/api/update/linux-x64/stable/latest"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("url", "https://code.visualstudio.com/sha/download?build=stable&os=linux-x64")
        except:
             return "https://code.visualstudio.com/sha/download?build=stable&os=linux-x64"
