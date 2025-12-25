"""DuckDB benchmark plugin."""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ...config import BenchmarkConfig
from .. import BenchmarkPlugin

logger = logging.getLogger("pds_benchmark")


class DuckDBPlugin(BenchmarkPlugin):
    """DuckDB benchmark plugin."""

    def __init__(self):
        self._config: BenchmarkConfig | None = None
        self._connection: Any = None

    @property
    def name(self) -> str:
        return "duckdb"

    @property
    def version(self) -> str | None:
        try:
            import duckdb

            return duckdb.__version__
        except ImportError:
            return None

    def setup(self, config: BenchmarkConfig) -> None:
        """Initialize DuckDB connection."""
        self._config = config
        self._setup_connection()

    def _setup_connection(self) -> None:
        """Setup DuckDB connection."""
        try:
            import duckdb

            self._connection = duckdb.connect()

            # Set up any DuckDB-specific configuration
            if self._config and self._config.extra_config:
                threads = self._config.extra_config.get("THREAD_COUNT")
                if threads:
                    self._connection.execute(f"SET threads TO {threads}")

                memory_limit = self._config.extra_config.get("MEMORY_LIMIT")
                if memory_limit:
                    self._connection.execute(f"SET memory_limit = '{memory_limit}'")

        except ImportError as e:
            raise ImportError(
                "DuckDB is not installed. Please install with: pip install duckdb"
            ) from e

    def _register_tables(self, file_paths: dict[str, str]) -> None:
        """Register all parquet files as tables in DuckDB for TPC-DS queries."""
        for table_name, file_path in file_paths.items():
            create_view_sql = (
                f"CREATE OR REPLACE VIEW {table_name} "
                f"AS SELECT * FROM parquet_scan('{file_path}')"
            )
            self._connection.execute(create_view_sql)

    def load_table(self, file_path: str) -> str:
        """For DuckDB, return appropriate reference based on benchmark."""
        if self._config and self._config.benchmark == "tpcds":
            # For TPC-DS, return table name (tables will be registered)
            return Path(file_path).stem
        else:
            # For TPC-H, use direct parquet_scan
            return f"parquet_scan('{file_path}')"

    def execute_query(self, query_func: Callable, data: dict[str, str]) -> Any:
        """Execute DuckDB query."""
        if self._config and self._config.benchmark == "tpcds":
            # For TPC-DS, ensure all tables are registered first
            from ...executor import get_dataset_path

            dataset_path = get_dataset_path(self._config)
            all_file_paths = {
                file.stem: str(file) for file in dataset_path.glob("*.parquet")
            }
            self._register_tables(all_file_paths)

            # Temporarily replace duckdb.sql with our connection's sql method
            import duckdb

            original_sql = duckdb.sql
            duckdb.sql = self._connection.sql
            try:
                result = query_func(**data)
            finally:
                duckdb.sql = original_sql
        else:
            # For TPC-H, use file path references
            result = query_func(**data)

        # If result has a fetchall method, call it to get the data
        if hasattr(result, "fetchall"):
            return result.fetchall()
        return result

    def cleanup(self) -> None:
        """Close the DuckDB connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
