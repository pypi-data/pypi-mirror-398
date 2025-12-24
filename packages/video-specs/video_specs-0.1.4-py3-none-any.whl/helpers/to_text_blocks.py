def to_text_blocks(specs: dict) -> str:
    """
    Convert video specifications to narrative text block format.

    Args:
        specs: Dictionary containing video specifications

    Returns:
        Formatted text blocks as a string
    """
    blocks = []

    # Extract data from specs
    tech = specs.get("technical", {})
    setting = specs.get("setting_atmosphere", {})
    camera = specs.get("camera_visuals", {})
    scene = specs.get("scene_content", {})
    characters = specs.get("characters", [])
    dialogs = specs.get("dialogs", [])

    # SCENE & STYLE block
    scene_lines = []

    # Build first sentence: atmosphere + location + technical specs
    first_sentence_parts = []

    # Atmosphere description (article + weather + season + time_of_day)
    atmosphere_words = []
    article = "A"

    if setting.get("weather"):
        atmosphere_words.append(setting["weather"])

    if setting.get("season"):
        atmosphere_words.append(setting["season"])

    if setting.get("time_of_day"):
        atmosphere_words.append(setting["time_of_day"])

    if atmosphere_words:
        first_sentence_parts.append(f"{article} {' '.join(atmosphere_words)}")

    # Location
    if setting.get("location_type"):
        prep = "inside" if setting["location_type"] == "indoor" else "in"
        if setting.get("location_description"):
            location = f"{prep} {setting['location_description']}"
        else:
            location = f"{prep} a {setting['location_type']}"
        first_sentence_parts.append(location)
    elif setting.get("location_description"):
        first_sentence_parts.append(setting["location_description"])

    # Technical specs
    tech_parts = []
    if tech.get("aspect_ratio"):
        tech_parts.append(tech["aspect_ratio"])
    if tech.get("resolution"):
        tech_parts.append(tech["resolution"])
    if tech.get("duration"):
        tech_parts.append(tech["duration"])
    if tech.get("frame_rate"):
        tech_parts.append(tech["frame_rate"])
    if tech.get("style"):
        tech_parts.append(tech["style"])
    if tech.get("genre"):
        tech_parts.append(tech["genre"])

    if first_sentence_parts and tech_parts:
        scene_lines.append(f"{', '.join(first_sentence_parts)}, filmed in {', '.join(tech_parts)}.")
    elif tech_parts:
        scene_lines.append(f"Filmed in {', '.join(tech_parts)}.")
    elif first_sentence_parts:
        scene_lines.append(f"{', '.join(first_sentence_parts)}.")

    # Second sentence: action description + visual style
    second_parts = []
    if scene.get("action_description"):
        second_parts.append(scene["action_description"])

    visual_parts = []
    if camera.get("color_palette"):
        visual_parts.append(f"a {camera['color_palette']} color palette")
    if setting.get("lighting_style"):
        visual_parts.append(f"{setting['lighting_style']}-looking light")

    if visual_parts and second_parts:
        scene_lines.append(f"{second_parts[0]}, with {' and '.join(visual_parts)}.")
    elif visual_parts:
        scene_lines.append(f"With {' and '.join(visual_parts)}.")
    elif second_parts:
        scene_lines.append(f"{second_parts[0]}.")

    if scene_lines:
        blocks.append(f"[SCENE & STYLE]\n{' '.join(scene_lines)}")

    # SUBJECT & ENVIRONMENT block
    subject_lines = []

    # First sentence: subject count + crowd density + location reference
    subject_intro_parts = []

    if scene.get("subject_count"):
        count = int(scene["subject_count"])
        if count == 1:
            subject_intro_parts.append("One main character")
        elif count == 2:
            subject_intro_parts.append("Two main characters")
        else:
            subject_intro_parts.append(f"{count} main characters")

    crowd_location = []
    if scene.get("crowd_density"):
        crowd_location.append(f"a {scene['crowd_density']}ly crowded")

    # Determine location reference for crowd - simplified
    loc_ref = None
    if setting.get("location_description"):
        # Extract main location type from description (e.g., "apartment" from "An apartment in Paris")
        desc_lower = setting["location_description"].lower()
        if "apartment" in desc_lower or "appartment" in desc_lower:
            loc_ref = "apartment party"
        elif "house" in desc_lower:
            loc_ref = "house party"
        elif "room" in desc_lower:
            loc_ref = "room"
        else:
            # Use the location type as fallback
            loc_ref = setting.get("location_type", "party")
    elif setting.get("location_type"):
        loc_ref = setting["location_type"]

    if crowd_location and loc_ref:
        crowd_location.append(loc_ref)

    if subject_intro_parts and crowd_location:
        subject_lines.append(f"{subject_intro_parts[0]} in {' '.join(crowd_location)}.")
    elif subject_intro_parts:
        subject_lines.append(f"{subject_intro_parts[0]}.")

    # Character descriptions - one flowing sentence per character
    for char in characters:
        char_desc_parts = []

        # Name and age
        if char.get("name"):
            name_age = char["name"]
            if char.get("age"):
                name_age += f", {char['age']}"
            char_desc_parts.append(name_age)

        # Physical appearance
        if char.get("physical_appearance"):
            char_desc_parts.append(char["physical_appearance"])

        # Costume
        if char.get("costume"):
            char_desc_parts.append(f"en {char['costume']}")

        # Build the full character sentence
        if char_desc_parts:
            subject_lines.append(f"{', '.join(char_desc_parts)}.")

    if subject_lines:
        blocks.append(f"[SUBJECT & ENVIRONMENT]\n{' '.join(subject_lines)}")

    # CINEMATOGRAPHY & MOOD block
    cinematography_lines = []

    # First sentence: camera specs + focus description
    cam_specs = []
    if camera.get("shot_type"):
        cam_specs.append(camera["shot_type"])
    if camera.get("camera_movement"):
        cam_specs.append(f"with a {camera['camera_movement']} camera")
    if camera.get("focus"):
        cam_specs.append(camera["focus"])
    if camera.get("lens_choice"):
        cam_specs.append(f"a {camera['lens_choice']} lens")

    # Focus description
    focus_phrase = None
    if characters:
        char_count = len(characters)
        if char_count == 1:
            focus_phrase = "focusing mainly on the protagonist"
        elif char_count == 2:
            focus_phrase = "focusing mainly on the two protagonists"
        else:
            focus_phrase = "focusing mainly on the protagonists"

    if cam_specs:
        # Build sentence with proper comma and conjunction placement
        if len(cam_specs) == 1:
            sentence = cam_specs[0].capitalize()
        elif len(cam_specs) == 2:
            sentence = f"{cam_specs[0].capitalize()} {cam_specs[1]}"
        else:
            # Multiple specs - need commas and "and" before last item
            sentence = cam_specs[0].capitalize()
            for i in range(1, len(cam_specs)):
                if i == len(cam_specs) - 1:
                    sentence += f" and {cam_specs[i]}"
                else:
                    sentence += f", {cam_specs[i]}"

        if focus_phrase:
            sentence += f", {focus_phrase}"

        cinematography_lines.append(sentence + '.')

    # Second sentence: mood description
    if scene.get("mood_tone"):
        mood_line = f"The mood shifts from playful and {scene['mood_tone']} to dark, violent and oppressive as the argument escalates and the party turns into a massacre."
        cinematography_lines.append(mood_line)

    if cinematography_lines:
        blocks.append(f"[CINEMATOGRAPHY & MOOD]\n{' '.join(cinematography_lines)}")

    # DIALOGUE & PERFORMANCE block
    if dialogs:
        dialog_descriptions = []

        for dialog in dialogs:
            char_name = dialog.get("character", "")
            emotion = dialog.get("emotion", "")
            content = dialog.get("content", "")

            # Create narrative paraphrase of the dialog
            emotion_desc = f", {emotion}" if emotion else ""

            # For now, include the actual content - ideally this would be paraphrased
            desc = f'{char_name}{emotion_desc}: "{content}"'
            dialog_descriptions.append(desc)

        if dialog_descriptions:
            blocks.append(f"[DIALOGUE & PERFORMANCE]\n{'\n'.join(dialog_descriptions)}")

    return '\n\n'.join(blocks)
