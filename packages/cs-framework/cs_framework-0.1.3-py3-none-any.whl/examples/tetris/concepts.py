import random
from cs_framework.core.concept import Concept

class TetrisEngine(Concept):
    def __init__(self, name="TetrisEngine"):
        super().__init__(name)
        # 10x20 grid, 0=empty, 1=filled
        self._state = {
            "grid": [[0 for _ in range(10)] for _ in range(20)],
            "current_piece": None, # {x, y, shape}
            "game_over": False
        }
        self.spawn_piece({})

    def spawn_piece(self, payload):
        if self._state["game_over"]:
            return
            
        # Check collision at spawn point (4, 0)
        if self._state["grid"][0][4] != 0:
            self._state["game_over"] = True
            self.emit("GameOver", {})
            return

        self._state["current_piece"] = {
            "x": 4,
            "y": 0,
            "shape": "T" # Simplified, always T for demo
        }
        self.emit("PieceSpawned", self._state["current_piece"])

    def _is_valid(self, x, y):
        # Check boundaries
        if x < 0 or x >= 10:
            return False
        if y >= 20:
            return False
        if y < 0:
            return True # Allow spawning above
        
        # Check collision with grid
        if self._state["grid"][y][x] != 0:
            return False
        return True

    def tick(self, payload):
        if self._state["game_over"]:
            return

        piece = self._state["current_piece"]
        if not piece:
            self.spawn_piece({})
            return

        # Try move down
        new_y = piece["y"] + 1
        
        if self._is_valid(piece["x"], new_y):
            piece["y"] = new_y
            self.emit("PieceMoved", {"x": piece["x"], "y": piece["y"]})
        else:
            # Collision detected, lock piece
            self._lock_piece()

    def move_left(self, payload):
        piece = self._state["current_piece"]
        if piece:
            new_x = piece["x"] - 1
            if self._is_valid(new_x, piece["y"]):
                piece["x"] = new_x
                self.emit("PieceMoved", piece)

    def move_right(self, payload):
        piece = self._state["current_piece"]
        if piece:
            new_x = piece["x"] + 1
            if self._is_valid(new_x, piece["y"]):
                piece["x"] = new_x
                self.emit("PieceMoved", piece)

    def _lock_piece(self):
        piece = self._state["current_piece"]
        # Lock it (set grid)
        if 0 <= piece["y"] < 20 and 0 <= piece["x"] < 10:
            self._state["grid"][piece["y"]][piece["x"]] = 1
            self.emit("PieceLocked", {"x": piece["x"], "y": piece["y"]})
        else:
            # Game Over condition if locked above grid
            self._state["game_over"] = True
            return
        
        # Check lines
        lines_cleared = 0
        new_grid = [row for row in self._state["grid"] if not all(cell == 1 for cell in row)]
        lines_cleared = 20 - len(new_grid)
        if lines_cleared > 0:
            # Add empty lines at top
            for _ in range(lines_cleared):
                new_grid.insert(0, [0] * 10)
            self._state["grid"] = new_grid
            self.emit("LinesCleared", {"count": lines_cleared})
        
        self._state["current_piece"] = None
        self.spawn_piece({})

class ScoreBoard(Concept):
    def __init__(self, name="ScoreBoard"):
        super().__init__(name)
        self._state = {"score": 0, "lines": 0}

    def add_score(self, payload):
        lines = payload.get("count", 0)
        points = lines * 100
        self._state["score"] += points
        self._state["lines"] += lines
        self.emit("ScoreUpdated", {"new_score": self._state["score"]})

class InputController(Concept):
    def __init__(self, name="InputController"):
        super().__init__(name)
        self._state = {"last_key": None}

    def press_key(self, payload):
        key = payload.get("key")
        self._state["last_key"] = key
        if key == "left":
            self.emit("LeftPressed", {})
        elif key == "right":
            self.emit("RightPressed", {})
        elif key == "down":
            self.emit("DownPressed", {})
        elif key == "quit":
            self.emit("QuitPressed", {})
