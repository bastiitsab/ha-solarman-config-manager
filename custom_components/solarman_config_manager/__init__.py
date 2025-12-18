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
    SERVICE_RESTORE_FROM_COMPARISON,
    DEFAULT_BACKUP_DIR,
    SOLARMAN_DOMAIN,
    DOMAIN_SERVICE_MAP,
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

RESTORE_FROM_COMPARISON_SCHEMA = vol.Schema({
    vol.Required("comparison_file"): cv.string,
    vol.Required("direction"): vol.In(["revert", "apply"]),
    vol.Optional("dry_run", default=False): cv.boolean,
    vol.Required("confirm"): cv.string,
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
    
    async def handle_restore_from_comparison(call: ServiceCall) -> None:
        """Handle the restore_from_comparison service call."""
        comparison_file = call.data["comparison_file"]
        direction = call.data["direction"]
        dry_run = call.data.get("dry_run", False)
        confirm = call.data["confirm"]
        
        # Confirmation check
        if confirm != "CONFIRM":
            error_msg = "Restore cancelled: You must type 'CONFIRM' to proceed"
            _LOGGER.warning(error_msg)
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": error_msg,
                    "title": "Solarman Restore Cancelled",
                    "notification_id": "solarman_config_manager_restore_error",
                },
            )
            return
        
        # Sanitize filename
        comparison_file = "".join(c for c in comparison_file if c.isalnum() or c in "._- ")
        
        if not comparison_file.endswith(".json"):
            comparison_file += ".json"
        
        comparison_filepath = backup_dir / comparison_file
        
        # Verify path is within backup directory
        try:
            if not comparison_filepath.resolve().is_relative_to(backup_dir.resolve()):
                _LOGGER.error(f"Security: Attempted path traversal with comparison file: {comparison_file}")
                await hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "message": "Invalid filename provided.",
                        "title": "Solarman Restore Failed",
                        "notification_id": "solarman_config_manager_restore_error",
                    },
                )
                return
        except ValueError:
            _LOGGER.error(f"Security: Path validation failed")
            return
        
        _LOGGER.info(f"{'[DRY RUN] ' if dry_run else ''}Restoring configuration from {comparison_file}, direction={direction}")
        
        def load_comparison():
            with open(comparison_filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        
        try:
            # Load comparison file
            comparison_data = await hass.async_add_executor_job(load_comparison)
            
            changes = comparison_data.get("changes", {})
            
            if not changes:
                await hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "message": "No changes found in comparison file.",
                        "title": "Solarman Restore",
                        "notification_id": "solarman_config_manager_restore",
                    },
                )
                return
            
            results = {
                "success": [],
                "failed": [],
                "skipped": [],
            }
            
            # Process each changed entity
            for entity_id, change_data in changes.items():
                domain = entity_id.split(".")[0]
                
                # Skip entities we can't restore
                if domain not in DOMAIN_SERVICE_MAP:
                    results["skipped"].append({"entity": entity_id, "reason": f"Domain '{domain}' not restorable"})
                    continue
                
                # Get target value based on direction
                target_value = change_data["old_value"] if direction == "revert" else change_data["new_value"]
                
                if target_value is None:
                    results["skipped"].append({"entity": entity_id, "reason": "Target value is None"})
                    continue
                
                # Build service call
                service_map = DOMAIN_SERVICE_MAP[domain]
                
                # Handle switch/boolean domains
                if "service_on" in service_map:
                    if target_value in ["on", "On", "ON", True, "true", "True"]:
                        service_name = service_map["service_on"]
                        service_data = {"entity_id": entity_id}
                    else:
                        service_name = service_map["service_off"]
                        service_data = {"entity_id": entity_id}
                else:
                    # Handle number/select domains
                    service_name = service_map["service"]
                    param_name = service_map["param"]
                    service_data = {
                        "entity_id": entity_id,
                        param_name: target_value,
                    }
                
                if dry_run:
                    _LOGGER.info(f"[DRY RUN] Would call {domain}.{service_name} with {service_data}")
                    results["success"].append({
                        "entity": entity_id,
                        "service": f"{domain}.{service_name}",
                        "data": service_data,
                        "dry_run": True,
                    })
                else:
                    try:
                        await hass.services.async_call(domain, service_name, service_data, blocking=True)
                        _LOGGER.info(f"Restored {entity_id} to {target_value}")
                        results["success"].append({
                            "entity": entity_id,
                            "value": target_value,
                        })
                        # Small delay to avoid flooding
                        await hass.async_add_executor_job(lambda: __import__('time').sleep(0.1))
                    except Exception as e:
                        _LOGGER.error(f"Failed to restore {entity_id}: {e}")
                        results["failed"].append({
                            "entity": entity_id,
                            "error": str(e),
                        })
            
            # Generate summary
            summary_msg = (
                f"{'[DRY RUN] ' if dry_run else ''}Restore Summary:\n\n"
                f"✅ Success: {len(results['success'])}\n"
                f"❌ Failed: {len(results['failed'])}\n"
                f"⏭️ Skipped: {len(results['skipped'])}\n\n"
            )
            
            # Show details of what will change (dry run) or what changed
            if results["success"]:
                if dry_run:
                    summary_msg += "**Will restore these entities:**\n"
                    for item in results["success"][:10]:  # Show first 10
                        entity_name = item['entity'].replace('number.', '').replace('select.', '').replace('_', ' ').title()
                        if 'data' in item:
                            # Extract the value from service data
                            value = item['data'].get('value') or item['data'].get('option') or 'on/off'
                            summary_msg += f"  • {entity_name}: → {value}\n"
                    if len(results["success"]) > 10:
                        summary_msg += f"  ... and {len(results['success']) - 10} more\n"
                else:
                    summary_msg += "**Restored entities:**\n"
                    for item in results["success"][:10]:
                        entity_name = item['entity'].replace('number.', '').replace('select.', '').replace('_', ' ').title()
                        summary_msg += f"  • {item['entity']}: → {item['value']}\n"
                    if len(results["success"]) > 10:
                        summary_msg += f"  ... and {len(results['success']) - 10} more\n"
                summary_msg += "\n"
            
            if results["failed"]:
                summary_msg += "**Failed entities:**\n"
                for item in results["failed"][:5]:
                    summary_msg += f"  • {item['entity']}: {item['error']}\n"
                summary_msg += "\n"
            
            if results["skipped"] and len(results["skipped"]) <= 5:
                summary_msg += "**Skipped entities:**\n"
                for item in results["skipped"]:
                    summary_msg += f"  • {item['entity']}: {item['reason']}\n"
            
            _LOGGER.info(f"Restore complete: {summary_msg}")
            
            # Store result in hass.data for sensor
            if DOMAIN not in hass.data:
                hass.data[DOMAIN] = {}
            hass.data[DOMAIN]["last_restore_result"] = {
                "success": len(results["success"]),
                "failed": len(results["failed"]),
                "skipped": len(results["skipped"]),
                "dry_run": dry_run,
                "direction": direction,
                "comparison_file": comparison_file,
                "timestamp": datetime.now().isoformat(),
                "summary": results,
            }
            
            # Trigger sensor update
            restore_sensor = hass.states.get(f"sensor.{DOMAIN}_restore")
            if restore_sensor:
                # Fire an event to trigger sensor update
                hass.bus.async_fire(f"{DOMAIN}_restore_complete")
            
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": summary_msg,
                    "title": f"Solarman Restore {'(Dry Run) ' if dry_run else ''}Complete",
                    "notification_id": "solarman_config_manager_restore",
                },
            )
            
        except FileNotFoundError:
            error_msg = f"Comparison file not found: {comparison_file}"
            _LOGGER.error(error_msg)
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": error_msg,
                    "title": "Solarman Restore Failed",
                    "notification_id": "solarman_config_manager_restore_error",
                },
            )
        except Exception as e:
            error_msg = f"Failed to restore configuration: {e}"
            _LOGGER.error(error_msg)
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": error_msg,
                    "title": "Solarman Restore Failed",
                    "notification_id": "solarman_config_manager_restore_error",
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
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_RESTORE_FROM_COMPARISON,
        handle_restore_from_comparison,
        schema=RESTORE_FROM_COMPARISON_SCHEMA,
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
