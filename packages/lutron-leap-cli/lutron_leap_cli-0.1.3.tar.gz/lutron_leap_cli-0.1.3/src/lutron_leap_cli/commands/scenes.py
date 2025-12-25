"""Scene management commands."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..core.config import load_config, get_scenes_dir
from ..core.bridge import LutronBridge
from ..core.cache import HouseCache
from ..core.models import Scene, ZoneState, HSVColor
from ..output.formatter import get_formatter
from ..output.tables import scenes_table

console = Console()


def _get_bridge_config(bridge_name: Optional[str] = None):
    """Get bridge configuration."""
    config = load_config()
    if bridge_name:
        bridge = config.get_bridge(bridge_name)
        if not bridge:
            raise typer.Exit(1)
        return bridge
    bridge = config.get_default_bridge()
    if not bridge:
        formatter = get_formatter()
        formatter.print_error("No bridge configured. Use 'lutron pair <IP>' first.")
        raise typer.Exit(1)
    return bridge


def _get_scene_path(name: str) -> Path:
    """Get path for a scene file."""
    scenes_dir = get_scenes_dir()
    return scenes_dir / f"{name}.json"


def _load_scene(name: str) -> Optional[Scene]:
    """Load a scene from disk."""
    path = _get_scene_path(name)
    if not path.exists():
        return None

    try:
        with open(path) as f:
            data = json.load(f)

        zones = {}
        for zone_id, state_data in data.get("zones", {}).items():
            color = None
            if state_data.get("color"):
                color = HSVColor(
                    hue=state_data["color"]["hue"],
                    saturation=state_data["color"]["saturation"],
                )
            zones[zone_id] = ZoneState(
                level=state_data["level"],
                color=color,
                vibrancy=state_data.get("vibrancy"),
            )

        return Scene(
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            zones=zones,
            area_filter=data.get("area_filter"),
        )
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def _save_scene(scene: Scene) -> None:
    """Save a scene to disk."""
    path = _get_scene_path(scene.name)

    data = {
        "name": scene.name,
        "created_at": scene.created_at.isoformat(),
        "area_filter": scene.area_filter,
        "zones": {},
    }

    for zone_id, state in scene.zones.items():
        state_data = {"level": state.level}
        if state.color:
            state_data["color"] = {
                "hue": state.color.hue,
                "saturation": state.color.saturation,
            }
        if state.vibrancy is not None:
            state_data["vibrancy"] = state.vibrancy
        data["zones"][zone_id] = state_data

    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _list_scenes() -> list[Scene]:
    """List all saved scenes."""
    scenes_dir = get_scenes_dir()
    scenes = []

    for path in scenes_dir.glob("*.json"):
        scene = _load_scene(path.stem)
        if scene:
            scenes.append(scene)

    return sorted(scenes, key=lambda s: s.name.lower())


def snapshot_cmd(
    name: str = typer.Argument(..., help="Name for the scene"),
    area: Optional[str] = typer.Option(
        None, "--area", "-a", help="Only capture zones in this area"
    ),
    bridge: Optional[str] = typer.Option(
        None, "--bridge", "-b", help="Bridge name to use"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing scene"),
) -> None:
    """
    Capture current state as a scene.

    DESCRIPTION:
        Saves the current state of all zones (or zones in a specific area)
        to a scene file. Scenes are saved in ./lutron-scenes/ directory.

    PARAMETERS:
        name: Scene name (used as filename)
        --area: Only capture zones in matching area (partial match)
        --force: Overwrite if scene already exists

    EXAMPLES:
        lutron snapshot "evening"
        lutron snapshot "patio-party" --area patio
        lutron snapshot "movie-mode" --force

    OUTPUT (--json):
        {"success": true, "scene": "evening", "zones_captured": 15}
    """
    formatter = get_formatter()
    bridge_config = _get_bridge_config(bridge)

    # Check if scene exists
    existing = _load_scene(name)
    if existing and not force:
        formatter.print_error(
            f"Scene '{name}' already exists. Use --force to overwrite."
        )
        raise typer.Exit(1)

    # Get house topology
    cache = HouseCache(bridge_config.name)
    house = cache.get()
    if house is None:
        formatter.print_info("Loading zones from bridge...")
        house = asyncio.run(_load_house(bridge_config))
        cache.save(house)

    # Filter zones by area if specified
    zones_to_capture = list(house.zones.values())
    if area:
        area_lower = area.lower()
        zones_to_capture = [z for z in zones_to_capture if area_lower in z.area.lower()]

    if not zones_to_capture:
        formatter.print_warning("No zones to capture")
        return

    formatter.print_info(f"Capturing state of {len(zones_to_capture)} zones...")

    # Get current state of each zone
    zone_states = asyncio.run(_capture_states(bridge_config, zones_to_capture))

    scene = Scene(
        name=name,
        created_at=datetime.now(),
        zones=zone_states,
        area_filter=area,
    )
    _save_scene(scene)

    formatter.print_success(
        f"Saved scene '{name}' ({len(zone_states)} zones)",
        {"scene": name, "zones_captured": len(zone_states)},
    )
    console.print(f"[dim]Saved to: {_get_scene_path(name)}[/dim]")


async def _load_house(bridge_config):
    """Load house topology from bridge."""
    async with LutronBridge(bridge_config) as bridge:
        return await bridge.load_house()


async def _capture_states(bridge_config, zones) -> dict[str, ZoneState]:
    """Capture current state of zones."""
    async with LutronBridge(bridge_config) as bridge:
        states = {}
        for zone in zones:
            status = await bridge.get_zone_status(zone.id)
            zone_status = status.get("ZoneStatus", {})

            level = zone_status.get("Level", 0)
            color = None
            vibrancy = None

            if "ColorTuningStatus" in zone_status:
                hsv = zone_status["ColorTuningStatus"].get("HSVTuningLevel", {})
                if hsv:
                    color = HSVColor(
                        hue=hsv.get("Hue", 0),
                        saturation=hsv.get("Saturation", 0),
                    )
                vibrancy = zone_status.get("Vibrancy")

            states[zone.id] = ZoneState(
                level=level,
                color=color,
                vibrancy=vibrancy,
            )

        return states


def recall_cmd(
    name: str = typer.Argument(..., help="Scene name to recall"),
    bridge: Optional[str] = typer.Option(
        None, "--bridge", "-b", help="Bridge name to use"
    ),
) -> None:
    """
    Recall a saved scene.

    DESCRIPTION:
        Restores all zones to the state saved in a scene.
        ColorTune/SpectrumTune zones restore both level and color.

    EXAMPLES:
        lutron recall "evening"
        lutron recall "patio-party"

    OUTPUT (--json):
        {"success": true, "scene": "evening", "zones_restored": 15}
    """
    formatter = get_formatter()
    bridge_config = _get_bridge_config(bridge)

    scene = _load_scene(name)
    if not scene:
        formatter.print_error(f"Scene not found: {name}")
        raise typer.Exit(1)

    # Get house topology for zone info
    cache = HouseCache(bridge_config.name)
    house = cache.get()
    if house is None:
        house = asyncio.run(_load_house(bridge_config))
        cache.save(house)

    formatter.print_info(f"Restoring {len(scene.zones)} zones...")

    success_count = asyncio.run(_restore_scene(bridge_config, scene, house))

    if success_count == len(scene.zones):
        formatter.print_success(
            f"Recalled scene '{name}' ({success_count} zones)",
            {"scene": name, "zones_restored": success_count},
        )
    else:
        formatter.print_warning(
            f"Restored {success_count}/{len(scene.zones)} zones from '{name}'"
        )


async def _restore_scene(bridge_config, scene: Scene, house) -> int:
    """Restore a scene."""
    async with LutronBridge(bridge_config) as bridge:
        success_count = 0

        for zone_id, state in scene.zones.items():
            zone = house.zones.get(zone_id)

            try:
                if state.color:
                    await bridge.set_color(
                        zone_id,
                        state.level,
                        state.color.hue,
                        state.color.saturation,
                        state.vibrancy or 50,
                    )
                else:
                    await bridge.set_level(zone_id, state.level, zone)
                success_count += 1
            except Exception:
                pass

        return success_count


def scenes_cmd() -> None:
    """
    List saved scenes.

    DESCRIPTION:
        Shows all scenes saved in the ./lutron-scenes/ directory.

    EXAMPLES:
        lutron scenes
        lutron scenes --json

    OUTPUT (--json):
        [{"name": "evening", "created_at": "...", "zone_count": 15}]
    """
    formatter = get_formatter()
    scenes = _list_scenes()

    if not scenes:
        formatter.print_warning(
            "No scenes saved. Use 'lutron snapshot <name>' to create one."
        )
        return

    table, data = scenes_table(scenes)
    formatter.print_table(table, data)


def scene_show_cmd(
    name: str = typer.Argument(..., help="Scene name"),
) -> None:
    """
    Show scene contents.

    DESCRIPTION:
        Displays the zones and their saved states in a scene.

    EXAMPLES:
        lutron scene show "evening"
        lutron scene show "evening" --json

    OUTPUT (--json):
        {"name": "...", "zones": {"123": {"level": 50, "color": {...}}}}
    """
    formatter = get_formatter()

    scene = _load_scene(name)
    if not scene:
        formatter.print_error(f"Scene not found: {name}")
        raise typer.Exit(1)

    if formatter.json_output:
        data = {
            "name": scene.name,
            "created_at": scene.created_at.isoformat(),
            "area_filter": scene.area_filter,
            "zones": {},
        }
        for zone_id, state in scene.zones.items():
            data["zones"][zone_id] = {
                "level": state.level,
                "color": {"hue": state.color.hue, "saturation": state.color.saturation}
                if state.color
                else None,
                "vibrancy": state.vibrancy,
            }
        formatter.print(data)
    else:
        table = Table(title=f"Scene: {scene.name}")
        table.add_column("Zone ID", style="dim")
        table.add_column("Level", style="cyan")
        table.add_column("Hue", style="yellow")
        table.add_column("Sat", style="yellow")
        table.add_column("Vibrancy", style="green")

        for zone_id, state in sorted(scene.zones.items()):
            table.add_row(
                zone_id,
                f"{state.level}%",
                str(state.color.hue) if state.color else "-",
                str(state.color.saturation) if state.color else "-",
                str(state.vibrancy) if state.vibrancy else "-",
            )

        console.print(table)
        console.print(
            f"\n[dim]Created: {scene.created_at.strftime('%Y-%m-%d %H:%M')}[/dim]"
        )
        if scene.area_filter:
            console.print(f"[dim]Area filter: {scene.area_filter}[/dim]")


def scene_delete_cmd(
    name: str = typer.Argument(..., help="Scene name"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Delete without confirmation"
    ),
) -> None:
    """
    Delete a scene.

    DESCRIPTION:
        Removes a saved scene from disk.

    EXAMPLES:
        lutron scene delete "old-scene"
        lutron scene delete "old-scene" --force

    OUTPUT (--json):
        {"success": true, "scene": "old-scene", "deleted": true}
    """
    formatter = get_formatter()

    scene = _load_scene(name)
    if not scene:
        formatter.print_error(f"Scene not found: {name}")
        raise typer.Exit(1)

    if not force and not formatter.json_output:
        from rich.prompt import Confirm

        if not Confirm.ask(f"Delete scene '{name}'?"):
            console.print("Cancelled")
            return

    path = _get_scene_path(name)
    path.unlink()

    formatter.print_success(
        f"Deleted scene '{name}'",
        {"scene": name, "deleted": True},
    )
