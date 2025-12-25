"""Command-line interface for PDS Benchmark."""

import json
import logging
import sys
from pathlib import Path

import click

from . import __version__
from .config import BenchmarkConfig
from .datagen import ensure_dataset, generate_tpcds_dataset, generate_tpch_dataset
from .executor import run_benchmarks

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("pds_benchmark")


@click.group()
@click.version_option(__version__)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool):
    """PDS Benchmark - A Polars-focused data processing benchmark suite."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command()
@click.option(
    "--library", default="polars", help="Library to benchmark (default: polars)"
)
@click.option(
    "--benchmark", default="tpch", help="Benchmark suite to run (default: tpch)"
)
@click.option("--scale-factor", "-s", default=1, help="Scale factor (default: 1)")
@click.option(
    "--mode",
    default="streaming",
    type=click.Choice(["streaming", "in-memory", "gpu"]),
    help="Execution mode (default: streaming). GPU dependencies auto-install when needed.",
)
@click.option("--runs", "-r", default=3, help="Number of measurement runs (default: 3)")
@click.option("--queries", help="Comma-separated query numbers (e.g., 1,2,3)")
@click.option("--data-path", default="./data", help="Data directory (default: ./data)")
@click.option("--version", help="Manual version override for reporting")
@click.option(
    "--extra-config",
    help="Extra configuration as JSON string (e.g., '{\"gpu_device\": 0}')",
)
def run(
    library: str,
    benchmark: str,
    scale_factor: int,
    mode: str,
    runs: int,
    queries: str | None,
    data_path: str,
    version: str | None,
    extra_config: str | None,
):
    """Run benchmarks."""

    # Parse extra config
    config_dict = {}
    gpu_device = 0

    if extra_config:
        try:
            parsed_config = json.loads(extra_config)
            if not isinstance(parsed_config, dict):
                raise ValueError("Extra config must be a JSON object")

            # Handle mapped keys
            if "gpu_device" in parsed_config:
                gpu_device = int(parsed_config.pop("gpu_device"))
            if "gpu_memory_resource" in parsed_config:
                config_dict["USE_RMM_MR"] = parsed_config.pop("gpu_memory_resource")
            if "threads" in parsed_config:
                config_dict["THREAD_COUNT"] = parsed_config.pop("threads")
            if "memory_limit" in parsed_config:
                config_dict["MEMORY_LIMIT"] = parsed_config.pop("memory_limit")

            # Add remaining keys
            config_dict.update(parsed_config)

        except json.JSONDecodeError as e:
            click.echo(f"Error parsing extra config JSON: {e}", err=True)
            sys.exit(1)
        except ValueError as e:
            click.echo(f"Error in extra config: {e}", err=True)
            sys.exit(1)

    cfg = BenchmarkConfig(
        library=library,
        benchmark=benchmark,
        scale_factor=scale_factor,
        measurement_runs=runs,
        execution_mode=mode,
        data_path=Path(data_path),
        version=version,
        gpu_device=gpu_device,
        extra_config=config_dict,
    )

    # Parse query list
    query_list = None
    if queries:
        try:
            query_list = [int(q.strip()) for q in queries.split(",")]
        except ValueError:
            click.echo("Error: Invalid query list format", err=True)
            sys.exit(1)

    click.echo("=" * 60)
    click.echo(
        f"PDS Benchmark - {cfg.library}/{cfg.benchmark} (scale factor {cfg.scale_factor})"
    )
    click.echo("=" * 60)

    # Ensure dataset exists
    try:
        ensure_dataset(cfg)
    except Exception as e:
        click.echo(f"Error generating dataset: {e}", err=True)
        sys.exit(1)

    # Run benchmarks
    try:
        results = run_benchmarks(cfg, query_list)

        if results:
            click.echo("\n" + "=" * 60)
            click.echo("Benchmark completed successfully!")
            total_time = sum(r["total_min"] for r in results.values())
            click.echo(f"Total time: {total_time:.3f}s ({len(results)} queries)")
        else:
            click.echo("No queries completed successfully", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Benchmark failed: {e}", err=True)
        sys.exit(1)


@cli.group()
def generate():
    """Generate benchmark datasets manually."""
    pass


@generate.command()
@click.option("--scale-factor", "-s", default=1, help="Scale factor (default: 1)")
@click.option("--output", "-o", help="Output directory (optional)")
def tpch(scale_factor: int, output: str | None):
    """Generate TPC-H dataset."""
    try:
        cfg = BenchmarkConfig(benchmark="tpch", scale_factor=scale_factor)
        out_path = Path(output) if output else None

        click.echo(f"Generating TPC-H dataset (SF={scale_factor})...")
        generate_tpch_dataset(cfg, override_path=out_path)
        click.echo(
            f"Dataset generated successfully at {out_path if out_path else 'default location'}"
        )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@generate.command()
@click.option("--scale-factor", "-s", default=1, help="Scale factor (default: 1)")
@click.option("--output", "-o", help="Output directory (optional)")
def tpcds(scale_factor: int, output: str | None):
    """Generate TPC-DS dataset."""
    try:
        cfg = BenchmarkConfig(benchmark="tpcds", scale_factor=scale_factor)
        out_path = Path(output) if output else None

        click.echo(f"Generating TPC-DS dataset (SF={scale_factor})...")
        generate_tpcds_dataset(cfg, override_path=out_path)
        click.echo(
            f"Dataset generated successfully at {out_path if out_path else 'default location'}"
        )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
