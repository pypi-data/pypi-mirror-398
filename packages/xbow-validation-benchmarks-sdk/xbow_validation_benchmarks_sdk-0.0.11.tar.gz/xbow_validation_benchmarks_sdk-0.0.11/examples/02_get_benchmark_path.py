#!/usr/bin/env python3
"""Get the local path of a specific benchmark."""
import structlog
import typer

from xbow_validation_benchmarks_sdk.managers.repository import BenchmarkRepository

log = structlog.get_logger()
app = typer.Typer()


@app.command()
def main(benchmark_id: str = typer.Argument(..., help='Benchmark ID to look up')):
    """Get the local filesystem path for a benchmark."""
    log.info('initializing repository')
    repository = BenchmarkRepository()

    try:
        path = repository.get_benchmark_path(benchmark_id)
        log.info('benchmark path', benchmark_id=benchmark_id, path=str(path))

        log.info('directory contents')
        for item in sorted(path.iterdir()):
            item_type = 'dir' if item.is_dir() else 'file'
            typer.echo(f"  [{item_type}] {item.name}")

    except FileNotFoundError as e:
        log.error('benchmark not found', error=str(e))
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
