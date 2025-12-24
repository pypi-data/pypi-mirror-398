from cs_framework.core.concept import Concept
from pydantic import BaseModel
from typing import Any, Dict

class MovedEvent(BaseModel):
    x: int
    y: int
    name: str

class Ghost(Concept):
    """
    Concept: Ghost
    Emits Events: moved
    """
    __events__ = {
        "moved": MovedEvent
    }

    def __init__(self, name: str = "Ghost", start_x: int = 5, start_y: int = 5, color: str = "red"):
        super().__init__(name)
        self._state = {
            "x": start_x,
            "y": start_y,
            "color": color,
            "target_x": 0,
            "target_y": 0
        }

    def update_target(self, payload: dict):
        """
        Action: update_target
        """
        self._state["target_x"] = payload.get("x", 0)
        self._state["target_y"] = payload.get("y", 0)

    def move(self, payload: dict):
        """
        Action: move
        """
        # Simple Chase AI
        tx, ty = self._state["target_x"], self._state["target_y"]
        x, y = self._state["x"], self._state["y"]
        
        if x < tx: x += 1
        elif x > tx: x -= 1
        elif y < ty: y += 1
        elif y > ty: y -= 1
        
        self._state["x"] = x
        self._state["y"] = y
        
        self.emit("moved", MovedEvent(x=x, y=y, name=self.name))

    def teleport(self, payload: dict):
        """
        Action: teleport
        """
        self._state["x"] = payload.get("x", 0)
        self._state["y"] = payload.get("y", 0)
        self.emit("moved", MovedEvent(x=self._state["x"], y=self._state["y"], name=self.name))

