"""Leviton API."""

from __future__ import annotations


class Schedule:
    """Schedule."""

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
    def disabled(self) -> bool | None:
        """Disabled."""
        return self.data.get("disabled")

    @property
    def enabled(self) -> bool | None:
        """Disabled."""
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
        """Enable."""
        setattr(self, "enabled", True)

    def disable(self) -> None:
        """Disable."""
        setattr(self, "enabled", False)

    @property
    def residence_id(self) -> int | None:
        """Residence ID."""
        return self.data.get("residenceId")

    @property
    def id(self) -> int | None:
        """ID."""
        return self.data.get("id")
