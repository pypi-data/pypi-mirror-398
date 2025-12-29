# utdg_env/utdg_env/transport/transport_hf.py
from __future__ import annotations

import asyncio
import logging
from queue import Queue
from typing import Optional, Dict, Any

from .transport_base import Transport, TransportTimeout, TransportError, TransportDisconnected
from .protocol import Message, MessageType, ActionPayload, ConfigData, create_config_message

logger = logging.getLogger(__name__)


class HFTransport(Transport):
    """
    HF (HuggingFace / FastAPI) transport with message-ID matching.

    This version assigns a unique msg_id to every RESET/STEP request and only
    unblocks the awaiting coroutine when a matching observation arrives.

    This eliminates race conditions:
      - late reset_response unblocking a step() call
      - multiple UI reset requests overlapping
      - stale observations causing timeouts
    """

    class ReconnectionError(TransportError):
        """Raised when a client reconnects (refresh/new tab) during a wait."""
        pass

    def __init__(
        self,
        to_godot: Queue,
        from_godot: Queue,
        timeout: float = 30.0,
        reconnect_attempts: int = 3,
        name: str = "HFTransport",
        cfg = None,  # Hydra DictConfig
    ) -> None:
        self._to_godot: Queue = to_godot
        self._from_godot: Queue = from_godot
        self.cfg = cfg

        self._obs_event: Optional[asyncio.Event] = None
        self._last_obs: Optional[Dict[str, Any]] = None

        # Human action support (for future imitation learning)
        self._last_human_action: Optional[int] = None
        self._human_action_event: Optional[asyncio.Event] = None

        # NEW: message correlation
        self._msg_counter: int = 0
        self._pending_id: Optional[int] = None
        self._pending_type: Optional[str] = None
        self._config_sent: bool = False  # Track if config has been sent

        super().__init__(
            timeout=timeout,
            reconnect_attempts=reconnect_attempts,
            name=name,
        )

    # ------------------------------------------------------------------
    # Core lifecycle
    # ------------------------------------------------------------------

    async def _async_connect(self) -> None:
        if self._obs_event is None:
            self._obs_event = asyncio.Event()

        if self._human_action_event is None:
            self._human_action_event = asyncio.Event()

        self._connected = True
        logger.info("[HFTransport] HFTransport marked as connected (no underlying socket).")

        # Send config on connect (will be queued and sent when Godot connects)
        self.send_config()

    async def _async_close(self) -> None:
        self._connected = False
        if self._obs_event:
            self._obs_event.set()
        logger.info("[HFTransport] Closed.")

    # ------------------------------------------------------------------
    # RESET / STEP
    # ------------------------------------------------------------------

    def _new_msg_id(self) -> int:
        self._msg_counter += 1
        return self._msg_counter

    async def _async_reset(self) -> Dict[str, Any]:
        if self._obs_event is None:
            self._obs_event = asyncio.Event()

        # Prepare for new response
        self._obs_event.clear()
        self._last_obs = None

        msg_id = self._new_msg_id()
        self._pending_id = msg_id
        self._pending_type = "reset_response"

        msg = Message(MessageType.RESET)
        data = msg.to_dict()
        data["id"] = msg_id

        self._to_godot.put(data)
        logger.info(f"[HFTransport] queued RESET (id={msg_id}).")

        return await self._wait_for_observation("reset", msg_id)

    async def _async_step(self, action: int) -> Dict[str, Any]:
        if self._obs_event is None:
            self._obs_event = asyncio.Event()

        self._obs_event.clear()
        self._last_obs = None

        msg_id = self._new_msg_id()
        self._pending_id = msg_id
        self._pending_type = "step_response"

        payload = ActionPayload(int(action))
        msg = Message(MessageType.STEP, payload)
        data = msg.to_dict()
        data["id"] = msg_id

        self._to_godot.put(data)
        logger.debug(f"[HFTransport] queued STEP({action}) (id={msg_id}).")

        return await self._wait_for_observation(f"step({action})", msg_id)

    # ------------------------------------------------------------------
    # Observation wait — with ID matching
    # ------------------------------------------------------------------

    async def _wait_for_observation(self, context: str, expected_id: int) -> Dict[str, Any]:
        assert self._obs_event is not None

        try:
            await asyncio.wait_for(self._obs_event.wait(), timeout=self.timeout)
        except asyncio.TimeoutError as exc:
            raise TransportTimeout(
                f"{self.name}: Timeout waiting for observation after {context} (id={expected_id})."
            ) from exc

        # NEW: Check for reconnection interrupt
        if getattr(self, "_reconnected", False):
            self._reconnected = False  # Consume flag
            raise self.ReconnectionError(f"{self.name}: Operation interrupted by client reconnection.")

        if self._last_obs is None:
            raise TransportError(
                f"{self.name}: Observation event set but no payload received after {context}."
            )

        # NEW: Verify the ID matches
        obs_id = self._last_obs.get("id")
        if obs_id != expected_id:
            raise TransportError(
                f"{self.name}: Received mismatched observation id={obs_id}, expected id={expected_id}."
            )

        return self._last_obs

    def handle_reconnect(self) -> None:
        """
        Called when a new client connects (e.g. page refresh).
        Interrupts any pending wait and resets internal state.
        """
        logger.warning(f"[{self.name}] Client Reconnected! Interrupting pending operations.")

        # 1. Reset protocol state
        self._pending_id = None
        self._pending_type = None
        self._config_sent = False

        # 2. Signal any waiting coroutines to wake up
        # We set a special flag or just set the event and let them check state?
        # A cleaner way is to set an error state on the transport that wait() checks.
        self._reconnected = True

        if self._obs_event:
            self._obs_event.set()

        if self._human_action_event:
            self._human_action_event.set()

    def send_config(self) -> None:
        """Send configuration to Godot via queue."""
        if not self.cfg:
            logger.warning(f"[{self.name}] No config available to send to Godot")
            return

        if self._config_sent:
            logger.debug(f"[{self.name}] Config already sent, skipping")
            return

        try:
            # Extract config values from Hydra config
            max_episode_steps = int(self.cfg.env.episode.max_episode_steps)
            starting_gold = int(self.cfg.env.episode.starting_gold)
            base_health = int(self.cfg.env.episode.base_health)

            config_data = ConfigData(
                headless=self.cfg.runtime.get("headless", True),
                port=self.cfg.runtime.server.get("port", 7860),
                host=self.cfg.runtime.server.get("host", "0.0.0.0"),
                max_episode_steps=max_episode_steps,
                starting_gold=starting_gold,
                base_health=base_health,
            )

            config_msg = create_config_message(config_data)
            self._to_godot.put(config_msg.to_dict())
            self._config_sent = True

            logger.info(
                f"[{self.name}] Queued config for Godot: max_episode_steps={max_episode_steps}, "
                f"starting_gold={starting_gold}, base_health={base_health}"
            )
        except AttributeError as e:
            logger.error(f"[{self.name}] Config missing required fields: {e}")
        except Exception as e:
            logger.error(f"[{self.name}] Failed to queue config: {e}")

    # ------------------------------------------------------------------
    # Interface for FastAPI godot_endpoint
    # ------------------------------------------------------------------

    def pop_command(self, block: bool = False, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        try:
            return self._to_godot.get(block=block, timeout=timeout)
        except Exception:
            return None

    def push_observation(self, obs: Dict[str, Any]) -> None:
        """
        Called from godot_endpoint on incoming reset_response or step_response.
        Only wake the waiting coroutine if the message ID matches.
        """
        logger.debug(f"[HFTransport] observation received: {obs}")

        # Put in raw queue (optional)
        self._from_godot.put(obs)

        if self._obs_event is None:
            self._obs_event = asyncio.Event()

        obs_id = obs.get("id")
        pending = self._pending_id

        if obs_id != pending:
            logger.warning(
                f"[HFTransport] Dropping stale observation id={obs_id}, expected id={pending}."
            )
            return

        # Good: this is the awaited observation
        self._last_obs = obs
        if self._loop:
            self._loop.call_soon_threadsafe(self._obs_event.set)
        else:
            # Fallback if loop not available (should not happen if connected)
            self._obs_event.set()

    def push_human_action(self, action_data: Dict[str, Any]) -> None:
        """
        Called from godot_endpoint on incoming human_action.

        This enables human demonstrations for imitation learning or human-in-the-loop
        training on HuggingFace Spaces.

        Args:
            action_data: Dictionary containing 'slot_index' key with the action value
        """
        if "slot_index" not in action_data:
            logger.warning(f"[HFTransport] Malformed human_action, missing 'slot_index': {action_data}")
            return

        self._last_human_action = int(action_data["slot_index"])
        logger.debug(f"[HFTransport] human_action received: slot_index={self._last_human_action}")

        # Signal waiting coroutine (if any)
        if self._human_action_event and self._loop:
            self._loop.call_soon_threadsafe(self._human_action_event.set)
        elif self._human_action_event:
            # Fallback if loop not available
            self._human_action_event.set()

    async def _async_get_human_action(self) -> Optional[int]:
        """
        Wait for a human action from Godot.

        This enables human demonstrations for imitation learning or human-in-the-loop
        training. For pure RL training, this method won't be called.

        Returns:
            The slot index of the human action, or None if no action available.

        Raises:
            TransportDisconnected: If called before connection is established.
        """
        if not self._connected:
            raise TransportDisconnected(
                f"{self.name}: get_human_action() called before connect()."
            )

        assert self._human_action_event is not None

        # Clear previous event state
        self._human_action_event.clear()
        self._last_human_action = None

        try:
            # Wait indefinitely for human input
            await self._human_action_event.wait()
        except asyncio.CancelledError:
            raise

        return self._last_human_action
