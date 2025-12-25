# Lutron LEAP CLI

A command-line tool for controlling Lutron lighting systems via the LEAP protocol.

## Supported Systems

- Caseta
- RA2 Select
- RadioRA3
- HomeWorks QSX

## Installation

```bash
# Using pipx (recommended)
pipx install lutron-leap-cli

# Using uv
uv tool install lutron-leap-cli

# Using pip
pip install lutron-leap-cli
```

## Quick Start

```bash
# 1. Discover Lutron bridges on your network
lutron discover

# 2. Pair with your bridge (press pairing button when prompted)
lutron pair 192.168.1.100

# 3. List all zones
lutron list

# 4. Control a light
lutron set "Kitchen Light" --level 50
lutron on "Kitchen Light"
lutron off "Kitchen Light"
```

## Commands

### Discovery & Setup

```bash
lutron discover              # Scan network for Lutron bridges
lutron pair <IP>            # Pair with a bridge
lutron bridges              # List configured bridges
lutron config               # Show configuration paths
```

### Zone Control

```bash
lutron list                 # List all zones
lutron list --rooms         # List zones grouped by room
lutron list --area kitchen  # Filter by area
lutron list --type ColorTune # Filter by control type

lutron status <zone>        # Get zone status
lutron set <zone> -l 50     # Set brightness to 50%
lutron set <zone> -l 100 --hue 30 --sat 70  # Set color
lutron on <zone>            # Turn on (100%)
lutron off <zone>           # Turn off (0%)
```

### Room Control

```bash
lutron rooms                # List all rooms
lutron room <room> -l 50    # Set all zones in room to 50%
lutron room <room> --on     # Turn all zones on
lutron room <room> --off    # Turn all zones off
```

### Scene Management

```bash
lutron snapshot <name>           # Save current state as scene
lutron snapshot <name> -a patio  # Save only zones in area
lutron recall <name>             # Restore saved scene
lutron scenes                    # List saved scenes
lutron scene show <name>         # Show scene contents
lutron scene delete <name>       # Delete a scene
```

## JSON Output

Add `--json` to any command for JSON output, useful for scripting and LLM integrations:

```bash
lutron list --json
lutron status "Kitchen Light" --json
```

## Configuration

Configuration is stored in platform-specific locations:

- **Linux**: `~/.config/lutron-leap-cli/`
- **macOS**: `~/Library/Application Support/lutron-leap-cli/`
- **Windows**: `C:\Users\<user>\AppData\Local\lutron-leap-cli\`

Scenes are saved in `./lutron-scenes/` in the current directory, allowing project-specific scene sets.

## Color Control

For zones that support color (ColorTune, SpectrumTune):

```bash
# Set color using HSV (Hue 0-360, Saturation 0-100)
lutron set "Pool Light" --level 100 --hue 200 --sat 80

# Warm white: low hue, low saturation
lutron set "Patio" -l 50 --hue 30 --sat 20

# Cool white: low saturation
lutron set "Kitchen" -l 100 --sat 0

# Colored light: high saturation
lutron set "Party" -l 100 --hue 280 --sat 100  # Purple
```

## LLM Integration

This CLI is designed to be LLM-friendly:

- `--json` output for structured data
- Detailed help with examples (`lutron --help`, `lutron <command> --help`)
- Consistent command structure
- Partial name matching for zones and rooms

## Development

```bash
# Clone and install in development mode
git clone https://github.com/peterengelbrecht/lutron-leap-cli
cd lutron-leap-cli
uv sync

# Run locally
uv run lutron --help
```

## License

MIT
