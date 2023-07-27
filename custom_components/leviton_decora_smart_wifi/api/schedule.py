"""Leviton API"""
from __future__ import annotations


class Schedule(object):

    def __init__(self, api, residence, data):
        self.api = api
        self.residence = residence
        self.data = data

    @property
    def name(self) -> str | None:
        return self.data.get("name")

    @property
    def disabled(self) -> bool | None:
        return self.data.get("disabled")

    @property
    def enabled(self) -> bool | None:
        return not bool(self.disabled)

    @enabled.setter
    def enabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            return
        self.api.call(
            method="put",
            url=f"residentialschedules/{self.id}",
            json={"disabled": bool(not value)},
        )

    def enable(self) -> None:
        setattr(self, "enabled", True)
    
    def disable(self) -> None:
        setattr(self, "enabled", False)
    
    @property
    def residence_id(self) -> int | None:
        return self.data.get("residenceId")

    @property
    def id(self) -> int | None:
        return self.data.get("id")
