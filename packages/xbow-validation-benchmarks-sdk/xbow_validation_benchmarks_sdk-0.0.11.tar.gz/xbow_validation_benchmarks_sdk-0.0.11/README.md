# XBOW Validation Benchmarks SDK

Python SDK for managing XBOW validation benchmark environments.

## Installation

```bash
pip install xbow-validation-benchmarks-sdk
```

## Quick Start

```python
from xbow_validation_benchmarks_sdk.managers.repository import BenchmarkRepository
from xbow_validation_benchmarks_sdk.managers.environment import EnvironmentManager
from xbow_validation_benchmarks_sdk.models.benchmark import Benchmark

# Initialize repository (auto-clones if needed)
repository = BenchmarkRepository()

# List available benchmarks
benchmark_ids = repository.list_benchmarks()

# Load a benchmark
benchmark_path = repository.get_benchmark_path(benchmark_ids[0])
benchmark = Benchmark.model_validate_json(
    (benchmark_path / "benchmark.json").read_text()
)

# Create and start environment
env_manager = EnvironmentManager(repository=repository)
environment = env_manager.create_environment(benchmark=benchmark, flag="FLAG{test}")
env_manager.start_environment(environment)

# Access targets
for target in environment.targets:
    print(f"Target: {target.host}:{target.port}")

# Cleanup
env_manager.stop_environment(environment)
env_manager.destroy_environment(environment)
```

## Features

- **Repository Management**: Auto-clone and update benchmark repositories
- **Environment Isolation**: Each environment gets unique ports and isolated containers
- **Docker Integration**: Seamless Docker Compose orchestration
- **Flag Injection**: Dynamic flag configuration for CTF-style benchmarks

## Requirements

- Python >= 3.12
- Docker

## License

MIT
