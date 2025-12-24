import xml.etree.ElementTree as ET


def to_xml(specs: dict) -> str:
    """Exporte en XML formaté"""
    root = ET.Element("VideoSpecifications")

    # Metadata
    metadata = ET.SubElement(root, "Metadata")
    for key, value in specs["metadata"].items():
        elem = ET.SubElement(metadata, key.replace("_", "-"))
        elem.text = str(value)

    # Technical
    technical = ET.SubElement(root, "Technical")
    for key, value in specs["technical"].items():
        elem = ET.SubElement(technical, key.replace("_", "-"))
        elem.text = str(value)

    # Setting & Atmosphere
    setting = ET.SubElement(root, "SettingAtmosphere")
    for key, value in specs["setting_atmosphere"].items():
        elem = ET.SubElement(setting, key.replace("_", "-"))
        elem.text = str(value)

    # Camera & Visuals
    camera = ET.SubElement(root, "CameraVisuals")
    for key, value in specs["camera_visuals"].items():
        elem = ET.SubElement(camera, key.replace("_", "-"))
        elem.text = str(value)

    # Scene Content
    scene = ET.SubElement(root, "SceneContent")
    for key, value in specs["scene_content"].items():
        elem = ET.SubElement(scene, key.replace("_", "-"))
        elem.text = str(value)

    # Characters
    characters = ET.SubElement(root, "Characters")
    for char in specs["characters"]:
        character = ET.SubElement(characters, "Character")
        for key, value in char.items():
            elem = ET.SubElement(character, key.replace("_", "-"))
            elem.text = str(value)

    # Dialogs
    if "dialogs" in specs and specs["dialogs"]:
        dialogs = ET.SubElement(root, "dialogs")
        for line_data in specs["dialogs"]:
            line = ET.SubElement(dialogs, "line")

            char_elem = ET.SubElement(line, "character")
            char_elem.text = str(line_data["character"])

            emotion_elem = ET.SubElement(line, "emotion")
            emotion_elem.text = str(line_data["emotion"])

            content_elem = ET.SubElement(line, "content")
            content_elem.text = str(line_data["content"])

    # Indentation
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", method="xml")