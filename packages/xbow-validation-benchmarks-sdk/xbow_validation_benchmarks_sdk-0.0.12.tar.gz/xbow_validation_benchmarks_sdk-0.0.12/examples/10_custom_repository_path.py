#!/usr/bin/env python3
"""Demonstrate custom repository path configuration."""
from pathlib import Path

import structlog
import typer

from xbow_validation_benchmarks_sdk.managers.repository import BenchmarkRepository
from xbow_validation_benchmarks_sdk.managers.repository import DEFAULT_LOCAL_PATH
from xbow_validation_benchmarks_sdk.managers.repository import DEFAULT_REPO_URL

log = structlog.get_logger()
app = typer.Typer()


@app.command()
def main(
    path: Path = typer.Option(None, help='Custom local path'),
    url: str = typer.Option(None, help='Custom repository URL'),
):
    """Initialize repository with custom path or URL."""
    log.info(
        'defaults',
        default_path=str(DEFAULT_LOCAL_PATH),
        default_url=DEFAULT_REPO_URL,
    )

    log.info('using custom configuration', path=str(path), url=url)
    repository = BenchmarkRepository(path=path, repo_url=url)

    log.info(
        'repository initialized',
        path=str(repository.path),
        benchmark_count=len(repository.list_benchmarks()),
    )


if __name__ == '__main__':
    app()
