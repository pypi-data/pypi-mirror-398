# services/registry_client.py

import httpx
from guardianhub.config.settings import settings

class RegistryClient:

    def __init__(self):
        self.base = settings.endpoints.get("DOC_REGISTRY_URL")

    async def save_document(self, doc):
        async with httpx.AsyncClient() as client:
            await client.post(f"{self.base}/v1/documents", json=doc)

    async def get_document(self, doc_id):
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base}/v1/documents/{doc_id}")
        return r.json()
