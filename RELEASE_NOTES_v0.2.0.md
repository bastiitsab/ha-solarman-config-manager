# Release Notes - Version 0.2.0

## 🎉 Major New Feature: Restore Configuration

Version 0.2.0 introduces the ability to restore your Solarman inverter configuration from comparison files! You can now not only track changes, but also apply or revert them with confidence.

## ✨ What's New

### Restore Configuration Service

- **New Service**: `solarman_config_manager.restore_from_comparison`
  - Apply changes forward (file1 → file2)
  - Revert changes backward (file2 → file1)
  - Dry-run mode to preview changes before applying
  - Safety confirmation requirement (`confirm: CONFIRM`)
  - Detailed notifications showing exactly what will change

### Dashboard Enhancements

- **Restore Configuration Card**: Complete UI for restore operations
  - File selection dropdown (auto-populated with comparison files)
  - Direction selector (apply/revert)
  - Dry-run toggle for safe previewing
  - One-click restore button
  
- **Restore Status Card**: Real-time operation results
  - Shows success/failed/skipped counts
  - Indicates dry-run vs actual operations
  - Updates immediately when operations complete

### New Sensor

- **sensor.solarman_config_manager_restore_result**: Tracks restore operations
  - Automatically updates via event bus
  - Stores full operation details
  - Accessible in automations and templates

### Enhanced File Tracking

- **sensor.solarman_config_manager_files** now includes:
  - `files` attribute: Export files (existing)
  - `comparison_files` attribute: Comparison files (NEW)

## 🚀 Common Workflows

### Before Firmware Update

```yaml
# 1. Backup before update
service: solarman_config_manager.export_config
data:
  filename: "before_firmware_v2_5"

# 2. Update firmware on inverter

# 3. Export after update
service: solarman_config_manager.export_config
data:
  filename: "after_firmware_v2_5"

# 4. Compare to see changes
service: solarman_config_manager.compare_exports
data:
  file1: "before_firmware_v2_5"
  file2: "after_firmware_v2_5"

# 5. If settings were lost, restore them
service: solarman_config_manager.restore_from_comparison
data:
  comparison_file: "comparison_20251217_120000"
  direction: "revert"  # Go back to before state
  dry_run: true  # Preview first!
  confirm: CONFIRM
```

### Test Configuration Safely

```yaml
# 1. Backup working config
service: solarman_config_manager.export_config
data:
  filename: "working_config"

# 2. Make experimental changes

# 3. If something goes wrong, revert instantly
service: solarman_config_manager.restore_from_comparison
data:
  comparison_file: "comparison_YYYYMMDD_HHMMSS"
  direction: "revert"
  dry_run: false
  confirm: CONFIRM
```

## 📦 Installation & Upgrade

### For New Users

Install via HACS and add to `configuration.yaml`:

```yaml
solarman_config_manager:
```

### For Existing Users (Upgrading from v0.1.x)

1. **Update via HACS** (will be available after merge)
2. **Add helper entities** (required for dashboard):
   - See [RESTORE_HELPERS.yaml](RESTORE_HELPERS.yaml) for the 3 required inputs
   - Create via Settings → Helpers or add to `configuration.yaml`
3. **Add automation** (optional but recommended):
   - See [RESTORE_AUTOMATION.yaml](RESTORE_AUTOMATION.yaml)
   - Auto-populates restore file dropdown
4. **Update dashboard**:
   - Replace with new [DASHBOARD.yaml](DASHBOARD.yaml) which includes restore controls
5. **Restart Home Assistant**

## 🛠️ Technical Details

### Service Mapping

The restore feature intelligently maps entity domains to the correct Home Assistant services:

- `number.*` entities → `number.set_value`
- `select.*` entities → `select.select_option`
- `switch.*` entities → `switch.turn_on` / `switch.turn_off`

### Safety Features

- **Confirmation Required**: Must pass `confirm: CONFIRM` to execute
- **Dry-Run Default**: Preview changes without risk
- **Detailed Notifications**: See exactly what will change before committing
- **Error Handling**: Failed entities don't stop the restore, all tracked separately

### Event-Driven Updates

- Restore operations fire `solarman_config_manager_restore_complete` event
- Sensors listen and update immediately for instant dashboard feedback

## 📚 Documentation Updates

- **README.md**: Complete workflow examples and troubleshooting
- **QUICK_START.md**: Step-by-step restore instructions
- **RESTORE_HELPERS.yaml**: Required helper entity definitions
- **RESTORE_AUTOMATION.yaml**: Automation and script for dashboard integration
- **DASHBOARD.yaml**: Full dashboard with restore controls

## 🐛 Bug Fixes

- Fixed sensor update timing for comparison results
- Improved template handling in dashboard cards
- Enhanced error messages for better troubleshooting

## ⚠️ Breaking Changes

None! This is a backward-compatible feature addition.

## 🔮 What's Next

Potential features for future releases:
- Schedule automatic restores
- Restore profiles (save favorite configurations)
- Bulk restore operations
- Integration with Home Assistant backups

## 🙏 Feedback

Please report any issues or suggestions at:
https://github.com/bastiitsab/ha-solarman-config-manager/issues

---

**Full Changelog**: https://github.com/bastiitsab/ha-solarman-config-manager/compare/v0.1.1...v0.2.0
