"""Bridge discovery commands."""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.config import load_config
from ..output.formatter import get_formatter
from ..output.tables import bridges_table, discovery_table

console = Console()


def discover_cmd(
    timeout: int = typer.Option(
        10, "--timeout", "-t", help="Discovery timeout in seconds"
    ),
) -> None:
    """
    Scan network for Lutron LEAP bridges.

    DESCRIPTION:
        Discovers Lutron bridges on the local network using mDNS/Bonjour.
        Supports Caseta, RA2 Select, RadioRA3, and HomeWorks QSX systems.

    EXAMPLES:
        lutron discover
        lutron discover --timeout 30

    OUTPUT (--json):
        [{"ip": "192.168.1.100", "mac": "...", "model": "...", "serial": "..."}]
    """
    formatter = get_formatter()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Scanning for Lutron bridges...", total=None)
        devices = asyncio.run(_discover_bridges(timeout))

    if not devices:
        formatter.print_warning("No Lutron bridges found on the network")
        return

    table, data = discovery_table(devices)
    formatter.print_table(table, data)

    formatter.print_info(
        f"\nFound {len(devices)} device(s). Use 'lutron pair <IP>' to pair."
    )


async def _discover_bridges(timeout: int) -> list[dict]:
    """Discover bridges using pylutron-caseta."""
    try:
        # Use the discovery functionality from pylutron-caseta
        # This discovers bridges via mDNS
        devices = []

        # Try to discover using zeroconf
        try:
            from zeroconf import Zeroconf, ServiceBrowser
            import socket

            discovered = []

            class BridgeListener:
                def add_service(self, zc, type_, name):
                    info = zc.get_service_info(type_, name)
                    if info and info.addresses:
                        ip = socket.inet_ntoa(info.addresses[0])
                        discovered.append(
                            {
                                "ip": ip,
                                "name": name,
                                "model": info.server,
                            }
                        )

                def remove_service(self, zc, type_, name):
                    pass

                def update_service(self, zc, type_, name):
                    pass

            zeroconf = Zeroconf()
            listener = BridgeListener()

            # Look for Lutron services
            services = [
                "_lutron._tcp.local.",
                "_leap._tcp.local.",
            ]

            browsers = []
            for service in services:
                try:
                    browsers.append(ServiceBrowser(zeroconf, service, listener))
                except Exception:
                    pass

            await asyncio.sleep(timeout)
            zeroconf.close()

            devices = discovered

        except ImportError:
            # Fall back to simple network scan if zeroconf not available
            formatter = get_formatter()
            formatter.print_warning("zeroconf not installed - using basic network scan")
            devices = await _basic_network_scan(timeout)

        return devices

    except Exception as e:
        formatter = get_formatter()
        formatter.print_error(f"Discovery failed: {e}")
        return []


async def _basic_network_scan(timeout: int) -> list[dict]:
    """Basic network scan for LEAP port (8081)."""
    import socket

    devices = []

    # Get local network range
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        return devices

    # Scan common ranges
    base_ip = ".".join(local_ip.split(".")[:-1])

    async def check_host(ip: str) -> Optional[dict]:
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, 8081),
                timeout=1.0,
            )
            writer.close()
            await writer.wait_closed()
            return {"ip": ip, "model": "Unknown", "mac": ""}
        except Exception:
            return None

    tasks = [check_host(f"{base_ip}.{i}") for i in range(1, 255)]
    results = await asyncio.gather(*tasks)

    return [r for r in results if r is not None]


def bridges_cmd() -> None:
    """
    List configured bridges.

    DESCRIPTION:
        Shows all bridges that have been paired and configured.
        The default bridge is marked with a checkmark.

    EXAMPLES:
        lutron bridges
        lutron bridges --json

    OUTPUT (--json):
        [{"name": "home", "ip": "192.168.1.100", "port": 8081, "default": true}]
    """
    formatter = get_formatter()
    config = load_config()

    if not config.bridges:
        formatter.print_warning(
            "No bridges configured. Use 'lutron pair <IP>' to add one."
        )
        return

    table, data = bridges_table(config.bridges)
    formatter.print_table(table, data)
