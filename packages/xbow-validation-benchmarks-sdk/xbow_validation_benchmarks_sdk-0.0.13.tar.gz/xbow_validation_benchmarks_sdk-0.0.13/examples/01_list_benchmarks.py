#!/usr/bin/env python3
"""List all available benchmarks."""
import structlog
import typer

from xbow_validation_benchmarks_sdk.managers.repository import BenchmarkRepository

log = structlog.get_logger()
app = typer.Typer()


@app.command()
def main():
    """List all available benchmarks in the repository."""
    log.info('initializing repository')
    repository = BenchmarkRepository()

    benchmarks = repository.list_benchmarks()
    if not benchmarks:
        log.warning('no benchmarks found')
        raise typer.Exit(1)

    log.info('benchmarks found', count=len(benchmarks))
    for benchmark_id in sorted(benchmarks):
        typer.echo(f"  - {benchmark_id}")


if __name__ == '__main__':
    app()
