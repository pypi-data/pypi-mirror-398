import sys
import os
import time
import msvcrt
import copy

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from cs_framework.core.synchronization import Synchronization
from cs_framework.core.event import EventPattern, ActionInvocation
from cs_framework.engine.runner import Runner
from cs_framework.logging.logger import RDFLogger
from concepts import TetrisEngine, ScoreBoard, InputController

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def render(engine, score):
    # Create a display grid (copy of static grid)
    grid = copy.deepcopy(engine._state["grid"])
    piece = engine._state["current_piece"]
    
    # Overlay current piece
    if piece:
        px, py = piece["x"], piece["y"]
        # Simple 1x1 piece for T shape center for now, or let's just render the center
        # The concept says "T", let's just render a block at x,y for simplicity
        if 0 <= py < 20 and 0 <= px < 10:
            grid[py][px] = 2 # 2 = current piece

    buffer = []
    buffer.append(f"Score: {score._state['score']}  Lines: {score._state['lines']}")
    buffer.append("+" + "-" * 20 + "+")
    for row in grid:
        line = "|"
        for cell in row:
            if cell == 0:
                line += " ."
            elif cell == 1:
                line += "[]" # Locked
            elif cell == 2:
                line += "<>" # Current
        line += "|"
        buffer.append(line)
    buffer.append("+" + "-" * 20 + "+")
    buffer.append("Controls: A (Left), D (Right), S (Drop/Tick), Q (Quit)")
    
    # Move cursor to top-left (ANSI escape code) or just clear
    # clear_screen() causes flickering. 
    # Better to print a lot of newlines or use ANSI if supported.
    # Windows pwsh supports ANSI.
    print("\033[H\033[J", end="") 
    print("\n".join(buffer))

def main():
    # Concepts
    engine = TetrisEngine("TetrisEngine")
    score = ScoreBoard("ScoreBoard")
    input_ctrl = InputController("Input")

    # Synchronizations
    sync_left = Synchronization(
        name="InputMoveLeft",
        when=EventPattern(input_ctrl, "LeftPressed"),
        then=[ActionInvocation(engine, "move_left", lambda e: {})]
    )
    sync_right = Synchronization(
        name="InputMoveRight",
        when=EventPattern(input_ctrl, "RightPressed"),
        then=[ActionInvocation(engine, "move_right", lambda e: {})]
    )
    sync_down = Synchronization(
        name="InputMoveDown",
        when=EventPattern(input_ctrl, "DownPressed"),
        then=[ActionInvocation(engine, "tick", lambda e: {})] # Manual tick
    )
    sync_score = Synchronization(
        name="UpdateScoreOnClear",
        when=EventPattern(engine, "LinesCleared"),
        then=[ActionInvocation(score, "add_score", lambda e: {"count": e.payload["count"]})]
    )

    # Setup Runner
    # We use a file logger so the GUI can pick it up
    # Throttle saving to once every 0.5 seconds to prevent I/O lag
    logger = RDFLogger(log_file="tetris_execution.ttl", console_output=False, save_interval=0.5) 
    runner = Runner(logger=logger)
    
    runner.register(engine)
    runner.register(score)
    runner.register(input_ctrl)
    runner.register(sync_left)
    runner.register(sync_right)
    runner.register(sync_down)
    runner.register(sync_score)

    print("Initializing Interactive Tetris...")
    time.sleep(1)

    last_tick = time.time()
    tick_interval = 1.0

    while True:
        # 1. Input Handling - Drain the buffer!
        # Process all pending keys to avoid "stuck key" effect due to OS buffer buildup
        while msvcrt.kbhit():
            ch = msvcrt.getch()
            if ch in (b'\x00', b'\xe0'):
                # Special key (arrows, etc), read next byte and ignore for now
                msvcrt.getch()
                key = ''
            else:
                try:
                    key = ch.decode('utf-8').lower()
                except UnicodeDecodeError:
                    key = ''

            if key == 'q':
                # Dispatch Quit event before exiting to log it in C-S
                runner.dispatch(input_ctrl.id, "press_key", {"key": "quit"})
                time.sleep(0.1) # Wait for event to be processed/logged
                # Force save log before quitting
                logger.last_save_time = 0 
                logger.save()
                return # Exit main loop
            elif key == 'a':
                runner.dispatch(input_ctrl.id, "press_key", {"key": "left"})
            elif key == 'd':
                runner.dispatch(input_ctrl.id, "press_key", {"key": "right"})
            elif key == 's':
                runner.dispatch(input_ctrl.id, "press_key", {"key": "down"})
        
        # 2. Auto Tick
        current_time = time.time()
        if current_time - last_tick > tick_interval:
            runner.dispatch(engine.id, "tick", {})
            last_tick = current_time

        # 3. Render
        render(engine, score)
        
        if engine._state["game_over"]:
            print("\nGame Over!")
            # Force save log
            logger.last_save_time = 0
            logger.save()
            break
        
        # Small sleep to prevent CPU hogging
        time.sleep(0.05)

    print("Game Over. Log saved to tetris_execution.ttl")

if __name__ == "__main__":
    main()
