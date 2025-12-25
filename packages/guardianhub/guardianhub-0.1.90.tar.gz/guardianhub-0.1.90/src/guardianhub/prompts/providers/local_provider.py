import yaml, os
from typing import Optional, Dict, Any


class LocalPromptProvider(PromptProvider):
    def __init__(self, directory: str):
        self.directory = directory

    async def get_prompt(self, name: str, version: Optional[str] = None) -> Dict[str, Any]:
        filename = f"{name}.yaml"
        path = os.path.join(self.directory, filename)

        if not os.path.exists(path):
            raise FileNotFoundError(f"Prompt '{name}' not found locally")

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        if version and "versions" in data:
            return data["versions"].get(version)

        return data
