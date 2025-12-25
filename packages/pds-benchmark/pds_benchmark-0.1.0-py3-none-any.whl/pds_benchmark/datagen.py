"""Minimal data generation for PDS Benchmark."""

import json
import logging
import shutil
import subprocess
from pathlib import Path

from .config import BenchmarkConfig

logger = logging.getLogger(__name__)


def get_dataset_path(config: BenchmarkConfig) -> Path:
    """Get the path to the dataset."""
    return config.data_path / config.benchmark / f"scale-{config.scale_factor}"


def get_manifest_path(config: BenchmarkConfig) -> Path:
    """Get the path to the dataset manifest file."""
    return get_dataset_path(config) / ".dataset_manifest.json"


def dataset_exists(config: BenchmarkConfig) -> bool:
    """Check if dataset exists with correct scale factor."""
    dataset_path = get_dataset_path(config)
    manifest_path = get_manifest_path(config)

    if not dataset_path.exists() or not manifest_path.exists():
        return False

    try:
        with manifest_path.open() as f:
            stored_config = json.load(f)
        return stored_config.get("scale_factor") == config.scale_factor
    except (json.JSONDecodeError, FileNotFoundError):
        return False


def write_manifest(config: BenchmarkConfig, dataset_path: Path | None = None):
    """Write manifest file."""
    path = dataset_path if dataset_path else get_manifest_path(config).parent
    manifest_path = path / ".dataset_manifest.json"
    config_data = {"scale_factor": config.scale_factor}
    with manifest_path.open("w") as f:
        json.dump(config_data, f, indent=2)


def generate_tpch_dataset(config: BenchmarkConfig, override_path: Path | None = None):
    """Generate TPC-H dataset using tpchgen-cli."""
    dataset_path = override_path if override_path else get_dataset_path(config)

    # Remove existing dataset
    if dataset_path.exists():
        shutil.rmtree(dataset_path)

    # Generate dataset
    try:
        subprocess.run(
            [
                "tpchgen-cli",
                "-s",
                str(config.scale_factor),
                "--output-dir",
                str(dataset_path),
                "--format",
                "parquet",
                "-c",
                "snappy",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Dataset generation failed: {e}")
        raise

    write_manifest(config, dataset_path)


def generate_tpcds_dataset(config: BenchmarkConfig, override_path: Path | None = None):
    """Generate TPC-DS dataset using DuckDB."""
    dataset_path = override_path if override_path else get_dataset_path(config)

    # Remove existing dataset
    if dataset_path.exists():
        shutil.rmtree(dataset_path)

    dataset_path.mkdir(parents=True, exist_ok=True)

    try:
        import duckdb

        con = duckdb.connect()
        con.execute("INSTALL tpcds; LOAD tpcds;")
        con.execute(f"CALL dsdgen(sf={config.scale_factor});")
        con.execute(
            f"EXPORT DATABASE '{dataset_path}' (FORMAT PARQUET, COMPRESSION ZSTD, COMPRESSION_LEVEL 3);"
        )
        con.close()
    except ImportError:
        logger.error("DuckDB is required for TPC-DS dataset generation")
        raise
    except Exception as e:
        logger.error(f"TPC-DS dataset generation failed: {e}")
        raise

    write_manifest(config, dataset_path)


def ensure_dataset(config: BenchmarkConfig):
    """Ensure dataset exists, generate if needed."""
    if dataset_exists(config):
        logger.info(f"Using dataset (scale factor {config.scale_factor})")
        return

    logger.info(f"Generating dataset (scale factor {config.scale_factor})...")

    if config.benchmark == "tpch":
        generate_tpch_dataset(config)
    elif config.benchmark == "tpcds":
        generate_tpcds_dataset(config)
    else:
        raise ValueError(f"Unsupported benchmark: {config.benchmark}")

    logger.info("Dataset generation complete!")
