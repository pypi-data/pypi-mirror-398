#!/usr/bin/env python3
"""Update the local benchmark repository from remote."""
import structlog
import typer

from xbow_validation_benchmarks_sdk.managers.repository import BenchmarkRepository

log = structlog.get_logger()
app = typer.Typer()


@app.command()
def main():
    """Pull the latest changes from the remote repository."""
    log.info('initializing repository')
    repository = BenchmarkRepository()
    log.info('repository path', path=str(repository.path))

    log.info('pulling latest changes')
    try:
        repository.update()
        log.info(
            'repository updated', benchmark_count=len(
                repository.list_benchmarks(),
            ),
        )
    except Exception as e:
        log.error('update failed', error=str(e))
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
