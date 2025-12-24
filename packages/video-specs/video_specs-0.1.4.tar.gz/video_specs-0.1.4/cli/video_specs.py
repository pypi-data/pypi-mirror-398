#!/usr/bin/env python3
"""
Video Specifications Tool - Interactive tool to capture the characteristics of a video
"""
import json

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import click
import rich_click as click
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box

from cli.const import LOGO
from cli.utils import banner, success_banner
from helpers.to_html import to_html
from helpers.to_xml import to_xml
from helpers.to_text_blocks import to_text_blocks
from helpers.converter import (
    convert_format,
    convert_to_all,
    save_converted_files,
    detect_format
)

# Configuration rich-click for a elegant help menu
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "magenta italic"
click.rich_click.ERRORS_SUGGESTION = "Try 'video-specs --help' for more information."
click.rich_click.STYLE_OPTION = "bold blue_violet"
click.rich_click.STYLE_SWITCH = "bold yellow3"

console = Console()


class VideoSpecs:
    """Class to manage the video specifications"""

    def __init__(self):
        self.specs = {
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

    def collect_technical_specs(self):
        """Collect the technical specifications"""
        console.clear()
        console.print(LOGO)
        console.input("Press Enter to continue...")
        banner("Technical Specifications")

        aspect_ratios = ["16:9", "9:16", "4:3", "1:1", "2.35:1", "2.39:1", "21:9", "18:9"]
        resolutions = ["4K (3840×2160)", "2K (2048×1080)", "1080p", "720p", "480p", "360p"]
        frame_rates = ["15", "24", "25", "30", "60", "120"]
        styles = ["cinematic", "documentary", "music video", "commercial", "trailer", "interview", "behind the scenes", "viral"]
        genres = ["action", "adventure", "comedy", "drama", "horror", "romance", "sci-fi", "thriller", "western"]

        # Aspect Ratio
        console.print("\n[yellow3]Ratios available:[/yellow3]", ", ".join(aspect_ratios))
        aspect_ratio = Prompt.ask(
            "Aspect Ratio",
            default="9:16"
        )

        # Resolution
        console.print("\n[yellow3]Resolutions available:[/yellow3]", ", ".join(resolutions))
        resolution = Prompt.ask(
            "Resolution",
            default="4K"
        )

        # Duration
        duration = Prompt.ask(
            "Duration (format HH:MM:SS)",
            default="00:00:15"
        )

        # Frame Rate
        console.print("\n[yellow3]Frame rates available:[/yellow3]", ", ".join(frame_rates))
        frame_rate = Prompt.ask(
            "Frame Rate (fps)",
            default="25"
        )

        # Style
        console.print("\n[yellow3]Styles available:[/yellow3]", ", ".join(styles))
        style = Prompt.ask("Style", default="documentary")

        # Genre
        console.print("\n[yellow3]Genres disponibles:[/yellow3]", ", ".join(genres))
        genre = Prompt.ask("Genre", default="comedy")

        self.specs["technical"] = {
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "duration": duration,
            "frame_rate": f"{frame_rate} fps",
            "style": style,
            "genre": genre
        }

    def collect_setting_atmosphere(self):
        """Collect the parameters of the setting and atmosphere"""
        banner("Setting & Atmosphere")
        times_of_day = ["morning", "afternoon", "evening", "night", "midnight", "dawn", "dusk", "golden hour"]
        seasons = ["spring", "summer", "autumn", "winter"]
        weathers = ["sunny", "cloudy", "rainy", "stormy", "snowy", "foggy", "overcast"]
        location_types = ["indoor", "outdoor", "urban", "rural", "nature", "studio", "mixed"]
        lighting_styles = ["natural", "dramatic", "soft", "hard", "low-key", "high-key", "neon", "cinematic"]

        console.print("\n[yellow3]Times of day:[/yellow3]", ", ".join(times_of_day))
        time_of_day = Prompt.ask("Time of Day", default="afternoon")

        console.print("\n[yellow3]Seasons:[/yellow3]", ", ".join(seasons))
        season = Prompt.ask("Season", default="summer")

        console.print("\n[yellow3]Weather:[/yellow3]", ", ".join(weathers))
        weather = Prompt.ask("Weather", default="sunny")

        console.print("\n[yellow3]Location types:[/yellow3]", ", ".join(location_types))
        location_type = Prompt.ask("Location Type", default="outdoor")

        location_description = Prompt.ask(
            "Location Description",
            default="A beautiful park with trees"
        )

        console.print("\n[yellow3]Lighting styles:[/yellow3]", ", ".join(lighting_styles))
        lighting_style = Prompt.ask("Lighting Style", default="natural")

        self.specs["setting_atmosphere"] = {
            "time_of_day": time_of_day,
            "season": season,
            "weather": weather,
            "location_type": location_type,
            "location_description": location_description,
            "lighting_style": lighting_style
        }

    def collect_camera_visuals(self):
        """Collect the parameters of the camera and visuals"""
        banner("Camera & Visuals")

        shot_types = ["close-up", "medium shot", "wide shot", "extreme close-up", "full shot", "over-the-shoulder", "POV", "establishing shot"]
        camera_movements = ["static", "pan", "tilt", "dolly", "tracking", "handheld", "crane", "steadicam", "drone"]
        focus_types = ["shallow depth of field", "deep focus", "rack focus", "soft focus", "selective focus"]
        lens_choices = ["wide-angle", "telephoto", "standard", "fisheye", "macro", "anamorphic"]
        color_palettes = ["warm", "cool", "monochrome", "vibrant", "desaturated", "pastel", "neon", "earth tones"]

        console.print("\n[yellow3]Shot types:[/yellow3]", ", ".join(shot_types[:5]), "...")
        shot_type = Prompt.ask("Shot Type", default="medium shot")

        console.print("\n[yellow3]Camera movements:[/yellow3]", ", ".join(camera_movements[:5]), "...")
        camera_movement = Prompt.ask("Camera Movement", default="static")

        console.print("\n[yellow3]Focus types:[/yellow3]", ", ".join(focus_types[:3]), "...")
        focus = Prompt.ask("Focus", default="shallow depth of field")

        console.print("\n[yellow3]Lens choices:[/yellow3]", ", ".join(lens_choices))
        lens_choice = Prompt.ask("Lens Choice", default="standard")

        console.print("\n[yellow3]Color palettes:[/yellow3]", ", ".join(color_palettes[:5]), "...")
        color_palette = Prompt.ask("Color Palette", default="neutral")

        self.specs["camera_visuals"] = {
            "shot_type": shot_type,
            "camera_movement": camera_movement,
            "focus": focus,
            "lens_choice": lens_choice,
            "color_palette": color_palette
        }

    def collect_scene_content(self):
        """Collect the content of the scene"""
        banner("Scene Content")

        crowd_densities = ["empty", "sparse", "moderate", "crowded", "packed"]
        moods = ["happy", "sad", "tense", "peaceful", "energetic", "melancholic", "mysterious", "dramatic", "romantic"]

        console.print("\n[yellow3]Crowd densities:[/yellow3]", ", ".join(crowd_densities))
        crowd_density = Prompt.ask("Crowd Density", default="moderate")

        subject_count = Prompt.ask("Subject Count", default="1")

        console.print("\n[yellow3]Moods/Tones:[/yellow3]", ", ".join(moods[:5]), "...")
        mood = Prompt.ask("Mood / Tone", default="peaceful")

        action_description = Prompt.ask(
            "Action Description",
            default="A person walking through the park"
        )

        self.specs["scene_content"] = {
            "crowd_density": crowd_density,
            "subject_count": int(subject_count),
            "mood_tone": mood,
            "action_description": action_description
        }

    def collect_characters(self):
        """Collect the information about the characters"""
        banner("Characters")

        roles = ["protagonist", "antagonist", "supporting", "extra", "narrator", "sidekick"]

        count = 1
        while count > 0:
            console.print(f"\n[cyan]Character #{len(self.specs['characters']) + 1}[/cyan]")

            name = Prompt.ask("Name", default=f"Character {len(self.specs['characters']) + 1}")

            console.print("\n[yellow3]Roles available:[/yellow3]", ", ".join(roles))
            role = Prompt.ask("Role", default="protagonist")

            age = Prompt.ask("Age", default="30")

            costume = Prompt.ask(
                "Costume",
                default="Casual clothes"
            )

            physical_appearance = Prompt.ask(
                "Physical Appearance",
                default="Average height, brown hair, blue eyes"
            )

            character = {
                "name": name,
                "role": role,
                "age": age,
                "costume": costume,
                "physical_appearance": physical_appearance
            }

            self.specs["characters"].append(character)

            # Ask if we want to add another character
            add_more = Confirm.ask(
                "\n[green]Add another character ?[/green]",
                default=False
            )

            if not add_more:
                count -= 1

    def collect_dialogs(self):
        """Collect the dialogs"""
        banner("Dialogs")

        if not self.specs["characters"]:
            console.print("[yellow]No characters defined. Impossible to add dialogs without characters.[/yellow]")
            return

        character_names = [c["name"] for c in self.specs["characters"]]
        
        # Ask if we want to add dialogs
        if not Confirm.ask("\n[green]Do you want to add dialogs ?[/green]", default=True):
            return

        while True:
            console.print(f"\n[cyan]Dialog line #{len(self.specs['dialogs']) + 1}[/cyan]")

            console.print("\n[yellow3]Characters available:[/yellow3]", ", ".join(character_names))
            character_id = Prompt.ask(
                "Character",
                choices=character_names
            )

            emotion = Prompt.ask("Emotion", default="neutral")
            
            content = Prompt.ask("Content")

            line = {
                "character": character_id,
                "emotion": emotion,
                "content": content
            }

            self.specs["dialogs"].append(line)

            if not Confirm.ask("\n[green]Add another line ?[/green]", default=True):
                break

    def to_json(self) -> str:
        """Export to JSON formatted"""
        return json.dumps(self.specs, indent=2, ensure_ascii=True)

    def to_xml(self) -> str:
        """Export to XML formatted"""
        return to_xml(self.specs)

    def to_html(self) -> str:
        """Export to HTML formatted"""
        return to_html(self.specs)

    def to_text_blocks(self) -> str:
        """Export to narrative text blocks"""
        return to_text_blocks(self.specs)

    def display_summary(self):
        """Display a summary of the collected specifications"""
        console.clear()
        success_banner("Collection completed!")
        console.input()
        console.clear()


        # Table of technical specifications
        table = Table(
            title="📹 Technical Specs", 
            box=box.SIMPLE, 
            show_header=False
        )
        table.add_column("Parameter", style="cyan")
        table.add_column("Value", style="white")
        for key, value in self.specs["technical"].items():
            table.add_row(key.replace("_", " ").title(), str(value))
        console.print(Align.center(table))

        # Table of characters
        if self.specs["characters"]:
            console.print()
            char_table = Table(title="👥 Characters", box=box.SIMPLE)
            char_table.add_column("Name", style="magenta")
            char_table.add_column("Role", style="yellow3")
            char_table.add_column("Age", style="cyan")
            for char in self.specs["characters"]:
                char_table.add_row(char["name"], char["role"], char["age"])
            console.print(Align.center(char_table))

        # Table of dialogs
        if self.specs["dialogs"]:
            console.print()
            dialog_table = Table(title="💬 Dialogs", box=box.SIMPLE)
            dialog_table.add_column("Character", style="magenta")
            dialog_table.add_column("Emotion", style="yellow3")
            dialog_table.add_column("Content", style="white")
            for line in self.specs["dialogs"]:
                dialog_table.add_row(line["character"], line["emotion"], line["content"])
            console.print(Align.center(dialog_table))


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """
    Video Specifications Tool

    Interactive tool to capture all the characteristics of a video.
    """
    # If no subcommand is provided, run the create command by default
    if ctx.invoked_subcommand is None:
        ctx.invoke(create)


@cli.command()
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="📁 Output file (extension: .json, .xml, .html, .txt)"
)
@click.option(
    "--format", "-f",
    type=click.Choice(["json", "xml", "html", "text-blocks"], case_sensitive=False),
    help="📋 Output format (detected automatically from the extension if not specified)"
)
@click.option(
    "--interactive/--no-interactive", "-i/-n",
    default=True,
    help="🖱️  Interactive mode (default) or non-interactive"
)
def create(output, format, interactive):
    """
    Video Specifications Tool

    Interactive tool to capture all the characteristics of a video.

    Examples of usage:

        Save in JSON:
        video-specs -o video.json

        Save in XML:
        video-specs -o specs.xml

        Save in HTML (with visualization):
        video-specs -o report.html
    """
    console.clear()
    console.print(LOGO)

    if not interactive:
        console.print("Non-interactive mode not yet implemented")
        return

    # Collect the data
    video = VideoSpecs()

    console_width = console.size.width    

    try:
        video.collect_technical_specs()
        video.collect_setting_atmosphere()
        video.collect_camera_visuals()
        video.collect_scene_content()
        video.collect_characters()
        video.collect_dialogs()

        # Display the summary
        video.display_summary()

        # Determine the output format
        if output:
            output_path = Path(output)
            if not format:
                # Detect from the extension
                ext = output_path.suffix.lower()
                if ext == ".json":
                    format = "json"
                elif ext == ".xml":
                    format = "xml"
                elif ext == ".html":
                    format = "html"
                else:
                    format = "text-blocks"  # Default
        else:
            # Ask for the format if no output file
            console.clear()
            format = Prompt.ask(
                "Output format",
                choices=["json", "xml", "html", "text-blocks"],
                default="text-blocks"
            )

        # Generate the output
        console.print(f"\n[cyan]Generating {format.upper()}...[/cyan]")

        if format == "json":
            output_data = video.to_json()
        elif format == "xml":
            output_data = video.to_xml()
        elif format == "html":
            output_data = video.to_html()
        elif format == "text-blocks":
            output_data = video.to_text_blocks()

        # Save or display
        saved_file_path = None
        if output:
            output_path.write_text(output_data, encoding="utf-8")
            console.print(f"\n[green]✓ File saved:[/green] {output_path}")
            saved_file_path = output_path
        else:
            console.print("\n" + "=" * console_width)
            console.print(output_data)
            console.print("=" * console_width)

            # Propose to save
            if Confirm.ask("\n[yellow3]Save in a file ?[/yellow3]", default=True):
                default_name = f"video_specs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
                filename = Prompt.ask("File name", default=default_name)
                saved_file_path = Path(filename)
                saved_file_path.write_text(output_data, encoding="utf-8")
                console.print(f"[green]✓ File saved:[/green] {filename}")

        # Offer format conversion
        if saved_file_path:
            console.print()
            if Confirm.ask("[cyan]Convert to other formats?[/cyan]", default=False):
                # Show conversion menu
                console.print("\n[bold]Available conversions:[/bold]")
                console.print("  1. XML")
                console.print("  2. HTML")
                console.print("  3. Text-blocks")
                console.print("  4. All formats")
                console.print("  5. Skip")

                choice = Prompt.ask(
                    "\nChoice",
                    choices=["1", "2", "3", "4", "5"],
                    default="5"
                )

                if choice != "5":
                    format_map = {
                        "1": ["xml"],
                        "2": ["html"],
                        "3": ["text-blocks"],
                        "4": ["json", "xml", "html", "text-blocks"]
                    }

                    # Remove current format from conversion list
                    target_formats = [f for f in format_map[choice] if f != format]

                    if target_formats:
                        console.print(f"\n[cyan]Converting to {', '.join(target_formats)}...[/cyan]")

                        try:
                            # Prepare specs dict for conversion
                            ext_map = {'json': '.json', 'xml': '.xml', 'html': '.html', 'text-blocks': '.txt'}

                            for target_format in target_formats:
                                # Convert using the video object's methods
                                if target_format == "json":
                                    converted_content = video.to_json()
                                elif target_format == "xml":
                                    converted_content = video.to_xml()
                                elif target_format == "html":
                                    converted_content = video.to_html()
                                elif target_format == "text-blocks":
                                    converted_content = video.to_text_blocks()

                                # Save converted file
                                target_ext = ext_map[target_format]
                                target_path = saved_file_path.parent / f"{saved_file_path.stem}{target_ext}"
                                target_path.write_text(converted_content, encoding="utf-8")
                                console.print(f"[green]✓ Saved:[/green] {target_path}")

                        except Exception as e:
                            console.print(f"[red]Conversion error:[/red] {e}")
                    else:
                        console.print("[yellow]No additional formats to convert (already in current format)[/yellow]")

    except KeyboardInterrupt:
        console.print("\n[yellow3]Cancelled by the user[/yellow3]")
        return


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option(
    "--to", "-t",
    "target_formats",
    multiple=True,
    type=click.Choice(["json", "xml", "html", "text-blocks", "all"], case_sensitive=False),
    help="🎯 Target format(s) for conversion. Use 'all' to convert to all formats. Can be specified multiple times."
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="📁 Output directory or file path (directory for 'all', file for single format)"
)
@click.option(
    "--from", "-f",
    "from_format",
    type=click.Choice(["json", "xml", "html", "text-blocks"], case_sensitive=False),
    help="📋 Source format (auto-detected if not specified)"
)
def convert(input_file, target_formats, output, from_format):
    """
    Convert video specifications between formats.

    INPUT_FILE: Path to the input file to convert

    Examples:

        Convert JSON to XML:
        video-specs convert specs.json --to xml

        Convert to multiple formats:
        video-specs convert specs.json --to xml --to html

        Convert to all formats:
        video-specs convert specs.json --to all

        Specify output location:
        video-specs convert specs.json --to all -o ./output
    """
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]Format Converter[/bold cyan]\n"
        "Convert video specifications between formats",
        border_style="cyan"
    ))

    input_path = Path(input_file)

    try:
        # Detect source format if not specified
        if from_format is None:
            from_format = detect_format(input_path)
            console.print(f"\n[dim]Detected source format: {from_format}[/dim]")

        # Handle no target format specified
        if not target_formats:
            console.print("\n[yellow]No target format specified. Please use --to option.[/yellow]")
            console.print("Example: video-specs convert input.json --to xml")
            return

        # Check if 'all' is in target formats
        if 'all' in target_formats:
            console.print(f"\n[cyan]Converting {input_path.name} to all formats...[/cyan]")

            # Convert to all formats
            results = convert_to_all(input_path, from_format)

            # Determine output directory
            if output:
                output_dir = Path(output)
                if output_dir.suffix:
                    # User provided a file path, use its directory
                    output_dir = output_dir.parent
            else:
                output_dir = input_path.parent

            # Save files
            base_name = input_path.stem
            created_files = save_converted_files(results, base_name, output_dir)

            # Display results
            console.print(f"\n[green]✓ Conversion completed![/green]")
            console.print("\n[bold]Created files:[/bold]")
            for file_path in created_files:
                console.print(f"  • {file_path}")

        else:
            # Convert to specific format(s)
            for target_format in target_formats:
                console.print(f"\n[cyan]Converting {input_path.name} from {from_format} to {target_format}...[/cyan]")

                # Convert
                output_content = convert_format(input_path, from_format, target_format)

                # Determine output path
                if output:
                    output_path = Path(output)
                    # If converting to multiple formats and output is a directory
                    if len(target_formats) > 1 and output_path.is_dir():
                        ext_map = {'json': '.json', 'xml': '.xml', 'html': '.html', 'text-blocks': '.txt'}
                        output_path = output_path / f"{input_path.stem}{ext_map[target_format]}"
                else:
                    # Auto-generate output path
                    ext_map = {'json': '.json', 'xml': '.xml', 'html': '.html', 'text-blocks': '.txt'}
                    output_path = input_path.parent / f"{input_path.stem}{ext_map[target_format]}"

                # Save file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(output_content, encoding='utf-8')

                console.print(f"[green]✓ Saved:[/green] {output_path}")

    except ValueError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        return
    except Exception as e:
        console.print(f"\n[red]Unexpected error:[/red] {e}")
        return


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()