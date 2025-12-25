"""Lutron bridge communication via LEAP protocol."""

import asyncio
import ssl
from typing import Optional
from contextlib import asynccontextmanager

from pylutron_caseta.leap import open_connection as leap_open_connection

from .config import get_certificates_dir, BridgeConfig
from .models import Zone, Area, House, ControlType, ColorTuningRange


class LutronBridge:
    """High-level Lutron bridge interface using native LEAP protocol."""

    def __init__(self, config: BridgeConfig):
        self.config = config
        self._certs_dir = get_certificates_dir()
        self._leap = None
        self._run_task: Optional[asyncio.Task] = None
        self._house: Optional[House] = None

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context with bridge certificates."""
        ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_REQUIRED

        ca_path = self._certs_dir / self.config.ca_cert
        cert_path = self._certs_dir / self.config.client_cert
        key_path = self._certs_dir / self.config.client_key

        ssl_ctx.load_verify_locations(str(ca_path))
        ssl_ctx.load_cert_chain(str(cert_path), str(key_path))

        return ssl_ctx

    async def connect(self) -> None:
        """Connect to the bridge."""
        ssl_ctx = self._create_ssl_context()
        self._leap = await leap_open_connection(
            self.config.ip,
            self.config.port,
            ssl=ssl_ctx,
        )
        # Start the event monitoring loop as a background task
        self._run_task = asyncio.create_task(self._leap.run())

    async def close(self) -> None:
        """Close the connection."""
        if self._leap:
            self._leap.close()
            if self._run_task:
                self._run_task.cancel()
                try:
                    await self._run_task
                except asyncio.CancelledError:
                    pass
            await self._leap.wait_closed()
            self._leap = None
            self._run_task = None

    async def __aenter__(self) -> "LutronBridge":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def request(
        self, url: str, command_type: str = "ReadRequest", body: Optional[dict] = None
    ) -> dict:
        """Send a LEAP request and return the Body as a dict."""
        if not self._leap:
            raise RuntimeError("Not connected to bridge")
        response = await self._leap.request(command_type, url, body)
        # Response is a namedtuple with Body, Header, CommuniqueType
        return {"Body": response.Body} if response.Body else {}

    # --- House Topology ---

    async def get_areas(self) -> list[dict]:
        """Get all areas from the bridge."""
        response = await self.request("/area")
        body = response.get("Body", {})
        return body.get("Areas", [])

    async def get_area_zones(self, area_href: str) -> list[dict]:
        """Get zones for a specific area."""
        response = await self.request(area_href)
        body = response.get("Body", {})
        # Zones are nested under Area
        area = body.get("Area", {})
        return area.get("AssociatedZones", [])

    async def get_zone_details(self, zone_href: str) -> dict:
        """Get detailed zone information."""
        response = await self.request(zone_href)
        return response.get("Body", {})

    async def load_house(self) -> House:
        """Load complete house topology."""
        areas_data = await self.get_areas()

        areas: dict[str, Area] = {}
        zones: dict[str, Zone] = {}
        zone_by_name: dict[str, str] = {}

        for area_data in areas_data:
            area_href = area_data.get("href", "")
            area_id = area_href.split("/")[-1] if area_href else ""
            area_name = area_data.get("Name", "Unknown")
            is_room = area_data.get("IsLeaf", False)
            parent_href = area_data.get("Parent", {}).get("href", "")
            parent_id = parent_href.split("/")[-1] if parent_href else None

            # Get zones for this area
            zone_ids = []
            if is_room:
                area_zones = await self.get_area_zones(area_href)
                for zone_ref in area_zones:
                    zone_href = zone_ref.get("href", "")
                    if zone_href:
                        zone_details = await self.get_zone_details(zone_href)
                        zone = self._parse_zone(zone_details, area_name, area_id)
                        if zone:
                            zones[zone.id] = zone
                            zone_ids.append(zone.id)
                            zone_by_name[zone.name.lower()] = zone.id

            areas[area_name] = Area(
                id=area_id,
                name=area_name,
                is_room=is_room,
                parent_id=parent_id,
                zone_ids=zone_ids,
            )

        self._house = House(
            bridge_name=self.config.name,
            areas=areas,
            zones=zones,
            zone_by_name=zone_by_name,
        )
        return self._house

    def _parse_zone(
        self, zone_data: dict, area_name: str, area_id: str
    ) -> Optional[Zone]:
        """Parse zone data into Zone model."""
        zone_info = zone_data.get("Zone", zone_data)
        zone_href = zone_info.get("href", "")
        zone_id = zone_href.split("/")[-1] if zone_href else ""

        if not zone_id:
            return None

        name = zone_info.get("Name", f"Zone {zone_id}")
        control_type_str = zone_info.get("ControlType", "Switched")

        try:
            control_type = ControlType(control_type_str)
        except ValueError:
            control_type = ControlType.SWITCHED

        # Determine if this is a light (vs fan, shade, etc)
        category = zone_info.get("Category", {}).get("Type", "")
        is_light = category not in ("CeilingFan", "ExhaustFan", "Shade")

        # Get available controls
        available_controls = []
        if "AssociatedControlStation" in zone_info:
            available_controls = ["station"]

        # Get color tuning range if applicable
        color_tuning_range = None
        if "ColorTuningProperties" in zone_info:
            props = zone_info["ColorTuningProperties"]
            if "WhiteTuningLevelRange" in props:
                range_data = props["WhiteTuningLevelRange"]
                color_tuning_range = ColorTuningRange(
                    Min=range_data.get("Min", 2700),
                    Max=range_data.get("Max", 6500),
                )

        return Zone(
            id=zone_id,
            name=name,
            area=area_name,
            area_id=area_id,
            control_type=control_type,
            is_light=is_light,
            available_controls=available_controls,
            color_tuning_range=color_tuning_range,
        )

    # --- Zone Control ---

    async def get_zone_status(self, zone_id: str) -> dict:
        """Get current status of a zone."""
        response = await self.request(f"/zone/{zone_id}/status")
        return response.get("Body", {})

    async def set_level(
        self, zone_id: str, level: int, zone: Optional[Zone] = None
    ) -> Optional[dict]:
        """Set zone brightness level (0-100)."""
        # ColorTune/SpectrumTune zones need special handling
        if zone and zone.control_type in (
            ControlType.COLOR_TUNE,
            ControlType.SPECTRUM_TUNE,
        ):
            # Get current color to preserve it
            status = await self.get_zone_status(zone_id)
            zone_status = status.get("ZoneStatus", {})

            hue, sat, vibrancy = 0, 0, 50
            if "ColorTuningStatus" in zone_status:
                hsv = zone_status["ColorTuningStatus"].get("HSVTuningLevel", {})
                hue = hsv.get("Hue", 0)
                sat = hsv.get("Saturation", 0)
            vibrancy = zone_status.get("Vibrancy", 50)

            return await self.set_color(zone_id, level, hue, sat, vibrancy)

        # Standard zones use GoToLevel
        body = {
            "Command": {
                "CommandType": "GoToLevel",
                "Parameter": [{"Type": "Level", "Value": level}],
            }
        }
        return await self.request(
            f"/zone/{zone_id}/commandprocessor",
            "CreateRequest",
            body,
        )

    async def set_color(
        self,
        zone_id: str,
        level: int,
        hue: int,
        saturation: int,
        vibrancy: int = 50,
    ) -> Optional[dict]:
        """Set zone color (for ColorTune/SpectrumTune zones)."""
        body = {
            "Command": {
                "CommandType": "GoToSpectrumTuningLevel",
                "SpectrumTuningLevelParameters": {
                    "Level": level,
                    "Vibrancy": vibrancy,
                    "ColorTuningStatus": {
                        "HSVTuningLevel": {
                            "Hue": hue,
                            "Saturation": saturation,
                        }
                    },
                },
            }
        }
        return await self.request(
            f"/zone/{zone_id}/commandprocessor",
            "CreateRequest",
            body,
        )

    async def turn_on(
        self, zone_id: str, zone: Optional[Zone] = None
    ) -> Optional[dict]:
        """Turn zone on (to 100%)."""
        return await self.set_level(zone_id, 100, zone)

    async def turn_off(
        self, zone_id: str, zone: Optional[Zone] = None
    ) -> Optional[dict]:
        """Turn zone off (to 0%)."""
        return await self.set_level(zone_id, 0, zone)

    # --- Room Control ---

    async def set_room_level(self, area: Area, level: int, house: House) -> list[dict]:
        """Set all zones in a room to a level."""
        results = []
        for zone_id in area.zone_ids:
            zone = house.zones.get(zone_id)
            result = await self.set_level(zone_id, level, zone)
            results.append({"zone_id": zone_id, "result": result})
        return results

    # --- Button Events ---

    async def get_buttons(self) -> list[dict]:
        """Get all buttons from the bridge."""
        # Try direct /button endpoint first (Caseta/RA3)
        response = await self.request("/button")
        body = response.get("Body", {})
        buttons = body.get("Buttons", [])

        if buttons:
            return buttons

        # For HomeWorks QSX, buttons are under devices
        # Find all Pico/keypad devices via control stations
        return await self._get_buttons_from_devices()

    async def _get_buttons_from_devices(self) -> list[dict]:
        """Get buttons from devices (HomeWorks QSX style)."""
        buttons = []

        # Get all areas to find control stations
        areas = await self.get_areas()

        # Collect all unique control station hrefs
        control_stations = set()
        for area in areas:
            if not area.get("IsLeaf", False):
                continue
            area_href = area.get("href", "")
            if not area_href:
                continue
            try:
                resp = await self.request(area_href)
                body = resp.get("Body", {})
                area_data = body.get("Area", {})
                for cs in area_data.get("AssociatedControlStations", []):
                    cs_href = cs.get("href", "")
                    if cs_href:
                        control_stations.add(cs_href)
            except Exception:
                pass

        # Get devices from control stations
        pico_types = {"Pico", "Keypad", "Sunnata"}
        device_hrefs = set()

        for cs_href in control_stations:
            try:
                resp = await self.request(cs_href)
                body = resp.get("Body", {})
                station = body.get("ControlStation", {})
                for gd in station.get("AssociatedGangedDevices", []):
                    device_info = gd.get("Device", {})
                    device_type = device_info.get("DeviceType", "")
                    device_href = device_info.get("href", "")
                    # Check if it's a button-capable device
                    if device_href and any(p in device_type for p in pico_types):
                        device_hrefs.add((device_href, device_type))
            except Exception:
                pass

        # Get buttons from each device
        for device_href, device_type in device_hrefs:
            try:
                # Get button groups for this device
                resp = await self.request(f"{device_href}/buttongroup")
                body = resp.get("Body", {})
                for bg in body.get("ButtonGroups", []):
                    for btn in bg.get("Buttons", []):
                        btn_href = btn.get("href", "")
                        if btn_href:
                            # Get button details
                            btn_resp = await self.request(btn_href)
                            btn_body = btn_resp.get("Body", {})
                            button = btn_body.get("Button", {})
                            button["href"] = btn_href
                            button["DeviceType"] = device_type
                            button["DeviceHref"] = device_href
                            buttons.append(button)
            except Exception:
                pass

        return buttons

    async def get_button_groups(self) -> list[dict]:
        """Get all button groups (Picos, Keypads) from the bridge."""
        response = await self.request("/buttongroup")
        body = response.get("Body", {})
        return body.get("ButtonGroups", [])

    async def subscribe_to_button(self, button_id: str, callback) -> tuple[dict, str]:
        """
        Subscribe to button status events.

        Args:
            button_id: The button ID to subscribe to
            callback: Async callback function(response) called on events

        Returns:
            Tuple of (initial response, subscription tag)
        """
        if not self._leap:
            raise RuntimeError("Not connected to bridge")

        response, tag = await self._leap.subscribe(
            f"/button/{button_id}/status/event",
            callback,
        )
        return ({"Body": response.Body} if response.Body else {}, tag)

    async def subscribe_to_all_buttons(self, callback) -> list[str]:
        """
        Subscribe to all button events.

        Args:
            callback: Async callback function(response) called on events

        Returns:
            List of subscription tags
        """
        buttons = await self.get_buttons()
        tags = []

        for button in buttons:
            button_href = button.get("href", "")
            button_id = button_href.split("/")[-1] if button_href else ""
            if button_id:
                try:
                    _, tag = await self.subscribe_to_button(button_id, callback)
                    tags.append(tag)
                except Exception:
                    pass  # Skip buttons that fail to subscribe

        return tags

    def subscribe_unsolicited(self, callback):
        """
        Subscribe to all unsolicited events from the bridge.

        This catches events that aren't tied to a specific subscription.
        """
        if not self._leap:
            raise RuntimeError("Not connected to bridge")
        self._leap.subscribe_unsolicited(callback)


@asynccontextmanager
async def connect_bridge(config: BridgeConfig):
    """Context manager for bridge connection."""
    bridge = LutronBridge(config)
    try:
        await bridge.connect()
        yield bridge
    finally:
        await bridge.close()
