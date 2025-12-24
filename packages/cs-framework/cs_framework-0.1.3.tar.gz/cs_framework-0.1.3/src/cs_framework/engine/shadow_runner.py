from typing import Any, Dict, List
from .runner import Runner

class ShadowRunner:
    """
    Orchestrates a Main Runner and a Shadow Runner.
    Forwards all actions to both.
    Compares state after execution.
    """
    def __init__(self, main_runner: Runner, shadow_runner: Runner):
        self.main = main_runner
        self.shadow = shadow_runner
        self.diffs = []

    def dispatch(self, concept_name: str, action_name: str, payload: Any):
        """
        Dispatch action to both runners by Concept Name.
        """
        # Main
        main_c = self.main.get_concept_by_name(concept_name)
        if main_c:
            self.main.dispatch(main_c.id, action_name, payload)
        
        # Shadow
        shadow_c = self.shadow.get_concept_by_name(concept_name)
        if shadow_c:
            self.shadow.dispatch(shadow_c.id, action_name, payload)

    def process_events(self):
        self.main.process_events()
        self.shadow.process_events()
        self._compare_states()

    def _compare_states(self):
        main_state = self.main._get_global_state()
        shadow_state = self.shadow._get_global_state()
        
        # Compare by Concept Name (since IDs might differ)
        main_by_name = {self.main.concepts[cid].name: state for cid, state in main_state.items()}
        shadow_by_name = {self.shadow.concepts[cid].name: state for cid, state in shadow_state.items()}
        
        for name, m_state in main_by_name.items():
            if name in shadow_by_name:
                s_state = shadow_by_name[name]
                if m_state != s_state:
                    diff = {
                        "tick": self.main.tick_count,
                        "concept": name,
                        "main": m_state,
                        "shadow": s_state
                    }
                    self.diffs.append(diff)
                    print(f"Shadow Diff detected for {name}: {diff}")
