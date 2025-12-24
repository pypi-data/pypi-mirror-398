import unittest
from pydantic import BaseModel
from cs_framework.core.concept import Concept

class MovePayload(BaseModel):
    x: int
    y: int

class Player(Concept):
    def move(self, payload: MovePayload):
        self.emit("moved", payload)

class TestPydanticSupport(unittest.TestCase):
    def test_dispatch_with_dict(self):
        player = Player("p1")
        # Dispatch with dict, should be converted to MovePayload
        player.dispatch("move", {"x": 10, "y": 20})
        
        events = player.collect_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload, {"x": 10, "y": 20})

    def test_dispatch_with_model(self):
        player = Player("p1")
        payload = MovePayload(x=30, y=40)
        player.dispatch("move", payload)
        
        events = player.collect_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload, {"x": 30, "y": 40})

    def test_validation_error(self):
        player = Player("p1")
        with self.assertRaises(TypeError):
            player.dispatch("move", {"x": "invalid", "y": 20})

if __name__ == '__main__':
    unittest.main()
