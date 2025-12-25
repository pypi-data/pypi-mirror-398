from typing import Dict, Type
from pydantic import BaseModel

MODEL_REGISTRY: Dict[str, Type[BaseModel]] = {}

def register_model(model: Type[BaseModel]):
    """
    Register a Pydantic model so it can be dynamically loaded across microservices.
    """
    MODEL_REGISTRY[model.__name__] = model
    return model

def get_model(name: str) -> Type[BaseModel]:
    try:
        return MODEL_REGISTRY[name]
    except KeyError:
        raise ValueError(f"Model '{name}' not found in registry")
