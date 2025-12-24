import yaml
from typing import Dict, Any, Callable
from ..engine.runner import Runner
from .synchronization import Synchronization
from .event import EventPattern, ActionInvocation

class YamlLoader:
    def __init__(self, runner: Runner):
        self.runner = runner

    def load(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data or 'synchronizations' not in data:
            return

        for sync_def in data.get('synchronizations', []):
            self._create_sync(sync_def)

    def _create_sync(self, data: Dict[str, Any]):
        name = data.get('name', 'UnnamedSync')
        
        # When
        when_data = data.get('when')
        if not when_data:
            raise ValueError(f"Synchronization '{name}' missing 'when' clause")

        source_name = when_data.get('source')
        event_name = when_data.get('event')
        
        source = self.runner.get_concept_by_name(source_name)
        if not source:
            raise ValueError(f"Concept '{source_name}' not found for sync '{name}'")
        
        event_pattern = EventPattern(source, event_name)
        
        # Then
        then_data = data.get('then', [])
        then_actions = []
        
        for action_data in then_data:
            target_name = action_data.get('target')
            action_name = action_data.get('action')
            payload_mapping = action_data.get('payload', {})
            
            target = self.runner.get_concept_by_name(target_name)
            if not target:
                raise ValueError(f"Concept '{target_name}' not found for sync '{name}'")
            
            mapper = self._create_payload_mapper(payload_mapping)
            then_actions.append(ActionInvocation(target, action_name, mapper))

        sync = Synchronization(name, event_pattern, then_actions)
        self.runner.register(sync)

    def _create_payload_mapper(self, mapping: Dict[str, str]) -> Callable[[Any], Dict[str, Any]]:
        """
        Creates a lambda that maps event payload to action payload.
        Supports simple key mapping: "target_key": "event.source_key"
        """
        def mapper(event):
            result = {}
            for target_key, source_expr in mapping.items():
                # Simple expression parsing: "event.key"
                if isinstance(source_expr, str) and source_expr.startswith("event."):
                    key = source_expr.split(".", 1)[1]
                    # Access payload
                    if isinstance(event.payload, dict):
                        result[target_key] = event.payload.get(key)
                    elif hasattr(event.payload, key):
                        result[target_key] = getattr(event.payload, key)
                    else:
                        result[target_key] = None # Or raise error?
                else:
                    # Constant value
                    result[target_key] = source_expr
            return result
        return mapper
