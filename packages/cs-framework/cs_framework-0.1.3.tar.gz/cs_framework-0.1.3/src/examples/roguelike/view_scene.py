import sys
import os
import time

# Add path to import visual_agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from visual_agent import analyze_screen, SCREEN_PATH

if __name__ == "__main__":
    if not os.path.exists(SCREEN_PATH):
        # Trigger help
        print(f"Screen file not found at {SCREEN_PATH}")
        sys.exit(1)
        
    state = analyze_screen()
    if state:
        rows = state["rows"]
        cols = state["cols"]
        grid = state["grid"]
        player = state["player"]
        stairs = state["stairs"]
        monsters = state["monsters"]
        
        print(f"INFO: Player: {player}, Stairs: {stairs}, Monsters: {monsters}")
        print("MAP:")
        for r in range(rows):
            line = ""
            for c in range(cols):
                line += grid[r][c]
            print(line)
    else:
        print("Failed to analyze screen.")
