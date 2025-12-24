from abc import ABC, abstractmethod
from typing import Callable, Any

class Transport(ABC):
    @abstractmethod
    def publish(self, channel: str, message: dict):
        pass

    @abstractmethod
    def subscribe(self, channel: str, callback: Callable[[dict], None]):
        pass

class LocalTransport(Transport):
    """
    In-memory transport for testing.
    """
    def __init__(self):
        self.subscribers = {}

    def publish(self, channel: str, message: dict):
        if channel in self.subscribers:
            for callback in self.subscribers[channel]:
                callback(message)

    def subscribe(self, channel: str, callback: Callable[[dict], None]):
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        self.subscribers[channel].append(callback)
