"""
AEGIS Runtime Container
=======================

Central dependency container and runtime factory for AEGIS.

Supports both the newer:
    AegisContainer / create_container

and the legacy/current application:
    AegisRuntime / create_runtime

This compatibility layer allows the runtime to evolve without breaking
the application entry point or dependent modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.config.settings import Settings
from app.runtime.event_bus import EventBus
from app.runtime.result_validator import ResultValidator
from app.runtime.action_gate import ActionGate
from app.runtime.supervisor import TaskSupervisor


# ============================================================
# AEGIS CONTAINER
# ============================================================

@dataclass
class AegisContainer:
    """
    Dependency-injection container for the AEGIS system.
    """

    settings: Settings
    event_bus: EventBus

    result_validator: Optional[ResultValidator] = None
    action_gate: Optional[ActionGate] = None
    supervisor: Optional[TaskSupervisor] = None

    planner: Optional[Any] = None
    llm: Optional[Any] = None
    context_builder: Optional[Any] = None

    memory: Optional[Any] = None
    verification: Optional[Any] = None

    agent_registry: Optional[Any] = None
    agent_runtime: Optional[Any] = None

    tool_registry: Optional[Any] = None
    tool_executor: Optional[Any] = None

    safety_engine: Optional[Any] = None
    approval_manager: Optional[Any] = None

    runtime: Optional[Any] = None
    service: Optional[Any] = None

    initialized: bool = False

    metadata: dict[str, Any] = field(default_factory=dict)

    # ========================================================
    # Initialization
    # ========================================================

    def initialize_core(self) -> "AegisContainer":
        """
        Initialize the fundamental runtime components.
        """

        if self.event_bus is None:
            self.event_bus = EventBus()

        if self.result_validator is None:
            try:
                self.result_validator = ResultValidator()
            except TypeError:
                self.result_validator = ResultValidator

        if self.action_gate is None:
            self.action_gate = self._build_action_gate()

        if self.supervisor is None:
            self.supervisor = self._build_supervisor()

        self.initialized = True

        return self

    # ========================================================
    # Action Gate
    # ========================================================

    def _build_action_gate(self) -> Optional[ActionGate]:
        """
        Construct ActionGate while remaining compatible with
        different constructor signatures.
        """

        attempts = [
            {
                "settings": self.settings,
                "event_bus": self.event_bus,
            },
            {
                "settings": self.settings,
            },
            {
                "event_bus": self.event_bus,
            },
            {},
        ]

        for kwargs in attempts:
            try:
                return ActionGate(**kwargs)
            except (TypeError, ValueError):
                continue

        return None

    # ========================================================
    # Supervisor
    # ========================================================

    def _build_supervisor(self) -> Optional[TaskSupervisor]:
        """
        Construct TaskSupervisor using the available dependency
        signature.
        """

        attempts = [
            {
                "settings": self.settings,
                "event_bus": self.event_bus,
                "result_validator": self.result_validator,
                "action_gate": self.action_gate,
            },
            {
                "event_bus": self.event_bus,
                "result_validator": self.result_validator,
                "action_gate": self.action_gate,
            },
            {
                "event_bus": self.event_bus,
            },
            {
                "settings": self.settings,
                "event_bus": self.event_bus,
            },
            {},
        ]

        for kwargs in attempts:
            try:
                return TaskSupervisor(**kwargs)
            except (TypeError, ValueError):
                continue

        return None

    # ========================================================
    # Registration
    # ========================================================

    def register(self, name: str, component: Any) -> None:
        """
        Register a dependency dynamically.
        """

        if not name:
            raise ValueError("Component name cannot be empty.")

        setattr(self, name, component)

    def resolve(self, name: str) -> Any:
        """
        Resolve a dependency by attribute name.
        """

        if not hasattr(self, name):
            raise KeyError(
                f"AEGIS component '{name}' does not exist."
            )

        value = getattr(self, name)

        if value is None:
            raise KeyError(
                f"AEGIS component '{name}' is not initialized."
            )

        return value

    # ========================================================
    # Health
    # ========================================================

    def health(self) -> dict[str, Any]:
        """
        Return runtime component health.
        """

        components = {
            "event_bus": self.event_bus,
            "result_validator": self.result_validator,
            "action_gate": self.action_gate,
            "supervisor": self.supervisor,
            "planner": self.planner,
            "llm": self.llm,
            "context_builder": self.context_builder,
            "memory": self.memory,
            "verification": self.verification,
            "agent_registry": self.agent_registry,
            "agent_runtime": self.agent_runtime,
            "tool_registry": self.tool_registry,
            "tool_executor": self.tool_executor,
            "safety_engine": self.safety_engine,
            "approval_manager": self.approval_manager,
            "runtime": self.runtime,
            "service": self.service,
        }

        available = {
            name: value is not None
            for name, value in components.items()
        }

        active = sum(available.values())
        total = len(available)

        return {
            "initialized": self.initialized,
            "healthy": self.initialized,
            "components": available,
            "active_components": active,
            "total_components": total,
            "readiness": active / total if total else 0.0,
        }

    # ========================================================
    # Shutdown
    # ========================================================

    async def shutdown(self) -> None:
        """
        Gracefully shut down runtime components.
        """

        components = [
            self.service,
            self.runtime,
            self.agent_runtime,
            self.tool_executor,
            self.supervisor,
            self.event_bus,
        ]

        for component in components:
            if component is None:
                continue

            shutdown = getattr(component, "shutdown", None)

            if shutdown is None:
                continue

            try:
                result = shutdown()

                if hasattr(result, "__await__"):
                    await result

            except Exception:
                # Shutdown is best-effort.
                continue

        self.initialized = False


# ============================================================
# AEGIS RUNTIME
# ============================================================

class AegisRuntime(AegisContainer):
    """
    Runtime facade used by app.main.

    AegisRuntime extends AegisContainer so both APIs point to the
    same underlying architecture.
    """

    def __init__(
        self,
        settings: Settings,
        event_bus: Optional[EventBus] = None,
        **kwargs: Any,
    ) -> None:

        super().__init__(
            settings=settings,
            event_bus=event_bus or EventBus(),
            **kwargs,
        )

    # --------------------------------------------------------
    # Start
    # --------------------------------------------------------

    async def start(self) -> "AegisRuntime":
        """
        Start the runtime.

        Initializes core dependencies and starts any components
        that expose an async start method.
        """

        self.initialize_core()

        components = [
            self.service,
            self.runtime,
            self.agent_runtime,
            self.tool_executor,
            self.supervisor,
        ]

        for component in components:
            if component is None:
                continue

            start = getattr(component, "start", None)

            if start is None:
                continue

            try:
                result = start()

                if hasattr(result, "__await__"):
                    await result

            except TypeError:
                # Some implementations may expose a synchronous
                # start() with a different contract.
                continue

        self.initialized = True

        return self

    # --------------------------------------------------------
    # Stop
    # --------------------------------------------------------

    async def stop(self) -> None:
        """
        Stop the runtime.
        """

        await self.shutdown()

    # --------------------------------------------------------
    # Execute
    # --------------------------------------------------------

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        """
        Delegate execution to the highest-level runtime component
        available.
        """

        target = self.runtime or self.service or self.supervisor

        if target is None:
            raise RuntimeError(
                "AEGIS runtime has no executable runtime service."
            )

        execute = getattr(target, "execute", None)

        if execute is None:
            raise RuntimeError(
                f"{type(target).__name__} does not expose execute()."
            )

        result = execute(*args, **kwargs)

        if hasattr(result, "__await__"):
            return await result

        return result


# ============================================================
# FACTORIES
# ============================================================

def create_container(
    settings: Settings,
    *,
    event_bus: Optional[EventBus] = None,
) -> AegisContainer:
    """
    Create an initialized AegisContainer.
    """

    container = AegisContainer(
        settings=settings,
        event_bus=event_bus or EventBus(),
    )

    return container.initialize_core()


def create_runtime(
    settings: Settings,
    *,
    event_bus: Optional[EventBus] = None,
    **kwargs: Any,
) -> AegisRuntime:
    """
    Create an initialized AegisRuntime.

    This is the factory expected by app.main.
    """

    runtime = AegisRuntime(
        settings=settings,
        event_bus=event_bus,
        **kwargs,
    )

    runtime.initialize_core()

    return runtime


# ============================================================
# COMPATIBILITY ALIASES
# ============================================================

RuntimeContainer = AegisContainer
Container = AegisContainer


__all__ = [
    "AegisContainer",
    "AegisRuntime",
    "RuntimeContainer",
    "Container",
    "create_container",
    "create_runtime",
]