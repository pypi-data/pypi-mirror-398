import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from cs_framework.engine.runner import Runner
from cs_framework.engine.shadow_runner import ShadowRunner
from cs_framework.core.concept import Concept

class CounterV1(Concept):
    def __init__(self, name="Counter"):
        super().__init__(name)
        self._state["count"] = 0
        
    def increment(self, payload):
        self._state["count"] += 1

class CounterV2(Concept):
    def __init__(self, name="Counter"):
        super().__init__(name)
        self._state["count"] = 0
        
    def increment(self, payload):
        # Buggy implementation: increments by 2
        self._state["count"] += 2

def main():
    # Main Runner
    runner_main = Runner()
    c1 = CounterV1("Counter")
    runner_main.register(c1)

    # Shadow Runner
    runner_shadow = Runner()
    c2 = CounterV2("Counter")
    runner_shadow.register(c2)

    # Shadow Orchestrator
    shadow_runner = ShadowRunner(runner_main, runner_shadow)

    print("Dispatching increment...")
    shadow_runner.dispatch("Counter", "increment", {})
    shadow_runner.process_events()

    if shadow_runner.diffs:
        print("Test Passed: Diff detected.")
    else:
        print("Test Failed: No diff detected.")

if __name__ == "__main__":
    main()
