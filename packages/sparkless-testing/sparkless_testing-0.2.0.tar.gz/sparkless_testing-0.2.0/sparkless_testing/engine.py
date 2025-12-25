"""
Engine detection and configuration for sparkless-testing.

This module provides centralized engine detection and configuration,
allowing tests to work with either sparkless (mock) or PySpark (real) engines.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .protocols import (
    AnalysisExceptionProtocol,
    FunctionsProtocol,
    TypesProtocol,
    WindowProtocol,
)


class EngineType(Enum):
    """Engine type enumeration."""

    MOCK = "mock"
    PYSPARK = "pyspark"
    AUTO = "auto"


@dataclass
class EngineConfig:
    """Configuration for a Spark engine."""

    functions: FunctionsProtocol
    types: TypesProtocol
    analysis_exception: type[BaseException] | AnalysisExceptionProtocol
    window: WindowProtocol | None = None
    desc: Any | None = None
    engine_name: str = "unknown"
    engine_type: EngineType = EngineType.AUTO
    dataframe_cls: Any | None = None
    spark_session_cls: Any | None = None
    column_cls: Any | None = None


# Global engine state (for backward compatibility)
_engine: EngineConfig | None = None

# Thread-local engine state (for parallel test isolation)
_thread_local = threading.local()


def configure_engine(
    *,
    functions: FunctionsProtocol,
    types: TypesProtocol,
    analysis_exception: type[BaseException] | AnalysisExceptionProtocol,
    window: WindowProtocol | None = None,
    desc: Any | None = None,
    engine_name: str = "unknown",
    engine_type: EngineType = EngineType.AUTO,
    dataframe_cls: Any | None = None,
    spark_session_cls: Any | None = None,
    column_cls: Any | None = None,
) -> None:
    """
    Inject engine components.

    Sets both thread-local and global engine state for backward compatibility.
    Thread-local state takes precedence in get_engine() for parallel test isolation.

    **Thread-Local vs Global State:**

    - **Thread-local state**: Used for parallel test execution (pytest-xdist).
      Each thread maintains its own engine configuration, ensuring test isolation.
      This is checked first by get_engine().

    - **Global state**: Used for backward compatibility and single-threaded execution.
      Falls back to this if thread-local state is not set.

    When configure_engine() is called, it sets BOTH thread-local and global state.
    This ensures compatibility with both parallel and sequential test execution.

    Args:
        functions: Functions module (F) from the engine
        types: Types module from the engine
        analysis_exception: AnalysisException class from the engine
        window: Window class from the engine (optional)
        desc: desc function from the engine (optional)
        engine_name: Name of the engine (e.g., "mock", "pyspark")
        engine_type: EngineType enum value
        dataframe_cls: DataFrame class from the engine (optional)
        spark_session_cls: SparkSession class from the engine (optional)
        column_cls: Column class from the engine (optional)
    """
    global _engine
    engine_config = EngineConfig(
        functions=functions,
        types=types,
        analysis_exception=analysis_exception,
        window=window,
        desc=desc,
        engine_name=engine_name,
        engine_type=engine_type,
        dataframe_cls=dataframe_cls,
        spark_session_cls=spark_session_cls,
        column_cls=column_cls,
    )

    # Set global state (for backward compatibility)
    _engine = engine_config

    # Set thread-local state (for parallel test isolation)
    _thread_local.engine = engine_config


def get_engine() -> EngineConfig:
    """
    Get the current engine config, raising if not configured.

    **Priority Order:**
    1. Thread-local state (checked first for parallel test isolation)
    2. Global state (fallback for backward compatibility)

    This ensures that in parallel test execution, each thread uses its own
    engine configuration, while single-threaded execution uses the global state.

    Returns:
        EngineConfig instance

    Raises:
        RuntimeError: If engine is not configured in either thread-local or global state
    """
    # Try thread-local first (for parallel test isolation)
    if hasattr(_thread_local, "engine") and _thread_local.engine is not None:
        return _thread_local.engine  # type: ignore[no-any-return]

    # Fallback to global state (for backward compatibility)
    if _engine is None:
        raise RuntimeError(
            "Engine not configured. Call configure_engine(...) before using sparkless-testing."
        )
    return _engine


def reset_engine_state() -> None:
    """
    Reset thread-local engine state.

    This is useful for test isolation - clears the thread-local engine
    so the next get_engine() call will use global state or raise an error.

    **Note:** This only resets thread-local state, not global state.
    After calling this, get_engine() will fall back to global state if available,
    or raise RuntimeError if global state is also not configured.
    """
    if hasattr(_thread_local, "engine"):
        delattr(_thread_local, "engine")


def detect_available_engines() -> set[EngineType]:
    """
    Detect which engines are available (installed).

    Returns:
        Set of available EngineType values
    """
    available: set[EngineType] = set()

    # Check for sparkless (mock)
    try:
        import sparkless  # noqa: F401

        available.add(EngineType.MOCK)
    except ImportError:
        pass

    # Check for PySpark
    try:
        import pyspark  # noqa: F401

        available.add(EngineType.PYSPARK)
    except ImportError:
        pass

    return available


def auto_configure_engine(
    preferred_engine: EngineType | None = None,
) -> EngineConfig:
    """
    Automatically configure engine based on availability and preference.

    Args:
        preferred_engine: Preferred engine type (defaults to MOCK if available)

    Returns:
        EngineConfig instance

    Raises:
        RuntimeError: If no engines are available
    """
    available = detect_available_engines()

    if not available:
        raise RuntimeError("No Spark engines available. Install either 'sparkless' or 'pyspark'.")

    # Determine which engine to use
    if preferred_engine is None:
        # Default preference: MOCK > PYSPARK
        if EngineType.MOCK in available:
            preferred_engine = EngineType.MOCK
        elif EngineType.PYSPARK in available:
            preferred_engine = EngineType.PYSPARK
        else:
            # Use first available
            preferred_engine = next(iter(available))

    if preferred_engine not in available:
        raise RuntimeError(
            f"Preferred engine '{preferred_engine.value}' is not available. "
            f"Available engines: {[e.value for e in available]}"
        )

    # Configure based on engine type
    if preferred_engine == EngineType.MOCK:
        return _configure_mock_engine()
    elif preferred_engine == EngineType.PYSPARK:
        return _configure_pyspark_engine()
    else:
        raise RuntimeError(f"Unknown engine type: {preferred_engine}")


def _configure_mock_engine() -> EngineConfig:
    """Configure sparkless (mock) engine."""
    try:
        from sparkless import AnalysisException as MockAnalysisException
        from sparkless import Column as MockColumn
        from sparkless import DataFrame as MockDataFrame
        from sparkless import SparkSession as MockSparkSession
        from sparkless import Window as MockWindow
        from sparkless import functions as mock_functions
        from sparkless import spark_types as mock_types
        from sparkless.functions import desc as mock_desc
    except ImportError as e:
        raise RuntimeError(
            "sparkless is not installed. Install it with: pip install sparkless"
        ) from e

    configure_engine(
        functions=mock_functions,
        types=mock_types,
        analysis_exception=MockAnalysisException,
        window=MockWindow,
        desc=mock_desc,
        engine_name="mock",
        engine_type=EngineType.MOCK,
        dataframe_cls=MockDataFrame,
        spark_session_cls=MockSparkSession,
        column_cls=MockColumn,
    )

    return get_engine()


def _configure_pyspark_engine() -> EngineConfig:
    """Configure PySpark engine."""
    try:
        from pyspark.sql import Column as PySparkColumn
        from pyspark.sql import DataFrame as PySparkDataFrame
        from pyspark.sql import SparkSession as PySparkSparkSession
        from pyspark.sql import functions as pyspark_functions
        from pyspark.sql import types as pyspark_types
        from pyspark.sql.functions import desc as pyspark_desc
        from pyspark.sql.utils import AnalysisException as PySparkAnalysisException
        from pyspark.sql.window import Window as PySparkWindow
    except ImportError as e:
        raise RuntimeError("PySpark is not installed. Install it with: pip install pyspark") from e

    configure_engine(
        functions=pyspark_functions,
        types=pyspark_types,
        analysis_exception=PySparkAnalysisException,
        window=PySparkWindow,
        desc=pyspark_desc,
        engine_name="pyspark",
        engine_type=EngineType.PYSPARK,
        dataframe_cls=PySparkDataFrame,
        spark_session_cls=PySparkSparkSession,
        column_cls=PySparkColumn,
    )

    return get_engine()


__all__ = [
    "EngineType",
    "EngineConfig",
    "configure_engine",
    "get_engine",
    "reset_engine_state",
    "detect_available_engines",
    "auto_configure_engine",
]
