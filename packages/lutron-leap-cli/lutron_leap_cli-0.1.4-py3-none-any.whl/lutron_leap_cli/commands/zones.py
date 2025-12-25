"""Zone control commands."""

import asyncio
from typing import Optional

import typer
from rich.console import Console

from ..core.config import load_config
from ..core.bridge import LutronBridge
from ..core.cache import HouseCache
from ..core.models import Zone, ZoneStatus, HSVColor, ControlType
from ..output.formatter import get_formatter
from ..output.tables import zones_table, zone_status_table

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


def _find_zone(query: str, zones: dict[str, Zone]) -> Optional[Zone]:
    """Find a zone by ID or name (partial match)."""
    # Exact ID match
    if query in zones:
        return zones[query]

    # Exact name match (case-insensitive)
    query_lower = query.lower()
    for zone in zones.values():
        if zone.name.lower() == query_lower:
            return zone

    # Partial name match
    matches = []
    for zone in zones.values():
        if query_lower in zone.name.lower():
            matches.append(zone)

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        formatter = get_formatter()
        formatter.print_warning(f"Multiple zones match '{query}':")
        for z in matches[:5]:
            console.print(f"  - {z.name} (ID: {z.id})")
        return None

    return None


def list_cmd(
    rooms: bool = typer.Option(False, "--rooms", "-r", help="Group zones by room"),
    area: Optional[str] = typer.Option(
        None, "--area", "-a", help="Filter by area name"
    ),
    zone_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="Filter by control type"
    ),
    bridge: Optional[str] = typer.Option(
        None, "--bridge", "-b", help="Bridge name to use"
    ),
    refresh: bool = typer.Option(False, "--refresh", help="Refresh cache from bridge"),
) -> None:
    """
    List all zones.

    DESCRIPTION:
        Lists all controllable zones (lights, fans, shades, etc.) from the bridge.
        Results are cached for 24 hours; use --refresh to update.

    PARAMETERS:
        --rooms: Group output by room/area
        --area: Filter to zones in a specific area (partial match)
        --type: Filter by control type (Dimmed, Switched, ColorTune, etc.)

    EXAMPLES:
        lutron list
        lutron list --rooms
        lutron list --area kitchen
        lutron list --type ColorTune
        lutron list --refresh

    OUTPUT (--json):
        [{"id": "123", "name": "Kitchen Light", "area": "Kitchen", ...}]
    """
    formatter = get_formatter()
    bridge_config = _get_bridge_config(bridge)

    # Get house topology
    cache = HouseCache(bridge_config.name)

    if refresh:
        cache.invalidate()

    house = cache.get()
    if house is None:
        formatter.print_info("Loading zones from bridge...")
        house = asyncio.run(_load_house(bridge_config))
        cache.save(house)

    # Filter zones
    zones_list = list(house.zones.values())

    if area:
        area_lower = area.lower()
        zones_list = [z for z in zones_list if area_lower in z.area.lower()]

    if zone_type:
        try:
            ct = ControlType(zone_type)
            zones_list = [z for z in zones_list if z.control_type == ct]
        except ValueError:
            formatter.print_warning(f"Unknown control type: {zone_type}")
            formatter.print_info(
                f"Valid types: {', '.join(t.value for t in ControlType)}"
            )

    if not zones_list:
        formatter.print_warning("No zones found matching criteria")
        return

    # Sort by area then name
    zones_list.sort(key=lambda z: (z.area.lower(), z.name.lower()))

    if rooms:
        # Group by area
        by_area: dict[str, list[Zone]] = {}
        for zone in zones_list:
            by_area.setdefault(zone.area, []).append(zone)

        all_data = []
        for area_name, area_zones in sorted(by_area.items()):
            table, data = zones_table(area_zones, title=area_name, show_area=False)
            if not formatter.json_output:
                formatter.print(table)
                console.print()
            all_data.extend(data)

        if formatter.json_output:
            formatter.print_table(None, all_data)
    else:
        table, data = zones_table(zones_list, title=f"Zones ({len(zones_list)})")
        formatter.print_table(table, data)


async def _load_house(bridge_config):
    """Load house topology from bridge."""
    async with LutronBridge(bridge_config) as bridge:
        return await bridge.load_house()


