import unittest
import os
from cs_framework.core.concept import Concept
from cs_framework.engine.runner import Runner
from cs_framework.core.yaml_loader import YamlLoader

class MockConcept(Concept):
    def action1(self, payload):
        self.emit("event1", payload)

class TestYamlLoader(unittest.TestCase):
    def setUp(self):
        self.runner = Runner()
        self.c1 = MockConcept("C1")
        self.c2 = MockConcept("C2")
        self.runner.register(self.c1)
        self.runner.register(self.c2)
        
        self.yaml_file = "test_sync.yaml"
        with open(self.yaml_file, "w") as f:
            f.write("""
synchronizations:
  - name: "TestSync"
    when:
      source: "C1"
      event: "event1"
    then:
      - target: "C2"
        action: "action1"
        payload:
          val: "event.val"
          const: 123
""")

    def tearDown(self):
        if os.path.exists(self.yaml_file):
            os.remove(self.yaml_file)

    def test_load_sync(self):
        loader = YamlLoader(self.runner)
        loader.load(self.yaml_file)
        
        self.assertEqual(len(self.runner.synchronizations), 1)
        sync = self.runner.synchronizations[0]
        self.assertEqual(sync.name, "TestSync")
        self.assertEqual(sync.when.source_concept, self.c1)
        self.assertEqual(sync.when.event_name, "event1")
        
        # Test mapper
        class MockEvent:
            def __init__(self, payload):
                self.payload = payload
        
        event = MockEvent({"val": "hello"})
        mapped = sync.then[0].payload_mapper(event)
        self.assertEqual(mapped["val"], "hello")
        self.assertEqual(mapped["const"], 123)

if __name__ == '__main__':
    unittest.main()
