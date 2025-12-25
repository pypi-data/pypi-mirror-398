from typing import Optional, List
from .base import PromptProvider

class PromptRegistry:
    def __init__(self, providers: List[PromptProvider]):
        self.providers = providers

    async def get_prompt(self, name: str, version: Optional[str] = None):
        for provider in self.providers:
            try:
                return await provider.get_prompt(name, version)
            except:
                continue
        raise ValueError(f"Prompt '{name}' not found in any provider")
