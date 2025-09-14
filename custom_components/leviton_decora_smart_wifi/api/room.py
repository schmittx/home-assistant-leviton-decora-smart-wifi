"""Leviton API."""

from __future__ import annotations

from .scene import Scene


class Room:
    """Room."""

    def __init__(self, api, residence, data) -> None:
        """Initialize."""
        self.api = api
        self.residence = residence
        self.data = data

    @property
    def name(self) -> str | None:
        """Name."""
        return self.data.get("name")

    @property
    def power(self) -> str | None:
        """Power."""
        return self.data.get("power")

    @property
    def all_connected(self) -> bool | None:
        """All connected."""
        return self.data.get("allConnected")

    @property
    def residence_id(self) -> int | None:
        """Residence ID."""
        return self.data.get("residenceId")

    @property
    def id(self) -> int | None:
        """ID."""
        return self.data.get("id")

    @property
    def scenes(self) -> list[Scene]:
        """Scenes."""
        return [
            Scene(self.api, self, scene)
            for scene in self.data.get("residentialScenes", [])
        ]
