from typing import Any, Dict
from .concept import Concept
from .transport import Transport

class EventBridge(Concept):
    """
    Concept that bridges local events to/from a Transport layer.
    """
    def __init__(self, name: str, transport: Transport, channel: str = "global"):
        super().__init__(name)
        self.transport = transport
        self.channel = channel
        
        # Subscribe to transport
        self.transport.subscribe(self.channel, self._on_remote_message)

    def _on_remote_message(self, message: dict):
        # This is called from transport thread/callback.
        # We need to emit an event.
        # Since emit just appends to a list, it's thread-safe enough for this simple example.
        # But strictly, we might need a lock if Runner is multi-threaded.
        # For now, assume single threaded or simple callback.
        
        # Avoid loops: check if source was us (if transport echoes)
        if message.get("source_bridge") == self.id:
            return

        self.emit("remote_received", message)

    def send_remote(self, payload: dict):
        """
        Action: send_remote
        Payload: { "event_name": "moved", "payload": {...} }
        """
        message = {
            "source_bridge": str(self.id),
            "original_event": payload.get("event_name"),
            "payload": payload.get("payload")
        }
        self.transport.publish(self.channel, message)
