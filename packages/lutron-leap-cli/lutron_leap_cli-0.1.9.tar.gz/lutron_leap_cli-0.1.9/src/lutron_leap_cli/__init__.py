"""
Lutron LEAP CLI - Control Lutron lighting systems via LEAP protocol.

Supports Caseta, RA2 Select, RadioRA3, and HomeWorks QSX systems.
"""

try:
    from importlib.metadata import version

    __version__ = version("lutron-leap-cli")
except Exception:
    __version__ = "0.0.0"
