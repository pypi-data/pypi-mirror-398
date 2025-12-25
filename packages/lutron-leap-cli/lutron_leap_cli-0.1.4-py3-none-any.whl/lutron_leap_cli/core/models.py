"""Pydantic models for Lutron LEAP CLI."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ControlType(str, Enum):
    """Zone control types."""

    DIMMED = "Dimmed"
    SWITCHED = "Switched"
    FAN_SPEED = "FanSpeed"
    SHADE = "Shade"
    WHITE_TUNE = "WhiteTune"
    COLOR_TUNE = "ColorTune"
    SPECTRUM_TUNE = "SpectrumTune"


class HSVColor(BaseModel):
    """HSV color representation."""

    hue: int = Field(ge=0, le=360, description="Hue value 0-360")
    saturation: int = Field(ge=0, le=100, description="Saturation 0-100")


class ColorTuningRange(BaseModel):
    """Color temperature range in Kelvin."""

    min_kelvin: int = Field(alias="Min")
    max_kelvin: int = Field(alias="Max")


class ZoneStatus(BaseModel):
    """Current status of a zone."""

    level: int = Field(ge=0, le=100, description="Brightness level 0-100")
    color: Optional[HSVColor] = None
    vibrancy: Optional[int] = Field(None, ge=0, le=100)
    availability: str = "Available"


class Zone(BaseModel):
    """A controllable zone (light, fan, shade, etc.)."""

    id: str = Field(description="Zone ID from LEAP API")
    name: str = Field(description="Zone display name")
    area: str = Field(description="Parent area/room name")
    area_id: str = Field(description="Parent area ID")
    control_type: ControlType = Field(description="Type of control")
    is_light: bool = Field(default=True, description="Whether this is a light")
    available_controls: list[str] = Field(default_factory=list)
    color_tuning_range: Optional[ColorTuningRange] = None

    @property
    def supports_color(self) -> bool:
        """Check if zone supports color tuning."""
        return self.control_type in (ControlType.COLOR_TUNE, ControlType.SPECTRUM_TUNE)

    @property
    def supports_dimming(self) -> bool:
        """Check if zone supports dimming."""
        return self.control_type not in (ControlType.SWITCHED, ControlType.FAN_SPEED)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "id": self.id,
            "name": self.name,
            "area": self.area,
            "control_type": self.control_type.value,
            "is_light": self.is_light,
            "supports_color": self.supports_color,
            "supports_dimming": self.supports_dimming,
        }


class Area(BaseModel):
    """An area (room or zone grouping)."""

    id: str = Field(description="Area ID from LEAP API")
    name: str = Field(description="Area display name")
    is_room: bool = Field(description="Whether this is a leaf/room (vs parent area)")
    parent_id: Optional[str] = Field(None, description="Parent area ID if nested")
    zone_ids: list[str] = Field(default_factory=list, description="Associated zone IDs")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "id": self.id,
            "name": self.name,
            "is_room": self.is_room,
            "zone_count": len(self.zone_ids),
        }


class ZoneState(BaseModel):
    """Saved state of a zone for scenes."""

    level: int = Field(ge=0, le=100)
    color: Optional[HSVColor] = None
    vibrancy: Optional[int] = Field(None, ge=0, le=100)


class Scene(BaseModel):
    """A saved lighting scene."""

    name: str = Field(description="Scene name")
    created_at: datetime = Field(default_factory=datetime.now)
    zones: dict[str, ZoneState] = Field(
        default_factory=dict, description="Zone ID to state mapping"
    )
    area_filter: Optional[str] = Field(
        None, description="Area filter used when capturing"
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "zone_count": len(self.zones),
            "area_filter": self.area_filter,
        }


class BridgeConfig(BaseModel):
    """Configuration for a Lutron bridge."""

    name: str = Field(description="Bridge display name")
    ip: str = Field(description="Bridge IP address")
    port: int = Field(default=8081, description="LEAP port")
    default: bool = Field(
        default=False, description="Whether this is the default bridge"
    )
    ca_cert: str = Field(description="CA certificate filename")
    client_cert: str = Field(description="Client certificate filename")
    client_key: str = Field(description="Client private key filename")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "name": self.name,
            "ip": self.ip,
            "port": self.port,
            "default": self.default,
        }


class House(BaseModel):
    """Complete house topology."""

    bridge_name: str
    areas: dict[str, Area] = Field(
        default_factory=dict, description="Area name to Area mapping"
    )
    zones: dict[str, Zone] = Field(
        default_factory=dict, description="Zone ID to Zone mapping"
    )
    zone_by_name: dict[str, str] = Field(
        default_factory=dict, description="Lowercase name to zone ID"
    )
    updated_at: datetime = Field(default_factory=datetime.now)
