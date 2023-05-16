"""Constants used by the Leviton Decora Smart Wi-Fi integration."""
CONF_DEVICES = "devices"
CONF_RESIDENCES = "residences"
CONF_SAVE_RESPONSES = "save_responses"
CONF_TIMEOUT = "timeout"

CONFIGURATION_URL = "https://my.leviton.com/home"

DATA_COORDINATOR = "coordinator"

DOMAIN = "leviton_decora_smart_wifi"

RELEASE_URL = "https://decorasmartsupport.zendesk.com/hc/en-us/articles/4409216317339-Decora-Smart-Wi-Fi-2nd-Generation-Firmware-Release-Notes"

UNDO_UPDATE_LISTENER = "undo_update_listener"

VALUES_SCAN_INTERVAL = [30, 60, 120, 300, 600]
VALUES_TIMEOUT = [10, 15, 30, 45, 60]

DEFAULT_SAVE_LOCATION = f"/config/custom_components/{DOMAIN}/api/responses"
DEFAULT_SAVE_RESPONSES = False
DEFAULT_SCAN_INTERVAL = VALUES_SCAN_INTERVAL[2]
DEFAULT_TIMEOUT = VALUES_TIMEOUT[0]
