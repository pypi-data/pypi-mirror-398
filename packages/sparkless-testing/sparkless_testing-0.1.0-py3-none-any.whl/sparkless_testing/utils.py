"""
Test utilities for sparkless-testing.

Helper functions for common test patterns and compatibility handling.
"""

from __future__ import annotations

import os
from typing import Any

from .engine import get_engine


def detect_spark_type(spark: Any) -> str:
    """
    Detect if spark session is PySpark or mock.

    Args:
        spark: SparkSession instance to check

    Returns:
        'pyspark', 'mock', or 'unknown'
    """
    # Fast-path: PySpark sessions have a JVM bridge
    if hasattr(spark, "sparkContext") and hasattr(spark.sparkContext, "_jsc"):
        return "pyspark"

    try:
        spark_module = type(spark).__module__
        if "pyspark" in spark_module:
            return "pyspark"
        # Detect sparkless/mock sessions by module path
        if "sparkless" in spark_module or "mock" in spark_module:
            return "mock"
    except Exception:
        pass

    # Fallback to engine name if available
    try:
        engine_config = get_engine()
        engine_name = engine_config.engine_name
        if engine_name in {"mock", "sparkless"}:
            return "mock"
        if engine_name == "pyspark":
            return "pyspark"
    except Exception:
        pass

    return "unknown"


def is_dataframe_like(obj: Any) -> bool:
    """
    Check if object is DataFrame-like using structural typing.

    Checks for essential DataFrame methods: count, columns (property), filter.

    Args:
        obj: Object to check

    Returns:
        True if object has DataFrame-like interface, False otherwise
    """
    # columns is typically a property (not callable), count and filter are methods
    return (
        hasattr(obj, "count")
        and hasattr(obj, "columns")
        and hasattr(obj, "filter")
        and callable(getattr(obj, "count", None))
        and callable(getattr(obj, "filter", None))
    )


def create_test_dataframe(
    spark: Any,
    data: Any,
    schema: Any | None = None,
    **kwargs: Any,
) -> Any:
    """
    High-level helper for creating test DataFrames.

    Provides a consistent API for creating DataFrames in tests.
    Handles PySpark 3.5+ schema argument position differences.

    Args:
        spark: SparkSession instance (PySpark or mock-spark)
        data: Data to create DataFrame from (list of tuples, list of dicts, etc.)
        schema: Schema definition (list of strings, StructType, or None)
        **kwargs: Additional arguments passed to createDataFrame

    Returns:
        DataFrame instance

    Raises:
        TypeError: If spark is not a valid SparkSession
        ValueError: If data is invalid or schema is incompatible
        RuntimeError: If DataFrame creation fails after all retry attempts
    """
    if not hasattr(spark, "createDataFrame"):
        raise TypeError(
            f"spark parameter must have a createDataFrame method, got {type(spark).__name__}"
        )

    create_df = spark.createDataFrame
    last_error: Exception | None = None

    # Call createDataFrame method
    # Handle PySpark 3.5+ schema argument issues
    if schema is None:
        try:
            return create_df(data, **kwargs)
        except (TypeError, ValueError) as e:
            raise ValueError(
                f"Failed to create DataFrame from data: {e}. Data type: {type(data).__name__}"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Unexpected error creating DataFrame: {e}") from e
    else:
        # Try different calling patterns to handle PySpark version differences
        # Pattern 1: Positional schema (PySpark 3.5+)
        try:
            if kwargs:
                return create_df(data, schema, **kwargs)
            else:
                return create_df(data, schema)
        except (TypeError, ValueError) as e:
            error_str = str(e)
            last_error = e

            # Check if this is the PySpark StructType error (known PySpark 3.5+ bug)
            if "NOT_LIST_OR_NONE_OR_STRUCT" in error_str:
                # Try without kwargs
                try:
                    return create_df(data, schema)
                except (TypeError, ValueError) as e2:
                    last_error = e2
                    # Last resort: try with schema as keyword
                    try:
                        return create_df(data, schema=schema, **kwargs)
                    except (TypeError, ValueError) as e3:
                        last_error = e3
                        # Final fallback: try without kwargs and keyword schema
                        try:
                            return create_df(data, schema=schema)
                        except (TypeError, ValueError) as e4:
                            last_error = e4
            else:
                # For other errors, try keyword argument (older PySpark)
                try:
                    return create_df(data, schema=schema, **kwargs)
                except (TypeError, ValueError) as e2:
                    last_error = e2
                    # Final fallback: try without kwargs and keyword schema
                    try:
                        return create_df(data, schema=schema)
                    except (TypeError, ValueError) as e3:
                        last_error = e3

        # If we get here, all attempts failed
        if last_error:
            raise ValueError(
                f"Failed to create DataFrame with schema after multiple attempts. "
                f"Last error: {last_error}. "
                f"Data type: {type(data).__name__}, Schema type: {type(schema).__name__}"
            ) from last_error
        else:
            raise RuntimeError("Failed to create DataFrame: unknown error occurred")


def get_spark_mode() -> str:
    """
    Get SPARK_MODE from environment variable.

    Returns:
        'mock', 'pyspark', or 'auto' (default)
    """
    return os.environ.get("SPARK_MODE", "auto").lower()


def get_warehouse_dir() -> str | None:
    """
    Get custom warehouse directory from environment variable.

    Returns:
        Warehouse directory path or None
    """
    return os.environ.get("SPARK_TEST_WAREHOUSE_DIR")


def get_app_name_prefix() -> str:
    """
    Get app name prefix from environment variable.

    Returns:
        App name prefix (default: 'sparkless-testing')
    """
    return os.environ.get("SPARK_TEST_APP_NAME", "sparkless-testing")


__all__ = [
    "detect_spark_type",
    "is_dataframe_like",
    "create_test_dataframe",
    "get_spark_mode",
    "get_warehouse_dir",
    "get_app_name_prefix",
]
