# 🎉 Your Complete Solarman Config Manager Dashboard is Ready!

## ✅ What's Installed

### 1. **Sensors**
- `sensor.solarman_config_manager_files` - Lists all available backup files
- `sensor.solarman_config_manager_comparison_result` - Shows the latest comparison results
- `sensor.solarman_config_manager_restore_result` - Shows restore operation results

### 2. **Input Helpers (for Compare)**
- `input_select.solarman_file1` - Dropdown for selecting older file
- `input_select.solarman_file2` - Dropdown for selecting newer file
- `input_boolean.solarman_config_only` - Toggle config-only mode

### 3. **Input Helpers (for Restore)** - Optional
- `input_select.solarman_restore_file` - Dropdown for selecting comparison file
- `input_select.solarman_restore_direction` - Choose apply or revert
- `input_boolean.solarman_restore_dry_run` - Enable dry-run preview

See [RESTORE_HELPERS.yaml](RESTORE_HELPERS.yaml) for setup.

### 4. **Automations**
- Auto-updates the file dropdowns whenever a new backup is created
- Optional: Updates restore file list (see [RESTORE_AUTOMATION.yaml](RESTORE_AUTOMATION.yaml))

### 5. **Dashboard Ready to Use**
- Complete YAML in `DASHBOARD.yaml` with compare and restore controls

## 🚀 How to Add the Dashboard

### Option 1: Add to Existing Dashboard

1. Go to your Home Assistant dashboard
2. Click the ✏️ (Edit) button in the top right
3. Click "+ ADD CARD" button
4. Click "Show Code Editor" (three dots menu → Show Code Editor)
5. Copy and paste the entire contents of [DASHBOARD.yaml](DASHBOARD.yaml)
6. Click "SAVE"

### Option 2: Create New Dashboard Tab

1. Go to Settings → Dashboards
2. Click "+ ADD DASHBOARD"
3. Choose "New dashboard from scratch"
4. Name it "Solarman Backup"
5. Once created, edit it and add the YAML from [DASHBOARD.yaml](DASHBOARD.yaml)

## 📖 How to Use

### Export a Backup
1. Click the **"Export Configuration Now"** button
2. Wait for notification
3. The file dropdown lists will update automatically

### Compare Two Backups
1. Select an older file from **"File 1 (Older)"** dropdown
2. Select a newer file from **"File 2 (Newer)"** dropdown
3. Toggle **"Configuration Only"** to filter sensor readings (recommended)
4. Click **"Compare Selected Files"**
5. Results appear immediately below:
   - Summary statistics (changed, added, removed)
   - Detailed list of all changes
   - Old vs New values for each change

### Restore Configuration (Optional - requires helpers)

If you've set up the restore helpers:

1. **Select comparison file** from the restore dropdown
2. **Choose direction:**
   - `revert` - Go back to File 1 (older) values
   - `apply` - Apply File 2 (newer) values
3. **Enable Dry Run** to preview changes first (recommended)
4. Click **"Restore Configuration"**
5. Review the notification showing what will change
6. If satisfied, disable Dry Run and click Restore again to apply

### View Results
- **Comparison Result** section shows summary
- **Detailed Changes** section shows exactly what changed with before/after values
- **Restore Status** section shows restore operation results
- All data updates automatically - no file opening required!

## 🎯 Features

✅ **One-Click Export** - No filename typing needed  
✅ **Dropdown File Selection** - No manual filename entry  
✅ **Live Results** - Comparison shown directly in dashboard  
✅ **Auto-Update** - File lists refresh automatically  
✅ **Config-Only Mode** - Filters out sensor readings by default  
✅ **Change Tracking** - See exactly what changed with old/new values  
✅ **Restore with Dry-Run** - Preview and apply configuration changes safely  
✅ **HACS Compatible** - Everything in custom_components directory  

## 📁 Files Still Saved

All backup and comparison files are still saved to:
```
/config/solarman_config_managers/
```

You can access them directly if needed via:
- File Editor add-on
- Samba/SSH
- Studio Code Server
- etc.

## 🔧 Advanced Usage

### Export with Custom Filename
Use Developer Tools → Actions:
```yaml
service: solarman_config_manager.export_config
data:
  filename: "before_firmware_update"
```

### Include Unavailable Entities
```yaml
service: solarman_config_manager.export_config
data:
  include_unavailable: true
```

### Show All Changes (Including Sensor Readings)
```yaml
service: solarman_config_manager.compare_exports
data:
  file1: "solarman_export_20251217_100000"
  file2: "solarman_export_20251217_110000"
  config_only: false  # Shows everything
```

## 🎨 Customization

The dashboard YAML can be customized:
- Change colors/icons
- Rearrange sections
- Add/remove fields
- Adjust formatting

All entities are available for use in your own automations too!

## 📊 Example Workflow

### Basic Backup & Compare
1. **Before firmware update:** Click "Export Configuration Now"
2. **Update firmware** on your inverter
3. **After update:** Click "Export Configuration Now" again
4. **Compare:** Select both files and click "Compare"
5. **Review:** See exactly what changed in the dashboard

### Advanced: Restore Lost Settings
1. **Before changes:** Export current config
2. **Make changes** to your inverter
3. **Export again** to capture changes
4. **Compare** to see what changed
5. **Dry-run restore** to preview reverting changes
6. **Apply restore** if needed to undo changes

## 🆘 Troubleshooting

### Dropdowns show "No files available"
- Make sure you've exported at least one backup
- Wait 30 seconds for sensors to update
- Check that `/config/solarman_config_managers/` directory exists

### Comparison Result shows "No comparison yet"
- You need to run a comparison first
- Select two files and click "Compare Selected Files"

### Services not appearing
- Check logs for errors
- Restart Home Assistant
- Verify Solarman integration is installed

## 🎓 Next Steps

- Create automatic daily backups with an automation
- Export before making any inverter changes
- Track configuration changes over time
- Share your setup with other Solarman users!

Enjoy your new convenient backup dashboard! 🚀
