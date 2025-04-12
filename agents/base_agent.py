from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    @abstractmethod
    def process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def validate_response(self, response: Dict[str, Any]) -> bool:
        pass 