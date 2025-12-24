from typing import Callable, Dict, Any, Optional
import uuid

class Invariant:
    def __init__(self, name: str, check_func: Callable[[Dict[uuid.UUID, Dict[str, Any]]], bool], description: Optional[str] = None):
        self.name = name
        self.check_func = check_func
        self.description = description

    def check(self, global_state: Dict[uuid.UUID, Dict[str, Any]]) -> bool:
        try:
            return self.check_func(global_state)
        except Exception as e:
            print(f"Error checking invariant '{self.name}': {e}")
            return False
