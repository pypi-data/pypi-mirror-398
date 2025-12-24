from cs_framework.core.concept import Concept
from pydantic import BaseModel
from typing import Any, Dict

class MovedEvent(BaseModel):
    x: int
    y: int
    name: str

class DiedEvent(BaseModel):
    pass

class Pacman(Concept):
    """
    Concept: Pacman
    Emits Events: moved, died
    """
    __events__ = {
        "moved": MovedEvent,
        "died": DiedEvent
    }

    def __init__(self, name: str = "Pacman", start_x: int = 0, start_y: int = 0):
        super().__init__(name)
        self._state = {
            "x": start_x,
            "y": start_y,
            "direction": "RIGHT",
            "is_alive": True
        }

    def move(self, payload: dict):
        """
        Action: move
        """
        if not self._state["is_alive"]:
            return

        direction = self._state["direction"]
        if direction == "UP": self._state["y"] -= 1
        elif direction == "DOWN": self._state["y"] += 1
        elif direction == "LEFT": self._state["x"] -= 1
        elif direction == "RIGHT": self._state["x"] += 1
        
        self.emit("moved", MovedEvent(x=self._state["x"], y=self._state["y"], name=self.name))

    def change_direction(self, payload: dict):
        """
        Action: change_direction
        """
        self._state["direction"] = payload.get("direction", "RIGHT")

    def die(self, payload: dict):
        """
        Action: die
        """
        self._state["is_alive"] = False
        self.emit("died", DiedEvent())

    def teleport(self, payload: dict):
        """
        Action: teleport
        """
        self._state["x"] = payload.get("x", 0)
        self._state["y"] = payload.get("y", 0)
        # Re-emit moved so rendering updates, but be careful of infinite loops if not handled
        # In this case, teleport is result of moved -> out_of_bounds, so emitting moved again is fine 
        # AS LONG AS the new position is valid.
        self.emit("moved", MovedEvent(x=self._state["x"], y=self._state["y"], name=self.name))

