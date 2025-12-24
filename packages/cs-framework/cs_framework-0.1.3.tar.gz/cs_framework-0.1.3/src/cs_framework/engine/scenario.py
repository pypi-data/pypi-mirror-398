import uuid
import time
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel
from .runner import Runner
from ..core.event import Event

class ScenarioStep(BaseModel):
    type: str  # "dispatch", "wait", "assert_state"
    target: Optional[str] = None # Concept name
    action: Optional[str] = None
    payload: Optional[Dict[str, Any]] = {}
    ticks: Optional[int] = 1
    expected_state: Optional[Dict[str, Any]] = None

class ScenarioPlayer:
    def __init__(self, runner: Runner):
        self.runner = runner

    def play(self, scenario: List[Dict[str, Any]]):
        for step_data in scenario:
            step = ScenarioStep(**step_data)
            self._execute_step(step)

    def _execute_step(self, step: ScenarioStep):
        if step.type == "dispatch":
            concept = self.runner.get_concept_by_name(step.target)
            if concept:
                print(f"Scenario: Dispatching {step.action} to {step.target}")
                self.runner.dispatch(concept.id, step.action, step.payload)
            else:
                print(f"Scenario Error: Concept {step.target} not found")
        
        elif step.type == "wait":
            print(f"Scenario: Waiting {step.ticks} ticks")
            # In a real-time system, this might sleep. 
            # In our tick-based runner, we might just process empty events or do nothing if it's purely event-driven.
            # But since runner.process_events() is recursive, "waiting" might mean just advancing time if we had a clock.
            # For now, we'll just print.
            pass

        elif step.type == "assert_state":
            concept = self.runner.get_concept_by_name(step.target)
            if concept:
                current_state = concept.get_state_snapshot()
                for k, v in step.expected_state.items():
                    if current_state.get(k) != v:
                        raise AssertionError(f"State mismatch for {step.target}. Expected {k}={v}, got {current_state.get(k)}")
                print(f"Scenario: Assertion passed for {step.target}")
            else:
                print(f"Scenario Error: Concept {step.target} not found")
