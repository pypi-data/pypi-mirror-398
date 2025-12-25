"""Core settings for the GuardianHub Foundation SDK."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field, ConfigDict
# Correct imports for Pydantic v2 and Pydantic-Settings v2
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_config_defaults(env: str = None) -> dict:
    """Load configuration defaults from JSON files based on environment."""
    if env is None:
        env = os.environ.get("ENVIRONMENT", "development").lower()

    # Mapping common aliases
    if env == "dev":
        env = "development"

    config_dir = Path(__file__).parent
    possible_files = [f"config_{env}.json", "config_dev.json", "config_development.json"]

    for filename in possible_files:
        config_path = config_dir / filename
        if config_path.exists():
            try:
                with open(config_path) as f:
                    return json.load(f)
            except Exception:
                continue
    return {}

class ServiceInfo(BaseModel):
    """Metadata about the microservice using the SDK."""
    name: str = "guardianhub-service"
    version: str = "0.0.1"
    id: str = "guardian-01"
    host: str = "0.0.0.0"
    port: int = 8001


class LoggingSettings(BaseModel):
    """Standardized logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

class ModelConfig(BaseModel):
    """Standardized schema for any LLM model configuration."""
    model_name: str
    provider: str = "OPENAI"  # GEMINI, OLLAMA, OPENAI, etc.
    base_url: str
    api_key: str = "your-api-key-here"
    temperature: float = 0.1
    max_tokens: int = 2048
    streaming: bool = False
    headers: Dict[str, str] = {}
    model_kwargs: Dict[str, Any] = {}

class LLMSettings(BaseModel):
    """Registry of models defined in the config JSON."""
    # This matches your "model_configs": { "judge": {...}, "tuned": {...} }
    model_configs: Dict[str, ModelConfig] = Field(default_factory=dict)

    def get_config(self, key: str = "default") -> ModelConfig:
        """Helper to safely retrieve a model config by its key."""
        return self.model_configs.get(key, self.model_configs.get("default"))

class ServiceEndpoints(BaseModel):
    """
    Endpoints for essential shared services.
    Supports dictionary-style access for backward compatibility.
    """
    model_config = ConfigDict(extra="allow")

    # Infrastructure & Databases
    POSTGRES_URL: str = "postgresql://user:password@localhost:5432/guardianhub"
    CONSUL_HTTP_ADDR: str = "http://localhost:8500"

    # Shared GuardianHub Services
    TOOL_REGISTRY_URL: str = "http://localhost:8000"
    TOOL_EXECUTOR_URL: str = "http://localhost:8003"
    LLM_URL: str = "http://localhost:8001"
    LANGFUSE_HOST: str = "http://localhost:3000"
    KG_INGESTION_URL: str = "http://localhost:8002"
    GRAPH_DB_URL: str = "http://localhost:8009"
    VECTOR_SERVICE_URL: str = "http://localhost:8005"

    # Observability
    # OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4318"
    LANGFUSE_OTLP_TRACES_ENDPOINT: str = "http://localhost:4318"
    ENVIRONMENT: str = "development"

    def __init__(self, **data):
        # Handle case-insensitive environment variables
        processed_data = {}
        for k, v in data.items():
            # Convert to uppercase for case-insensitive matching
            if k.upper() in self.model_fields:
                processed_data[k.upper()] = v
            else:
                processed_data[k] = v

        # Initialize the model with known fields
        super().__init__(**{k: v for k, v in processed_data.items()
                          if k in self.model_fields})

        # Store extra fields in __pydantic_extra__
        extra_data = {k: v for k, v in processed_data.items()
                     if k not in self.model_fields}
        if extra_data:
            if not hasattr(self, '__pydantic_extra__'):
                object.__setattr__(self, '__pydantic_extra__', {})
            self.__pydantic_extra__.update(extra_data)

    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-style get method for backward compatibility."""
        # First try to get from model fields (case-insensitive)
        key_upper = key.upper()
        if key_upper in self.model_fields:
            return getattr(self, key_upper, default)

        # Then try to get from extra fields (case-sensitive)
        if hasattr(self, '__pydantic_extra__'):
            # Try exact match first
            if key in self.__pydantic_extra__:
                return self.__pydantic_extra__[key]
            # Try case-insensitive match
            for k, v in self.__pydantic_extra__.items():
                if k.upper() == key_upper:
                    return v

        # Finally, try direct attribute access
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        """Enable dictionary-style access."""
        value = self.get(key)
        if value is None and not hasattr(self, key) and not (hasattr(self, '__pydantic_extra__') and key in self.__pydantic_extra__):
            raise KeyError(f"'{key}' not found in ServiceEndpoints")
        return value

class VectorConfig(BaseModel):
    """Vector database configuration."""
    default_collection: str = Field("", description="Default collection name")


class CoreSettings(BaseSettings):
    """
    The Core Settings class. Automatically merges bundled JSON
    profiles with environment variables.
    """
    model_config = SettingsConfigDict(
        env_prefix="GH_",
        env_nested_delimiter="__",
        extra="allow"
    )

    service: ServiceInfo = Field(default_factory=ServiceInfo)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    endpoints: ServiceEndpoints = Field(default_factory=ServiceEndpoints)
    vector: VectorConfig = Field(default_factory=VectorConfig)
    excluded_urls: Optional[str] = None
    max_retries: int = 3
    retry_delay: int = 2
    http_timeout: int = 30

    def __init__(self, **data):
        # Handle environment variable overrides for ENVIRONMENT
        env = os.environ.get("ENVIRONMENT")
        if env:
            if "endpoints" not in data:
                data["endpoints"] = {}
            data["endpoints"]["ENVIRONMENT"] = env

        # Let Pydantic handle the main initialization
        super().__init__(**data)

        # Apply environment variable overrides for other fields
        # for field_name in self.model_fields:
        #     env_value = os.environ.get(f"GH_{field_name.upper()}")
        #     if env_value is not None and hasattr(self, field_name):
        #         setattr(self, field_name, env_value)

        # Handle nested environment variables for endpoints
        for key, value in os.environ.items():
            if key.startswith("GH_"):
                # Convert GH_ENDPOINTS__LLM_URL to llm_url
                attr_name = key[3:].replace("__", ".")
                setattr(self.endpoints, attr_name, value)

    @model_validator(mode="before")
    @classmethod
    def _bootstrap_config(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Load the appropriate config file based on environment
            env = data.get("ENVIRONMENT") or os.environ.get("ENVIRONMENT", "development")
            config_data = _load_config_defaults(env)

            if isinstance(config_data, dict):
                # Create a copy of the input data to avoid modifying it
                result = config_data.copy()

                # Update with environment variables, but preserve the endpoints
                if "endpoints" in data and isinstance(data["endpoints"], dict):
                    # Create a new endpoints dict with the config defaults
                    endpoints = result.get("endpoints", {}).copy()
                    # Update with any environment overrides
                    endpoints.update(data["endpoints"])
                    result["endpoints"] = endpoints

                # Update with any other non-endpoint data
                for key, value in data.items():
                    if key != "endpoints":
                        result[key] = value

                return result
        return data

@lru_cache()
def get_cached_settings() -> CoreSettings:
    return CoreSettings()


# Exported singleton
settings: CoreSettings = get_cached_settings()