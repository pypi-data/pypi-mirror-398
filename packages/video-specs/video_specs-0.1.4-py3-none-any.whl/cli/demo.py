#!/usr/bin/env python3
"""
Script de démonstration pour le Video Specifications Tool
Ce script génère automatiquement un exemple complet dans les 3 formats
"""
import sys
from pathlib import Path

# Ajouter le répertoire courant au path
sys.path.insert(0, str(Path(__file__).parent))

from video_specs import VideoSpecs
from rich.console import Console
from rich.panel import Panel

console = Console()


def create_demo_video_specs():
    """Crée un exemple de spécifications vidéo"""
    video = VideoSpecs()

    # Technical
    video.specs["technical"] = {
        "aspect_ratio": "2.39:1",
        "resolution": "4K (3840×2160)",
        "duration": "00:03:45",
        "frame_rate": "24 fps"
    }

    # Setting & Atmosphere
    video.specs["setting_atmosphere"] = {
        "time_of_day": "golden hour",
        "season": "autumn",
        "weather": "partly cloudy",
        "location_type": "urban",
        "location_description": "Busy downtown street with modern architecture and autumn leaves",
        "lighting_style": "cinematic"
    }

    # Camera & Visuals
    video.specs["camera_visuals"] = {
        "shot_type": "wide shot",
        "camera_movement": "dolly",
        "focus": "deep focus",
        "lens_choice": "anamorphic",
        "color_palette": "warm earth tones"
    }

    # Scene Content
    video.specs["scene_content"] = {
        "crowd_density": "crowded",
        "subject_count": 1,
        "mood_tone": "melancholic",
        "action_description": "A lone figure walking through the busy street, lost in thought"
    }

    # Characters
    video.specs["characters"] = [
        {
            "name": "Alex Chen",
            "role": "protagonist",
            "age": "35",
            "costume": "Dark wool coat, burgundy scarf, leather boots",
            "physical_appearance": "Medium build, short black hair with grey streaks, contemplative expression"
        },
        {
            "name": "Street Musician",
            "role": "extra",
            "age": "50",
            "costume": "Worn denim jacket, vintage hat",
            "physical_appearance": "Weathered face, playing violin"
        }
    ]

    return video


def main():
    """Génère les exemples dans tous les formats"""
    console.print(Panel.fit(
        "[bold cyan]🎬 Video Specs Tool - DEMO[/bold cyan]\n"
        "[dim]Génération d'exemples dans tous les formats[/dim]",
        border_style="cyan"
    ))

    # Créer les spécifications
    console.print("\n[yellow]Création des spécifications d'exemple...[/yellow]")
    video = create_demo_video_specs()

    # Afficher le résumé
    video.display_summary()

    # Générer les fichiers
    console.print("\n[cyan]Génération des fichiers...[/cyan]")

    # JSON
    json_path = Path("demo_output.json")
    json_path.write_text(video.to_json(), encoding="utf-8")
    console.print(f"[green]✓[/green] JSON: {json_path}")

    # XML
    xml_path = Path("demo_output.xml")
    xml_path.write_text(video.to_xml(), encoding="utf-8")
    console.print(f"[green]✓[/green] XML: {xml_path}")

    # HTML
    html_path = Path("demo_output.html")
    html_path.write_text(video.to_html(), encoding="utf-8")
    console.print(f"[green]✓[/green] HTML: {html_path}")

    console.print("\n[bold green]✨ Fichiers de démonstration générés avec succès ![/bold green]")
    console.print(f"\n[yellow]Ouvrez[/yellow] [cyan]{html_path}[/cyan] [yellow]dans votre navigateur pour voir le rendu HTML[/yellow]")


if __name__ == "__main__":
    main()