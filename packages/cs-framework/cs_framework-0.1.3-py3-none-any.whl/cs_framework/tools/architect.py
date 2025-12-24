import os
from typing import List

def generate_concept(name: str, actions: List[str] = None, events: List[str] = None, output_dir: str = "."):
    if actions is None: actions = []
    if events is None: events = []
    
    class_name = name
    # Convert CamelCase to snake_case for filename if needed, but simple lower() is often enough for simple names
    file_name = f"{name.lower()}.py"
    file_path = os.path.join(output_dir, file_name)

    actions_code = ""
    for action in actions:
        actions_code += f"""
    def {action}(self, payload: dict):
        \"\"\"
        Action: {action}
        \"\"\"
        # TODO: Implement logic
        # self.emit("SomeEvent", {{}})
        pass
"""

    events_doc = ", ".join(events) if events else "None"
    
    event_models_code = ""
    event_registry_entries = []
    
    for event in events:
        # Simple heuristic for class name: moved -> MovedEvent
        event_class_name = f"{event.capitalize()}Event"
        event_models_code += f"""
class {event_class_name}(BaseModel):
    # TODO: Define fields for {event}
    pass
"""
        event_registry_entries.append(f'        "{event}": {event_class_name}')
    
    event_registry_code = ""
    if event_registry_entries:
        event_registry_code = "    __events__ = {\n" + ",\n".join(event_registry_entries) + "\n    }\n"

    content = f"""from cs_framework.core.concept import Concept
from pydantic import BaseModel
from typing import Any, Dict

{event_models_code}
class {class_name}(Concept):
    \"\"\"
    Concept: {class_name}
    Emits Events: {events_doc}
    \"\"\"
{event_registry_code}
    def __init__(self, name: str = "{class_name}"):
        super().__init__(name)
{actions_code}
"""
    
    os.makedirs(output_dir, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Generated Concept '{class_name}' at {file_path}")
