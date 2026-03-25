"""Leviton API."""

from __future__ import annotations

import io
import logging
from typing import Literal

import pyqrcode

from .button import Button
from .const import (
    AUTO_SHUTOFF_MAP,
    CONTROL_TIMING_MAP,
    DIM_LED_MAP,
    FADE_ON_OFF_RATE_MAP,
    GFCI_STATUS_MAP,
    LOAD_TYPE_MAP,
    MOTION_MODE_MAP,
    MOTION_NIGHT_MODE_MAP,
    MOTION_SNOOZE_MAP,
    MOTION_TIMEOUT_MAP,
    STATUS_LED_MODE_MAP,
    SUPPORTED_DEVICES_CONTROLLER,
    SUPPORTED_DEVICES_FAN,
    SUPPORTED_DEVICES_GENERATION_TWO,
    SUPPORTED_DEVICES_GFCI,
    SUPPORTED_DEVICES_LIGHT,
    SUPPORTED_DEVICES_MODEL,
    SUPPORTED_DEVICES_OUTLET,
    SUPPORTED_DEVICES_SWITCH,
    ControlTiming,
    DimmingMode,
    GFCIStatus,
    Level,
    LoadType,
    MotionMode,
    MotionNightMode,
    MotionSnooze,
    Power,
    StatusLED,
    StatusLEDMode,
    TimePeriod,
)

_LOGGER = logging.getLogger(__name__)


