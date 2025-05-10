import os
import subprocess
import platform
from pathlib import Path
from typing import List, Dict
import sys

# Create stubs for missing models
class PythonInstallation:
    def __init__(self, path, version, provider, is_valid=True):
        self.path = path
        self.version = version
        self.provider = provider
        self.is_valid = is_valid
        
    def to_dict(self):
        return {
            "path": self.path,
            "version": self.version,
            "provider": self.provider,
            "is_valid": self.is_valid
        }

class Issue:
    def __init__(self, description, type="general", severity="medium", details=None):
        self.description = description
        self.type = type
        self.severity = severity
        self.details = details or {}
        
    def to_dict(self):
        return {
            "description": self.description,
            "type": self.type,
            "severity": self.severity,
            "details": self.details
        }

class SystemScanner:
    def __init__(self):
        self.installations = []
        self.issues = []
        
    def scan(self, comprehensive=False):
        """Scan system for Python installations and issues"""
        self.installations = []  # Reset installations
        self.issues = []  # Reset issues
        
        self._detect_system_python()
        self._detect_pyenv_installations()
        
        if comprehensive:
            self._deep_scan()
            
        return self.issues
        
    def _detect_system_python(self):
        """Detect system Python installations"""
        system_paths = [
            '/usr/bin/python3',
            '/usr/local/bin/python3',
            '/opt/homebrew/bin/python3',
            '/bin/python3'
        ]
        
        for path in system_paths:
            if os.path.exists(path):
                version = self._get_python_version(path)
                installation = PythonInstallation(
                    path=path,
                    version=version,
                    provider="system",
                    is_valid=self._verify_installation(path)
                )
                self.installations.append(installation)
                
    def _detect_pyenv_installations(self):
        """Detect pyenv installations"""
        pyenv_root = os.environ.get('PYENV_ROOT', os.path.expanduser('~/.pyenv'))
        versions_dir = Path(pyenv_root) / 'versions'
        
        if versions_dir.exists():
            for version_dir in versions_dir.iterdir():
                if version_dir.is_dir():
                    python_path = version_dir / 'bin' / 'python'
                    if python_path.exists():
                        version = version_dir.name
                        installation = PythonInstallation(
                            path=str(python_path),
                            version=version,
                            provider="pyenv",
                            is_valid=self._verify_installation(str(python_path))
                        )
                        self.installations.append(installation)
                        
    def _get_python_version(self, python_path):
        """Get Python version from executable"""
        try:
            result = subprocess.run([python_path, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip().replace('Python ', '')
            return "Unknown"
        except Exception as e:
            return "Error"
            
    def _verify_installation(self, python_path):
        """Verify a Python installation is working"""
        try:
            result = subprocess.run([python_path, '-c', 'print("OK")'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0 and result.stdout.strip() == "OK"
        except Exception:
            return False
            
    def _deep_scan(self):
        """Perform deep scan for issues"""
        self._check_missing_dependencies()
        self._check_permission_issues()
        self._check_version_conflicts()
        
    def _check_missing_dependencies(self):
        """Check for missing system dependencies"""
        # Check for common build dependencies
        dependencies = ['make', 'gcc', 'git']
        
        if platform.system() == 'Darwin':
            dependencies.extend(['brew'])
        elif platform.system() == 'Linux':
            dependencies.extend(['apt-get'])
            
        for dep in dependencies:
            if not self._command_exists(dep):
                self.issues.append(Issue(
                    description=f"Missing dependency: {dep}",
                    type="missing_dependency",
                    severity="medium",
                    details={"dependency_name": dep}
                ))
                
    def _check_permission_issues(self):
        """Check for permission issues"""
        # Check common directories
        dirs_to_check = []
        
        if platform.system() == 'Darwin':
            dirs_to_check.extend([
                '/usr/local/lib/python3.12/site-packages',
                os.path.expanduser('~/.pyenv')
            ])
            
        for directory in dirs_to_check:
            if os.path.exists(directory):
                try:
                    # Try to create a temp file
                    test_file = Path(directory) / '.test_write'
                    test_file.touch()
                    test_file.unlink()
                except PermissionError:
                    self.issues.append(Issue(
                        description=f"Permission denied: {directory}",
                        type="permission_error",
                        severity="high",
                        details={"path": directory}
                    ))
                except Exception:
                    pass
                    
    def _check_version_conflicts(self):
        """Check for Python version conflicts"""
        # Simple check for multiple Python versions
        if len(self.installations) > 3:
            self.issues.append(Issue(
                description=f"Multiple Python installations detected ({len(self.installations)})",
                type="version_conflict",
                severity="low",
                details={"count": len(self.installations)}
            ))
            
    def _command_exists(self, command):
        """Check if a command exists in PATH"""
        try:
            subprocess.run([command, '--version'], capture_output=True, timeout=5)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
            
    def get_installations(self):
        """Get all found installations"""
        return self.installations
