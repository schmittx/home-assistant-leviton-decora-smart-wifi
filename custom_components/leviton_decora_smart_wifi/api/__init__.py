"""Leviton API."""

from __future__ import annotations

from collections.abc import Callable
import json
import logging
from pathlib import Path
from typing import Any

import requests

from .const import (
    API_ENDPOINT,
    LOGIN_CODE_INVALID,
    LOGIN_CODE_REQUIRED,
    LOGIN_FAILED,
    LOGIN_SUCCESS,
    LOGIN_TOO_MANY_ATTEMPTS,
)
from .residence import Residence

_LOGGER = logging.getLogger(__name__)


class LevitonException(Exception):
    """LevitonException."""

    def __init__(self, status_code: int, name: str, message: str) -> None:
        """Initialize."""
        super().__init__()
        self.status_code = status_code
        self.name = name
        self.message = message
        _LOGGER.debug(
            "\n- LevitionException\n- Status: %s\n- Name: %s\n- Message: %s, self.status_code, self.name, self.message"
        )


class LevitonAPI:
    """LevitonAPI."""

    def __init__(
        self,
        authorization: str | None = None,
        save_location: str | None = None,
        user_id: str | None = None,
    ) -> None:
        """Initialize."""
        self.authorization = authorization
        self.save_location = save_location
        self.user_id = user_id

        self.credentials: dict = {}
        self.data: list = []
        self.session = requests.Session()
        self.user_name: str = None

    def call(
        self,
        method: str,
        url: str,
        headers: dict | None = None,
        **kwargs,
    ) -> dict[str, Any] | None:
        """Call."""
        if method not in ("get", "post", "put"):
            return None
        if headers is None:
            headers = {}
        if self.authorization:
            headers["authorization"] = self.authorization
        _LOGGER.debug("Calling API with method: %s and URL: %s", method, url)
        if method == "get":
            response = self.refresh(
                lambda: self.session.get(
                    url=f"{API_ENDPOINT}/{url}", headers=headers, **kwargs
                )
            )
        if method == "post":
            response = self.refresh(
                lambda: self.session.post(
                    url=f"{API_ENDPOINT}/{url}", headers=headers, **kwargs
                )
            )
        if method == "put":
            response = self.refresh(
                lambda: self.session.put(
                    url=f"{API_ENDPOINT}/{url}", headers=headers, **kwargs
                )
            )
        response = self.parse_response(response=response)
        self.save_response(response=response, name=url)
        return response

    def login(self, email: str, password: str, code: str | None = None) -> str:
        """Login."""
        try:
            data = {"email": email, "password": password}
            if code:
                data["code"] = code
            response = self.call(
                method="post",
                url="person/login",
                params={"include": "user"},
                data=data,
            )
            self.authorization = response["id"]
            self.user_id = response["user"]["id"]
            self.user_name = "{} {}".format(
                response["user"]["firstName"],
                response["user"]["lastName"],
            )
        except LevitonException as exception:
            if all(
                [
                    exception.status_code == 401,
                    exception.message == "Login Failed",
                ]
            ):
                return LOGIN_FAILED
            if all(
                [
                    exception.status_code == 403,
                    exception.message == "Too many failed attempts",
                ]
            ):
                return LOGIN_TOO_MANY_ATTEMPTS
            if all(
                [
                    exception.status_code == 406,
                    exception.message
                    == "Insufficient Data: Person uses two factor authentication. Requires code.",
                ]
            ):
                return LOGIN_CODE_REQUIRED
            if all(
                [
                    exception.status_code == 408,
                    exception.message == "Error: Invalid code",
                ]
            ):
                return LOGIN_CODE_INVALID
            return LOGIN_FAILED
        self.credentials = data
        return LOGIN_SUCCESS

    def parse_response(self, response: requests.Response) -> dict[str, Any] | None:
        """Parse the response."""
        text = json.loads(response.text)
        if response.status_code not in [200]:
            error = text["error"]
            raise LevitonException(
                status_code=error.get("statusCode"),
                name=error.get("name"),
                message=error.get("message"),
            )
        return text

    def refresh(self, function: Callable) -> requests.Response:
        """Refresh login authorization."""
        response = function()
        if response.status_code not in [200]:
            text = json.loads(response.text)
            error = text["error"]
            if all(
                [
                    response.status_code == 401,
                    error["message"] == "Invalid Access Token",
                ]
            ):
                self.login(
                    email=self.credentials["email"],
                    password=self.credentials["password"],
                    code=self.credentials.get("code"),
                )
                response = function()
        return response

    def save_response(self, response: dict[str, Any], name: str = "response") -> None:
        """Save the response to a file."""
        if self.save_location and response:
            if not Path(self.save_location).is_dir():
                _LOGGER.debug("Creating directory: %s", self.save_location)
                Path(self.save_location).mkdir()
            name = name.replace("/", "_").replace(".", "_")
            file_path_name = f"{self.save_location}/{name}.json"
            _LOGGER.debug("Saving response: %s", file_path_name)
            with Path(file_path_name).open(mode="w", encoding="utf-8") as file:
                json.dump(
                    obj=response,
                    fp=file,
                    indent=4,
                    default=lambda o: "not-serializable",
                    sort_keys=True,
                )
            file.close()

    def update(self, target_residences: list[int] | None = None) -> list[Residence]:
        """Update."""
        try:
            data = []
            permissions = self.call(
                method="get",
                url=f"person/{self.user_id}/residentialpermissions",
            )
            for permission in permissions:
                residential_account_id = permission["residentialAccountId"]
                residences = self.call(
                    method="get",
                    url=f"residentialaccounts/{residential_account_id}/residences",
                )
                for residence in residences:
                    residence_id = residence["id"]
                    if any(
                        [
                            target_residences is None,
                            target_residences and residence_id in target_residences,
                        ]
                    ):
                        residence["activities"] = self.call(
                            method="get",
                            url=f"residences/{residence_id}/residentialactivities",
                        )
                        residence["devices"] = self.call(
                            method="get",
                            url=f"residences/{residence_id}/iotswitches",
                            headers={
                                "filter": json.dumps(obj={"include": ["iotButtons"]})
                            },
                        )
                        residence["rooms"] = self.call(
                            method="get",
                            url=f"residences/{residence_id}/residentialrooms",
                            headers={
                                "filter": json.dumps(
                                    obj={"include": ["residentialScenes"]}
                                )
                            },
                        )
                        residence["schedules"] = self.call(
                            method="get",
                            url=f"residences/{residence_id}/residentialschedules",
                        )
                        data.append(Residence(self, residence))
            self.data = data
        except LevitonException:
            return self.data
        return self.data
