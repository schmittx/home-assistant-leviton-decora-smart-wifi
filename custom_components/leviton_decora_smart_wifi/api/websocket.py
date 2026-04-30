"""Leviton MyLeviton cloud websocket client.

Connects to ``wss://my.leviton.com/socket/websocket`` and subscribes to
real-time push notifications. The protocol was reverse-engineered from
the official myapp.leviton.com bundle (``authenticateSocketConnection``
wired to ``onOpen``) and the homebridge-myleviton plugin.

Auth model used here:
- We do NOT call ``LevitonAPI.login`` from this client. The bearer token
  already in the config entry is enough to synthesize a token payload.
- If auth fails, we back off ``AUTH_FAILURE_COOLDOWN`` (default 1 hour)
  before any retry, to avoid hammering Leviton's auth endpoint and
  locking the account out.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

WS_URL = "wss://my.leviton.com/socket/websocket"
WS_ORIGIN = "https://my.leviton.com"

PING_INTERVAL = 30.0

# Reconnect when the network blip drops the WS — this is conservative.
INITIAL_RECONNECT_DELAY = 30.0
MAX_RECONNECT_DELAY = 600.0

# Auth failure cooldown — long, so we never hammer Leviton even if the
# token is bad. The integration's polling layer continues to work.
AUTH_FAILURE_COOLDOWN = 3600.0

CHALLENGE_TIMEOUT = 10.0


class LevitonWebSocket:
    """Persistent websocket subscriber for the MyLeviton cloud."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        token_provider: Callable[[], dict[str, Any] | None],
        on_notification: Callable[[dict[str, Any]], None],
    ) -> None:
        self._session = session
        self._token_provider = token_provider
        self._on_notification = on_notification
        self._subscriptions: list[tuple[str, int]] = []
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._ready = asyncio.Event()

    def set_subscriptions(self, subs: list[tuple[str, int]]) -> None:
        """Replace the subscription set; takes effect on next connect."""
        self._subscriptions = list(subs)
        if self._ready.is_set() and self._ws is not None and not self._ws.closed:
            asyncio.create_task(self._send_subscriptions())

    def start(self) -> None:
        """Start the websocket loop as a background task."""
        if self._task and not self._task.done():
            return
        self._stop.clear()
        _LOGGER.debug("Leviton websocket task starting")
        self._task = asyncio.create_task(self._run(), name="leviton_ws")

    async def stop(self) -> None:
        """Stop the websocket loop and close the connection."""
        self._stop.set()
        if self._ws is not None and not self._ws.closed:
            await self._ws.close()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self._task.cancel()

    async def _run(self) -> None:
        delay = INITIAL_RECONNECT_DELAY
        while not self._stop.is_set():
            token = self._token_provider()
            if not token or "id" not in token:
                _LOGGER.error(
                    "Leviton websocket: no token available; sleeping for %.0fs",
                    AUTH_FAILURE_COOLDOWN,
                )
                await self._sleep_or_stop(AUTH_FAILURE_COOLDOWN)
                continue

            outcome = "transient"
            try:
                outcome = await self._connect(token)
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Leviton websocket loop error")
            finally:
                self._ready.clear()
                self._ws = None

            if outcome == "auth_failed":
                _LOGGER.warning(
                    "Leviton websocket auth failed; cooling down for %.0fs to avoid account lockout",
                    AUTH_FAILURE_COOLDOWN,
                )
                await self._sleep_or_stop(AUTH_FAILURE_COOLDOWN)
                delay = INITIAL_RECONNECT_DELAY
                continue

            if outcome == "ok":
                delay = INITIAL_RECONNECT_DELAY

            if not self._stop.is_set():
                await self._sleep_or_stop(delay)
                delay = min(delay * 2, MAX_RECONNECT_DELAY)

    async def _sleep_or_stop(self, seconds: float) -> None:
        try:
            await asyncio.wait_for(self._stop.wait(), timeout=seconds)
        except asyncio.TimeoutError:
            pass

    async def _connect(self, token: dict[str, Any]) -> str:
        """Open the WS, authenticate, then run the receive loop.

        Returns ``"ok"`` if we authenticated and ran cleanly,
        ``"auth_failed"`` if auth was rejected (so the caller backs off
        hard), or ``"transient"`` for any other failure.
        """
        _LOGGER.debug("Connecting to Leviton websocket %s", WS_URL)
        headers = {"Origin": WS_ORIGIN}
        try:
            async with self._session.ws_connect(
                WS_URL, headers=headers, heartbeat=PING_INTERVAL, autoclose=True
            ) as ws:
                self._ws = ws
                auth_outcome = await self._authenticate(ws, token)
                if auth_outcome != "ok":
                    return auth_outcome
                self._ready.set()
                await self._send_subscriptions()
                await self._receive_loop(ws)
                return "ok"
        except aiohttp.ClientError:
            _LOGGER.warning("Leviton websocket connection error", exc_info=True)
            return "transient"

    async def _authenticate(
        self,
        ws: aiohttp.ClientWebSocketResponse,
        token: dict[str, Any],
    ) -> str:
        """Authenticate the websocket.

        Sends ``{token: <login response>}`` immediately on open per the
        myapp.leviton.com client behavior. Waits up to a short window for
        ``{type:"status", status:"ready"}``. Anything else (including the
        ``challenge`` frame with a nonce or repeated ``status:"not ready"``)
        is treated as info-level traffic and ignored — only an explicit
        rejection or timeout drops auth to ``auth_failed``.
        """
        await ws.send_json({"token": token})
        deadline = asyncio.get_running_loop().time() + CHALLENGE_TIMEOUT * 2

        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                _LOGGER.error("Websocket auth handshake timed out")
                return "auth_failed"

            try:
                frame = await asyncio.wait_for(ws.receive(), timeout=remaining)
            except asyncio.TimeoutError:
                _LOGGER.error("Websocket auth handshake timed out")
                return "auth_failed"

            if frame.type is aiohttp.WSMsgType.TEXT:
                try:
                    payload = json.loads(frame.data)
                except ValueError:
                    _LOGGER.warning("Non-JSON handshake frame: %r", frame.data)
                    continue
                _LOGGER.debug("WS handshake frame: %s", payload)
                if (
                    payload.get("type") == "status"
                    and payload.get("status") == "ready"
                ):
                    _LOGGER.info("Leviton websocket authenticated")
                    return "ok"
                continue

            if frame.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING):
                _LOGGER.error("WS closed during auth (code=%s)", getattr(frame, "data", None))
                return "auth_failed"
            if frame.type is aiohttp.WSMsgType.ERROR:
                _LOGGER.error("WS error during auth: %s", ws.exception())
                return "auth_failed"

    async def _send_subscriptions(self) -> None:
        if self._ws is None or self._ws.closed:
            return
        for model_name, model_id in self._subscriptions:
            msg = {
                "type": "subscribe",
                "subscription": {"modelName": model_name, "modelId": model_id},
            }
            _LOGGER.debug("WS subscribe: %s", msg)
            await self._ws.send_json(msg)

    async def _receive_loop(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        async for msg in ws:
            if self._stop.is_set():
                break
            if msg.type is aiohttp.WSMsgType.TEXT:
                self._dispatch(msg.data)
            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING):
                _LOGGER.debug("WS closed/closing")
                break
            elif msg.type is aiohttp.WSMsgType.ERROR:
                _LOGGER.warning("WS error: %s", ws.exception())
                break

    def _dispatch(self, raw: str) -> None:
        try:
            payload = json.loads(raw)
        except ValueError:
            _LOGGER.warning("Non-JSON WS frame: %r", raw[:200])
            return

        msg_type = payload.get("type")
        if msg_type == "notification":
            _LOGGER.debug("WS notification: %s", json.dumps(payload, sort_keys=True))
            try:
                self._on_notification(payload.get("notification") or {})
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Notification handler raised")
        else:
            _LOGGER.debug("WS frame (type=%s): %s", msg_type, payload)
