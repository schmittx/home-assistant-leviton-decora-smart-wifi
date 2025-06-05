"""Leviton API"""
from __future__ import annotations


class Activity(object):

    def __init__(self, api, residence, data):
        self.api = api
        self.residence = residence
        self.data = data

    @property
    def name(self) -> str | None:
        return self.data.get("name")

    @property
    def id(self) -> int | None:
        return self.data.get("id")

    @property
    def is_button_activity(self) -> bool | None:
        return self.data.get("isButtonActivity")

    @property
    def on_away_id(self) -> int | None:
        return self.data.get("onAwayId")

    @property
    def on_home_id(self) -> int | None:
        return self.data.get("onHomeId")

    def execute(self) -> None:
        self.api.call(
            method="post",
            url=f"residentialactivities/execute",
            params={"id": self.id},
        )
