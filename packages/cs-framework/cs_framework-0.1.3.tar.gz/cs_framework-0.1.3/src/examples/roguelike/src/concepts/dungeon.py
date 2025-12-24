from cs_framework.core.concept import Concept
from pydantic import BaseModel
from typing import Any, Dict, List, Tuple, Optional
import random


class GeneratedEvent(BaseModel):
    width: int
    height: int
    floor: int


class TileRevealedEvent(BaseModel):
    x: int
    y: int
    tile_type: str


class Dungeon(Concept):
    """
    Concept: Dungeon
    Manages the dungeon map with procedural generation.
    """
    __events__ = {
        "generated": GeneratedEvent,
        "tile_revealed": TileRevealedEvent
    }
    
    TILE_WALL = 0
    TILE_FLOOR = 1
    TILE_STAIRS = 2

    def __init__(self, name: str = "Dungeon", width: int = 40, height: int = 25):
        super().__init__(name)
        self._state = {
            "width": width,
            "height": height,
            "tiles": [[self.TILE_WALL for _ in range(width)] for _ in range(height)],
            "rooms": [],
            "floor": 1,
            "stairs_x": 0,
            "stairs_y": 0
        }

    def generate(self, payload: dict):
        """
        Action: generate
        Generate a new dungeon floor using simple room-based algorithm.
        """
        floor = payload.get("floor", self._state["floor"])
        self._state["floor"] = floor
        
        width = self._state["width"]
        height = self._state["height"]
        
        # Reset tiles to all walls
        self._state["tiles"] = [[self.TILE_WALL for _ in range(width)] for _ in range(height)]
        self._state["rooms"] = []
        
        # Generate rooms
        num_rooms = random.randint(5, 8)
        for _ in range(num_rooms * 3):  # Try multiple times
            if len(self._state["rooms"]) >= num_rooms:
                break
            
            # Random room dimensions
            room_w = random.randint(4, 8)
            room_h = random.randint(4, 6)
            room_x = random.randint(1, width - room_w - 1)
            room_y = random.randint(1, height - room_h - 1)
            
            # Check overlap with existing rooms
            new_room = {"x": room_x, "y": room_y, "w": room_w, "h": room_h}
            overlaps = False
            for room in self._state["rooms"]:
                if self._rooms_overlap(new_room, room):
                    overlaps = True
                    break
            
            if not overlaps:
                self._state["rooms"].append(new_room)
                self._carve_room(new_room)
        
        # Connect rooms with corridors
        for i in range(1, len(self._state["rooms"])):
            prev_room = self._state["rooms"][i - 1]
            curr_room = self._state["rooms"][i]
            self._connect_rooms(prev_room, curr_room)
        
        # Place stairs in the last room
        if self._state["rooms"]:
            last_room = self._state["rooms"][-1]
            stairs_x = last_room["x"] + last_room["w"] // 2
            stairs_y = last_room["y"] + last_room["h"] // 2
            self._state["tiles"][stairs_y][stairs_x] = self.TILE_STAIRS
            self._state["stairs_x"] = stairs_x
            self._state["stairs_y"] = stairs_y
        
        self.emit("generated", GeneratedEvent(
            width=width,
            height=height,
            floor=floor
        ))

    def _rooms_overlap(self, room1: dict, room2: dict) -> bool:
        """Check if two rooms overlap (with padding)."""
        return (room1["x"] < room2["x"] + room2["w"] + 1 and
                room1["x"] + room1["w"] + 1 > room2["x"] and
                room1["y"] < room2["y"] + room2["h"] + 1 and
                room1["y"] + room1["h"] + 1 > room2["y"])

    def _carve_room(self, room: dict):
        """Carve out a room in the tiles."""
        for y in range(room["y"], room["y"] + room["h"]):
            for x in range(room["x"], room["x"] + room["w"]):
                self._state["tiles"][y][x] = self.TILE_FLOOR

    def _connect_rooms(self, room1: dict, room2: dict):
        """Connect two rooms with an L-shaped corridor."""
        x1 = room1["x"] + room1["w"] // 2
        y1 = room1["y"] + room1["h"] // 2
        x2 = room2["x"] + room2["w"] // 2
        y2 = room2["y"] + room2["h"] // 2
        
        # Randomly choose horizontal-first or vertical-first
        if random.random() < 0.5:
            self._carve_h_tunnel(x1, x2, y1)
            self._carve_v_tunnel(y1, y2, x2)
        else:
            self._carve_v_tunnel(y1, y2, x1)
            self._carve_h_tunnel(x1, x2, y2)

    def _carve_h_tunnel(self, x1: int, x2: int, y: int):
        """Carve a horizontal tunnel."""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= y < self._state["height"] and 0 <= x < self._state["width"]:
                self._state["tiles"][y][x] = self.TILE_FLOOR

    def _carve_v_tunnel(self, y1: int, y2: int, x: int):
        """Carve a vertical tunnel."""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= y < self._state["height"] and 0 <= x < self._state["width"]:
                self._state["tiles"][y][x] = self.TILE_FLOOR

    def check_tile(self, payload: dict) -> int:
        """
        Action: check_tile
        Check the tile type at a given position.
        Returns: 0 = wall, 1 = floor, 2 = stairs
        """
        x = payload.get("x", 0)
        y = payload.get("y", 0)
        
        if 0 <= x < self._state["width"] and 0 <= y < self._state["height"]:
            return self._state["tiles"][y][x]
        return self.TILE_WALL

    def get_neighbors(self, payload: dict) -> List[Tuple[int, int]]:
        """
        Action: get_neighbors
        Get walkable neighboring tiles.
        """
        x = payload.get("x", 0)
        y = payload.get("y", 0)
        neighbors = []
        
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self._state["width"] and 0 <= ny < self._state["height"]:
                if self._state["tiles"][ny][nx] != self.TILE_WALL:
                    neighbors.append((nx, ny))
        
        return neighbors

    def get_player_start(self) -> Tuple[int, int]:
        """Get the starting position for the player (center of first room)."""
        if self._state["rooms"]:
            first_room = self._state["rooms"][0]
            return (first_room["x"] + first_room["w"] // 2,
                    first_room["y"] + first_room["h"] // 2)
        return (1, 1)

    def get_monster_spawn_positions(self, count: int) -> List[Tuple[int, int]]:
        """Get spawn positions for monsters (in rooms, not first room)."""
        positions = []
        for room in self._state["rooms"][1:]:  # Skip first room
            cx = room["x"] + room["w"] // 2
            cy = room["y"] + room["h"] // 2
            positions.append((cx, cy))
            if len(positions) >= count:
                break
        return positions
