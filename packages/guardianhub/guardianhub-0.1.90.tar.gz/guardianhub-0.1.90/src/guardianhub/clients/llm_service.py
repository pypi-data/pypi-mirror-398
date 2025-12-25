# llm/llm_service.py

import json
from typing import Any, Dict, Type, TypeVar, List, Optional

from openai import BaseModel
from pydantic import ValidationError
from pydantic import create_model

from guardianhub.config.settings import settings
from guardianhub import get_logger
from guardianhub.models.template.extraction import StructuredExtractionResult
from guardianhub.models.template.suggestion import TemplateSchemaSuggestion
from .llm_client import LLMClient
from ..utils.json_utils import parse_structured_response

logger = get_logger(__name__)
T = TypeVar("T", bound=BaseModel)


class LLMService:
    """Service layer for structured extraction from Aura-LLM."""


    def __init__(self, llm_client: LLMClient):

        self.llm = llm_client
        logger.info("LLMService initialized with client: %s", llm_client.__class__.__name__)


    def create_model_from_schema(self,schema: Dict[str, Any]) -> Type[BaseModel]:
        """Create a dynamic Pydantic model from a JSON schema."""
        fields = {}
        for field_name, field_props in schema.get('properties', {}).items():
            field_type = self._get_python_type(field_props.get('type', 'string'))
            fields[field_name] = (field_type, field_props.get('description', ''))

        return create_model('DynamicModel', **fields)

    def _get_python_type(self, schema_type) -> type:
        """Map JSON schema types to Python types, handling both strings and lists of types."""
        # If it's a list, use the first type (or default to string)
        if isinstance(schema_type, list):
            schema_type = schema_type[0] if schema_type else 'string'

        # Ensure schema_type is a string
        schema_type = str(schema_type).lower()

        type_map = {
            'string': str,
            'integer': int,
            'number': float,
            'boolean': bool,
            'array': list,
            'object': dict,
        }
        return type_map.get(schema_type, str)

    async def get_structured_response(
            self,
            user_input: str,
            system_prompt: str,
            response_model: Optional[Type[T]] = None,
            model_json_schema: Optional[Dict[str, Any]] = None,
            temperature: float = settings.llm.temperature,
            max_tokens: int = settings.llm.max_tokens,
    ) -> T:
        """Request structured JSON response from Aura-LLM and parse it safely.

        Args:
            user_input: The input text to process
            system_prompt: Task-specific instructions for the LLM
            response_model: Pydantic model defining the expected response schema
            temperature: Controls randomness (0.0 = deterministic)
            max_tokens: Maximum number of tokens to generate

        Returns:
            An instance of the response model with the extracted data
        """
        # Get JSON schema from the response model
        """Request structured JSON response from Aura-LLM and parse it safely."""
        logger.info("Starting get_structured_response")
        logger.info("System prompt: %s", system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt)
        logger.info("User input length: %d characters", len(user_input))
        if model_json_schema and not response_model:
            logger.info("Creating model from JSON schema")
            response_model = self.create_model_from_schema(model_json_schema)

        if not response_model:
            error_msg = "Either response_model or model_json_schema must be provided"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Create schema description for the LLM
        schema = response_model.model_json_schema()
        logger.debug("Using schema: %s", json.dumps(schema, indent=2))

        schema_description = json.dumps(schema, indent=2)

        # --- NEW: Single, Unified, Aggressive System Prompt ---
        # Merging the general JSON generator persona with the specific task and schema.
        unified_system_prompt = f"""
        You are an **expert, precise JSON generator and data extraction API**. 

        {system_prompt}

        Your SOLE output **MUST** be a single, valid JSON object that **STRICTLY** conforms to the following schema. **DO NOT** include any other text, markdown wrappers (like ```json), explanations, or custom fields.

        --- REQUIRED JSON SCHEMA ---
        {schema_description}
        --- END SCHEMA ---

        STRICT CONFORMANCE RULES:
        1. The output MUST be raw JSON text, with NO wrapping characters.
        2. Only include fields defined in the schema (document_type, metadata, confidence).
        3. If a field is a complex object (like 'metadata'), it MUST be output as a **direct JSON object**, NOT a nested JSON string. For example: "metadata": {{ "key": "value" }}, NOT "metadata": "{{\\"key\\": \\"value\\"}}".
        4. Maintain the exact field names and types from the schema.
        """

        # Using a single system instruction to avoid message conflict
        messages = [
            {"role": "system", "content": unified_system_prompt},
            {"role": "user", "content": user_input},
        ]

        try:
            logger.debug("Sending request to LLM with %d messages", len(messages))
            response = await self.llm.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                model=settings.llm.model_key,
                response_format={"type": "json"},
            )
            logger.debug("Received response from LLM")
            if not response:
                error_msg = "Empty response from LLM"
                logger.error(error_msg)
                raise ValueError(error_msg)

            logger.debug("Full LLM response: %s", json.dumps(response, indent=2))

            # Extract and clean the response
            raw_text = (
                response.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )

            if not raw_text:
                error_msg = "Empty content in LLM response"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Extract and validate JSON
            logger.debug("Raw text from LLM: %s", raw_text)
            result = parse_structured_response(raw_text, response_model)
            logger.info("Successfully parsed structured response")
            return result
        except json.JSONDecodeError as e:
            error_msg = f"Failed to decode LLM response as JSON: {str(e)}"
            logger.error("%s\nRaw response: %s", error_msg, raw_text)
            raise
        except ValidationError as e:
            error_msg = f"Response validation failed: {str(e)}"
            logger.error("%s\nResponse was: %s", error_msg, raw_text)
            raise
        except Exception as e:
            logger.error("Unexpected error in get_structured_response: %s", str(e), exc_info=True)
            raise

    async def classify_and_extract_document_metadata(
            self,
            document_text: str,
            available_document_types: List[str] = None
    ) -> StructuredExtractionResult:
        """
        Performs unified zero-shot classification and structured metadata extraction.

        Args:
            document_text: The full text content of the document.
            available_document_types: A list of known document types to classify against.

        Returns:
            StructuredExtractionResult: An object containing the classified type and extracted metadata.
        """
        """Suggests a template schema based on document text and type."""
        logger.info("Suggesting template schema for document type: %s", document_type)
        logger.debug("Document text length: %d characters", len(document_text))

        try:
            if available_document_types is None:
                available_document_types = ["Invoice", "Receipt", "Contract", "Bill", "Statement", "Form", "Other",
                                            "Technical Knowledge Documents"]

            # Build the system prompt for the unified task
            document_types_list = ", ".join(available_document_types)

            system_prompt = f"""
            You are an expert document classification and data extraction engine.
            Your task is two-fold:
            1. Classify the document text into one of the following high-level types: **{document_types_list}**.
            2. Based on the classification, extract all relevant key-value metadata pairs.

            Extraction Rules:
            - If classified as 'Invoice' or 'Receipt': Extract fields like `vendor_name`, `date`, `total_amount`, `currency`, and `invoice_number`.
            - If classified as 'Contract' or 'Statement': Extract fields like `parties`, `start_date`, `end_date`, and `document_title`.
            - If classified as 'Technical Knowledge Documents': Extract fields like `document_title`, `key_components` (list of strings), and `abstract`.
            - Extract dates in ISO 8601 format (YYYY-MM-DD) and monetary values as floats/strings.
            - If the document is classified as 'Other', return an empty dictionary for 'metadata'.
            - If no type can be determined, use 'Unknown' for `document_type`.
            """

            suggestion = await self.get_structured_response(
                user_input=document_text,
                system_prompt=system_prompt,
                response_model=StructuredExtractionResult,
                temperature=0.0
            )
            logger.info("Successfully generated template suggestion")
            logger.debug("Suggestion: %s", suggestion.model_dump_json(indent=2))
            return suggestion
        except Exception as e:
            logger.error("Failed to generate template suggestion: %s", str(e), exc_info=True)
            raise

    async def suggest_template_schema(self, document_text: str, document_type: str) -> Optional[
        TemplateSchemaSuggestion]:
        """
        Uses the LLM to analyze document text and suggest a new template schema with structured output.

        Args:
            document_text: The full cleaned text of the new document.
            document_type: The type of document being processed.

        Returns:
            A validated TemplateSchemaSuggestion instance or None if processing fails.
        """
        try:
            # 1. Define the system prompt with clear instructions for structured output
            system_prompt = (
                "You are an expert document template designer. Analyze the provided document text and "
                "return a structured response with the following fields:\n"
                "- document_type: The type of document (e.g., 'Invoice', 'Contract')\n"
                "- template_name: A descriptive name for this template\n"
                "- description: A brief description of the document's purpose\n"
                "- fields: A list of fields with their types and descriptions\n"
                "- required_fields: List of required field names\n"
                "- examples: Sample values for each field\n\n"
                "The response must be a valid JSON object that matches the TemplateSchemaSuggestion schema."
            )

            # 2. Prepare the user query with document context
            user_query = (
                f"Document Type: {document_type}\n\n"
                "Document Content:\n"
                f"--- DOCUMENT START ---\n"
                f"{document_text[:4000]}"  # Limit context window
                f"\n--- DOCUMENT END ---\n\n"
                "Please analyze this document and provide a structured template suggestion."
            )

            # 3. Get structured response using the LLM client
            response = await self.llm.generate_structured(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                response_model=TemplateSchemaSuggestion,
                temperature=0.1,  # Lower temperature for more deterministic output
                max_tokens=2048
            )

            logger.info(f"Generated template schema: {response}")
            return response

        except ValidationError as ve:
            logger.error(f"Schema validation failed: {str(ve)}")
            # Try to recover partial data if possible
            try:
                if hasattr(ve, 'raw_errors') and ve.raw_errors:
                    # Log the specific validation errors
                    for error in ve.raw_errors:
                        logger.debug(f"Validation error: {error}")
                    # If partial data is available, return it with a warning
                    if hasattr(ve, 'model') and ve.model:
                        return ve.model
            except Exception as e:
                logger.debug(f"Error during validation error handling: {str(e)}")

        except Exception as e:
            logger.error(f"Failed to generate template schema: {str(e)}", exc_info=True)

        return None