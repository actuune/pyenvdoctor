# src/pyenvdoctor/scanner/pyenv_scanner.py
class PyenvScanner(BaseScanner):
    def scan(self):
        pyenv_root = Path.home() / ".pyenv/versions"
        # Implémentation...