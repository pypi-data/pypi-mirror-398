from typing import Type, Dict, Any, Optional
from pydantic import BaseModel
from .registry import MODEL_REGISTRY, get_model
from .dynamic_loader import DynamicModelBuilder


class Loader:

    @staticmethod
    def load(
            model_name: Optional[str] = None,
            schema_json: Optional[Dict[str, Any]] = None
    ) -> Type[BaseModel]:
        """
        Load a Pydantic model either by registry name or dynamically from schema.

        Args:
            model_name: Optional name of a registered model
            schema_json: Optional JSON schema dict to build a dynamic model

        Returns:
            Pydantic model class
        """
        # 1. Try registry first
        if model_name:
            try:
                return get_model(model_name)
            except ValueError:
                pass  # fallback to schema if provided

        # 2. Generate dynamically from schema
        if schema_json:
            dynamic_name = model_name or "DynamicModel"
            return DynamicModelBuilder.load_from_schema(dynamic_name, schema_json)

        # 3. Neither provided → raise error
        raise ValueError("Either a registered model name or schema JSON must be provided")
