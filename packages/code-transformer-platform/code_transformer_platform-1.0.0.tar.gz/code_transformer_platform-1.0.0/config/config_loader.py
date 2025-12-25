import yaml
from pathlib import Path


class ConfigLoader:
    @staticmethod
    def load(path: str) -> dict:
        file = Path(path)
        if not file.exists():
            raise FileNotFoundError(f"Config not found: {path}")
        with open(file, "r") as f:
            return yaml.safe_load(f)
