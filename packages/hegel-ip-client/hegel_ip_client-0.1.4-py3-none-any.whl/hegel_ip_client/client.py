"""Async client for Hegel amplifiers with push + command support."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import re
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable

from .exceptions import HegelConnectionError

_LOGGER = logging.getLogger(__name__)

CR = "\r"


@dataclass
class HegelStateUpdate:
    """Represents a state update from a Hegel device."""

    power: bool | None = None
    volume: float | None = None
    mute: bool | None = None
    input: int | None = None
    reset: str | None = None

    def has_changes(self) -> bool:
        """Check if this update contains any changes."""
        return any(
            [
                self.power is not None,
                self.volume is not None,
                self.mute is not None,
                self.input is not None,
                self.reset is not None,
            ]
        )


def parse_reply_message(reply: str) -> HegelStateUpdate:
    """Parse a single reply/push message and return state changes.

    Args:
        reply: Raw reply string from the Hegel device

    Returns:
        HegelStateUpdate with parsed changes
    """
    update = HegelStateUpdate()

    if reply.startswith("-p."):
        update.power = reply.endswith(".1")
    elif reply.startswith("-v."):
        m = re.search(r"-v\.(\d+)", reply)
        if m:
            level = int(m.group(1))
            update.volume = max(0.0, min(1.0, level / 100.0))
    elif reply.startswith("-m."):
        # -m.1 means muted, -m.0 unmuted
        update.mute = "1" in reply and "0" not in reply
    elif reply.startswith("-i."):
        m = re.search(r"-i\.(\d+)", reply)
        if m:
            update.input = int(m.group(1))
    elif reply.startswith("-r.") or reply.startswith("-reset"):
        update.reset = reply

    return update


def apply_state_changes(
    state: dict[str, Any],
    update: HegelStateUpdate,
    logger: logging.Logger | None = None,
    source: str = "reply",
) -> None:
    """Apply parsed changes to the state dictionary.

    Args:
        state: State dictionary to update
        update: HegelStateUpdate containing the changes
        logger: Optional logger for debug output
        source: Source of the update (for logging)
    """
    if logger is None:
        logger = _LOGGER

    if update.power is not None:
        logger.debug("[%s] Power: %s", source, update.power)
        state["power"] = update.power

    if update.volume is not None:
        logger.debug("[%s] Volume: %s", source, update.volume)
        state["volume"] = update.volume

    if update.mute is not None:
        logger.debug("[%s] Mute: %s", source, update.mute)
        state["mute"] = update.mute

    if update.input is not None:
        logger.debug("[%s] Input: %s", source, update.input)
        state["input"] = update.input

    if update.reset is not None:
        logger.debug("[%s] Reset/heartbeat: %s", source, update.reset)
        state["reset"] = update.reset


class HegelClient:
    """Async client for Hegel amplifiers with push + command support.

    This client maintains a persistent TCP connection to the Hegel amplifier
    and handles automatic reconnection with exponential backoff. It supports
    both command/response communication and push notifications from the device.

    Usage:
        client = HegelClient("192.168.1.100", 50001)
        await client.start()
        await client.ensure_connected()

        # Send command and get response
        response = await client.send("-p.1", expect_reply=True)

        # Stop when done
        await client.stop()

    Attributes:
        host: The IP address or hostname of the Hegel amplifier
        port: The TCP port number
        connected_event: An asyncio.Event that is set when connected
    """

    def __init__(self, host: str, port: int = 50001) -> None:
        """Initialize the Hegel client.

        Args:
            host: IP address or hostname of the Hegel amplifier
            port: TCP port (default: 50001)
        """
        self._host = host
        self._port = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._write_lock = asyncio.Lock()

        # Lifecycle management
        self._stopping = False
        self._listen_task: asyncio.Task[None] | None = None
        self._manager_task: asyncio.Task[None] | None = None
        self._connected_event = asyncio.Event()
        self._reconnect_lock = asyncio.Lock()

        # Pending command futures (FIFO queue)
        self._pending: deque[asyncio.Future[str]] = deque()
        self._pending_lock = asyncio.Lock()

        # Push notification callbacks
        self._push_callbacks: list[Callable[[str], None]] = []

        # Track if this is the first connection (for logging)
        self._has_connected_before = False

    def __repr__(self) -> str:
        """Return a string representation of the client."""
        status = "connected" if self.is_connected() else "disconnected"
        return f"HegelClient({self._host}:{self._port}, {status})"

    # ------------------------------------------------------------------ #
    # Public Properties
    # ------------------------------------------------------------------ #

    @property
    def host(self) -> str:
        """Return the host address."""
        return self._host

    @property
    def port(self) -> int:
        """Return the port number."""
        return self._port

    @property
    def connected_event(self) -> asyncio.Event:
        """Return the connected event for external monitoring.

        This event is set when the client is connected and cleared when
        disconnected. Use this for connection state monitoring.
        """
        return self._connected_event

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def is_connected(self) -> bool:
        """Return True if connected to the device."""
        return self._connected_event.is_set()

    async def start(self) -> None:
        """Start the connection manager.

        The connection manager runs in the background and maintains the
        connection, automatically reconnecting with exponential backoff
        if the connection is lost.
        """
        async with self._reconnect_lock:
            if self._manager_task and not self._manager_task.done():
                _LOGGER.debug("Connection manager already running")
                return

            self._stopping = False
            _LOGGER.debug("Starting connection manager for %s:%s", self._host, self._port)
            self._manager_task = asyncio.create_task(
                self._manage_connection(), name="hegel_connection_manager"
            )

    async def stop(self) -> None:
        """Stop the client and close the connection."""
        _LOGGER.debug("Stopping client for %s:%s", self._host, self._port)
        self._stopping = True

        # Cancel manager task
        if self._manager_task:
            self._manager_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._manager_task
            self._manager_task = None

        # Close connection (this also cancels listen task)
        await self._close_connection()

        # Reset state for potential restart
        self._has_connected_before = False

    def add_push_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback for push messages.

        Args:
            callback: Function to call with the raw message string
        """
        if callback not in self._push_callbacks:
            self._push_callbacks.append(callback)

    def remove_push_callback(self, callback: Callable[[str], None]) -> None:
        """Remove a previously registered push callback.

        Args:
            callback: The callback to remove
        """
        if callback in self._push_callbacks:
            self._push_callbacks.remove(callback)

    async def send(
        self, command: str, expect_reply: bool = True, timeout: float = 5.0
    ) -> HegelStateUpdate | None:
        """Send a command to the amplifier.

        Args:
            command: Command string to send
            expect_reply: Whether to wait for a reply
            timeout: Timeout in seconds for the reply

        Returns:
            HegelStateUpdate with parsed response if expect_reply=True, else None

        Raises:
            HegelConnectionError: If the send fails
            TimeoutError: If no reply is received within timeout
        """
        # Normalize line ending
        command_to_send = command if command.endswith(CR) else command + CR

        await self.ensure_connected()

        fut: asyncio.Future[str] | None = None
        async with self._write_lock:
            if expect_reply:
                fut = asyncio.get_running_loop().create_future()
                async with self._pending_lock:
                    self._pending.append(fut)

            try:
                if self._writer is None:
                    raise HegelConnectionError("Not connected")
                self._writer.write(command_to_send.encode())
                await self._writer.drain()
            except OSError as err:
                if fut:
                    async with self._pending_lock:
                        if fut in self._pending:
                            self._pending.remove(fut)
                    if not fut.done():
                        fut.set_exception(err)
                _LOGGER.debug("Send failed, closing connection: %s", err)
                await self._close_connection()
                raise HegelConnectionError(
                    f"Failed to send command to Hegel device: {err}"
                ) from err

        if not fut:
            return None

        try:
            raw_reply = await asyncio.wait_for(fut, timeout=timeout)
            return parse_reply_message(raw_reply)
        except asyncio.TimeoutError:
            _LOGGER.debug("Timeout waiting for reply to %s", command.strip())
            # Remove the future from pending if still there
            async with self._pending_lock:
                if fut in self._pending:
                    self._pending.remove(fut)
            raise

    async def ensure_connected(self, timeout: float = 5.0) -> None:
        """Wait until connected or raise TimeoutError.

        Args:
            timeout: Maximum time to wait for connection

        Raises:
            TimeoutError: If not connected within timeout
        """
        if self._connected_event.is_set():
            return

        async with self._reconnect_lock:
            if not self._connected_event.is_set():
                if not self._manager_task or self._manager_task.done():
                    await self.start()

        try:
            await asyncio.wait_for(self._connected_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError("Timeout waiting for connection") from None

    async def disconnect(self) -> None:
        """Disconnect from the device. Alias for stop()."""
        await self.stop()

    # ------------------------------------------------------------------ #
    # Connection Management (Private)
    # ------------------------------------------------------------------ #

    async def _manage_connection(self) -> None:
        """Maintain connection with automatic reconnection and backoff."""
        backoff = 1.0
        max_backoff = 60.0

        _LOGGER.debug("Connection manager started for %s:%s", self._host, self._port)

        while not self._stopping:
            try:
                await self._open_connection()
                backoff = 1.0  # Reset on successful connection

                # Wait for listen task to complete (happens on disconnect)
                if self._listen_task:
                    _LOGGER.debug("Waiting for listen task to complete")
                    await self._listen_task
                    _LOGGER.debug("Listen task completed, will attempt reconnect")

            except asyncio.CancelledError:
                _LOGGER.debug("Connection manager cancelled")
                break
            except HegelConnectionError as err:
                _LOGGER.debug(
                    "Connection to %s:%s failed: %s — retrying in %.1fs",
                    self._host,
                    self._port,
                    err,
                    backoff,
                )
                await asyncio.sleep(backoff)
                backoff = min(max_backoff, backoff * 2)

        _LOGGER.debug("Connection manager stopped for %s:%s", self._host, self._port)

    async def _open_connection(self) -> None:
        """Open TCP connection and start the listen task."""
        if self._writer and not self._writer.is_closing():
            return

        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=10.0,
            )
        except asyncio.TimeoutError as err:
            self._connected_event.clear()
            raise HegelConnectionError(
                f"Timeout connecting to {self._host}:{self._port}"
            ) from err
        except OSError as err:
            self._connected_event.clear()
            raise HegelConnectionError(
                f"Failed to connect to {self._host}:{self._port}: {err}"
            ) from err

        self._connected_event.set()

        # Log appropriately based on whether this is initial connect or reconnect
        if self._has_connected_before:
            _LOGGER.info("Reconnected to Hegel at %s:%s", self._host, self._port)
        else:
            _LOGGER.debug("Connected to Hegel at %s:%s", self._host, self._port)
            self._has_connected_before = True

        # Start listen task
        if self._listen_task and not self._listen_task.done():
            _LOGGER.debug("Cancelling existing listen task")
            self._listen_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listen_task

        _LOGGER.debug("Starting listen loop")
        self._listen_task = asyncio.create_task(
            self._listen_loop(), name="hegel_listen_loop"
        )

    async def _close_connection(self) -> None:
        """Close connection and clean up resources."""
        _LOGGER.debug("Closing connection to %s:%s", self._host, self._port)
        self._connected_event.clear()

        # Cancel listen task
        if self._listen_task and not self._listen_task.done():
            _LOGGER.debug("Cancelling listen task")
            self._listen_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listen_task
            self._listen_task = None

        # Close writer
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except OSError:
                pass

        self._reader = None
        self._writer = None

        # Fail pending futures
        async with self._pending_lock:
            pending_count = len(self._pending)
            if pending_count:
                _LOGGER.debug("Failing %d pending futures", pending_count)
            while self._pending:
                fut = self._pending.popleft()
                if not fut.done():
                    fut.set_exception(HegelConnectionError("Connection closed"))

    # ------------------------------------------------------------------ #
    # Listen Loop (Private)
    # ------------------------------------------------------------------ #

    async def _listen_loop(self) -> None:
        """Read messages from the device and route to pending futures or callbacks."""
        disconnect_reason: str | None = None
        _LOGGER.debug("Listen loop started")

        try:
            if self._reader is None:
                return

            while not self._reader.at_eof() and not self._stopping:
                try:
                    line = await self._reader.readuntil(separator=b"\r")
                except asyncio.IncompleteReadError as err:
                    disconnect_reason = f"Incomplete read: {err}"
                    break
                except OSError as err:
                    disconnect_reason = str(err)
                    break

                msg = line.decode(errors="ignore").strip()
                if not msg:
                    continue

                _LOGGER.debug("Received: %s", msg)

                # Route to pending future or push callback
                async with self._pending_lock:
                    if self._pending:
                        fut = self._pending.popleft()
                        if not fut.done():
                            fut.set_result(msg)
                        continue

                # No pending future - dispatch as push
                self._dispatch_push(msg)

        except asyncio.CancelledError:
            _LOGGER.debug("Listen loop cancelled")
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Unexpected error in listen loop: %s", err)
            disconnect_reason = str(err)
        finally:
            # Signal disconnection - manager will handle reconnect
            self._connected_event.clear()
            if disconnect_reason and not self._stopping:
                _LOGGER.debug("Disconnected from %s:%s: %s", self._host, self._port, disconnect_reason)
            _LOGGER.debug("Listen loop ended")

    def _dispatch_push(self, msg: str) -> None:
        """Dispatch a push message to all registered callbacks."""
        for callback in self._push_callbacks:
            try:
                callback(msg)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Push callback failed for message: %s", msg)
