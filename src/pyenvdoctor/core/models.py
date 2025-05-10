from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

@dataclass
class PythonInstallation:
    path: str
    version: str
    provider: str
    packages: Dict[str, str] = None
    size_mb: float = 0.0
    last_used: Optional[datetime] = None
