"""Leviton API."""

from __future__ import annotations


class Scene:
    """Scene."""

    def __init__(self, api, room, data) -> None:
        """Initialize."""
        self.api = api
        self.room = room
        self.data = data

    @property
    def name(self) -> str | None:
        """Name."""
        return self.data.get("name")

    @property
    def id(self) -> int | None:
        """ID."""
        return self.data.get("id")

    def execute(self) -> None:
        """Execute."""
        self.api.call(
            method="post",
            url="residentialscenes/execute",
            params={"id": self.id},
        )
