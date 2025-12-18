"""Sensor platform for Solarman Config Manager."""
from __future__ import annotations

import json
import logging
from datetime import timedelta
from pathlib import Path

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DEFAULT_BACKUP_DIR

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
) -> None:
    """Set up Solarman Config Manager sensors."""
    sensors = [
        SolarmanConfigManagerFilesSensor(hass),
        SolarmanConfigManagerComparisonResultSensor(hass),
        SolarmanConfigManagerRestoreResultSensor(hass),
    ]
    async_add_entities(sensors, True)


class SolarmanConfigManagerFilesSensor(SensorEntity):
    """Sensor to list available backup files."""

    _attr_name = "Solarman Config Manager Files"
    _attr_icon = "mdi:file-document-multiple"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._attr_unique_id = f"{DOMAIN}_files"
        self._attr_native_value = 0
        self._files = []
        self._comparison_files = []

    @property
    def native_value(self) -> int:
        """Return the number of backup files."""
        return self._attr_native_value

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            "files": self._files,
            "file_list": self._files,
            "comparison_files": self._comparison_files,
        }

    async def async_update(self) -> None:
        """Update the sensor."""
        backup_dir = Path(self.hass.config.path(DEFAULT_BACKUP_DIR))
        
        def get_files():
            if not backup_dir.exists():
                return [], []
            export_files = sorted(
                [f.stem for f in backup_dir.glob("solarman_export_*.json")],
                reverse=True,
            )
            comparison_files = sorted(
                [f.stem for f in backup_dir.glob("comparison_*.json")],
                reverse=True,
            )
            return export_files, comparison_files

        self._files, self._comparison_files = await self.hass.async_add_executor_job(get_files)
        self._attr_native_value = len(self._files)
        _LOGGER.debug(f"Updated backup files sensor: {self._attr_native_value} export files, {len(self._comparison_files)} comparison files found")


class SolarmanConfigManagerComparisonResultSensor(SensorEntity):
    """Sensor to display the latest comparison result."""

    _attr_name = "Solarman Config Manager Comparison Result"
    _attr_icon = "mdi:file-compare"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._attr_unique_id = f"{DOMAIN}_comparison"
        self._attr_native_value = "No comparison yet"
        self._comparison_data = {}

    @property
    def native_value(self) -> str:
        """Return the state."""
        return self._attr_native_value

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return self._comparison_data

    async def async_update(self) -> None:
        """Update the sensor with latest comparison."""
        backup_dir = Path(self.hass.config.path(DEFAULT_BACKUP_DIR))
        
        def get_latest_comparison():
            if not backup_dir.exists():
                return None
            comparison_files = sorted(
                backup_dir.glob("comparison_*.json"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )
            if not comparison_files:
                return None
            
            latest_file = comparison_files[0]
            try:
                with latest_file.open("r") as f:
                    return json.load(f), latest_file.name
            except Exception as e:
                _LOGGER.error(f"Error reading comparison file {latest_file}: {e}")
                return None

        result = await self.hass.async_add_executor_job(get_latest_comparison)

        if not result:
            self._attr_native_value = "No comparison yet"
            self._comparison_data = {}
            return

        data, filename = result
        try:
            summary = data.get("summary", {})
            # Handle both old and new key formats
            changed = summary.get("changed", summary.get("changed_entities", 0))
            added = summary.get("added", summary.get("added_entities", 0))
            removed = summary.get("removed", summary.get("removed_entities", 0))
            unchanged = summary.get("unchanged", summary.get("unchanged_entities", 0))
            
            if changed == 0 and added == 0 and removed == 0:
                self._attr_native_value = "No changes"
            else:
                self._attr_native_value = f"{changed} changed, {added} added, {removed} removed"
            
            # Normalize changes
            raw_changes = data.get("changes", data.get("changed_entities", {}))
            normalized_changes = {}
            if isinstance(raw_changes, list):
                for item in raw_changes:
                    eid = item.get("entity_id")
                    if eid:
                        diffs = item.get("changes", {})
                        normalized_changes[eid] = {
                            "old_value": diffs.get("state", {}).get("old"),
                            "new_value": diffs.get("state", {}).get("new"),
                            "changed_attributes": list(diffs.get("attributes", {}).keys()) if "attributes" in diffs else []
                        }
            else:
                normalized_changes = raw_changes

            self._comparison_data = {
                "file1": data.get("file1", ""),
                "file2": data.get("file2", ""),
                "config_only": data.get("config_only", False),
                "timestamp": data.get("comparison_time", data.get("export2_timestamp", "")),
                "summary": {
                    "changed": changed,
                    "added": added,
                    "removed": removed,
                    "unchanged": unchanged,
                },
                "changes": normalized_changes,
                "added_entities": data.get("added_entities", []),
                "removed_entities": data.get("removed_entities", []),
                "comparison_file": filename,
            }
            _LOGGER.debug(f"Updated comparison sensor: {self._attr_native_value}")
        except Exception as e:
            _LOGGER.error(f"Error processing comparison data: {e}")
            self._attr_native_value = "Error processing comparison"
            self._comparison_data = {}


class SolarmanConfigManagerRestoreResultSensor(SensorEntity):
    """Sensor to display the latest restore result."""

    _attr_name = "Solarman Config Manager Restore Result"
    _attr_icon = "mdi:restore"
    _attr_should_poll = False  # Only updates via events

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._attr_unique_id = f"{DOMAIN}_restore"
        self._attr_native_value = "No restore yet"
        self._restore_data = {}
        self._unsub_listener = None

    async def async_added_to_hass(self) -> None:
        """Register event listener when entity is added."""
        async def handle_restore_complete(event):
            """Handle restore complete event."""
            _LOGGER.debug("Restore complete event received, updating sensor")
            # Read data and update state
            restore_result = self.hass.data.get(DOMAIN, {}).get("last_restore_result")
            if restore_result:
                self._restore_data = restore_result
                if restore_result.get("dry_run"):
                    self._attr_native_value = "Dry Run Complete"
                else:
                    self._attr_native_value = "Restore Complete"
                self.async_write_ha_state()
        
        self._unsub_listener = self.hass.bus.async_listen(
            f"{DOMAIN}_restore_complete", handle_restore_complete
        )

    async def async_will_remove_from_hass(self) -> None:
        """Clean up event listener when entity is removed."""
        if self._unsub_listener:
            self._unsub_listener()

    @property
    def native_value(self) -> str:
        """Return the state."""
        return self._attr_native_value

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return self._restore_data

    async def async_update(self) -> None:
        """Update the sensor by reading the latest restore result from persistent notification."""
        # This sensor is updated by the restore service via hass.data
        restore_result = self.hass.data.get(DOMAIN, {}).get("last_restore_result")
        if restore_result:
            self._restore_data = restore_result
            if restore_result.get("dry_run"):
                self._attr_native_value = "Dry Run Complete"
            else:
                self._attr_native_value = "Restore Complete"
            _LOGGER.debug(f"Updated restore sensor: {self._attr_native_value}")

