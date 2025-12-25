# guardianhub_sdk/http/http_client.py
import httpx
from typing import Optional, Any, Dict


class BaseHTTPClient:


    def __init__(self, base_url: str, timeout: int = 30):

        self.base_url = base_url.rstrip('/')
        self._client = httpx.AsyncClient(timeout=timeout)


    async def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        resp = await self._client.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp


    async def get(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("POST", path, **kwargs)
