# Temporary build script to check hatchling behavior
import subprocess
import sys
result = subprocess.run([sys.executable, "-m", "hatchling", "build", "-v"], 
                       capture_output=True, text=True, cwd="/home/cosmah/tools/ide-updater")
print(result.stdout)
print(result.stderr, file=sys.stderr)
