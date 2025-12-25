"""
Parametrization support for running tests with both engines.

This module provides utilities for running tests with both sparkless (mock)
and PySpark (real) engines automatically.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Generator
from typing import Any

import pytest

from .engine import EngineType, auto_configure_engine, detect_available_engines
from .session import SessionConfig, create_session


def pytest_configure(config: Any) -> None:
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "spark_engine(engine): Mark test to use specific engine (mock or pyspark)",
    )
    config.addinivalue_line(
        "markers",
        "parametrize_engines: Run test with both available engines",
    )


@pytest.fixture(scope="function")  # type: ignore[untyped-decorator]
def both_engines(request: pytest.FixtureRequest) -> Generator[tuple[Any, EngineType], None, None]:
    """
    Fixture that yields both available engines via parametrization.

    This fixture is automatically parametrized to run with both engines.
    The test will be called twice - once with mock engine, once with PySpark.

    Example:
        def test_both_engines(both_engines):
            spark, engine_type = both_engines
            df = spark.createDataFrame([{"id": 1}])
            assert df.count() == 1
    """
    # Get the parametrized engine type
    engine_type = getattr(request, "param", None)
    if engine_type is None:
        # If not parametrized, check availability and use default
        available = detect_available_engines()
        if EngineType.MOCK not in available or EngineType.PYSPARK not in available:
            pytest.skip(f"Both engines not available. Available: {[e.value for e in available]}")
        # Default to MOCK if not parametrized
        engine_type = EngineType.MOCK

    # Configure and create session for the specified engine
    unique_id = f"{os.getpid()}-{uuid.uuid4().hex[:8]}"
    config = SessionConfig(app_name=f"test-{unique_id}")
    auto_configure_engine(engine_type)
    spark = create_session(engine_type=engine_type, config=config)

    yield spark, engine_type

    # Cleanup
    try:
        spark.stop()
    except Exception:
        pass


# Auto-parametrize both_engines fixture if both engines are available
def pytest_generate_tests(metafunc: Any) -> None:
    """Generate test parameters for parametrize_engines marker and both_engines fixture."""
    # Handle both_engines fixture parametrization
    if "both_engines" in metafunc.fixturenames:
        available = detect_available_engines()
        if EngineType.MOCK in available and EngineType.PYSPARK in available:
            # Parametrize the both_engines fixture
            metafunc.parametrize(
                "both_engines",
                [EngineType.MOCK, EngineType.PYSPARK],
                ids=["mock", "pyspark"],
                indirect=True,
            )
        elif EngineType.MOCK in available or EngineType.PYSPARK in available:
            # Only one engine available, parametrize with just that one
            available_list = list(available)
            metafunc.parametrize(
                "both_engines",
                available_list,
                ids=[e.value for e in available_list],
                indirect=True,
            )

    # Handle spark_session fixture parametrization for parametrize_engines marker
    if "spark_session" in metafunc.fixturenames:
        # Check if test has parametrize_engines marker
        marker = metafunc.definition.get_closest_marker("parametrize_engines")
        if marker:
            available = detect_available_engines()

            if EngineType.MOCK in available and EngineType.PYSPARK in available:
                # Parametrize the spark_session fixture
                metafunc.parametrize(
                    "spark_session",
                    [EngineType.MOCK, EngineType.PYSPARK],
                    ids=["mock", "pyspark"],
                    indirect=True,
                )


def parametrize_engines(*args: Any, **kwargs: Any) -> Any:
    """
    Decorator to parametrize a test to run with both engines.

    This is a convenience decorator that uses pytest.mark.parametrize
    to run the test with both mock and pyspark engines.

    Example:
        @parametrize_engines
        def test_my_function(spark_session):
            df = spark_session.createDataFrame([{"id": 1}])
            assert df.count() == 1

    Note: This decorator requires both engines to be available.
    """
    available = detect_available_engines()

    if EngineType.MOCK not in available or EngineType.PYSPARK not in available:
        # Skip parametrization if both engines not available
        return pytest.mark.skip(
            f"Both engines not available. Available: {[e.value for e in available]}"
        )(*args, **kwargs)

    # Create parametrize marker
    return pytest.mark.parametrize(
        "engine_type",
        [EngineType.MOCK, EngineType.PYSPARK],
        ids=["mock", "pyspark"],
    )(*args, **kwargs)


__all__ = [
    "pytest_configure",
    "both_engines",
    "parametrize_engines",
    "pytest_generate_tests",
]
