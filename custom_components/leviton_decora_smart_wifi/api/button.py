"""Leviton API"""
from __future__ import annotations


class Button(object):

    def __init__(self, api, device, data):
        self.api = api
        self.device = device
        self.data = data

    @property
    def config_type(self) -> str | None:
        return self.data.get("configurationType")

    @property
    def id(self) -> int | None:
        return self.data.get("id")

    @property
    def number(self) -> int | None:
        return self.data.get("number")

    @property
    def text(self) -> str | None:
        return self.data.get("text")

    @property
    def actions(self) -> list[Action]:
        return [Action(self.api, self, action) for action in self.data.get("iotButtonActions", [])]

    def press(self) -> None:
        for action in self.actions:
            for parameter in action.parameters:
                self.api.call(
                    method="post",
                    url=f"residentialactivities/execute",
                    params={"id": parameter.value},
                )


class Action(object):

    def __init__(self, api, button, data):
        self.api = api
        self.button = button
        self.data = data

    @property
    def parameters(self) -> list[Parameter]:
        return [Parameter(self.api, self, parameter) for parameter in self.data.get("parameters", [])]


class Parameter(object):

    def __init__(self, api, action, data):
        self.api = api
        self.action = action
        self.data = data

    @property
    def value(self) -> int | None:
        return self.data.get("parameterValue")

