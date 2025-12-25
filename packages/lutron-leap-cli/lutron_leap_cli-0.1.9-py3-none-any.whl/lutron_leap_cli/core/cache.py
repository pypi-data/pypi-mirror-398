"""House topology cache management."""

import json
from datetime import datetime, timedelta
from typing import Optional

from .config import get_cache_dir
from .models import House, Zone, Area, ControlType, ColorTuningRange


# Cache expires after 24 hours
CACHE_TTL = timedelta(hours=24)


class HouseCache:
    """Manages cached house topology data."""

    def __init__(self, bridge_name: str):
        self.bridge_name = bridge_name
        self._cache_file = get_cache_dir() / f"{bridge_name}.json"

    def get(self) -> Optional[House]:
        """Get cached house data if valid."""
        if not self._cache_file.exists():
            return None

        try:
            with open(self._cache_file) as f:
                data = json.load(f)

            # Check cache freshness
            updated_at = datetime.fromisoformat(data.get("updated_at", ""))
            if datetime.now() - updated_at > CACHE_TTL:
                return None

            return self._deserialize(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def save(self, house: House) -> None:
        """Save house data to cache."""
        data = self._serialize(house)
        with open(self._cache_file, "w") as f:
            json.dump(data, f, indent=2)

    def invalidate(self) -> None:
        """Remove cached data."""
        if self._cache_file.exists():
            self._cache_file.unlink()

    def _serialize(self, house: House) -> dict:
        """Convert House to JSON-serializable dict."""
        return {
            "bridge_name": house.bridge_name,
            "updated_at": house.updated_at.isoformat(),
            "areas": {
                name: {
                    "id": area.id,
                    "name": area.name,
                    "is_room": area.is_room,
                    "parent_id": area.parent_id,
                    "zone_ids": area.zone_ids,
                }
                for name, area in house.areas.items()
            },
            "zones": {
                zone_id: {
                    "id": zone.id,
                    "name": zone.name,
                    "area": zone.area,
                    "area_id": zone.area_id,
                    "control_type": zone.control_type.value,
                    "is_light": zone.is_light,
                    "available_controls": zone.available_controls,
                    "color_tuning_range": {
                        "min": zone.color_tuning_range.min_kelvin,
                        "max": zone.color_tuning_range.max_kelvin,
                    }
                    if zone.color_tuning_range
                    else None,
                }
                for zone_id, zone in house.zones.items()
            },
            "zone_by_name": house.zone_by_name,
        }

    def _deserialize(self, data: dict) -> House:
        """Convert dict back to House model."""
        areas = {}
        for name, area_data in data.get("areas", {}).items():
            areas[name] = Area(
                id=area_data["id"],
                name=area_data["name"],
                is_room=area_data["is_room"],
                parent_id=area_data.get("parent_id"),
                zone_ids=area_data.get("zone_ids", []),
            )

        zones = {}
        for zone_id, zone_data in data.get("zones", {}).items():
            color_range = None
            if zone_data.get("color_tuning_range"):
                color_range = ColorTuningRange(
                    Min=zone_data["color_tuning_range"]["min"],
                    Max=zone_data["color_tuning_range"]["max"],
                )

            zones[zone_id] = Zone(
                id=zone_data["id"],
                name=zone_data["name"],
                area=zone_data["area"],
                area_id=zone_data["area_id"],
                control_type=ControlType(zone_data["control_type"]),
                is_light=zone_data.get("is_light", True),
                available_controls=zone_data.get("available_controls", []),
                color_tuning_range=color_range,
            )

        return House(
            bridge_name=data["bridge_name"],
            areas=areas,
            zones=zones,
            zone_by_name=data.get("zone_by_name", {}),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


def get_or_load_house(bridge_name: str, loader) -> House:
    """Get house from cache or load fresh."""
    cache = HouseCache(bridge_name)
    house = cache.get()

    if house is None:
        house = loader()
        cache.save(house)

    return house
