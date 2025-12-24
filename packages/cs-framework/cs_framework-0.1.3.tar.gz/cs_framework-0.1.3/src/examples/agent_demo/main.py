import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from cs_framework.engine.runner import Runner
from cs_framework.logging.logger import RDFLogger
from cs_framework.core.agent import AgentConcept
from cs_framework.core.llm import MockLLMProvider

def main():
    logger = RDFLogger("src/examples/agent_demo/execution.ttl")
    runner = Runner(logger=logger)

    # Configure Mock LLM
    mock_llm = MockLLMProvider(responses={
        "Hello": "Greetings, traveler!",
        "quest": "I have a task for you."
    })

    # Create Agent
    npc = AgentConcept("WiseOldMan", "You are a wise old sage.", llm_provider=mock_llm)
    runner.register(npc)

    runner.start()

    # Interact
    print("--- Interaction 1 ---")
    runner.dispatch(npc.id, "chat", {"message": "Hello there!"})
    runner.process_events()
    print(f"NPC State: {npc.get_state_snapshot()['last_response']}")

    print("--- Interaction 2 ---")
    runner.dispatch(npc.id, "chat", {"message": "Do you have a quest?"})
    runner.process_events()
    print(f"NPC State: {npc.get_state_snapshot()['last_response']}")

if __name__ == "__main__":
    main()
