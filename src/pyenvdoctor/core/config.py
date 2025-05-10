import os
from pathlib import Path
from typing import Dict, Any
import yaml

class Config:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "pyenvdoctor"
        self.config_file = self.config_dir / "config.yaml"
        self._config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = self.get_default_config()
            self.save_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "version": "2.0.0",
            "ai": {
                "enabled": True,
                "api_key": os.environ.get("PYENVDOCTOR_API_KEY", ""),
                "model": "pyenvdoctor-v1",
                "max_suggestions": 5
            },
            "gamification": {
                "enabled": True,
                "show_achievements": True,
                "celebrate_unlocks": True
            },
            "security": {
                "audit_enabled": True,
                "cis_compliance": True,
                "vulnerability_scanning": True,
                "security_log": str(Path.home() / ".pyenvdoctor" / "security.log")
            },
            "fixer": {
                "default_mode": "interactive",
                "auto_rollback": True,
                "max_undo_history": 50,
                "audit_log": str(Path.home() / ".pyenvdoctor" / "audit.log")
            },
            "scanner": {
                "full_scan_interval": "7d",
                "quick_scan_interval": "1d",
                "cache_results": True,
                "cache_ttl": "1h"
            },
            "logging": {
                "level": "INFO",
                "file": str(Path.home() / ".pyenvdoctor" / "pyenvdoctor.log"),
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "rotate": True,
                "max_size": "10MB",
                "backup_count": 5
            },
            "notifications": {
                "critical_issues": True,
                "achievement_unlocks": True,
                "update_available": True,
                "webhook_url": ""
            },
            "environment": {
                "pyenv_root": os.environ.get("PYENV_ROOT", ""),
                "prefer_pyenv": True,
                "check_shims": True,
                "verify_installations": True
            }
        }
    
    def save_config(self):
        """Save configuration to file"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()

# Global config instance
config = Config()
