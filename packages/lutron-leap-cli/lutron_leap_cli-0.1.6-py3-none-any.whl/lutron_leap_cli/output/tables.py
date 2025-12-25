"""Rich table builders for Lutron LEAP CLI."""

from typing import Optional

from rich.table import Table

from ..core.models import Zone, Area, BridgeConfig, Scene, ZoneStatus


def zones_table(
    zones: list[Zone],
    title: str = "Zones",
    show_area: bool = True,
) -> tuple[Table, list[dict]]:
    """Build a table of zones."""
    table = Table(title=title, show_lines=False)
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    if show_area:
        table.add_column("Area", style="blue")
    table.add_column("Type", style="yellow")
    table.add_column("Features", style="green")

    data = []
    for zone in zones:
        features = []
        if zone.supports_dimming:
            features.append("dim")
        if zone.supports_color:
            features.append("color")

        row = [
            zone.id,
            zone.name,
        ]
        if show_area:
            row.append(zone.area)
        row.extend(
            [
                zone.control_type.value,
                ", ".join(features) if features else "-",
            ]
        )
        table.add_row(*row)

        data.append(zone.to_dict())

    return table, data


def areas_table(
    areas: list[Area],
    title: str = "Areas",
) -> tuple[Table, list[dict]]:
    """Build a table of areas."""
    table = Table(title=title, show_lines=False)
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Zones", style="green", justify="right")

    data = []
    for area in areas:
        area_type = "Room" if area.is_room else "Area"
        table.add_row(
            area.id,
            area.name,
            area_type,
            str(len(area.zone_ids)),
        )
        data.append(area.to_dict())

    return table, data


def bridges_table(
    bridges: list[BridgeConfig],
    title: str = "Configured Bridges",
) -> tuple[Table, list[dict]]:
    """Build a table of configured bridges."""
    table = Table(title=title, show_lines=False)
    table.add_column("Name", style="cyan")
    table.add_column("IP Address", style="blue")
    table.add_column("Port", style="dim")
    table.add_column("Default", style="green")

    data = []
    for bridge in bridges:
        default_marker = "✓" if bridge.default else ""
        table.add_row(
            bridge.name,
            bridge.ip,
            str(bridge.port),
            default_marker,
        )
        data.append(bridge.to_dict())

    return table, data


def scenes_table(
    scenes: list[Scene],
    title: str = "Scenes",
) -> tuple[Table, list[dict]]:
    """Build a table of scenes."""
    table = Table(title=title, show_lines=False)
    table.add_column("Name", style="cyan")
    table.add_column("Created", style="dim")
    table.add_column("Zones", style="green", justify="right")
    table.add_column("Area Filter", style="blue")

    data = []
    for scene in scenes:
        table.add_row(
            scene.name,
            scene.created_at.strftime("%Y-%m-%d %H:%M"),
            str(len(scene.zones)),
            scene.area_filter or "-",
        )
        data.append(scene.to_dict())

    return table, data


def zone_status_table(
    zone: Zone,
    status: ZoneStatus,
    title: Optional[str] = None,
) -> tuple[Table, dict]:
    """Build a status table for a single zone."""
    table = Table(title=title or f"Zone: {zone.name}", show_lines=False)
    table.add_column("Property", style="dim")
    table.add_column("Value", style="cyan")

    table.add_row("ID", zone.id)
    table.add_row("Name", zone.name)
    table.add_row("Area", zone.area)
    table.add_row("Type", zone.control_type.value)
    table.add_row("Level", f"{status.level}%")

    if status.color:
        table.add_row("Hue", str(status.color.hue))
        table.add_row("Saturation", f"{status.color.saturation}%")

    if status.vibrancy is not None:
        table.add_row("Vibrancy", f"{status.vibrancy}%")

    table.add_row("Availability", status.availability)

    data = {
        "zone": zone.to_dict(),
        "status": {
            "level": status.level,
            "color": {
                "hue": status.color.hue,
                "saturation": status.color.saturation,
            }
            if status.color
            else None,
            "vibrancy": status.vibrancy,
            "availability": status.availability,
        },
    }

    return table, data


def discovery_table(
    devices: list[dict],
    title: str = "Discovered Devices",
) -> tuple[Table, list[dict]]:
    """Build a table of discovered devices."""
    table = Table(title=title, show_lines=False)
    table.add_column("IP Address", style="cyan")
    table.add_column("MAC Address", style="dim")
    table.add_column("Model", style="blue")
    table.add_column("Serial", style="yellow")

    for device in devices:
        table.add_row(
            device.get("ip", ""),
            device.get("mac", ""),
            device.get("model", "Unknown"),
            device.get("serial", ""),
        )

    return table, devices
