"""Client implementation for interacting with the Paperless-ngx REST API.

This client provides granular methods for document upload, processing status polling,
and text retrieval, supporting better error handling and custom OCR integration.
"""
import asyncio
import time  # <-- Added time import for standard time tracking
from typing import Dict, Any, Optional, List

import httpx
from guardianhub import get_logger
from guardianhub.config.settings import settings
logger = get_logger(__name__)

# Define a simple exception for task failures
class PaperlessTaskFailure(RuntimeError):
    """Custom exception for Paperless task failures."""
    pass

# Paperless field types: string, integer, float, boolean, date, document_link
SCHEMA_TYPE_MAP = {
    "string": "string",
    "number": "float", # Use float for Pydantic's 'number' type (covers decimals)
    "integer": "integer",
    "boolean": "boolean",
    "date": "date" # Assuming a custom type for dates, otherwise use 'string'
}
class PaperlessClient:
    """
    Asynchronous client for Paperless-ngx API interactions.

    This client assumes an API endpoint is available and requires an API token.
    It maintains a persistent httpx client session for reuse across activity calls.
    """
    def __init__(self,base_url:str, poll_interval: int = 5, poll_timeout: int = 300):
        """
        Initializes the Paperless client.
        """
        self.api_url = base_url.rstrip('/')
        self.api_token = settings.endpoints.get("PAPERLESS_ACCESS_KEY")
        self.headers = {
            "Authorization": f"Token {self.api_token}",
            "Accept": "application/json",
        }
        self.poll_interval = poll_interval
        self.poll_timeout = poll_timeout

        # Initialize the persistent httpx client here.
        # DO NOT use it in an 'async with' block in methods, or it will be closed.
        self.client = httpx.AsyncClient(headers=self.headers, base_url=self.api_url, timeout=self.poll_timeout + 60)
        # self.client = httpx.AsyncClient(
        #     auth=("jayant_yantramops", "itapp123"),
        #     base_url=self.api_url,
        #     timeout=self.poll_timeout + 60,
        #     follow_redirects=False
        # )
        logger.info("PaperlessClient initialized for URL: %s", self.api_url)

    async def upload_document(self, file_path: str, file_name: str, skip_ocr: bool) -> Optional[str]:
        """
        Uploads a single document to Paperless-ngx.
        """
        upload_endpoint = "/api/documents/post_document/"
        logger.info("Attempting to upload file: %s", file_name)

        try:
            data = {
                'title': file_name,
                'full_text_search': 'auto'
                # 'full_text_search': 'skip' if skip_ocr else 'auto'
            }


            # Use the persistent client directly without 'async with'
            with open(file_path, 'rb') as f:
                files = {'document': (file_name, f)}

                response = await self.client.post(upload_endpoint, files=files, data=data)

            response.raise_for_status()

            # Reads the response as text and strips quotes/whitespace (Fix from previous step)
            initial_doc_id = response.text.strip().strip('"')
            document_id = str(initial_doc_id)

            if not document_id or document_id.lower() == 'none' or not document_id.strip():
                raise RuntimeError("Paperless API did not return a document ID after upload (response was empty or invalid).")

            logger.info("File uploaded. Document ID assigned: %s", document_id)
            return document_id

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            error_msg = f"Paperless HTTP error during upload (Status {status_code}): {e.response.text}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg)

        except Exception as e:
            logger.error("A critical error occurred during Paperless upload: %s", str(e), exc_info=True)
            raise

    async def wait_for_document_processing(self, task_id: str) -> Dict[str, Any]:
        """
        Polls the Paperless API for a document's processing status using the Task ID until it completes.

        Returns the final Document ID on success, or the ID of the existing document if a duplicate is found.
        """
        endpoint = f"/api/tasks/?task_id={task_id}"
        start_time = time.time()

        logger.info("Polling Paperless for task %s status...", task_id)

        while time.time() - start_time < self.poll_timeout:
            try:
                response = await self.client.get(endpoint)
                response.raise_for_status()
                data: List[Dict[str, Any]] = response.json()

                if not data:
                    # Case 1: Task not yet created or found in the system
                    logger.info("Task %s is not yet visible in the task list. Retrying in %d seconds.",
                                         task_id, self.poll_interval)
                    await asyncio.sleep(self.poll_interval)
                    continue

                # Case 2: Task found, check status
                task_info = data[0]
                status = task_info.get('status')
                result = task_info.get('result', 'No result message provided.')

                if status == 'SUCCESS':
                    document_id = str(task_info.get('related_document'))
                    if not document_id or document_id == 'None':
                        raise PaperlessTaskFailure(
                            f"Task succeeded but returned no 'related_document' ID. Result: {result}")

                    logger.info("Document ingestion successful. Final Document ID: %s. Result: %s",
                                         document_id, result)
                    return task_info

                elif status == 'FAILURE':
                    logger.error("Paperless-ngx processing failed for task %s: %s", task_id, result)

                    # --- CRITICAL CHANGE: Handle Duplicate Failure (SOFT FAILURE) ---
                    # If the failure is due to duplication, the task's 'related_document' field should hold the ID of the existing document.
                    if 'duplicate' in result.lower() and task_info.get('related_document'):
                        existing_doc_id = str(task_info['related_document'])
                        logger.warning(
                            "DUPLICATE DETECTED: Task failed, but document already exists as ID %s. The workflow will proceed using this existing ID.",
                            existing_doc_id)
                        # Return the existing document ID instead of raising an error
                        return task_info

                    # Hard Failure
                    raise PaperlessTaskFailure(f"Paperless-ngx task failed ({task_id}): {result}")

                else:
                    # STARTED, PENDING, UNKNOWN, etc.
                    logger.info("Task %s status: %s. Retrying in %d seconds.",
                                         task_id, status, self.poll_interval)

                await asyncio.sleep(self.poll_interval)

            except httpx.HTTPStatusError as e:
                logger.error("HTTP error while polling task %s: %s", task_id, e)
                raise
            # Catch PaperlessTaskFailure and re-raise immediately (not transient)
            except PaperlessTaskFailure:
                raise
            except Exception as e:
                # Catch unexpected JSON errors or network issues (which are transient)
                logger.warning("Transient error while polling task %s: %s. Retrying...", task_id, e)
                await asyncio.sleep(self.poll_interval)

        raise TimeoutError(f"Paperless-ngx processing timed out after {self.poll_timeout} seconds for task {task_id}")

    async def get_document(self, document_id: int) -> Dict[str, Any]:
        """
        Retrieves comprehensive document metadata and content from Paperless-ngx.

        It hits the document detail endpoint (/api/documents/{id}/) to get:
        - raw_text (from the 'content' field)
        - classification metadata (title, dates, tags, etc.)
        """
        # Use the endpoint that provides full JSON details
        endpoint = f"/api/documents/{document_id}/"

        try:
            # Use the persistent client directly (assuming self.client is available)
            response = await self.client.get(endpoint)

            # --- CRITICAL FIX: Manually check for 3xx status codes which indicate unauthenticated redirect ---
            if 300 <= response.status_code < 400:
                logger.error(
                    "Authentication required: Received redirect (Status %d) to login page for document %s. Check API token.",
                    response.status_code, document_id)
                # Raising a custom error here since a 302 on this endpoint means authorization failed.
                raise RuntimeError(
                    f"Authentication Failure: Paperless redirected to login page when trying to fetch document {document_id}. Status: {response.status_code}")

            response.raise_for_status()

            doc_data = response.json()

            # Extract classification-relevant fields
            raw_text = doc_data.get("content", "")

            # Build a metadata dictionary for the MetadataClassifier
            classification_metadata = {
                # Core Textual/Contextual Fields
                "title": doc_data.get("title", ""),
                "original_file_name": doc_data.get("original_file_name", ""),

                # Date Fields
                "created_date": doc_data.get("created", ""),
                "modified_date": doc_data.get("modified", ""),

                # Structural Fields (New)
                "mime_type": doc_data.get("mime_type", ""),  # e.g., 'application/pdf'
                "page_count": doc_data.get("page_count", 1),  # Page count is a strong signal for reports vs. receipts

                # Paperless Relations (using IDs)
                "tags": doc_data.get("tags", []),
                "document_type_id": doc_data.get("document_type", None),
                "correspondent_id": doc_data.get("correspondent", None),  # Strong signal for vendors/banks
                "archive_serial_number": doc_data.get("archive_serial_number", None)

                # Note: We skip 'custom_fields' for now until their schema is defined.
            }

            if not raw_text:
                logger.warning(
                    "Retrieved text is empty for document %s. This may indicate poor OCR quality or an empty file.",
                    document_id)

            # Return a dictionary containing all needed classification inputs
            return {
                "document_id": document_id,
                "raw_text": raw_text,
                "metadata": classification_metadata,
                "embedding_id": doc_data.get("embedding_id", None),
                # Note: The 'embedding_id' must be managed/added by the calling service (DCM)
                # if it's an internal ID, as Paperless does not know about it.
            }

        except httpx.HTTPStatusError as e:
            logger.error("HTTP error fetching document %s: %s", document_id, str(e))
            # Re-raise the exception after logging
            raise
        except Exception as e:
            logger.error("An unexpected error occurred fetching document %s: %s", document_id, str(e))
            # Re-raise the exception after logging
            raise
    async def get_document_text(self, document_id: int) -> str:
        """
        Retrieves the full OCR'd text content of a processed document.
        """
        # Note: Paperless documentation uses /api/documents/{id}/text/
        # endpoint = f"/api/documents/{document_id}/text/"
        # endpoint = f"/api/documents/{document_id}/download/?as_text=1"
        endpoint = f"/api/documents/{document_id}/"

        try:
            # Use the persistent client directly
            response = await self.client.get(endpoint)

            # --- CRITICAL FIX: Manually check for 3xx status codes which indicate unauthenticated redirect ---
            if 300 <= response.status_code < 400:
                logger.error(
                    "Authentication required: Received redirect (Status %d) to login page for document %s. Check API token.",
                    response.status_code, document_id)
                # Raising a custom error here since a 302 on this endpoint means authorization failed.
                raise RuntimeError(
                    f"Authentication Failure: Paperless redirected to login page when trying to fetch text for document {document_id}. Status: {response.status_code}")

            response.raise_for_status()

            document_text = response.json().get('content')
            if not document_text:
                logger.warning(
                    "Retrieved text is empty for document %s. This may indicate poor OCR quality or an empty file.",
                    document_id)

            return document_text

        except httpx.HTTPStatusError as e:
            logger.error("Failed to retrieve text for document %s: %s", document_id, e)
            raise RuntimeError(
                f"Failed to retrieve text from Paperless for document {document_id}. Status: {e.response.status_code}")
        except Exception as e:
            logger.error("Error retrieving text for document %s: %s", document_id, e)
            raise

    # services/clients/paperless_client.py (Add these methods to the class)

    from typing import Dict, Any, List, Optional
    import logging
    # Assume PaperlessClient is initialized with base_url and credentials/token

    logger = logging.getLogger(__name__)

    # --- Helper Mapping for Schema Types to Paperless Types ---
    # Paperless field types: string, integer, float, boolean, date, document_link
    SCHEMA_TYPE_MAP = {
        "string": "string",
        "number": "float",  # Use float for Pydantic's 'number' type (covers decimals)
        "integer": "integer",
        "boolean": "boolean",
        "date": "date"  # Assuming a custom type for dates, otherwise use 'string'
    }

    async def _get_all_custom_fields(self) -> List[Dict[str, Any]]:
        """Internal method to fetch all existing custom fields."""
        try:
            response = await self.client.get("/api/custom_fields/")
            response.raise_for_status()
            return response.json().get("results", [])
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch custom fields: {e}")
            return []

    async def ensure_custom_field(self, schema_field_name: str, schema_type: str) -> Optional[int]:
        """
        Checks if a custom field exists based on the schema name and creates it if not.
        Returns the Paperless Custom Field ID.
        """

        # Standardize the name and map the type
        paperless_name = schema_field_name.replace('_', ' ').title()  # e.g., 'invoice_total' -> 'Invoice Total'
        field_type = SCHEMA_TYPE_MAP.get(schema_type, "string")

        existing_fields = await self._get_all_custom_fields()

        # Check if field already exists
        for field in existing_fields:
            if field['name'].lower() == paperless_name.lower():
                logger.info(f"Custom field '{paperless_name}' already exists (ID: {field['id']}).")
                return field['id']

        # If not found, create it
        creation_payload = {
            "name": paperless_name,
            "data_type": field_type,
            "default_value": None
        }

        try:
            response = await self.client.post("/api/custom_fields/", json=creation_payload)
            response.raise_for_status()
            new_field = response.json()
            logger.info(f"Created new Custom Field '{paperless_name}' (ID: {new_field['id']}).")
            return new_field['id']
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create Custom Field '{paperless_name}': {e}. Response: {e.response.text}")
            return None

    # services/clients/paperless_client.py (Updated method)

    # ... (Existing imports and class structure remain) ...

    async def update_document_metadata(
            self,
            document_id: int,
            template_id: str,
            custom_field_values: Dict[int, Any]
    ) -> bool:
        """
        Updates a document in Paperless using the bulk_edit endpoint for Custom Fields
        and Tagging.

        Args:
            document_id: The ID of the document in Paperless.
            template_id: The ID of the newly registered template.
            custom_field_values: A dictionary mapping {Paperless_Field_ID: Extracted_Value}.

        Returns:
            bool: True if all updates were successful, False otherwise.
        """

        success_status = True
        bulk_edit_endpoint = "/api/documents/bulk_edit/"

        # --- 1. Prepare Custom Field Payload ---
        # The 'modify_custom_fields' method requires 'add_custom_fields' payload
        add_custom_fields_payload: Dict[int, Any] = {}
        for field_id, value in custom_field_values.items():
            # Ensure value is JSON serializable/Paperless acceptable (converting if needed)
            add_custom_fields_payload[field_id] = str(value) if not isinstance(value, (str, int, float, bool,
                                                                                       type(None))) else value

        if add_custom_fields_payload:
            custom_field_payload = {
                "documents": [document_id],
                "method": "modify_custom_fields",
                "parameters": {
                    "add_custom_fields": add_custom_fields_payload,
                    # We are not removing any fields here
                    "remove_custom_fields": []
                }
            }

            try:
                cf_response = await self.client.post(bulk_edit_endpoint, json=custom_field_payload)
                cf_response.raise_for_status()
                logger.info(f"Custom fields updated for document {document_id}.")
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"Failed to apply custom fields via bulk_edit (Doc {document_id}): {e.response.text}")
                success_status = False

        # --- 2. Tagging Payload (Associating the Template ID) ---
        # We must first ensure the tag exists. The simplest way is to assume the Template ID is
        # the name of a tag, but the API requires the TAG_ID.

        # NOTE: To use add_tag, we need the TAG_ID. We MUST add a step to get/create the tag ID.
        tag_id = await self._ensure_tag_exists(template_id)  # Assume this helper function exists

        if tag_id and success_status:  # Only proceed if custom fields succeeded
            tagging_payload = {
                "documents": [document_id],
                "method": "add_tag",
                "parameters": {
                    "tag": tag_id
                }
            }

            try:
                tag_response = await self.client.post(bulk_edit_endpoint, json=tagging_payload)
                tag_response.raise_for_status()
                logger.info(f"Document {document_id} tagged with Template ID: {template_id}.")
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to tag document {document_id} via bulk_edit: {e.response.text}")
                success_status = False

        # 3. Final Result
        if success_status:
            logger.info(f"Document {document_id} successfully updated with metadata and template tag.")

        return success_status

    # --- ASSUMED HELPER METHOD (required for the above logic) ---
    async def _ensure_tag_exists(self, tag_name: str) -> Optional[int]:
        """
        Checks if a tag exists by name and creates it if not. Returns the Paperless Tag ID.
        (This is needed because bulk_edit requires the ID, not the name.)
        """
        # 1. GET /api/tags/?name__iexact=tag_name to check existence
        # 2. If not found, POST to /api/tags/ {"name": tag_name}
        # 3. Returns the ID from the existing or new tag.
        # Note: This complexity is hidden here but must be implemented for the call to work.
        try:
            # Example implementation placeholder:
            response = await self.client.get(f"/api/tags/?name__iexact={tag_name}")
            if response.status_code == 200 and response.json().get('results'):
                return response.json()['results'][0]['id']

            response = await self.client.post("/api/tags/", json={"name": tag_name})
            response.raise_for_status()
            return response.json()['id']
        except Exception as e:
            logger.error(f"Failed to ensure tag '{tag_name}' exists: {str(e)}")
            return None

    # services/clients/paperless_client.py (Add this to PaperlessClient class)

    async def _ensure_document_type_exists(self, doc_type_name: str) -> Optional[int]:
        """
        Checks if a Paperless Document Type exists and creates it if not. Returns the ID.
        (This is analogous to the _ensure_tag_exists helper.)
        """
        try:
            # Check existing types
            check_response = await self.client.get(f"/api/document_types/?name__iexact={doc_type_name}")
            check_response.raise_for_status()

            results = check_response.json().get('results')
            if results:
                return results[0]['id']

            # Create if not found
            creation_response = await self.client.post("/api/document_types/", json={"name": doc_type_name})
            creation_response.raise_for_status()
            return creation_response.json()['id']

        except Exception as e:
            logger.error(f"Failed to ensure document type '{doc_type_name}' exists: {str(e)}")
            return None

    async def set_document_type_by_name(self, document_id: int, doc_type_name: str) -> bool:
        """
        Sets the document_type for a specific document using its name.
        """
        doc_type_id = await self._ensure_document_type_exists(doc_type_name)

        if not doc_type_id:
            logger.warning(
                f"Skipping document type setting for {document_id}: Could not find or create '{doc_type_name}' type ID.")
            return False

        bulk_edit_payload = {
            "documents": [document_id],
            "method": "set_document_type",
            "parameters": {
                "document_type": doc_type_id
            }
        }

        try:
            response = await self.client.post("/api/documents/bulk_edit/", json=bulk_edit_payload)
            response.raise_for_status()
            logger.info(f"Document {document_id} successfully assigned to Document Type: {doc_type_name}.")
            return True
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to set document type via bulk_edit: {e.response.text}")
            return False