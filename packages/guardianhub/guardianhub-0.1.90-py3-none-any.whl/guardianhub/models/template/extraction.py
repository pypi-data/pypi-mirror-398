from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from ..registry.registry import register_model


@register_model
class StructuredExtractionResult(BaseModel):
    """
    Unified result model for document classification and metadata extraction.
    The LLM must populate the 'document_type' and 'metadata' fields.
    """
    document_type: str = Field(
        ...,
        description=(
            "The primary classification of the document. Must be one of the provided types "
            "(e.g., 'Invoice', 'Receipt', 'Contract', 'Technical Knowledge Documents', 'Unknown')."
        )
    )
    # FIX: Use default_factory=dict. This ensures that if the field is missing or comes in as null,
    # Pydantic accepts it and defaults it to an empty dictionary {}.
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="A dictionary containing the extracted key-value metadata pairs specific to the classified document_type."
    )
    confidence: float = Field(
        1.0,
        description="A confidence score (0.0 to 1.0) of the classification/extraction accuracy. Default to 1.0."
    )