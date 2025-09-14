"""Leviton AP."""

from __future__ import annotations


class Activity:
    """Activity."""

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
    def id(self) -> int | None:
        """ID."""
        return self.data.get("id")

    @property
    def is_button_activity(self) -> bool | None:
        """Is button activity."""
        return self.data.get("isButtonActivity")

    @property
    def on_away_id(self) -> int | None:
        """On away ID."""
        return self.data.get("onAwayId")

    @property
    def on_home_id(self) -> int | None:
        """On home ID."""
        return self.data.get("onHomeId")

    def execute(self) -> None:
        """Execute."""
        self.api.call(
            method="post",
            url="residentialactivities/execute",
            params={"id": self.id},
        )
