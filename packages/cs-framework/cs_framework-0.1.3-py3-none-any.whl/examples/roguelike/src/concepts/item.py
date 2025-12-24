from cs_framework.core.concept import Concept
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import random


class SpawnedEvent(BaseModel):
    item_id: str
    x: int
    y: int
    item_type: str


class PickedUpEvent(BaseModel):
    item_id: str
    item_type: str
    picker_name: str


class UsedEvent(BaseModel):
    item_id: str
    item_type: str
    effect_value: int
    user_name: str


class Item(Concept):
    """
    Concept: Item
    Manages items in the dungeon.
    """
    __events__ = {
        "spawned": SpawnedEvent,
        "picked_up": PickedUpEvent,
        "used": UsedEvent
    }
    
    ITEM_TYPES = {
        "health_potion": {"char": "!", "effect": "heal", "value": 10},
        "strength_potion": {"char": "+", "effect": "attack_boost", "value": 2},
    }

    def __init__(self, name: str = "ItemManager"):
        super().__init__(name)
        self._state = {
            "items": [],  # List of {id, x, y, type, picked_up}
            "next_id": 0
        }

    def spawn(self, payload: dict):
        """
        Action: spawn
        Spawn a new item at a position.
        """
        x = payload.get("x", 0)
        y = payload.get("y", 0)
        item_type = payload.get("item_type", "health_potion")
        
        item_id = f"item_{self._state['next_id']}"
        self._state["next_id"] += 1
        
        item = {
            "id": item_id,
            "x": x,
            "y": y,
            "type": item_type,
            "picked_up": False
        }
        self._state["items"].append(item)
        
        self.emit("spawned", SpawnedEvent(
            item_id=item_id,
            x=x,
            y=y,
            item_type=item_type
        ))

    def pickup(self, payload: dict):
        """
        Action: pickup
        Pick up an item at a position.
        """
        x = payload.get("x", 0)
        y = payload.get("y", 0)
        picker_name = payload.get("picker_name", "Player")
        
        for item in self._state["items"]:
            if item["x"] == x and item["y"] == y and not item["picked_up"]:
                item["picked_up"] = True
                self.emit("picked_up", PickedUpEvent(
                    item_id=item["id"],
                    item_type=item["type"],
                    picker_name=picker_name
                ))
                return item
        
        return None

    def use(self, payload: dict):
        """
        Action: use
        Use an item from inventory.
        """
        item_id = payload.get("item_id", "")
        item_type = payload.get("item_type", "health_potion")
        user_name = payload.get("user_name", "Player")
        
        item_info = self.ITEM_TYPES.get(item_type, self.ITEM_TYPES["health_potion"])
        
        self.emit("used", UsedEvent(
            item_id=item_id,
            item_type=item_type,
            effect_value=item_info["value"],
            user_name=user_name
        ))

    def get_items_at(self, x: int, y: int) -> List[dict]:
        """Get unpicked items at a position."""
        return [item for item in self._state["items"] 
                if item["x"] == x and item["y"] == y and not item["picked_up"]]

    def get_all_items(self) -> List[dict]:
        """Get all unpicked items."""
        return [item for item in self._state["items"] if not item["picked_up"]]
