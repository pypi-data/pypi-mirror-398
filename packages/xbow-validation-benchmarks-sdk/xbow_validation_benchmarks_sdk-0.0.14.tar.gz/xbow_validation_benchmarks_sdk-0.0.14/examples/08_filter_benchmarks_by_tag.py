#!/usr/bin/env python3
"""Filter benchmarks by tag."""
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
def main(tag: str = typer.Argument(..., help='Tag to filter by')):
    """Filter and display benchmarks by tag."""
    log.info('initializing repository')
    repository = BenchmarkRepository()

    log.info('loading benchmarks')
    benchmarks = load_all_benchmarks(repository)
    if not benchmarks:
        log.error('no benchmarks found')
        raise typer.Exit(1)

    # Collect all tags
    all_tags: set[str] = set()
    for b in benchmarks:
        all_tags.update(b.tags)

    log.info('available tags', tags=sorted(all_tags))

    # Case-insensitive filter
    filtered = [
        b for b in benchmarks
        if tag.lower() in [t.lower() for t in b.tags]
    ]
    log.info('filtered results', tag=tag, count=len(filtered))
    for b in filtered:
        typer.echo(f"  - {b.name} (level={b.level})")


if __name__ == '__main__':
    app()
