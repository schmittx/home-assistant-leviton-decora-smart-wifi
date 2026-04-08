"""Leviton API."""

from __future__ import annotations


class Firmware:
    """Firmware."""

    def __init__(self, data) -> None:
        """Initialize."""
        self.data = data

    @property
    def enabled(self) -> bool | None:
        """Enabled."""
        return self.data.get("enabled")

    @property
    def model(self) -> str | None:
        """Model."""
        return self.data.get("model")

    @property
    def notes(self) -> str | None:
        """Notes."""
        return self.data.get("notes")

    @property
    def version(self) -> str | None:
        """Version."""
        return self.data.get("version")
