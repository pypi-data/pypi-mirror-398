from cs_framework.core.concept import Concept
from pydantic import BaseModel
from typing import Any, Dict

class InputReceivedEvent(BaseModel):
    key: str

class InputSystem(Concept):
    """
    Concept: InputSystem
    Emits Events: input_received
    """
    __events__ = {
        "input_received": InputReceivedEvent
    }

    def __init__(self, name: str = "InputSystem"):
        super().__init__(name)
        self._state = {"last_key": None}

    def receive_input(self, payload: dict):
        """
        Action: receive_input
        """
        key = payload.get("key")
        self._state["last_key"] = key
        self.emit("input_received", InputReceivedEvent(key=key))

