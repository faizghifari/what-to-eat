import os
import json
from typing import List, Dict, Any


def read_restaurant_config(config_path: str) -> List[Dict[str, Any]]:
    """Read restaurant config from a JSON file. Raise error if not found."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Config file '{config_path}' not found. Please create it (see scraper_config_example.json for format)."
        )
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)
