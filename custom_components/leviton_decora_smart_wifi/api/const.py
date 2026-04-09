"""Leviton API."""

from enum import IntEnum, StrEnum

API_ENDPOINT = "https://my.leviton.com/api"

LOGIN_CODE_INVALID = "login_code_invalid"
LOGIN_CODE_REQUIRED = "login_code_required"
LOGIN_FAILED = "login_failed"
LOGIN_SUCCESS = "login_success"
LOGIN_TOO_MANY_ATTEMPTS = "login_too_many_attempts"


DEVICE_MODEL = "model"
DEVICE_TYPE = "type"
DEVICE_GENERATION = "generation"


class ControlTiming(StrEnum):
    """Control timing."""

    NORMAL = "normal"
    MEDIUM = "medium"
    EXTENDED = "extended"
    UNKNOWN = "unknown"


class DeviceGeneration(IntEnum):
    """Device generation."""

    ONE = 1
    TWO = 2


class DeviceType(StrEnum):
    """Device type."""

    BRIDGE = "bridge"
    CONTROLLER = "controller"
    FAN = "fan"
    GFCI = "gfci"
    LIGHT = "light"
    OUTLET = "outlet"
    SWITCH = "switch"


class DimLEDMode(StrEnum):
    """Dim LED mode."""

    OFF = "always_off"
    ON = "always_on"


class DimmingMode(StrEnum):
    """Dimming mode."""

    FORWARD = "forward"
    REVERSE = "reverse"
    UNKNOWN = "unknown"


class GFCIStatus(StrEnum):
    """GFCI status."""

    FAULT = "fault"
    PROTECTED = "protected"
    TEST = "test"
    UNKNOWN = "unknown"


class Level(IntEnum):
    """Level."""

    MAXIMUM = 100

    MINIMUM_AMBIENT_THRESHOLD = 1
    MINIMUM_FAN = 25
    MINIMUM_LIGHT = 1

    PRESET_OFF = 0

    STEP_FAN = 25
    STEP_LIGHT = 1


class LoadType(StrEnum):
    """Load type."""

    ELV = "elv"
    INCANDESCENT = "incandescent"
    LED = "led"
    CFL = "cfl"
    NON_DIMMABLE = "non_dimmable"
    MLV = "mlv"
    UNKNOWN = "unknown"


class MotionMode(StrEnum):
    """Motion mode."""

    OCCUPANCY = "occupancy"
    VACANCY = "vacancy"
    UNKNOWN = "unknown"


class MotionNightMode(StrEnum):
    """Motion night mode."""

    ROOM = "room_lights"
    GUIDE = "guidelight"
    UNKNOWN = "unknown"


class MotionSnooze(StrEnum):
    """Motion snooze."""

    DISABLED = "disabled"
    UNKNOWN = "unknown"


class Power(StrEnum):
    """Power."""

    OFF = "OFF"
    ON = "ON"


class Status(StrEnum):
    """Status."""

    AWAY = "away"
    HOME = "home"
    UNKNOWN = "unknown"


class StatusLED(IntEnum):
    """Status LED."""

    DISABLED = 0
    ENABLED = 255


class StatusLEDMode(StrEnum):
    """Status LED mode."""

    OFF = "led_always_off"
    STATUS = "status_mode"
    LOCATOR = "locator_mode"
    UNKNOWN = "unknown"


class TimePeriod(StrEnum):
    """Time period."""

    SECONDS_0 = "0_seconds"
    SECONDS_0_5 = "0_5_seconds"
    SECONDS_1 = "1_second"
    SECONDS_1_5 = "1_5_seconds"
    SECONDS_2 = "2_seconds"
    SECONDS_3 = "3_seconds"
    SECONDS_5 = "5_seconds"
    SECONDS_10 = "10_seconds"
    SECONDS_15 = "15_seconds"
    SECONDS_25 = "25_seconds"

    MINUTES_1 = "1_minute"
    MINUTES_2 = "2_minutes"
    MINUTES_3 = "3_minutes"
    MINUTES_4 = "4_minutes"
    MINUTES_5 = "5_minutes"
    MINUTES_6 = "6_minutes"
    MINUTES_7 = "7_minutes"
    MINUTES_8 = "8_minutes"
    MINUTES_9 = "9_minutes"
    MINUTES_10 = "10_minutes"
    MINUTES_15 = "15_minutes"
    MINUTES_20 = "20_minutes"
    MINUTES_25 = "25_minutes"
    MINUTES_30 = "30_minutes"
    MINUTES_45 = "45_minutes"
    MINUTES_60 = "60_minutes"

    HOURS_1 = "1_hour"
    HOURS_2 = "2_hours"
    HOURS_3 = "3_hours"
    HOURS_4 = "4_hours"
    HOURS_5 = "5_hours"
    HOURS_6 = "6_hours"
    HOURS_7 = "7_hours"
    HOURS_8 = "8_hours"
    HOURS_9 = "9_hours"
    HOURS_10 = "10_hours"
    HOURS_11 = "11_hours"
    HOURS_12 = "12_hours"
    HOURS_24 = "24_hours"

    UNKNOWN = "unknown"


