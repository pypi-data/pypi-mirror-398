from cs_framework.core.concept import Concept
from pydantic import BaseModel
from typing import Any, Dict, Optional
import random


class MovedEvent(BaseModel):
    x: int
    y: int
    monster_id: str
    name: str


class AttackedEvent(BaseModel):
    target_x: int
    target_y: int
    monster_id: str
    attack_power: int


class DamagedEvent(BaseModel):
    amount: int
    remaining_hp: int
    monster_id: str
    name: str


class DiedEvent(BaseModel):
    monster_id: str
    name: str
    exp_value: int


class Monster(Concept):
    """
    Concept: Monster
    An enemy creature in the dungeon.
    """
    __events__ = {
        "moved": MovedEvent,
        "attacked": AttackedEvent,
        "damaged": DamagedEvent,
        "died": DiedEvent
    }

    MONSTER_TYPES = {
        "goblin": {"hp": 10, "attack": 3, "defense": 0, "exp": 5, "char": "g"},
        "orc": {"hp": 20, "attack": 5, "defense": 2, "exp": 15, "char": "O"},
        "troll": {"hp": 35, "attack": 8, "defense": 3, "exp": 30, "char": "T"},
    }

    def __init__(self, name: str = "Monster", monster_id: str = "", 
                 monster_type: str = "goblin", x: int = 0, y: int = 0):
        super().__init__(name)
        stats = self.MONSTER_TYPES.get(monster_type, self.MONSTER_TYPES["goblin"])
        
        self._state = {
            "monster_id": monster_id or f"{monster_type}_{id(self)}",
            "x": x,
            "y": y,
            "hp": stats["hp"],
            "max_hp": stats["hp"],
            "attack": stats["attack"],
            "defense": stats["defense"],
            "exp_value": stats["exp"],
            "monster_type": monster_type,
            "char": stats["char"],
            "is_alive": True,
            "target_x": None,
            "target_y": None
        }

    def ai_move(self, payload: dict):
        """
        Action: ai_move
        Move towards the player using simple AI.
        """
        if not self._state["is_alive"]:
            return
        
        target_x = payload.get("target_x", self._state.get("target_x"))
        target_y = payload.get("target_y", self._state.get("target_y"))
        
        if target_x is None or target_y is None:
            return
        
        # Store target for future reference
        self._state["target_x"] = target_x
        self._state["target_y"] = target_y
        
        # Simple AI: move towards player
        dx = 0
        dy = 0
        
        if self._state["x"] < target_x:
            dx = 1
        elif self._state["x"] > target_x:
            dx = -1
            
        if self._state["y"] < target_y:
            dy = 1
        elif self._state["y"] > target_y:
            dy = -1
        
        # Move one step (prioritize horizontal or vertical randomly)
        if random.random() < 0.5:
            if dx != 0:
                dy = 0
            # else keep dy
        else:
            if dy != 0:
                dx = 0
            # else keep dx
        
        new_x = self._state["x"] + dx
        new_y = self._state["y"] + dy
        
        self._state["x"] = new_x
        self._state["y"] = new_y
        
        self.emit("moved", MovedEvent(
            x=new_x,
            y=new_y,
            monster_id=self._state["monster_id"],
            name=self.name
        ))

    def attack(self, payload: dict):
        """
        Action: attack
        Attack the player.
        """
        if not self._state["is_alive"]:
            return
        
        target_x = payload.get("target_x", self._state["x"])
        target_y = payload.get("target_y", self._state["y"])
        
        self.emit("attacked", AttackedEvent(
            target_x=target_x,
            target_y=target_y,
            monster_id=self._state["monster_id"],
            attack_power=self._state["attack"]
        ))

    def take_damage(self, payload: dict):
        """
        Action: take_damage
        Receive damage from an attack.
        """
        if not self._state["is_alive"]:
            return
        
        raw_damage = payload.get("amount", 0)
        actual_damage = max(1, raw_damage - self._state["defense"])
        
        self._state["hp"] = max(0, self._state["hp"] - actual_damage)
        
        self.emit("damaged", DamagedEvent(
            amount=actual_damage,
            remaining_hp=self._state["hp"],
            monster_id=self._state["monster_id"],
            name=self.name
        ))
        
        if self._state["hp"] <= 0:
            self._state["is_alive"] = False
            self.emit("died", DiedEvent(
                monster_id=self._state["monster_id"],
                name=self.name,
                exp_value=self._state["exp_value"]
            ))

    def die(self, payload: dict):
        """
        Action: die
        Force the monster to die.
        """
        self._state["is_alive"] = False
        self._state["hp"] = 0
        self.emit("died", DiedEvent(
            monster_id=self._state["monster_id"],
            name=self.name,
            exp_value=self._state["exp_value"]
        ))
