#!/usr/bin/env python3
"""
DisplayCtl - Display Configuration Manager for GNOME

A script to save and load monitor configurations using GNOME's D-Bus interface.
Uses org.gnome.Mutter.DisplayConfig for monitor management.

This module provides the command-line interface for DisplayCtl.
"""

import json
import sys
import argparse
import re
from pathlib import Path
from typing import Dict, Any, List
from enum import IntEnum

# Defer dbus import until needed
dbus = None


class ApplyMethod(IntEnum):
    """Methods for applying monitor configurations via D-Bus."""
    VERIFY = 0      # Only verify configuration without applying
    TEMPORARY = 1   # Apply configuration temporarily (default)
    PERSISTENT = 2  # Apply configuration permanently


def _ensure_dbus():
    """Import dbus module when needed."""
    global dbus
    if dbus is None:
        try:
            import dbus as _dbus
            dbus = _dbus
        except ImportError:
            print("Error: python3-dbus is required. "
                  "Install with: sudo apt install python3-dbus")
            sys.exit(1)
    return dbus


class MonitorConfigManager:
    """Manages monitor configurations using GNOME's D-Bus interface."""

    def __init__(self):
        self.bus = None
        self.display_config = None
        self.interface = None

        # Create config directory
        self.config_dir = Path.home() / '.config' / 'displayctl'
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_dbus_connection(self):
        """Ensure D-Bus connection is established."""
        if self.interface is None:
            _ensure_dbus()
            self.bus = dbus.SessionBus()
            self.display_config = self.bus.get_object(
                'org.gnome.Mutter.DisplayConfig',
                '/org/gnome/Mutter/DisplayConfig'
            )
            self.interface = dbus.Interface(
                self.display_config,
                'org.gnome.Mutter.DisplayConfig'
            )

    def _safe_dict_conversion(self, properties):
        """Safely convert D-Bus properties to a dictionary."""
        try:
            if isinstance(properties, dict):
                return dict(properties)
            else:
                # Handle D-Bus arrays/structs
                return dict(properties) if properties else {}
        except (ValueError, TypeError):
            return {}

    def get_current_state(self) -> Dict[str, Any]:
        """Get the current monitor configuration state."""
        self._ensure_dbus_connection()
        try:
            # Get current resources (monitors, logical monitors, etc.)
            result = self.interface.GetCurrentState()
            serial, monitors, logical_monitors, properties = result

            monitors_ = self._parse_monitors(monitors)
            return {
                'serial': int(serial),
                'monitors': monitors_,
                'logical_monitors': self._parse_logical_monitors(
                    logical_monitors, monitors_),
                'properties': dict(properties)
            }
        except Exception as e:
            if 'dbus' in str(type(e).__module__):
                raise RuntimeError(f"Failed to get current state: {e}")
            else:
                raise

    def _parse_monitors(self, monitors) -> List[Dict[str, Any]]:
        """Parse monitor information from D-Bus response."""
        parsed_monitors = []

        for monitor in monitors:
            data1, modes, properties = monitor
            connector, _vendor, _product, _serial = data1

            # Extract clean connector name from D-Bus structure
            connector_name = str(connector)

            parsed_monitor = {
                'connector': connector_name,
                'modes': [],
                'properties': self._safe_dict_conversion(properties)
            }

            for mode in modes:
                (mode_id, width, height, refresh_rate, preferred_scale,
                 supported_scales, mode_properties) = mode

                parsed_mode = {
                    'id': str(mode_id),
                    'width': int(width),
                    'height': int(height),
                    'refresh_rate': float(refresh_rate),
                    'preferred_scale': float(preferred_scale),
                    'supported_scales': [float(s) for s in supported_scales],
                    'properties': self._safe_dict_conversion(mode_properties)
                }
                parsed_monitor['modes'].append(parsed_mode)

            parsed_monitors.append(parsed_monitor)

        return parsed_monitors

    def get_mode_for_connector(self, connector: str, monitors) -> Any:
        for m in monitors:
            if m["connector"] == connector:
                for mm in m["modes"]:
                    if mm["properties"].get("is-current", False):
                        return mm["id"]
        return None

    def _parse_logical_monitors(self, logical_monitors, monitors) -> List[
            Dict[str, Any]]:
        """Parse logical monitor information from D-Bus response."""
        parsed_logical = []

        for logical_monitor in logical_monitors:
            (x, y, scale, transform, primary, monitor_specs,
             properties) = logical_monitor

            parsed_logical_monitor = {
                'x': int(x),
                'y': int(y),
                'scale': float(scale),
                'transform': int(transform),
                'primary': bool(primary),
                'monitors': [],
                'properties': self._safe_dict_conversion(properties)
            }

            for monitor_spec in monitor_specs:
                try:
                    connector, _vendor, _product, _serial = monitor_spec

                    parsed_logical_monitor['monitors'].append({
                        'connector': connector,
                        'mode_id': self.get_mode_for_connector(connector,
                                                               monitors),
                    })
                except (IndexError, ValueError, TypeError) as e:
                    print(f"Warning: Failed to parse monitor spec: {e}")
            parsed_logical.append(parsed_logical_monitor)

        return parsed_logical

    def save_config(self, name: str) -> None:
        """Save the current monitor configuration."""
        try:
            config = self.get_current_state()
            config_file = self.config_dir / f"{name}.json"

            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)

            print(f"Configuration saved as '{name}' to {config_file}")

        except Exception as e:
            print(f"Error saving configuration: {e}")
            sys.exit(1)

    def load_config(self, name: str, dry_run: bool = False,
                    method: ApplyMethod = ApplyMethod.TEMPORARY) -> None:
        """Load and apply a saved monitor configuration.
        
        Args:
            name: Name of the configuration to load
            dry_run: If True, show what would be applied without applying
            method: Configuration method (VERIFY, TEMPORARY, PERSISTENT)
        """
        config_file = self.config_dir / f"{name}.json"

        if not config_file.exists():
            print(f"Configuration '{name}' not found in {self.config_dir}")
            sys.exit(1)

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)

            if dry_run:
                self._show_config_preview(config, name)
            else:
                self._apply_config(config, method)
                print(f"Configuration '{name}' applied successfully")

        except Exception as e:
            print(f"Error loading configuration: {e}")
            sys.exit(1)

    def _show_config_preview(self, config: Dict[str, Any], name: str) -> None:
        """Show what a configuration would do without applying it."""
        print(f"Configuration '{name}' would apply:")
        print(f"Serial: {config['serial']}")

        for i, lm in enumerate(config.get('logical_monitors', [])):
            primary = " (primary)" if lm.get('primary', False) else ""
            print(f"  Logical monitor {i+1}: {lm['x']},{lm['y']} "
                  f"scale {lm['scale']}{primary}")
            for monitor in lm.get('monitors', []):
                print(f"    - {monitor['connector']} "
                      f"(mode: {monitor['mode_id']})")

        print("\nUse 'load' without --dry-run to apply this configuration.")

    def _apply_config(self, config: Dict[str, Any],
                      method: ApplyMethod = ApplyMethod.TEMPORARY) -> None:
        """Apply a monitor configuration using D-Bus.
        
        Args:
            config: The monitor configuration to apply
            method: Configuration method (VERIFY, TEMPORARY, PERSISTENT)
        """
        self._ensure_dbus_connection()

        try:
            # Get current state to validate monitors are still available
            current_state = self.get_current_state()
            current_monitors = {
                m['connector']: m for m in current_state['monitors']
            }

            # Validate that all monitors in the config are still available
            config_monitors = set()
            for lm in config.get('logical_monitors', []):
                for monitor in lm.get('monitors', []):
                    config_monitors.add(monitor['connector'])

            missing_monitors = config_monitors - set(current_monitors.keys())
            if missing_monitors:
                missing = ', '.join(missing_monitors)
                print(f"Warning: Monitors not currently available: {missing}")
                print("Configuration cannot be applied.")
                return

            # Convert saved config to D-Bus format
            logical_monitors_dbus = []

            for lm in config.get('logical_monitors', []):
                # Build monitor specs for this logical monitor
                monitor_specs = []

                for monitor in lm.get('monitors', []):
                    connector = monitor['connector']
                    mode_id = monitor['mode_id']
                    properties = monitor.get('properties', {})

                    # Validate the mode still exists
                    current_monitor = current_monitors.get(connector)
                    if current_monitor:
                        available_modes = {
                            m['id']: m for m in current_monitor['modes']
                        }
                        if mode_id not in available_modes:
                            warning_msg = (
                                f"Warning: Mode {mode_id} no longer "
                                f"available for {connector}")
                            print(warning_msg)
                            # Try to find a similar mode
                            saved_mode = None
                            for saved_lm in config.get('logical_monitors', []):
                                for saved_mon in saved_lm.get('monitors', []):
                                    if saved_mon['connector'] == connector:
                                        # Look for the mode in original config
                                        for config_monitor in config.get(
                                                'monitors', []):
                                            if (config_monitor['connector'] ==
                                                    connector):
                                                for mode in config_monitor[
                                                        'modes']:
                                                    if mode['id'] == mode_id:
                                                        saved_mode = mode
                                                        break

                            if saved_mode:
                                # Try to find a mode with matching resolution
                                for mode in current_monitor['modes']:
                                    if (mode['width'] == saved_mode['width']
                                            and mode['height'] ==
                                            saved_mode['height']):
                                        alt_msg = (
                                            f"Using alternative mode "
                                            f"{mode['id']} for "
                                            f"{connector}")
                                        print(alt_msg)
                                        mode_id = mode['id']
                                        break
                                else:
                                    no_alt_msg = (
                                        f"No suitable alternative "
                                        f"mode found for {connector}")
                                    print(no_alt_msg)
                                    return

                    # Create monitor spec tuple
                    monitor_spec = (
                        dbus.String(connector),
                        dbus.String(mode_id),
                        dbus.Dictionary(properties, signature='sv')
                    )
                    monitor_specs.append(monitor_spec)

                # Create logical monitor tuple
                logical_monitor = (
                    dbus.Int32(lm['x']),
                    dbus.Int32(lm['y']),
                    dbus.Double(lm['scale']),
                    dbus.UInt32(lm['transform']),
                    dbus.Boolean(lm['primary']),
                    dbus.Array(monitor_specs, signature='(ssa{sv})'),
                )
                logical_monitors_dbus.append(logical_monitor)

            # Convert to D-Bus array
            logical_monitors_array = dbus.Array(
                logical_monitors_dbus, signature='(iiduba(ssa{sv})a{sv})')

            # Apply the configuration
            method_value = dbus.UInt32(method)
            properties = dbus.Dictionary(
                config.get('properties', {}), signature='sv')

            print("Applying monitor configuration...")
            method_names = {
                ApplyMethod.VERIFY: "verify",
                ApplyMethod.TEMPORARY: "temporary",
                ApplyMethod.PERSISTENT: "persistent"
            }
            print(f"Using method: {method_names.get(method, method)}")
            self.interface.ApplyMonitorsConfig(
                current_state['serial'],
                method_value,
                logical_monitors_array,
                properties
            )
            print("Configuration applied successfully!")

        except Exception as e:
            if 'dbus' in str(type(e).__module__):
                print(f"D-Bus error applying configuration: {e}")
                print("This may indicate:")
                print("- Invalid mode IDs or monitor configuration")
                print("- Monitors have been disconnected or changed")
                print("- Permission issues with D-Bus")
            else:
                print(f"Error applying configuration: {e}")
            raise

    def list_configs(self) -> None:
        """List all saved configurations."""
        config_files = list(self.config_dir.glob("*.json"))

        if not config_files:
            print(f"No configurations found in {self.config_dir}")
            return

        print("Saved configurations:")
        for config_file in sorted(config_files):
            name = config_file.stem
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)

                logical_monitors = config.get('logical_monitors', [])
                monitor_count = sum(
                    len(lm.get('monitors', [])) for lm in logical_monitors)

                print(f"  {name}: {monitor_count} monitor(s)")

                for i, lm in enumerate(logical_monitors):
                    primary = " (primary)" if lm.get('primary', False) else ""
                    print(f"    Logical monitor {i+1}: {lm['x']}x{lm['y']}, "
                          f"scale {lm['scale']}{primary}")
                    for monitor in lm.get('monitors', []):
                        print(f"      - {monitor['connector']} "
                              f"(mode: {monitor['mode_id']})")

            except Exception as e:
                print(f"  {name}: (error reading file: {e})")

    def show_current(self) -> None:
        """Show current monitor configuration."""
        try:
            config = self.get_current_state()

            print("Current monitor configuration:")
            print(f"Serial: {config['serial']}")

            print("\nAvailable monitors:")
            for monitor in config['monitors']:
                print(f"  {monitor['connector']}:")
                print(f"    Available modes: {len(monitor['modes'])}")
                for mode in monitor['modes'][:3]:  # Show first 3 modes
                    refresh = mode['refresh_rate']
                    print(f"      {mode['width']}x{mode['height']}"
                          f"@{refresh:.1f}Hz")
                if len(monitor['modes']) > 3:
                    remaining = len(monitor['modes']) - 3
                    print(f"      ... and {remaining} more")

            print("\nActive logical monitors:")
            for i, lm in enumerate(config['logical_monitors']):
                primary = " (primary)" if lm['primary'] else ""
                print(f"  Logical monitor {i+1}: {lm['x']},{lm['y']} "
                      f"scale {lm['scale']}{primary}")
                for monitor in lm['monitors']:
                    print(f"    - {monitor['connector']} "
                          f"(mode: {monitor['mode_id']})")

        except Exception as e:
            print(f"Error getting current configuration: {e}")
            # Add debug information
            import traceback
            print("Debug information:")
            traceback.print_exc()
            sys.exit(1)

    def delete_config(self, name: str) -> None:
        """Delete a saved configuration."""
        config_file = self.config_dir / f"{name}.json"

        if not config_file.exists():
            print(f"Configuration '{name}' not found")
            sys.exit(1)

        try:
            config_file.unlink()
            print(f"Configuration '{name}' deleted")
        except Exception as e:
            print(f"Error deleting configuration: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="DisplayCtl - Display Configuration Manager for GNOME",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s save work                 # Save current config as 'work'
  %(prog)s load work                 # Load 'work' config (temporary)
  %(prog)s load work --persistent    # Load 'work' config (persistent)
  %(prog)s load work --temp          # Load 'work' config (temporary)
  %(prog)s load work --verify        # Verify 'work' config only
  %(prog)s load work --method 2      # Load 'work' config (persistent)
  %(prog)s list                      # List all saved configs
  %(prog)s current                   # Show current monitor setup
  %(prog)s delete work               # Delete 'work' config
        """
    )

    subparsers = parser.add_subparsers(
        dest='command', help='Available commands')

    # Save command
    save_parser = subparsers.add_parser(
        'save', help='Save current monitor configuration')
    save_parser.add_argument('name', help='Name for the configuration')

    # Load command
    load_parser = subparsers.add_parser(
        'load', help='Load and apply a saved configuration')
    load_parser.add_argument('name', help='Name of the configuration to load')
    load_parser.add_argument('--dry-run', action='store_true',
                             help='Show what would be applied '
                                  'without applying')
    
    # Method selection - either numeric or alias
    method_group = load_parser.add_mutually_exclusive_group()
    method_group.add_argument('--method', type=int,
                              choices=[ApplyMethod.VERIFY,
                                       ApplyMethod.TEMPORARY,
                                       ApplyMethod.PERSISTENT],
                              default=ApplyMethod.TEMPORARY,
                              help='Configuration method: 0=verify, '
                                   '1=temporary (default), 2=persistent')
    method_group.add_argument('--verify', action='store_const',
                              const=ApplyMethod.VERIFY,
                              dest='method',
                              help='Only verify configuration without '
                                   'applying')
    method_group.add_argument('--temporary', '--temp', action='store_const',
                              const=ApplyMethod.TEMPORARY, dest='method',
                              help='Apply configuration temporarily')
    method_group.add_argument('--persistent', action='store_const',
                              const=ApplyMethod.PERSISTENT,
                              dest='method',
                              help='Apply configuration permanently')

    # List command
    subparsers.add_parser('list', help='List all saved configurations')

    # Current command
    subparsers.add_parser('current', help='Show current monitor configuration')

    # Delete command
    delete_parser = subparsers.add_parser(
        'delete', help='Delete a saved configuration')
    delete_parser.add_argument(
        'name', help='Name of the configuration to delete')

    args = parser.parse_args()

    try:
        if not args.command:
            parser.print_help()
            sys.exit(1)

        manager = MonitorConfigManager()

        if args.command == 'save':
            manager.save_config(args.name)
        elif args.command == 'load':
            dry_run = getattr(args, 'dry_run', False)
            method_value = getattr(args, 'method', ApplyMethod.TEMPORARY)
            # Ensure we have an ApplyMethod enum value
            if isinstance(method_value, int):
                method = ApplyMethod(method_value)
            else:
                method = method_value
            manager.load_config(args.name, dry_run, method)
        elif args.command == 'list':
            manager.list_configs()
        elif args.command == 'current':
            manager.show_current()
        elif args.command == 'delete':
            manager.delete_config(args.name)

    except KeyboardInterrupt:
        print("\nOperation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
