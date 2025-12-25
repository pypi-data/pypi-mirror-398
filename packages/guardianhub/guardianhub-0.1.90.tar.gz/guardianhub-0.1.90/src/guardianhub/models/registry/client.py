# guardianhub_sdk/models/registry/client.py
from typing import Optional
from ...models.registry.loader import Loader


class ModelRegistryClient:
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.loader = Loader()

    async def fetch_model(self, name: str, version: Optional[str] = None):
        """Fetch remote model metadata and python artifact, return a loaded class or metadata."""
        return await self.loader.load(name)

# singleton-ish convenience
client = ModelRegistryClient(base_url="https://registry.internal.local")