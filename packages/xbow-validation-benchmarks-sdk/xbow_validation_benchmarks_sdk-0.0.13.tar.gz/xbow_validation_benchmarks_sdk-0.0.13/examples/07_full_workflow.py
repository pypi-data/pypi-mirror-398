#!/usr/bin/env python3
"""Complete workflow: list, select, create, start, stop, and destroy."""
import time

import structlog
import typer

from xbow_validation_benchmarks_sdk.managers.environment import EnvironmentManager
from xbow_validation_benchmarks_sdk.managers.repository import BenchmarkRepository
from xbow_validation_benchmarks_sdk.models.benchmark import Benchmark

log = structlog.get_logger()
app = typer.Typer()


def load_benchmark(repository: BenchmarkRepository, benchmark_id: str) -> Benchmark:
    """Load a benchmark by ID."""
    benchmark_path = repository.get_benchmark_path(benchmark_id)
    return Benchmark.model_validate_json(
        (benchmark_path / 'benchmark.json').read_text(),
    )


@app.command()
def main(
    flag: str = typer.Option('FLAG{workflow_demo}', help='Flag to inject'),
    duration: int = typer.Option(
        10, help='Seconds to keep environment running',
    ),
):
    """Run a complete benchmark workflow from start to finish."""
    log.info('step 1: initializing repository')
    repository = BenchmarkRepository()

    log.info('step 2: listing benchmarks')
    benchmark_ids = repository.list_benchmarks()
    if not benchmark_ids:
        log.error('no benchmarks found')
        raise typer.Exit(1)
    log.info('benchmarks available', count=len(benchmark_ids))

    log.info('step 3: loading benchmarks')
    benchmarks = []
    for bid in benchmark_ids:
        try:
            benchmarks.append(load_benchmark(repository, bid))
        except Exception:
            continue

    if not benchmarks:
        log.error('no valid benchmarks')
        raise typer.Exit(1)

    log.info('step 4: selecting easiest benchmark')
    selected = min(benchmarks, key=lambda b: b.level)
    log.info('selected', name=selected.name, level=selected.level)

    log.info('step 5: creating environment')
    env_manager = EnvironmentManager(repository=repository)
    try:
        environment = env_manager.create_environment(
            benchmark=selected, flag=flag,
        )
        log.info('environment created', id=environment.id)

        log.info('step 6: starting environment')
        env_manager.start_environment(environment)
        log.info(
            'environment running',
            targets=[f"{t.host}:{t.port}" for t in environment.targets],
        )

        log.info('step 7: simulating test', duration=duration)
        time.sleep(duration)

        log.info('step 8: cleanup')
        env_manager.stop_environment(environment)
        env_manager.destroy_environment(environment)
        log.info('workflow complete')

    except Exception as e:
        log.error('workflow failed', error=str(e))
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
