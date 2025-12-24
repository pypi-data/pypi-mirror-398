import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Optional

class Event:
    def __init__(
        self,
        name: str,
        payload: Dict[str, Any],
        source_id: uuid.UUID,
        causal_link: Optional[uuid.UUID] = None,
        status: str = "Success"
    ):
        self.id = uuid.uuid4()
        self.name = name
        self.payload = payload
        self.source_id = source_id
        self.timestamp = datetime.now()
        self.causal_link = causal_link
        self.status = status

    def __repr__(self):
        return f"<Event {self.name} from {self.source_id} status={self.status}>"

class FailureEvent(Event):
    def __init__(
        self,
        original_event: Event,
        error_message: str,
        source_id: uuid.UUID
    ):
        super().__init__(
            name="Failure",
            payload={"error": error_message, "original_event_id": str(original_event.id)},
            source_id=source_id,
            causal_link=original_event.id,
            status="Error"
        )

class EventPattern:
    def __init__(self, source_concept: Any, event_name: str):
        # source_concept can be a Concept instance or a string ID/Name depending on usage.
        # For strict decoupling, maybe just ID or Name. But quickstart uses instance.
        self.source_concept = source_concept
        self.event_name = event_name

class ActionInvocation:
    def __init__(
        self,
        target_concept: Any,
        action_name: str,
        payload_mapper: Callable[[Event], Dict[str, Any]]
    ):
        self.target_concept = target_concept
        self.action_name = action_name
        self.payload_mapper = payload_mapper
