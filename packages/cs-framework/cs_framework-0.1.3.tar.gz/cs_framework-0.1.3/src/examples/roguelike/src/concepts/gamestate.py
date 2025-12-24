from cs_framework.core.concept import Concept
from pydantic import BaseModel
from typing import Any, Dict, List


class TurnEndedEvent(BaseModel):
    turn: int
    floor: int


class GameEndedEvent(BaseModel):
    victory: bool
    turns: int
    floor: int


class MessageAddedEvent(BaseModel):
    message: str
    turn: int


class GameState(Concept):
    """
    Concept: GameState
    Manages the overall game state.
    """
    __events__ = {
        "turn_ended": TurnEndedEvent,
        "game_ended": GameEndedEvent,
        "message_added": MessageAddedEvent
    }

    def __init__(self, name: str = "GameState"):
        super().__init__(name)
        self._state = {
            "turn": 0,
            "floor": 1,
            "status": "playing",  # playing, game_over, victory
            "messages": [],
            "max_messages": 5
        }

    def next_turn(self, payload: dict):
        """
        Action: next_turn
        Advance to the next turn.
        """
        if self._state["status"] != "playing":
            return
        
        self._state["turn"] += 1
        
        self.emit("turn_ended", TurnEndedEvent(
            turn=self._state["turn"],
            floor=self._state["floor"]
        ))

    def end_game(self, payload: dict):
        """
        Action: end_game
        End the game (victory or defeat).
        """
        victory = payload.get("victory", False)
        
        if victory:
            self._state["status"] = "victory"
        else:
            self._state["status"] = "game_over"
        
        self.emit("game_ended", GameEndedEvent(
            victory=victory,
            turns=self._state["turn"],
            floor=self._state["floor"]
        ))

    def add_message(self, payload: dict):
        """
        Action: add_message
        Add a message to the game log.
        """
        message = payload.get("message", "")
        
        self._state["messages"].append({
            "text": message,
            "turn": self._state["turn"]
        })
        
        # Keep only recent messages
        while len(self._state["messages"]) > self._state["max_messages"]:
            self._state["messages"].pop(0)
        
        self.emit("message_added", MessageAddedEvent(
            message=message,
            turn=self._state["turn"]
        ))

    def next_floor(self, payload: dict = None):
        """
        Action: next_floor
        Advance to the next floor.
        """
        self._state["floor"] += 1
        self.add_message({"message": f"You descend to floor {self._state['floor']}."})

    def get_messages(self) -> List[str]:
        """Get recent messages."""
        return [m["text"] for m in self._state["messages"]]
