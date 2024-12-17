"""Leviton API"""
from __future__ import annotations

import io
import logging
import pyqrcode

from .button import Button
from .const import (
    AUTO_SHUTOFF_MAP,
    CONTROL_TIMING_MAP,
    CONTROL_TIMING_UNKNOWN,
    DIM_LED_MAP,
    DIMMING_MODE_FORWARD,
    DIMMING_MODE_REVERSE,
    DIMMING_MODE_UNKNOWN,
    FADE_ON_OFF_RATE_MAP,
    GFCI_STATUS_MAP,
    GFCI_STATUS_PROTECTED,
    GFCI_STATUS_UNKNOWN,
    LOAD_TYPE_ELV,
    LOAD_TYPE_MAP,
    LOAD_TYPE_MLV,
    LOAD_TYPE_UNKNOWN,
    MAXIMUM_LEVEL,
    MINIMUM_LEVEL_FAN,
    MINIMUM_LEVEL_LIGHT,
    MOTION_SNOOZE_DISABLED,
    MOTION_SNOOZE_MAP,
    MOTION_SNOOZE_UNKNOWN,
    MOTION_MODE_MAP,
    MOTION_MODE_UNKNOWN,
    MOTION_NIGHT_MODE_MAP,
    MOTION_NIGHT_MODE_UNKNOWN,
    MOTION_TIMEOUT_MAP,
    MOTION_TIMEOUT_UNKNOWN,
    POWER_OFF,
    POWER_ON,
    STATUS_LED_DISABLED,
    STATUS_LED_ENABLED,
    STATUS_LED_MODE_MAP,
    STATUS_LED_MODE_UNKNOWN,
    SUPPORTED_DEVICES_CONTROLLER,
    SUPPORTED_DEVICES_FAN,
    SUPPORTED_DEVICES_GFCI,
    SUPPORTED_DEVICES_LIGHT,
    SUPPORTED_DEVICES_MODEL,
    SUPPORTED_DEVICES_OUTLET,
    SUPPORTED_DEVICES_SECOND_GENERATION,
    SUPPORTED_DEVICES_SWITCH,
    TIME_PERIOD_UNKNOWN,
)

_LOGGER = logging.getLogger(__name__)


