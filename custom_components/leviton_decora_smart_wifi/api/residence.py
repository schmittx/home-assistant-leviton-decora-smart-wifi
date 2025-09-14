"""Leviton API."""

from __future__ import annotations

from typing import Any

from .activity import Activity
from .const import HOME_AWAY_ACTIVITY_DISABLED, STATUS_MAP, STATUS_UNKNOWN
from .device import Device
from .room import Room
from .schedule import Schedule


class Residence:
    """Residence."""

    def __init__(self, api, data) -> None:
        """Initialize."""
        self.api = api
        self.data = data

    @property
    def name(self) -> str | None:
        """Name."""
        return self.data.get("name")

    @property
    def name_location(self) -> str:
        """Name location."""
        return f"{self.name} ({self.locality}, {self.region})"

    @property
    def _status(self) -> str | None:
        return self.data.get("status")

    @property
    def status(self) -> str:
        """Status."""
        if self._status is not None:
            return STATUS_MAP.get(self._status, STATUS_UNKNOWN)
        return STATUS_UNKNOWN

    @property
    def status_options(self) -> list[str]:
        """Status options."""
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
        """Is away."""
        return bool(self.status == "AWAY")

    @property
    def is_home(self) -> bool:
        """Is home."""
        return bool(self.status == "HOME")

    def set_away(self) -> None:
        """Set away."""
        setattr(self, "status", "AWAY")

    def set_home(self) -> None:
        """Set home."""
        setattr(self, "status", "HOME")

    @property
    def auto_update_enabled(self) -> bool | None:
        """Auto update enabled."""
        return self.data.get("isAutoUpdateEnabled")

    @auto_update_enabled.setter
    def auto_update_enabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.id}",
            json={"isAutoUpdateEnabled": value},
        )

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
            url=f"residences/{self.id}",
            json={"isRandomEnabled": value},
        )

    @property
    def street(self) -> str | None:
        """Street."""
        return self.data.get("street")

    @property
    def locality(self) -> str | None:
        """Locality."""
        return self.data.get("locality")

    @property
    def region(self) -> str | None:
        """Region."""
        return self.data.get("region")

    @property
    def country(self) -> str | None:
        """Country."""
        return self.data.get("country")

    @property
    def postcode(self) -> str | None:
        """Postcode."""
        return self.data.get("postcode")

    @property
    def geopoint_lat(self) -> float | int | None:
        """Geopoint latitude."""
        return self.data.get("geopoint", {}).get("lat")

    @property
    def geopoint_lng(self) -> float | int | None:
        """Geopoint longitude."""
        return self.data.get("geopoint", {}).get("lng")

    @property
    def timezone_id(self) -> str | None:
        """Timezone ID."""
        return self.data.get("timezone", {}).get("id")

    @property
    def timezone_name(self) -> str | None:
        """Timezone name."""
        return self.data.get("timezone", {}).get("name")

    @property
    def created(self) -> str | None:
        """Created."""
        return self.data.get("created")

    @property
    def last_updated(self) -> str | None:
        """Last updated."""
        return self.data.get("lastUpdated")

    @property
    def energy_cost(self) -> float | int | None:
        """Energy cost."""
        return self.data.get("energyCost")

    @property
    def residential_account_id(self) -> int | None:
        """Residential account ID."""
        return self.data.get("residentialAccountId")

    @property
    def id(self) -> int | None:
        """ID."""
        return self.data.get("id")

    @property
    def night_mode_begin(self) -> int | None:
        """Night mode begin."""
        return self.data.get("nightModeBegin")

    @property
    def night_mode_end(self) -> int | None:
        """Night mode end."""
        return self.data.get("nightModeEnd")

    @property
    def home_activity_enabled(self) -> bool | None:
        """Home activity enabled."""
        return self.data.get("isOnHomeActivityEnabled")

    @home_activity_enabled.setter
    def home_activity_enabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.id}",
            json={"isOnHomeActivityEnabled": value},
        )

    @property
    def away_activity_enabled(self) -> bool | None:
        """Away activity enabled."""
        return self.data.get("isOnAwayActivityEnabled")

    @away_activity_enabled.setter
    def away_activity_enabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method="put",
            url=f"residences/{self.id}",
            json={"isOnAwayActivityEnabled": value},
        )

    @property
    def home_away_activity_map(self) -> dict[str, Any]:
        """Home away activity map."""
        return {activity.name: activity.id for activity in self.activities}

    @property
    def home_away_activity_options(self) -> list[str]:
        """Home away activity options."""
        ###        return [HOME_AWAY_ACTIVITY_DISABLED] + list(self.home_away_activity_map.keys())
        return [HOME_AWAY_ACTIVITY_DISABLED, *list(self.home_away_activity_map.keys())]

    @property
    def home_activity_id(self) -> int | None:
        """Home activity ID."""
        for activity in self.activities:
            if activity.on_home_id == self.id:
                return activity.id
        return None

    @property
    def home_activity(self) -> str:
        """Home activity."""
        if self.home_activity_id:
            return list(self.home_away_activity_map.keys())[
                list(self.home_away_activity_map.values()).index(self.home_activity_id)
            ]
        return HOME_AWAY_ACTIVITY_DISABLED

    @home_activity.setter
    def home_activity(self, value: str) -> None:
        if (
            value not in self.home_away_activity_options
            or not self.home_activity_enabled
        ):
            return
        current_activity_id = self.home_activity_id
        target_activity_id = self.home_away_activity_map.get(value)
        if current_activity_id:
            self.api.call(
                method="put",
                url=f"residentialactivities/{current_activity_id}",
                json={"onHomeId": None},
            )
        if target_activity_id:
            self.api.call(
                method="put",
                url=f"residentialactivities/{target_activity_id}",
                json={"onHomeId": self.id},
            )

    @property
    def away_activity_id(self) -> int | None:
        """Away activity ID."""
        for activity in self.activities:
            if activity.on_away_id == self.id:
                return activity.id
        return None

    @property
    def away_activity(self) -> str:
        """Away activity."""
        if self.away_activity_id:
            return list(self.home_away_activity_map.keys())[
                list(self.home_away_activity_map.values()).index(self.away_activity_id)
            ]
        return HOME_AWAY_ACTIVITY_DISABLED

    @away_activity.setter
    def away_activity(self, value: str) -> None:
        if (
            value not in self.home_away_activity_options
            or not self.away_activity_enabled
        ):
            return
        current_activity_id = self.away_activity_id
        target_activity_id = self.home_away_activity_map.get(value)
        if current_activity_id:
            self.api.call(
                method="put",
                url=f"residentialactivities/{current_activity_id}",
                json={"onAwayId": None},
            )
        if target_activity_id:
            self.api.call(
                method="put",
                url=f"residentialactivities/{target_activity_id}",
                json={"onAwayId": self.id},
            )

    @property
    def activities(self) -> list[Activity]:
        """Activities."""
        return [
            Activity(self.api, self, activity)
            for activity in self.data.get("activities", [])
        ]

    @property
    def devices(self) -> list[Device]:
        """Devices."""
        return [
            Device(self.api, self, device) for device in self.data.get("devices", [])
        ]

    @property
    def rooms(self) -> list[Room]:
        """Rooms."""
        return [Room(self.api, self, room) for room in self.data.get("rooms", [])]

    @property
    def schedules(self) -> list[Schedule]:
        """Schedules."""
        return [
            Schedule(self.api, self, schedule)
            for schedule in self.data.get("schedules", [])
        ]
