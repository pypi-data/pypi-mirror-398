from cs_framework.core.concept import Concept
from pydantic import BaseModel
from typing import Any, Dict, Optional


class MovedEvent(BaseModel):
    x: int
    y: int
    name: str


class AttackedEvent(BaseModel):
    target_x: int
    target_y: int
    attacker_name: str
    attack_power: int


class DamagedEvent(BaseModel):
    amount: int
    remaining_hp: int
    name: str


class HealedEvent(BaseModel):
    amount: int
    current_hp: int
    name: str


class DiedEvent(BaseModel):
    name: str


class LeveledUpEvent(BaseModel):
    new_level: int
    name: str


class Player(Concept):
    """
    Concept: Player
    The player character in the roguelike game.
    """
    __events__ = {
        "moved": MovedEvent,
        "attacked": AttackedEvent,
        "damaged": DamagedEvent,
        "healed": HealedEvent,
        "died": DiedEvent,
        "leveled_up": LeveledUpEvent
    }

    def __init__(self, name: str = "Player", start_x: int = 1, start_y: int = 1):
        super().__init__(name)
        self._state = {
            "x": start_x,
            "y": start_y,
            "hp": 30,
            "max_hp": 30,
            "attack": 5,
            "defense": 2,
            "level": 1,
            "exp": 0,
            "exp_to_level": 10,
            "is_alive": True
        }

    def move(self, payload: dict):
        """
        Action: move
        Move the player in a direction (dx, dy).
        """
        if not self._state["is_alive"]:
            return
        
        dx = payload.get("dx", 0)
        dy = payload.get("dy", 0)
        
        new_x = self._state["x"] + dx
        new_y = self._state["y"] + dy
        
        self._state["x"] = new_x
        self._state["y"] = new_y
        
        self.emit("moved", MovedEvent(
            x=new_x,
            y=new_y,
            name=self.name
        ))

    def attack(self, payload: dict):
        """
        Action: attack
        Attack in the direction the player is facing.
        """
        if not self._state["is_alive"]:
            return
        
        dx = payload.get("dx", 0)
        dy = payload.get("dy", 0)
        target_x = self._state["x"] + dx
        target_y = self._state["y"] + dy
        
        self.emit("attacked", AttackedEvent(
            target_x=target_x,
            target_y=target_y,
            attacker_name=self.name,
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
            name=self.name
        ))
        
        if self._state["hp"] <= 0:
            self._state["is_alive"] = False
            self.emit("died", DiedEvent(name=self.name))

    def heal(self, payload: dict):
        """
        Action: heal
        Restore HP.
        """
        if not self._state["is_alive"]:
            return
        
        amount = payload.get("amount", 5)
        old_hp = self._state["hp"]
        self._state["hp"] = min(self._state["max_hp"], self._state["hp"] + amount)
        actual_heal = self._state["hp"] - old_hp
        
        if actual_heal > 0:
            self.emit("healed", HealedEvent(
                amount=actual_heal,
                current_hp=self._state["hp"],
                name=self.name
            ))

    def die(self, payload: dict):
        """
        Action: die
        Force the player to die.
        """
        self._state["is_alive"] = False
        self._state["hp"] = 0
        self.emit("died", DiedEvent(name=self.name))

    def gain_exp(self, payload: dict):
        """
        Action: gain_exp
        Gain experience points and level up if threshold is reached.
        """
        if not self._state["is_alive"]:
            return
        
        exp_gained = payload.get("amount", 0)
        self._state["exp"] += exp_gained
        
        # Check for level up
        while self._state["exp"] >= self._state["exp_to_level"]:
            self._state["exp"] -= self._state["exp_to_level"]
            self._state["level"] += 1
            self._state["exp_to_level"] = int(self._state["exp_to_level"] * 1.5)
            
            # Stat increases on level up
            self._state["max_hp"] += 5
            self._state["hp"] = self._state["max_hp"]
            self._state["attack"] += 2
            self._state["defense"] += 1
            
            self.emit("leveled_up", LeveledUpEvent(
                new_level=self._state["level"],
                name=self.name
            ))
