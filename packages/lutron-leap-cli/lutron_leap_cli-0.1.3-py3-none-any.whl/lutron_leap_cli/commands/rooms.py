"""Room control commands."""

import asyncio
from typing import Optional

import typer
from rich.console import Console

from ..core.config import load_config
from ..core.bridge import LutronBridge
from ..core.cache import HouseCache
from ..core.models import Area
from ..output.formatter import get_formatter
from ..output.tables import areas_table

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


def _find_area(query: str, areas: dict[str, Area]) -> Optional[Area]:
    """Find an area by name (partial match)."""
    query_lower = query.lower()

    # Exact name match (case-insensitive)
    for area in areas.values():
        if area.name.lower() == query_lower:
            return area

    # Partial name match
    matches = []
    for area in areas.values():
        if query_lower in area.name.lower():
            matches.append(area)

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        formatter = get_formatter()
        formatter.print_warning(f"Multiple rooms match '{query}':")
        for a in matches[:5]:
            console.print(f"  - {a.name} ({len(a.zone_ids)} zones)")
        return None

    return None


def room_cmd(
    room_query: str = typer.Argument(..., help="Room name (partial match)"),
    level: Optional[int] = typer.Option(
        None, "--level", "-l", min=0, max=100, help="Set all zones to level 0-100"
    ),
    on: bool = typer.Option(False, "--on", help="Turn all zones on (100%)"),
    off: bool = typer.Option(False, "--off", help="Turn all zones off (0%)"),
    bridge: Optional[str] = typer.Option(
        None, "--bridge", "-b", help="Bridge name to use"
    ),
) -> None:
    """
    Control all zones in a room.

    DESCRIPTION:
        Sets all zones in a room to the same level. Useful for controlling
        multiple lights at once.

    PARAMETERS:
        room: Room/area name (partial match)
        --level: Set all zones to this brightness (0-100)
        --on: Turn all zones on (equivalent to --level 100)
        --off: Turn all zones off (equivalent to --level 0)

    EXAMPLES:
        lutron room kitchen --level 50
        lutron room "Living Room" --on
        lutron room patio --off

    OUTPUT (--json):
        {"success": true, "room": "Kitchen", "level": 50, "zones_updated": 3}
    """
    formatter = get_formatter()
    bridge_config = _get_bridge_config(bridge)

    # Validate options
    if on and off:
        formatter.print_error("Cannot use both --on and --off")
        raise typer.Exit(1)

    if level is None and not on and not off:
        formatter.print_error("Specify --level, --on, or --off")
        raise typer.Exit(1)

    if on:
        level = 100
    elif off:
        level = 0

    # Get house topology
    cache = HouseCache(bridge_config.name)
    house = cache.get()
    if house is None:
        formatter.print_info("Loading zones from bridge...")
        house = asyncio.run(_load_house(bridge_config))
        cache.save(house)

    # Find room
    area = _find_area(room_query, house.areas)
    if not area:
        formatter.print_error(f"Room not found: {room_query}")
        raise typer.Exit(1)

    if not area.zone_ids:
        formatter.print_warning(f"No zones in room '{area.name}'")
        return

    # Set all zones
    results = asyncio.run(_set_room_level(bridge_config, area, level, house))

    success_count = sum(1 for r in results if r.get("result"))
    total_count = len(results)

    if success_count == total_count:
        action = "ON" if level == 100 else "OFF" if level == 0 else f"@ {level}%"
        formatter.print_success(
            f"{area.name} {action} ({success_count} zones)",
            {"room": area.name, "level": level, "zones_updated": success_count},
        )
    else:
        formatter.print_warning(
            f"Updated {success_count}/{total_count} zones in {area.name}"
        )


async def _load_house(bridge_config):
    """Load house topology from bridge."""
    async with LutronBridge(bridge_config) as bridge:
        return await bridge.load_house()


async def _set_room_level(bridge_config, area: Area, level: int, house) -> list[dict]:
    """Set all zones in a room to a level."""
    async with LutronBridge(bridge_config) as bridge:
        return await bridge.set_room_level(area, level, house)


def rooms_cmd(
    bridge: Optional[str] = typer.Option(
        None, "--bridge", "-b", help="Bridge name to use"
    ),
    refresh: bool = typer.Option(False, "--refresh", help="Refresh cache from bridge"),
) -> None:
    """
    List all rooms/areas.

    DESCRIPTION:
        Lists all areas and rooms in the house with their zone counts.

    EXAMPLES:
        lutron rooms
        lutron rooms --json

    OUTPUT (--json):
        [{"id": "123", "name": "Kitchen", "is_room": true, "zone_count": 3}]
    """
    formatter = get_formatter()
    bridge_config = _get_bridge_config(bridge)

    # Get house topology
    cache = HouseCache(bridge_config.name)

    if refresh:
        cache.invalidate()

    house = cache.get()
    if house is None:
        formatter.print_info("Loading from bridge...")
        house = asyncio.run(_load_house(bridge_config))
        cache.save(house)

    # Filter to rooms only (is_room=True)
    rooms = [a for a in house.areas.values() if a.is_room]
    rooms.sort(key=lambda a: a.name.lower())

    if not rooms:
        formatter.print_warning("No rooms found")
        return

    table, data = areas_table(rooms, title=f"Rooms ({len(rooms)})")
    formatter.print_table(table, data)
