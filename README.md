# Solarman Config Manager for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/bastiitsab/ha-solarman-config-manager.svg)](https://github.com/bastiitsab/ha-solarman-config-manager/releases)
[![License](https://img.shields.io/github/license/bastiitsab/ha-solarman-config-manager.svg)](LICENSE)

Export and compare [Solarman](https://github.com/davidrapan/ha-solarman) inverter configuration settings in Home Assistant.

> [!IMPORTANT]
> This integration is a companion tool and **requires** the [ha-solarman](https://github.com/davidrapan/ha-solarman) integration by David Rapan to be installed and configured. It will not work with other Solarman integrations.

## Features

- 📥 **Export Configuration**: Capture all Solarman entity states, attributes, and metadata to timestamped JSON files
- 🔍 **Compare Exports**: Generate detailed diff reports showing exactly what changed between two configurations
- 🎯 **Config-Only Mode**: Filter out sensor readings to only show user-configurable setting changes
- 📁 **Automatic Organization**: Files saved to `/config/solarman_config_backups/` with timestamps
- 🔔 **Notifications**: Receive alerts when operations complete

## Use Cases

- **Before firmware updates** - Backup your settings before updating inverter firmware
- **Change tracking** - Compare configurations to see what changed after modifications
- **Troubleshooting** - Track when specific settings were modified
- **Documentation** - Keep historical records of your inverter configuration
- **Recovery** - Export settings before testing new configurations

## Prerequisites

This integration **only** works with the following Solarman integration:
- **[ha-solarman by davidrapan](https://github.com/davidrapan/ha-solarman)**

Ensure you have `ha-solarman` installed and your inverter is already showing up in Home Assistant before installing this manager.

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add `https://github.com/bastiitsab/ha-solarman-config-manager` as an Integration
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/solarman_config_manager` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

Add to your `configuration.yaml`:

```yaml
solarman_config_manager:
```

Then restart Home Assistant.

## Usage

### Services

The integration provides two services accessible via Developer Tools → Actions:

#### `solarman_config_manager.export_config`

Export current Solarman configuration to a JSON file.

**Parameters:**
- `filename` (optional): Custom filename (without .json extension). Auto-generated if not provided.
- `include_unavailable` (optional, default: false): Include entities that are currently unavailable.

**Example:**
```yaml
service: solarman_config_manager.export_config
data:
  filename: "before_firmware_update"
  include_unavailable: false
```

#### `solarman_config_manager.compare_exports`

Compare two export files and generate a detailed diff report.

**Parameters:**
- `file1` (required): Filename of first export (older/baseline) without .json extension
- `file2` (required): Filename of second export (newer/comparison) without .json extension
- `config_only` (optional, default: true): Only show changes to user-configurable settings (filters out sensor readings)

**Example:**
```yaml
service: solarman_config_manager.compare_exports
data:
  file1: "solarman_export_20251217_100000"
  file2: "solarman_export_20251217_110000"
  config_only: true
```

### Export Files

Files are saved to `/config/solarman_config_backups/` with format:
- Exports: `solarman_export_YYYYMMDD_HHMMSS.json`
- Comparisons: `comparison_YYYYMMDD_HHMMSS.json`

### Export File Contents

Each export contains:
- Export timestamp
- Total entity count
- For each Solarman entity:
  - Entity ID
  - Name and friendly name
  - Current state
  - All attributes
  - Device class and unit of measurement
  - Last changed/updated timestamps

### Comparison File Contents

Comparison reports include:
- Summary statistics (added, removed, changed, unchanged)
- List of added entities
- List of removed entities
- Detailed changes for modified entities with before/after values

## Dashboard Integration

You can easily add controls to your Lovelace dashboard:

### Simple Button Card

```yaml
type: button
name: Export Solarman Config
icon: mdi:download
tap_action:
  action: call-service
  service: solarman_config_manager.export_config
  service_data: {}
```

### Complete Dashboard Example

Create a new dashboard card with this YAML:

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: |
      ## 🔧 Solarman Configuration Backup
      
      Backup and compare your Solarman inverter settings.
  
  - type: entities
    title: Quick Actions
    entities:
      - type: button
        name: Export Configuration Now
        icon: mdi:download
        tap_action:
          action: call-service
          service: solarman_config_manager.export_config
  
  - type: markdown
    content: |
      ### 📋 How to Compare Configurations
      
      1. Export your current config (button above)
      2. Make changes to your inverter settings
      3. Export again with a different name
      4. Go to **Developer Tools → Actions**
      5. Search for **"Solarman Backup: Compare Two Exports"**
      6. Enter both filenames (without .json)
      7. Check `/config/solarman_config_managers/` for the comparison report
      
      **Example filenames:**
      - `solarman_export_20251217_100000`
      - `before_firmware_update`
```

### Script Integration

Add to `scripts.yaml`:

```yaml
export_solarman_config:
  alias: Export Solarman Configuration
  icon: mdi:content-save
  sequence:
    - service: solarman_config_manager.export_config
      data:
        include_unavailable: false

compare_solarman_configs:
  alias: Compare Solarman Configurations
  icon: mdi:compare
  fields:
    older_file:
      description: Older export filename (without .json)
      example: "solarman_export_20251217_100000"
    newer_file:
      description: Newer export filename (without .json)
      example: "solarman_export_20251217_110000"
  sequence:
    - service: solarman_config_manager.compare_exports
      data:
        file1: "{{ older_file }}"
        file2: "{{ newer_file }}"
        config_only: true
```

### Automation Examples

**Daily automatic backup:**
```yaml
automation:
  - alias: Daily Solarman Backup
    trigger:
      - platform: time
        at: "02:00:00"
    action:
      - service: solarman_config_manager.export_config
```

**Backup before making changes:**
```yaml
automation:
  - alias: Backup Before Solarman Changes
    trigger:
      - platform: state
        entity_id: input_button.backup_solarman
    action:
      - service: solarman_config_manager.export_config
        data:
          filename: "before_change_{{ now().strftime('%Y%m%d_%H%M%S') }}"
```

## File Management

Export files are stored in `/config/solarman_config_managers/`. You can:
- Access files via Samba/SSH
- Download via File Editor add-on
- Use in automations for backup to cloud storage
- Delete old files manually to save space

## Troubleshooting

### Services not appearing

1. Check that the integration is loaded: Developer Tools → States → search for "solarman_config_manager"
2. Verify configuration.yaml has `solarman_config_manager:` entry
3. Check logs: Settings → System → Logs → search for "solarman"
4. Restart Home Assistant

### No export files created

1. Check `/config/solarman_config_managers/` directory exists and is writable
2. Verify Solarman integration is installed and configured
3. Check Home Assistant logs for errors

### Comparison shows too many changes

Use `config_only: true` to filter out sensor readings and only show configuration changes:

```yaml
service: solarman_config_manager.compare_exports
data:
  file1: "export1"
  file2: "export2"
  config_only: true  # Only shows number, select, switch entities
```

## Requirements

- Home Assistant 2024.1.0 or newer
- [Solarman integration](https://github.com/davidrapan/ha-solarman) installed and configured

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file for details

## Credits

- Built for the [Solarman integration](https://github.com/davidrapan/ha-solarman) by [@davidrapan](https://github.com/davidrapan)
- Inspired by the need for configuration tracking and backup

## Support

- [Report Issues](https://github.com/bastiitsab/ha-solarman-config-manager/issues)
- [Feature Requests](https://github.com/bastiitsab/ha-solarman-config-manager/issues)
- [Discussions](https://github.com/bastiitsab/ha-solarman-config-manager/discussions)

---

**Note:** This integration only backs up entity states and attributes. It does not backup or restore actual inverter firmware settings. Always use your inverter's native backup functionality for firmware-level backups.