class Device:
    """Device."""

    def __init__(self, api, residence, data) -> None:
        """Initialize."""
        self.api = api
        self.residence = residence
        self.data = data

    @property
    def name(self) -> str | None:
        """Name."""
        return self.data.get("name")

    @property
    def power(self) -> str | None:
        """Power."""
        return self.data.get("power")

    @power.setter
    def power(self, value: Literal[Power.OFF, Power.ON]) -> None:
        if value not in (Power.OFF, Power.ON):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"power": value},
        )

    @property
    def is_on(self) -> bool:
        """Is on."""
        return bool(self.power == Power.ON)

    def turn_on(self) -> None:
        """Turn on."""
        setattr(self, "power", Power.ON)

    def turn_off(self) -> None:
        """Turn off."""
        setattr(self, "power", Power.OFF)

    @property
    def brightness(self) -> int | None:
        """Brightness."""
        return self.data.get("brightness")

    @brightness.setter
    def brightness(self, value: int) -> None:
        if not isinstance(value, int):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"power": Power.ON, "brightness": value},
        )

    def set_brightness(self, value: int) -> None:
        """Set brightness."""
        setattr(self, "brightness", value)

    def set_speed(self, value: int) -> None:
        """Set speed."""
        self.set_brightness(value)

    @property
    def manufacturer(self) -> str | None:
        """Manufacturer."""
        return self.data.get("manufacturer")

    @property
    def model(self) -> str | None:
        """Model."""
        return self.data.get("model")

    @property
    def serial(self) -> str | None:
        """Serial."""
        return self.data.get("serial")

    @property
    def version(self) -> str | None:
        """Version."""
        return self.data.get("version")

    @property
    def min_level(self) -> int | None:
        """Minimum level."""
        return self.data.get("minLevel")

    @min_level.setter
    def min_level(self, value: int) -> None:
        if any(
            [
                all(
                    [
                        self.is_fan,
                        value < Level.MINIMUM_FAN,
                    ]
                ),
                all(
                    [
                        self.is_light,
                        value < Level.MINIMUM_LIGHT,
                    ]
                ),
                value > Level.MAXIMUM,
                not self.can_set_level,
            ]
        ):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"minLevel": int(value), "maxLevel": self.max_level},
        )

    @property
    def max_level(self) -> int | None:
        """Maximum level."""
        return self.data.get("maxLevel")

    @max_level.setter
    def max_level(self, value: int) -> None:
        if any(
            [
                all(
                    [
                        self.is_fan,
                        value < Level.MINIMUM_FAN,
                    ]
                ),
                all(
                    [
                        self.is_light,
                        value < Level.MINIMUM_LIGHT,
                    ]
                ),
                value > Level.MAXIMUM,
                not self.can_set_level,
            ]
        ):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"minLevel": self.min_level, "maxLevel": int(value)},
        )

    @property
    def can_set_level(self) -> bool | None:
        """Can set level."""
        return self.data.get("canSetLevel")

    @property
    def connected(self) -> bool | None:
        """Connected."""
        return self.data.get("connected")

    @property
    def is_connected(self) -> bool:
        """Is connected."""
        return bool(self.connected)

    @property
    def local_ip(self) -> str | None:
        """Local IP."""
        return self.data.get("localIP")

    @property
    def bridge_id(self) -> int | None:
        """Bridge ID."""
        return self.data.get("iotBridgeId")

    @property
    def bridge_serial(self) -> str | None:
        """Bridge serial."""
        return self.data.get("iotBridgeSerial")

    @property
    def has_bridge(self) -> bool:
        """Has bridge."""
        return bool(self.bridge_id or self.bridge_serial)

    @property
    def created(self) -> str | None:
        """Created."""
        return self.data.get("created")

    @property
    def last_updated(self) -> str | None:
        """Last updated."""
        return self.data.get("lastUpdated")

    @property
    def residence_id(self) -> int | None:
        """Residence ID."""
        return self.data.get("residenceId")

    @property
    def residential_room_id(self) -> int | None:
        """Residential room ID."""
        return self.data.get("residentialRoomId")

    @property
    def room_name(self) -> str | None:
        """Room name."""
        for room in self.residence.rooms:
            if room.id == self.residential_room_id:
                return room.name
        return None

    @property
    def mac(self) -> str | None:
        """MAC address."""
        return self.data.get("mac")

    @property
    def id(self) -> int | None:
        """ID."""
        return self.data.get("id")

    @property
    def random_enabled(self) -> bool | None:
        """Random enabled."""
        return self.data.get("isRandomEnabled")

    @random_enabled.setter
    def random_enabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"isRandomEnabled": value},
        )

    @property
    def status_led(self) -> int | None:
        """Status LED."""
        return self.data.get("statusLED")

    @property
    def status_led_behavior(self) -> str | None:
        """Status LED behavior."""
        if self.status_led is not None:
            return STATUS_LED_MODE_MAP.get(self.status_led, StatusLEDMode.UNKNOWN)
        return StatusLEDMode.UNKNOWN

    @property
    def status_led_behavior_options(self) -> list[str]:
        """Status LED behavior options."""
        return list(STATUS_LED_MODE_MAP.values())

    @property
    def supports_status_led_behavior(self) -> bool:
        """Supports status LED behavior configuration."""
        return not self.is_controller and not self.is_gfci

    @status_led_behavior.setter
    def status_led_behavior(self, value: str) -> None:
        if value not in self.status_led_behavior_options:
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={
                "statusLED": list(STATUS_LED_MODE_MAP.keys())[
                    self.status_led_behavior_options.index(value)
                ]
            },
        )

    @property
    def status_led_enabled(self) -> bool:
        """Status LED enabled."""
        return bool(self.status_led == StatusLED.ENABLED)

    @status_led_enabled.setter
    def status_led_enabled(self, value: bool) -> None:
        if any(
            [
                not isinstance(value, bool),
                not self.is_controller,
            ]
        ):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"statusLED": StatusLED.ENABLED if value else StatusLED.DISABLED},
        )

    @property
    def dim_led(self) -> int | None:
        """Dim LED."""
        return self.data.get("dimLED")

    @property
    def led_bar_behavior(self) -> str | None:
        """LED bar behavior."""
        if self.dim_led is not None:
            return DIM_LED_MAP.get(self.dim_led, TimePeriod.UNKNOWN)
        return TimePeriod.UNKNOWN

    @property
    def led_bar_behavior_options(self) -> list[str]:
        """LED bar behavior options."""
        return list(DIM_LED_MAP.values())

    @led_bar_behavior.setter
    def led_bar_behavior(self, value: str) -> None:
        if any(
            [
                value not in self.led_bar_behavior_options,
                not self.can_set_level,
            ]
        ):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={
                "dimLED": list(DIM_LED_MAP.keys())[
                    self.led_bar_behavior_options.index(value)
                ]
            },
        )

    @property
    def load_type(self) -> int | None:
        """Load type."""
        return self.data.get("loadType")

    @property
    def bulb_type(self) -> str | None:
        """Bulb type."""
        if self.load_type is not None:
            return LOAD_TYPE_MAP.get(self.load_type, LoadType.UNKNOWN)
        return LoadType.UNKNOWN

    @property
    def bulb_type_options(self) -> list[LoadType]:
        """Bulb type options."""
        options = list(LOAD_TYPE_MAP.values())
        if self.is_elv_capable:
            options.remove(LoadType.MLV)
        else:
            options.remove(LoadType.ELV)
        return options

    @bulb_type.setter
    def bulb_type(self, value: LoadType) -> None:
        if any(
            [
                value not in self.bulb_type_options,
                not self.can_set_level,
                not self.is_light,
            ]
        ):
            return
        json_value = list(LOAD_TYPE_MAP.keys())[self.bulb_type_options.index(value)]
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"loadType": json_value},
        )

    @property
    def fade_off_time(self) -> int | None:
        """Fade off time."""
        return self.data.get("fadeOffTime")

    @property
    def fade_on_time(self) -> int | None:
        """Fade on time."""
        return self.data.get("fadeOnTime")

    @property
    def fade_off_rate(self) -> str | None:
        """Fade off rate."""
        if self.fade_off_time is not None:
            return FADE_ON_OFF_RATE_MAP.get(self.fade_off_time, TimePeriod.UNKNOWN)
        return TimePeriod.UNKNOWN

    @property
    def fade_on_rate(self) -> str | None:
        """Fade on rate."""
        if self.fade_on_time is not None:
            return FADE_ON_OFF_RATE_MAP.get(self.fade_on_time, TimePeriod.UNKNOWN)
        return TimePeriod.UNKNOWN

    @property
    def fade_on_off_rate_options(self) -> list[str]:
        """Fade on off rate options."""
        return list(FADE_ON_OFF_RATE_MAP.values())

    @fade_off_rate.setter
    def fade_off_rate(self, value: str) -> None:
        if any(
            [
                value not in self.fade_on_off_rate_options,
                not self.can_set_level,
                not self.is_light,
            ]
        ):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={
                "fadeOffTime": list(FADE_ON_OFF_RATE_MAP.keys())[
                    self.fade_on_off_rate_options.index(value)
                ]
            },
        )

    @fade_on_rate.setter
    def fade_on_rate(self, value: str) -> None:
        if any(
            [
                value not in self.fade_on_off_rate_options,
                not self.can_set_level,
                not self.is_light,
            ]
        ):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={
                "fadeOnTime": list(FADE_ON_OFF_RATE_MAP.keys())[
                    self.fade_on_off_rate_options.index(value)
                ]
            },
        )

    @property
    def preset_level(self) -> int | None:
        """Preset level."""
        return self.data.get("presetLevel")

    @preset_level.setter
    def preset_level(self, value: int) -> None:
        if any(
            [
                not self.can_set_level,
                all(
                    [
                        not self.is_fan,
                        not self.is_light,
                    ]
                ),
            ]
        ):
            _LOGGER.debug("[%s] Unable to set preset level", self.name)
            return
        _LOGGER.debug("[%s] Setting preset level to: %s%%", self.name, int(value))
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"presetLevel": int(value)},
        )

    def identify(self) -> None:
        """Identify."""
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"identify": 10},
        )

    @property
    def auto_off_time(self) -> int | None:
        """Auto off time."""
        return self.data.get("autoOffTime")

    @property
    def auto_shutoff(self) -> str | None:
        """Auto shutoff."""
        if self.auto_off_time is not None:
            return AUTO_SHUTOFF_MAP[self.auto_off_time]
        return None

    @property
    def auto_shutoff_options(self) -> list[str]:
        """Auto shutoff options."""
        return list(AUTO_SHUTOFF_MAP.values())

    @property
    def supports_auto_shutoff(self) -> bool:
        """Supports auto shutoff configuration."""
        return not self.has_motion_sensor and not self.is_gfci

    @auto_shutoff.setter
    def auto_shutoff(self, value: str) -> None:
        if any(
            [
                value not in self.auto_shutoff_options,
                self.has_motion_sensor,
            ]
        ):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={
                "autoOffTime": list(AUTO_SHUTOFF_MAP.keys())[
                    self.auto_shutoff_options.index(value)
                ]
            },
        )

    @property
    def ota_status(self) -> int | None:
        """OTA status."""
        return self.data.get("otaStatus")

    @property
    def update_downloading(self) -> bool:
        """Updating downloading."""
        return bool(self.ota_status == 3)

    @property
    def update_ready(self) -> bool:
        """Update ready."""
        return bool(self.ota_status in [0, 2])

    @property
    def update_version(self) -> str | None:
        """Update version."""
        downloaded = self.data.get("downloaded")
        if downloaded == "0.0.0":
            return self.version
        return downloaded

    def apply_update(self) -> None:
        """Apply update."""
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"apply_ota": 2},
        )

    @property
    def triac_off(self) -> int | None:
        """Triac off."""
        return self.data.get("triacOff")

    @property
    def control_timing(self) -> str:
        """Control timing."""
        if self.triac_off is not None:
            return CONTROL_TIMING_MAP.get(self.triac_off, ControlTiming.UNKNOWN)
        return ControlTiming.UNKNOWN

    @property
    def control_timing_options(self) -> list[str]:
        """Control timing options."""
        return list(CONTROL_TIMING_MAP.values())

    @control_timing.setter
    def control_timing(self, value: str) -> None:
        if any(
            [
                value not in self.control_timing_options,
                not self.can_set_level,
                not self.is_light,
            ]
        ):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={
                "triacOff": list(CONTROL_TIMING_MAP.keys())[
                    self.control_timing_options.index(value)
                ]
            },
        )

    @property
    def night_preset_level(self) -> int | None:
        """Night preset level."""
        return self.data.get("motionNightLevel")

    @night_preset_level.setter
    def night_preset_level(self, value: int) -> None:
        if any(
            [
                not self.can_set_level,
                all(
                    [
                        not self.is_light,
                    ]
                ),
            ]
        ):
            _LOGGER.debug("[%s] Unable to set night preset level", self.name)
            return
        _LOGGER.debug("[%s] Setting night preset level to: %s%%", self.name, int(value))
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"motionNightLevel": int(value)},
        )

    @property
    def motion_night_mode(self) -> str | None:
        """Motion night mode."""
        value = self.data.get("motionNightMode")
        if value is not None:
            return MOTION_NIGHT_MODE_MAP.get(value, MotionNightMode.UNKNOWN)
        return MotionNightMode.UNKNOWN

    @property
    def motion_night_mode_options(self) -> list[str]:
        """Motion night mode options."""
        return list(MOTION_NIGHT_MODE_MAP.values())

    @motion_night_mode.setter
    def motion_night_mode(self, value: str) -> None:
        if any(
            [
                value not in self.motion_night_mode_options,
                not self.has_motion_sensor,
            ]
        ):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={
                "motionNightMode": list(MOTION_NIGHT_MODE_MAP.keys())[
                    self.motion_night_mode_options.index(value)
                ]
            },
        )

    @property
    def light_enable(self) -> bool | None:
        """Light enable."""
        return self.data.get("lightEnable")

    @property
    def light_sensor_enabled(self) -> bool:
        """Light sensor enabled."""
        return bool(self.light_enable)

    @light_sensor_enabled.setter
    def light_sensor_enabled(self, value: bool) -> None:
        if any(
            [
                not isinstance(value, bool),
                not self.has_light_sensor,
            ]
        ):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"lightEnable": bool(value)},
        )

    @property
    def motion_disable(self) -> bool | None:
        """Motion disable."""
        return self.data.get("motionDisable")

    @property
    def motion_detection_enabled(self) -> bool:
        """Motion detection enabled."""
        return not bool(self.motion_disable)

    @motion_detection_enabled.setter
    def motion_detection_enabled(self, value: bool) -> None:
        if any(
            [
                not isinstance(value, bool),
                not self.has_motion_sensor,
            ]
        ):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"motionDisable": (not bool(value))},
        )

    @property
    def motion_led_feedback_enabled(self) -> bool | None:
        """Motion LED feedback enabled."""
        return self.data.get("motionLED")

    @motion_led_feedback_enabled.setter
    def motion_led_feedback_enabled(self, value: bool) -> None:
        if any(
            [
                not isinstance(value, bool),
                not self.has_motion_sensor,
            ]
        ):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"motionLED": value},
        )

    @property
    def motion_mode(self) -> str | None:
        """Motion mode."""
        value = self.data.get("motionMode")
        if value is not None:
            return MOTION_MODE_MAP.get(value, MotionMode.UNKNOWN)
        return MotionMode.UNKNOWN

    @property
    def motion_mode_options(self) -> list[str]:
        """Motion mode options."""
        return list(MOTION_MODE_MAP.values())

    @motion_mode.setter
    def motion_mode(self, value: str) -> None:
        if any(
            [
                value not in self.motion_mode_options,
                not self.has_motion_sensor,
            ]
        ):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={
                "motionMode": list(MOTION_MODE_MAP.keys())[
                    self.motion_mode_options.index(value)
                ]
            },
        )

    @property
    def motion_timeout(self) -> str | None:
        """Motion timeout."""
        value = self.data.get("motionTimeout")
        if value is not None:
            return MOTION_TIMEOUT_MAP.get(value, TimePeriod.UNKNOWN)
        return TimePeriod.UNKNOWN

    @property
    def motion_timeout_options(self) -> list[str]:
        """Motion timeout options."""
        return list(MOTION_TIMEOUT_MAP.values())

    @motion_timeout.setter
    def motion_timeout(self, value: str) -> None:
        if any(
            [
                value not in self.motion_timeout_options,
                not self.has_motion_sensor,
            ]
        ):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={
                "motionTimeout": list(MOTION_TIMEOUT_MAP.keys())[
                    self.motion_timeout_options.index(value)
                ]
            },
        )

    @property
    def motion_occupied(self) -> bool | None:
        """Motion occupied."""
        return self.data.get("motionOccupied")

    @property
    def motion_disable_time(self) -> int | None:
        """Motion disable time."""
        return self.data.get("motionDisableTime")

    @property
    def motion_snooze(self) -> str | None:
        """Motion snooze."""
        disable = self.motion_disable
        time = self.motion_disable_time
        if disable is not None and time is not None:
            if not disable or not time:
                return MotionSnooze.DISABLED
            return MOTION_SNOOZE_MAP.get(time, MotionSnooze.UNKNOWN)
        return MotionSnooze.UNKNOWN

    @property
    def motion_snooze_options(self) -> list[str]:
        """Motion snooze options."""
        return list(MOTION_SNOOZE_MAP.values())

    @motion_snooze.setter
    def motion_snooze(self, value: str) -> None:
        if any(
            [
                value not in self.motion_snooze_options,
                not self.has_motion_sensor,
            ]
        ):
            return
        json = {"motionDisable": False}
        if json_value := list(MOTION_SNOOZE_MAP.keys())[
            self.motion_snooze_options.index(value)
        ]:
            json = {"motionDisable": True, "motionDisableTime": json_value}
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json=json,
        )

    @property
    def motion_ambient_threshold(self) -> int | None:
        """Motion ambient threshold."""
        return self.data.get("motionAmbientThr")

    @motion_ambient_threshold.setter
    def motion_ambient_threshold(self, value: int) -> None:
        if not self.has_motion_sensor:
            _LOGGER.debug("[%s] Unable to set motion ambient threshold", self.name)
            return
        _LOGGER.debug(
            "[%s] Setting motion ambient threshold to: %s%%", self.name, int(value)
        )
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"motionAmbientThr": int(value)},
        )

    @property
    def matter_manual_code(self) -> str | None:
        """Matter manual code."""
        return self.data.get("matterManualCode")

    @property
    def _matter_qr_code(self) -> str | None:
        return self.data.get("matterQRCode")

    @property
    def matter_qr_code(self) -> bytes | None:
        """Matter QR code."""
        if self._matter_qr_code is None:
            return None
        qr_stream = io.BytesIO()
        qr_code = pyqrcode.create(self._matter_qr_code)
        qr_code.png(qr_stream, scale=5, module_color="#000", background="#FFF")
        return qr_stream.getvalue()

    @property
    def fault_detected(self) -> bool | None:
        """Fault detected."""
        return bool(self.fault_status != GFCIStatus.PROTECTED)

    @property
    def fault_status(self) -> str | None:
        """Fault status."""
        fault = self.data.get("fault")
        if fault is not None:
            return GFCI_STATUS_MAP.get(fault, GFCIStatus.UNKNOWN)
        return GFCIStatus.UNKNOWN

    @property
    def buzzer_enabled(self) -> bool | None:
        """Buzzer enabled."""
        return self.data.get("enableBuzzer")

    @buzzer_enabled.setter
    def buzzer_enabled(self, value: bool) -> None:
        if any(
            [
                not isinstance(value, bool),
                not self.is_gfci,
            ]
        ):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"enableBuzzer": bool(value)},
        )

    def silence_buzzer(self) -> None:
        """Silence buzzer."""
        if not self.is_gfci:
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"silenceBuzzer": True},
        )

    @property
    def signal_strength(self) -> int | None:
        """Signal strength."""
        return self.data.get("rssi")

    @property
    def dimming_mode(self) -> str | None:
        """Dimming mode."""
        value = self.data.get("reversePhase")
        if value is not None:
            return DimmingMode.REVERSE if value else DimmingMode.FORWARD
        return DimmingMode.UNKNOWN

    @property
    def dimming_mode_options(self) -> list[str]:
        """Dimming mode options."""
        return [DimmingMode.FORWARD, DimmingMode.REVERSE]

    @dimming_mode.setter
    def dimming_mode(self, value: str) -> None:
        if any(
            [
                value not in self.dimming_mode_options,
                not self.is_elv_capable,
            ]
        ):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"reversePhase": bool(value == DimmingMode.REVERSE)},
        )

    @property
    def buttons(self) -> list[Button]:
        """Button."""
        buttons = [
            Button(self.api, self, button) for button in self.data.get("iotButtons", [])
        ]
        if self.is_generation_two:
            return [button for button in buttons if button.number != 4]
        return buttons

    @property
    def is_supported(self) -> bool:
        """Is supported."""
        return bool(self.model in SUPPORTED_DEVICES_MODEL)

    @property
    def is_controller(self) -> bool:
        """Is controller."""
        return bool(self.model in SUPPORTED_DEVICES_CONTROLLER)

    @property
    def is_fan(self) -> bool:
        """Is fan."""
        return any(
            [
                self.model in SUPPORTED_DEVICES_FAN,
                all(
                    [
                        self.model in SUPPORTED_DEVICES_SWITCH,
                        self.name is not None and "fan" in self.name.lower(),
                    ]
                ),
            ]
        )

    @property
    def is_gfci(self) -> bool:
        """Is GFCI."""
        return bool(self.model in SUPPORTED_DEVICES_GFCI)

    @property
    def is_light(self) -> bool:
        """Is light."""
        return any(
            [
                self.model in SUPPORTED_DEVICES_LIGHT,
                all(
                    [
                        self.model in SUPPORTED_DEVICES_SWITCH,
                        self.name is not None and "light" in self.name.lower(),
                    ]
                ),
            ]
        )

    @property
    def is_outlet(self) -> bool:
        """Is outlet."""
        return all(
            [
                self.model in SUPPORTED_DEVICES_OUTLET,
                not self.is_fan,
                not self.is_light,
            ]
        )

    @property
    def is_switch(self) -> bool:
        """Is switch."""
        return all(
            [
                self.model in SUPPORTED_DEVICES_SWITCH,
                not self.is_fan,
                not self.is_light,
            ]
        )

    @property
    def is_generation_two(self) -> bool:
        """Is second generation."""
        return bool(self.model in SUPPORTED_DEVICES_GENERATION_TWO)

    @property
    def has_led_bar(self) -> bool:
        """Has LED bar."""
        return all(
            [
                self.can_set_level,
                self.model != "D23LP",
            ]
        )

    @property
    def has_light_sensor(self) -> bool:
        """Has light sensor."""
        return bool(self.model == "D215O")

    @property
    def has_motion_sensor(self) -> bool:
        """Has motion sensor."""
        return bool(self.model == "D2MSD")

    @property
    def is_elv_capable(self) -> bool:
        """Is ELV capable."""
        return bool(self.model == "D2ELV")

    @property
    def is_matter_capable(self) -> bool:
        """Is matter capable."""
        return bool(self._matter_qr_code)