SUPPORTED_DEVICES = [
    {
        DEVICE_MODEL: "D215O",
        DEVICE_TYPE: [DeviceType.OUTLET],
        DEVICE_GENERATION: DeviceGeneration.TWO,
    },
    {
        DEVICE_MODEL: "D215P",
        DEVICE_TYPE: [DeviceType.OUTLET],
        DEVICE_GENERATION: DeviceGeneration.TWO,
    },
    {
        DEVICE_MODEL: "D215R",
        DEVICE_TYPE: [DeviceType.OUTLET],
        DEVICE_GENERATION: DeviceGeneration.TWO,
    },
    {
        DEVICE_MODEL: "D215S",
        DEVICE_TYPE: [DeviceType.SWITCH],
        DEVICE_GENERATION: DeviceGeneration.TWO,
    },
    {
        DEVICE_MODEL: "D23LP",
        DEVICE_TYPE: [DeviceType.LIGHT],
        DEVICE_GENERATION: DeviceGeneration.TWO,
    },
    {
        DEVICE_MODEL: "D24SF",
        DEVICE_TYPE: [DeviceType.FAN],
        DEVICE_GENERATION: DeviceGeneration.TWO,
    },
    {
        DEVICE_MODEL: "D26HD",
        DEVICE_TYPE: [DeviceType.LIGHT],
        DEVICE_GENERATION: DeviceGeneration.TWO,
    },
    {
        DEVICE_MODEL: "D2ELV",
        DEVICE_TYPE: [DeviceType.LIGHT],
        DEVICE_GENERATION: DeviceGeneration.TWO,
    },
    {
        DEVICE_MODEL: "D2GF1",
        DEVICE_TYPE: [DeviceType.GFCI],
        DEVICE_GENERATION: DeviceGeneration.TWO,
    },
    {
        DEVICE_MODEL: "D2GF2",
        DEVICE_TYPE: [DeviceType.GFCI],
        DEVICE_GENERATION: DeviceGeneration.TWO,
    },
    {
        DEVICE_MODEL: "D2MSD",
        DEVICE_TYPE: [DeviceType.LIGHT],
        DEVICE_GENERATION: DeviceGeneration.TWO,
    },
    {
        DEVICE_MODEL: "DN15S",
        DEVICE_TYPE: [DeviceType.SWITCH],
        DEVICE_GENERATION: DeviceGeneration.TWO,
    },
    {
        DEVICE_MODEL: "DN6HD",
        DEVICE_TYPE: [DeviceType.LIGHT],
        DEVICE_GENERATION: DeviceGeneration.TWO,
    },
    {
        DEVICE_MODEL: "D2SCS",
        DEVICE_TYPE: [DeviceType.CONTROLLER, DeviceType.SWITCH],
        DEVICE_GENERATION: DeviceGeneration.TWO,
    },
    {
        DEVICE_MODEL: "MLWSB",
        DEVICE_TYPE: [DeviceType.BRIDGE],
        DEVICE_GENERATION: DeviceGeneration.TWO,
    },
    {
        DEVICE_MODEL: "DW15A",
        DEVICE_TYPE: [DeviceType.OUTLET],
        DEVICE_GENERATION: DeviceGeneration.ONE,
    },
    {
        DEVICE_MODEL: "DW15P",
        DEVICE_TYPE: [DeviceType.OUTLET],
        DEVICE_GENERATION: DeviceGeneration.ONE,
    },
    {
        DEVICE_MODEL: "DW15R",
        DEVICE_TYPE: [DeviceType.OUTLET],
        DEVICE_GENERATION: DeviceGeneration.ONE,
    },
    {
        DEVICE_MODEL: "DW15S",
        DEVICE_TYPE: [DeviceType.SWITCH],
        DEVICE_GENERATION: DeviceGeneration.ONE,
    },
    {
        DEVICE_MODEL: "DW1KD",
        DEVICE_TYPE: [DeviceType.LIGHT],
        DEVICE_GENERATION: DeviceGeneration.ONE,
    },
    {
        DEVICE_MODEL: "DW3HL",
        DEVICE_TYPE: [DeviceType.LIGHT],
        DEVICE_GENERATION: DeviceGeneration.ONE,
    },
    {
        DEVICE_MODEL: "DW4BC",
        DEVICE_TYPE: [DeviceType.CONTROLLER],
        DEVICE_GENERATION: DeviceGeneration.ONE,
    },
    {
        DEVICE_MODEL: "DW4SF",
        DEVICE_TYPE: [DeviceType.FAN],
        DEVICE_GENERATION: DeviceGeneration.ONE,
    },
    {
        DEVICE_MODEL: "DW6HD",
        DEVICE_TYPE: [DeviceType.LIGHT],
        DEVICE_GENERATION: DeviceGeneration.ONE,
    },
    {
        DEVICE_MODEL: "DWVAA",
        DEVICE_TYPE: [DeviceType.LIGHT],
        DEVICE_GENERATION: DeviceGeneration.ONE,
    },
]

