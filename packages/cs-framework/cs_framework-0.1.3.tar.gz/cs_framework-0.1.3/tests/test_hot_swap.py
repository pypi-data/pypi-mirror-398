import unittest
import os
from cs_framework.core.concept import Concept
from cs_framework.engine.runner import Runner
from cs_framework.core.yaml_loader import YamlLoader

class SourceConcept(Concept):
    def trigger(self, payload: dict):
        self.emit("trigger", payload)

class TargetConcept(Concept):
    def __init__(self, name: str):
        super().__init__(name)
        self._state = {"last_action": None}

    def action_a(self, payload: dict):
        self._state["last_action"] = "A"

    def action_b(self, payload: dict):
        self._state["last_action"] = "B"

class TestHotSwap(unittest.TestCase):
    def test_hot_swap(self):
        runner = Runner()
        source = SourceConcept("SourceConcept")
        target = TargetConcept("TargetConcept")
        runner.register(source)
        runner.register(target)
        
        loader = YamlLoader(runner)

        # 1. Load V1
        loader.load("tests/sync_v1.yaml")
        runner.start()

        # Trigger -> Expect Action A
        runner.dispatch(source.id, "trigger", {})
        self.assertEqual(target._state["last_action"], "A")

        # 2. Hot Swap
        runner.clear_synchronizations()
        loader.load("tests/sync_v2.yaml")

        # Trigger -> Expect Action B
        runner.dispatch(source.id, "trigger", {})
        self.assertEqual(target._state["last_action"], "B")

if __name__ == '__main__':
    unittest.main()
