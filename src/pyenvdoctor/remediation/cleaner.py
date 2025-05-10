import shutil
from typing import List
from ..core.models import PythonInstallation

class EnvironmentCleaner:
    def __init__(self, installations: List[PythonInstallation]):
        self.installations = installations
    
    def clean_installation(self, path: str) -> bool:
        try:
            shutil.rmtree(path)
            return True
        except Exception as e:
            print(f"Erreur de nettoyage: {e}")
            return False
