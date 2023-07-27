"""Leviton API"""
from __future__ import annotations


class Scene(object):

    def __init__(self, api, room, data):
        self.api = api
        self.room = room
        self.data = data

    @property
    def name(self) -> str | None:
        return self.data.get("name")

    @property
    def id(self) -> int | None:
        return self.data.get("id")

    def execute(self) -> None:
        self.api.call(
            method="post",
            url=f"residentialscenes/execute",
            params={"id": self.id},
        )
