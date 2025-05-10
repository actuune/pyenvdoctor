"""PyEnvDoctor - Advanced Python Environment Management with AI and Gamification"""

__version__ = "2.0.0"
__author__ = "PyEnvDoctor Team"

from .core.config import config
from .core.models import Issue, FixSuggestion, PythonInstallation

__all__ = ['config', 'Issue', 'FixSuggestion', 'PythonInstallation']
