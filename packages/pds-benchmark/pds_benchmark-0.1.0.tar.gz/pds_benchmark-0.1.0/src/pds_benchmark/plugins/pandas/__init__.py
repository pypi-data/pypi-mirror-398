"""Pandas benchmark plugin."""

import logging
from collections.abc import Callable
from typing import Any

from ...config import BenchmarkConfig
from .. import BenchmarkPlugin

logger = logging.getLogger("pds_benchmark")


class PandasPlugin(BenchmarkPlugin):
    """Pandas benchmark plugin."""

    def __init__(self):
        self._config: BenchmarkConfig | None = None

    @property
    def name(self) -> str:
        return "pandas"

    @property
    def version(self) -> str | None:
        try:
            import pandas as pd

            return pd.__version__
        except ImportError:
            return None

    def setup(self, config: BenchmarkConfig) -> None:
        """Initialize Pandas plugin."""
        self._config = config

    def load_table(self, file_path: str) -> Any:
        """Load table as pandas DataFrame."""
        try:
            import pandas as pd

            return pd.read_parquet(file_path)
        except ImportError as e:
            raise ImportError(
                "Pandas is not installed. Please install with: pip install pandas"
            ) from e

    def execute_query(self, query_func: Callable, data: dict[str, Any]) -> Any:
        """Execute pandas query."""
        return query_func(**data)
