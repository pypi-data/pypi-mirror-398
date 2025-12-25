class Langfuse:
    def __init__(self, secret_key: str, host: str):
        self.secret_key = secret_key
        self.host = host
from typing import Optional, Dict, Any
from ..base import PromptProvider
class LangfusePromptProvider(PromptProvider):
    def __init__(self, api_key: str, host: str):
        self.client = Langfuse(secret_key=api_key, host=host)

    async def get_prompt(self, name: str, version: Optional[str] = None) -> Dict[str, Any]:
        prompt = self.client.get_prompt(name=name, version=version)
        return prompt.to_dict()
