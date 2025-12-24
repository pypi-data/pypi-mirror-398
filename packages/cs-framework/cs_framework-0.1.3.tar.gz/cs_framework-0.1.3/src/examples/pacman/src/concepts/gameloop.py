from cs_framework.core.concept import Concept
from pydantic import BaseModel
from typing import Any, Dict

class TickedEvent(BaseModel):
    tick: int

class GameOverEvent(BaseModel):
    pass

class GameLoop(Concept):
    """
    Concept: GameLoop
    Emits Events: ticked, game_over
    """
    __events__ = {
        "ticked": TickedEvent,
        "game_over": GameOverEvent
    }

    def __init__(self, name: str = "GameLoop"):
        super().__init__(name)
        self._state = {
            "tick_count": 0,
            "score": 0,
            "status": "playing"
        }

    def start(self, payload: dict):
        """
        Action: start
        """
        self._state["status"] = "playing"

    def tick(self, payload: dict):
        """
        Action: tick
        """
        if self._state["status"] == "playing":
            self._state["tick_count"] += 1
            self.emit("ticked", TickedEvent(tick=self._state["tick_count"]))

    def end_game(self, payload: dict):
        """
        Action: end_game
        """
        self._state["status"] = "game_over"
        self.emit("game_over", GameOverEvent())

    def add_score(self, payload: dict):
        """
        Action: add_score
        """
        points = payload.get("points", 0)
        self._state["score"] += points

