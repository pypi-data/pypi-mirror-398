import uuid
import copy
import inspect
from typing import Any, Dict, List, Optional, Union, Type
from pydantic import BaseModel
from .event import Event

class Concept:
    __events__: Dict[str, Type[BaseModel]] = {}

    def __init__(self, name: str):
        self.id = uuid.uuid4()
        self.name = name
        self._state: Dict[str, Any] = {}
        self._pending_events: List[Event] = []

    def dispatch(self, action_name: str, payload: Any) -> None:
        """
        Execute an action.
        Supports Pydantic model validation if the method is type-hinted.
        """
        if hasattr(self, action_name):
            method = getattr(self, action_name)
            if callable(method):
                # Runtime type checking using Pydantic
                sig = inspect.signature(method)
                params = list(sig.parameters.values())
                if len(params) > 0:
                    payload_param = params[0]
                    # Check if the parameter is a Pydantic model
                    if isinstance(payload_param.annotation, type) and issubclass(payload_param.annotation, BaseModel):
                        # If payload is dict, convert to model
                        if isinstance(payload, dict):
                            try:
                                payload = payload_param.annotation(**payload)
                            except Exception as e:
                                raise TypeError(f"Invalid payload for action '{action_name}': {e}")
                
                method(payload)
            else:
                raise AttributeError(f"Action '{action_name}' not found or not callable on {self.name}")
        else:
             raise AttributeError(f"Action '{action_name}' not found on {self.name}")

    def apply(self, event: Event) -> None:
        """
        Update state based on event.
        """
        pass

    def emit(self, event_name: str, payload: Union[Dict[str, Any], BaseModel], causal_link: Optional[uuid.UUID] = None) -> None:
        """
        Create and queue an event.
        Supports Pydantic models as payload.
        """
        # Validate against registered event schema if available
        if event_name in self.__events__:
            model_class = self.__events__[event_name]
            if isinstance(payload, dict):
                try:
                    payload = model_class(**payload)
                except Exception as e:
                    raise TypeError(f"Invalid payload for event '{event_name}': {e}")
            elif isinstance(payload, BaseModel):
                if not isinstance(payload, model_class):
                    raise TypeError(f"Payload for event '{event_name}' must be instance of {model_class.__name__}, got {type(payload).__name__}")

        if isinstance(payload, BaseModel):
            payload_dict = payload.model_dump()
        else:
            payload_dict = payload

        event = Event(
            name=event_name,
            payload=payload_dict,
            source_id=self.id,
            causal_link=causal_link
        )
        self._pending_events.append(event)

    def get_state_snapshot(self) -> Dict[str, Any]:
        """
        Return a read-only copy of the current state.
        """
        return copy.deepcopy(self._state)

    def restore_state(self, state: Dict[str, Any]) -> None:
        """
        Restore state from a snapshot.
        """
        self._state = copy.deepcopy(state)

    def collect_events(self) -> List[Event]:
        """
        Return and clear pending events.
        """
        events = self._pending_events
        self._pending_events = []
        return events
