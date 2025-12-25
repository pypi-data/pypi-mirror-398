# services/ocr_client.py

import httpx
from typing import Dict, Any, Optional
from guardianhub.config.settings import settings

from guardianhub import get_logger

logger = get_logger(__name__)

class OCRClient:
    """Client for interacting with the OCR service."""

    def __init__(self, base_url: Optional[str] = None):
        """Initialize the OCR client.
        
        Args:
            base_url: Base URL of the OCR service. If not provided, uses settings.endpoints.OCR_URL
        """
        self.base = base_url or getattr(settings.endpoints, 'OCR_URL', 'http://doc-ocr.guardianhub.com')
        logger.info("Initialized OCR client with base URL: %s", self.base)

    # Update the extract_text method in OCRClient
    async def extract_text(self, object_identifier: str) -> Dict[str, Any]:
        """Extract text from a document in MinIO."""
        endpoint = f"{self.base}/v1/ocr/process_from_minio"

        # Prepare the request payload
        payload = {"object_name": object_identifier}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                logger.debug(f"Sending OCR request to {endpoint} with payload: {payload}")
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()  # Raise HTTPStatusError for bad responses

                result = response.json()
                logger.debug(f"Received OCR response: {result}")

                # Handle the nested response structure
                if not isinstance(result, dict):
                    raise ValueError(f"Unexpected response type: {type(result).__name__}")

                # Check for success status and extract data
                if result.get('status') != 'success' or 'data' not in result:
                    raise ValueError(f"Unexpected response format: {result}")

                data = result.get('data', {})

                # Check for extracted text in the data section
                if 'extracted_text' in data:
                    return {
                        'extracted_text': data['extracted_text'],
                        'status': 'success',
                        'raw_response': result
                    }
                elif 'text' in data:
                    return {
                        'extracted_text': data['text'],
                        'status': 'success',
                        'raw_response': result
                    }
                else:
                    raise ValueError("Response missing 'text' or 'extracted_text' in data")

        except httpx.HTTPStatusError as e:
            error_msg = f"OCR service returned {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            e.add_note(f"Response content: {e.response.text}")
            raise
        except httpx.RequestError as e:
            error_msg = f"Request to OCR service failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except ValueError as e:
            logger.error("Failed to parse OCR response: %s. Response: %s", str(e),
                         response.text if 'response' in locals() else 'No response')
            raise ValueError(f"Invalid response from OCR service: {str(e)}") from e
        except Exception as e:
            logger.error("Unexpected error in OCR client: %s", str(e), exc_info=True)
            raise RuntimeError(f"Failed to process OCR request: {str(e)}") from e
