"""
AEGIS Event System
==================

Central event definitions for the AEGIS runtime.

This module intentionally keeps compatibility with the existing AEGIS
runtime, which historically imports:

    from app.runtime.events import Event, EventType

while also exposing the newer AegisEvent name.

Events are the backbone of:

    Runtime
        ↓
    EventBus
        ↓
    WebSocket
        ↓
    AEGIS Command Center
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4


# ============================================================================
# EVENT TYPES
# ============================================================================


class EventType(str, Enum):
    """
    Canonical AEGIS event types.

    Keep these values stable because the frontend can use them to determine
    how an event should be rendered.
    """

    # ------------------------------------------------------------------------
    # System
    # ------------------------------------------------------------------------

    SYSTEM_STARTED = "SYSTEM_STARTED"
    SYSTEM_STOPPED = "SYSTEM_STOPPED"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    SYSTEM_WARNING = "SYSTEM_WARNING"
    SYSTEM_HEALTH_CHANGED = "SYSTEM_HEALTH_CHANGED"

    # ------------------------------------------------------------------------
    # Mission
    # ------------------------------------------------------------------------

    MISSION_CREATED = "MISSION_CREATED"
    MISSION_STARTED = "MISSION_STARTED"
    MISSION_PAUSED = "MISSION_PAUSED"
    MISSION_RESUMED = "MISSION_RESUMED"
    MISSION_COMPLETED = "MISSION_COMPLETED"
    MISSION_FAILED = "MISSION_FAILED"
    MISSION_CANCELLED = "MISSION_CANCELLED"

    # ------------------------------------------------------------------------
    # Planning
    # ------------------------------------------------------------------------

    PLAN_STARTED = "PLAN_STARTED"
    PLAN_CREATED = "PLAN_CREATED"
    PLAN_UPDATED = "PLAN_UPDATED"
    PLAN_FAILED = "PLAN_FAILED"
    REPLAN_STARTED = "REPLAN_STARTED"
    REPLAN_COMPLETED = "REPLAN_COMPLETED"

    # ------------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------------

    TASK_CREATED = "TASK_CREATED"
    TASK_READY = "TASK_READY"
    TASK_STARTED = "TASK_STARTED"
    TASK_RUNNING = "TASK_RUNNING"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    TASK_BLOCKED = "TASK_BLOCKED"
    TASK_CANCELLED = "TASK_CANCELLED"
    TASK_RETRY_REQUIRED = "TASK_RETRY_REQUIRED"

    # ------------------------------------------------------------------------
    # Agents
    # ------------------------------------------------------------------------

    AGENT_REGISTERED = "AGENT_REGISTERED"
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_WORKING = "AGENT_WORKING"
    AGENT_COMPLETED = "AGENT_COMPLETED"
    AGENT_FAILED = "AGENT_FAILED"
    AGENT_IDLE = "AGENT_IDLE"

    # ------------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------------

    TOOL_CALL_STARTED = "TOOL_CALL_STARTED"
    TOOL_CALL_COMPLETED = "TOOL_CALL_COMPLETED"
    TOOL_CALL_FAILED = "TOOL_CALL_FAILED"
    TOOL_PERMISSION_REQUIRED = "TOOL_PERMISSION_REQUIRED"

    # ------------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------------

    VERIFICATION_STARTED = "VERIFICATION_STARTED"
    VERIFICATION_PASSED = "VERIFICATION_PASSED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"

    # ------------------------------------------------------------------------
    # Safety
    # ------------------------------------------------------------------------

    SAFETY_CHECK_STARTED = "SAFETY_CHECK_STARTED"
    SAFETY_APPROVAL_REQUIRED = "SAFETY_APPROVAL_REQUIRED"
    SAFETY_APPROVED = "SAFETY_APPROVED"
    SAFETY_REJECTED = "SAFETY_REJECTED"
    SAFETY_BLOCKED = "SAFETY_BLOCKED"

    # ------------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------------

    MEMORY_READ = "MEMORY_READ"
    MEMORY_WRITE = "MEMORY_WRITE"
    MEMORY_RETRIEVED = "MEMORY_RETRIEVED"

    # ------------------------------------------------------------------------
    # Runtime control
    # ------------------------------------------------------------------------

    RUNTIME_PAUSED = "RUNTIME_PAUSED"
    RUNTIME_RESUMED = "RUNTIME_RESUMED"
    RUNTIME_ERROR = "RUNTIME_ERROR"

    # ------------------------------------------------------------------------
    # Emergency
    # ------------------------------------------------------------------------

    EMERGENCY_STOP = "EMERGENCY_STOP"

    # ------------------------------------------------------------------------
    # Telemetry
    # ------------------------------------------------------------------------

    HEARTBEAT = "HEARTBEAT"


# ============================================================================
# EVENT SEVERITY
# ============================================================================


class EventSeverity(str, Enum):
    """
    Severity used by the UI and observability layer.
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================================
# EVENT
# ============================================================================


