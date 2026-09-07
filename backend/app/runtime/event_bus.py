"""
AEGIS Event Bus
===============

Asynchronous publish/subscribe event infrastructure.

The EventBus allows the runtime to remain independent from:

- WebSockets
- UI
- logging
- tracing
- analytics
- future plugins

Anything interested in AEGIS events subscribes to the bus.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections import defaultdict
from typing import (
    Any,
    Awaitable,
    Callable,
    DefaultDict,
    List,
    Optional,
)

from .events import AegisEvent, EventType


logger = logging.getLogger("aegis.event_bus")


EventHandler = Callable[
    [AegisEvent],
    Any,
]


class EventBus:
    """
    Lightweight asynchronous event bus.

    Supports:

        bus.subscribe(handler)

    and:

        await bus.emit(event)
    """

    def __init__(
        self,
        *,
        max_history: int = 500,
    ) -> None:

        self.max_history = max_history

        self._handlers: List[EventHandler] = []

        self._typed_handlers: DefaultDict[
            str,
            List[EventHandler],
        ] = defaultdict(list)

        self._history: List[AegisEvent] = []

        self._sequence = 0

        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def subscribe(
        self,
        handler: EventHandler,
        event_type: Optional[EventType | str] = None,
    ) -> Callable[[], None]:
        """
        Subscribe a handler.

        Returns an unsubscribe function.
        """

        if event_type is None:
            self._handlers.append(handler)

            def unsubscribe() -> None:
                if handler in self._handlers:
                    self._handlers.remove(handler)

            return unsubscribe

        key = self._event_key(event_type)

        self._typed_handlers[key].append(handler)

        def unsubscribe() -> None:
            handlers = self._typed_handlers.get(key)

            if handlers and handler in handlers:
                handlers.remove(handler)

        return unsubscribe

    # ------------------------------------------------------------------
    # Publishing
    # ------------------------------------------------------------------

    async def emit(
        self,
        event: AegisEvent,
    ) -> AegisEvent:
        """
        Publish an event to all matching subscribers.
        """

        async with self._lock:

            self._sequence += 1
            event.sequence = self._sequence

            self._history.append(event)

            if len(self._history) > self.max_history:
                self._history = self._history[
                    -self.max_history:
                ]

        handlers = list(self._handlers)

        event_key = self._event_key(event.type)

        handlers.extend(
            self._typed_handlers.get(
                event_key,
                [],
            )
        )

        if not handlers:
            return event

        results = []

        for handler in handlers:

            try:

                result = handler(event)

                if inspect.isawaitable(result):
                    results.append(result)

            except Exception:
                logger.exception(
                    "Event handler failed for %s",
                    event.type,
                )

        if results:
            await asyncio.gather(
                *results,
                return_exceptions=True,
            )

        return event

    def emit_nowait(
        self,
        event: AegisEvent,
    ) -> asyncio.Task[AegisEvent]:
        """
        Schedule event publishing without awaiting it.
        """

        return asyncio.create_task(
            self.emit(event)
        )

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def history(
        self,
        *,
        limit: Optional[int] = None,
    ) -> List[AegisEvent]:

        events = list(self._history)

        if limit is not None:
            return events[-limit:]

        return events

    def clear_history(self) -> None:
        self._history.clear()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _event_key(
        event_type: EventType | str,
    ) -> str:

        if isinstance(event_type, EventType):
            return event_type.value

        return str(event_type)

    @property
    def subscriber_count(self) -> int:
        typed_count = sum(
            len(items)
            for items in self._typed_handlers.values()
        )

        return len(self._handlers) + typed_count


__all__ = [
    "EventBus",
    "EventHandler",
]