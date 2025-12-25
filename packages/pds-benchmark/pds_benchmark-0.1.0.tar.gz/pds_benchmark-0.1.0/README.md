# PDS Benchmark

A minimal, Polars-focused data processing benchmark suite for evaluating performance across different execution modes.

## Features

- **Polars-focused**: Optimized for Polars with support for streaming, in-memory, and GPU execution
- **Minimal dependencies**: Lightweight with essential dependencies only
- **Easy installation**: Single command installation via pip
- **TPC-H benchmarks**: Industry-standard TPC-H queries (1-22)
- **Flexible configuration**: Comprehensive CLI options
- **Multiple modes**: Streaming, in-memory, and GPU acceleration support

## Quick Start

### Installation

```bash
# Install from PyPI (when published)
pip install pds-benchmark

# Or install from source
git clone https://github.com/pds-benchmark/pds-benchmark
cd pds-benchmark
pip install -e .
```

### Basic Usage

```bash
# Run with defaults (Polars streaming, scale factor 1)
pds-benchmark run

# Run with specific options
pds-benchmark run --scale-factor 10 --mode streaming --runs 3

# Run specific queries
pds-benchmark run --queries "1,6,12"

# Generate Dataset
pds-benchmark generate tpch --scale-factor 10 --output "./dataset"
```

## Configuration

### CLI Options

```bash
pds-benchmark run --help
```

Key options:
- `--scale-factor, -s`: TPC-H scale factor (default: 1)
- `--mode`: Execution mode - streaming, in-memory, or gpu (default: streaming)
- `--runs, -r`: Number of measurement runs (default: 3)
- `--queries`: Comma-separated query numbers to run
- `--data-path`: Directory for datasets (default: ./data)
- `--extra-config`: JSON string for advanced configuration

### Advanced Configuration

Use the `--extra-config` option to pass advanced settings as a JSON string:

```bash
pds-benchmark run --mode gpu --extra-config '{"gpu_device": 1, "gpu_memory_resource": "cuda-pool"}'
```

| Key | Description | Applicable To |
|-----|-------------|---------------|
| `gpu_device` | GPU device ID (e.g., 0, 1) | Polars (GPU mode) |
| `gpu_memory_resource` | Memory resource type (e.g., `cuda`, `cuda-pool`) | Polars (GPU mode) |
| `threads` | Number of threads to use | DuckDB |
| `memory_limit` | Memory limit (e.g., "10GB") | DuckDB |

## Execution Modes

### Streaming Mode (Default)
Memory-efficient processing for large datasets:
```bash
pds-benchmark run --mode streaming --scale-factor 100
```

### In-Memory Mode
Load all data into memory for fastest query execution:
```bash
pds-benchmark run --mode in-memory --scale-factor 10
```

### GPU Mode
GPU-accelerated processing (requires NVIDIA GPU + CUDA):
```bash
pds-benchmark run --mode gpu --scale-factor 10
```

GPU dependencies are installed automatically when first used. Falls back to CPU if unavailable.

## Use Cases

### CI/CD Integration

```yaml
# .github/workflows/benchmark.yml
name: Performance Benchmark
on: [push, pull_request]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      
      - name: Install benchmark
        run: pip install pds-benchmark
      
      - name: Run benchmark
        run: pds-benchmark run --scale-factor 1 --runs 1
```

### Performance Testing

```bash
# Quick performance check
pds-benchmark run --scale-factor 1 --runs 1

# Full benchmark suite
pds-benchmark run --scale-factor 10 --runs 5

# Compare execution modes
pds-benchmark run --mode streaming --scale-factor 10 --runs 3
pds-benchmark run --mode in-memory --scale-factor 10 --runs 3
```

## Requirements

- Python 3.11+
- Polars 1.0+
- tqdm
- For GPU mode: NVIDIA GPU with CUDA support

### System Requirements

- **Memory**: 4GB+ RAM for scale factor 1, 16GB+ for scale factor 10
- **Storage**: 1GB+ free space for datasets
- **GPU** (optional): CUDA 11.8+ compatible GPU for GPU mode

## Architecture

The benchmark uses a plugin-based architecture:

```
src/pds_benchmark/
├── executor.py              # Generic benchmark runner
├── plugins/
│   ├── __init__.py          # BenchmarkPlugin interface (ABC)
│   ├── polars/              # Polars plugin
│   │   ├── __init__.py      # PolarsPlugin (streaming/in-memory/GPU)
│   │   └── queries/tpch/    # TPC-H query implementations
│   ├── duckdb/              # DuckDB plugin
│   │   ├── __init__.py      # DuckDBPlugin
│   │   └── queries/         # Query implementations
│   └── pandas/              # Pandas plugin
│       └── __init__.py      # PandasPlugin
```

Each plugin implements:
- `setup(config)`: Initialize the library
- `load_table(path)`: Load data from parquet
- `execute_query(func, data)`: Execute a query
- `get_available_queries()`: List available queries
- `load_query()`: Load a specific query

This makes it easy to add support for new libraries.

## Output

Results are saved as JSON files with comprehensive metadata:

```json
{
  "metadata": {
    "library": "polars",
    "version": "1.32.0",
    "execution_mode": "streaming",
    "scale_factor": 10,
    "timestamp": "2024-01-15T10:30:00"
  },
  "results": {
    "Q1": {
      "load_median": 0.001,
      "exec_median": 0.145,
      "total_median": 0.146,
      "runs": 3
    }
  }
}
```

## Troubleshooting

### Common Issues

**Import Error**: Ensure Polars is installed
```bash
pip install polars>=1.0.0
```

**Dataset Generation Fails**: Install tpchgen-cli
```bash
pip install tpchgen-cli
```

**GPU Mode Issues**: GPU dependencies install automatically when needed
```bash
pds-benchmark --verbose run --mode gpu  # Shows fallback details
```

**Permission Errors**: Ensure write access to data directory
```bash
chmod 755 ./data
```

### Debug Mode

Enable verbose logging:
```bash
pds-benchmark --verbose run --scale-factor 1
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Benchmark Results

Quick comparison of execution modes (TPC-H scale factor 1 & 10):

```bash
# Compare modes easily
python compare_modes.py --scale-factor 1 --queries 1,21 --runs 2
```

**Key Findings:**
- **Streaming mode** consistently outperforms in-memory mode at larger scales
- **Complex queries** (Q9, Q18, Q21) show 2-3x better performance in streaming
- **Simple queries** show similar performance between modes
- **Memory usage** is significantly lower in streaming mode

**Recommendation:** Use streaming mode (default) for production workloads.

## Testing

### Quick Validation
```bash
# Run smoke tests (30-60 seconds)
./run_tests.sh

# Or directly:
python test_runner.py
```

### Comprehensive Testing
```bash
# Full test suite (2-5 minutes)
./run_tests.sh --full

# Test specific library
./run_tests.sh --polars
./run_tests.sh --duckdb

# Clean start
./run_tests.sh --clean
```

The test suite validates:
- ✅ CLI functionality (help, queries)
- ✅ Polars TPC-H (streaming, in-memory, GPU fallback)
- ✅ DuckDB TPC-H and TPC-DS
- ✅ Multiple scale factors
- ✅ Error handling

**Recommendation**: Run `./run_tests.sh` after any code changes to ensure everything still works.

## Links

- [Repository](https://github.com/pds-benchmark/pds-benchmark)
- [Issues](https://github.com/pds-benchmark/pds-benchmark/issues)
- [Polars Documentation](https://pola-rs.github.io/polars/)
- [TPC-H Specification](http://www.tpc.org/tpch/)
