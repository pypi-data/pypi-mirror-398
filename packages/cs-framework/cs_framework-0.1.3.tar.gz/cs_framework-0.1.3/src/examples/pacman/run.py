import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from cs_framework.engine.runner import Runner
from cs_framework.core.yaml_loader import YamlLoader
from cs_framework.logging.logger import RDFLogger
from examples.pacman.src.concepts.pacman import Pacman
from examples.pacman.src.concepts.ghost import Ghost
from examples.pacman.src.concepts.board import Board
from examples.pacman.src.concepts.gameloop import GameLoop
from examples.pacman.src.concepts.inputsystem import InputSystem

def get_runner():
    # Disable console output for game loop to avoid flicker, but keep file logging
    logger = RDFLogger("src/examples/pacman/execution.ttl", console_output=False)
    runner = Runner(logger=logger)

    # Instantiate Concepts
    pacman = Pacman("Pacman", start_x=0, start_y=0)
    ghost = Ghost("Ghost", start_x=5, start_y=5, color="red")
    board = Board("Board", width=10, height=10)
    game_loop = GameLoop("GameLoop")
    input_system = InputSystem("InputSystem")

    # Register Concepts
    runner.register(pacman)
    runner.register(ghost)
    runner.register(board)
    runner.register(game_loop)
    runner.register(input_system)

    # Load Synchronizations
    loader = YamlLoader(runner)
    loader.load("src/examples/pacman/src/sync/rules.yaml")
    
    return runner

if __name__ == "__main__":
    runner = get_runner()
    runner.start()
    
    # Manual run for testing
    input_sys = runner.get_concept_by_name("InputSystem")
    game_loop = runner.get_concept_by_name("GameLoop")
    
    runner.dispatch(input_sys.id, "receive_input", {"key": "RIGHT"})
    runner.dispatch(game_loop.id, "tick", {})
    runner.dispatch(game_loop.id, "tick", {})
    runner.dispatch(game_loop.id, "tick", {})
