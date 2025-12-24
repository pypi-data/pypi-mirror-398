import uuid
from typing import Dict, List, Any, Optional
from ..core.concept import Concept
from ..core.synchronization import Synchronization
from ..core.event import Event, FailureEvent
from ..core.invariant import Invariant
from ..logging.logger import RDFLogger

class Runner:
    def __init__(self, max_depth: int = 10, logger: Optional[RDFLogger] = None):
        self.concepts: Dict[uuid.UUID, Concept] = {}
        self.concepts_by_name: Dict[str, Concept] = {}
        self.synchronizations: List[Synchronization] = []
        self.invariants: List[Invariant] = []
        self.max_depth = max_depth
        self._event_queue: List[Event] = []
        self.logger = logger
        
        # Time-Travel
        self.history: List[Dict[uuid.UUID, Dict[str, Any]]] = []
        self.tick_count: int = 0

    def register(self, entity: Any):
        if isinstance(entity, Concept):
            self.concepts[entity.id] = entity
            self.concepts_by_name[entity.name] = entity
            if self.logger:
                self.logger.log_concept(entity.id, entity.name, entity.get_state_snapshot())
        elif isinstance(entity, Synchronization):
            self.synchronizations.append(entity)
            if self.logger:
                self.logger.log_synchronization(entity.id, entity.name)
        elif isinstance(entity, Invariant):
            self.invariants.append(entity)
        else:
            raise ValueError("Entity must be a Concept, Synchronization, or Invariant")

    def clear_synchronizations(self):
        """
        Remove all registered synchronizations.
        Used for hot-swapping logic.
        """
        self.synchronizations = []

    def get_concept_by_name(self, name: str) -> Optional[Concept]:
        return self.concepts_by_name.get(name)

    def start(self):
        # In a real app, this might start a thread or just be ready.
        # For this simple version, it just initializes.
        self._save_snapshot()

    def _save_snapshot(self):
        snapshot = {cid: c.get_state_snapshot() for cid, c in self.concepts.items()}
        self.history.append(snapshot)

    def _get_global_state(self) -> Dict[uuid.UUID, Dict[str, Any]]:
        return {cid: c.get_state_snapshot() for cid, c in self.concepts.items()}

    def process_events(self, depth: int = 0):
        if depth == 0:
             # Collect any pending events from all concepts (e.g. from async callbacks or external inputs)
             for concept in self.concepts.values():
                 self._event_queue.extend(concept.collect_events())

        if depth > self.max_depth:
            print("Max recursion depth reached. Stopping propagation.")
            return

        # Process all currently queued events
        current_batch = self._event_queue[:]
        self._event_queue = []

        for event in current_batch:
            self._handle_event(event, depth)
        
        if self.logger and depth == 0:
            self.logger.save()

        if depth == 0:
            self.tick_count += 1
            self._save_snapshot()
            self._check_invariants()

    def _check_invariants(self):
        global_state = self._get_global_state()
        for invariant in self.invariants:
            if not invariant.check(global_state):
                msg = f"Invariant Violation: {invariant.name}"
                if invariant.description:
                    msg += f" ({invariant.description})"
                print(f"!!! {msg} !!!")
                raise RuntimeError(msg)

    def _handle_event(self, event: Event, depth: int):
        if self.logger:
            self.logger.log_event(event.id, event.name, event.source_id, event.causal_link, event.status, payload=event.payload)

        # Find matching synchronizations
        global_state = self._get_global_state()
        
        for sync in self.synchronizations:
            if sync.evaluate(event, global_state):
                # Execute sync
                invocations = sync.execute(event)
                for invocation in invocations:
                    target_concept = invocation.target_concept
                    # Resolve target concept if it's an ID or Name (not implemented fully yet, assuming object)
                    target_id = target_concept.id if hasattr(target_concept, 'id') else target_concept
                    
                    if target_id in self.concepts:
                        concept = self.concepts[target_id]
                        try:
                            payload = invocation.payload_mapper(event)
                            
                            # Log Action Start
                            action_id = uuid.uuid4() # Generate ID for the action execution
                            if self.logger:
                                self.logger.log_action(action_id, invocation.action_name, concept.id, triggered_by=event.id) # Triggered by Event -> Sync -> Action

                            concept.dispatch(invocation.action_name, payload)
                            
                            # Collect new events from the concept
                            new_events = concept.collect_events()
                            # Set causal link to the ACTION that caused it
                            for ne in new_events:
                                ne.causal_link = action_id 
                            
                            self._event_queue.extend(new_events)
                        except Exception as e:
                            # Handle failure
                            failure_event = FailureEvent(event, str(e), concept.id)
                            self._event_queue.append(failure_event)
                    else:
                        print(f"Target concept {target_id} not found.")
        
        # Recursive call if there are new events
        if self._event_queue:
            self.process_events(depth + 1)

    def dispatch(self, concept_id: uuid.UUID, action_name: str, payload: Any):
        """
        External entry point to trigger an action.
        """
        if concept_id in self.concepts:
            concept = self.concepts[concept_id]
            try:
                # Log Initial Action
                action_id = uuid.uuid4()
                if self.logger:
                    self.logger.log_action(action_id, action_name, concept.id, triggered_by=None)

                concept.dispatch(action_name, payload)
                new_events = concept.collect_events()
                # Set causal link for initial action
                for ne in new_events:
                    ne.causal_link = action_id

                self._event_queue.extend(new_events)
                self.process_events()
            except Exception as e:
                print(f"Error dispatching initial action: {e}")
                raise e
        else:
            print(f"Concept {concept_id} not found.")

    def replay(self, tick_index: int):
        """
        Revert the system state to a specific tick.
        """
        if 0 <= tick_index < len(self.history):
            snapshot = self.history[tick_index]
            for cid, state in snapshot.items():
                if cid in self.concepts:
                    self.concepts[cid].restore_state(state)
            
            self.tick_count = tick_index
            self.history = self.history[:tick_index + 1]
            self._event_queue = []
            print(f"Replayed to tick {tick_index}")
        else:
            print(f"Invalid tick index {tick_index}. Max {len(self.history)-1}")

    # ===== External Command Interface =====

    def poll_and_execute_commands(self) -> int:
        """
        Poll for pending commands from the RDF graph and execute them.
        Returns the number of commands executed.
        
        This enables LLM agents to control the Runner via SPARQL.
        """
        if not self.logger:
            return 0
        
        commands = self.logger.get_pending_commands()
        executed = 0
        
        for cmd in commands:
            try:
                target_name = cmd["target"]
                action_name = cmd["action"]
                payload = cmd["payload"]
                
                concept = self.get_concept_by_name(target_name)
                if concept:
                    self.dispatch(concept.id, action_name, payload)
                    self.logger.mark_command_done(cmd["uri"])
                    executed += 1
                    print(f"Executed command: {target_name}.{action_name}")
                else:
                    self.logger.mark_command_done(cmd["uri"], f"Concept '{target_name}' not found")
                    print(f"Command failed: Concept '{target_name}' not found")
            except Exception as e:
                self.logger.mark_command_done(cmd["uri"], str(e))
                print(f"Command error: {e}")
        
        return executed

    def publish_all_states(self):
        """
        Publish current state of all concepts to the command graph.
        Allows external agents (LLMs) to query current game state.
        """
        if not self.logger:
            return
        
        for concept in self.concepts.values():
            self.logger.publish_state(concept.name, concept.get_state_snapshot())
        
        self.logger.save_command_graph()

    def run_with_external_control(self, tick_callback=None, max_ticks: int = 1000, poll_interval: float = 0.1):
        """
        Run the game loop with external command polling.
        
        This is the main loop for LLM-controlled execution:
        1. Publish current state to RDF
        2. Poll for commands from RDF
        3. Execute commands
        4. Repeat
        
        Args:
            tick_callback: Optional function to call each tick (for game logic like AI)
            max_ticks: Maximum number of ticks to run
            poll_interval: Seconds to wait between polls
        """
        import time
        
        for tick in range(max_ticks):
            # Publish state for external agents to read
            self.publish_all_states()
            
            # Poll and execute external commands
            executed = self.poll_and_execute_commands()
            
            # Optional game tick logic
            if tick_callback:
                tick_callback(self, tick)
            
            # If no commands, wait before next poll
            if executed == 0:
                time.sleep(poll_interval)
            
            # Check for termination conditions (could be enhanced)
            if hasattr(self, '_should_stop') and self._should_stop:
                break
        
        print(f"External control loop ended after {tick + 1} ticks")

    def stop_external_control(self):
        """Signal the external control loop to stop."""
        self._should_stop = True

