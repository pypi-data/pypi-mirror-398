"""Bridge pairing command."""

import asyncio

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.config import (
    load_config,
    save_config,
    get_certificates_dir,
)
from ..core.models import BridgeConfig
from ..output.formatter import get_formatter

console = Console()


def pair_cmd(
    ip: str = typer.Argument(..., help="IP address of the Lutron bridge"),
    name: str = typer.Option("home", "--name", "-n", help="Name for this bridge"),
    port: int = typer.Option(8081, "--port", "-p", help="LEAP port (usually 8081)"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing bridge with same name"
    ),
) -> None:
    """
    Pair with a Lutron bridge.

    DESCRIPTION:
        Initiates the pairing process with a Lutron bridge. You will need to
        press the pairing button on the bridge when prompted.

        For Caseta: Small button on the back of the bridge
        For HomeWorks QSX: Button on the processor panel

        Certificates are saved to the config directory and can be reused.

    EXAMPLES:
        lutron pair 192.168.1.100
        lutron pair 192.168.1.100 --name "living-room"
        lutron pair 192.168.1.100 --force

    OUTPUT (--json):
        {"success": true, "bridge": {"name": "home", "ip": "192.168.1.100"}}
    """
    formatter = get_formatter()
    config = load_config()

    # Check if bridge already exists
    existing = config.get_bridge(name)
    if existing and not force:
        formatter.print_error(
            f"Bridge '{name}' already exists. Use --force to overwrite."
        )
        raise typer.Exit(1)

    console.print(f"\n[bold]Pairing with Lutron bridge at {ip}[/bold]\n")
    console.print("Please press the pairing button on your bridge...")
    console.print("[dim]  Caseta: Small button on the back[/dim]")
    console.print("[dim]  HomeWorks QSX: Button on processor panel[/dim]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Waiting for pairing...", total=None)

        try:
            result = asyncio.run(_pair_bridge(ip, port, name))
        except Exception as e:
            formatter.print_error(f"Pairing failed: {e}")
            raise typer.Exit(1)

    if not result:
        formatter.print_error("Pairing failed - no certificates received")
        raise typer.Exit(1)

    ca_cert, client_cert, client_key = result

    # Save certificates
    certs_dir = get_certificates_dir()
    ca_path = certs_dir / f"{name}-ca.crt"
    cert_path = certs_dir / f"{name}.crt"
    key_path = certs_dir / f"{name}.key"

    ca_path.write_text(ca_cert)
    cert_path.write_text(client_cert)
    key_path.write_text(client_key)

    # Save bridge config
    bridge = BridgeConfig(
        name=name,
        ip=ip,
        port=port,
        default=len(config.bridges) == 0,  # First bridge is default
        ca_cert=f"{name}-ca.crt",
        client_cert=f"{name}.crt",
        client_key=f"{name}.key",
    )
    config.add_bridge(bridge)
    save_config(config)

    formatter.print_success(
        f"Paired successfully with bridge '{name}'",
        {"bridge": bridge.to_dict()},
    )
    console.print(f"\n[dim]Certificates saved to: {certs_dir}[/dim]")


async def _pair_bridge(ip: str, port: int, name: str) -> tuple[str, str, str]:
    """Perform the pairing process."""
    try:
        from pylutron_caseta.pairing import async_pair

        # Use pylutron-caseta's pairing function
        data = await async_pair(ip)

        ca_cert = data["ca"]
        client_cert = data["cert"]
        client_key = data["key"]

        return ca_cert, client_cert, client_key

    except ImportError:
        raise RuntimeError("pylutron-caseta pairing module not available")
    except Exception as e:
        raise RuntimeError(f"Pairing error: {e}")
