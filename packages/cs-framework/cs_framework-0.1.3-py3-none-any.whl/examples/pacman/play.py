import sys
import os
import time
import msvcrt

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from examples.pacman.run import get_runner

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def render(runner):
    # Get Snapshots
    board = runner.get_concept_by_name("Board").get_state_snapshot()
    pacman = runner.get_concept_by_name("Pacman").get_state_snapshot()
    ghost = runner.get_concept_by_name("Ghost").get_state_snapshot()
    game_loop = runner.get_concept_by_name("GameLoop").get_state_snapshot()

    width = board["width"]
    height = board["height"]
    pellets = board["pellets"]
    
    # Create Grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]

    # Draw Pellets
    for p in pellets:
        if 0 <= p["x"] < width and 0 <= p["y"] < height:
            grid[p["y"]][p["x"]] = '.'

    # Draw Ghost
    gx, gy = ghost["x"], ghost["y"]
    if 0 <= gx < width and 0 <= gy < height:
        grid[gy][gx] = 'G'

    # Draw Pacman
    px, py = pacman["x"], pacman["y"]
    if 0 <= px < width and 0 <= py < height:
        grid[py][px] = 'C' if pacman["is_alive"] else 'X'

    # Render to string
    output = []
    output.append(f"Score: {game_loop['score']} | Tick: {game_loop['tick_count']}")
    output.append("-" * (width + 2))
    for row in grid:
        output.append("|" + "".join(row) + "|")
    output.append("-" * (width + 2))
    
    if not pacman["is_alive"]:
        output.append("GAME OVER!")

    # Print all at once to reduce flicker
    clear_screen()
    print("\n".join(output))

def main():
    runner = get_runner()
    runner.start()
    
    input_system_id = runner.get_concept_by_name("InputSystem").id
    game_loop_id = runner.get_concept_by_name("GameLoop").id

    print("Use WASD to move. Press 'q' to quit.")
    time.sleep(2)

    while True:
        # Input Handling
        if msvcrt.kbhit():
            key = msvcrt.getch()
            direction = None
            if key == b'w': direction = "UP"
            elif key == b's': direction = "DOWN"
            elif key == b'a': direction = "LEFT"
            elif key == b'd': direction = "RIGHT"
            elif key == b'q': break
            
            if direction:
                runner.dispatch(input_system_id, "receive_input", {"key": direction})

        # Game Logic
        runner.dispatch(game_loop_id, "tick", {})
        
        # Render
        render(runner)
        
        # Check Game Over
        game_loop = runner.get_concept_by_name("GameLoop").get_state_snapshot()
        if game_loop["status"] == "game_over":
            break

        time.sleep(0.5) # Game speed

if __name__ == "__main__":
    main()
