"""Configuration management for PDS Benchmark."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class BenchmarkConfig:
    """Configuration for running benchmarks."""

    # Core settings
    library: str = "polars"
    benchmark: str = "tpch"
    scale_factor: int = 1
    measurement_runs: int = 3
    data_path: Path = Path("./data")

    # Polars-specific settings
    execution_mode: str = "streaming"  # streaming, in-memory, gpu
    gpu_device: int = 0
    version: str | None = None

    # Additional config
    extra_config: dict[str, Any] | None = None

    def __post_init__(self):
        if self.extra_config is None:
            self.extra_config = {}
        self.data_path = Path(self.data_path)


def create_default_config() -> BenchmarkConfig:
    """Create a default configuration."""
    return BenchmarkConfig()