def status_cmd(
    zone_query: str = typer.Argument(..., help="Zone name or ID"),
    bridge: Optional[str] = typer.Option(
        None, "--bridge", "-b", help="Bridge name to use"
    ),
) -> None:
    """
    Get zone status.

    DESCRIPTION:
        Shows current level, color (if applicable), and availability for a zone.

    PARAMETERS:
        zone: Zone name (partial match) or ID

    EXAMPLES:
        lutron status "Kitchen Light"
        lutron status dome
        lutron status 123

    OUTPUT (--json):
        {"zone": {...}, "status": {"level": 50, "color": {"hue": 0, "saturation": 0}}}
    """
    formatter = get_formatter()
    bridge_config = _get_bridge_config(bridge)

    # Get zone from cache
    cache = HouseCache(bridge_config.name)
    house = cache.get()
    if house is None:
        house = asyncio.run(_load_house(bridge_config))
        cache.save(house)

    zone = _find_zone(zone_query, house.zones)
    if not zone:
        formatter.print_error(f"Zone not found: {zone_query}")
        raise typer.Exit(1)

    # Get live status
    status_data = asyncio.run(_get_zone_status(bridge_config, zone.id))

    zone_status = status_data.get("ZoneStatus", {})
    level = zone_status.get("Level", 0)

    color = None
    if "ColorTuningStatus" in zone_status:
        hsv = zone_status["ColorTuningStatus"].get("HSVTuningLevel", {})
        if hsv:
            color = HSVColor(
                hue=hsv.get("Hue", 0),
                saturation=hsv.get("Saturation", 0),
            )

    vibrancy = zone_status.get("Vibrancy")
    availability = zone_status.get("Availability", "Available")

    status = ZoneStatus(
        level=level,
        color=color,
        vibrancy=vibrancy,
        availability=availability,
    )

    table, data = zone_status_table(zone, status)
    formatter.print_table(table, [data])


async def _get_zone_status(bridge_config, zone_id: str) -> dict:
    """Get zone status from bridge."""
    async with LutronBridge(bridge_config) as bridge:
        return await bridge.get_zone_status(zone_id)


def set_cmd(
    zone_query: str = typer.Argument(..., help="Zone name or ID"),
    level: Optional[int] = typer.Option(
        None, "--level", "-l", min=0, max=100, help="Brightness 0-100"
    ),
    hue: Optional[int] = typer.Option(
        None, "--hue", "-H", min=0, max=360, help="Color hue 0-360"
    ),
    saturation: Optional[int] = typer.Option(
        None, "--sat", "-s", min=0, max=100, help="Saturation 0-100"
    ),
    vibrancy: Optional[int] = typer.Option(
        None, "--vibrancy", "-v", min=0, max=100, help="Vibrancy 0-100"
    ),
    bridge: Optional[str] = typer.Option(
        None, "--bridge", "-b", help="Bridge name to use"
    ),
) -> None:
    """
    Set zone level and/or color.

    DESCRIPTION:
        Sets brightness and optional color for a zone. Color options only work
        with ColorTune or SpectrumTune zones.

    PARAMETERS:
        zone: Zone name (partial match) or ID
        --level: Brightness level 0-100
        --hue: Color hue 0-360 (color zones only)
        --sat: Saturation 0-100 (color zones only)
        --vibrancy: Vibrancy 0-100 (SpectrumTune zones only)

    EXAMPLES:
        lutron set "Kitchen Light" --level 50
        lutron set dome --level 100 --hue 30 --sat 70
        lutron set pool --level 80 --hue 200 --sat 50 --vibrancy 60

    OUTPUT (--json):
        {"success": true, "zone": "Kitchen Light", "level": 50}
    """
    formatter = get_formatter()
    bridge_config = _get_bridge_config(bridge)

    if level is None and hue is None and saturation is None:
        formatter.print_error("At least one of --level, --hue, or --sat required")
        raise typer.Exit(1)

    # Get zone from cache
    cache = HouseCache(bridge_config.name)
    house = cache.get()
    if house is None:
        house = asyncio.run(_load_house(bridge_config))
        cache.save(house)

    zone = _find_zone(zone_query, house.zones)
    if not zone:
        formatter.print_error(f"Zone not found: {zone_query}")
        raise typer.Exit(1)

    # Check color support
    if (hue is not None or saturation is not None) and not zone.supports_color:
        formatter.print_warning(
            f"Zone '{zone.name}' doesn't support color (type: {zone.control_type.value})"
        )

    result = asyncio.run(
        _set_zone(bridge_config, zone, level, hue, saturation, vibrancy)
    )

    if result:
        msg_parts = [zone.name]
        if level is not None:
            msg_parts.append(f"@ {level}%")
        if hue is not None:
            msg_parts.append(f"H:{hue}")
        if saturation is not None:
            msg_parts.append(f"S:{saturation}")

        formatter.print_success(
            " ".join(msg_parts),
            {
                "zone": zone.name,
                "zone_id": zone.id,
                "level": level,
                "hue": hue,
                "saturation": saturation,
            },
        )
    else:
        formatter.print_error(f"Failed to set {zone.name}")
        raise typer.Exit(1)


