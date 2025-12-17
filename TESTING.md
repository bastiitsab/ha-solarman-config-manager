## Testing the Dashboard

The sensors ARE loading.

Try these steps:

1. **Go to Developer Tools → States**
2. **Search for:** `solarman`
3. **You should see:**
   - `sensor.solarman_config_manager_files`
   - `sensor.solarman_config_manager_comparison_result`
   - `input_select.solarman_file1`
   - `input_select.solarman_file2`

If the sensors don't appear in States, try:

1. **Go to Settings → Devices & Services**  
2. **Search for "Solarman Config Manager"**
3. **Check if integration is loaded**

**To test the dashboard:**
1. First create an export via Developer Tools → Actions
2. Search for "solarman_config_manager.export_config"
3. Run it
4. Then check if `sensor.solarman_config_manager_files` updates with the file list
