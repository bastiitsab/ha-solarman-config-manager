# Solarman Config Manager Dashboard Configuration

This file contains configuration for input helpers and dashboard setup.

## Step 1: Create Input Helpers

Add these to your `configuration.yaml`:

```yaml
input_select:
  solarman_file1:
    name: "Solarman - File 1 (Older)"
    options:
      - "No files available"
    icon: mdi:file-document

  solarman_file2:
    name: "Solarman - File 2 (Newer)"
    options:
      - "No files available"
    icon: mdi:file-document

input_button:
  solarman_compare:
    name: "Compare Solarman Configs"
    icon: mdi:compare

input_boolean:
  solarman_config_only:
    name: "Solarman - Configuration Only"
    initial: true
    icon: mdi:cog-transfer
```

## Step 2: Create Automations

Add these to your `automations.yaml`:

```yaml
- id: update_solarman_file_lists
  alias: Update Solarman File Lists
  trigger:
    - platform: state
      entity_id: sensor.solarman_config_manager_files
    - platform: homeassistant
      event: start
    - platform: state
      entity_id: input_button.solarman_compare
  action:
    - service: input_select.set_options
      target:
        entity_id: input_select.solarman_file1
      data:
        options: >
          {% set files = state_attr("sensor.solarman_config_manager_files", "files") %}
          {% if files and files|length > 0 %}
            {{ ["No files available"] + files }}
          {% else %}
            ["No files available"]
          {% endif %}
    - service: input_select.set_options
      target:
        entity_id: input_select.solarman_file2
      data:
        options: >
          {% set files = state_attr("sensor.solarman_config_manager_files", "files") %}
          {% if files and files|length > 0 %}
            {{ ["No files available"] + files }}
          {% else %}
            ["No files available"]
          {% endif %}

- id: solarman_compare_trigger
  alias: Trigger Solarman Comparison
  trigger:
    - platform: state
      entity_id: input_button.solarman_compare
  action:
    - service: solarman_config_manager.compare_exports
      data:
        file1: "{{ states('input_select.solarman_file1') }}"
        file2: "{{ states('input_select.solarman_file2') }}"
        config_only: "{{ is_state('input_boolean.solarman_config_only', 'on') }}"
```

## Step 3: Complete Dashboard YAML

Copy the contents of `DASHBOARD.yaml` and paste it into a new card in your Lovelace dashboard.
      - Added: {{ data.added }}
      - Removed: {{ data.removed }}
      - Unchanged: {{ data.unchanged }}
      {% endif %}
      
  - type: conditional
    conditions:
      - entity: sensor.solarman_comparison_result
        state_not: "No comparison yet"
    card:
      type: markdown
      content: |
        ### 🔍 Detailed Changes
        
        {% set changes = state_attr('sensor.solarman_comparison_result', 'changes') %}
        {% if changes %}
        {% for entity_id, change in changes.items() %}
        **{{ entity_id }}**
        - Old: `{{ change.old_value }}`
        - New: `{{ change.new_value }}`
        {% if change.old_attributes or change.new_attributes %}
        - Attributes changed: {{ change.changed_attributes | join(', ') }}
        {% endif %}
        
        {% endfor %}
        {% else %}
        No changes detected.
        {% endif %}
```

## Alternative: Compact Version

If you want a more compact view:

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: "## 🔧 Solarman Backup"
    
  - type: horizontal-stack
    cards:
      - type: button
        name: Export Now
        icon: mdi:download
        tap_action:
          action: call-service
          service: solarman_config_manager.export_config
      - type: entity
        entity: sensor.solarman_config_manager_files
        name: Files
        
  - type: entities
    entities:
      - input_select.solarman_file1
      - input_select.solarman_file2
      - type: button
        name: Compare
        icon: mdi:compare
        tap_action:
          action: call-service
          service: solarman_config_manager.compare_exports
          service_data:
            file1: "{{ states('input_select.solarman_file1') }}"
            file2: "{{ states('input_select.solarman_file2') }}"
            config_only: true
            
  - type: entity
    entity: sensor.solarman_comparison_result
    
  - type: markdown
    content: |
      {% set changes = state_attr('sensor.solarman_comparison_result', 'changes') %}
      {% if changes %}
      ### Changes:
      {% for entity_id, change in changes.items() %}
      - **{{ entity_id.split('.')[-1] }}**: {{ change.old_value }} → {{ change.new_value }}
      {% endfor %}
      {% endif %}
```

## Notes

- The file list dropdowns update automatically when new exports are created
- The comparison result updates automatically after running a comparison
- All files are still saved to `/config/solarman_config_managers/` for direct access
- The `config_only: true` parameter filters out sensor readings, showing only configuration changes
