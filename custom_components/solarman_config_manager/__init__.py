"""Solarman Config Manager Integration."""
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import entity_registry as er

from .const import (
    DOMAIN,
    SERVICE_EXPORT_CONFIG,
    SERVICE_COMPARE_EXPORTS,
    DEFAULT_BACKUP_DIR,
    SOLARMAN_DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

EXPORT_CONFIG_SCHEMA = vol.Schema({
    vol.Optional("filename"): cv.string,
    vol.Optional("include_unavailable", default=False): cv.boolean,
})

COMPARE_EXPORTS_SCHEMA = vol.Schema({
    vol.Required("file1"): cv.string,
    vol.Required("file2"): cv.string,
    vol.Optional("config_only", default=True): cv.boolean,
})


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Solarman Config Manager component."""
    _LOGGER.info("Setting up Solarman Config Manager integration")
    
    # Store hass instance in domain data
    hass.data.setdefault(DOMAIN, {})
    
    # Create backup directory
    backup_dir = Path(hass.config.path(DEFAULT_BACKUP_DIR))
    backup_dir.mkdir(exist_ok=True)
    
    async def handle_export_config(call: ServiceCall) -> None:
        """Handle the export_config service call."""
        filename = call.data.get("filename")
        include_unavailable = call.data.get("include_unavailable", False)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"solarman_export_{timestamp}.json"
        
        # Sanitize filename - remove path separators and dangerous characters
        filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        filename = filename.strip()
        
        if not filename:
            filename = f"solarman_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        if not filename.endswith(".json"):
            filename += ".json"
        
        # Ensure filename stays within backup directory
        filepath = backup_dir / filename
        if not filepath.resolve().is_relative_to(backup_dir.resolve()):
            _LOGGER.error(f"Security: Attempted path traversal with filename: {filename}")
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": "Invalid filename provided. Please use only alphanumeric characters.",
                    "title": "Solarman Export Failed",
                    "notification_id": "solarman_config_manager_export_error",
                },
            )
            return
        
        _LOGGER.info(f"Exporting Solarman configuration to {filepath}")
        
        # Get entity registry
        entity_reg = er.async_get(hass)
        
        # Collect all Solarman entities
        solarman_entities = []
        for entity in entity_reg.entities.values():
            if entity.platform == SOLARMAN_DOMAIN:
                state = hass.states.get(entity.entity_id)
                if state:
                    if not include_unavailable and state.state == "unavailable":
                        continue
                    
                    entity_data = {
                        "entity_id": entity.entity_id,
                        "name": entity.original_name or entity.name,
                        "device_class": entity.device_class,
                        "unit_of_measurement": entity.unit_of_measurement,
                        "state": state.state,
                        "attributes": dict(state.attributes),
                        "last_changed": state.last_changed.isoformat(),
                        "last_updated": state.last_updated.isoformat(),
                    }
                    solarman_entities.append(entity_data)
        
        # Prepare export data
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_entities": len(solarman_entities),
            "entities": solarman_entities,
        }
        
        def save_export():
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        # Write to file using executor
        try:
            await hass.async_add_executor_job(save_export)
            
            _LOGGER.info(f"Successfully exported {len(solarman_entities)} Solarman entities to {filename}")
            
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": f"Successfully exported {len(solarman_entities)} Solarman entities to:\n{filename}",
                    "title": "Solarman Export Complete",
                    "notification_id": "solarman_config_manager_export",
                },
            )
        except Exception as e:
            _LOGGER.error(f"Failed to export configuration: {e}")
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": f"Failed to export configuration: {e}",
                    "title": "Solarman Export Failed",
                    "notification_id": "solarman_config_manager_export_error",
                },
            )
    
    async def handle_compare_exports(call: ServiceCall) -> None:
        """Handle the compare_exports service call."""
        file1 = call.data["file1"]
        file2 = call.data["file2"]
        config_only = call.data.get("config_only", True)
        
        # Sanitize filenames - remove path separators
        file1 = "".join(c for c in file1 if c.isalnum() or c in "._- ")
        file2 = "".join(c for c in file2 if c.isalnum() or c in "._- ")
        
        if not file1.endswith(".json"):
            file1 += ".json"
        if not file2.endswith(".json"):
            file2 += ".json"
        
        filepath1 = backup_dir / file1
        filepath2 = backup_dir / file2
        
        # Verify paths are within backup directory
        try:
            if not filepath1.resolve().is_relative_to(backup_dir.resolve()) or \
               not filepath2.resolve().is_relative_to(backup_dir.resolve()):
                _LOGGER.error(f"Security: Attempted path traversal in comparison")
                await hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "message": "Invalid filenames provided.",
                        "title": "Solarman Comparison Failed",
                        "notification_id": "solarman_config_manager_comparison_error",
                    },
                )
                return
        except ValueError:
            _LOGGER.error(f"Security: Path validation failed")
            return
        
        _LOGGER.info(f"Comparing exports: {file1} vs {file2}")
        
        def load_files():
            with open(filepath1, "r", encoding="utf-8") as f:
                d1 = json.load(f)
            with open(filepath2, "r", encoding="utf-8") as f:
                d2 = json.load(f)
            return d1, d2

        try:
            # Load both files using executor
            data1, data2 = await hass.async_add_executor_job(load_files)
            
            # Compare entities
            entities1 = {e["entity_id"]: e for e in data1.get("entities", [])}
            entities2 = {e["entity_id"]: e for e in data2.get("entities", [])}
            
            # Find differences
            added = set(entities2.keys()) - set(entities1.keys())
            removed = set(entities1.keys()) - set(entities2.keys())
            common = set(entities1.keys()) & set(entities2.keys())
            
            # Writable entity domains (user-configurable)
            writable_domains = ["number", "select", "switch", "button", "input_number", "input_select", "input_boolean", "input_text"]
            
            changed = []
            for entity_id in common:
                e1 = entities1[entity_id]
                e2 = entities2[entity_id]
                
                # If config_only mode, skip read-only sensors
                if config_only:
                    domain = entity_id.split(".")[0]
                    if domain not in writable_domains:
                        continue
                
                differences = {}
                
                # Compare state
                if e1.get("state") != e2.get("state"):
                    differences["state"] = {
                        "old": e1.get("state"),
                        "new": e2.get("state")
                    }
                
                # Compare key attributes
                for key in ["name", "device_class", "unit_of_measurement"]:
                    if e1.get(key) != e2.get(key):
                        differences[key] = {
                            "old": e1.get(key),
                            "new": e2.get(key)
                        }
                
                # Compare attributes
                attrs1 = e1.get("attributes", {})
                attrs2 = e2.get("attributes", {})
                
                # Remove dynamic attributes that always change
                for attr_key in ["last_changed", "last_updated", "context_id"]:
                    attrs1.pop(attr_key, None)
                    attrs2.pop(attr_key, None)
                
                if attrs1 != attrs2:
                    # Find specific attribute changes
                    all_keys = set(attrs1.keys()) | set(attrs2.keys())
                    attr_changes = {}
                    for key in all_keys:
                        if attrs1.get(key) != attrs2.get(key):
                            attr_changes[key] = {
                                "old": attrs1.get(key),
                                "new": attrs2.get(key)
                            }
                    if attr_changes:
                        differences["attributes"] = attr_changes
                
                if differences:
                    changed.append({
                        "entity_id": entity_id,
                        "changes": differences
                    })
            
            # Generate comparison report
            comparison = {
                "file1": file1,
                "file2": file2,
                "config_only": config_only,
                "export1_timestamp": data1.get("export_timestamp"),
                "export2_timestamp": data2.get("export_timestamp"),
                "comparison_time": datetime.now().isoformat(),
                "summary": {
                    "total_entities_file1": len(entities1),
                    "total_entities_file2": len(entities2),
                    "added": len(added),
                    "removed": len(removed),
                    "changed": len(changed),
                    "unchanged": len(common) - len(changed),
                },
                "added_entities": list(added),
                "removed_entities": list(removed),
                "changes": {
                    c["entity_id"]: {
                        "old_value": c["changes"].get("state", {}).get("old"),
                        "new_value": c["changes"].get("state", {}).get("new"),
                        "changed_attributes": list(c["changes"].get("attributes", {}).keys()) if "attributes" in c["changes"] else []
                    } for c in changed
                },
            }
            
            # Save comparison report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            comparison_filename = f"comparison_{timestamp}.json"
            comparison_filepath = backup_dir / comparison_filename
            
            def save_comparison():
                with open(comparison_filepath, "w", encoding="utf-8") as f:
                    json.dump(comparison, f, indent=2, ensure_ascii=False)
            
            await hass.async_add_executor_job(save_comparison)
            
            _LOGGER.info(f"Saved comparison to {comparison_filename}")
            
            # Create notification
            summary = comparison["summary"]
            message = (
                f"Comparison saved to: {comparison_filename}\n\n"
                f"Added: {summary['added']} | "
                f"Removed: {summary['removed']} | "
                f"Changed: {summary['changed']} | "
                f"Unchanged: {summary['unchanged']}"
            )
            
            _LOGGER.info(f"Comparison complete: {message}")
            
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": message,
                    "title": "Solarman Comparison Complete",
                    "notification_id": "solarman_config_manager_comparison",
                },
            )
            
        except FileNotFoundError as e:
            error_msg = f"File not found: {e.filename}"
            _LOGGER.error(error_msg)
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": error_msg,
                    "title": "Solarman Comparison Failed",
                    "notification_id": "solarman_config_manager_comparison_error",
                },
            )
        except Exception as e:
            error_msg = f"Failed to compare exports: {e}"
            _LOGGER.error(error_msg)
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": error_msg,
                    "title": "Solarman Comparison Failed",
                    "notification_id": "solarman_config_manager_comparison_error",
                },
            )
    
    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_CONFIG,
        handle_export_config,
        schema=EXPORT_CONFIG_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_COMPARE_EXPORTS,
        handle_compare_exports,
        schema=COMPARE_EXPORTS_SCHEMA,
    )
    
    # Load sensors
    from homeassistant.helpers import discovery
    hass.async_create_task(
        discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config)
    )
    
    _LOGGER.info("Solarman Config Manager setup complete")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return True
