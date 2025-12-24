"""
Parser HTML to video specs dictionary
"""
import re
from typing import Dict, Any
from datetime import datetime


def from_html(html_data: str) -> Dict[str, Any]:
    """
    Parse HTML string to video specifications dictionary.
    Uses regex-based parsing for a tolerant approach.

    Args:
        html_data: HTML formatted string

    Returns:
        Dictionary containing video specifications

    Raises:
        ValueError: If HTML cannot be parsed
    """
    specs = {
        "technical": {},
        "setting_atmosphere": {},
        "camera_visuals": {},
        "scene_content": {},
        "characters": [],
        "dialogs": [],
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "tool_version": "1.0.0"
        }
    }

    def extract_section_params(section_title: str) -> Dict[str, str]:
        """Extract parameters from a section."""
        params = {}
        # Find the section - match emoji + text in h2
        section_pattern = rf'<h2>[^<]*{re.escape(section_title)}.*?</h2>(.*?)</div>\s*(?=<div class="section"|</div>\s*<div class="metadata"|$)'
        section_match = re.search(section_pattern, html_data, re.DOTALL | re.IGNORECASE)

        if section_match:
            section_content = section_match.group(1)
            # Extract param divs
            param_pattern = r'<div class="param">\s*<div class="param-label">(.*?)</div>\s*<div class="param-value">(.*?)</div>\s*</div>'
            for match in re.finditer(param_pattern, section_content, re.DOTALL):
                label = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                value = re.sub(r'<[^>]+>', '', match.group(2)).strip()
                # Convert label to key format
                key = label.lower().replace(' ', '_')
                params[key] = value

        return params

    # Extract Technical Specifications
    specs["technical"] = extract_section_params("Technical Specifications")

    # Extract Setting & Atmosphere
    specs["setting_atmosphere"] = extract_section_params("Setting & Atmosphere")

    # Extract Camera & Visuals
    specs["camera_visuals"] = extract_section_params("Camera & Visuals")

    # Extract Scene Content
    scene_content = extract_section_params("Scene Content")
    # Convert subject_count to int if present
    if "subject_count" in scene_content:
        try:
            scene_content["subject_count"] = int(scene_content["subject_count"])
        except (ValueError, TypeError):
            pass
    specs["scene_content"] = scene_content

    # Extract Characters
    char_section_pattern = r'<h2>[^<]*Characters.*?</h2>(.*?)</div>\s*(?=</div>\s*<div class="metadata"|$)'
    char_section_match = re.search(char_section_pattern, html_data, re.DOTALL | re.IGNORECASE)

    if char_section_match:
        char_section = char_section_match.group(1)
        # Find individual character divs
        char_div_pattern = r'<div class="character">(.*?)</div>\s*(?=<div class="character"|$)'
        for char_match in re.finditer(char_div_pattern, char_section, re.DOTALL):
            char_content = char_match.group(1)
            character = {}

            # Extract character name from h3
            name_match = re.search(r'<h3>Character #\d+:\s*(.*?)</h3>', char_content)
            if name_match:
                character["name"] = name_match.group(1).strip()

            # Extract character params
            param_pattern = r'<div class="param">\s*<div class="param-label">(.*?)</div>\s*<div class="param-value">(.*?)</div>\s*</div>'
            for match in re.finditer(param_pattern, char_content, re.DOTALL):
                label = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                value = re.sub(r'<[^>]+>', '', match.group(2)).strip()
                key = label.lower().replace(' ', '_')
                character[key] = value

            if character:
                specs["characters"].append(character)

    # Extract metadata from footer
    metadata_pattern = r'Created on (.*?) \| Tool v(.*?)</div>'
    metadata_match = re.search(metadata_pattern, html_data)
    if metadata_match:
        specs["metadata"]["created_at"] = metadata_match.group(1).strip()
        specs["metadata"]["tool_version"] = metadata_match.group(2).strip()

    return specs
