"""
Parser text-blocks to video specs dictionary
"""
import re
from typing import Dict, Any
from datetime import datetime


def from_text_blocks(text_data: str) -> Dict[str, Any]:
    """
    Parse text-blocks string to video specifications dictionary.
    Uses pattern matching and heuristics for tolerant parsing.

    Args:
        text_data: Text-blocks formatted string

    Returns:
        Dictionary containing video specifications
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

    # Split into blocks
    blocks = {}
    block_pattern = r'\[([A-Z\s&]+)\]\s*(.*?)(?=\n\[|$)'
    for match in re.finditer(block_pattern, text_data, re.DOTALL):
        block_name = match.group(1).strip()
        block_content = match.group(2).strip()
        blocks[block_name] = block_content

    # Parse SCENE & STYLE block
    if "SCENE & STYLE" in blocks:
        content = blocks["SCENE & STYLE"]

        # Extract technical specs from "filmed in ..." pattern
        filmed_pattern = r'filmed in ([^.]+)'
        filmed_match = re.search(filmed_pattern, content, re.IGNORECASE)
        if filmed_match:
            tech_string = filmed_match.group(1)
            # Parse comma-separated technical specs
            parts = [p.strip() for p in tech_string.split(',')]
            for part in parts:
                # Detect aspect ratios (contains :)
                if ':' in part and re.match(r'^\d+:\d+', part):
                    specs["technical"]["aspect_ratio"] = part
                # Detect resolutions (contains K or p or x)
                elif re.search(r'\d+[KkPp]|\d+×\d+', part):
                    specs["technical"]["resolution"] = part
                # Detect frame rates (contains fps)
                elif 'fps' in part.lower():
                    specs["technical"]["frame_rate"] = part
                # Detect durations (HH:MM:SS format)
                elif re.match(r'\d{2}:\d{2}:\d{2}', part):
                    specs["technical"]["duration"] = part
                # Common styles
                elif part.lower() in ["cinematic", "documentary", "music video", "commercial", "trailer", "interview", "behind the scenes", "viral"]:
                    specs["technical"]["style"] = part.lower()
                # Common genres
                elif part.lower() in ["action", "adventure", "comedy", "drama", "horror", "romance", "sci-fi", "thriller", "western"]:
                    specs["technical"]["genre"] = part.lower()

        # Extract weather, season, time from beginning
        weather_pattern = r'\b(sunny|cloudy|rainy|stormy|snowy|foggy|overcast)\b'
        weather_match = re.search(weather_pattern, content, re.IGNORECASE)
        if weather_match:
            specs["setting_atmosphere"]["weather"] = weather_match.group(1).lower()

        season_pattern = r'\b(spring|summer|autumn|fall|winter)\b'
        season_match = re.search(season_pattern, content, re.IGNORECASE)
        if season_match:
            season = season_match.group(1).lower()
            if season == "fall":
                season = "autumn"
            specs["setting_atmosphere"]["season"] = season

        time_pattern = r'\b(morning|afternoon|evening|night|midnight|dawn|dusk|golden hour)\b'
        time_match = re.search(time_pattern, content, re.IGNORECASE)
        if time_match:
            specs["setting_atmosphere"]["time_of_day"] = time_match.group(1).lower()

        # Extract location
        location_pattern = r'(?:inside|in|at|on)\s+([^,]+)'
        location_match = re.search(location_pattern, content, re.IGNORECASE)
        if location_match:
            location_desc = location_match.group(1).strip()
            specs["setting_atmosphere"]["location_description"] = location_desc
            # Detect location type
            if re.search(r'\b(indoor|inside|room|apartment|house|building)\b', location_desc, re.IGNORECASE):
                specs["setting_atmosphere"]["location_type"] = "indoor"
            elif re.search(r'\b(outdoor|outside|park|street|city|urban)\b', location_desc, re.IGNORECASE):
                specs["setting_atmosphere"]["location_type"] = "outdoor"

        # Extract color palette and lighting
        color_pattern = r'(?:a|with)\s+(warm|cool|monochrome|vibrant|desaturated|pastel|neon|earth tones?|neutral)\s+color palette'
        color_match = re.search(color_pattern, content, re.IGNORECASE)
        if color_match:
            specs["camera_visuals"]["color_palette"] = color_match.group(1).lower()

        lighting_pattern = r'(natural|dramatic|soft|hard|low-key|high-key|neon|cinematic)-looking light'
        lighting_match = re.search(lighting_pattern, content, re.IGNORECASE)
        if lighting_match:
            specs["setting_atmosphere"]["lighting_style"] = lighting_match.group(1).lower()

    # Parse SUBJECT & ENVIRONMENT block
    if "SUBJECT & ENVIRONMENT" in blocks:
        content = blocks["SUBJECT & ENVIRONMENT"]

        # Extract subject count
        count_pattern = r'(One|Two|Three|Four|Five|\d+)\s+main\s+characters?'
        count_match = re.search(count_pattern, content, re.IGNORECASE)
        if count_match:
            count_str = count_match.group(1)
            count_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
            count = count_map.get(count_str.lower(), count_str)
            try:
                specs["scene_content"]["subject_count"] = int(count)
            except (ValueError, TypeError):
                specs["scene_content"]["subject_count"] = 1

        # Extract crowd density
        crowd_pattern = r'(?:a|in)\s+(empty|sparse|moderate|crowded|packed)ly\s+crowded'
        crowd_match = re.search(crowd_pattern, content, re.IGNORECASE)
        if crowd_match:
            specs["scene_content"]["crowd_density"] = crowd_match.group(1).lower()

        # Parse characters (simple heuristic: lines with name, age, description)
        # Pattern: "Name, age, physical description, costume"
        char_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*(\d+),\s*([^,]+),\s*(?:en\s+)?(.+?)(?:\.|$)'
        for match in re.finditer(char_pattern, content):
            character = {
                "name": match.group(1).strip(),
                "age": match.group(2).strip(),
                "physical_appearance": match.group(3).strip(),
                "costume": match.group(4).strip(),
                "role": "protagonist"  # Default
            }
            specs["characters"].append(character)

    # Parse CINEMATOGRAPHY & MOOD block
    if "CINEMATOGRAPHY & MOOD" in blocks:
        content = blocks["CINEMATOGRAPHY & MOOD"]

        # Extract shot type
        shot_pattern = r'\b(close-up|medium shot|wide shot|extreme close-up|full shot|over-the-shoulder|POV|establishing shot)\b'
        shot_match = re.search(shot_pattern, content, re.IGNORECASE)
        if shot_match:
            specs["camera_visuals"]["shot_type"] = shot_match.group(1).lower()

        # Extract camera movement
        movement_pattern = r'with a (static|pan|tilt|dolly|tracking|handheld|crane|steadicam|drone) camera'
        movement_match = re.search(movement_pattern, content, re.IGNORECASE)
        if movement_match:
            specs["camera_visuals"]["camera_movement"] = movement_match.group(1).lower()

        # Extract focus
        focus_pattern = r'\b(shallow depth of field|deep focus|rack focus|soft focus|selective focus)\b'
        focus_match = re.search(focus_pattern, content, re.IGNORECASE)
        if focus_match:
            specs["camera_visuals"]["focus"] = focus_match.group(1).lower()

        # Extract lens
        lens_pattern = r'a (wide-angle|telephoto|standard|fisheye|macro|anamorphic) lens'
        lens_match = re.search(lens_pattern, content, re.IGNORECASE)
        if lens_match:
            specs["camera_visuals"]["lens_choice"] = lens_match.group(1).lower()

        # Extract mood
        mood_pattern = r'mood.*?(happy|sad|tense|peaceful|energetic|melancholic|mysterious|dramatic|romantic|playful)'
        mood_match = re.search(mood_pattern, content, re.IGNORECASE)
        if mood_match:
            specs["scene_content"]["mood_tone"] = mood_match.group(1).lower()

        # Extract action description (the mood line often contains action context)
        if "mood" in content.lower():
            # Try to extract action description from context
            action_pattern = r'The mood.*?as (.+?)(?:\.|$)'
            action_match = re.search(action_pattern, content, re.IGNORECASE)
            if action_match:
                specs["scene_content"]["action_description"] = action_match.group(1).strip()

    # Parse DIALOGUE & PERFORMANCE block
    if "DIALOGUE & PERFORMANCE" in blocks:
        content = blocks["DIALOGUE & PERFORMANCE"]

        # Parse dialog lines
        # Pattern: Character, emotion: "content"
        dialog_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),?\s*(?:,\s*)?([^:]+)?:\s*["""](.*?)["""]'
        for match in re.finditer(dialog_pattern, content):
            character = match.group(1).strip()
            emotion = match.group(2).strip() if match.group(2) else "neutral"
            dialog_content = match.group(3).strip()

            dialog = {
                "character": character,
                "emotion": emotion,
                "content": dialog_content
            }
            specs["dialogs"].append(dialog)

    return specs
