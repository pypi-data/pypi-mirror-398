from typing import Dict, Any, Type, Optional, List
from pydantic import BaseModel, create_model
from pydantic.fields import Field

_DYNAMIC_MODEL_CACHE: Dict[str, Type[BaseModel]] = {}

class DynamicModelBuilder:

    @staticmethod
    def load_from_schema(
        model_name: str,
        schema_json: Dict[str, Any]
    ) -> Type[BaseModel]:

        # 1: Cache
        if model_name in _DYNAMIC_MODEL_CACHE:
            return _DYNAMIC_MODEL_CACHE[model_name]

        # 2: Generate
        model = DynamicModelBuilder._create_model(model_name, schema_json)
        _DYNAMIC_MODEL_CACHE[model_name] = model
        return model

    @staticmethod
    def _create_model(
        model_name: str,
        schema: Dict[str, Any]
    ) -> Type[BaseModel]:

        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])

        model_fields = {}

        for field_name, field_schema in properties.items():
            field_type = DynamicModelBuilder._map_schema_to_type(field_schema)

            default_value = ...
            if field_name not in required_fields:
                default_value = None

            model_fields[field_name] = (field_type, default_value)

        return create_model(model_name, **model_fields)

    @staticmethod
    def _map_schema_to_type(schema: Dict[str, Any]):
        """Map JSON Schema types to Python."""
        t = schema.get("type")

        # Primitive
        if t == "string":
            return str
        if t == "number":
            return float
        if t == "integer":
            return int
        if t == "boolean":
            return bool

        # Array
        if t == "array":
            item_schema = schema.get("items", {})
            item_type = DynamicModelBuilder._map_schema_to_type(item_schema)
            return List[item_type]

        # Object
        if t == "object":
            inner_model_name = "NestedObject"
            return DynamicModelBuilder._create_model(inner_model_name, schema)

        # Fallback
        return Any
