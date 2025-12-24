"""
Roguelike Dungeon Game using C-S Framework and Pyxel
"""
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pyxel

from examples.roguelike.run import get_runner
from examples.roguelike.src.concepts.dungeon import Dungeon


class RoguelikeGame:
    """Main game class using Pyxel for rendering."""
    
    # Tile size in pixels
    TILE_SIZE = 8
    
    # Colors
    COL_WALL = 5       # Dark gray
    COL_FLOOR = 13     # Light gray
    COL_STAIRS = 10    # Yellow
    COL_PLAYER = 11    # Light green
    COL_MONSTER = 8    # Red
    COL_ITEM = 9       # Orange
    COL_TEXT = 7       # White
    COL_HP_BAR = 11    # Green
    COL_HP_EMPTY = 8   # Red
    COL_UI_BG = 1      # Dark blue
    
    def __init__(self):
        # Initialize game
        self.runner = get_runner()
        self.runner.start()
        
        # Get concepts
        self.dungeon = self.runner.get_concept_by_name("Dungeon")
        self.player = self.runner.get_concept_by_name("Player")
        self.game_state = self.runner.get_concept_by_name("GameState")
        self.item_manager = self.runner.get_concept_by_name("ItemManager")
        
        # Get monsters
        self.monsters = []
        for concept in self.runner.concepts.values():
            if concept.name.startswith("Monster_"):
                self.monsters.append(concept)
        
        # Calculate screen size
        dungeon_state = self.dungeon.get_state_snapshot()
        self.map_width = dungeon_state["width"]
        self.map_height = dungeon_state["height"]
        
        screen_width = self.map_width * self.TILE_SIZE
        screen_height = self.map_height * self.TILE_SIZE + 40  # Extra space for UI
        
        # Initialize Pyxel
        pyxel.init(screen_width, screen_height, title="CSFW Roguelike")
        
        # Start game
        pyxel.run(self.update, self.draw)
    
    def update(self):
        """Update game logic."""
        game_status = self.game_state.get_state_snapshot()["status"]
        if game_status != "playing":
            if pyxel.btnp(pyxel.KEY_R):
                self.restart_game()
            return
        
        # Handle input
        player_state = self.player.get_state_snapshot()
        if not player_state["is_alive"]:
            return
        
        dx, dy = 0, 0
        attack = False
        
        if pyxel.btnp(pyxel.KEY_UP) or pyxel.btnp(pyxel.KEY_W):
            dy = -1
        elif pyxel.btnp(pyxel.KEY_DOWN) or pyxel.btnp(pyxel.KEY_S):
            dy = 1
        elif pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_A):
            dx = -1
        elif pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_D):
            dx = 1
        elif pyxel.btnp(pyxel.KEY_SPACE):
            attack = True
        
        if dx != 0 or dy != 0:
            new_x = player_state["x"] + dx
            new_y = player_state["y"] + dy
            
            tile = self.dungeon.check_tile({"x": new_x, "y": new_y})
            
            if tile != Dungeon.TILE_WALL:
                monster_at_pos = self.get_monster_at(new_x, new_y)
                
                if monster_at_pos:
                    self.attack_monster(monster_at_pos)
                else:
                    self.runner.dispatch(self.player.id, "move", {"dx": dx, "dy": dy})
                    
                    if tile == Dungeon.TILE_STAIRS:
                        self.next_floor()
                
                self.end_turn()
        
        elif attack:
            for adx, ady in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ax = player_state["x"] + adx
                ay = player_state["y"] + ady
                monster = self.get_monster_at(ax, ay)
                if monster:
                    self.attack_monster(monster)
                    self.end_turn()
                    break
    
    def get_monster_at(self, x: int, y: int):
        """Get monster at position, or None."""
        for monster in self.monsters:
            state = monster.get_state_snapshot()
            if state["is_alive"] and state["x"] == x and state["y"] == y:
                return monster
        return None
    
    def attack_monster(self, monster):
        """Attack a monster."""
        player_state = self.player.get_state_snapshot()
        monster_state = monster.get_state_snapshot()
        
        self.runner.dispatch(monster.id, "take_damage", {
            "amount": player_state["attack"]
        })
        
        self.game_state.add_message({
            "message": f"Hit {monster_state['monster_type']} for {player_state['attack']} dmg!"
        })
    
    def end_turn(self):
        """End the player's turn and let monsters act."""
        self.runner.dispatch(self.game_state.id, "next_turn", {})
        
        player_state = self.player.get_state_snapshot()
        
        for monster in self.monsters:
            m_state = monster.get_state_snapshot()
            if not m_state["is_alive"]:
                continue
            
            self.runner.dispatch(monster.id, "ai_move", {
                "target_x": player_state["x"],
                "target_y": player_state["y"]
            })
            
            m_state = monster.get_state_snapshot()
            dist_x = abs(m_state["x"] - player_state["x"])
            dist_y = abs(m_state["y"] - player_state["y"])
            
            if dist_x + dist_y == 1:
                self.runner.dispatch(self.player.id, "take_damage", {
                    "amount": m_state["attack"]
                })
                self.game_state.add_message({
                    "message": f"{m_state['monster_type']} attacks!"
                })
    
    def next_floor(self):
        """Go to the next floor."""
        self.game_state.next_floor()
        self.dungeon.generate({"floor": self.game_state.get_state_snapshot()["floor"]})
        
        start_x, start_y = self.dungeon.get_player_start()
        self.player._state["x"] = start_x
        self.player._state["y"] = start_y
        
        spawns = self.dungeon.get_monster_spawn_positions(3)
        for i, monster in enumerate(self.monsters):
            if i < len(spawns):
                monster._state["x"] = spawns[i][0]
                monster._state["y"] = spawns[i][1]
                monster._state["hp"] = monster._state["max_hp"]
                monster._state["is_alive"] = True
    
    def restart_game(self):
        """Restart the game."""
        self.runner = get_runner()
        self.runner.start()
        
        self.dungeon = self.runner.get_concept_by_name("Dungeon")
        self.player = self.runner.get_concept_by_name("Player")
        self.game_state = self.runner.get_concept_by_name("GameState")
        self.item_manager = self.runner.get_concept_by_name("ItemManager")
        
        self.monsters = []
        for concept in self.runner.concepts.values():
            if concept.name.startswith("Monster_"):
                self.monsters.append(concept)
    
    def draw(self):
        """Draw the game."""
        pyxel.cls(0)
        
        # Draw dungeon
        dungeon_state = self.dungeon.get_state_snapshot()
        tiles = dungeon_state["tiles"]
        
        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                px = x * self.TILE_SIZE
                py = y * self.TILE_SIZE
                
                if tile == Dungeon.TILE_WALL:
                    pyxel.rect(px, py, self.TILE_SIZE, self.TILE_SIZE, self.COL_WALL)
                elif tile == Dungeon.TILE_FLOOR:
                    pyxel.rect(px, py, self.TILE_SIZE, self.TILE_SIZE, self.COL_FLOOR)
                elif tile == Dungeon.TILE_STAIRS:
                    pyxel.rect(px, py, self.TILE_SIZE, self.TILE_SIZE, self.COL_STAIRS)
        
        # Draw items
        for item in self.item_manager.get_all_items():
            ix = item["x"] * self.TILE_SIZE + 2
            iy = item["y"] * self.TILE_SIZE + 2
            pyxel.rect(ix, iy, 4, 4, self.COL_ITEM)
        
        # Draw monsters
        for monster in self.monsters:
            m_state = monster.get_state_snapshot()
            if m_state["is_alive"]:
                mx = m_state["x"] * self.TILE_SIZE + 1
                my = m_state["y"] * self.TILE_SIZE + 1
                pyxel.rect(mx, my, 6, 6, self.COL_MONSTER)
        
        # Draw player
        player_state = self.player.get_state_snapshot()
        px = player_state["x"] * self.TILE_SIZE + 1
        py = player_state["y"] * self.TILE_SIZE + 1
        pyxel.rect(px, py, 6, 6, self.COL_PLAYER)
        
        # Draw UI
        ui_y = self.map_height * self.TILE_SIZE
        pyxel.rect(0, ui_y, self.map_width * self.TILE_SIZE, 40, self.COL_UI_BG)
        
        # HP bar
        hp = player_state["hp"]
        max_hp = player_state["max_hp"]
        hp_width = 60
        hp_filled = int(hp_width * hp / max_hp) if max_hp > 0 else 0
        
        pyxel.text(4, ui_y + 4, f"HP:", self.COL_TEXT)
        pyxel.rect(20, ui_y + 4, hp_width, 6, self.COL_HP_EMPTY)
        pyxel.rect(20, ui_y + 4, hp_filled, 6, self.COL_HP_BAR)
        pyxel.text(84, ui_y + 4, f"{hp}/{max_hp}", self.COL_TEXT)
        
        # Stats
        pyxel.text(4, ui_y + 14, f"Lv:{player_state['level']} Atk:{player_state['attack']} Def:{player_state['defense']}", self.COL_TEXT)
        pyxel.text(4, ui_y + 24, f"Floor:{self.game_state.get_state_snapshot()['floor']} Turn:{self.game_state.get_state_snapshot()['turn']}", self.COL_TEXT)
        
        # Messages
        messages = self.game_state.get_messages()
        if messages:
            pyxel.text(140, ui_y + 4, messages[-1][:25], self.COL_TEXT)
        
        # Game over overlay
        game_status = self.game_state.get_state_snapshot()["status"]
        if game_status == "game_over":
            pyxel.text(100, 100, "GAME OVER", 8)
            pyxel.text(90, 115, "Press R to restart", 7)
        elif game_status == "victory":
            pyxel.text(100, 100, "VICTORY!", 11)
            pyxel.text(90, 115, "Press R to restart", 7)


if __name__ == "__main__":
    RoguelikeGame()
