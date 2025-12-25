"""
sparkless-testing - Easy testing with sparkless or PySpark.

A Python package that simplifies running tests with either sparkless (mock)
or PySpark (real) engines on demand.
"""

__version__ = "0.1.0"
__author__ = "Odos Matthews"
__email__ = "odosmatthews@gmail.com"

# Core engine configuration
from .engine import (
    EngineConfig,
    EngineType,
    auto_configure_engine,
    configure_engine,
    detect_available_engines,
    get_engine,
    reset_engine_state,
)

# Protocols (for type checking)
from .protocols import (
    AnalysisExceptionProtocol,
    ColumnProtocol,
    DataFrameProtocol,
    FunctionsProtocol,
    SparkSessionProtocol,
    TypesProtocol,
    WindowProtocol,
)

# Session factory
from .session import (
    SessionConfig,
    create_mock_session,
    create_pyspark_session,
    create_session,
    stop_all_sessions,
)

# Test utilities
from .utils import (
    create_test_dataframe,
    detect_spark_type,
    get_app_name_prefix,
    get_spark_mode,
    get_warehouse_dir,
    is_dataframe_like,
)

__all__ = [
    # Package metadata
    "__version__",
    "__author__",
    "__email__",
    # Engine configuration
    "EngineType",
    "EngineConfig",
    "configure_engine",
    "get_engine",
    "reset_engine_state",
    "detect_available_engines",
    "auto_configure_engine",
    # Session factory
    "SessionConfig",
    "create_mock_session",
    "create_pyspark_session",
    "create_session",
    "stop_all_sessions",
    # Test utilities
    "detect_spark_type",
    "is_dataframe_like",
    "create_test_dataframe",
    "get_spark_mode",
    "get_warehouse_dir",
    "get_app_name_prefix",
    # Protocols
    "ColumnProtocol",
    "DataFrameProtocol",
    "FunctionsProtocol",
    "TypesProtocol",
    "WindowProtocol",
    "AnalysisExceptionProtocol",
    "SparkSessionProtocol",
]
