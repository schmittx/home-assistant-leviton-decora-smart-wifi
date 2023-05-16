"""Leviton API"""
from __future__ import annotations


from .device import Device
from .room import Room


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
    def status(self) -> str | None:
        return self.data.get("status")

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
    def rooms(self) -> list[Room]:
        return [Room(self.api, self, room) for room in self.data.get("rooms", [])]

    @property
    def devices(self) -> list[Device]:
        return [Device(self.api, self, device) for device in self.data.get("devices", [])]
