"""Watch for button events and trigger actions."""

import asyncio
import signal
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console

from ..core.config import load_config
from ..core.bridge import LutronBridge
from ..core.cache import HouseCache
from ..core.buttons import (
    ButtonConfig,
    load_button_config,
    get_binding_for_button,
    SceneAction,
    ToggleAction,
    RoomAction,
    DimAction,
)
from ..core.scenes import load_scene
from ..output.formatter import get_formatter

console = Console()

# Track toggle states for each button
_toggle_states: dict[int, int] = {}
# Track last scene zones for __off__ functionality
_last_scene_zones: dict[int, list[str]] = {}


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


class ButtonWatcher:
    """Watches for button events and triggers actions."""

    def __init__(
        self,
        bridge: LutronBridge,
        config: Optional[ButtonConfig],
        debug: bool = False,
        house=None,
    ):
        self.bridge = bridge
        self.config = config
        self.debug = debug
        self.house = house
        self.running = True
        self.events: list[dict] = []
        self._press_times: dict[str, datetime] = {}

    def handle_event(self, response):
        """Handle a button event from the bridge."""
        try:
            body = response.Body
            if not body:
                return

            status = body.get("ButtonStatus", {})
            button_href = status.get("Button", {}).get("href", "")
            button_id = button_href.split("/")[-1] if button_href else ""
            event_data = status.get("ButtonEvent", {})
            event_type = event_data.get("EventType", "Unknown")

            if not button_id:
                return

            timestamp = datetime.now()

            # Track press times for long press detection
            if event_type == "Press":
                self._press_times[button_id] = timestamp
            elif event_type == "Release" and button_id in self._press_times:
                press_time = self._press_times.pop(button_id)
                duration_ms = (timestamp - press_time).total_seconds() * 1000
                if self.config and duration_ms > self.config.long_press_ms:
                    # This was a long press
                    event_type = "LongHold"

            event = {
                "timestamp": timestamp,
                "button_id": button_id,
                "event_type": event_type,
            }
            self.events.append(event)

            # Keep only last 20 events
            if len(self.events) > 20:
                self.events = self.events[-20:]

            if self.debug:
                self._print_debug_event(event)
            elif self.config:
                # Execute action
                asyncio.create_task(self._execute_action(event))

        except Exception as e:
            if self.debug:
                console.print(f"[red]Error handling event: {e}[/red]")

    def _print_debug_event(self, event: dict):
        """Print a debug event to console."""
        ts = event["timestamp"].strftime("%H:%M:%S.%f")[:-3]
        btn = event["button_id"]
        evt = event["event_type"]

        color = {
            "Press": "green",
            "Release": "dim",
            "MultiTap": "yellow",
            "LongHold": "cyan",
        }.get(evt, "white")

        console.print(
            f"[dim]{ts}[/dim] Button [bold]{btn}[/bold] [{color}]{evt}[/{color}]"
        )

    async def _execute_action(self, event: dict):
        """Execute the action for a button event."""
        if not self.config:
            return

        button_id = int(event["button_id"])
        event_type = event["event_type"]

        # Log the event
        console.print(f"[cyan]Event:[/cyan] Button {button_id} → {event_type}")

        binding = get_binding_for_button(self.config, button_id)
        if not binding:
            console.print(f"  [dim]No binding configured for button {button_id}[/dim]")
            return

        # Get action based on event type
        action = None
        if event_type == "Press" and binding.press:
            action = binding.press
        elif event_type == "Release" and binding.release:
            action = binding.release
        elif event_type == "MultiTap" and binding.double_tap:
            action = binding.double_tap
        elif event_type == "LongHold" and binding.long_press:
            action = binding.long_press

        if not action:
            console.print(f"  [dim]No action for {event_type} event[/dim]")
            return

        console.print("  [green]→ Executing action[/green]")

        try:
            if action.stop_dim:
                # Stop any ongoing dimming
                pass  # TODO: Implement stop dim

            elif isinstance(action.action, SceneAction):
                await self._recall_scene(action.action.scene)

            elif isinstance(action.action, ToggleAction):
                await self._toggle_scenes(button_id, action.action.scenes)

            elif isinstance(action.action, RoomAction):
                await self._set_room_level(action.action.room, action.action.level)

            elif isinstance(action.action, DimAction):
                await self._dim_zone(action.action)

        except Exception as e:
            console.print(f"[red]Action failed: {e}[/red]")

    async def _recall_scene(self, scene_name: str, button_id: Optional[int] = None):
        """Recall a scene."""
        scene = load_scene(scene_name)
        if not scene:
            console.print(f"[yellow]Scene not found: {scene_name}[/yellow]")
            return

        console.print(
            f"[dim]Recalling scene '{scene_name}' ({len(scene.zones)} zones)...[/dim]"
        )
        success = 0
        failed = 0

        # Track zones for __off__ toggle
        if button_id is not None:
            _last_scene_zones[button_id] = list(scene.zones.keys())

        for zone_id, state in scene.zones.items():
            zone = self.house.zones.get(zone_id) if self.house else None
            zone_name = zone.name if zone else zone_id
            try:
                if state.color:
                    await self.bridge.set_color(
                        zone_id,
                        state.level,
                        state.color.hue,
                        state.color.saturation,
                        state.vibrancy or 50,
                    )
                else:
                    await self.bridge.set_level(zone_id, state.level, zone)
                console.print(f"  [dim]{zone_name}[/dim] → {state.level}%")
                success += 1
            except Exception as e:
                console.print(f"  [red]{zone_name}[/red] → failed: {e}")
                failed += 1

        if failed:
            console.print(
                f"[yellow]⚠[/yellow] Recalled '{scene_name}': {success} ok, {failed} failed"
            )
        else:
            console.print(
                f"[green]✓[/green] Recalled scene '{scene_name}' ({success} zones)"
            )

    async def _toggle_scenes(self, button_id: int, scenes: list[str]):
        """Toggle between scenes."""
        current_index = _toggle_states.get(button_id, -1)
        next_index = (current_index + 1) % len(scenes)
        _toggle_states[button_id] = next_index

        scene_name = scenes[next_index]

        if scene_name == "__off__":
            # Turn off zones from last recalled scene for this button
            zone_ids = _last_scene_zones.get(button_id, [])
            if zone_ids:
                console.print(f"[dim]Turning off {len(zone_ids)} zones...[/dim]")
                for zone_id in zone_ids:
                    zone = self.house.zones.get(zone_id) if self.house else None
                    zone_name = zone.name if zone else zone_id
                    try:
                        await self.bridge.set_level(zone_id, 0, zone)
                        console.print(f"  [dim]{zone_name}[/dim] → 0%")
                    except Exception as e:
                        console.print(f"  [red]{zone_name}[/red] → failed: {e}")
                console.print(f"[green]✓[/green] Turned off {len(zone_ids)} zones")
            else:
                console.print("[yellow]No zones to turn off[/yellow]")
        else:
            await self._recall_scene(scene_name, button_id)

    async def _set_room_level(self, room_name: str, level: int):
        """Set all zones in a room to a level."""
        if not self.house:
            return

        # Find the room
        for area in self.house.areas.values():
            if area.is_room and room_name.lower() in area.name.lower():
                for zone_id in area.zone_ids:
                    zone = self.house.zones.get(zone_id)
                    try:
                        await self.bridge.set_level(zone_id, level, zone)
                    except Exception:
                        pass
                console.print(f"[green]✓[/green] Set {area.name} to {level}%")
                return

        console.print(f"[yellow]Room not found: {room_name}[/yellow]")

    async def _dim_zone(self, action: DimAction):
        """Dim a zone up or down."""
        if not self.house:
            return

        # Find the zone
        zone_id = self.house.zone_by_name.get(action.zone.lower())
        if not zone_id:
            console.print(f"[yellow]Zone not found: {action.zone}[/yellow]")
            return

        zone = self.house.zones.get(zone_id)

        # Get current level
        status = await self.bridge.get_zone_status(zone_id)
        current_level = status.get("ZoneStatus", {}).get("Level", 0)

        # Calculate new level
        if action.direction == "up":
            new_level = min(100, current_level + action.step)
        else:
            new_level = max(0, current_level - action.step)

        await self.bridge.set_level(zone_id, new_level, zone)
        console.print(f"[dim]Dim {action.zone}: {current_level}% → {new_level}%[/dim]")