SUPPORTED_DEVICES_BRIDGE = [
    device[DEVICE_MODEL]
    for device in SUPPORTED_DEVICES
    if DeviceType.BRIDGE in device[DEVICE_TYPE]
]

SUPPORTED_DEVICES_CONTROLLER = [
    device[DEVICE_MODEL]
    for device in SUPPORTED_DEVICES
    if DeviceType.CONTROLLER in device[DEVICE_TYPE]
]

SUPPORTED_DEVICES_FAN = [
    device[DEVICE_MODEL]
    for device in SUPPORTED_DEVICES
    if DeviceType.FAN in device[DEVICE_TYPE]
]

SUPPORTED_DEVICES_GENERATION_TWO = [
    device[DEVICE_MODEL]
    for device in SUPPORTED_DEVICES
    if device[DEVICE_GENERATION] == DeviceGeneration.TWO
]

SUPPORTED_DEVICES_GFCI = [
    device[DEVICE_MODEL]
    for device in SUPPORTED_DEVICES
    if DeviceType.GFCI in device[DEVICE_TYPE]
]

SUPPORTED_DEVICES_LIGHT = [
    device[DEVICE_MODEL]
    for device in SUPPORTED_DEVICES
    if DeviceType.LIGHT in device[DEVICE_TYPE]
]

SUPPORTED_DEVICES_MODEL = [device[DEVICE_MODEL] for device in SUPPORTED_DEVICES]

SUPPORTED_DEVICES_OUTLET = [
    device[DEVICE_MODEL]
    for device in SUPPORTED_DEVICES
    if DeviceType.OUTLET in device[DEVICE_TYPE]
]

SUPPORTED_DEVICES_SWITCH = [
    device[DEVICE_MODEL]
    for device in SUPPORTED_DEVICES
    if DeviceType.SWITCH in device[DEVICE_TYPE]
]

AUTO_SHUTOFF_DISABLED = "disabled"

AUTO_SHUTOFF_MAP = {
    0: AUTO_SHUTOFF_DISABLED,
    60: TimePeriod.MINUTES_1,
    300: TimePeriod.MINUTES_5,
    600: TimePeriod.MINUTES_10,
    900: TimePeriod.MINUTES_15,
    1800: TimePeriod.MINUTES_30,
    3600: TimePeriod.HOURS_1,
    7200: TimePeriod.HOURS_2,
    10800: TimePeriod.HOURS_3,
    14400: TimePeriod.HOURS_4,
    18000: TimePeriod.HOURS_5,
    21600: TimePeriod.HOURS_6,
    25200: TimePeriod.HOURS_7,
    28800: TimePeriod.HOURS_8,
    32400: TimePeriod.HOURS_9,
    36000: TimePeriod.HOURS_10,
    39600: TimePeriod.HOURS_11,
    43200: TimePeriod.HOURS_12,
}

