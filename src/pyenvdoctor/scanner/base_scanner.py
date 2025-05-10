from abc import ABC, abstractmethod
from typing import List
from ..core.models import PythonInstallation

class BaseScanner(ABC):
    def __init__(self):
        self.found_installations: List[PythonInstallation] = []

    @abstractmethod
    def scan(self):
        pass

    def get_installations(self):
        return self.found_installations
