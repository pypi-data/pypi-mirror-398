#!/usr/bin/env python3
"""Load and display benchmark metadata."""
import structlog
import typer

from xbow_validation_benchmarks_sdk.managers.repository import BenchmarkRepository
from xbow_validation_benchmarks_sdk.models.benchmark import Benchmark

log = structlog.get_logger()
app = typer.Typer()


@app.command()
def main(benchmark_id: str = typer.Argument(..., help='Benchmark ID to load')):
    """Load and display metadata for a specific benchmark."""
    log.info('initializing repository')
    repository = BenchmarkRepository()

    try:
        benchmark_path = repository.get_benchmark_path(benchmark_id)
        metadata_path = benchmark_path / 'benchmark.json'

        if not metadata_path.exists():
            log.error('metadata file not found', path=str(metadata_path))
            raise typer.Exit(1)

        benchmark = Benchmark.model_validate_json(metadata_path.read_text())
        log.info(
            'benchmark loaded',
            id=benchmark.id,
            name=benchmark.name,
            level=benchmark.level,
            win_condition=benchmark.win_condition.value,
            tags=benchmark.tags,
        )

    except FileNotFoundError as e:
        log.error('benchmark not found', error=str(e))
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
