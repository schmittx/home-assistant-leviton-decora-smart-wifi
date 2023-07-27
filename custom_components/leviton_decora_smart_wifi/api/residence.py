"""Leviton API"""
from __future__ import annotations

from .activity import Activity
from .const import STATUS_MAP, STATUS_UNKNOWN
from .device import Device
from .room import Room
from .schedule import Schedule


class Residence(object):

    def __init__(self, api, data):
        self.api = api
        self.data = data

    @property
    def name(self) -> str | None:
        return self.data.get("name")

    @property
    def name_location(self) -> str:
        return f"{self.name} ({self.locality}, {self.region})"

    @property
    def _status(self) -> str | None:
        return self.data.get("status")

    @property
    def status(self) -> str:
        if self._status is not None:
            return STATUS_MAP.get(self._status, STATUS_UNKNOWN)
        return STATUS_UNKNOWN

    @property
    def status_options(self) -> list[str]:
        return list(STATUS_MAP.values())

    @status.setter
    def status(self, value: str) -> None:
        if value not in STATUS_MAP.values():
            return
        value = list(STATUS_MAP.keys())[list(STATUS_MAP.values()).index(value)]
        self.api.call(
            method="put",
            url=f"residences/{self.id}",
            json={"status": value},
        )

    @property
    def is_away(self) -> bool:
        return bool(self.status == "AWAY")

    @property
    def is_home(self) -> bool:
        return bool(self.status == "HOME")

    def set_away(self) -> None:
        setattr(self, "status", "AWAY")
    
    def set_home(self) -> None:
        setattr(self, "status", "HOME")
    
    @property
    def street(self) -> str | None:
        return self.data.get("street")

    @property
    def locality(self) -> str | None:
        return self.data.get("locality")

    @property
    def region(self) -> str | None:
        return self.data.get("region")

    @property
    def country(self) -> str | None:
        return self.data.get("country")

    @property
    def postcode(self) -> str | None:
        return self.data.get("postcode")

    @property
    def geopoint_lat(self) -> float | int | None:
        return self.data.get("geopoint", {}).get("lat")

    @property
    def geopoint_lng(self) -> float | int | None:
        return self.data.get("geopoint", {}).get("lng")

    @property
    def timezone_id(self) -> str | None:
        return self.data.get("timezone", {}).get("id")

    @property
    def timezone_name(self) -> str | None:
        return self.data.get("timezone", {}).get("name")

    @property
    def created(self) -> str | None:
        return self.data.get("created")

    @property
    def last_updated(self) -> str | None:
        return self.data.get("lastUpdated")

    @property
    def energy_cost(self) -> float | int | None:
        return self.data.get("energyCost")

    @property
    def residential_account_id(self) -> int | None:
        return self.data.get("residentialAccountId")

    @property
    def id(self) -> int | None:
        return self.data.get("id")

    @property
    def night_mode_begin(self) -> int | None:
        return self.data.get("nightModeBegin")

    @property
    def night_mode_end(self) -> int | None:
        return self.data.get("nightModeEnd")

    @property
    def activities(self) -> list[Activity]:
        return [Activity(self.api, self, activity) for activity in self.data.get("activities", [])]

    @property
    def devices(self) -> list[Device]:
        return [Device(self.api, self, device) for device in self.data.get("devices", [])]

    @property
    def rooms(self) -> list[Room]:
        return [Room(self.api, self, room) for room in self.data.get("rooms", [])]

    @property
    def schedules(self) -> list[Schedule]:
        return [Schedule(self.api, self, schedule) for schedule in self.data.get("schedules", [])]
