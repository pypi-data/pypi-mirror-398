from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from ..registry.registry import register_model


@register_model
class TemplateSchemaSuggestion(BaseModel):
    """
    Schema expected from the LLM for a new document type.
    """
    template_id: str = Field(
        ...,
        description="The id with which it will be identified."
    )

    document_type: str = Field(
        ...,
        description="The high-level category (e.g., 'Invoice', 'CV', 'Tax Form')."
    )

    template_name: str = Field(
        ...,
        description="A unique, descriptive name (e.g., 'ACME Q3 2024 Invoice')."
    )

    fingerprint_vector: Optional[List[float]] = Field(
        None,
        description="The fingerprint vector of the document."
    )

    json_schema: Dict[str, Any] = Field(
        ...,
        description=(
            "The Pydantic-compatible JSON Schema defining the required "
            "extraction fields."
        )
    )

    required_keywords: List[str] = Field(
        default_factory=list,
        description="Top 5 keywords unique to this document template."
    )
