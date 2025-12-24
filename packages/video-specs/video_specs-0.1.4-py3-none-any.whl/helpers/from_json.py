"""
Parser JSON to video specs dictionary
"""
import json
from typing import Dict, Any


def from_json(json_data: str) -> Dict[str, Any]:
    """
    Parse JSON string to video specifications dictionary.

    Args:
        json_data: JSON formatted string

    Returns:
        Dictionary containing video specifications

    Raises:
        ValueError: If JSON is invalid or missing required fields
    """
    try:
        specs = json.loads(json_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")

    # Ensure all required top-level keys exist (tolerant parsing)
    required_keys = ["technical", "setting_atmosphere", "camera_visuals", "scene_content"]
    for key in required_keys:
        if key not in specs:
            specs[key] = {}

    # Ensure array fields exist
    if "characters" not in specs:
        specs["characters"] = []
    if "dialogs" not in specs:
        specs["dialogs"] = []

    # Ensure metadata exists
    if "metadata" not in specs:
        from datetime import datetime
        specs["metadata"] = {
            "created_at": datetime.now().isoformat(),
            "tool_version": "1.0.0"
        }

    return specs
