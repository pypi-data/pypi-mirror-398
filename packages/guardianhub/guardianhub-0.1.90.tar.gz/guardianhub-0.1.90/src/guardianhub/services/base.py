# guardianhub_sdk/services/base.py
from typing import Optional
from guardianhub import get_logger

class BaseServiceClient:
    def __init__(self, base_url: str, token_provider=None, logger_name: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.token_provider = token_provider
        self.logger = get_logger(logger_name or __name__)

    async def _auth_headers(self) -> dict:
        if not self.token_provider:
            return {}
        token = await self.token_provider.get_token()
        return {"Authorization": f"Bearer {token}"}