async def _set_zone(
    bridge_config,
    zone: Zone,
    level: Optional[int],
    hue: Optional[int],
    saturation: Optional[int],
    vibrancy: Optional[int],
) -> dict:
    """Set zone level/color."""
    async with LutronBridge(bridge_config) as bridge:
        if zone.supports_color and (hue is not None or saturation is not None):
            # Get current values for any not specified
            if level is None or hue is None or saturation is None or vibrancy is None:
                status = await bridge.get_zone_status(zone.id)
                zone_status = status.get("ZoneStatus", {})

                if level is None:
                    level = zone_status.get("Level", 100)

                current_hsv = zone_status.get("ColorTuningStatus", {}).get(
                    "HSVTuningLevel", {}
                )
                if hue is None:
                    hue = current_hsv.get("Hue", 0)
                if saturation is None:
                    saturation = current_hsv.get("Saturation", 0)
                if vibrancy is None:
                    vibrancy = zone_status.get("Vibrancy", 50)

            return await bridge.set_color(zone.id, level, hue, saturation, vibrancy)
        else:
            if level is None:
                level = 100
            return await bridge.set_level(zone.id, level, zone)


def on_cmd(
    zone_query: str = typer.Argument(..., help="Zone name or ID"),
    bridge: Optional[str] = typer.Option(
        None, "--bridge", "-b", help="Bridge name to use"
    ),
) -> None:
    """
    Turn zone on (100%).

    DESCRIPTION:
        Turns a zone on to full brightness, preserving color settings.

    EXAMPLES:
        lutron on "Kitchen Light"
        lutron on dome

    OUTPUT (--json):
        {"success": true, "zone": "Kitchen Light", "level": 100}
    """
    formatter = get_formatter()
    bridge_config = _get_bridge_config(bridge)

    # Get zone from cache
    cache = HouseCache(bridge_config.name)
    house = cache.get()
    if house is None:
        house = asyncio.run(_load_house(bridge_config))
        cache.save(house)

    zone = _find_zone(zone_query, house.zones)
    if not zone:
        formatter.print_error(f"Zone not found: {zone_query}")
        raise typer.Exit(1)

    result = asyncio.run(_turn_on(bridge_config, zone))

    if result:
        formatter.print_success(
            f"{zone.name} ON",
            {"zone": zone.name, "zone_id": zone.id, "level": 100},
        )
    else:
        formatter.print_error(f"Failed to turn on {zone.name}")
        raise typer.Exit(1)


async def _turn_on(bridge_config, zone: Zone) -> dict:
    """Turn zone on."""
    async with LutronBridge(bridge_config) as bridge:
        return await bridge.turn_on(zone.id, zone)


def off_cmd(
    zone_query: str = typer.Argument(..., help="Zone name or ID"),
    bridge: Optional[str] = typer.Option(
        None, "--bridge", "-b", help="Bridge name to use"
    ),
) -> None:
    """
    Turn zone off (0%).

    DESCRIPTION:
        Turns a zone off (brightness to 0).

    EXAMPLES:
        lutron off "Kitchen Light"
        lutron off dome

    OUTPUT (--json):
        {"success": true, "zone": "Kitchen Light", "level": 0}
    """
    formatter = get_formatter()
    bridge_config = _get_bridge_config(bridge)

    # Get zone from cache
    cache = HouseCache(bridge_config.name)
    house = cache.get()
    if house is None:
        house = asyncio.run(_load_house(bridge_config))
        cache.save(house)

    zone = _find_zone(zone_query, house.zones)
    if not zone:
        formatter.print_error(f"Zone not found: {zone_query}")
        raise typer.Exit(1)

    result = asyncio.run(_turn_off(bridge_config, zone))

    if result:
        formatter.print_success(
            f"{zone.name} OFF",
            {"zone": zone.name, "zone_id": zone.id, "level": 0},
        )
    else:
        formatter.print_error(f"Failed to turn off {zone.name}")
        raise typer.Exit(1)


async def _turn_off(bridge_config, zone: Zone) -> dict:
    """Turn zone off."""
    async with LutronBridge(bridge_config) as bridge:
        return await bridge.turn_off(zone.id, zone)
