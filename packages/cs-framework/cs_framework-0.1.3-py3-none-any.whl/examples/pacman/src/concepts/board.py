from cs_framework.core.concept import Concept
from pydantic import BaseModel
from typing import Any, Dict

class OutOfBoundsEvent(BaseModel):
    target: str
    x: int
    y: int

class CollisionDetectedEvent(BaseModel):
    type: str
    target: str

class PelletEatenEvent(BaseModel):
    points: int

class Board(Concept):
    """
    Concept: Board
    Emits Events: pellet_eaten, collision_detected, out_of_bounds
    """
    __events__ = {
        "out_of_bounds": OutOfBoundsEvent,
        "collision_detected": CollisionDetectedEvent,
        "pellet_eaten": PelletEatenEvent
    }

    def __init__(self, name: str = "Board", width: int = 10, height: int = 10):
        super().__init__(name)
        # Generate more pellets
        pellets = []
        for y in range(height):
            for x in range(width):
                if (x + y) % 2 == 0: # Checkerboard pattern
                    pellets.append({"x": x, "y": y})
        
        self._state = {
            "width": width,
            "height": height,
            "pellets": pellets,
            "walls": [],
            "entities": {} # { "Pacman": {x, y}, "Ghost": {x, y} }
        }

    def update_entity_position(self, payload: dict):
        """
        Action: update_entity_position
        Updates entity position and checks for collisions/boundaries.
        Payload: { "name": "Pacman", "x": 1, "y": 2 }
        """
        name = payload.get("name", "Unknown")
        x = payload.get("x")
        y = payload.get("y")
        
        # 1. Boundary Check (Wrap-around)
        width = self._state["width"]
        height = self._state["height"]
        
        if x < 0:
            self.emit("out_of_bounds", OutOfBoundsEvent(target=name, x=width - 1, y=y))
            return
        elif x >= width:
            self.emit("out_of_bounds", OutOfBoundsEvent(target=name, x=0, y=y))
            return
        elif y < 0:
            self.emit("out_of_bounds", OutOfBoundsEvent(target=name, x=x, y=height - 1))
            return
        elif y >= height:
            self.emit("out_of_bounds", OutOfBoundsEvent(target=name, x=x, y=0))
            return

        # Update internal state
        self._state["entities"][name] = {"x": x, "y": y}

        # 2. Entity Collision Check (Pacman vs Ghost)
        if name == "Pacman":
            # Check against all Ghosts
            for ename, pos in self._state["entities"].items():
                if "Ghost" in ename and pos["x"] == x and pos["y"] == y:
                    self.emit("collision_detected", CollisionDetectedEvent(type="ghost", target=name))
        elif "Ghost" in name:
            # Check against Pacman
            pacman_pos = self._state["entities"].get("Pacman")
            if pacman_pos and pacman_pos["x"] == x and pacman_pos["y"] == y:
                self.emit("collision_detected", CollisionDetectedEvent(type="ghost", target="Pacman"))

        # 3. Pellet Check (Only for Pacman)
        if name == "Pacman":
            pellets = self._state["pellets"]
            for p in pellets:
                if p["x"] == x and p["y"] == y:
                    pellets.remove(p)
                    self.emit("pellet_eaten", PelletEatenEvent(points=10))
                    break


