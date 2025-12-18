"""Constants for Solarman Config Manager integration."""

DOMAIN = "solarman_config_manager"

# Service names
SERVICE_EXPORT_CONFIG = "export_config"
SERVICE_COMPARE_EXPORTS = "compare_exports"
SERVICE_RESTORE_FROM_COMPARISON = "restore_from_comparison"

# Default paths
DEFAULT_BACKUP_DIR = "solarman_config_backups"

# Solarman integration domain
SOLARMAN_DOMAIN = "solarman"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and invalid characters."""
    return "".join(c for c in filename if c.isalnum() or c in "._- ").strip()


# Domain to service mapping for restore operations
DOMAIN_SERVICE_MAP = {
    "number": {
        "service": "set_value",
        "param": "value",
    },
    "select": {
        "service": "select_option",
        "param": "option",
    },
    "switch": {
        "service_on": "turn_on",
        "service_off": "turn_off",
    },
    "input_number": {
        "service": "set_value",
        "param": "value",
    },
    "input_select": {
        "service": "select_option",
        "param": "option",
    },
    "input_boolean": {
        "service_on": "turn_on",
        "service_off": "turn_off",
    },
}
