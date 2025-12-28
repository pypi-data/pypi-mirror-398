from pathlib import Path

from pydantic import BaseModel
from pydantic import Field

from xbow_validation_benchmarks_sdk.models.benchmark import Benchmark


class Target(BaseModel):
    host: str
    port: int


class Environment(BaseModel):
    id: str = Field(..., description='The id of the environment')
    path: Path = Field(..., description='The path of the environment')
    benchmark: Benchmark
    flag: str = Field(..., description='The flag of the environment')
    targets: list[Target] = Field(
        ...,
        description='The targets of the environment',
    )
