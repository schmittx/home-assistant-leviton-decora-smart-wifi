"""Leviton API."""

from .const import FirmwareAppID, ReleaseURL


class Firmware:
    """Firmware."""

    def __init__(self, data) -> None:
        """Initialize."""
        self.data = data

    @property
    def app_id(self) -> FirmwareAppID | None:
        """App ID."""
        if lcs_app_id := self.data.get("lcsAppId"):
            return {app_id.value: app_id for app_id in FirmwareAppID}[
                lcs_app_id.lower()
            ]
        return None

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
    def release_url(self) -> str | None:
        """Release URL."""
        return (
            ReleaseURL.GENERATION_TWO
            if self.app_id == FirmwareAppID.DECORA_SMART_2
            else None
        )

    @property
    def version(self) -> str | None:
        """Version."""
        return self.data.get("version")
