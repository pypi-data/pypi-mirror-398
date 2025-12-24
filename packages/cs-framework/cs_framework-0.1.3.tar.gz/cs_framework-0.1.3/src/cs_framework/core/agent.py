from typing import Any, Dict, Optional
from pydantic import BaseModel
from .concept import Concept
from .llm import LLMProvider, MockLLMProvider

class AgentConcept(Concept):
    """
    A Concept that uses an LLM to generate state updates or responses.
    """
    def __init__(self, name: str, system_prompt: str, llm_provider: Optional[LLMProvider] = None):
        super().__init__(name)
        self.system_prompt = system_prompt
        self.llm = llm_provider or MockLLMProvider()
        self._state["history"] = []

    def chat(self, payload: Dict[str, Any]):
        """
        Action: chat
        Payload: { "message": "Hello" }
        """
        user_message = payload.get("message", "")
        
        # Update history
        self._state["history"].append({"role": "user", "content": user_message})
        
        # Construct prompt from history (simplified)
        conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self._state["history"]])
        
        # Call LLM
        response = self.llm.generate(conversation, system_prompt=self.system_prompt)
        
        # Update state with response
        self._state["history"].append({"role": "assistant", "content": response})
        self._state["last_response"] = response
        
        # Emit event
        self.emit("responded", {"message": response, "to": user_message})

    def set_provider(self, provider: LLMProvider):
        self.llm = provider
