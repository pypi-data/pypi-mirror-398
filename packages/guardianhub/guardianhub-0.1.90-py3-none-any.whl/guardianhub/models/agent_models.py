# models/agent_models.py
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from .registry.registry import register_model

@register_model
class AgentCreateRequest(BaseModel):
    """Request model for creating a new agent with flexible configuration.
    
    Example:
    ```json
    {
        "agent_name": "social-media-ai",
        "agent_type": "social_media",
        "description": "AI assistant for managing social media presence",
        "system_prompt": "You are a helpful social media assistant...",
        "config": {
            "target_platforms": ["LinkedIn", "Twitter", "Instagram"],
            "posting_schedule": {
                "Monday": ["10:00", "15:00"],
                "Wednesday": ["11:00", "17:00"]
            },
            "content_themes": ["Industry news", "Company updates"]
        }
    }
    """
    agent_name: str = Field(
        example="social-media-ai",
        description="Unique identifier for the agent (e.g., 'social-media-ai', 'customer-support-bot')."
    )
    agent_type: str = Field(
        example="social_media",
        description="Type of the agent (e.g., 'social_media', 'customer_support', 'data_analyst')."
    )
    description: str = Field(
        default="",
        example="AI assistant for managing social media presence",
        description="Brief description of the agent's purpose and functionality."
    )
    system_prompt: str = Field(
        example="You are a helpful social media assistant that creates engaging content...",
        description="The system prompt that defines the agent's behavior and capabilities."
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        example={
            "target_platforms": ["LinkedIn", "Twitter", "Instagram"],
            "posting_schedule": {
                "Monday": ["10:00", "15:00"],
                "Wednesday": ["11:00"]
            }
        },
        description="Agent-specific configuration parameters as key-value pairs."
    )

class AgentStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    TRAINING = "TRAINING"

@register_model
class AgentCreate(BaseModel):
    name: str = Field(..., description="Name of the agent")
    domain: str = Field(..., description="Domain of the agent")
    description: Optional[str] = Field(None, description="Description of the agent")
    system_prompt: str = Field(..., description="System prompt for the agent")
    status: AgentStatus = Field(AgentStatus.DRAFT, description="Status of the agent")
    tags: List[str] = Field(default_factory=list, description="Tags for the agent")
    default_tools: List[str] = Field(default_factory=list, description="List of default tool IDs")
    reflection_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration for agent reflection and learning"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the agent"
    )

@register_model
class Agent(AgentCreate):
    id: str = Field(..., description="Unique identifier for the agent")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


@register_model
class AgentResponse(BaseModel):
    """Response model for agent operations."""
    id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Name of the agent")
    agent_type: str = Field(..., description="Type of the agent")
    status: AgentStatus = Field(..., description="Current status of the agent")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    system_prompt: str = Field(..., description="System prompt for the agent")
    domain: str = Field(..., description="Domain of the agent")
    description: str = Field(default="", description="Description of the agent")
    message: Optional[str] = Field(None, description="Additional details about the operation")
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Agent-specific configuration parameters as key-value pairs."
    )
    class Config:
        from_attributes = True


# Wrapper model to ensure the LLM outputs a single JSON object.
@register_model
class SearchPhrasesResponse(BaseModel):
    """The expected structure for the LLM output."""
    search_phrases: List[str] = Field(
        ...,
        description="A list of 1 to 3 search phrases relevant to the agent's domain."
    )

@register_model
class LLMReflectionConfig(BaseModel):
    """Domain-specific reflection parameters to override defaults."""
    enabled: Optional[bool] = Field(None, description="Whether ACE reflection should be enabled.")
    optimization_types: List[str] = Field(default_factory=list,
                                          description="List of domain-specific optimization types (e.g., DataQuality, Sentiment).")
    synthesis_directives: Optional[Dict[str, Any]] = Field(None,
                                                           description="Directives for semantic tool synthesis (e.g., concrete_tool_whitelist).")
@register_model
class LLMKnowledgeSuggestion(BaseModel):
    """Suggestions for initial knowledge base articles or queries."""
    type: str = Field(..., description="Type of knowledge (e.g., 'document', 'query').")
    value: str = Field(..., description="The document ID, query text, or relevant URL.")

@register_model
class AgentLLMConfigSuggestion(BaseModel):
    """
    Structured configuration output generated by the LLM for a new agent.
    This replaces the unreliable Dict[str, Any] response.
    """
    system_prompt: str = Field(...,
                               description="The comprehensive, domain-specific system prompt and persona for the agent's core LLM.")

    # Use the structured reflection config model
    reflection_config: LLMReflectionConfig = Field(...,
                                                   description="Structured parameters for the agent's ACE reflection process.")

    # Suggestions for the warm-up phase (Initial query generation and knowledge seeding)
    initial_warmup_query: str = Field(...,
                                      description="The most effective synthetic query to run for the initial ACE warm-up.")
    knowledge_suggestions: List[LLMKnowledgeSuggestion] = Field(default_factory=list,
                                                                description="Suggestions for initial knowledge to pull or seed.")