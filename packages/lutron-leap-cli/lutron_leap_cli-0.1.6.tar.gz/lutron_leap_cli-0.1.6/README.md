# Lutron LEAP CLI

A command-line tool for controlling Lutron lighting systems via the LEAP protocol.

## Supported Systems

- Caseta (requires Smart Bridge Pro)
- RA2 Select
- RadioRA3
- HomeWorks QSX

## Installation

```bash
# Using uv (recommended)
uv tool install lutron-leap-cli

# Using pipx
pipx install lutron-leap-cli

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
lutron pair <IP>             # Pair with a bridge
lutron bridges               # List configured bridges
lutron config                # Show configuration paths
lutron refresh               # Refresh zone cache from bridge
```

### Zone Control

```bash
lutron list                  # List all zones
lutron list --rooms          # List zones grouped by room
lutron list --area kitchen   # Filter by area
lutron list --type ColorTune # Filter by control type

lutron status <zone>         # Get zone status
lutron set <zone> -l 50      # Set brightness to 50%
lutron set <zone> -l 100 --hue 30 --sat 70  # Set color
lutron on <zone>             # Turn on (100%)
lutron off <zone>            # Turn off (0%)
```

### Room Control

```bash
lutron rooms                 # List all rooms
lutron room <room> -l 50     # Set all zones in room to 50%
lutron room <room> --on      # Turn all zones on
lutron room <room> --off     # Turn all zones off
```

### Scene Management

Scenes capture the current state of your lights and can be recalled later.
Supports both YAML and JSON formats.

```bash
lutron snapshot <name>              # Save current state as scene
lutron snapshot <name> -a patio     # Save only zones in area
lutron snapshot ./path/to/scene.yaml  # Save to specific path
lutron recall <name>                # Restore saved scene
lutron recall ./path/to/scene.yaml  # Recall from specific path
lutron scenes                       # List saved scenes
lutron scene show <name>            # Show scene contents
lutron scene delete <name>          # Delete a scene
```

Scene files are saved as YAML in `./lutron-scenes/` by default:

```yaml
name: evening
created_at: '2025-12-22T19:30:00'
area_filter: kitchen
zones:
  '1234':
    level: 50
  '5678':
    level: 25
    color:
      hue: 30
      saturation: 60
```

### Button Events

Watch for button presses from Pico remotes and keypads, and trigger actions.

**Note:** Only Pico remotes and Keypads emit button events. Hardwired switches do NOT emit button events via LEAP.

```bash
lutron buttons               # List all buttons with IDs
lutron watch --debug         # See all button events (for testing)
lutron watch                 # Execute configured actions
lutron watch -c ./buttons.yaml  # Use specific config file
```

#### Button Configuration

Create `lutron-buttons.yaml` in your scenes directory:

```yaml
buttons:
  # Simple scene trigger
  - button: 42
    press: dining-intimate

  # Toggle between scenes
  - button: 43
    press:
      toggle:
        - scene-bright
        - scene-dim

  # Different actions per event type
  - button: 44
    press: evening
    double_tap: party-mode
    long_press:
      dim:
        zone: "Kitchen"
        direction: down
        step: 10

  # Room control
  - button: 45
    press:
      room: "Living Room"
      level: 100

settings:
  long_press_ms: 500   # Long press detection threshold
  dim_step: 10         # Default dimming step
```

## JSON Output

Add `--json` to any command for JSON output, useful for scripting and LLM integrations:

```bash
lutron list --json
lutron status "Kitchen Light" --json
lutron buttons --json
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

# Common commands (requires just: brew install just)
just install     # Install from PyPI
just dev         # Install local dev version
just publish     # Build & publish to PyPI
just patch       # Bump patch version
just fmt         # Format code with ruff
just lint        # Lint code with ruff

# Or use uv directly
uv sync
uv run lutron --help
```

## License

MIT
