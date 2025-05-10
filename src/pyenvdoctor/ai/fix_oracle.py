import platform
from typing import List, Dict

# Create local stubs for models since we don't have the proper imports
class FixSuggestion:
    def __init__(self, description, command, explanation, risk_level="low", confidence=1.0, safety_rating=1.0):
        self.description = description
        self.command = command
        self.explanation = explanation
        self.risk_level = risk_level
        self.confidence = confidence
        self.safety_rating = safety_rating
        
    def to_dict(self):
        return {
            "description": self.description,
            "command": self.command,
            "explanation": self.explanation,
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "safety_rating": self.safety_rating
        }

class FixOracle:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.platform_info = self._gather_platform_info()
        
    def suggest_fixes(self, issue) -> List[FixSuggestion]:
        """Generate fix suggestions for an issue"""
        # For now, return mock suggestions based on issue type
        if issue.type == "missing_dependency":
            return self._suggest_dependency_fix(issue)
        elif issue.type == "permission_error":
            return self._suggest_permission_fix(issue)
        else:
            return self._suggest_generic_fix(issue)
            
    def _suggest_dependency_fix(self, issue) -> List[FixSuggestion]:
        """Suggest fixes for missing dependencies"""
        suggestions = []
        dep_name = issue.details.get("dependency_name", "unknown")
        
        if self.platform_info["system"] == "Darwin":
            suggestions.append(FixSuggestion(
                description=f"Install {dep_name} using Homebrew",
                command=["brew", "install", dep_name],
                explanation=f"Installs {dep_name} package using Homebrew",
                risk_level="low",
                confidence=0.9,
                safety_rating=0.95
            ))
        elif self.platform_info["system"] == "Linux":
            suggestions.append(FixSuggestion(
                description=f"Install {dep_name} using apt",
                command=["sudo", "apt", "install", "-y", dep_name],
                explanation=f"Installs {dep_name} package using apt",
                risk_level="medium",
                confidence=0.85,
                safety_rating=0.8
            ))
            
        return suggestions
        
    def _suggest_permission_fix(self, issue) -> List[FixSuggestion]:
        """Suggest fixes for permission issues"""
        suggestions = []
        path = issue.details.get("path", "")
        
        suggestions.append(FixSuggestion(
            description=f"Fix permissions for {path}",
            command=["chmod", "755", path],
            explanation="Sets proper permissions for the directory",
            risk_level="medium",
            confidence=0.9,
            safety_rating=0.9
        ))
        
        return suggestions
        
    def _suggest_generic_fix(self, issue) -> List[FixSuggestion]:
        """Suggest generic fixes"""
        return [
            FixSuggestion(
                description="Manual investigation required",
                command=["echo", "Please investigate manually"],
                explanation="This issue requires manual investigation",
                risk_level="low",
                confidence=0.5,
                safety_rating=1.0
            )
        ]
        
    def _gather_platform_info(self) -> Dict:
        """Gather platform information"""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "processor": platform.processor()
        }
