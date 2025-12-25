"""Button configuration and event handling."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Union

import yaml

from .config import get_scenes_dir


class EventType(str, Enum):
    """Button event types."""

    PRESS = "Press"
    RELEASE = "Release"
    MULTI_TAP = "MultiTap"
    LONG_HOLD = "LongHold"  # Client-side detection


@dataclass
class DimAction:
    """Dimming action configuration."""

    zone: str
    direction: str = "up"  # "up" or "down"
    step: int = 10
    continuous: bool = False


@dataclass
class ToggleAction:
    """Toggle action - cycles between scenes or on/off."""

    scenes: list[str]  # List of scene names to cycle through


@dataclass
class SceneAction:
    """Direct scene recall action."""

    scene: str


@dataclass
class RoomAction:
    """Set room to a specific level."""

    room: str
    level: int


@dataclass
class ButtonAction:
    """Action to perform on a button event."""

    action: Union[SceneAction, ToggleAction, DimAction, RoomAction, None] = None
    stop_dim: bool = False  # For release events


@dataclass
class ButtonBinding:
    """Maps button events to actions."""

    button: Optional[int] = None
    buttons: Optional[list[int]] = None
    device: Optional[str] = None
    button_number: Optional[int] = None

    press: Optional[ButtonAction] = None
    release: Optional[ButtonAction] = None
    double_tap: Optional[ButtonAction] = None
    long_press: Optional[ButtonAction] = None


@dataclass
class ButtonConfig:
    """Button configuration file."""

    buttons: list[ButtonBinding] = field(default_factory=list)
    long_press_ms: int = 500
    dim_step: int = 10
    fade_time: float = 1.0


def parse_action(value) -> Optional[ButtonAction]:
    """Parse an action from config value."""
    if value is None:
        return None

    # Simple string = scene name
    if isinstance(value, str):
        return ButtonAction(action=SceneAction(scene=value))

    # Dict with specific action type
    if isinstance(value, dict):
        if "toggle" in value:
            toggle_val = value["toggle"]
            if isinstance(toggle_val, str):
                # Single scene = toggle between scene and off
                scenes = [toggle_val, "__off__"]
            else:
                scenes = toggle_val
            return ButtonAction(action=ToggleAction(scenes=scenes))

        if "dim" in value:
            dim = value["dim"]
            if isinstance(dim, dict):
                return ButtonAction(
                    action=DimAction(
                        zone=dim.get("zone", ""),
                        direction=dim.get("direction", "up"),
                        step=dim.get("step", 10),
                        continuous=dim.get("continuous", False),
                    )
                )

        if "room" in value:
            return ButtonAction(
                action=RoomAction(
                    room=value["room"],
                    level=value.get("level", 100),
                )
            )

        if "scene" in value:
            return ButtonAction(action=SceneAction(scene=value["scene"]))

        if "stop_dim" in value:
            return ButtonAction(stop_dim=value["stop_dim"])

    return None


def load_button_config(path: Optional[str] = None) -> Optional[ButtonConfig]:
    """
    Load button configuration from YAML file.

    If no path provided, looks for lutron-buttons.yaml in scenes directory.
    """
    if path:
        config_path = Path(path)
    else:
        # Look in scenes directory
        scenes_dir = get_scenes_dir()
        config_path = scenes_dir / "lutron-buttons.yaml"
        if not config_path.exists():
            config_path = scenes_dir.parent / "lutron-buttons.yaml"

    if not config_path.exists():
        return None

    with open(config_path) as f:
        data = yaml.safe_load(f)

    if not data:
        return None

    config = ButtonConfig()

    # Parse settings
    settings = data.get("settings", {})
    config.long_press_ms = settings.get("long_press_ms", 500)
    config.dim_step = settings.get("dim_step", 10)
    config.fade_time = settings.get("fade_time", 1.0)

    # Parse button bindings
    for binding_data in data.get("buttons", []):
        binding = ButtonBinding(
            button=binding_data.get("button"),
            buttons=binding_data.get("buttons"),
            device=binding_data.get("device"),
            button_number=binding_data.get("button_number"),
            press=parse_action(binding_data.get("press")),
            release=parse_action(binding_data.get("release")),
            double_tap=parse_action(binding_data.get("double_tap")),
            long_press=parse_action(binding_data.get("long_press")),
        )
        config.buttons.append(binding)

    return config


def get_binding_for_button(
    config: ButtonConfig, button_id: int, device_name: Optional[str] = None
) -> Optional[ButtonBinding]:
    """Find the binding that matches a button ID or device/button_number."""
    for binding in config.buttons:
        # Match by button ID
        if binding.button == button_id:
            return binding
        if binding.buttons and button_id in binding.buttons:
            return binding

        # Match by device name (if we have device info)
        # This would require additional context from the bridge

    return None
