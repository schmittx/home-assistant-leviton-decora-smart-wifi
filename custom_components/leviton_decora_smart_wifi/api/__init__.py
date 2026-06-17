"""Leviton API."""

from collections.abc import Callable
from http import HTTPMethod
import json
import logging
from pathlib import Path
from typing import Any

import requests

from .const import API_ENDPOINT, FIRMWARE_APP_MAP, FirmwareAppID, LoginResult
from .firmware import Firmware
from .residence import Residence

_LOGGER = logging.getLogger(__name__)


class LevitonData:
    """LevitonData."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        """Initialize."""
        self.data = data if data is not None else {}

    @property
    def firmware(self) -> dict[str, Firmware]:
        """Firmware."""
        return self.data.get("firmware", {})

    @property
    def residences(self) -> list[Residence]:
        """Residences."""
        return self.data.get("residences", [])


class LevitonException(Exception):
    """LevitonException."""

    def __init__(self, status_code: int, name: str, message: str) -> None:
        """Initialize."""
        super().__init__()
        self.status_code = status_code
        self.name = name
        self.message = message
        _LOGGER.error(
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
        self.data: LevitonData = LevitonData()
        self.session = requests.Session()
        self.user_name: str | None = None
        self.login_response: dict[str, Any] | None = None

    def call(
        self,
        method: HTTPMethod,
        url: str,
        headers: dict | None = None,
        **kwargs,
    ) -> list[dict] | dict[str, Any] | None:
        """Call."""
        if headers is None:
            headers = {}
        if self.authorization:
            headers["authorization"] = self.authorization
        _LOGGER.debug("Calling API with method: %s and URL: %s", method, url)
        response = self.refresh(
            lambda: self.session.request(
                method=method, url=f"{API_ENDPOINT}/{url}", headers=headers, **kwargs
            )
        )
        response = self.parse_response(response=response)
        self.save_response(response=response, name=url)
        return response

    def login(self, email: str, password: str, code: str | None = None) -> LoginResult:
        """Login."""
        try:
            data = {"email": email, "password": password}
            if code:
                data["code"] = code
            response = self.call(
                method=HTTPMethod.POST,
                url="person/login",
                params={"include": "user"},
                data=data,
            )
            if response and isinstance(response, dict):
                self.authorization = response["id"]
                self.user_id = response["user"]["id"]
                self.user_name = "{} {}".format(
                    response["user"]["firstName"],
                    response["user"]["lastName"],
                )
                self.login_response = response
        except LevitonException as exception:
            if all(
                [
                    exception.status_code == 401,
                    exception.message == "Login Failed",
                ]
            ):
                return LoginResult.FAILED
            if all(
                [
                    exception.status_code == 403,
                    exception.message == "Too many failed attempts",
                ]
            ):
                return LoginResult.TOO_MANY_ATTEMPTS
            if all(
                [
                    exception.status_code == 406,
                    exception.message
                    == "Insufficient Data: Person uses two factor authentication. Requires code.",
                ]
            ):
                return LoginResult.CODE_REQUIRED
            if all(
                [
                    exception.status_code == 408,
                    exception.message == "Error: Invalid code",
                ]
            ):
                return LoginResult.CODE_INVALID
            return LoginResult.FAILED
        self.credentials = data
        return LoginResult.SUCCESS

    def parse_response(self, response: requests.Response) -> dict[str, Any] | None:
        """Parse the response."""
        text = json.loads(response.text)
        if response.status_code != 200:
            error = text["error"]
            raise LevitonException(
                status_code=error.get("statusCode"),
                name=error.get("name"),
                message=error.get("message"),
            )
        return text

    def refresh(self, function: Callable) -> requests.Response:
        """Refresh login authorization, retrying once on a stale connection.

        Leviton's REST endpoint silently closes pooled keep-alive
        connections; the next request on a stale connection fails with
        ``ConnectionError``/``RemoteDisconnected`` and HA marks every
        coordinator-bound entity unavailable until the next cycle. Retry
        once after rotating the requests.Session so the client gets a
        fresh socket.
        """
        try:
            response = function()
        except requests.exceptions.ConnectionError:
            _LOGGER.debug(
                "Leviton REST connection dropped; retrying with fresh session"
            )
            self.session = requests.Session()
            response = function()
        if response.status_code != 200:
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

    def save_response(
        self, response: dict[str, Any] | None, name: str = "response"
    ) -> None:
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

    def update(self, target_residences: list[int] | None = None) -> LevitonData:
        """Update."""
        try:
            data = {}
            data["residences"] = self.get_residences(target_residences)
            data["firmware"] = self.get_firmware(data["residences"])
            self.data = LevitonData(data)
        except LevitonException:
            return self.data
        return self.data

    def get_residences(
        self, target_residences: list[int] | None = None
    ) -> list[Residence]:
        """Get residences."""
        data = []
        permissions = self.call(
            method=HTTPMethod.GET,
            url=f"person/{self.user_id}/residentialpermissions",
        )
        if permissions and isinstance(permissions, list):
            for permission in permissions:
                residential_account_id = permission["residentialAccountId"]
                residences = self.call(
                    method=HTTPMethod.GET,
                    url=f"residentialaccounts/{residential_account_id}/residences",
                )
                if residences and isinstance(residences, list):
                    for residence in residences:
                        if residence and isinstance(residence, dict):
                            residence_id = residence["id"]
                            if any(
                                [
                                    target_residences is None,
                                    target_residences
                                    and residence_id in target_residences,
                                ]
                            ):
                                residence["activities"] = self.call(
                                    method=HTTPMethod.GET,
                                    url=f"residences/{residence_id}/residentialactivities",
                                )
                                residence["devices"] = self.call(
                                    method=HTTPMethod.GET,
                                    url=f"residences/{residence_id}/iotswitches",
                                    headers={
                                        "filter": json.dumps(
                                            obj={"include": ["iotButtons"]}
                                        )
                                    },
                                )
                                residence["rooms"] = self.call(
                                    method=HTTPMethod.GET,
                                    url=f"residences/{residence_id}/residentialrooms",
                                    headers={
                                        "filter": json.dumps(
                                            obj={"include": ["residentialScenes"]}
                                        )
                                    },
                                )
                                residence["schedules"] = self.call(
                                    method=HTTPMethod.GET,
                                    url=f"residences/{residence_id}/residentialschedules",
                                )
                                data.append(Residence(self, residence))
        return data

    def get_firmware(self, residences: list[Residence]) -> dict[str, Firmware]:
        """Get firmware."""
        devices: dict[str, FirmwareAppID] = {}
        for residence in residences:
            for device in residence.devices:
                if device.model and device.model not in devices:
                    devices[device.model] = FIRMWARE_APP_MAP[device.generation]

        firmware: dict[str, Firmware] = {}
        for model, app_id in devices.items():
            app_firmware = self.call(
                method=HTTPMethod.GET,
                url="lcsapps/getfirmware",
                params={
                    "appId": app_id,
                    "model": model,
                    "data": json.dumps(
                        {
                            "condensed": False,
                        }
                    ).encode("ascii"),
                },
            )
            if app_firmware and isinstance(app_firmware, list):
                firmware[model] = Firmware(app_firmware[0])
        return firmware
