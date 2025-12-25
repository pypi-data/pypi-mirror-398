"""
Auto-configure pytest fixtures for sparkless-testing.

This module automatically registers pytest fixtures and hooks when imported.
Import this in your conftest.py or test files to enable sparkless-testing fixtures.
"""

from __future__ import annotations

# Import parametrization hooks
from .parametrize import (  # noqa: F401
    both_engines,
    parametrize_engines,
    pytest_configure,
    pytest_generate_tests,
)

# Import fixtures to register them
from .pytest_fixtures import (  # noqa: F401
    mock_spark_session,
    pyspark_session,
    spark_engine_type,
    spark_functions,
    spark_session,
    spark_types,
)

__all__ = [
    "spark_session",
    "mock_spark_session",
    "pyspark_session",
    "spark_functions",
    "spark_types",
    "spark_engine_type",
    "both_engines",
    "parametrize_engines",
    "pytest_configure",
    "pytest_generate_tests",
]