CONTROL_TIMING_MAP = {
    80: ControlTiming.NORMAL,
    92: ControlTiming.MEDIUM,
    97: ControlTiming.EXTENDED,
}

DIM_LED_MAP = {
    0: DimLEDMode.OFF,
    1: TimePeriod.SECONDS_1,
    2: TimePeriod.SECONDS_2,
    3: TimePeriod.SECONDS_3,
    5: TimePeriod.SECONDS_5,
    10: TimePeriod.SECONDS_10,
    15: TimePeriod.SECONDS_15,
    25: TimePeriod.SECONDS_25,
    255: DimLEDMode.ON,
}

FADE_ON_OFF_RATE_MAP = {
    0: TimePeriod.SECONDS_0,
    5: TimePeriod.SECONDS_0_5,
    10: TimePeriod.SECONDS_1,
    15: TimePeriod.SECONDS_1_5,
    20: TimePeriod.SECONDS_2,
    30: TimePeriod.SECONDS_3,
    50: TimePeriod.SECONDS_5,
    100: TimePeriod.SECONDS_10,
    150: TimePeriod.SECONDS_1,
    250: TimePeriod.SECONDS_25,
}

GFCI_STATUS_MAP = {
    "": GFCIStatus.PROTECTED,
    "GFCI_FAULT": GFCIStatus.FAULT,
    "MANUAL_TRIP": GFCIStatus.TEST,
}

HOME_AWAY_ACTIVITY_DISABLED = "disabled"

LOAD_TYPE_MAP = {
    0: LoadType.INCANDESCENT,
    1: LoadType.LED,
    2: LoadType.CFL,
    4: LoadType.MLV,
    5: LoadType.NON_DIMMABLE,
    6: LoadType.ELV,
}

MOTION_MODE_MAP = {
    0: MotionMode.OCCUPANCY,
    1: MotionMode.VACANCY,
}

MOTION_NIGHT_MODE_MAP = {
    0: MotionNightMode.ROOM,
    2: MotionNightMode.GUIDE,
}

MOTION_SNOOZE_MAP = {
    0: MotionSnooze.DISABLED,
    1: TimePeriod.MINUTES_1,
    5: TimePeriod.MINUTES_5,
    10: TimePeriod.MINUTES_10,
    15: TimePeriod.MINUTES_15,
    30: TimePeriod.MINUTES_30,
    60: TimePeriod.HOURS_1,
    120: TimePeriod.HOURS_2,
    180: TimePeriod.HOURS_3,
    240: TimePeriod.HOURS_4,
    300: TimePeriod.HOURS_5,
    360: TimePeriod.HOURS_6,
    420: TimePeriod.HOURS_7,
    480: TimePeriod.HOURS_8,
    540: TimePeriod.HOURS_9,
    600: TimePeriod.HOURS_10,
    660: TimePeriod.HOURS_11,
    720: TimePeriod.HOURS_12,
    1440: TimePeriod.HOURS_24,
}

MOTION_TIMEOUT_MAP = {
    1: TimePeriod.MINUTES_1,
    2: TimePeriod.MINUTES_2,
    3: TimePeriod.MINUTES_3,
    4: TimePeriod.MINUTES_4,
    5: TimePeriod.MINUTES_5,
    6: TimePeriod.MINUTES_6,
    7: TimePeriod.MINUTES_7,
    8: TimePeriod.MINUTES_8,
    9: TimePeriod.MINUTES_9,
    10: TimePeriod.MINUTES_10,
    15: TimePeriod.MINUTES_15,
    20: TimePeriod.MINUTES_20,
    25: TimePeriod.MINUTES_25,
    30: TimePeriod.MINUTES_30,
    45: TimePeriod.MINUTES_45,
    60: TimePeriod.MINUTES_60,
}

STATUS_LED_MODE_MAP = {
    0: StatusLEDMode.OFF,
    254: StatusLEDMode.STATUS,
    255: StatusLEDMode.LOCATOR,
}

STATUS_MAP = {
    "AWAY": Status.AWAY,
    "HOME": Status.HOME,
}
