import subprocess
from pathlib import Path
from .base_scanner import BaseScanner
from ..core.models import PythonInstallation

class SystemScanner(BaseScanner):
    SYSTEM_PATHS = [
        "/usr/bin/python3",
        "/usr/local/bin/python3",
        "/opt/homebrew/bin/python3"
    ]

    def scan(self):
        for path in self.SYSTEM_PATHS:
            if Path(path).exists():
                version = self._get_version(path)
                self.found_installations.append(
                    PythonInstallation(
                        path=path,
                        version=version,
                        provider="system"
                    )
                )

    def _get_version(self, path):
        result = subprocess.run([path, "--version"], capture_output=True, text=True)
        return result.stdout.strip().split()[-1]
