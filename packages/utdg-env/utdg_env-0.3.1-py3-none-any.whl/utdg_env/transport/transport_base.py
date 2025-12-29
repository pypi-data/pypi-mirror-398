from __future__ import annotations

import abc
import asyncio
import threading
from typing import Any, Optional


class TransportError(RuntimeError):
    """Raised when communication with the simulator fails."""


class TransportTimeout(RuntimeError):
    """Raised when awaiting a response exceeds the configured timeout."""


class TransportDisconnected(RuntimeError):
    """Raised when the underlying WebSocket connection is unexpectedly closed."""


class Transport(abc.ABC):
    """Abstract base class for all UTDG simulator transports.

    This provides a synchronous public API backed by async networking,
    executed on a dedicated background event loop thread.

    Concrete transports must implement the async protocol:
        _async_connect, _async_reset, _async_step, _async_close
    """

    def __init__(
        self,
        timeout: float = 30.0,
        reconnect_attempts: int = 3,
        name: str = "UTDGTransport",
    ) -> None:
        self.timeout = timeout
        self.reconnect_attempts = reconnect_attempts
        self.name = name

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._connected: bool = False

        self._start_background_loop()

    # ------------------------------------------------------------------
    # Background event loop management
    # ------------------------------------------------------------------

    def _start_background_loop(self) -> None:
        """Create a dedicated asyncio loop in a daemon thread."""
        if self._loop is not None:
            # already initialized
            return

        self._loop = asyncio.new_event_loop()

        def _loop_runner() -> None:
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()

        self._thread = threading.Thread(
            target=_loop_runner,
            name=f"{self.name}-Loop",
            daemon=True,
        )
        self._thread.start()

    def _run_async(self, coro, timeout: Optional[float] = -1.0) -> Any:
        """Submit coroutine to background loop and wait synchronously.

        Args:
            coro: Coroutine to run.
            timeout: Timeout in seconds.
                     If -1.0 (default), uses self.timeout.
                     If None, waits indefinitely.
        """
        if self._loop is None:
            raise RuntimeError("Transport event loop not initialized.")

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)

        # Determine effective timeout
        # future.result(timeout=None) waits indefinitely
        wait_time = self.timeout if timeout == -1.0 else timeout

        try:
            return future.result(timeout=wait_time)

        except TimeoutError:
            # (Python <3.11) catching generic, since queue may raise a different TimeoutError
            raise TransportTimeout(
                f"{self.name}: Operation exceeded timeout ({wait_time}s)."
            )

        except asyncio.TimeoutError:
            # asyncio-native timeout
            raise TransportTimeout(
                f"{self.name}: Operation exceeded timeout ({wait_time}s)."
            )

        except Exception as e:
            raise TransportError(f"{self.name}: Transport operation failed: {e}") from e

    # ------------------------------------------------------------------
    # Public synchronous API
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Establish transport connection with retry support."""
        for attempt in range(1, self.reconnect_attempts + 1):
            try:
                self._run_async(self._async_connect())
                self._connected = True
                return
            except Exception as e:
                if attempt == self.reconnect_attempts:
                    raise TransportError(
                        f"{self.name}: Could not connect after {attempt} attempts: {e}"
                    )

    def reset(self) -> dict:
        """Request reset → return initial observation."""
        if not self._connected:
            raise TransportDisconnected(
                f"{self.name}: reset() called before connect()."
            )
        return self._run_async(self._async_reset())

    def step(self, action: int) -> dict:
        """Single RL step → return observation payload."""
        if not self._connected:
            raise TransportDisconnected(
                f"{self.name}: step() called before connect()."
            )
        return self._run_async(self._async_step(action))

    def close(self) -> None:
        """Close connection and shut down transport loop."""
        self._connected = False

        try:
            self._run_async(self._async_close())
        except Exception:
            # close should be tolerant to broken sockets / half-duplex shutdown
            pass

        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

        self._loop = None

    # ------------------------------------------------------------------
    # Async transport protocol — must be implemented by subclass
    # ------------------------------------------------------------------

    @abc.abstractmethod
    async def _async_connect(self) -> None:
        """Async setup hook."""
        ...

    @abc.abstractmethod
    async def _async_reset(self) -> dict:
        """Async reset."""
        ...

    @abc.abstractmethod
    async def _async_step(self, action: int) -> dict:
        """Async step."""
        ...

    @abc.abstractmethod
    async def _async_close(self) -> None:
        """Async teardown."""
        ...

    @abc.abstractmethod
    async def _async_get_human_action(self) -> Optional[int]:
        """Async get human action."""
        ...

    def get_human_action(self) -> Optional[int]:
        """Get the next human action from the queue (blocking).

        Returns:
            Slot index of the human action, or None if no action.
        """
        if not self._connected:
            raise TransportDisconnected(
                f"{self.name}: get_human_action() called before connect()."
            )
        # Wait indefinitely for human input
        return self._run_async(self._async_get_human_action(), timeout=None)
