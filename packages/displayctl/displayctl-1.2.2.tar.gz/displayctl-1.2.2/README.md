# DisplayCtl - Display Configuration Manager for GNOME

A Python script that allows you to save and load monitor configurations on GNOME desktop environments using the D-Bus interface.

## Features

- Save current monitor configuration with a custom name
- Load and apply previously saved configurations
- List all saved configurations
- Display current monitor setup
- Delete saved configurations
- Uses GNOME's native D-Bus interface (`org.gnome.Mutter.DisplayConfig`)

## Requirements

- GNOME desktop environment (GNOME Shell)
- Python 3.8+
- python3-dbus package (automatically handled by uvx/pip)

## Installation & Usage

### Option 1: Using uvx (Recommended)

The easiest way to use DisplayCtl is with `uvx`, which handles all dependencies automatically:

```bash
# Run directly with uvx (no installation needed!)
uvx displayctl current
uvx displayctl save work
uvx displayctl load work
uvx displayctl list

# Or install for repeated use
uvx install displayctl
displayctl current
```

### Option 2: Using pip

```bash
pip install displayctl
displayctl current
```

### Option 3: From source

```bash
# Clone/download the repository
git clone <repository-url>
cd displayctl

# Install dependencies
sudo apt install python3-dbus  # or equivalent for your distro

# Run directly
python3 -m displayctl current
# or
./displayctl.py current
```

## Usage Examples

### Save Current Configuration

```bash
displayctl save work
displayctl save home
displayctl save presentation
```

### Load a Configuration

```bash
displayctl load work
displayctl load home
```

### List All Saved Configurations

```bash
displayctl list
```

### Show Current Monitor Setup

```bash
displayctl current
```

### Delete a Configuration

```bash
displayctl delete old-config
```

## Configuration Storage

Configurations are stored as JSON files in `~/.config/displayctl/`. Each configuration contains:

- Monitor information (connectors, available modes)
- Logical monitor layout (position, scale, rotation)
- Primary monitor designation
- Display properties

## Example Output

```bash
## Example Output

```bash
$ displayctl current
Current monitor configuration:
Serial: 123456

Available monitors:
  DP-1:
    Available modes: 15
      2560x1440@59.9Hz
      1920x1080@60.0Hz
      1680x1050@59.9Hz
      ... and 12 more

Active logical monitors:
  Logical monitor 1: 0,0 scale 1.0 (primary)
    - DP-1 (mode: 2560x1440@59.951171875)

$ displayctl list
Saved configurations:
  work: 2 monitor(s)
    Logical monitor 1: 0,0, scale 1.0 (primary)
      - DP-1 (mode: 2560x1440@59.951171875)
    Logical monitor 2: 2560,0, scale 1.0
      - HDMI-1 (mode: 1920x1080@60.0)
  home: 1 monitor(s)
    Logical monitor 1: 0,0, scale 1.25 (primary)
      - eDP-1 (mode: 1920x1080@60.049)
```

## Configuration Storage

Configurations are stored as JSON files in `~/.config/displayctl/`. Each configuration contains:
```

## How It Works

The script uses GNOME's D-Bus interface to:

1. **Get Current State**: Queries `org.gnome.Mutter.DisplayConfig.GetCurrentState()` to retrieve:
   - Available monitors and their supported modes
   - Current logical monitor configuration
   - Display properties

2. **Apply Configuration**: Uses `org.gnome.Mutter.DisplayConfig.ApplyMonitorsConfig()` to:
   - Set monitor positions and scales
   - Configure display modes
   - Designate primary monitor

## Troubleshooting

### "No such interface" error
This usually means you're not running GNOME Shell or the display server doesn't support the interface.

### "Permission denied" error
Make sure you're running the script as your regular user (not root) and that you have an active GNOME session.

### Configuration doesn't apply
Some monitor configurations might not be valid (e.g., unsupported resolution/refresh rate combinations). The script will try to apply the configuration but may fall back if it's not supported.

## Limitations

- Only works with GNOME desktop environment
- Requires an active GNOME session
- Some exotic monitor configurations might not be supported
- The D-Bus interface may change between GNOME versions

## License

This script is provided as-is for educational and practical use.
