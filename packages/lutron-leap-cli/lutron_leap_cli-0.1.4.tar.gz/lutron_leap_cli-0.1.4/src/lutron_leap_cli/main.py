"""Main entry point for Lutron LEAP CLI."""

from typing import Optional

import typer
from rich.console import Console

from . import __version__
from .output.formatter import OutputFormatter, set_formatter
from .commands.discover import discover_cmd, bridges_cmd
from .commands.pair import pair_cmd
from .commands.zones import list_cmd, status_cmd, set_cmd, on_cmd, off_cmd
from .commands.rooms import room_cmd, rooms_cmd
from .commands.scenes import (
    snapshot_cmd,
    recall_cmd,
    scenes_cmd,
    scene_show_cmd,
    scene_delete_cmd,
)

# Main app
app = typer.Typer(
    name="lutron",
    help="""
Lutron LEAP CLI - Control Lutron lighting systems.

SUPPORTED SYSTEMS:
    Caseta, RA2 Select, RadioRA3, HomeWorks QSX

QUICK START:
    1. Discover bridges:  lutron discover
    2. Pair with bridge:  lutron pair 192.168.1.100
    3. List zones:        lutron list
    4. Control lights:    lutron set "Kitchen" --level 50

COMMON COMMANDS:
    lutron list              List all zones
    lutron list --rooms      List zones grouped by room
    lutron status <zone>     Get zone status
    lutron set <zone> -l 50  Set zone to 50%
    lutron on <zone>         Turn zone on
    lutron off <zone>        Turn zone off
    lutron room <room> -l 50 Set all zones in room

SCENE MANAGEMENT:
    lutron snapshot <name>   Save current state
    lutron recall <name>     Restore saved scene
    lutron scenes            List saved scenes

OUTPUT:
    Add --json to any command for JSON output (useful for scripting/LLMs)

CONFIGURATION:
    Config: ~/.config/lutron-leap-cli/
    Scenes: ./lutron-scenes/ (current directory)
""",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Scene subcommands
scene_app = typer.Typer(
    name="scene",
    help="Scene management commands",
    no_args_is_help=True,
)
app.add_typer(scene_app, name="scene")

console = Console()


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print(f"lutron-leap-cli {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output as JSON (for scripting/LLMs)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """
    Lutron LEAP CLI - Control Lutron lighting systems.
    """
    formatter = OutputFormatter(json_output=json_output, verbose=verbose)
    set_formatter(formatter)


# Discovery & Setup Commands
app.command("discover", help="Scan network for Lutron bridges")(discover_cmd)
app.command("pair", help="Pair with a Lutron bridge")(pair_cmd)
app.command("bridges", help="List configured bridges")(bridges_cmd)

# Zone Commands
app.command("list", help="List all zones")(list_cmd)
app.command("status", help="Get zone status")(status_cmd)
app.command("set", help="Set zone level and/or color")(set_cmd)
app.command("on", help="Turn zone on (100%)")(on_cmd)
app.command("off", help="Turn zone off (0%)")(off_cmd)

# Room Commands
app.command("room", help="Control all zones in a room")(room_cmd)
app.command("rooms", help="List all rooms")(rooms_cmd)

# Scene Commands (top-level shortcuts)
app.command("snapshot", help="Capture current state as scene")(snapshot_cmd)
app.command("recall", help="Recall a saved scene")(recall_cmd)
app.command("scenes", help="List saved scenes")(scenes_cmd)

# Scene subcommands
scene_app.command("show", help="Show scene contents")(scene_show_cmd)
scene_app.command("delete", help="Delete a scene")(scene_delete_cmd)
scene_app.command("list", help="List saved scenes")(scenes_cmd)


@app.command("refresh", help="Refresh zone cache from bridge")
def refresh_cmd(
    bridge: Optional[str] = typer.Option(
        None, "--bridge", "-b", help="Bridge name to use"
    ),
):
    """
    Refresh the zone cache.

    DESCRIPTION:
        Forces a refresh of the cached house topology from the bridge.
        Useful after adding or modifying zones in the Lutron app.

    EXAMPLES:
        lutron refresh

    OUTPUT (--json):
        {"success": true, "zones_loaded": 150}
    """
    from .output.formatter import get_formatter
    from .core.config import load_config
    from .core.cache import HouseCache
    from .core.bridge import LutronBridge
    import asyncio

    formatter = get_formatter()
    config = load_config()

    if bridge:
        bridge_config = config.get_bridge(bridge)
        if not bridge_config:
            formatter.print_error(f"Bridge not found: {bridge}")
            raise typer.Exit(1)
    else:
        bridge_config = config.get_default_bridge()
        if not bridge_config:
            formatter.print_error("No bridge configured. Use 'lutron pair <IP>' first.")
            raise typer.Exit(1)

    formatter.print_info("Loading zones from bridge...")

    cache = HouseCache(bridge_config.name)
    cache.invalidate()

    async def load():
        async with LutronBridge(bridge_config) as br:
            return await br.load_house()

    house = asyncio.run(load())
    cache.save(house)

    formatter.print_success(
        f"Loaded {len(house.zones)} zones in {len([a for a in house.areas.values() if a.is_room])} rooms",
        {
            "zones_loaded": len(house.zones),
            "rooms": len([a for a in house.areas.values() if a.is_room]),
        },
    )


@app.command("config", help="Show configuration paths")
def config_cmd():
    """
    Show configuration information.

    DESCRIPTION:
        Displays paths to configuration, certificates, cache, and scenes.

    EXAMPLES:
        lutron config
        lutron config --json

    OUTPUT (--json):
        {"config_dir": "...", "certs_dir": "...", "cache_dir": "...", "scenes_dir": "..."}
    """
    from .output.formatter import get_formatter
    from .core.config import (
        get_config_dir,
        get_certificates_dir,
        get_cache_dir,
        get_scenes_dir,
    )

    formatter = get_formatter()

    data = {
        "config_dir": str(get_config_dir()),
        "certs_dir": str(get_certificates_dir()),
        "cache_dir": str(get_cache_dir()),
        "scenes_dir": str(get_scenes_dir()),
    }

    if formatter.json_output:
        formatter.print(data)
    else:
        console.print("[bold]Configuration Paths[/bold]\n")
        console.print(f"Config:       {data['config_dir']}")
        console.print(f"Certificates: {data['certs_dir']}")
        console.print(f"Cache:        {data['cache_dir']}")
        console.print(f"Scenes:       {data['scenes_dir']}")


if __name__ == "__main__":
    app()
