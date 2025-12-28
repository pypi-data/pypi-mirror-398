import subprocess
from pathlib import Path

DEFAULT_REPO_URL = 'https://github.com/xbow-engineering/validation-benchmarks'
DEFAULT_LOCAL_PATH = Path.home() / '.ctf-arena' / 'xbow-validation-benchmarks'


class BenchmarkRepository:
    """Manages access to the XBOW validation benchmarks repository.

    This class handles:
    - Locating the local benchmark repository
    - Cloning from a remote Git repository if needed
    - Providing paths to individual benchmarks
    """

    def __init__(
        self,
        path: Path | None = None,
        repo_url: str | None = None,
    ) -> None:
        """Initialize the benchmark repository.

        Args:
            path: Local path to the benchmark repository.
                  Defaults to ~/.ctf-arena/xbow-validation-benchmarks
            repo_url: Git repository URL to clone from if local path is empty.
                      Defaults to the official XBOW validation-benchmarks repo.
        """
        self.repo_url = repo_url or DEFAULT_REPO_URL
        self.path = self._ensure_repository(path)

    def _ensure_repository(self, path: Path | None) -> Path:
        """Ensure the repository exists locally, cloning if necessary."""
        target_path = path or DEFAULT_LOCAL_PATH

        if target_path.exists():
            # Check if directory is non-empty
            try:
                next(target_path.iterdir())
                return target_path
            except StopIteration:
                # Directory exists but is empty; will clone
                pass
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)

        # Clone the repository
        subprocess.run(
            ['git', 'clone', self.repo_url, str(target_path)],
            check=True,
        )

        return target_path

    def get_benchmark_path(self, benchmark_id: str) -> Path:
        """Get the path to a specific benchmark.

        Args:
            benchmark_id: The ID of the benchmark.

        Returns:
            Path to the benchmark directory.

        Raises:
            FileNotFoundError: If the benchmark does not exist.
        """
        benchmark_path = self.path / 'benchmarks' / benchmark_id
        if not benchmark_path.exists():
            raise FileNotFoundError(
                f"Benchmark '{benchmark_id}' not found at {benchmark_path}",
            )
        return benchmark_path

    def list_benchmarks(self) -> list[str]:
        """List all available benchmark IDs.

        Returns:
            Sorted list of benchmark IDs.
        """
        benchmarks_dir = self.path / 'benchmarks'
        if not benchmarks_dir.exists():
            return []
        return sorted([
            d.name for d in benchmarks_dir.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ])

    def update(self) -> None:
        """Pull the latest changes from the remote repository."""
        subprocess.run(
            ['git', '-C', str(self.path), 'pull'],
            check=True,
        )
