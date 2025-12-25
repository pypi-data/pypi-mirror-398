
"""
Module: aimpf.mqtt.logger

This module provides the AimpfLogger class and utility functions for
subscribing to and logging AIMPF administrative metrics over MQTT.

Features:
    - Automatic subscription to multiple admin levels at a specified QoS.
    - Blocking until each subscription is acknowledged (SUBACK) for reliability.
    - Utilization of Paho's built-in background I/O threads (loop_start/loop_stop).
    - A single monitoring thread to enforce idle or total runtime limits.
    - Clean teardown of all MQTT loops, client disconnects, and subscription contexts,
      even in the face of exceptions or interpreter shutdown.

Utilities:
    topic_logger_filter: Create a logging.Filter for a set of logger names.
    broker_echo: Default callback to log broker messages.
    enable_console_aimpf: Configure root logger to output only AIMPF messages.
"""

import atexit
import logging
import os
import threading
import time
import weakref
from typing import Any, Callable, Literal, Optional, Sequence, Type, Union

from paho.mqtt.client import Client
from .subscriber import AimpfSubscriber
from pycarta.mqtt.credentials import TLSCredentials

__all__ = [
    "AimpfLogger",
    "topic_logger_filter",
    "broker_echo",
    "enable_console_aimpf",
    "LEVEL_MAP",
]

# Poll interval for monitor thread in seconds
_POLL = float(os.environ.get("AIMPF_LOGGER_POLL_INTERVAL") or 0.25)

# Mapping of AIMPF metric names to Python logging levels
LEVEL_MAP = {
    "Information": logging.INFO,
    "Warning":     logging.WARNING,
    "Error":       logging.ERROR,
    "Alarm":       logging.CRITICAL,
}

# Module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


def topic_logger_filter(topics: Sequence[str]) -> logging.Filter:
    """
    Create a filter that only allows records from specified logger names.

    Args:
        topics: Sequence of logger names to allow.

    Returns:
        A logging.Filter instance.
    """
    wanted = set(topics)

    class _Filter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return record.name in wanted

    return _Filter()


def broker_echo(level: str, payload: Any) -> None:
    """
    Default callback that logs broker messages via the module logger.

    Args:
        level: AIMPF metric level name (e.g. 'Warning').
        payload: Message payload.
    """
    logger.log(LEVEL_MAP.get(level, logging.INFO), "[AIMPF broker]: %s", payload)


def enable_console_aimpf(level: int = logging.INFO, aimpf_only: bool = True) -> None:
    """
    Configure root logger to output console messages for AIMPF.

    Args:
        level: Logging level threshold.
        aimpf_only: If True, only messages containing "[AIMPF broker]" are shown.
    """
    # Remove existing handlers
    for h in list(logging.root.handlers):
        logging.root.removeHandler(h)

    root = logging.getLogger()
    root.setLevel(level)

    fmt = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(fmt)
    handler.setLevel(level)
    if aimpf_only:
        handler.addFilter(lambda r: "[AIMPF broker]" in r.getMessage())
    root.addHandler(handler)


class _ThreadCtl:
    """
    Mixin providing start/stop control for a single background thread.
    """
    _alive: threading.Event
    _thread: threading.Thread | None = None

    def start(self) -> "_ThreadCtl":
        """
        Launch the background thread if not already running.

        Returns:
            Self, for chaining.
        """
        if not self.active:
            self._alive = threading.Event()
            self._alive.set()
            self._thread = threading.Thread(target=self._run, daemon=True)  # type: ignore[reportAttributeAccessIssue]
            self._thread.start()
        return self

    def stop(self) -> None:
        """
        Signal the background thread to stop and wait up to 5 seconds,
        unless called from within that thread itself.
        """
        if self._thread:
            self._alive.clear()
            # Avoid joining the current thread
            if threading.current_thread() is not self._thread:
                self._thread.join(timeout=5)
            self._thread = None

    @property
    def active(self) -> bool:
        """Whether the thread is currently alive."""
        return bool(self._thread and self._thread.is_alive())

    def __enter__(self) -> "_ThreadCtl":
        return self.start()

    def __exit__(self, exc_type: Optional[Type[BaseException]], *_: Any) -> bool:
        self.stop()
        return False


