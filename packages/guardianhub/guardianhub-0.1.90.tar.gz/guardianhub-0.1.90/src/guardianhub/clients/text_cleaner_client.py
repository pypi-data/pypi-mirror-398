# clients/metadata_extractor_client.py

import uuid

from clients import LLMService

from guardianhub import get_logger

logger = get_logger(__name__)


class TextCleanerClient:
    def __init__(self, llm_service:LLMService):
        self.llm_service = llm_service

    async def call_llm_extraction_service_impl(self,input_data: dict) -> str:
        """Implementation of LLM-based invoice extraction service call."""

        # 1️⃣ Normalize the input to get plain text
        if isinstance(input_data, str):
            extracted_text = input_data
        else:
            extracted_text = input_data.get("text")

        if not extracted_text or not isinstance(extracted_text, str):
            raise ValueError("No valid text provided for LLM extraction")

        if isinstance(extracted_text, bytes):
            extracted_text = extracted_text.decode("utf-8")

        # 2️⃣ Initialize LLM service

        # 3️⃣ Generate internal tracking ID (not passed to LLM)
        workflow_invoice_id = input_data.get("invoice_id") or f"inv-{str(uuid.uuid4())[:8]}"

        # 4️⃣ Define system prompt (without injecting invoice_id)
        system_prompt = (
            "You are an expert AI assistant specialized in extracting structured data from invoices. "
            "Analyze the given invoice text and extract key details such as invoice number, vendor, date, amount, and due date. "
            "Return your response as a JSON object matching the given schema.\n"
            "If any field is missing, use null."
        )

        # 5️⃣ Call LLM for structured extraction
        try:
            invoice_data = await self.llm_service.get_structured_response(
                user_input=extracted_text,
                system_prompt=system_prompt,
                response_model=None
            )

            result = invoice_data.model_dump(exclude_unset=True)
            result["workflow_invoice_id"] = workflow_invoice_id  # attach for traceability
            return result

        except Exception as e:
            logger.error(f"LLM extraction failed: {str(e)}")
            raise RuntimeError("Failed to process invoice with LLM") from e