"""Base plugin interface for benchmark implementations."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..config import BenchmarkConfig


class BenchmarkPlugin(ABC):
    """Abstract base class for benchmark plugins.

    Each library (Polars, DuckDB, Pandas) should implement this interface.
    The plugin handles all library-specific operations including:
    - Loading data from parquet files
    - Executing queries with the appropriate engine
    - Managing library-specific configuration (e.g., Polars execution modes)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the plugin name (e.g., 'polars', 'duckdb')."""
        ...

    @property
    @abstractmethod
    def version(self) -> str | None:
        """Return the library version, or None if not installed."""
        ...

    @abstractmethod
    def setup(self, config: BenchmarkConfig) -> None:
        """Initialize the plugin with configuration.

        Args:
            config: Benchmark configuration including execution mode, etc.
        """
        ...

    @abstractmethod
    def load_table(self, file_path: str) -> Any:
        """Load a table from a parquet file.

        Args:
            file_path: Path to the parquet file.

        Returns:
            Library-specific data representation (LazyFrame, connection reference, etc.)
        """
        ...

    @abstractmethod
    def execute_query(self, query_func: Callable, data: dict[str, Any]) -> Any:
        """Execute a query function with loaded data.

        Args:
            query_func: The query function to execute.
            data: Dictionary mapping table names to loaded data.

        Returns:
            Query result (materialized).
        """
        ...

    def get_queries_dir(self, benchmark: str) -> Path:
        """Get the directory containing queries for this plugin.

        Args:
            benchmark: Benchmark suite name (e.g., 'tpch', 'tpcds').

        Returns:
            Path to the queries directory.
        """
        plugin_dir = Path(__file__).parent / self.name / "queries" / benchmark
        return plugin_dir

    def get_available_queries(self, benchmark: str) -> list[int]:
        """Get list of available query numbers.

        Args:
            benchmark: Benchmark suite name.

        Returns:
            List of available query numbers.
        """
        queries_dir = self.get_queries_dir(benchmark)
        if not queries_dir.exists():
            return []

        max_queries = 99 if benchmark == "tpcds" else 22
        return [
            i for i in range(1, max_queries + 1) if (queries_dir / f"q{i}.py").exists()
        ]

    def load_query(self, benchmark: str, query_num: int) -> Callable:
        """Load a query function.

        Args:
            benchmark: Benchmark suite name.
            query_num: Query number.

        Returns:
            The query function.

        Raises:
            FileNotFoundError: If the query file doesn't exist.
            ImportError: If the query can't be loaded.
        """
        import importlib.util

        query_file = self.get_queries_dir(benchmark) / f"q{query_num}.py"

        if not query_file.exists():
            raise FileNotFoundError(f"Query file not found: {query_file}")

        spec = importlib.util.spec_from_file_location(f"q{query_num}", query_file)
        if spec is None:
            raise ImportError(f"Could not create spec for {query_file}")

        module = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            raise ImportError(f"No loader found for {query_file}")

        spec.loader.exec_module(module)
        return module.q  # type: ignore

    def cleanup(self) -> None:
        """Clean up any resources. Override if needed."""
        return
