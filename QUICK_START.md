# 🎉 Your Complete Solarman Config Manager Dashboard is Ready!

## ✅ What's Installed

### 1. **Two Sensors**
- `sensor.solarman_config_manager_files` - Lists all available backup files
- `sensor.solarman_config_manager_comparison_result` - Shows the latest comparison results

### 2. **Two Input Helpers**
- `input_select.solarman_file1` - Dropdown for selecting older file
- `input_select.solarman_file2` - Dropdown for selecting newer file

### 3. **One Automation**
- Auto-updates the file dropdowns whenever a new backup is created

### 4. **Dashboard Ready to Use**
- Complete YAML in `DASHBOARD.yaml`

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
3. Click **"Compare Selected Files"**
4. Results appear immediately below:
   - Summary statistics (changed, added, removed)
   - Detailed list of all changes
   - Old vs New values for each change

### View Results
- **Comparison Result** section shows summary
- **Detailed Changes** section shows exactly what changed with before/after values
- All data updates automatically - no file opening required!

## 🎯 Features

✅ **One-Click Export** - No filename typing needed  
✅ **Dropdown File Selection** - No manual filename entry  
✅ **Live Results** - Comparison shown directly in dashboard  
✅ **Auto-Update** - File lists refresh automatically  
✅ **Config-Only Mode** - Filters out sensor readings by default  
✅ **Change Tracking** - See exactly what changed with old/new values  
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

1. **Before firmware update:** Click "Export Configuration Now"
2. **Update firmware** on your inverter
3. **After update:** Click "Export Configuration Now" again
4. **Compare:** Select both files and click "Compare"
5. **Review:** See exactly what changed in the dashboard

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
