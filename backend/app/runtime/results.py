"""
AEGIS Runtime Results
=====================

Canonical result models used across the runtime, tools, validation,
supervision, and API layers.

This module intentionally exposes compatibility aliases/classes such as
ToolResult so older runtime modules continue to work while the architecture
is being upgraded.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================
# Helpers
# ============================================================

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _serialize(value: Any) -> Any:
    """
    Convert common Python objects into JSON-safe structures.
    """
    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, Enum):
        return value.value

    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()

    if hasattr(value, "model_dump") and callable(value.model_dump):
        return value.model_dump()

    if isinstance(value, dict):
        return {str(k): _serialize(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_serialize(v) for v in value]

    return value


# ============================================================
# Result Status
# ============================================================

class ResultStatus(str, Enum):
    """
    Canonical execution result status.
    """

    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    REJECTED = "rejected"
    PENDING = "pending"
    RUNNING = "running"


# ============================================================
# Tool Result
# ============================================================

@dataclass
class ToolResult:
    """
    Result returned by a tool execution.

    This is intentionally flexible because different tools may return
    different payload structures.
    """

    success: bool = False

    output: Any = None

    error: Optional[str] = None

    tool_name: Optional[str] = None

    status: ResultStatus = ResultStatus.SUCCESS

    metadata: Dict[str, Any] = field(default_factory=dict)

    started_at: Optional[datetime] = None

    completed_at: Optional[datetime] = None

    duration_ms: Optional[float] = None

    task_id: Optional[str] = None

    mission_id: Optional[str] = None

    agent_id: Optional[str] = None

    attempt: int = 1

    evidence: List[Any] = field(default_factory=list)

    confidence: Optional[float] = None

    # --------------------------------------------------------
    # Compatibility properties
    # --------------------------------------------------------

    @property
    def result(self) -> Any:
        """
        Compatibility alias.

        Some older code refers to the actual tool output as `result`
        instead of `output`.
        """
        return self.output

    @property
    def data(self) -> Any:
        """
        Compatibility alias for consumers expecting `data`.
        """
        return self.output

    @property
    def is_success(self) -> bool:
        return self.success

    @property
    def is_error(self) -> bool:
        return not self.success

    # --------------------------------------------------------
    # Serialization
    # --------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result into a JSON-safe dictionary.
        """

        data = asdict(self)

        return _serialize(data)

    def model_dump(self) -> Dict[str, Any]:
        """
        Pydantic-style compatibility method.
        """

        return self.to_dict()

    def json(self) -> str:
        """
        JSON representation.

        Kept lightweight so the runtime does not require Pydantic.
        """

        import json

        return json.dumps(self.to_dict(), default=str)

    # --------------------------------------------------------
    # Factory methods
    # --------------------------------------------------------

    @classmethod
    def success_result(
        cls,
        output: Any = None,
        *,
        tool_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
        mission_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        duration_ms: Optional[float] = None,
        attempt: int = 1,
        evidence: Optional[List[Any]] = None,
        confidence: Optional[float] = None,
    ) -> "ToolResult":

        return cls(
            success=True,
            output=output,
            error=None,
            tool_name=tool_name,
            status=ResultStatus.SUCCESS,
            metadata=metadata or {},
            started_at=started_at,
            completed_at=completed_at or _utc_now(),
            duration_ms=duration_ms,
            task_id=task_id,
            mission_id=mission_id,
            agent_id=agent_id,
            attempt=attempt,
            evidence=evidence or [],
            confidence=confidence,
        )

    @classmethod
    def failure(
        cls,
        error: str,
        *,
        tool_name: Optional[str] = None,
        output: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
        mission_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        status: ResultStatus = ResultStatus.FAILED,
        attempt: int = 1,
        evidence: Optional[List[Any]] = None,
        confidence: Optional[float] = None,
    ) -> "ToolResult":

        return cls(
            success=False,
            output=output,
            error=str(error),
            tool_name=tool_name,
            status=status,
            metadata=metadata or {},
            completed_at=_utc_now(),
            task_id=task_id,
            mission_id=mission_id,
            agent_id=agent_id,
            attempt=attempt,
            evidence=evidence or [],
            confidence=confidence,
        )

    @classmethod
    def error_result(
        cls,
        error: str,
        **kwargs: Any,
    ) -> "ToolResult":

        return cls.failure(
            error,
            status=ResultStatus.ERROR,
            **kwargs,
        )

    @classmethod
    def blocked(
        cls,
        reason: str,
        **kwargs: Any,
    ) -> "ToolResult":

        return cls.failure(
            reason,
            status=ResultStatus.BLOCKED,
            **kwargs,
        )

    @classmethod
    def cancelled(
        cls,
        reason: str = "Execution cancelled.",
        **kwargs: Any,
    ) -> "ToolResult":

        return cls.failure(
            reason,
            status=ResultStatus.CANCELLED,
            **kwargs,
        )

    @classmethod
    def timeout(
        cls,
        reason: str = "Execution timed out.",
        **kwargs: Any,
    ) -> "ToolResult":

        return cls.failure(
            reason,
            status=ResultStatus.TIMEOUT,
            **kwargs,
        )


