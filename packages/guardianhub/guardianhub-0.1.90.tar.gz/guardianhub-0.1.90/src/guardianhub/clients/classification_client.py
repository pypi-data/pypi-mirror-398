"""Minio client with graceful error handling and connection management."""
import logging
from datetime import timedelta
from typing import Optional, Union, Dict, Any

import httpx

from guardianhub.config.settings import settings
from guardianhub.logging import get_logger
logger = get_logger(__name__)
class ClassificationClient:
    """Minio client wrapper with graceful error handling."""

    def __init__(self, base_url:str, poll_interval: int = 5, poll_timeout: int = 300):
        self.initialized = False
        self.client = None

        try:
            self.api_url = base_url.rstrip('/')
            self.headers = {
                "Accept": "application/json",
            }
            self.poll_interval = poll_interval
            self.poll_timeout = poll_timeout

            # Initialize the persistent httpx client here.
            # DO NOT use it in an 'async with' block in methods, or it will be closed.
            self.client = httpx.AsyncClient(headers=self.headers, base_url=self.api_url,
                                            timeout=self.poll_timeout + 60)
            self.initialized = True
            logger.info(f"✅ Classification client connected to {settings.endpoints.CLASSIFICATION_ENDPOINT}")

        except Exception as e:
            logger.warning(
                f"⚠️ Failed to initialize Classification client: {str(e)}. "
                "Classification operations will be disabled."
            )
            self.initialized = False

    async def classify(self, text: str,metadata:Dict[str, Any]) -> Dict[str, Any]:
        """Generate a presigned URL for uploading an object."""
        if not self.initialized:
            logger.warning("Classification client not initialized, cannot generate presigned URL")
            return {}

        try:
            response = await self.client.post("/v1/document/classify", json={"text": text, "metadata":metadata})
            return response.json()

        except Exception as e:
            logger.error(f"Failed to classify document: {str(e)}")
            return {}
