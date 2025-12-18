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
- 🔄 **Restore Configuration**: Apply or revert changes from comparison files with dry-run preview
- 🎯 **Config-Only Mode**: Filter out sensor readings to only show user-configurable setting changes
- 📁 **Automatic Organization**: Files saved to `/config/solarman_config_backups/` with timestamps
- 🔔 **Notifications**: Receive alerts when operations complete

## Use Cases

- **Before firmware updates** - Backup your settings before updating inverter firmware
- **Change tracking** - Compare configurations to see what changed after modifications
- **Restore settings** - Revert to previous configurations or apply changes from one backup to another
- **Troubleshooting** - Track when specific settings were modified
- **Documentation** - Keep historical records of your inverter configuration
- **Recovery** - Quickly restore settings after accidental changes

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

The integration provides three services accessible via Developer Tools → Actions:

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

#### `solarman_config_manager.restore_from_comparison`

Restore configuration from a comparison file. Can apply changes forward or revert changes backward.

**Parameters:**
- `comparison_file` (required): Filename of comparison file (without .json extension)
- `direction` (required): Either `apply` (file1 → file2) or `revert` (file2 → file1)
- `dry_run` (optional, default: false): Preview changes without applying them
- `confirm` (required): Must be set to `CONFIRM` to proceed (safety feature)

**Example:**
```yaml
# Preview changes before applying
service: solarman_config_manager.restore_from_comparison
data:
  comparison_file: "comparison_20251217_120000"
  direction: "revert"
  dry_run: true
  confirm: CONFIRM

# Actually apply the restore
service: solarman_config_manager.restore_from_comparison
data:
  comparison_file: "comparison_20251217_120000"
  direction: "revert"
  dry_run: false
  confirm: CONFIRM
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

See [DASHBOARD.yaml](DASHBOARD.yaml) for a full-featured dashboard with:
- Export controls
- File selection for comparison
- Detailed diff display
- **Restore controls** with dry-run preview
- Status indicators

To use the complete dashboard:

1. **Create helper entities** (see [RESTORE_HELPERS.yaml](RESTORE_HELPERS.yaml)):
   - Copy the helper definitions to your `configuration.yaml`
   - Or create them via Settings → Devices & Services → Helpers

2. **Add the automation** (see [RESTORE_AUTOMATION.yaml](RESTORE_AUTOMATION.yaml)):
   - Copy to your `automations.yaml`
   - Or create via Settings → Automations & Scenes

3. **Add the dashboard**:
   - Copy the contents of [DASHBOARD.yaml](DASHBOARD.yaml)
   - Paste into a new Lovelace dashboard card

## Common Workflows

### Backup Before Firmware Update

```yaml
# 1. Export current config
service: solarman_config_manager.export_config
data:
  filename: "before_firmware_v2_5"

# 2. Update firmware via inverter interface

# 3. Export new config  
service: solarman_config_manager.export_config
data:
  filename: "after_firmware_v2_5"

# 4. Compare
service: solarman_config_manager.compare_exports
data:
  file1: "before_firmware_v2_5"
  file2: "after_firmware_v2_5"
  config_only: true

# 5. If settings were lost, restore them
service: solarman_config_manager.restore_from_comparison
data:
  comparison_file: "comparison_20251217_120000"
  direction: "revert"  # Go back to "before" state
  dry_run: true  # Preview first
  confirm: CONFIRM
```

### Test Configuration Changes Safely

```yaml
# 1. Backup current working config
service: solarman_config_manager.export_config
data:
  filename: "working_config"

# 2. Make experimental changes via HA

# 3. Export experimental config
service: solarman_config_manager.export_config
data:
  filename: "experimental_config"

# 4. Compare to see all changes
service: solarman_config_manager.compare_exports
data:
  file1: "working_config"
  file2: "experimental_config"

# 5a. If something went wrong, revert
service: solarman_config_manager.restore_from_comparison
data:
  comparison_file: "comparison_20251217_120000"
  direction: "revert"
  dry_run: false
  confirm: CONFIRM

# 5b. Or keep the changes and document them
# (comparison file serves as documentation)
```

### Daily Backup with Quick Restore

Set up daily backups, then quickly restore if needed:

```yaml
# Automation for daily backup
automation:
  - alias: Daily Solarman Backup
    trigger:
      - platform: time
        at: "02:00:00"
    action:
      - service: solarman_config_manager.export_config

# When you need to restore yesterday's settings:
# 1. Compare today vs yesterday
service: solarman_config_manager.compare_exports
data:
  file1: "solarman_export_20251216_020000"  # Yesterday
  file2: "solarman_export_20251217_020000"  # Today

# 2. Preview the restore
service: solarman_config_manager.restore_from_comparison
data:
  comparison_file: "comparison_20251217_080000"
  direction: "revert"  # Go back to yesterday
  dry_run: true
  confirm: CONFIRM

# 3. Apply the restore
service: solarman_config_manager.restore_from_comparison
data:
  comparison_file: "comparison_20251217_080000"
  direction: "revert"
  dry_run: false
  confirm: CONFIRM
```

## Script Integration

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

### Restore operation fails

1. Always use `dry_run: true` first to preview changes
2. Check that the comparison file exists in `/config/solarman_config_backups/`
3. Ensure you've entered `confirm: CONFIRM` exactly (safety requirement)
4. Verify entities in the comparison are still available
5. Check logs for specific errors: Settings → System → Logs

### Restore doesn't show what will change

The notification shows a summary and lists the first 10 entities with their target values. For full details, check the dry-run logs or the comparison file.

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
