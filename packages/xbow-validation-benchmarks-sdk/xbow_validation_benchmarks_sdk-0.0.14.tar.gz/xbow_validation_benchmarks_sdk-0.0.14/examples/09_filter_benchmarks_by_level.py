#!/usr/bin/env python3
"""Filter benchmarks by difficulty level."""
from collections import Counter

import structlog
import typer

from xbow_validation_benchmarks_sdk.managers.repository import BenchmarkRepository
from xbow_validation_benchmarks_sdk.models.benchmark import Benchmark

log = structlog.get_logger()
app = typer.Typer()


def load_all_benchmarks(repository: BenchmarkRepository) -> list[Benchmark]:
    """Load all benchmarks from the repository."""
    benchmarks = []
    for benchmark_id in repository.list_benchmarks():
        try:
            path = repository.get_benchmark_path(benchmark_id)
            benchmark = Benchmark.model_validate_json(
                (path / 'benchmark.json').read_text(),
            )
            benchmarks.append(benchmark)
        except Exception:
            continue
    return benchmarks


@app.command()
def main(
    level: int = typer.Argument(None, help='Filter by specific level'),
    max_level: int = typer.Option(None, '--max', help='Maximum level'),
    min_level: int = typer.Option(None, '--min', help='Minimum level'),
):
    """Filter and display benchmarks by difficulty level."""
    log.info('initializing repository')
    repository = BenchmarkRepository()

    log.info('loading benchmarks')
    benchmarks = load_all_benchmarks(repository)
    if not benchmarks:
        log.error('no benchmarks found')
        raise typer.Exit(1)

    # Show level distribution
    levels = [b.level for b in benchmarks]
    distribution = dict(sorted(Counter(levels).items()))
    log.info(
        'level statistics',
        min=min(levels),
        max=max(levels),
        distribution=distribution,
    )

    # Apply filters
    filtered = benchmarks
    if level is not None:
        filtered = [b for b in filtered if b.level == level]
    if max_level is not None:
        filtered = [b for b in filtered if b.level <= max_level]
    if min_level is not None:
        filtered = [b for b in filtered if b.level >= min_level]

    # Sort by level
    filtered = sorted(filtered, key=lambda b: b.level)

    log.info('results', count=len(filtered))
    for b in filtered:
        typer.echo(f"  [L{b.level}] {b.name}")


if __name__ == '__main__':
    app()
