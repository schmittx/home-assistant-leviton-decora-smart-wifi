"""Leviton API"""
from __future__ import annotations

from .scene import Scene


class Room(object):

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

    @property
    def all_connected(self) -> bool | None:
        return self.data.get("allConnected")

    @property
    def residence_id(self) -> int | None:
        return self.data.get("residenceId")

    @property
    def id(self) -> int | None:
        return self.data.get("id")

    @property
    def scenes(self) -> list[Scene]:
        return [Scene(self.api, self, scene) for scene in self.data.get("residentialScenes", [])]