class Device(object):

    def __init__(self, api, residence, data):
        self.api = api
        self.residence = residence
        self.data = data

    @property
    def name(self) -> str | None:
        return self.data.get("name")

    @property
    def power(self) -> str | None:
        return self.data.get("power")

    @power.setter
    def power(self, value: str) -> None:
        if value not in (POWER_OFF, POWER_ON):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"power": value},
        )

    @property
    def is_on(self) -> bool:
        return bool(self.power == POWER_ON)

    def turn_on(self) -> None:
        setattr(self, "power", POWER_ON)
    
    def turn_off(self) -> None:
        setattr(self, "power", POWER_OFF)

    @property
    def brightness(self) -> int | None:
        return self.data.get("brightness")

    @brightness.setter
    def brightness(self, value: int) -> None:
        if not isinstance(value, int):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"power": POWER_ON, "brightness": value},
        )

    def set_brightness(self, value: int) -> None:
        setattr(self, "brightness", value)

    def set_speed(self, value: int) -> None:
        self.set_brightness(value)
    
    @property
    def manufacturer(self) -> str | None:
        return self.data.get("manufacturer")

    @property
    def model(self) -> str | None:
        return self.data.get("model")

    @property
    def serial(self) -> str | None:
        return self.data.get("serial")

    @property
    def version(self) -> str | None:
        return self.data.get("version")

    @property
    def min_level(self) -> int | None:
        return self.data.get("minLevel")

    @min_level.setter
    def min_level(self, value: int) -> None:
        if any(
            [
                all(
                    [
                        self.is_fan,
                        value < MINIMUM_LEVEL_FAN,
                    ]
                ),
                all(
                    [
                        self.is_light,
                        value < MINIMUM_LEVEL_LIGHT,
                    ]
                ),
                value > MAXIMUM_LEVEL,
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
        return self.data.get("maxLevel")

    @max_level.setter
    def max_level(self, value: int) -> None:
        if any(
            [
                all(
                    [
                        self.is_fan,
                        value < MINIMUM_LEVEL_FAN,
                    ]
                ),
                all(
                    [
                        self.is_light,
                        value < MINIMUM_LEVEL_LIGHT,
                    ]
                ),
                value > MAXIMUM_LEVEL,
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
        return self.data.get("canSetLevel")

    @property
    def connected(self) -> bool | None:
        return self.data.get("connected")

    @property
    def is_connected(self) -> bool:
        return bool(self.connected)

    @property
    def local_ip(self) -> str | None:
        return self.data.get("localIP")

    @property
    def created(self) -> str | None:
        return self.data.get("created")

    @property
    def last_updated(self) -> str | None:
        return self.data.get("lastUpdated")

    @property
    def residence_id(self) -> int | None:
        return self.data.get("residenceId")

    @property
    def residential_room_id(self) -> int | None:
        return self.data.get("residentialRoomId")

    @property
    def room_name(self) -> str | None:
        for room in self.residence.rooms:
            if room.id == self.residential_room_id:
                return room.name
        return None

    @property
    def mac(self) -> str | None:
        return self.data.get("mac")

    @property
    def id(self) -> int | None:
        return self.data.get("id")

    @property
    def status_led(self) -> int | None:
        return self.data.get("statusLED")

    @property
    def status_led_behavior(self) -> str | None:
        if self.status_led is not None:
            return STATUS_LED_MODE_MAP.get(self.status_led, STATUS_LED_MODE_UNKNOWN)
        return STATUS_LED_MODE_UNKNOWN

    @property
    def status_led_behavior_options(self) -> list[str] | None:
        return list(STATUS_LED_MODE_MAP.values())

    @status_led_behavior.setter
    def status_led_behavior(self, value: str) -> None:
        if value not in self.status_led_behavior_options:
            return
        value = list(STATUS_LED_MODE_MAP.keys())[self.status_led_behavior_options.index(value)]
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"statusLED": value},
        )

    @property
    def status_led_enabled(self) -> bool:
        return bool(self.status_led == STATUS_LED_ENABLED)

    @status_led_enabled.setter
    def status_led_enabled(self, value: bool) -> None:
        if any(
            [
                not isinstance(value, bool),
                not self.is_controller,
            ]
        ):
            return
        value = STATUS_LED_ENABLED if value else STATUS_LED_DISABLED
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"statusLED": value},
        )

    @property
    def dim_led(self) -> int | None:
        return self.data.get("dimLED")

    @property
    def led_bar_behavior(self) -> str | None:
        if self.dim_led is not None:
            return DIM_LED_MAP.get(self.dim_led, TIME_PERIOD_UNKNOWN)
        return TIME_PERIOD_UNKNOWN

    @property
    def led_bar_behavior_options(self) -> list[str] | None:
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
        value = list(DIM_LED_MAP.keys())[self.led_bar_behavior_options.index(value)]
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"dimLED": value},
        )

    @property
    def load_type(self) -> int | None:
        return self.data.get("loadType")

    @property
    def bulb_type(self) -> str | None:
        if self.load_type is not None:
            return LOAD_TYPE_MAP.get(self.load_type, LOAD_TYPE_UNKNOWN)
        return LOAD_TYPE_UNKNOWN

    @property
    def bulb_type_options(self) -> list[str] | None:
        options = list(LOAD_TYPE_MAP.values())
        if self.is_elv_capable:
            options.remove(LOAD_TYPE_MLV)
        else:
            options.remove(LOAD_TYPE_ELV)
        return options

    @bulb_type.setter
    def bulb_type(self, value: str) -> None:
        if any(
            [
                value not in self.bulb_type_options,
                not self.can_set_level,
                not self.is_light,
            ]
        ):
            return
        value = list(LOAD_TYPE_MAP.keys())[self.bulb_type_options.index(value)]
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"loadType": value},
        )

    @property
    def fade_off_time(self) -> int | None:
        return self.data.get("fadeOffTime")

    @property
    def fade_on_time(self) -> int | None:
        return self.data.get("fadeOnTime")

    @property
    def fade_off_rate(self) -> str | None:
        if self.fade_off_time is not None:
            return FADE_ON_OFF_RATE_MAP.get(self.fade_off_time, TIME_PERIOD_UNKNOWN)
        return TIME_PERIOD_UNKNOWN

    @property
    def fade_on_rate(self) -> str | None:
        if self.fade_on_time is not None:
            return FADE_ON_OFF_RATE_MAP.get(self.fade_on_time, TIME_PERIOD_UNKNOWN)
        return TIME_PERIOD_UNKNOWN

    @property
    def fade_on_off_rate_options(self) -> list[str] | None:
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
        value = list(FADE_ON_OFF_RATE_MAP.keys())[self.fade_on_off_rate_options.index(value)]
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"fadeOffTime": value},
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
        value = list(FADE_ON_OFF_RATE_MAP.keys())[self.fade_on_off_rate_options.index(value)]
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"fadeOnTime": value},
        )

    @property
    def preset_level(self) -> int | None:
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
            _LOGGER.debug(f"[{self.name}] Unable to set preset level")
            return
        _LOGGER.debug(f"[{self.name}] Setting preset level to: {int(value)}%")
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"presetLevel": int(value)},
        )

    def identify(self) -> None:
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"identify": 10},
        )

    @property
    def auto_off_time(self) -> int | None:
        return self.data.get("autoOffTime")

    @property
    def auto_shutoff(self) -> str | None:
        if self.auto_off_time is not None:
            return AUTO_SHUTOFF_MAP[self.auto_off_time]
        return None

    @property
    def auto_shutoff_options(self) -> list[str] | None:
        return list(AUTO_SHUTOFF_MAP.values())

    @auto_shutoff.setter
    def auto_shutoff(self, value: str) -> None:
        if any(
            [
                value not in self.auto_shutoff_options,
                self.has_motion_sensor,
            ]
        ):
            return
        value = list(AUTO_SHUTOFF_MAP.keys())[self.auto_shutoff_options.index(value)]
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"autoOffTime": value},
        )

    @property
    def ota_status(self) -> int | None:
        return self.data.get("otaStatus")

    @property
    def update_downloading(self) -> bool:
        return bool(self.ota_status == 3)

    @property
    def update_ready(self) -> bool:
        return bool(self.ota_status in [0, 2])

    @property
    def update_version(self) -> str | None:
        downloaded = self.data.get("downloaded")
        if downloaded == "0.0.0":
            return self.version
        return downloaded

    def apply_update(self) -> None:
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"apply_ota": 2},
        )

    @property
    def triac_off(self) -> int | None:
        return self.data.get("triacOff")

    @property
    def control_timing(self) -> str:
        if self.triac_off is not None:
            return CONTROL_TIMING_MAP.get(self.triac_off, CONTROL_TIMING_UNKNOWN)
        return CONTROL_TIMING_UNKNOWN

    @property
    def control_timing_options(self) -> list[str] | None:
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
        value = list(CONTROL_TIMING_MAP.keys())[self.control_timing_options.index(value)]
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"triacOff": value},
        )

    @property
    def night_preset_level(self) -> int | None:
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
            _LOGGER.debug(f"[{self.name}] Unable to set night preset level")
            return
        _LOGGER.debug(f"[{self.name}] Setting night preset level to: {int(value)}%")
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"motionNightLevel": int(value)},
        )

    @property
    def motion_night_mode(self) -> str | None:
        value = self.data.get("motionNightMode")
        if value is not None:
            return MOTION_NIGHT_MODE_MAP.get(value, MOTION_NIGHT_MODE_UNKNOWN)
        return MOTION_NIGHT_MODE_UNKNOWN

    @property
    def motion_night_mode_options(self) -> list[str] | None:
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
        value = list(MOTION_NIGHT_MODE_MAP.keys())[self.motion_night_mode_options.index(value)]
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"motionNightMode": value},
        )

    @property
    def light_enable(self) -> bool | None:
        return self.data.get("lightEnable")

    @property
    def light_sensor_enabled(self) -> bool:
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
        return self.data.get("motionDisable")

    @property
    def motion_detection_enabled(self) -> bool:
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
        value = self.data.get("motionMode")
        if value is not None:
            return MOTION_MODE_MAP.get(value, MOTION_MODE_UNKNOWN)
        return MOTION_MODE_UNKNOWN

    @property
    def motion_mode_options(self) -> list[str] | None:
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
        value = list(MOTION_MODE_MAP.keys())[self.motion_mode_options.index(value)]
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"motionMode": value},
        )

    @property
    def motion_timeout(self) -> str | None:
        value = self.data.get("motionTimeout")
        if value is not None:
            return MOTION_TIMEOUT_MAP.get(value, MOTION_TIMEOUT_UNKNOWN)
        return MOTION_TIMEOUT_UNKNOWN

    @property
    def motion_timeout_options(self) -> list[str] | None:
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
        value = list(MOTION_TIMEOUT_MAP.keys())[self.motion_timeout_options.index(value)]
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"motionTimeout": value},
        )

    @property
    def motion_occupied(self) -> bool | None:
        return self.data.get("motionOccupied")

    @property
    def motion_disable_time(self) -> int | None:
        return self.data.get("motionDisableTime")

    @property
    def motion_snooze(self) -> str | None:
        disable = self.motion_disable
        time = self.motion_disable_time
        if disable is not None and time is not None:
            if not disable or not time:
                return MOTION_SNOOZE_DISABLED
            return MOTION_SNOOZE_MAP.get(time, MOTION_SNOOZE_UNKNOWN)
        return MOTION_SNOOZE_UNKNOWN

    @property
    def motion_snooze_options(self) -> list[str] | None:
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
        value = list(MOTION_SNOOZE_MAP.keys())[self.motion_snooze_options.index(value)]
        json = {"motionDisable": False}
        if value:
            json = {"motionDisable": True, "motionDisableTime": value}
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json=json,
        )

    @property
    def motion_ambient_threshold(self) -> int | None:
        return self.data.get("motionAmbientThr")

    @motion_ambient_threshold.setter
    def motion_ambient_threshold(self, value: int) -> None:
        if not self.has_motion_sensor:
            _LOGGER.debug(f"[{self.name}] Unable to set motion ambient threshold")
            return
        _LOGGER.debug(f"[{self.name}] Setting motion ambient threshold to: {int(value)}%")
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"motionAmbientThr": int(value)},
        )

    @property
    def matter_manual_code(self) -> str | None:
        return self.data.get("matterManualCode")

    @property
    def _matter_qr_code(self) -> str | None:
        return self.data.get("matterQRCode")

    @property
    def matter_qr_code(self) -> bytes | None:
        if self._matter_qr_code is None:
            return None
        qr_stream = io.BytesIO()
        qr_code = pyqrcode.create(self._matter_qr_code)
        qr_code.png(qr_stream, scale=5, module_color="#000", background="#FFF")
        return qr_stream.getvalue()

    @property
    def fault_detected(self) -> bool | None:
        return bool(self.fault_status != GFCI_STATUS_PROTECTED)

    @property
    def fault_status(self) -> str | None:
        fault = self.data.get("fault")
        if fault is not None:
            return GFCI_STATUS_MAP.get(fault, GFCI_STATUS_UNKNOWN)
        return GFCI_STATUS_UNKNOWN

    @property
    def buzzer_enabled(self) -> bool | None:
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
        if not self.is_gfci:
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"silenceBuzzer": True},
        )

    @property
    def signal_strength(self) -> int | None:
        return self.data.get("rssi")

    @property
    def dimming_mode(self) -> str | None:
        value = self.data.get("reversePhase")
        if value is not None:
            return DIMMING_MODE_REVERSE if value else DIMMING_MODE_FORWARD
        return DIMMING_MODE_UNKNOWN

    @property
    def dimming_mode_options(self) -> list[str] | None:
        return [DIMMING_MODE_FORWARD, DIMMING_MODE_REVERSE]

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
            json={"reversePhase": bool(value == DIMMING_MODE_REVERSE)},
        )

    @property
    def buttons(self) -> list[Button]:
        buttons = [Button(self.api, self, button) for button in self.data.get("iotButtons", [])]
        if self.is_second_generation:
            return [button for button in buttons if button.number != 4]
        return buttons

    @property
    def is_supported(self) -> bool:
        return bool(self.model in SUPPORTED_DEVICES_MODEL)   

    @property
    def is_controller(self) -> bool:
        return bool(self.model in SUPPORTED_DEVICES_CONTROLLER)

    @property
    def is_fan(self) -> bool:
        return any(
            [
                self.model in SUPPORTED_DEVICES_FAN,
                all(
                    [
                        self.model in SUPPORTED_DEVICES_SWITCH,
                        "fan" in self.name.lower(),
                    ]
                ),
            ]
        )

    @property
    def is_gfci(self) -> bool:
        return bool(self.model in SUPPORTED_DEVICES_GFCI)

    @property
    def is_light(self) -> bool:
        return any(
            [
                self.model in SUPPORTED_DEVICES_LIGHT,
                all(
                    [
                        self.model in SUPPORTED_DEVICES_SWITCH,
                        "light" in self.name.lower(),
                    ]
                ),
            ]
        )

    @property
    def is_outlet(self) -> bool:
        return all(
            [
                self.model in SUPPORTED_DEVICES_OUTLET,
                not self.is_fan,
                not self.is_light,
            ]
        )

    @property
    def is_switch(self) -> bool:
        return all(
            [
                self.model in SUPPORTED_DEVICES_SWITCH,
                not self.is_fan,
                not self.is_light,
            ]
        )

    @property
    def is_second_generation(self) -> bool:
        return bool(self.model in SUPPORTED_DEVICES_SECOND_GENERATION)

    @property
    def has_led_bar(self) -> bool:
        return all(
            [
                self.can_set_level,
                self.model != "D23LP",
            ]
        )

    @property
    def has_light_sensor(self) -> bool:
        return bool(self.model == "D215O")

    @property
    def has_motion_sensor(self) -> bool:
        return bool(self.model == "D2MSD")

    @property
    def is_elv_capable(self) -> bool:
        return bool(self.model == "D2ELV")

    @property
    def is_matter_capable(self) -> bool:
        return bool(self._matter_qr_code)
