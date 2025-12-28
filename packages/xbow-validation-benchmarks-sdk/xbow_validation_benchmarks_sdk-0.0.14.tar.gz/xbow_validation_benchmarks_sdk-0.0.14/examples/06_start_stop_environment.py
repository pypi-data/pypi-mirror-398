#!/usr/bin/env python3
"""Start and stop a benchmark environment with Docker."""
import structlog
import typer
from rich.console import Console
from rich.prompt import Confirm

from xbow_validation_benchmarks_sdk.managers.environment import EnvironmentManager
from xbow_validation_benchmarks_sdk.managers.repository import BenchmarkRepository
from xbow_validation_benchmarks_sdk.models.benchmark import Benchmark

log = structlog.get_logger()
app = typer.Typer()
console = Console()


@app.command()
def main(
    benchmark_id: str = typer.Argument(..., help='Benchmark ID'),
    flag: str = typer.Option('FLAG{test}', help='Flag to inject'),
):
    """Create, start, and stop a benchmark environment."""
    log.info('initializing')
    repository = BenchmarkRepository()
    env_manager = EnvironmentManager(repository=repository)

    try:
        benchmark_path = repository.get_benchmark_path(benchmark_id)
        benchmark = Benchmark.model_validate_json(
            (benchmark_path / 'benchmark.json').read_text(),
        )

        log.info('creating environment', benchmark=benchmark.name)
        environment = env_manager.create_environment(
            benchmark=benchmark, flag=flag,
        )
        log.info('environment created', id=environment.id)

        log.info('starting environment')
        env_manager.start_environment(environment)
        log.info(
            'environment started',
            targets=[f"{t.host}:{t.port}" for t in environment.targets],
        )

        console.print()
        Confirm.ask('Press Enter to stop the environment', default=True)
        console.print()

        log.info('stopping environment')
        env_manager.stop_environment(environment)

        log.info('destroying environment')
        env_manager.destroy_environment(environment)
        log.info('done')

    except Exception as e:
        log.error('failed', error=str(e))
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
