import uuid
from typing import Callable, List, Dict, Any, Optional
from .event import Event, EventPattern, ActionInvocation
from .concept import Concept

class Synchronization:
    def __init__(
        self,
        name: str,
        when: EventPattern,
        then: List[ActionInvocation],
        where: Optional[Callable[[Dict[uuid.UUID, Dict[str, Any]]], bool]] = None
    ):
        self.id = uuid.uuid4()
        self.name = name
        self.when = when
        self.then = then
        self.where = where

    def evaluate(self, event: Event, global_state: Dict[uuid.UUID, Dict[str, Any]]) -> bool:
        """
        Check if event matches 'when' and 'where' condition passes.
        """
        # Check 'when'
        source_match = False
        if isinstance(self.when.source_concept, Concept):
            source_match = (event.source_id == self.when.source_concept.id)
        elif isinstance(self.when.source_concept, str):
             # Assuming source_concept is name or ID string. 
             # Ideally we match ID, but for now let's assume strict ID match if it's a string representation of UUID
             # or maybe we need a lookup.
             # For simplicity and following quickstart, we expect Concept object in definition but here we compare IDs.
             pass
        
        # If source_concept was passed as object, we can compare IDs.
        # If it was passed as ID, we compare IDs.
        target_source_id = None
        if hasattr(self.when.source_concept, 'id'):
            target_source_id = self.when.source_concept.id
        else:
            target_source_id = self.when.source_concept

        if str(event.source_id) != str(target_source_id):
            return False

        if event.name != self.when.event_name:
            return False

        # Check 'where'
        if self.where:
            if not self.where(global_state):
                return False

        return True

    def execute(self, event: Event) -> List[ActionInvocation]:
        """
        Returns the list of ActionInvocations to be dispatched.
        """
        return self.then
