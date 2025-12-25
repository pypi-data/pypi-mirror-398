"""
Session factory for creating SparkSession instances.

This module provides functions to create SparkSession instances for both
sparkless (mock) and PySpark (real) engines with proper configuration.
"""

from __future__ import annotations

import os
import uuid
import warnings
from dataclasses import dataclass
from typing import Any

from .engine import EngineType, auto_configure_engine, get_engine
from .utils import get_app_name_prefix, get_warehouse_dir


@dataclass
class SessionConfig:
    """Configuration for SparkSession creation."""

    app_name: str
    warehouse_dir: str | None = None
    enable_delta: bool = True
    enable_ui: bool = False
    shuffle_partitions: int = 1
    parallelism: int = 1
    adaptive_enabled: bool = False


def create_mock_session(
    app_name: str | None = None,
    config: SessionConfig | None = None,
) -> Any:
    """
    Create a sparkless (mock) SparkSession.

    Args:
        app_name: Application name (defaults to auto-generated)
        config: Optional SessionConfig (currently unused for mock sessions)

    Returns:
        SparkSession instance from sparkless
    """
    try:
        from sparkless import SparkSession
    except ImportError as e:
        raise RuntimeError(
            "sparkless is not installed. Install it with: pip install sparkless"
        ) from e

    # Auto-configure engine if not already configured
    try:
        get_engine()
    except RuntimeError:
        auto_configure_engine(EngineType.MOCK)

    # Generate app name if not provided
    if app_name is None:
        app_name = f"{get_app_name_prefix()}-mock-{os.getpid()}"

    # Create mock Spark session
    spark = SparkSession(app_name)

    # Create test schema if possible
    try:
        spark.sql("CREATE SCHEMA IF NOT EXISTS test_schema")
    except Exception:
        pass  # Ignore schema creation errors

    return spark


def create_pyspark_session(
    app_name: str | None = None,
    config: SessionConfig | None = None,
) -> Any:
    """
    Create a PySpark SparkSession with optional Delta Lake support.

    Args:
        app_name: Application name (defaults to auto-generated)
        config: Optional SessionConfig for session customization

    Returns:
        SparkSession instance from PySpark
    """
    try:
        from pyspark.sql import SparkSession
    except ImportError as e:
        raise RuntimeError("PySpark is not installed. Install it with: pip install pyspark") from e

    # Auto-configure engine if not already configured
    try:
        get_engine()
    except RuntimeError:
        auto_configure_engine(EngineType.PYSPARK)

    # Skip environment variable manipulation for parallel testing compatibility
    # PySpark will use the current Python interpreter by default
    # Setting these can cause contention in parallel execution

    # Get worker ID for concurrent testing isolation (pytest-xdist)
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "gw0")

    # Generate app name if not provided
    # Priority: explicit app_name parameter > config.app_name > auto-generated
    if app_name is None:
        if config and config.app_name:
            app_name = config.app_name
        else:
            app_name = f"{get_app_name_prefix()}-pyspark-{worker_id}-{uuid.uuid4().hex[:8]}"

    # Determine warehouse directory with unique identifier per process/test
    warehouse_dir = None
    if config and config.warehouse_dir:
        warehouse_dir = config.warehouse_dir
    else:
        # Add unique identifier to avoid collisions across parallel workers
        unique_id = uuid.uuid4().hex[:8]
        base_dir = get_warehouse_dir() or f"/tmp/spark-warehouse-{os.getpid()}-{unique_id}"
        warehouse_dir = base_dir

    # Build Spark session builder - use local[1] to ensure single-threaded execution
    # This prevents resource contention in parallel test execution
    builder = (
        SparkSession.builder.appName(app_name)
        .master("local[1]")  # Explicitly use 1 thread, not local[*]
        .config("spark.sql.warehouse.dir", warehouse_dir)
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.executor.cores", "1")  # Ensure only 1 core per executor
        .config("spark.executor.instances", "1")  # Ensure only 1 executor instance
    )

    # Only add optional configs if explicitly provided
    if config:
        if config.enable_ui:
            builder = builder.config("spark.ui.enabled", "true")
        if config.shuffle_partitions != 1:
            builder = builder.config("spark.sql.shuffle.partitions", str(config.shuffle_partitions))
        if config.parallelism != 1:
            builder = builder.config("spark.default.parallelism", str(config.parallelism))
        if config.adaptive_enabled:
            builder = builder.config("spark.sql.adaptive.enabled", "true")

    # Add Delta Lake support if enabled and available
    enable_delta = config.enable_delta if config else True
    if enable_delta:
        try:
            from delta import configure_spark_with_delta_pip

            builder = builder.config(
                "spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension"
            ).config(
                "spark.sql.catalog.spark_catalog",
                "org.apache.spark.sql.delta.catalog.DeltaCatalog",
            )
            builder = configure_spark_with_delta_pip(builder)
        except ImportError:
            # Delta Lake not available, continue without it
            pass

    # Stop any existing session in this process first to ensure clean state
    # This prevents conflicts when multiple tests run in the same process
    try:
        existing = SparkSession.getActiveSession()
        if existing is not None:
            existing.stop()
    except Exception:
        pass

    # Use getOrCreate() with unique app name - PySpark will create a new session
    # for each unique app name, ensuring test isolation
    spark = builder.getOrCreate()

    # Minimal post-creation setup - avoid operations that could block
    # Set log level to WARN to reduce noise (non-blocking)
    try:
        if hasattr(spark, "sparkContext") and spark.sparkContext:
            spark.sparkContext.setLogLevel("WARN")
    except Exception:
        # Ignore errors - log level setting is not critical
        pass

    # No environment variable restoration needed since we're not modifying them

    return spark


def create_session(
    engine_type: EngineType | None = None,
    app_name: str | None = None,
    config: SessionConfig | None = None,
) -> Any:
    """
    Factory function that creates appropriate session based on engine type.

    Args:
        engine_type: Engine type to use (defaults to auto-detect)
        app_name: Application name (defaults to auto-generated)
        config: Optional SessionConfig for session customization

    Returns:
        SparkSession instance
    """
    # Auto-detect engine type if not specified
    if engine_type is None or engine_type == EngineType.AUTO:
        from .engine import detect_available_engines

        available = detect_available_engines()
        if EngineType.MOCK in available:
            engine_type = EngineType.MOCK
        elif EngineType.PYSPARK in available:
            engine_type = EngineType.PYSPARK
        else:
            raise RuntimeError(
                "No Spark engines available. Install either 'sparkless' or 'pyspark'."
            )

    # Create session based on engine type
    if engine_type == EngineType.MOCK:
        return create_mock_session(app_name, config)
    elif engine_type == EngineType.PYSPARK:
        return create_pyspark_session(app_name, config)
    else:
        raise ValueError(f"Unknown engine type: {engine_type}")


def stop_all_sessions() -> None:
    """
    Stop all active Spark sessions.

    This is a cleanup utility for test teardown.
    """
    # Try to stop PySpark sessions
    try:
        from pyspark.sql import SparkSession

        active_session = SparkSession.getActiveSession()
        if active_session:
            active_session.stop()
    except Exception as e:
        warnings.warn(
            f"Failed to stop existing PySpark session during cleanup: {e}",
            UserWarning,
            stacklevel=2,
        )

    # Note: sparkless sessions don't need explicit stopping,
    # but we could add cleanup here if needed


__all__ = [
    "SessionConfig",
    "create_mock_session",
    "create_pyspark_session",
    "create_session",
    "stop_all_sessions",
]
