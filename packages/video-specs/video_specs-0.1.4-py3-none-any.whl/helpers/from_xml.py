"""
Parser XML to video specs dictionary
"""
import xml.etree.ElementTree as ET
from typing import Dict, Any
from datetime import datetime


def from_xml(xml_data: str) -> Dict[str, Any]:
    """
    Parse XML string to video specifications dictionary.

    Args:
        xml_data: XML formatted string

    Returns:
        Dictionary containing video specifications

    Raises:
        ValueError: If XML is invalid
    """
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML format: {e}")

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

    # Parse Metadata
    metadata_elem = root.find("Metadata")
    if metadata_elem is not None:
        for child in metadata_elem:
            key = child.tag.replace("-", "_")
            specs["metadata"][key] = child.text or ""

    # Parse Technical
    technical_elem = root.find("Technical")
    if technical_elem is not None:
        for child in technical_elem:
            key = child.tag.replace("-", "_")
            specs["technical"][key] = child.text or ""

    # Parse SettingAtmosphere
    setting_elem = root.find("SettingAtmosphere")
    if setting_elem is not None:
        for child in setting_elem:
            key = child.tag.replace("-", "_")
            specs["setting_atmosphere"][key] = child.text or ""

    # Parse CameraVisuals
    camera_elem = root.find("CameraVisuals")
    if camera_elem is not None:
        for child in camera_elem:
            key = child.tag.replace("-", "_")
            specs["camera_visuals"][key] = child.text or ""

    # Parse SceneContent
    scene_elem = root.find("SceneContent")
    if scene_elem is not None:
        for child in scene_elem:
            key = child.tag.replace("-", "_")
            value = child.text or ""
            # Try to convert subject_count to int
            if key == "subject_count":
                try:
                    specs["scene_content"][key] = int(value)
                except (ValueError, TypeError):
                    specs["scene_content"][key] = value
            else:
                specs["scene_content"][key] = value

    # Parse Characters
    characters_elem = root.find("Characters")
    if characters_elem is not None:
        for char_elem in characters_elem.findall("Character"):
            character = {}
            for child in char_elem:
                key = child.tag.replace("-", "_")
                character[key] = child.text or ""
            if character:
                specs["characters"].append(character)

    # Parse Dialogs
    dialogs_elem = root.find("dialogs")
    if dialogs_elem is not None:
        for line_elem in dialogs_elem.findall("line"):
            dialog = {}
            char_elem = line_elem.find("character")
            if char_elem is not None:
                dialog["character"] = char_elem.text or ""

            emotion_elem = line_elem.find("emotion")
            if emotion_elem is not None:
                dialog["emotion"] = emotion_elem.text or ""

            content_elem = line_elem.find("content")
            if content_elem is not None:
                dialog["content"] = content_elem.text or ""

            if dialog:
                specs["dialogs"].append(dialog)

    return specs
