import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

class OperationHistory:
    def __init__(self):
        self.history_file = Path.home() / ".pyenvdoctor" / "operation_history.json"
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
    def add_operation(self, operation_type: str, description: str, command: List[str], 
                     result: Dict = None):
        """Add an operation to history"""
        operation = {
            "timestamp": datetime.now().isoformat(),
            "type": operation_type,
            "description": description,
            "command": command,
            "result": result or {},
            "id": len(self.get_history()) + 1
        }
        
        history = self.get_history()
        history.append(operation)
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
            
    def get_history(self, limit: int = None) -> List[Dict]:
        """Get operation history"""
        if not self.history_file.exists():
            return []
            
        with open(self.history_file, 'r') as f:
            history = json.load(f)
            
        if limit:
            return history[-limit:]
        return history
        
    def rollback_operation(self, operation_id: int) -> Dict:
        """Generate rollback command for an operation"""
        history = self.get_history()
        
        for op in history:
            if op.get("id") == operation_id:
                # Generate rollback based on operation type
                rollback_cmd = self._generate_rollback(op)
                return {
                    "original_operation": op,
                    "rollback_command": rollback_cmd,
                    "description": f"Rollback for: {op['description']}"
                }
                
        return None
        
    def _generate_rollback(self, operation: Dict) -> List[str]:
        """Generate rollback command based on operation type"""
        cmd = operation.get("command", [])
        
        if not cmd:
            return ["echo", "No rollback available"]
            
        # pip install -> pip uninstall
        if cmd[0] == "pip" and len(cmd) > 2 and cmd[1] == "install":
            return ["pip", "uninstall", "-y"] + cmd[2:]
            
        # brew install -> brew uninstall
        elif cmd[0] == "brew" and len(cmd) > 2 and cmd[1] == "install":
            return ["brew", "uninstall"] + cmd[2:]
            
        # chmod -> restore original permissions (if known)
        elif cmd[0] == "chmod" and len(cmd) > 2:
            # This is a placeholder - would need to store original permissions
            return ["echo", f"Manual restoration needed for: {' '.join(cmd[2:])}"]
            
        else:
            return ["echo", f"No automated rollback for: {' '.join(cmd)}"]
