import sys
import uuid
import json
from datetime import datetime
from typing import Any, Optional, List, Dict
from rdflib import Graph, Literal, RDF, URIRef, XSD
from loguru import logger
from .ontology import (
    CS, CONCEPT, ACTION, EVENT, SYNCHRONIZATION, COMMAND,
    HAS_NAME, HAS_STATE, BELONGS_TO, TRIGGERED_BY, CAUSED_BY, STATUS,
    HAS_ACTION, HAS_TARGET, HAS_PAYLOAD, COMMAND_STATUS, CREATED_AT, PROCESSED_AT, ERROR_MESSAGE
)

import time


class RDFLogger:
    def __init__(self, log_file: str = "execution.ttl", console_output: bool = True, save_interval: float = 0.0):
        self.graph = Graph()
        self.graph.bind("cs", CS)
        # Convert to absolute path for reliable file access
        self.log_file = os.path.abspath(log_file)
        self.console_output = console_output
        self.save_interval = save_interval
        self.last_save_time = 0.0
        
        # Command graph (separate for external interaction)
        self.command_file = self.log_file.replace(".ttl", "_commands.ttl")
        self.command_graph = Graph()
        self.command_graph.bind("cs", CS)
        
        # Configure loguru
        logger.remove() # Remove default handler
        if self.console_output:
            logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")
        
        # Also log to a text file for easier reading
        text_log = log_file.replace(".ttl", ".log")
        logger.add(text_log, rotation="1 MB")

    def _log_to_console(self, message: str):
        logger.info(message)

    def log_concept(self, concept_id: uuid.UUID, name: str, state: Any):
        concept_uri = CS[str(concept_id)]
        self.graph.add((concept_uri, RDF.type, CONCEPT))
        self.graph.add((concept_uri, HAS_NAME, Literal(name)))
        self.graph.add((concept_uri, HAS_STATE, Literal(json.dumps(str(state))))) # Simplified state serialization
        self._log_to_console(f"Registered Concept: {name} ({concept_id})")

    def log_synchronization(self, sync_id: uuid.UUID, name: str):
        sync_uri = CS[str(sync_id)]
        self.graph.add((sync_uri, RDF.type, SYNCHRONIZATION))
        self.graph.add((sync_uri, HAS_NAME, Literal(name)))
        self._log_to_console(f"Registered Sync: {name} ({sync_id})")

    def log_action(self, action_id: uuid.UUID, name: str, concept_id: uuid.UUID, triggered_by: Optional[uuid.UUID] = None):
        action_uri = CS[str(action_id)]
        self.graph.add((action_uri, RDF.type, ACTION))
        self.graph.add((action_uri, HAS_NAME, Literal(name)))
        self.graph.add((action_uri, BELONGS_TO, CS[str(concept_id)]))
        if triggered_by:
            self.graph.add((action_uri, TRIGGERED_BY, CS[str(triggered_by)]))
        self._log_to_console(f"Action: {name} on {concept_id}")

    def log_event(self, event_id: uuid.UUID, name: str, source_id: uuid.UUID, causal_link: Optional[uuid.UUID] = None, status: str = "Success", payload: Any = None):
        event_uri = CS[str(event_id)]
        self.graph.add((event_uri, RDF.type, EVENT))
        self.graph.add((event_uri, HAS_NAME, Literal(name)))
        self.graph.add((event_uri, BELONGS_TO, CS[str(source_id)]))
        self.graph.add((event_uri, STATUS, Literal(status)))
        if payload:
             self.graph.add((event_uri, HAS_STATE, Literal(json.dumps(str(payload)))))
        if causal_link:
            self.graph.add((event_uri, CAUSED_BY, CS[str(causal_link)]))
        self._log_to_console(f"Event: {name} from {source_id} (Status: {status})")

    # ===== Command Interface for LLM =====
    
    def publish_state(self, concept_name: str, state: Dict[str, Any]):
        """Publish current concept state to command graph for LLM to read."""
        state_uri = CS[f"state_{concept_name}"]
        
        # Remove old state
        self.command_graph.remove((state_uri, None, None))
        
        # Add new state
        self.command_graph.add((state_uri, RDF.type, CS.ConceptState))
        self.command_graph.add((state_uri, HAS_NAME, Literal(concept_name)))
        self.command_graph.add((state_uri, HAS_STATE, Literal(json.dumps(state))))
        self.command_graph.add((state_uri, CREATED_AT, Literal(datetime.now().isoformat())))

    def get_pending_commands(self) -> List[Dict[str, Any]]:
        """Query command graph for pending commands."""
        # Reload command graph from file (external process may have written)
        try:
            if os.path.exists(self.command_file):
                self.command_graph.parse(self.command_file, format="turtle")
        except Exception as e:
            self._log_to_console(f"Error loading command file: {e}")
        
        # SPARQL query for pending commands
        query = """
        PREFIX cs: <http://cs-framework.org/schema/>
        SELECT ?cmd ?action ?target ?payload WHERE {
            ?cmd a cs:Command ;
                 cs:commandStatus "pending" ;
                 cs:hasAction ?action ;
                 cs:hasTarget ?target .
            OPTIONAL { ?cmd cs:hasPayload ?payload }
        }
        """
        
        commands = []
        try:
            results = self.command_graph.query(query)
            for row in results:
                cmd = {
                    "uri": str(row.cmd),
                    "action": str(row.action),
                    "target": str(row.target),
                    "payload": json.loads(str(row.payload)) if row.payload else {}
                }
                commands.append(cmd)
        except Exception as e:
            self._log_to_console(f"Error querying commands: {e}")
        
        return commands

    def mark_command_done(self, cmd_uri: str, error: Optional[str] = None):
        """Mark a command as processed."""
        uri = URIRef(cmd_uri)
        
        # Remove pending status
        self.command_graph.remove((uri, COMMAND_STATUS, Literal("pending")))
        
        # Add done/error status
        if error:
            self.command_graph.add((uri, COMMAND_STATUS, Literal("error")))
            self.command_graph.add((uri, ERROR_MESSAGE, Literal(error)))
        else:
            self.command_graph.add((uri, COMMAND_STATUS, Literal("done")))
        
        self.command_graph.add((uri, PROCESSED_AT, Literal(datetime.now().isoformat())))
        self.save_command_graph()

    def add_command(self, action: str, target: str, payload: Dict[str, Any] = None) -> str:
        """Add a new command to the graph (for testing / programmatic use)."""
        cmd_id = f"cmd_{uuid.uuid4().hex[:8]}"
        cmd_uri = CS[cmd_id]
        
        self.command_graph.add((cmd_uri, RDF.type, COMMAND))
        self.command_graph.add((cmd_uri, HAS_ACTION, Literal(action)))
        self.command_graph.add((cmd_uri, HAS_TARGET, Literal(target)))
        self.command_graph.add((cmd_uri, HAS_PAYLOAD, Literal(json.dumps(payload or {}))))
        self.command_graph.add((cmd_uri, COMMAND_STATUS, Literal("pending")))
        self.command_graph.add((cmd_uri, CREATED_AT, Literal(datetime.now().isoformat())))
        
        self.save_command_graph()
        return str(cmd_uri)

    def save_command_graph(self):
        """Save command graph to file."""
        try:
            self.command_graph.serialize(destination=self.command_file, format="turtle")
        except Exception as e:
            self._log_to_console(f"Error saving command graph: {e}")

    def save(self):
        import os
        
        # Check throttle
        current_time = time.time()
        if current_time - self.last_save_time < self.save_interval:
            return

        # Write to a temp file first to avoid read/write race conditions
        temp_file = self.log_file + ".tmp"
        try:
            self.graph.serialize(destination=temp_file, format="turtle")
            # Atomic replace
            os.replace(temp_file, self.log_file)
            self._log_to_console(f"Log saved to {self.log_file}")
            self.last_save_time = current_time
        except Exception as e:
            self._log_to_console(f"Error saving log: {e}")
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass


# Import os at module level for use in methods
import os
