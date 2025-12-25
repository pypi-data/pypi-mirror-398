"""CLI commands for Lutron LEAP CLI."""

from .discover import discover_cmd, bridges_cmd
from .pair import pair_cmd
from .zones import list_cmd, status_cmd, set_cmd, on_cmd, off_cmd
from .rooms import room_cmd, rooms_cmd
from .scenes import (
    snapshot_cmd,
    recall_cmd,
    scenes_cmd,
    scene_show_cmd,
    scene_delete_cmd,
)

__all__ = [
    # Discovery
    "discover_cmd",
    "bridges_cmd",
    "pair_cmd",
    # Zones
    "list_cmd",
    "status_cmd",
    "set_cmd",
    "on_cmd",
    "off_cmd",
    # Rooms
    "room_cmd",
    "rooms_cmd",
    # Scenes
    "snapshot_cmd",
    "recall_cmd",
    "scenes_cmd",
    "scene_show_cmd",
    "scene_delete_cmd",
]
