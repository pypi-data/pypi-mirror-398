"""
Format conversion utilities for video specifications
"""
import json
from pathlib import Path
from typing import Dict, Any, Union, List

from helpers.from_json import from_json
from helpers.from_xml import from_xml
from helpers.from_html import from_html
from helpers.from_text_blocks import from_text_blocks
from helpers.to_xml import to_xml
from helpers.to_html import to_html
from helpers.to_text_blocks import to_text_blocks


def detect_format(input_source: Union[str, Path]) -> str:
    """
    Detect the format of the input source.

    Args:
        input_source: File path or content string

    Returns:
        Format name: 'json', 'xml', 'html', or 'text-blocks'

    Raises:
        ValueError: If format cannot be detected
    """
    # Check if it's a file path
    if isinstance(input_source, (str, Path)):
        path = Path(input_source)
        if path.exists() and path.is_file():
            # Detect from extension
            ext = path.suffix.lower()
            if ext == '.json':
                return 'json'
            elif ext == '.xml':
                return 'xml'
            elif ext == '.html' or ext == '.htm':
                return 'html'
            elif ext == '.txt' or ext == '.md':
                return 'text-blocks'

            # Try to detect from content
            content = path.read_text(encoding='utf-8')
            return detect_format_from_content(content)

    # Detect from content string
    if isinstance(input_source, str):
        return detect_format_from_content(input_source)

    raise ValueError("Cannot detect format from input source")


def detect_format_from_content(content: str) -> str:
    """
    Detect format from content string.

    Args:
        content: Content string

    Returns:
        Format name: 'json', 'xml', 'html', or 'text-blocks'
    """
    content = content.strip()

    # Check JSON
    if content.startswith('{'):
        try:
            json.loads(content)
            return 'json'
        except json.JSONDecodeError:
            pass

    # Check XML
    if content.startswith('<?xml') or content.startswith('<VideoSpecifications'):
        return 'xml'

    # Check HTML
    if content.lower().startswith('<!doctype html') or '<html' in content.lower()[:100]:
        return 'html'

    # Check text-blocks (contains block markers)
    if '[SCENE & STYLE]' in content or '[SUBJECT & ENVIRONMENT]' in content:
        return 'text-blocks'

    raise ValueError("Cannot detect format from content. Supported formats: JSON, XML, HTML, text-blocks")


def parse_input(input_source: Union[str, Path], format: str = None) -> Dict[str, Any]:
    """
    Parse input source to specs dictionary.

    Args:
        input_source: File path or content string
        format: Format name (auto-detected if None)

    Returns:
        Video specifications dictionary

    Raises:
        ValueError: If parsing fails
    """
    # Read content if it's a file
    if isinstance(input_source, (str, Path)):
        path = Path(input_source)
        if path.exists() and path.is_file():
            content = path.read_text(encoding='utf-8')
        else:
            content = str(input_source)
    else:
        content = str(input_source)

    # Auto-detect format if not specified
    if format is None:
        format = detect_format(input_source)

    # Parse based on format
    if format == 'json':
        return from_json(content)
    elif format == 'xml':
        return from_xml(content)
    elif format == 'html':
        return from_html(content)
    elif format == 'text-blocks':
        return from_text_blocks(content)
    else:
        raise ValueError(f"Unsupported format: {format}")


def convert_format(input_source: Union[str, Path],
                   from_format: str = None,
                   to_format: str = 'json') -> str:
    """
    Convert input from one format to another.

    Args:
        input_source: File path or content string
        from_format: Source format (auto-detected if None)
        to_format: Target format

    Returns:
        Converted content as string

    Raises:
        ValueError: If conversion fails
    """
    # Parse input to specs dict
    specs = parse_input(input_source, from_format)

    # Convert to target format
    if to_format == 'json':
        return to_json(specs)
    elif to_format == 'xml':
        return to_xml(specs)
    elif to_format == 'html':
        return to_html(specs)
    elif to_format == 'text-blocks':
        return to_text_blocks(specs)
    else:
        raise ValueError(f"Unsupported target format: {to_format}")


def convert_to_all(input_source: Union[str, Path],
                   from_format: str = None,
                   base_filename: str = None) -> Dict[str, str]:
    """
    Convert input to all supported formats.

    Args:
        input_source: File path or content string
        from_format: Source format (auto-detected if None)
        base_filename: Base filename for output files (without extension)

    Returns:
        Dictionary mapping format to content
        Format: {'json': content, 'xml': content, 'html': content, 'text-blocks': content}

    Raises:
        ValueError: If conversion fails
    """
    # Parse input to specs dict
    specs = parse_input(input_source, from_format)

    # Convert to all formats
    results = {
        'json': to_json(specs),
        'xml': to_xml(specs),
        'html': to_html(specs),
        'text-blocks': to_text_blocks(specs)
    }

    return results


def save_converted_files(content_dict: Dict[str, str],
                         base_path: Union[str, Path],
                         output_dir: Union[str, Path] = None) -> List[Path]:
    """
    Save converted content to files.

    Args:
        content_dict: Dictionary mapping format to content
        base_path: Base file path (without extension) or full path to derive base name
        output_dir: Output directory (uses base_path directory if None)

    Returns:
        List of created file paths

    Raises:
        IOError: If file writing fails
    """
    base_path = Path(base_path)

    # Determine base name and output directory
    if base_path.suffix:
        # Has extension, remove it
        base_name = base_path.stem
        if output_dir is None:
            output_dir = base_path.parent
    else:
        base_name = base_path.name
        if output_dir is None:
            output_dir = base_path.parent if base_path.parent.name else Path.cwd()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extension mapping
    ext_map = {
        'json': '.json',
        'xml': '.xml',
        'html': '.html',
        'text-blocks': '.txt'
    }

    created_files = []
    for format_name, content in content_dict.items():
        ext = ext_map.get(format_name, '.txt')
        output_path = output_dir / f"{base_name}{ext}"

        output_path.write_text(content, encoding='utf-8')
        created_files.append(output_path)

    return created_files


def to_json(specs: Dict[str, Any]) -> str:
    """
    Convert specs dictionary to JSON string.
    Wrapper for compatibility.

    Args:
        specs: Video specifications dictionary

    Returns:
        JSON formatted string
    """
    return json.dumps(specs, indent=2, ensure_ascii=False)
