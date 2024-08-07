"""Leviton API"""
from __future__ import annotations

import io
import logging
import pyqrcode

from .button import Button
from .const import (
    AUTO_SHUTOFF_MAP,
    BULB_THRESHOLD_MAP,
    BULB_THRESHOLD_UNKNOWN,
    DIM_LED_MAP,
    FADE_ON_OFF_RATE_MAP,
    GFCI_STATUS_MAP,
    GFCI_STATUS_PROTECTED,
    GFCI_STATUS_UNKNOWN,
    LOAD_TYPE_MAP,
    LOAD_TYPE_UNKNOWN,
    MAXIMUM_LEVEL,
    MINIMUM_LEVEL_FAN,
    MINIMUM_LEVEL_LIGHT,
    MOTION_AMBIENT_THRESHOLD_MAP,
    MOTION_AMBIENT_THRESHOLD_UNKNOWN,
    MOTION_SNOOZE_DISABLED,
    MOTION_SNOOZE_MAP,
    MOTION_SNOOZE_UNKNOWN,
    MOTION_MODE_MAP,
    MOTION_MODE_UNKNOWN,
    MOTION_NIGHT_MODE_MAP,
    MOTION_NIGHT_MODE_UNKNOWN,
    MOTION_TIMEOUT_MAP,
    MOTION_TIMEOUT_UNKNOWN,
    SECOND_GENERATION_MODELS,
    STATUS_LED_DISABLED,
    STATUS_LED_ENABLED,
    STATUS_LED_MODE_MAP,
    STATUS_LED_MODE_UNKNOWN,
    SUPPORTED_MODELS_CONTROLLER,
    SUPPORTED_MODELS_FAN,
    SUPPORTED_MODELS_GFCI,
    SUPPORTED_MODELS_LIGHT,
    SUPPORTED_MODELS_LIGHT_SENSOR,
    SUPPORTED_MODELS_MOTION_SENSOR,
    SUPPORTED_MODELS_OUTLET,
    SUPPORTED_MODELS_SWITCH,
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
        if value not in ("ON", "OFF"):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"power": value},
        )

    @property
    def is_on(self) -> bool:
        return bool(self.power == "ON")

    def turn_on(self) -> None:
        setattr(self, "power", "ON")
    
    def turn_off(self) -> None:
        setattr(self, "power", "OFF")
    
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
            json={"power": "ON", "brightness": value},
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
        if value not in STATUS_LED_MODE_MAP.values():
            return
        value = list(STATUS_LED_MODE_MAP.keys())[list(STATUS_LED_MODE_MAP.values()).index(value)]
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
                value not in DIM_LED_MAP.values(),
                not self.can_set_level,
            ]
        ):
            return
        value = list(DIM_LED_MAP.keys())[list(DIM_LED_MAP.values()).index(value)]
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
        return list(LOAD_TYPE_MAP.values())

    @bulb_type.setter
    def bulb_type(self, value: str) -> None:
        if any(
            [
                value not in LOAD_TYPE_MAP.values(),
                not self.can_set_level,
                not self.is_light,
            ]
        ):
            return
        value = list(LOAD_TYPE_MAP.keys())[list(LOAD_TYPE_MAP.values()).index(value)]
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
                value not in FADE_ON_OFF_RATE_MAP.values(),
                not self.can_set_level,
                not self.is_light,
            ]
        ):
            return
        value = list(FADE_ON_OFF_RATE_MAP.keys())[list(FADE_ON_OFF_RATE_MAP.values()).index(value)]
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"fadeOffTime": value},
        )

    @fade_on_rate.setter
    def fade_on_rate(self, value: str) -> None:
        if any(
            [
                value not in FADE_ON_OFF_RATE_MAP.values(),
                not self.can_set_level,
                not self.is_light,
            ]
        ):
            return
        value = list(FADE_ON_OFF_RATE_MAP.keys())[list(FADE_ON_OFF_RATE_MAP.values()).index(value)]
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
                value not in AUTO_SHUTOFF_MAP.values(),
                self.is_motion_sensor,
            ]
        ):
            return
        value = list(AUTO_SHUTOFF_MAP.keys())[list(AUTO_SHUTOFF_MAP.values()).index(value)]
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
    def bulb_threshold(self) -> str:
        if self.triac_off is not None:
            return BULB_THRESHOLD_MAP.get(self.triac_off, BULB_THRESHOLD_UNKNOWN)
        return BULB_THRESHOLD_UNKNOWN

    @property
    def bulb_threshold_options(self) -> list[str] | None:
        return list(BULB_THRESHOLD_MAP.values())

    @bulb_threshold.setter
    def bulb_threshold(self, value: str) -> None:
        if any(
            [
                value not in BULB_THRESHOLD_MAP.values(),
                not self.can_set_level,
                not self.is_light,
            ]
        ):
            return
        value = list(BULB_THRESHOLD_MAP.keys())[list(BULB_THRESHOLD_MAP.values()).index(value)]
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
                value not in MOTION_NIGHT_MODE_MAP.values(),
                not self.is_motion_sensor,
            ]
        ):
            return
        value = list(MOTION_NIGHT_MODE_MAP.keys())[list(MOTION_NIGHT_MODE_MAP.values()).index(value)]
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
                not self.is_light_sensor,
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
                not self.is_motion_sensor,
            ]
        ):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"motionDisable": (not bool(value))},
        )

    @property
    def motion_led_feedback(self) -> bool | None:
        return self.data.get("motionLED")

    @motion_led_feedback.setter
    def motion_led_feedback(self, value: bool) -> None:
        if any(
            [
                not isinstance(value, bool),
                not self.is_motion_sensor,
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

    @motion_mode.setter
    def motion_mode(self, value: str) -> None:
        if any(
            [
                value not in MOTION_MODE_MAP.values(),
                not self.is_motion_sensor,
            ]
        ):
            return
        value = list(MOTION_MODE_MAP.keys())[list(MOTION_MODE_MAP.values()).index(value)]
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"motionMode": value},
        )

    @property
    def motion_mode_options(self) -> list[str] | None:
        return list(MOTION_MODE_MAP.values())

    @property
    def motion_timeout(self) -> str | None:
        value = self.data.get("motionTimeout")
        if value is not None:
            return MOTION_TIMEOUT_MAP.get(value, MOTION_TIMEOUT_UNKNOWN)
        return MOTION_TIMEOUT_UNKNOWN

    @motion_timeout.setter
    def motion_timeout(self, value: str) -> None:
        if any(
            [
                value not in MOTION_TIMEOUT_MAP.values(),
                not self.is_motion_sensor,
            ]
        ):
            return
        value = list(MOTION_TIMEOUT_MAP.keys())[list(MOTION_TIMEOUT_MAP.values()).index(value)]
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"motionTimeout": value},
        )

    @property
    def motion_timeout_options(self) -> list[str] | None:
        return list(MOTION_TIMEOUT_MAP.values())

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

    @motion_snooze.setter
    def motion_snooze(self, value: str) -> None:
        if any(
            [
                value not in MOTION_SNOOZE_MAP.values(),
                not self.is_motion_sensor,
            ]
        ):
            return
        value = list(MOTION_SNOOZE_MAP.keys())[list(MOTION_SNOOZE_MAP.values()).index(value)]
        json = {"motionDisable": False}
        if value:
            json = {"motionDisable": True, "motionDisableTime": value}
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json=json,
        )

    @property
    def motion_snooze_options(self) -> list[str] | None:
        return list(MOTION_SNOOZE_MAP.values())

    @property
    def motion_ambient_threshold(self) -> int | None:
        value = self.data.get("motionAmbientThr")
        if value is not None:
            return MOTION_AMBIENT_THRESHOLD_MAP.get(value, MOTION_AMBIENT_THRESHOLD_UNKNOWN)
        return MOTION_AMBIENT_THRESHOLD_UNKNOWN

    @motion_ambient_threshold.setter
    def motion_ambient_threshold(self, value: str) -> None:
        if any(
            [
                value not in MOTION_AMBIENT_THRESHOLD_MAP.values(),
                not self.is_motion_sensor,
            ]
        ):
            return
        value = list(MOTION_AMBIENT_THRESHOLD_MAP.keys())[list(MOTION_AMBIENT_THRESHOLD_MAP.values()).index(value)]
        self.api.call(
            method="put",
            url=f"residences/{self.residence.id}/iotswitches/{self.id}",
            json={"motionAmbientThr": value},
        )

    @property
    def motion_ambient_threshold_options(self) -> list[str] | None:
        return list(MOTION_AMBIENT_THRESHOLD_MAP.values())

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
    def enable_buzzer(self) -> bool | None:
        return self.data.get("enableBuzzer")

    @enable_buzzer.setter
    def enable_buzzer(self, value: bool) -> None:
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
    def buttons(self) -> list[Button]:
        buttons = [Button(self.api, self, button) for button in self.data.get("iotButtons", [])]
        if self.is_second_generation:
            return [button for button in buttons if button.number != 4]
        return buttons

    @property
    def is_controller(self) -> bool:
        return bool(self.model in SUPPORTED_MODELS_CONTROLLER)

    @property
    def is_fan(self) -> bool:
        return any(
            [
                self.model in SUPPORTED_MODELS_FAN,
                all(
                    [
                        self.model in SUPPORTED_MODELS_SWITCH,
                        "fan" in self.name.lower(),
                    ]
                ),
            ]
        )

    @property
    def is_gfci(self) -> bool:
        return bool(self.model in SUPPORTED_MODELS_GFCI)

    @property
    def is_light(self) -> bool:
        return any(
            [
                self.model in SUPPORTED_MODELS_LIGHT,
                all(
                    [
                        self.model in SUPPORTED_MODELS_SWITCH,
                        "light" in self.name.lower(),
                    ]
                ),
            ]
        )

    @property
    def is_light_sensor(self) -> bool:
        return bool(self.model in SUPPORTED_MODELS_LIGHT_SENSOR)

    @property
    def is_motion_sensor(self) -> bool:
        return bool(self.model in SUPPORTED_MODELS_MOTION_SENSOR)

    @property
    def is_outlet(self) -> bool:
        return all(
            [
                self.model in SUPPORTED_MODELS_OUTLET,
                not self.is_fan,
                not self.is_light,
            ]
        )

    @property
    def is_switch(self) -> bool:
        return all(
            [
                self.model in SUPPORTED_MODELS_SWITCH,
                not self.is_fan,
                not self.is_light,
            ]
        )

    @property
    def is_second_generation(self) -> bool:
        return bool(self.model in SECOND_GENERATION_MODELS)

    @property
    def has_led_bar(self) -> bool:
        return all(
            [
                self.can_set_level,
                self.model != "D23LP",
            ]
        )

    @property
    def is_matter_capable(self) -> bool:
        return bool(self._matter_qr_code)