class AimpfLogger(_ThreadCtl):
    """
    Logger that subscribes to AIMPF admin metrics and dispatches messages.

    This class:
        - Subscribes to multiple admin metric levels.
        - Blocks until each subscription is acknowledged (SUBACK).
        - Uses Paho's loop_start on each client for network I/O.
        - Runs a monitor thread to enforce idle/total runtime limits.
        - Cleans up all MQTT loops, disconnects clients, and closes contexts.
    """

    def __init__(
        self,
        *,
        project: str,
        node: str,
        device: str,
        levels: Union[str, Sequence[str]] = ("Information",),
        qos: Literal[1, 2, 3] = 1,
        subscribe_timeout: float = 2.0,
        idle_timeout: Optional[float] = None,
        run_for: Optional[float] = None,
        callback: Optional[Callable[[str, Any], None]] = None,
        credentials: Union[str, TLSCredentials, None] = None,
    ) -> None:
        # Validate requested levels
        lvl_list = [levels] if isinstance(levels, str) else list(levels)
        invalid = list(set(lvl_list) - set(LEVEL_MAP))
        if invalid:
            raise ValueError(f"Invalid metric level(s): {invalid}")

        # Store config
        self._project = project
        self._node = node
        self._device = device
        self._levels = lvl_list
        self._qos = qos
        self._subscribe_timeout = subscribe_timeout
        self._idle = idle_timeout
        self._total = run_for
        self._cb = callback or broker_echo
        self._creds = credentials

        # Internal state
        self._clients: list[Client] = []
        self._subready: list[threading.Event] = []
        self._opened_tasks: list[Any] = []
        self._stopped = False

        # Create subscriber contexts and start Paho IO threads
        for level in self._levels:
            sub = AimpfSubscriber(
                project=project,
                node=node,
                device=device,
                metric=level,
                credentials=self._creds,
                qos=self._qos,
            )
            # subscription context opens the MQTT client
            task = sub(lambda payload, _lvl=level: self._dispatch(_lvl, payload))
            try:
                task.__enter__()  # type: ignore[reportAttributeAccessIssue]
                self._opened_tasks.append(task)
            except:
                # cleanup already-opened tasks
                for otask in self._opened_tasks:
                    try:
                        otask.__exit__(None, None, None)
                    except Exception:
                        pass
                raise

            client = task.scope.connection.client
            self._clients.append(client)  # type: ignore[reportArgumentType]

            # setup SUBACK event
            ev = threading.Event()
            client.on_subscribe = lambda *args, ev=ev: ev.set()  # type: ignore[reportAttributeAccessIssue]
            self._subready.append(ev)

            # use Paho's auto loop
            client.loop_start()  # type: ignore[reportAttributeAccessIssue]

        # safety nets
        atexit.register(self.stop)
        weakref.finalize(self, self.stop)

    def start(self) -> "AimpfLogger":
        """
        Wait for subscriptions then launch monitor thread.

        Returns:
            Self for chaining.
        """
        logger.info(f"Waiting to subscribe to metrics: {self._levels}…")
        # Wait for all SUBACKs
        deadline = time.monotonic() + self._subscribe_timeout
        for ev in self._subready:
            while not ev.is_set() and time.monotonic() < deadline:
                time.sleep(0.01)
        logger.info("Subscriptions established, ready for messages.")
        return super().start()  # type: ignore[reportReturnType]

    def _run(self) -> None:
        """
        Monitor idle and total time, then stop logger.
        """
        start = self._last = time.monotonic()
        while self._alive.is_set():
            now = time.monotonic()
            # total runtime limit
            if self._total is not None and now - start >= self._total:
                break
            # idle inactivity limit
            if self._idle is not None and now - self._last >= self._idle:
                break
            time.sleep(_POLL)
        # call stop() will not join current thread
        self.stop()

    def _dispatch(self, level: str, payload: Any) -> None:
        """
        Internal callback to invoke user callback and update idle timer.

        Args:
            level: Metric level name.
            payload: Message payload.
        """
        if not (getattr(self, "_alive", None) and self._alive.is_set()):
            return
        # reset idle timer
        self._last = time.monotonic()
        self._cb(level, payload)

    def stop(self) -> None:
        """
        Stop monitor thread, stop Paho loops, disconnect, and close contexts.
        """
        if self._stopped:
            return
        self._stopped = True
        # stop monitor thread
        super().stop()
        # cleanup MQTT clients
        for client in self._clients:
            try:
                client.loop_stop(wait=True)  # type: ignore[reportCallIssue]
                client.disconnect()
            except Exception:
                pass
        # close subscriber contexts
        for task in self._opened_tasks:
            try:
                task.__exit__(None, None, None)
            except Exception:
                pass

    def __del__(self) -> None:
        """
        Finalizer to ensure shutdown if object is garbage-collected.
        """
        try:
            self.stop()
        except Exception:
            pass

