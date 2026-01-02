import json
from pathlib import Path


def load_json_file(file_path: str) -> dict:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"No file found at {file_path}")

    with path.open(mode='r', encoding='utf-8') as file:
        return json.load(file)

