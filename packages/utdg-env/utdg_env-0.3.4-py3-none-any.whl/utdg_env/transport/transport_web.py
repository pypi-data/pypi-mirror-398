from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

import websockets
from websockets.server import WebSocketServerProtocol

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


class WebTransport(Transport):
    """Web deployment transport: Python WebSocket server ← Godot WebGL client.

    This transport is used for deployment in browser environments (e.g.,
    Hugging Face Spaces). Browsers cannot act as WebSocket servers, so
    Python must host the server and wait for Godot WebGL to connect.

    Protocol semantics match Native mode:
        Python → RESET/STEP messages
        Godot → reset_response / step_response / observation

    Supports auto-reconnection logic and optional multi-client handling
    (typical in browser environments where refreshes are common).
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        timeout: float = 30.0,
        max_connections: int = 1,
        reconnect_attempts: int = 3,
        name: str = "WebTransport",
        cfg = None,  # Hydra DictConfig
    ) -> None:
        """Initialize the Web transport.

        Args:
            host: Host interface where the WebSocket server should bind.
            port: Port number.
            timeout: Maximum wait time for async operations.
            max_connections: Max number of simultaneous WebGL connections.
            reconnect_attempts: Retry attempts before failure.
            name: Logging/debugging identifier.
            cfg: Hydra configuration object (optional).
        """
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.cfg = cfg

        self._ws: Optional[WebSocketServerProtocol] = None
        self._server: Optional[websockets.server.Serve] = None

        self._last_response_data: Optional[dict] = None
        self._obs_event: Optional[asyncio.Event] = None

        self._last_human_action: Optional[int] = None
        self._human_action_event: Optional[asyncio.Event] = None

        super().__init__(
            timeout=timeout,
            reconnect_attempts=reconnect_attempts,
            name=name,
        )

    # ----------------------------------------------------------------------
    # Async lifecycle
    # ----------------------------------------------------------------------

    async def _async_connect(self) -> None:
        """Start the WebSocket server and wait for the first Godot browser client."""
        # Check if already connected
        if self._server is not None:
            logger.info(f"[{self.name}] Already connected, skipping bind")
            return

        if self._obs_event is None:
            self._obs_event = asyncio.Event()

        if self._human_action_event is None:
            self._human_action_event = asyncio.Event()

        # Configure server to reuse address (prevents TIME_WAIT issues on macOS)
        import socket

        self._server = await websockets.serve(
            self._handler,
            host=self.host,
            port=self.port,
            max_size=None,
            ping_interval=20,
            ping_timeout=20,
            # Allow address reuse - critical for rapid restarts on macOS
            family=socket.AF_INET,
            reuse_address=True,
        )

        logger.info(f"[{self.name}] Listening for Godot Web client on ws://{self.host}:{self.port}")

        try:
            await asyncio.wait_for(self._wait_for_client(), timeout=self.timeout)
        except asyncio.TimeoutError as exc:
            raise TransportTimeout(
                f"{self.name}: Timeout while waiting for Godot Web client."
            ) from exc

        logger.info(f"[{self.name}] WebGL Godot client connected.")

    async def _wait_for_client(self) -> None:
        """Wait until browser Godot connects."""
        while self._ws is None:
            await asyncio.sleep(0.05)

    async def _async_get_human_action(self) -> Optional[int]:
        """Wait for a human action from Godot."""
        if not self._ws:
            raise TransportDisconnected(f"{self.name}: get_human_action() called with no active WebSocket.")

        assert self._human_action_event is not None

        # Clear previous event state
        self._human_action_event.clear()
        self._last_human_action = None

        # Wait for the next action
        # We don't use strict timeout here because we are waiting for human input which can take time
        # But we should respect the transport timeout if it's meant to be strict,
        # usually waiting for human input needs indefinite or very long timeout.
        # Let's use a longer timeout or loop. For now, use transport timeout but maybe log warning.
        # Actually, for data collection, we might wait forever.
        # Let's trust the user to interrupt if they get bored.
        # However, asyncio.wait_for(..., timeout) raises TimeoutError.

        try:
            # wait indefinitely for human input? Or use a very long timeout?
            # Using transport timeout (30s) is too short for gameplay thinking.
            # Let's wait indefinitely.
            await self._human_action_event.wait()
        except asyncio.CancelledError:
            raise

        return self._last_human_action

    async def _async_reset(self) -> dict:
        """Send reset request and wait for initial observation."""
        if not self._ws:
            logger.info(f"[{self.name}] reset() called with no active WebSocket. Waiting for client...")
            await self._wait_for_client()

        assert self._obs_event is not None

        self._obs_event.clear()
        self._last_response_data = None

        msg = Message(MessageType.RESET)
        await self._send(msg)

        return await self._wait_for_observation("reset")

    async def _async_step(self, action: int) -> dict:
        """Send step action to Godot WebGL client and wait for response."""
        if not self._ws:
            raise TransportDisconnected(f"{self.name}: step() called with no active WebSocket.")

        assert self._obs_event is not None

        self._obs_event.clear()
        self._last_response_data = None

        payload = ActionPayload(int(action))
        msg = Message(MessageType.STEP, payload)
        await self._send(msg)

        return await self._wait_for_observation(f"step({action})")

    async def _async_close(self) -> None:
        """Close WebSocket and server listener."""
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

        if self._server is not None:
            self._server.close()
            try:
                await self._server.wait_closed()
            except Exception:
                pass
            self._server = None

        logger.info(f"[{self.name}] Closed.")

    # ----------------------------------------------------------------------
    # Message handling + send/recv helpers
    # ----------------------------------------------------------------------

    async def _send(self, message: Message) -> None:
        if not self._ws:
            raise TransportDisconnected(f"{self.name}: Cannot send, no WebSocket client.")

        try:
            await self._ws.send(json.dumps(message.to_dict()))
        except Exception as exc:
            raise TransportError(f"{self.name}: Send failed: {exc}") from exc

    async def _wait_for_observation(self, context: str) -> dict:
        """Wait for observation and return full response data from Godot.

        Returns:
            Full response data dict as received from Godot containing:
                - observation: Game state dict
                - done: Terminal flag
                - truncated: Truncation flag
                - info: Additional info including events
        """
        assert self._obs_event is not None

        try:
            await asyncio.wait_for(self._obs_event.wait(), timeout=self.timeout)
        except asyncio.TimeoutError as exc:
            raise TransportTimeout(
                f"{self.name}: Timeout waiting for observation after {context}."
            ) from exc

        if self._last_response_data is None:
            raise TransportError(f"{self.name}: No response data received.")

        # Return the full data payload from Godot
        # This already has the correct structure: {observation, done, truncated, info}
        return self._last_response_data

    async def _send_config(self) -> None:
        """Send configuration to Godot after connection."""
        if not self.cfg:
            logger.warning(f"[{self.name}] No config available to send to Godot")
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
                f"[{self.name}] Sent config to Godot: max_episode_steps={max_episode_steps}, "
                f"starting_gold={starting_gold}, base_health={base_health}"
            )
        except AttributeError as e:
            logger.error(f"[{self.name}] Config missing required fields: {e}")
        except Exception as e:
            logger.error(f"[{self.name}] Failed to send config: {e}")

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
                    f"[{self.name}] Config update sent to Godot: max_episode_steps={config_data.max_episode_steps}"
                )
            except Exception as e:
                logger.error(f"[{self.name}] Failed to send config update: {e}")

        # Run async method synchronously using the transport's event loop
        self._run_async(_async_send_config_dict())

    async def _handler(self, ws: WebSocketServerProtocol) -> None:
        """Handle incoming messages from Godot WebGL clients."""

        # Handle reconnection: replace existing connection if max_connections == 1
        if self._ws is not None and self.max_connections == 1:
            logger.info(f"[{self.name}] Replacing existing connection with new one")
            old_ws = self._ws
            try:
                await old_ws.close()
            except:
                pass

        # Accept the new connection
        self._ws = ws
        logger.info(f"[{self.name}] Godot WebGL client connected")

        try:
            # Listen for messages from Godot
            async for raw_message in ws:
                try:
                    data = json.loads(raw_message)
                    msg_type = data.get("type", "")

                    # Handle observation responses from Godot
                    if msg_type in ("reset_response", "step_response", "observation"):
                        # Godot sends: {"type": "...", "data": {"observation": {...}, "done": ..., "truncated": ..., "info": {...}}}
                        # We need to extract the entire "data" payload
                        logger.debug(f"[{self.name}] DEBUG: Received message: {json.dumps(data, indent=2)}")

                        if "data" in data and isinstance(data["data"], dict):
                            # Store the full data payload (observation, done, truncated, info)
                            self._last_response_data = data["data"]

                            # Wake up the waiting coroutine (reset() or step())
                            if self._obs_event:
                                self._obs_event.set()

                            logger.debug(f"[{self.name}] Received {msg_type} with full data payload")
                        else:
                            logger.warning(f"[{self.name}] Received {msg_type} but no 'data' field found")

                    elif msg_type == MessageType.HUMAN_ACTION.value:
                        logger.info(f"[{self.name}] received human action")
                        if "data" in data and "slot_index" in data["data"]:
                            self._last_human_action = int(data["data"]["slot_index"])
                            if self._human_action_event:
                                self._human_action_event.set()
                        else:
                            logger.warning(f"[{self.name}] Malformed human_action: {data}")

                    elif msg_type == MessageType.ERROR.value:
                        logger.error(f"[{self.name}] ERROR from Godot: {data}")

                    elif msg_type == MessageType.HELLO.value:
                        logger.info(f"[{self.name}] Received hello from client")

                        # Send configuration to Godot after hello
                        await self._send_config()

                    elif msg_type == "human_action":
                        # User reported these appear during RL training; safe to ignore/debug log
                        logger.debug(f"[{self.name}] Received human_action (ignoring): {data}")

                    else:
                        logger.warning(f"[{self.name}] Unknown message type: {msg_type}")

                except json.JSONDecodeError as e:
                    logger.error(f"[{self.name}] Failed to parse message: {e}")
                except Exception as e:
                    logger.exception(f"[{self.name}] Error handling message: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"[{self.name}] Godot WebGL client disconnected normally")
        except Exception as e:
            logger.exception(f"[{self.name}] Connection error: {e}")
        finally:
            # Clean up connection
            if self._ws == ws:
                self._ws = None
                logger.info(f"[{self.name}] Client handler cleanup complete")
