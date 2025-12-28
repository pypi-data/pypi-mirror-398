import shutil
import uuid
from pathlib import Path

import portpicker
import yaml
from dotenv import load_dotenv
from dotenv import set_key
from python_on_whales import DockerClient

from xbow_validation_benchmarks_sdk.managers.repository import BenchmarkRepository
from xbow_validation_benchmarks_sdk.models.benchmark import Benchmark
from xbow_validation_benchmarks_sdk.models.benchmark import WinCondition
from xbow_validation_benchmarks_sdk.models.environment import Environment
from xbow_validation_benchmarks_sdk.models.environment import Target


class EnvironmentManager:
    """Manages the lifecycle of benchmark environments.

    This class handles:
    - Creating isolated environments from benchmarks
    - Starting/stopping Docker containers
    - Destroying environments
    """

    def __init__(
        self,
        repository: BenchmarkRepository | Path | None = None,
        public_accessible_host: str = '127.0.0.1',
    ) -> None:
        """Initialize the environment manager.

        Args:
            repository: A BenchmarkRepository instance, a Path to a local
                        benchmark folder, or None to use the default repository.
            public_accessible_host: The host address for exposed ports.
        """
        if repository is None:
            self.repository = BenchmarkRepository()
        elif isinstance(repository, Path):
            self.repository = BenchmarkRepository(path=repository)
        else:
            self.repository = repository

        self.public_accessible_host = public_accessible_host

    def _update_docker_compose_file(self, environment_path: Path) -> list[int]:
        environment_docker_compose_path = environment_path / 'docker-compose.yml'
        with open(environment_docker_compose_path) as f:
            environment_docker_compose_object = yaml.safe_load(f)

        unused_host_ports = []
        for service in environment_docker_compose_object.get('services', {}).values():
            new_ports = []
            for ports in service.get('ports', []):
                if isinstance(ports, str) and ':' in ports:
                    unused_host_port = portpicker.pick_unused_port()
                    unused_host_ports.append(unused_host_port)
                    parts = ports.split(':')
                    new_ports.append(f"{unused_host_port}:{parts[-1]}")
                else:
                    new_ports.append(ports)
            service['ports'] = new_ports

        with open(environment_docker_compose_path, 'w') as f:
            yaml.dump(environment_docker_compose_object, f)

        return unused_host_ports

    def _update_flag(self, environment_path: Path, flag: str) -> None:
        env_file_path = environment_path / '.env'
        assert env_file_path.exists(), 'Environment .env file not found'
        load_dotenv(env_file_path, override=True)
        set_key(str(env_file_path), 'FLAG', flag)

    def create_environment(self, benchmark: Benchmark, flag: str) -> Environment:
        if benchmark.win_condition != WinCondition.FLAG:
            raise ValueError('Benchmark win condition must be FLAG')

        environment_id = str(uuid.uuid4())
        benchmark_path = self.repository.get_benchmark_path(benchmark.id)
        environment_path = Path('environments') / benchmark.id / environment_id

        shutil.copytree(benchmark_path, environment_path)
        unused_host_ports = self._update_docker_compose_file(
            environment_path=environment_path,
        )
        self._update_flag(environment_path=environment_path, flag=flag)

        return Environment(
            id=environment_id,
            path=environment_path,
            benchmark=benchmark,
            flag=flag,
            targets=[
                Target(
                    host=self.public_accessible_host, port=unused_port,
                ) for unused_port in unused_host_ports
            ],
        )

    def destroy_environment(self, environment: Environment):
        shutil.rmtree(
            Path('environments') /
            environment.benchmark.id / environment.id,
        )

    def start_environment(self, environment: Environment):
        docker = DockerClient(
            compose_files=[environment.path / 'docker-compose.yml'],
        )
        docker.compose.up(
            detach=True,
            wait=True,
            remove_orphans=True,
            build=True,
        )

    def stop_environment(self, environment: Environment):
        docker = DockerClient(
            compose_files=[environment.path / 'docker-compose.yml'],
        )
        docker.compose.down(volumes=True)
