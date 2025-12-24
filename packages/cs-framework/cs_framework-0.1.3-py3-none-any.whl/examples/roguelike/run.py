import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from cs_framework.engine.runner import Runner
from cs_framework.core.yaml_loader import YamlLoader
from cs_framework.logging.logger import RDFLogger
from examples.roguelike.src.concepts.player import Player
from examples.roguelike.src.concepts.monster import Monster
from examples.roguelike.src.concepts.dungeon import Dungeon
from examples.roguelike.src.concepts.item import Item
from examples.roguelike.src.concepts.gamestate import GameState


def get_runner():
    """Create and configure the game runner."""
    logger = RDFLogger("src/examples/roguelike/execution.ttl", console_output=False)
    runner = Runner(logger=logger)

    # Create Dungeon first and generate map
    dungeon = Dungeon("Dungeon", width=40, height=25)
    dungeon.generate({"floor": 1})
    
    # Get spawn positions
    player_start = dungeon.get_player_start()
    monster_spawns = dungeon.get_monster_spawn_positions(3)

    # Create Player at start position
    player = Player("Player", start_x=player_start[0], start_y=player_start[1])
    
    # Create Monsters
    monsters = []
    monster_types = ["goblin", "goblin", "orc"]
    for i, (mx, my) in enumerate(monster_spawns):
        m_type = monster_types[i] if i < len(monster_types) else "goblin"
        monster = Monster(f"Monster_{i}", monster_id=f"m{i}", 
                         monster_type=m_type, x=mx, y=my)
        monsters.append(monster)
    
    # Create other concepts
    item_manager = Item("ItemManager")
    game_state = GameState("GameState")
    
    # Spawn some items in random rooms
    dungeon_state = dungeon.get_state_snapshot()
    for room in dungeon_state["rooms"][1:3]:  # Items in 2nd and 3rd rooms
        item_manager.spawn({
            "x": room["x"] + 1,
            "y": room["y"] + 1,
            "item_type": "health_potion"
        })

    # Register all concepts
    runner.register(dungeon)
    runner.register(player)
    for monster in monsters:
        runner.register(monster)
    runner.register(item_manager)
    runner.register(game_state)

    # Load synchronization rules
    loader = YamlLoader(runner)
    loader.load("src/examples/roguelike/src/sync/rules.yaml")
    
    return runner


# Export runner for scenario testing
runner = None

def get_or_create_runner():
    global runner
    if runner is None:
        runner = get_runner()
    return runner


if __name__ == "__main__":
    r = get_runner()
    r.start()
    
    # Quick test
    player = r.get_concept_by_name("Player")
    game_state = r.get_concept_by_name("GameState")
    
    print(f"Player at: {player.get_state_snapshot()['x']}, {player.get_state_snapshot()['y']}")
    
    r.dispatch(player.id, "move", {"dx": 1, "dy": 0})
    print(f"Player moved to: {player.get_state_snapshot()['x']}, {player.get_state_snapshot()['y']}")
