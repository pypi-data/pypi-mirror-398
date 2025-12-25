from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

class PromptProvider(ABC):
    @abstractmethod
    async def get_prompt(self, name: str, version: Optional[str] = None) -> Dict[str, Any]:
        pass
