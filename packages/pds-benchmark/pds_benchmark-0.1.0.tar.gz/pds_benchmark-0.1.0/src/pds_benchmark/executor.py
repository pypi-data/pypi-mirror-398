"""Multi-library benchmark executor for PDS Benchmark."""

import csv
import gc
import inspect
import logging
import time
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

from .config import BenchmarkConfig
from .plugins import BenchmarkPlugin

logger = logging.getLogger("pds_benchmark")


def get_plugin(library: str) -> BenchmarkPlugin:
    """Get the appropriate plugin for the library.

    Args:
        library: Library name (polars, duckdb, pandas).

    Returns:
        Initialized plugin instance.

    Raises:
        ValueError: If library is not supported.
    """
    if library == "polars":
        from .plugins.polars import PolarsPlugin

        return PolarsPlugin()
    elif library == "duckdb":
        from .plugins.duckdb import DuckDBPlugin

        return DuckDBPlugin()
    elif library == "pandas":
        from .plugins.pandas import PandasPlugin

        return PandasPlugin()
    else:
        raise ValueError(f"Unsupported library: {library}")


def get_dataset_path(config: BenchmarkConfig) -> Path:
    """Get dataset path."""
    return config.data_path / config.benchmark / f"scale-{config.scale_factor}"


def build_file_paths(config: BenchmarkConfig) -> dict[str, str]:
    """Build file path mapping."""
    dataset_path = get_dataset_path(config)
    return {file.stem: str(file) for file in dataset_path.glob("*.parquet")}


def append_result_to_csv(
    config: BenchmarkConfig,
    plugin: BenchmarkPlugin,
    query_num: int,
    run_index: int,
    total_time: float,
):
    """Append result to CSV file."""
    csv_file = Path("benchmark_results.csv")
    file_exists = csv_file.exists()

    with csv_file.open("a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                [
                    "timestamp",
                    "library",
                    "version",
                    "benchmark",
                    "scale_factor",
                    "mode",
                    "query",
                    "run_index",
                    "total_time_s",
                ]
            )

        writer.writerow(
            [
                datetime.now().isoformat(),
                plugin.name,
                config.version or plugin.version or "unknown",
                config.benchmark,
                config.scale_factor,
                config.execution_mode,
                f"Q{query_num}",
                run_index,
                f"{total_time:.4f}",
            ]
        )


def run_benchmarks(config: BenchmarkConfig, queries: list[int] | None = None) -> dict:
    """Run benchmarks with multi-library support.

    Args:
        config: Benchmark configuration.
        queries: Optional list of query numbers to run. If None, runs all available.

    Returns:
        Dictionary of results keyed by query name.
    """
    # Get plugin for the library
    try:
        plugin = get_plugin(config.library)
        plugin.setup(config)
    except (ImportError, ValueError) as e:
        logger.error(f"Failed to create plugin for {config.library}: {e}")
        return {}

    # Get available queries if not specified
    if queries is None:
        queries = plugin.get_available_queries(config.benchmark)

    if not queries:
        logger.error(f"No queries found for {config.library}/{config.benchmark}")
        return {}

    total_executions = len(queries) * config.measurement_runs
    logger.info(
        f"Running {len(queries)} queries with {config.measurement_runs} runs each"
    )

    file_paths = build_file_paths(config)
    results = {}

    with tqdm(total=total_executions, desc="Running Benchmarks", unit="run") as pbar:
        for query_num in queries:
            try:
                query_func = plugin.load_query(config.benchmark, query_num)
            except FileNotFoundError:
                logger.warning(f"Query Q{query_num} not found, skipping")
                pbar.update(config.measurement_runs)
                continue

            times = []
            pbar.set_description(f"Running Q{query_num}")

            for run in range(config.measurement_runs):
                try:
                    # Start timer
                    start_time = time.perf_counter()

                    # Get required tables from query signature
                    sig = inspect.signature(query_func)
                    required_tables = {
                        name
                        for name, param in sig.parameters.items()
                        if name != "kwargs" and param.kind != param.VAR_KEYWORD
                    }

                    # Load only required tables - plugin handles the format
                    loaded_data = {}
                    missing_tables = []
                    for table_name in required_tables:
                        if table_name in file_paths:
                            loaded_data[table_name] = plugin.load_table(
                                file_paths[table_name]
                            )
                        else:
                            missing_tables.append(table_name)

                    if missing_tables:
                        raise FileNotFoundError(
                            f"Required tables not found in dataset: {missing_tables}"
                        )

                    # Execute query
                    gc.disable()
                    plugin.execute_query(query_func, loaded_data)
                    gc.enable()

                    # Stop timer
                    total_time = time.perf_counter() - start_time
                    times.append(total_time)
                    pbar.update(1)

                    # Append to CSV
                    append_result_to_csv(config, plugin, query_num, run + 1, total_time)

                except Exception as e:
                    gc.enable()
                    tqdm.write(f"Q{query_num} run {run + 1} failed: {e}")
                    remaining_runs = config.measurement_runs - (run + 1)
                    if remaining_runs > 0:
                        pbar.update(remaining_runs)
                    break

            if times:
                min_time = min(times)
                median_time = sorted(times)[len(times) // 2]
                max_time = max(times)
                results[f"Q{query_num}"] = {
                    "total_min": min_time,
                    "total_median": median_time,
                    "total_max": max_time,
                    "runs": len(times),
                }

    # Summary
    if results:
        total_min = sum(r["total_min"] for r in results.values())
        total_median = sum(r["total_median"] for r in results.values())
        total_max = sum(r["total_max"] for r in results.values())

        logger.info("")
        logger.info("Benchmark Results:")
        logger.info("┌─────────┬────────────┬────────────┬────────────┐")
        logger.info("│ Query   │ Min (s)    │ Median (s) │ Max (s)    │")
        logger.info("├─────────┼────────────┼────────────┼────────────┤")

        for query_name in sorted(results.keys(), key=lambda x: int(x[1:])):
            r = results[query_name]
            logger.info(
                f"│ {query_name:<7} │ {r['total_min']:>10.4f} │ {r['total_median']:>10.4f} │ {r['total_max']:>10.4f} │"
            )

        logger.info("├─────────┼────────────┼────────────┼────────────┤")
        logger.info(
            f"│ Total   │ {total_min:>10.4f} │ {total_median:>10.4f} │ {total_max:>10.4f} │"
        )
        logger.info("└─────────┴────────────┴────────────┴────────────┘")
        logger.info("")
        logger.info("Detailed results saved to benchmark_results.csv")

    # Clean up plugin resources
    plugin.cleanup()

    return results
