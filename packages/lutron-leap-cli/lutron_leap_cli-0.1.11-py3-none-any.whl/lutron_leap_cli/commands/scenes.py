"""Scene management commands."""

import asyncio
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..core.config import load_config
from ..core.bridge import LutronBridge
from ..core.cache import HouseCache
from ..core.models import Scene, ZoneState, HSVColor
from ..core.scenes import (
    load_scene,
    save_scene,
    delete_scene,
    list_scenes,
)
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


def snapshot_cmd(
    name: str = typer.Argument(..., help="Name or path for the scene"),
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
        to a scene file in YAML format.

    PARAMETERS:
        name: Scene name or path (e.g., "evening", "./scenes/evening.yaml")
        --area: Only capture zones in matching area (partial match)
        --force: Overwrite if scene already exists

    EXAMPLES:
        lutron snapshot "evening"
        lutron snapshot "patio-party" --area patio
        lutron snapshot "./my-scenes/custom.yaml" --force

    OUTPUT (--json):
        {"success": true, "scene": "evening", "zones_captured": 15}
    """
    formatter = get_formatter()
    bridge_config = _get_bridge_config(bridge)

    # Check if scene exists
    existing = load_scene(name)
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

    # Extract scene name from path if needed
    from pathlib import Path

    scene_name = Path(name).stem if "/" in name or "\\" in name else name

    scene = Scene(
        name=scene_name,
        created_at=datetime.now(),
        zones=zone_states,
        area_filter=area,
    )
    saved_path = save_scene(scene, name)

    formatter.print_success(
        f"Saved scene '{scene_name}' ({len(zone_states)} zones)",
        {"scene": scene_name, "zones_captured": len(zone_states)},
    )
    console.print(f"[dim]Saved to: {saved_path}[/dim]")


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
    name: str = typer.Argument(..., help="Scene name or path to recall"),
    bridge: Optional[str] = typer.Option(
        None, "--bridge", "-b", help="Bridge name to use"
    ),
) -> None:
    """
    Recall a saved scene.

    DESCRIPTION:
        Restores all zones to the state saved in a scene.
        ColorTune/SpectrumTune zones restore both level and color.
        Supports YAML and JSON formats.

    EXAMPLES:
        lutron recall "evening"
        lutron recall "./my-scenes/party.yaml"
        lutron recall "/absolute/path/to/scene.yaml"

    OUTPUT (--json):
        {"success": true, "scene": "evening", "zones_restored": 15}
    """
    formatter = get_formatter()
    bridge_config = _get_bridge_config(bridge)

    scene = load_scene(name)
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
            f"Recalled scene '{scene.name}' ({success_count} zones)",
            {"scene": scene.name, "zones_restored": success_count},
        )
    else:
        formatter.print_warning(
            f"Restored {success_count}/{len(scene.zones)} zones from '{scene.name}'"
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
        Supports both YAML and JSON formats.

    EXAMPLES:
        lutron scenes
        lutron scenes --json

    OUTPUT (--json):
        [{"name": "evening", "created_at": "...", "zone_count": 15}]
    """
    formatter = get_formatter()
    scenes = list_scenes()

    if not scenes:
        formatter.print_warning(
            "No scenes saved. Use 'lutron snapshot <name>' to create one."
        )
        return

    table, data = scenes_table(scenes)
    formatter.print_table(table, data)


def scene_show_cmd(
    name: str = typer.Argument(..., help="Scene name or path"),
) -> None:
    """
    Show scene contents.

    DESCRIPTION:
        Displays the zones and their saved states in a scene.
        Supports YAML and JSON formats.

    EXAMPLES:
        lutron scene show "evening"
        lutron scene show "./my-scenes/party.yaml" --json

    OUTPUT (--json):
        {"name": "...", "zones": {"123": {"level": 50, "color": {...}}}}
    """
    formatter = get_formatter()

    scene = load_scene(name)
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
    name: str = typer.Argument(..., help="Scene name or path"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Delete without confirmation"
    ),
) -> None:
    """
    Delete a scene.

    DESCRIPTION:
        Removes a saved scene from disk.
        Supports YAML and JSON formats.

    EXAMPLES:
        lutron scene delete "old-scene"
        lutron scene delete "./my-scenes/party.yaml" --force

    OUTPUT (--json):
        {"success": true, "scene": "old-scene", "deleted": true}
    """
    formatter = get_formatter()

    scene = load_scene(name)
    if not scene:
        formatter.print_error(f"Scene not found: {name}")
        raise typer.Exit(1)

    if not force and not formatter.json_output:
        from rich.prompt import Confirm

        if not Confirm.ask(f"Delete scene '{scene.name}'?"):
            console.print("Cancelled")
            return

    deleted = delete_scene(name)
    if deleted:
        formatter.print_success(
            f"Deleted scene '{scene.name}'",
            {"scene": scene.name, "deleted": True},
        )
    else:
        formatter.print_error(f"Failed to delete scene: {name}")
