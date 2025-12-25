"""PDS Benchmark - A Polars-focused data processing benchmark suite."""

__version__ = "0.1.0"
__author__ = "PDS Benchmark Contributors"
__description__ = (
    "A minimal, Polars-focused benchmark suite for data processing systems"
)

# Core exports
from .config import BenchmarkConfig
from .executor import run_benchmarks

__all__ = [
    "__version__",
    "BenchmarkConfig",
    "run_benchmarks",
]
