"""Constants used by the Leviton Decora Smart Wi-Fi integration."""

CONF_DEVICES: str = "devices"
CONF_RESIDENCES: str = "residences"
CONF_SAVE_RESPONSES: str = "save_responses"
CONF_TIMEOUT: str = "timeout"

CONFIGURATION_URL: str = "https://my.leviton.com/home"

DATA_API: str = "api"
DATA_COORDINATOR: str = "coordinator"

DOMAIN: str = "leviton_decora_smart_wifi"

RELEASE_URL: str = "https://decorasmartsupport.zendesk.com/hc/en-us/articles/4409216317339-Decora-Smart-Wi-Fi-2nd-Generation-Firmware-Release-Notes"

UNDO_UPDATE_LISTENER: str = "undo_update_listener"

DEFAULT_SAVE_LOCATION: str = f"/config/custom_components/{DOMAIN}/api/responses"
DEFAULT_SAVE_RESPONSES: bool = False
DEFAULT_SCAN_INTERVAL: int = 120
DEFAULT_TIMEOUT: int = 30

DEVICE_INFO_MANUFACTURER: str = "Leviton Manufacturing Co., Inc."
DEVICE_INFO_MODEL_RESIDENCE: str = "Residence"

MIN_SCAN_INTERVAL: int = 30
MAX_SCAN_INTERVAL: int = 600
STEP_SCAN_INTERVAL: int = 30

MIN_TIMEOUT: int = 10
MAX_TIMEOUT: int = 60
STEP_TIMEOUT: int = 5
