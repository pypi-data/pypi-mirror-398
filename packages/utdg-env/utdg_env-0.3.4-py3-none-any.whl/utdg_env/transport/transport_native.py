from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional

import websockets
from websockets.client import WebSocketClientProtocol

from .transport_base import (
    Transport,
    TransportError,
    TransportTimeout,
    TransportDisconnected,
)
from .protocol import (
    Message,
    MessageType,
    ActionPayload,
    ConfigData,
    create_config_message,
)

logger = logging.getLogger(__name__)


class NativeTransport(Transport):
    """Native desktop transport: Python WebSocket client → Godot desktop server.

    In this mode:

      - Godot runs a WebSocket server (your WebSocketServerBackend).
      - Python connects as a WebSocket client to ws://host:port.
      - Python sends:
          { "type": "reset" }
          { "type": "step", "data": { "slot_index": int } }
      - Godot replies with:
          { "type": "reset_response", "data": { ...obs... } }
          { "type": "step_response",
            "data": { "observation": {...}, "reward": float,
                      "done": bool, "truncated": bool, "info": {} } }

    This class translates those messages to ObservationPayload + dicts
    for the gym environment.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9876,
        timeout: float = 30.0,
        reconnect_attempts: int = 3,
        name: str = "NativeTransport",
        cfg = None,  # Hydra DictConfig
    ) -> None:
        self.host = host
        self.port = port
        self.cfg = cfg

        # Active WebSocket connection to Godot
        self._ws: Optional[WebSocketClientProtocol] = None

        # Last response data received from Godot
        self._last_response_data: Optional[dict] = None

        # Event used by reset()/step() to wait for a response
        self._obs_event: asyncio.Event = asyncio.Event()

        self._last_human_action: Optional[int] = None
        self._human_action_event: Optional[asyncio.Event] = None

        # Background listener task
        self._listener_task: Optional[asyncio.Task] = None

        super().__init__(timeout=timeout, reconnect_attempts=reconnect_attempts, name=name)

    # ------------------------------------------------------------------
    # Async lifecycle (called within Transport's event loop)
    # ------------------------------------------------------------------

    async def _async_connect(self) -> None:
        """Connect to Godot WebSocket server and start listener task."""
        uri = f"ws://{self.host}:{self.port}"

        if self._human_action_event is None:
            self._human_action_event = asyncio.Event()

        last_exc: Optional[BaseException] = None
        for attempt in range(1, self.reconnect_attempts + 1):
            try:
                logger.info(
                    "Connecting to %s (attempt %d/%d)...",
                    uri, attempt, self.reconnect_attempts
                )
                self._ws = await websockets.connect(uri)
                logger.info("Connected to Godot at %s", uri)

                # Start background listener
                self._listener_task = asyncio.create_task(self._handler())
                logger.debug("Listener task started")

                # Send configuration to Godot after connection
                await self._send_config()

                return
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                logger.warning(
                    "Connection attempt %d failed: %r", attempt, exc
                )
                await asyncio.sleep(0.5)

        raise TransportError(
            f"{self.name}: Could not connect after {self.reconnect_attempts} attempts: {last_exc}"
        ) from last_exc

    async def _async_get_human_action(self) -> Optional[int]:
        """Wait for a human action from Godot."""
        if self._ws is None:
            raise TransportDisconnected(f"{self.name}: get_human_action() called with no active WebSocket.")

        assert self._human_action_event is not None

        # Clear previous event state
        self._human_action_event.clear()
        self._last_human_action = None

        try:
            # wait indefinitely for human input
            await self._human_action_event.wait()
        except asyncio.CancelledError:
            raise

        return self._last_human_action

    async def _async_reset(self) -> dict:
        """Send reset message to Godot and wait for observation."""
        if self._ws is None:
            raise TransportDisconnected(f"{self.name}: No active WebSocket for reset().")

        # Clear state & event
        self._last_response_data = None
        self._obs_event.clear()

        msg = Message(MessageType.RESET)
        await self._send(msg)
        logger.debug("RESET sent, waiting for reset_response...")

        obs = await self._wait_for_observation(context="reset")
        return obs

    async def _async_step(self, action: int) -> dict:
        """Send step(action) to Godot and wait for observation."""
        if self._ws is None:
            raise TransportDisconnected(f"{self.name}: No active WebSocket for step().")

        self._last_response_data = None
        self._obs_event.clear()

        payload = ActionPayload(slot_index=int(action))
        msg = Message(MessageType.STEP, payload)
        await self._send(msg)
        logger.debug("STEP(action=%d) sent, waiting for step_response...", action)

        obs = await self._wait_for_observation(context=f"step(action={action})")
        return obs

    async def _async_close(self) -> None:
        """Close WebSocket and stop listener task."""
        if self._listener_task is not None:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            self._listener_task = None

        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

        logger.info("Transport closed")

    async def _send_config(self) -> None:
        """Send configuration to Godot after connection."""
        if not self.cfg:
            logger.debug("No config available to send to Godot")
            return

        try:
            # Extract config values from Hydra config
            max_episode_steps = int(self.cfg.env.episode.max_episode_steps)
            starting_gold = int(self.cfg.env.episode.starting_gold)
            base_health = int(self.cfg.env.episode.base_health)

            config_data = ConfigData(
                headless=self.cfg.runtime.get("headless", True),
                port=self.port,
                host=self.host,
                max_episode_steps=max_episode_steps,
                starting_gold=starting_gold,
                base_health=base_health,
            )

            config_msg = create_config_message(config_data)
            await self._send(config_msg)

            logger.info(
                "Sent config to Godot: max_episode_steps=%d, starting_gold=%d, base_health=%d",
                max_episode_steps, starting_gold, base_health
            )
        except AttributeError as e:
            logger.error("Config missing required fields: %s", e)
        except Exception as e:
            logger.error("Failed to send config: %s", e)

    def send_config(self, config_dict: dict[str, Any]) -> None:
        """Send configuration update to Godot (synchronous, callable from callbacks).

        This is used for mid-training config updates (e.g., curriculum learning).
        Updates are applied at episode boundaries only.

        Args:
            config_dict: Dictionary with config values (e.g., max_episode_steps, starting_gold, base_health)
        """
        async def _async_send_config_dict() -> None:
            """Send config dict to Godot."""
            try:
                config_data = ConfigData(
                    headless=config_dict.get("headless", True),
                    port=self.port,
                    host=self.host,
                    max_episode_steps=int(config_dict.get("max_episode_steps", 5000)),
                    starting_gold=int(config_dict.get("starting_gold", 150)),
                    base_health=int(config_dict.get("base_health", 10)),
                )

                config_msg = create_config_message(config_data)
                await self._send(config_msg)

                logger.debug(
                    "Config update sent to Godot: max_episode_steps=%d",
                    config_data.max_episode_steps
                )
            except Exception as e:
                logger.error("Failed to send config update: %s", e)

        # Run async method synchronously using the transport's event loop
        self._run_async(_async_send_config_dict())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _send(self, message: Message) -> None:
        """Serialize and send Message to Godot."""
        if self._ws is None:
            raise TransportDisconnected(f"{self.name}: Cannot send, no active WebSocket.")

        try:
            payload = json.dumps(message.to_dict())
            logger.debug("Sending frame: %s", payload)
            await self._ws.send(payload)
        except Exception as exc:  # noqa: BLE001
            raise TransportError(f"{self.name}: Failed to send message: {exc}") from exc

    async def _wait_for_observation(self, context: str) -> dict:
        """Wait until _handler sets _obs_event and _last_response_data is filled.

        Returns:
            Full response data dict containing:
                - observation: Game state dict
                - done: Terminal flag
                - truncated: Truncation flag
                - info: Additional info including events
        """
        try:
            logger.debug("Waiting for observation after %s...", context)
            await asyncio.wait_for(self._obs_event.wait(), timeout=self.timeout)
        except asyncio.TimeoutError as exc:
            raise TransportTimeout(
                f"{self.name}: Timed out waiting for observation after {context}."
            ) from exc

        if self._last_response_data is None:
            raise TransportError(
                f"{self.name}: Observation event set but _last_response_data is None "
                f"(context={context})."
            )

        logger.debug("Response received after %s: %s", context, self._last_response_data)
        return self._last_response_data

    # ------------------------------------------------------------------
    # Listener: runs in the background and consumes frames from Godot
    # ------------------------------------------------------------------

    async def _handler(self) -> None:
        """Background listener that consumes WebSocket frames from Godot."""
        if self._ws is None:
            logger.warning("Listener started with no WebSocket (unexpected)")
            return

        logger.debug("Listener started; waiting for frames from Godot")

        try:
            async for raw in self._ws:
                # Log the raw frame
                logger.debug("Listener received frame: %r", raw)

                # websockets can yield str (TEXT) or bytes
                if isinstance(raw, bytes):
                    try:
                        raw_str = raw.decode("utf-8")
                    except UnicodeDecodeError as exc:
                        logger.error("Failed to decode bytes frame: %s", exc)
                        continue
                else:
                    raw_str = raw

                # Parse JSON
                try:
                    msg = json.loads(raw_str)
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "JSON decode error: %s. Raw payload: %r", exc, raw_str
                    )
                    continue

                logger.debug("Parsed message: %s", msg)

                mtype = msg.get("type", "")
                data: Any = msg.get("data", {})

                if mtype in ("reset_response", "step_response", "observation"):
                    # Build proper response structure
                    # step_response contains: {"observation": {...}, "done": ..., "truncated": ..., "info": {...}}
                    if isinstance(data, dict) and "observation" in data:
                        # Full response structure from Godot
                        self._last_response_data = data
                    else:
                        # Legacy: data is just the observation, build response structure
                        self._last_response_data = {
                            "observation": data,
                            "done": data.get("done", False),
                            "truncated": data.get("truncated", False),
                            "info": {"events": data.get("events", {})}
                        }

                    self._obs_event.set()
                    logger.debug("Response event set (type=%s)", mtype)

                elif mtype == MessageType.HUMAN_ACTION.value:
                    logger.info("Received human action")
                    if "data" in data and "slot_index" in data["data"]:
                        self._last_human_action = int(data["data"]["slot_index"])
                        if self._human_action_event:
                            self._human_action_event.set()
                    else:
                        logger.warning("Malformed human_action: %s", data)
                else:
                    logger.debug("Ignoring message type=%r, msg=%r", mtype, msg)

        except Exception as exc:  # noqa: BLE001
            logger.error("Listener stopped due to exception: %r", exc)

        finally:
            logger.debug("Listener terminating; remote closed connection")
            self._ws = None
