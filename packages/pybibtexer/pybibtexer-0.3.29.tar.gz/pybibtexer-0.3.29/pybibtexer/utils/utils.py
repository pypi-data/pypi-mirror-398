import json
import os
from typing import Any


def load_json_file(file_path: str) -> dict[str, Any]:
    if not file_path.strip():
        return {}

    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        return {}

    try:
        # Open and read the JSON file
        with open(file_path, encoding="utf-8", newline="\n") as file:
            return json.load(file)

    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return {}


def save_to_json(data: dict, full_json: str) -> None:
    try:
        if data:
            with open(full_json, "w", encoding="utf-8", newline="\n") as f:
                json.dump(data, f, indent=4, sort_keys=True, ensure_ascii=True)

    except Exception as e:
        print(f"Error saving JSON file: {e}")

    return None
