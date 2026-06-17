"""Constants used by the Leviton Decora Smart Wi-Fi integration."""

from enum import IntEnum

CONF_DEVICES: str = "devices"
CONF_RESIDENCES: str = "residences"
CONF_SAVE_RESPONSES: str = "save_responses"
CONF_TIMEOUT: str = "timeout"

CONFIGURATION_URL: str = "https://my.leviton.com/home"

DATA_API: str = "api"
DATA_COORDINATOR: str = "coordinator"
DATA_WEBSOCKET: str = "websocket"

CONF_LOGIN_RESPONSE: str = "login_response"

DOMAIN: str = "leviton_decora_smart_wifi"

EVENT_NOTIFICATION: str = f"{DOMAIN}_event"
UPDATE_NOTIFICATION: str = f"{DOMAIN}_update"

UNDO_UPDATE_LISTENER: str = "undo_update_listener"

DEFAULT_SAVE_LOCATION: str = f"/config/custom_components/{DOMAIN}/api/responses"
DEFAULT_SAVE_RESPONSES: bool = False

DEVICE_INFO_MANUFACTURER: str = "Leviton Manufacturing Co., Inc."
DEVICE_INFO_MODEL_RESIDENCE: str = "Residence"


class ScanInterval(IntEnum):
    """Scan interval."""

    DEFAULT = 10
    MAX = 60
    MIN = 1
    STEP = 1


class Timeout(IntEnum):
    """Timeout."""

    DEFAULT = 30
    MAX = 60
    MIN = 10
    STEP = 5
