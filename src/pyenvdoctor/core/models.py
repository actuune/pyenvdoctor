from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class PythonInstallation:
    path: str
    version: str
    provider: str = "system"
    is_active: bool = False
    is_valid: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "version": self.version,
            "provider": self.provider,
            "is_active": self.is_active,
            "is_valid": self.is_valid
        }

@dataclass
class Issue:
    description: str
    type: str = "general"
    severity: str = "medium"  # low, medium, high, critical
    details: Dict[str, Any] = field(default_factory=dict)
    suggested_fixes: List['FixSuggestion'] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "description": self.description,
            "type": self.type,
            "severity": self.severity,
            "details": self.details,
            "suggested_fixes": [fix.to_dict() for fix in self.suggested_fixes],
            "discovered_at": self.discovered_at.isoformat()
        }

@dataclass
class FixSuggestion:
    description: str
    command: List[str]
    explanation: str
    risk_level: str = "low"  # low, medium, high
    confidence: float = 1.0
    safety_rating: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "description": self.description,
            "command": self.command,
            "explanation": self.explanation,
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "safety_rating": self.safety_rating
        }
