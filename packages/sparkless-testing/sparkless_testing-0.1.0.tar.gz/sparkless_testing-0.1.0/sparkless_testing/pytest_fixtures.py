"""
Pytest fixtures for sparkless-testing.

This module provides pytest fixtures for easy test integration with both
sparkless (mock) and PySpark (real) engines.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Generator
from typing import Any

import pytest

from .engine import EngineType, auto_configure_engine, get_engine
from .session import SessionConfig, create_mock_session, create_pyspark_session, create_session
from .utils import get_spark_mode


def _get_engine_type_from_marker(request: pytest.FixtureRequest) -> EngineType | None:
    """Get engine type from pytest marker if present."""
    marker = request.node.get_closest_marker("spark_engine")
    if marker:
        engine_arg = marker.args[0] if marker.args else None
        if engine_arg:
            engine_str = str(engine_arg).lower()
            if engine_str == "mock":
                return EngineType.MOCK
            elif engine_str == "pyspark":
                return EngineType.PYSPARK
    return None


def _determine_engine_type(request: pytest.FixtureRequest) -> EngineType:
    """Determine which engine type to use based on markers and environment."""
    # Check pytest marker first
    marker_engine = _get_engine_type_from_marker(request)
    if marker_engine:
        return marker_engine

    # Check environment variable
    spark_mode = get_spark_mode()
    if spark_mode == "mock":
        return EngineType.MOCK
    elif spark_mode == "pyspark":
        return EngineType.PYSPARK
    else:
        # Auto-detect
        return EngineType.AUTO


@pytest.fixture(scope="function")  # type: ignore[untyped-decorator]
def spark_session(request: pytest.FixtureRequest) -> Generator[Any, None, None]:
    """
    Main fixture that provides appropriate SparkSession based on configuration.

    This fixture respects:
    - `SPARK_MODE` environment variable: `mock`, `pyspark`, or `auto` (default)
    - `@pytest.mark.spark_engine("mock")` or `@pytest.mark.spark_engine("pyspark")` markers
    - Auto-detection if only one engine is available
    - Parametrization via `@pytest.mark.parametrize_engines`

    Example:
        def test_my_function(spark_session):
            df = spark_session.createDataFrame([{"id": 1}])
            assert df.count() == 1
    """
    # Check if parametrized (for parametrize_engines support)
    param = getattr(request, "param", None)
    if param is not None:
        # Use the parametrized engine type
        engine_type = param
    else:
        # Determine engine type from markers/environment
        engine_type = _determine_engine_type(request)

    # Auto-configure engine if not already configured
    try:
        get_engine()
    except RuntimeError:
        if engine_type == EngineType.AUTO:
            auto_configure_engine()
        else:
            auto_configure_engine(engine_type)

    # Create session with Delta Lake disabled for parallel testing compatibility
    # Use process ID and UUID for unique session names (pytest-xdist uses separate processes)
    unique_id = f"{os.getpid()}-{uuid.uuid4().hex[:8]}"
    config = SessionConfig(app_name=f"test-{unique_id}", enable_delta=False)
    spark = create_session(engine_type=engine_type, config=config)

    yield spark

    # Cleanup
    try:
        spark.stop()
    except Exception:
        pass


@pytest.fixture(scope="function")  # type: ignore[untyped-decorator]
def mock_spark_session() -> Generator[Any, None, None]:
    """
    Fixture that explicitly uses sparkless (mock) engine.

    Example:
        def test_mock_only(mock_spark_session):
            # Only runs with sparkless
            df = mock_spark_session.createDataFrame([{"id": 1}])
            assert df.count() == 1
    """
    # Auto-configure mock engine if not already configured
    try:
        get_engine()
    except RuntimeError:
        auto_configure_engine(EngineType.MOCK)

    spark = create_mock_session()

    yield spark

    # Cleanup
    try:
        spark.stop()
    except Exception:
        pass


@pytest.fixture(scope="function")  # type: ignore[untyped-decorator]
def pyspark_session() -> Generator[Any, None, None]:
    """
    Fixture that explicitly uses PySpark (real) engine.

    Example:
        def test_pyspark_only(pyspark_session):
            # Only runs with PySpark
            df = pyspark_session.createDataFrame([{"id": 1}])
            assert df.count() == 1
    """
    # Auto-configure PySpark engine if not already configured
    try:
        get_engine()
    except RuntimeError:
        auto_configure_engine(EngineType.PYSPARK)

    # Disable Delta Lake for parallel testing compatibility
    unique_id = f"{os.getpid()}-{uuid.uuid4().hex[:8]}"
    config = SessionConfig(app_name=f"test-{unique_id}", enable_delta=False)
    spark = create_pyspark_session(config=config)

    yield spark

    # Cleanup
    try:
        spark.stop()
    except Exception:
        pass


@pytest.fixture(scope="function")  # type: ignore[untyped-decorator]
def spark_functions() -> Any:
    """
    Fixture that provides the functions module (F) for the current engine.

    **Important**: For PySpark, functions like `F.col()` require an active SparkContext.
    Always use this fixture together with `spark_session` to ensure the session is active.

    Example:
        def test_with_functions(spark_session, spark_functions):
            F = spark_functions
            df = spark_session.createDataFrame([{"name": "Alice"}])
            result = df.select(F.upper(F.col("name"))).collect()
            assert result[0][0] == "ALICE"

    Note:
        If you use this fixture without `spark_session`, PySpark functions may fail
        with an AssertionError if no SparkContext is active. Always use both fixtures together.
    """
    try:
        return get_engine().functions
    except RuntimeError:
        # Auto-configure if not configured
        auto_configure_engine()
        return get_engine().functions


@pytest.fixture(scope="function")  # type: ignore[untyped-decorator]
def spark_types() -> Any:
    """
    Fixture that provides the types module for the current engine.

    Example:
        def test_with_types(spark_session, spark_types):
            from spark_types import StructType, StructField, StringType
            schema = StructType([StructField("name", StringType())])
            df = spark_session.createDataFrame([{"name": "Alice"}], schema)
    """
    try:
        return get_engine().types
    except RuntimeError:
        # Auto-configure if not configured
        auto_configure_engine()
        return get_engine().types


@pytest.fixture(scope="function")  # type: ignore[untyped-decorator]
def spark_engine_type() -> str:
    """
    Fixture that provides the current engine type as a string.

    Returns:
        'mock' or 'pyspark'

    Example:
        def test_engine_type(spark_engine_type):
            assert spark_engine_type in ("mock", "pyspark")
    """
    try:
        return get_engine().engine_name
    except RuntimeError:
        # Auto-configure if not configured
        auto_configure_engine()
        return get_engine().engine_name


__all__ = [
    "spark_session",
    "mock_spark_session",
    "pyspark_session",
    "spark_functions",
    "spark_types",
    "spark_engine_type",
]
