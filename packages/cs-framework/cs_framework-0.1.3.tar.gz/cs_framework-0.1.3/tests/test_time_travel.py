import unittest
import uuid
from cs_framework.core.concept import Concept
from cs_framework.engine.runner import Runner

class Counter(Concept):
    def __init__(self, name: str):
        super().__init__(name)
        self._state = {"count": 0}

    def increment(self, payload: dict):
        self._state["count"] += payload.get("amount", 1)

class TestTimeTravel(unittest.TestCase):
    def test_replay(self):
        runner = Runner()
        counter = Counter("counter")
        runner.register(counter)
        runner.start() # Tick 0 (Initial state: count=0)

        # Tick 1
        runner.dispatch(counter.id, "increment", {"amount": 1})
        self.assertEqual(counter._state["count"], 1)
        self.assertEqual(runner.tick_count, 1)

        # Tick 2
        runner.dispatch(counter.id, "increment", {"amount": 2})
        self.assertEqual(counter._state["count"], 3)
        self.assertEqual(runner.tick_count, 2)

        # Replay to Tick 1
        runner.replay(1)
        self.assertEqual(counter._state["count"], 1)
        self.assertEqual(runner.tick_count, 1)

        # Replay to Tick 0
        runner.replay(0)
        self.assertEqual(counter._state["count"], 0)
        self.assertEqual(runner.tick_count, 0)

if __name__ == '__main__':
    unittest.main()