# ============================================================
# Execution Result
# ============================================================

@dataclass
class ExecutionResult:
    """
    Higher-level result representing an entire task execution.

    A task may involve multiple tools, agents, retries, and verification
    steps. ToolResult represents one tool call; ExecutionResult represents
    the overall execution.
    """

    success: bool = False

    output: Any = None

    error: Optional[str] = None

    status: ResultStatus = ResultStatus.SUCCESS

    task_id: Optional[str] = None

    mission_id: Optional[str] = None

    agent_id: Optional[str] = None

    tool_results: List[ToolResult] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)

    started_at: Optional[datetime] = None

    completed_at: Optional[datetime] = None

    duration_ms: Optional[float] = None

    confidence: Optional[float] = None

    verified: bool = False

    verification_notes: Optional[str] = None

    attempts: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(asdict(self))

    def model_dump(self) -> Dict[str, Any]:
        return self.to_dict()

    @property
    def result(self) -> Any:
        return self.output

    @property
    def is_success(self) -> bool:
        return self.success

    @property
    def is_error(self) -> bool:
        return not self.success

    @classmethod
    def success_result(
        cls,
        output: Any = None,
        **kwargs: Any,
    ) -> "ExecutionResult":

        return cls(
            success=True,
            output=output,
            status=ResultStatus.SUCCESS,
            completed_at=_utc_now(),
            **kwargs,
        )

    @classmethod
    def failure(
        cls,
        error: str,
        **kwargs: Any,
    ) -> "ExecutionResult":

        return cls(
            success=False,
            error=str(error),
            status=ResultStatus.FAILED,
            completed_at=_utc_now(),
            **kwargs,
        )


# ============================================================
# Validation Result
# ============================================================

@dataclass
class ValidationResult:
    """
    Result produced by the runtime result validator.
    """

    valid: bool

    reason: Optional[str] = None

    confidence: Optional[float] = None

    checks: Dict[str, Any] = field(default_factory=dict)

    warnings: List[str] = field(default_factory=list)

    errors: List[str] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(asdict(self))

    def model_dump(self) -> Dict[str, Any]:
        return self.to_dict()

    @property
    def success(self) -> bool:
        return self.valid


# ============================================================
# Generic Runtime Result
# ============================================================

@dataclass
class RuntimeResult:
    """
    Generic result envelope used when the caller does not need to
    distinguish between tool-level and execution-level results.
    """

    success: bool

    output: Any = None

    error: Optional[str] = None

    status: ResultStatus = ResultStatus.SUCCESS

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(asdict(self))

    def model_dump(self) -> Dict[str, Any]:
        return self.to_dict()


# ============================================================
# Backwards Compatibility
# ============================================================

# Some modules may import these older names.

Result = RuntimeResult

TaskResult = ExecutionResult


# ============================================================
# Public API
# ============================================================

__all__ = [
    "ResultStatus",
    "ToolResult",
    "ExecutionResult",
    "TaskResult",
    "ValidationResult",
    "RuntimeResult",
    "Result",
]