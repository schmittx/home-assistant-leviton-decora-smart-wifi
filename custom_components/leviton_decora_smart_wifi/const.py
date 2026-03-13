"""Constants used by the Leviton Decora Smart Wi-Fi integration."""

from enum import IntEnum

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

DEVICE_INFO_MANUFACTURER: str = "Leviton Manufacturing Co., Inc."
DEVICE_INFO_MODEL_RESIDENCE: str = "Residence"


class ScanInterval(IntEnum):
    """Scan interval."""

    DEFAULT = 120
    MAX = 600
    MIN = 30
    STEP = 30


class Timeout(IntEnum):
    """Timeout."""

    DEFAULT = 30
    MAX = 60
    MIN = 10
    STEP = 5