async def _run_watcher(
    bridge_config,
    button_config: Optional[ButtonConfig],
    debug: bool,
):
    """Run the button watcher loop."""
    cache = HouseCache(bridge_config.name)
    house = cache.get()

    async with LutronBridge(bridge_config) as bridge:
        if house is None:
            console.print("[dim]Loading house topology...[/dim]")
            house = await bridge.load_house()
            cache.save(house)

        watcher = ButtonWatcher(bridge, button_config, debug=debug, house=house)

        # Subscribe to button events
        console.print("[dim]Subscribing to button events...[/dim]")
        tags = await bridge.subscribe_to_all_buttons(watcher.handle_event)

        if not tags:
            console.print("[yellow]No buttons found to subscribe to[/yellow]")
            return

        console.print(f"[green]✓[/green] Watching {len(tags)} buttons")

        if debug:
            console.print("[dim]Press Ctrl+C to stop[/dim]\n")
        elif button_config:
            console.print(
                f"[dim]Loaded {len(button_config.buttons)} button bindings[/dim]"
            )
            console.print("[dim]Press Ctrl+C to stop[/dim]\n")
        else:
            console.print(
                "[yellow]No button config found - use --debug to see events[/yellow]"
            )

        # Keep running until interrupted
        try:
            while watcher.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

        console.print("\n[dim]Stopped watching[/dim]")


