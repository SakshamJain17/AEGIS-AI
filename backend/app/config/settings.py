"""
AEGIS Configuration
===================

Central configuration for the AEGIS runtime.

AEGIS is designed to run locally first, while keeping the configuration
clean enough to support remote models, databases, and additional services
later.

Environment variables can override the defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

APP_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = APP_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent

DATA_DIR = PROJECT_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
MEMORY_DIR = DATA_DIR / "memory"
TRACE_DIR = DATA_DIR / "traces"

for directory in (
    DATA_DIR,
    LOG_DIR,
    MEMORY_DIR,
    TRACE_DIR,
):
    directory.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return float(value)
    except ValueError:
        return default


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Settings:
    """
    Global AEGIS configuration.

    The object intentionally avoids requiring pydantic so the backend can
    start with a minimal Python environment.
    """

    # -----------------------------------------------------------------------
    # Application
    # -----------------------------------------------------------------------

    app_name: str = field(
        default_factory=lambda: os.getenv(
            "AEGIS_APP_NAME",
            "AEGIS",
        )
    )

    environment: str = field(
        default_factory=lambda: os.getenv(
            "AEGIS_ENV",
            "development",
        )
    )

    debug: bool = field(
        default_factory=lambda: _env_bool(
            "AEGIS_DEBUG",
            True,
        )
    )

    version: str = field(
        default_factory=lambda: os.getenv(
            "AEGIS_VERSION",
            "0.1.0",
        )
    )

    # -----------------------------------------------------------------------
    # Server
    # -----------------------------------------------------------------------

    host: str = field(
        default_factory=lambda: os.getenv(
            "AEGIS_HOST",
            "127.0.0.1",
        )
    )

    port: int = field(
        default_factory=lambda: _env_int(
            "AEGIS_PORT",
            8765,
        )
    )

    websocket_path: str = field(
        default_factory=lambda: os.getenv(
            "AEGIS_WS_PATH",
            "/ws",
        )
    )

    # -----------------------------------------------------------------------
    # Frontend
    # -----------------------------------------------------------------------

    frontend_url: str = field(
        default_factory=lambda: os.getenv(
            "AEGIS_FRONTEND_URL",
            "http://localhost:5173",
        )
    )

    allowed_origins: Tuple[str, ...] = field(
        default_factory=lambda: (
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "null",
        )
    )

    # -----------------------------------------------------------------------
    # Runtime
    # -----------------------------------------------------------------------

    max_concurrent_tasks: int = field(
        default_factory=lambda: _env_int(
            "AEGIS_MAX_CONCURRENT_TASKS",
            4,
        )
    )

    default_task_timeout: float = field(
        default_factory=lambda: _env_float(
            "AEGIS_TASK_TIMEOUT",
            120.0,
        )
    )

    max_task_retries: int = field(
        default_factory=lambda: _env_int(
            "AEGIS_MAX_TASK_RETRIES",
            2,
        )
    )

    enable_parallel_execution: bool = field(
        default_factory=lambda: _env_bool(
            "AEGIS_PARALLEL_EXECUTION",
            True,
        )
    )

    # -----------------------------------------------------------------------
    # Safety
    # -----------------------------------------------------------------------

    default_autonomy_level: str = field(
        default_factory=lambda: os.getenv(
            "AEGIS_AUTONOMY_LEVEL",
            "assist",
        )
    )

    require_approval_for_high_risk: bool = field(
        default_factory=lambda: _env_bool(
            "AEGIS_REQUIRE_HIGH_RISK_APPROVAL",
            True,
        )
    )

    require_approval_for_critical: bool = field(
        default_factory=lambda: _env_bool(
            "AEGIS_REQUIRE_CRITICAL_APPROVAL",
            True,
        )
    )

    emergency_stop_enabled: bool = field(
        default_factory=lambda: _env_bool(
            "AEGIS_EMERGENCY_STOP",
            True,
        )
    )

    # -----------------------------------------------------------------------
    # LLM
    # -----------------------------------------------------------------------

    llm_provider: str = field(
        default_factory=lambda: os.getenv(
            "AEGIS_LLM_PROVIDER",
            "ollama",
        )
    )

    llm_base_url: str = field(
        default_factory=lambda: os.getenv(
            "AEGIS_LLM_BASE_URL",
            "http://127.0.0.1:11434",
        )
    )

    llm_model: str = field(
        default_factory=lambda: os.getenv(
            "AEGIS_LLM_MODEL",
            "qwen3:8b",
        )
    )

    llm_temperature: float = field(
        default_factory=lambda: _env_float(
            "AEGIS_LLM_TEMPERATURE",
            0.35,
        )
    )

    llm_top_p: float = field(
        default_factory=lambda: _env_float(
            "AEGIS_LLM_TOP_P",
            0.90,
        )
    )

    llm_timeout: float = field(
        default_factory=lambda: _env_float(
            "AEGIS_LLM_TIMEOUT",
            120.0,
        )
    )

    # -----------------------------------------------------------------------
    # Context
    # -----------------------------------------------------------------------

    max_context_chars: int = field(
        default_factory=lambda: _env_int(
            "AEGIS_MAX_CONTEXT_CHARS",
            18000,
        )
    )

    max_history_messages: int = field(
        default_factory=lambda: _env_int(
            "AEGIS_MAX_HISTORY_MESSAGES",
            30,
        )
    )

    # -----------------------------------------------------------------------
    # Observability
    # -----------------------------------------------------------------------

    enable_event_logging: bool = field(
        default_factory=lambda: _env_bool(
            "AEGIS_EVENT_LOGGING",
            True,
        )
    )

    enable_trace_recording: bool = field(
        default_factory=lambda: _env_bool(
            "AEGIS_TRACE_RECORDING",
            True,
        )
    )

    # -----------------------------------------------------------------------
    # Paths
    # -----------------------------------------------------------------------

    data_dir: Path = DATA_DIR
    log_dir: Path = LOG_DIR
    memory_dir: Path = MEMORY_DIR
    trace_dir: Path = TRACE_DIR

    # -----------------------------------------------------------------------
    # Derived properties
    # -----------------------------------------------------------------------

    @property
    def backend_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def websocket_url(self) -> str:
        return (
            f"ws://{self.host}:{self.port}"
            f"{self.websocket_path}"
        )

    def ensure_directories(self) -> None:
        """
        Make sure runtime directories exist.
        """

        for directory in (
            self.data_dir,
            self.log_dir,
            self.memory_dir,
            self.trace_dir,
        ):
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )


# ---------------------------------------------------------------------------
# Singleton settings object
# ---------------------------------------------------------------------------

settings = Settings()
settings.ensure_directories()


__all__ = [
    "Settings",
    "settings",
    "APP_DIR",
    "BACKEND_DIR",
    "PROJECT_DIR",
    "DATA_DIR",
    "LOG_DIR",
    "MEMORY_DIR",
    "TRACE_DIR",
]