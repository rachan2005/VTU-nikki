from abc import ABC, abstractmethod
from typing import Dict, Any

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, raw_text: str, system_prompt: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        pass