def buttons_cmd(
    bridge: Optional[str] = typer.Option(
        None, "--bridge", "-b", help="Bridge name to use"
    ),
) -> None:
    """
    List all buttons (Picos and Keypads).

    DESCRIPTION:
        Shows all buttons that can emit events.
        Use this to find button IDs for your configuration.

    EXAMPLES:
        lutron buttons
        lutron buttons --json
    """
    formatter = get_formatter()
    bridge_config = _get_bridge_config(bridge)

    async def _list_buttons():
        async with LutronBridge(bridge_config) as br:
            return await br.get_buttons()

    buttons = asyncio.run(_list_buttons())

    if not buttons:
        formatter.print_warning("No buttons found")
        return

    if formatter.json_output:
        data = []
        for button in buttons:
            href = button.get("href", "")
            button_id = href.split("/")[-1] if href else ""
            engraving = button.get("Engraving", {})
            data.append(
                {
                    "id": button_id,
                    "name": button.get("Name", ""),
                    "engraving": engraving.get("Text", ""),
                    "button_number": button.get("ButtonNumber"),
                    "device_type": button.get("DeviceType", ""),
                    "device_href": button.get("DeviceHref", ""),
                    "parent": button.get("Parent", {}).get("href", ""),
                }
            )
        formatter.print(data)
    else:
        from rich.table import Table

        table = Table(title="Buttons")
        table.add_column("ID", style="cyan")
        table.add_column("Name")
        table.add_column("Engraving", style="green")
        table.add_column("#", style="dim")
        table.add_column("Device Type")

        for button in buttons:
            href = button.get("href", "")
            button_id = href.split("/")[-1] if href else ""
            engraving = button.get("Engraving", {})
            table.add_row(
                button_id,
                button.get("Name", ""),
                engraving.get("Text", ""),
                str(button.get("ButtonNumber", "")),
                button.get("DeviceType", button.get("Parent", {}).get("href", "")),
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(buttons)} buttons[/dim]")


def watch_cmd(
    config: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to button config YAML file"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Debug mode - just print events, don't execute actions",
    ),
    bridge: Optional[str] = typer.Option(
        None, "--bridge", "-b", help="Bridge name to use"
    ),
) -> None:
    """
    Watch for button events and trigger actions.

    DESCRIPTION:
        Subscribes to button events from Picos and Keypads.
        In debug mode, prints all events to stdout.
        Otherwise, executes actions defined in lutron-buttons.yaml.

    CONFIGURATION:
        Create lutron-buttons.yaml in your scenes directory:

        buttons:
          - button: 42
            press: dining-intimate

          - button: 43
            press:
              toggle:
                - scene-a
                - scene-b

          - button: 44
            long_press:
              dim:
                zone: "Kitchen"
                direction: down

        settings:
          long_press_ms: 500

    EXAMPLES:
        lutron watch --debug          # See all button events
        lutron watch                  # Execute configured actions
        lutron watch -c ./buttons.yaml

    NOTE:
        Only Pico remotes and Keypads emit button events.
        Hardwired switches do NOT emit button events via LEAP.
    """
    bridge_config = _get_bridge_config(bridge)

    # Load button config
    button_config = None
    if not debug:
        button_config = load_button_config(config)
        if not button_config and not debug:
            console.print(
                "[yellow]No button config found. "
                "Create lutron-buttons.yaml or use --debug mode.[/yellow]"
            )

    # Set up signal handler for clean shutdown
    def handle_signal(signum, frame):
        console.print("\n[dim]Shutting down...[/dim]")
        raise KeyboardInterrupt()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        asyncio.run(_run_watcher(bridge_config, button_config, debug))
    except KeyboardInterrupt:
        pass
