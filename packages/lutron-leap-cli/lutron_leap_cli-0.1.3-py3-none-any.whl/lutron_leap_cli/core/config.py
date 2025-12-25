"""Configuration management for Lutron LEAP CLI."""

from pathlib import Path
from typing import Optional

import yaml
from platformdirs import user_config_dir, user_cache_dir
from pydantic import BaseModel, Field

from .models import BridgeConfig


APP_NAME = "lutron-leap-cli"


def get_config_dir() -> Path:
    """Get the platform-specific configuration directory."""
    config_dir = Path(user_config_dir(APP_NAME))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_cache_dir() -> Path:
    """Get the platform-specific cache directory."""
    cache_dir = Path(user_cache_dir(APP_NAME))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_certificates_dir() -> Path:
    """Get the certificates directory."""
    certs_dir = get_config_dir() / "certificates"
    certs_dir.mkdir(parents=True, exist_ok=True)
    return certs_dir


def get_scenes_dir() -> Path:
    """Get the scenes directory (current working directory or parent if already in lutron-scenes)."""
    cwd = Path.cwd()
    if cwd.name == "lutron-scenes":
        scenes_dir = cwd
    else:
        scenes_dir = cwd / "lutron-scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    return scenes_dir


class Config(BaseModel):
    """Main configuration model."""

    bridges: list[BridgeConfig] = Field(default_factory=list)

    def get_default_bridge(self) -> Optional[BridgeConfig]:
        """Get the default bridge configuration."""
        for bridge in self.bridges:
            if bridge.default:
                return bridge
        # Return first bridge if none is default
        return self.bridges[0] if self.bridges else None

    def get_bridge(self, name: str) -> Optional[BridgeConfig]:
        """Get a bridge by name."""
        for bridge in self.bridges:
            if bridge.name.lower() == name.lower():
                return bridge
        return None

    def add_bridge(self, bridge: BridgeConfig) -> None:
        """Add a new bridge configuration."""
        # Remove existing bridge with same name
        self.bridges = [
            b for b in self.bridges if b.name.lower() != bridge.name.lower()
        ]
        # If this is the first bridge or marked as default, ensure it's default
        if not self.bridges or bridge.default:
            for b in self.bridges:
                b.default = False
            bridge.default = True
        self.bridges.append(bridge)

    def remove_bridge(self, name: str) -> bool:
        """Remove a bridge by name. Returns True if removed."""
        original_len = len(self.bridges)
        self.bridges = [b for b in self.bridges if b.name.lower() != name.lower()]
        return len(self.bridges) < original_len


def get_config_path() -> Path:
    """Get the path to the config file."""
    return get_config_dir() / "config.yaml"


def load_config() -> Config:
    """Load configuration from disk."""
    config_path = get_config_path()
    if not config_path.exists():
        return Config()

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    bridges = []
    for bridge_data in data.get("bridges", []):
        bridges.append(
            BridgeConfig(
                name=bridge_data["name"],
                ip=bridge_data["ip"],
                port=bridge_data.get("port", 8081),
                default=bridge_data.get("default", False),
                ca_cert=bridge_data["certificates"]["ca"],
                client_cert=bridge_data["certificates"]["cert"],
                client_key=bridge_data["certificates"]["key"],
            )
        )

    return Config(bridges=bridges)


def save_config(config: Config) -> None:
    """Save configuration to disk."""
    config_path = get_config_path()

    data = {"bridges": []}
    for bridge in config.bridges:
        data["bridges"].append(
            {
                "name": bridge.name,
                "ip": bridge.ip,
                "port": bridge.port,
                "default": bridge.default,
                "certificates": {
                    "ca": bridge.ca_cert,
                    "cert": bridge.client_cert,
                    "key": bridge.client_key,
                },
            }
        )

    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def get_config() -> Config:
    """Get the current configuration (convenience alias)."""
    return load_config()
