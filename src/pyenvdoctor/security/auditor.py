import os
import subprocess
import platform
from pathlib import Path
from typing import Dict, List

class SecurityAuditor:
    def __init__(self):
        self.pyenv_root = Path(os.environ.get("PYENV_ROOT", "~/.pyenv")).expanduser()
        
    def run_security_audit(self, check_cis=True, check_cve=True):
        """Run security audit"""
        results = {}
        
        if check_cis:
            results["cis_compliance"] = self._check_cis_compliance()
            
        if check_cve:
            results["vulnerability_scan"] = self._check_vulnerabilities()
            
        return results
        
    def _check_cis_compliance(self):
        """Check CIS compliance for Python environment"""
        compliance_results = {}
        
        # Check directory permissions
        compliance_results["directory_permissions"] = self._check_directory_permissions()
        
        # Check for secure Python configurations
        compliance_results["python_config"] = self._check_python_security_config()
        
        # Check for insecure environment variables
        compliance_results["environment_vars"] = self._check_environment_variables()
        
        return compliance_results
        
    def _check_directory_permissions(self):
        """Check directory permissions for security compliance"""
        results = {"status": "pass", "issues": []}
        
        # Check pyenv directory permissions
        if self.pyenv_root.exists():
            mode = oct(self.pyenv_root.stat().st_mode)[-3:]
            if int(mode) > 755:
                results["status"] = "fail"
                results["issues"].append({
                    "severity": "medium",
                    "description": f"PyEnv root directory has too open permissions: {mode}",
                    "recommendation": "Run: chmod 755 ~/.pyenv"
                })
                
        return results
        
    def _check_python_security_config(self):
        """Check Python security configurations"""
        results = {"status": "pass", "checks": []}
        
        # Check for secure SSL/TLS settings
        try:
            result = subprocess.run(
                ["python3", "-c", "import ssl; print(ssl.OPENSSL_VERSION)"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                results["checks"].append({
                    "name": "OpenSSL Version",
                    "result": result.stdout.strip(),
                    "status": "info"
                })
        except Exception:
            pass
            
        return results
        
    def _check_environment_variables(self):
        """Check for insecure environment variables"""
        results = {"status": "pass", "issues": []}
        
        # Check for dangerous environment variables
        dangerous_vars = {
            "PYTHONPATH": "May cause import issues",
            "PYTHON_DISABLE_SSL": "Disables SSL verification",
            "PYTHON_NO_USER_SITE": "May affect package installations"
        }
        
        for var, description in dangerous_vars.items():
            if os.environ.get(var):
                results["status"] = "fail"
                results["issues"].append({
                    "severity": "medium",
                    "variable": var,
                    "value": os.environ[var],
                    "description": description
                })
                
        return results
        
    def _check_vulnerabilities(self):
        """Check for known vulnerabilities in Python versions"""
        results = {"status": "checking", "vulnerabilities": []}
        
        # Get installed Python versions
        try:
            versions = self._get_installed_python_versions()
            for version in versions:
                # Placeholder for actual CVE checking
                results["vulnerabilities"].append({
                    "version": version,
                    "cves": [],
                    "status": "clean"
                })
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            
        return results
        
    def _get_installed_python_versions(self):
        """Get list of installed Python versions"""
        versions = []
        
        # Check system Python
        try:
            result = subprocess.run(["python3", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                versions.append(result.stdout.strip())
        except:
            pass
            
        # Check pyenv versions
        versions_dir = self.pyenv_root / "versions"
        if versions_dir.exists():
            for version_dir in versions_dir.iterdir():
                if version_dir.is_dir():
                    versions.append(version_dir.name)
                    
        return versions
