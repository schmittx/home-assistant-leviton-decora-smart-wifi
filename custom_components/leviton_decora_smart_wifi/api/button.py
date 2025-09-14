"""Leviton API."""

from __future__ import annotations


class Button:
    """Button."""

    def __init__(self, api, device, data) -> None:
        """Initialize."""
        self.api = api
        self.device = device
        self.data = data

    @property
    def config_type(self) -> str | None:
        """Config type."""
        return self.data.get("configurationType")

    @property
    def id(self) -> int | None:
        """ID."""
        return self.data.get("id")

    @property
    def number(self) -> int | None:
        """Number."""
        return self.data.get("number")

    @property
    def text(self) -> str | None:
        """Text."""
        return self.data.get("text")

    @property
    def actions(self) -> list[Action]:
        """Actions."""
        return [
            Action(self.api, self, action)
            for action in self.data.get("iotButtonActions", [])
        ]

    def press(self) -> None:
        """Press."""
        for action in self.actions:
            for parameter in action.parameters:
                self.api.call(
                    method="post",
                    url="residentialactivities/execute",
                    params={"id": parameter.value},
                )


class Action:
    """Action."""

    def __init__(self, api, button, data) -> None:
        """Initialize."""
        self.api = api
        self.button = button
        self.data = data

    @property
    def parameters(self) -> list[Parameter]:
        """Parameters."""
        return [
            Parameter(self.api, self, parameter)
            for parameter in self.data.get("parameters", [])
        ]


class Parameter:
    """Parameter."""

    def __init__(self, api, action, data) -> None:
        """Initialize."""
        self.api = api
        self.action = action
        self.data = data

    @property
    def value(self) -> int | None:
        """Value."""
        return self.data.get("parameterValue")
