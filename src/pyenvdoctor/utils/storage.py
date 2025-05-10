import json
from pathlib import Path
from typing import Any, Dict, Optional
import fcntl
import tempfile
import os

class Storage:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
    def load(self) -> Optional[Dict]:
        """Thread-safe load with file locking"""
        if not self.file_path.exists():
            return None
            
        with open(self.file_path, 'r') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return None
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                
    def save(self, data: Dict):
        """Thread-safe save with atomic write"""
        temp_path = self.file_path.with_suffix('.tmp')
        
        with open(temp_path, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(data, f, indent=2, sort_keys=True)
                f.flush()
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                
        # Atomic replace
        temp_path.replace(self.file_path)
        
    def append(self, data: Dict):
        """Append data to a list in the storage"""
        current = self.load() or {}
        
        if 'entries' not in current:
            current['entries'] = []
            
        current['entries'].append(data)
        self.save(current)
