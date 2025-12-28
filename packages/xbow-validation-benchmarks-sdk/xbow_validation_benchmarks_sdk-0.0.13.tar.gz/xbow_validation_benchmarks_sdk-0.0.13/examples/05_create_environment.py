#!/usr/bin/env python3
"""Create an isolated benchmark environment."""
import structlog
import typer

from xbow_validation_benchmarks_sdk.managers.environment import EnvironmentManager
from xbow_validation_benchmarks_sdk.managers.repository import BenchmarkRepository
from xbow_validation_benchmarks_sdk.models.benchmark import Benchmark

log = structlog.get_logger()
app = typer.Typer()


@app.command()
def main(
    benchmark_id: str = typer.Argument(..., help='Benchmark ID'),
    flag: str = typer.Option('FLAG{test}', help='Flag to inject'),
):
    """Create an environment for a benchmark (does not start containers)."""
    log.info('initializing')
    repository = BenchmarkRepository()
    env_manager = EnvironmentManager(repository=repository)

    try:
        benchmark_path = repository.get_benchmark_path(benchmark_id)
        benchmark = Benchmark.model_validate_json(
            (benchmark_path / 'benchmark.json').read_text(),
        )
        log.info('creating environment', benchmark=benchmark.name, flag=flag)

        environment = env_manager.create_environment(
            benchmark=benchmark, flag=flag,
        )
        log.info(
            'environment created',
            id=environment.id,
            path=str(environment.path),
            targets=[f"{t.host}:{t.port}" for t in environment.targets],
        )

    except (FileNotFoundError, ValueError) as e:
        log.error('failed to create environment', error=str(e))
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
