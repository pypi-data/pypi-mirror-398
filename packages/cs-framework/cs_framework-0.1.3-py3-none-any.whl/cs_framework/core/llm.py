from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        pass

class MockLLMProvider(LLMProvider):
    def __init__(self, responses: Dict[str, str] = None):
        self.responses = responses or {}
        self.default_response = "I am a mock LLM."

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        # Simple keyword matching for mock behavior
        for key, response in self.responses.items():
            if key in prompt:
                return response
        return self.default_response
