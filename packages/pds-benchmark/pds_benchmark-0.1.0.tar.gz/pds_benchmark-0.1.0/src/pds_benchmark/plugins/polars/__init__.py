"""Polars benchmark plugin with multiple execution modes."""

import logging
import subprocess
import sys
from collections.abc import Callable
from typing import Any

import polars as pl

from ...config import BenchmarkConfig
from .. import BenchmarkPlugin

logger = logging.getLogger("pds_benchmark")


class PolarsPlugin(BenchmarkPlugin):
    """Polars benchmark plugin supporting streaming, in-memory, and GPU modes."""

    def __init__(self):
        self._config: BenchmarkConfig | None = None
        self._engine: Any = None

    @property
    def name(self) -> str:
        return "polars"

    @property
    def version(self) -> str | None:
        try:
            return pl.__version__
        except Exception:
            return None

    def setup(self, config: BenchmarkConfig) -> None:
        """Initialize Polars with the appropriate execution mode."""
        self._config = config
        self._engine = self._setup_engine()

    def _setup_engine(self) -> Any:
        """Setup Polars execution engine based on mode."""
        if self._config is None:
            return "streaming"

        if self._config.execution_mode == "streaming":
            return "streaming"
        elif self._config.execution_mode == "gpu":
            return self._setup_gpu_engine()
        else:  # in-memory
            return "in-memory"

    def _install_gpu_dependencies(self) -> bool:
        """Attempt to install GPU dependencies automatically."""
        try:
            logger.info(
                "GPU dependencies missing. Attempting automatic installation..."
            )
            logger.info("Installing 'polars[gpu]'...")

            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "polars[gpu]"],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode == 0:
                logger.info("GPU dependencies installed successfully!")
                return True
            else:
                logger.warning(f"Failed to install GPU dependencies: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.warning("GPU dependency installation timed out")
            return False
        except Exception as e:
            logger.warning(f"Could not install GPU dependencies: {e}")
            return False

    def _setup_gpu_engine(self) -> Any:
        """Setup GPU engine with automatic dependency installation and graceful fallback."""
        try:
            # Test if GPU execution works
            test_df = pl.LazyFrame({"test": [1, 2]})
            test_df.select(pl.col("test") * 2).collect(engine="gpu")

            # If we get here, GPU execution works - create the actual engine
            if (
                self._config
                and self._config.extra_config
                and "USE_RMM_MR" in self._config.extra_config
            ):
                try:
                    import rmm  # type: ignore

                    device = self._config.gpu_device or 0
                    mr_type = self._config.extra_config.get("USE_RMM_MR", "cuda-pool")

                    if mr_type == "cuda-pool":
                        free_mem, _ = rmm.mr.available_device_memory()
                        pool_size = int(free_mem * 0.8)
                        mr = rmm.mr.PoolMemoryResource(
                            rmm.mr.CudaMemoryResource(), initial_pool_size=pool_size
                        )
                    else:
                        mr = rmm.mr.CudaMemoryResource()

                    return pl.GPUEngine(
                        device=device, memory_resource=mr, raise_on_fail=True
                    )
                except ImportError:
                    logger.warning("RMM not available, using basic GPU engine")
                    return pl.GPUEngine(raise_on_fail=True)

            return pl.GPUEngine(raise_on_fail=True)

        except Exception as e:
            # Check if this is a missing GPU dependency issue
            if "cudf_polars" in str(e) and "not found" in str(e):
                logger.info(
                    "GPU dependencies not found. Attempting automatic installation..."
                )

                if self._install_gpu_dependencies():
                    # Try again after installation
                    try:
                        test_df = pl.LazyFrame({"test": [1, 2]})
                        test_df.select(pl.col("test") * 2).collect(engine="gpu")
                        logger.info("GPU support now available after installation!")
                        return pl.GPUEngine(raise_on_fail=True)
                    except Exception as retry_e:
                        logger.warning(
                            f"GPU still not working after installation: {retry_e}"
                        )

            # Fall back to streaming
            logger.info("GPU mode not available, falling back to streaming mode")
            if "cudf_polars" in str(e):
                logger.info(
                    "To manually install GPU support: pip install 'polars[gpu]'"
                )
                logger.info(
                    "Requirements: NVIDIA GPU (compute 7.0+), CUDA 12+, Linux/WSL2"
                )

            return "streaming"

    def load_table(self, file_path: str) -> pl.LazyFrame:
        """Load a table as LazyFrame."""
        return pl.scan_parquet(file_path)

    def execute_query(self, query_func: Callable, data: dict[str, pl.LazyFrame]) -> Any:
        """Execute query with the configured engine."""
        result = query_func(**data)

        if not hasattr(result, "collect"):
            return result

        # Execute based on engine type
        if self._engine == "streaming":
            return result.collect(streaming=True)
        elif self._engine == "in-memory":
            return result.collect()
        else:  # GPU
            return result.collect(engine=self._engine)