@dataclass(slots=True)
class Event:
    """
    Canonical AEGIS event.

    This is the compatibility class expected by the existing runtime.

    Example:

        event = Event(
            type=EventType.TASK_STARTED,
            source="runtime",
            message="Task started",
            task_id="task-123",
        )
    """

    type: EventType | str

    source: str = "runtime"

    message: str = ""

    severity: EventSeverity | str = EventSeverity.INFO

    mission_id: Optional[str] = None

    task_id: Optional[str] = None

    agent_id: Optional[str] = None

    data: Dict[str, Any] = field(
        default_factory=dict
    )

    event_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    timestamp: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    sequence: Optional[int] = None

    # ------------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the event into a JSON-safe dictionary.
        """

        payload = asdict(self)

        if isinstance(self.type, Enum):
            payload["type"] = self.type.value

        if isinstance(self.severity, Enum):
            payload["severity"] = self.severity.value

        return payload

    def model_dump(self) -> Dict[str, Any]:
        """
        Compatibility helper for code that expects Pydantic-like objects.
        """

        return self.to_dict()

    # ------------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        event_type: EventType | str,
        *,
        message: str = "",
        source: str = "runtime",
        severity: EventSeverity | str = EventSeverity.INFO,
        mission_id: Optional[str] = None,
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> "Event":

        return cls(
            type=event_type,
            source=source,
            message=message,
            severity=severity,
            mission_id=mission_id,
            task_id=task_id,
            agent_id=agent_id,
            data=data or {},
        )


# ============================================================================
# NEW NAME
# ============================================================================

# Newer AEGIS code can use AegisEvent.
#
# Existing code can continue using Event.
#
# They intentionally refer to the same class.

AegisEvent = Event


# ============================================================================
# HELPER FACTORIES
# ============================================================================


def system_event(
    event_type: EventType,
    message: str,
    *,
    severity: EventSeverity = EventSeverity.INFO,
    data: Optional[Dict[str, Any]] = None,
) -> Event:

    return Event.create(
        event_type,
        source="system",
        message=message,
        severity=severity,
        data=data,
    )


def mission_event(
    event_type: EventType,
    mission_id: str,
    message: str,
    *,
    data: Optional[Dict[str, Any]] = None,
) -> Event:

    return Event.create(
        event_type,
        source="mission",
        message=message,
        mission_id=mission_id,
        data=data,
    )


def task_event(
    event_type: EventType,
    task_id: str,
    message: str,
    *,
    mission_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Event:

    return Event.create(
        event_type,
        source="task",
        message=message,
        mission_id=mission_id,
        task_id=task_id,
        agent_id=agent_id,
        data=data,
    )


def agent_event(
    event_type: EventType,
    agent_id: str,
    message: str,
    *,
    mission_id: Optional[str] = None,
    task_id: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Event:

    return Event.create(
        event_type,
        source="agent",
        message=message,
        mission_id=mission_id,
        task_id=task_id,
        agent_id=agent_id,
        data=data,
    )


__all__ = [
    "Event",
    "AegisEvent",
    "EventType",
    "EventSeverity",
    "system_event",
    "mission_event",
    "task_event",
    "agent_event",
]