import sys
import os
import time

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from cs_framework.core.synchronization import Synchronization
from cs_framework.core.event import EventPattern, ActionInvocation
from cs_framework.engine.runner import Runner
from cs_framework.logging.logger import RDFLogger
from concepts import TetrisEngine, ScoreBoard, InputController

def main():
    # Concepts
    engine = TetrisEngine("TetrisEngine")
    score = ScoreBoard("ScoreBoard")
    input_ctrl = InputController("Input")

    # Synchronizations
    
    # 1. Input -> Engine
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
    
    # 2. Engine -> Score
    sync_score = Synchronization(
        name="UpdateScoreOnClear",
        when=EventPattern(engine, "LinesCleared"),
        then=[ActionInvocation(score, "add_score", lambda e: {"count": e.payload["count"]})]
    )

    # Setup Runner
    logger = RDFLogger(log_file="tetris_execution.ttl", console_output=True)
    runner = Runner(logger=logger)
    
    runner.register(engine)
    runner.register(score)
    runner.register(input_ctrl)
    runner.register(sync_left)
    runner.register(sync_right)
    runner.register(sync_score)

    print("Starting Tetris Simulation...")

    # Simulation Loop
    # Tick 1: Spawn
    runner.dispatch(engine.id, "tick", {})
    
    # Tick 2: Move Down
    runner.dispatch(engine.id, "tick", {})
    
    # Input: Move Left
    runner.dispatch(input_ctrl.id, "press_key", {"key": "left"})
    
    # Tick 3: Move Down
    runner.dispatch(engine.id, "tick", {})
    
    # Fast forward to bottom (Simulate many ticks)
    for _ in range(18):
        runner.dispatch(engine.id, "tick", {})
        
    print("Simulation finished. Log saved to tetris_execution.ttl")

if __name__ == "__main__":
    main()
