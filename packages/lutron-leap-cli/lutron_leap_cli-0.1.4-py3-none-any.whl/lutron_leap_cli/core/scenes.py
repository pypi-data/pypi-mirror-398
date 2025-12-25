"""Scene file utilities - supports YAML and JSON formats."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from .config import get_scenes_dir
from .models import Scene, ZoneState, HSVColor


def resolve_scene_path(name_or_path: str) -> Optional[Path]:
    """
    Resolve a scene name or path to an actual file path.

    Supports:
    - Scene name: "dining-intimate" -> looks in default scenes dir
    - Relative path: "./my-scenes/dining.yaml"
    - Absolute path: "/path/to/scene.yaml"

    Returns the path if found, None otherwise.
    """
    path = Path(name_or_path)

    # If it's an absolute path or has directory components, use directly
    if path.is_absolute() or "/" in name_or_path or "\\" in name_or_path:
        # Try exact path first
        if path.exists():
            return path
        # Try adding extensions
        for ext in [".yaml", ".yml", ".json"]:
            p = path.with_suffix(ext)
            if p.exists():
                return p
        return None

    # It's just a name - look in the default scenes directory
    scenes_dir = get_scenes_dir()

    # Try each extension in order of preference
    for ext in [".yaml", ".yml", ".json"]:
        p = scenes_dir / f"{name_or_path}{ext}"
        if p.exists():
            return p

    return None


def get_scene_save_path(name_or_path: str) -> Path:
    """
    Get the path where a scene should be saved.

    If a path with directory components is provided, use it directly.
    Otherwise, save to the default scenes directory with .yaml extension.
    """
    path = Path(name_or_path)

    # If it's an absolute path or has directory components, use directly
    if path.is_absolute() or "/" in name_or_path or "\\" in name_or_path:
        # Ensure it has an extension
        if not path.suffix:
            path = path.with_suffix(".yaml")
        # Create parent directory if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    # Save to default directory with .yaml extension
    scenes_dir = get_scenes_dir()
    return scenes_dir / f"{name_or_path}.yaml"


def load_scene(name_or_path: str) -> Optional[Scene]:
    """
    Load a scene from disk.

    Supports both YAML and JSON formats.
    Accepts scene names, relative paths, or absolute paths.
    """
    path = resolve_scene_path(name_or_path)
    if not path or not path.exists():
        return None

    try:
        with open(path) as f:
            content = f.read()

        # Parse based on extension
        if path.suffix in [".yaml", ".yml"]:
            data = yaml.safe_load(content)
        else:
            data = json.loads(content)

        if not data:
            return None

        return _parse_scene_data(data)

    except (yaml.YAMLError, json.JSONDecodeError, KeyError, ValueError):
        return None


def _parse_scene_data(data: dict) -> Scene:
    """Parse scene data dict into Scene model."""
    zones = {}
    for zone_id, state_data in data.get("zones", {}).items():
        color = None
        if state_data.get("color"):
            color = HSVColor(
                hue=state_data["color"]["hue"],
                saturation=state_data["color"]["saturation"],
            )
        zones[str(zone_id)] = ZoneState(
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


def save_scene(scene: Scene, path_or_name: Optional[str] = None) -> Path:
    """
    Save a scene to disk in YAML format.

    If path_or_name is not provided, uses scene.name.
    Returns the path where the scene was saved.
    """
    if path_or_name is None:
        path_or_name = scene.name

    path = get_scene_save_path(path_or_name)

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
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    return path


def delete_scene(name_or_path: str) -> bool:
    """
    Delete a scene file.

    Returns True if deleted, False if not found.
    """
    path = resolve_scene_path(name_or_path)
    if path and path.exists():
        path.unlink()
        return True
    return False


def list_scenes() -> list[Scene]:
    """
    List all saved scenes in the default scenes directory.

    Supports both .yaml/.yml and .json files.
    """
    scenes_dir = get_scenes_dir()
    scenes = []

    # Find all scene files
    for pattern in ["*.yaml", "*.yml", "*.json"]:
        for path in scenes_dir.glob(pattern):
            scene = load_scene(str(path))
            if scene:
                scenes.append(scene)

    # Remove duplicates (in case of same scene in different formats)
    seen_names = set()
    unique_scenes = []
    for scene in scenes:
        if scene.name not in seen_names:
            seen_names.add(scene.name)
            unique_scenes.append(scene)

    return sorted(unique_scenes, key=lambda s: s.name.lower())
