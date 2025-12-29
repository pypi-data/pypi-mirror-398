from os import (
    environ,
)
from typing import (
    Literal,
)


def guess_environment() -> Literal["development", "production"]:
    return "production" if environ.get("CI_COMMIT_REF_NAME", "trunk") == "trunk" else "development"


def is_fluid_batch_env() -> bool:
    return "FLUIDATTACKS_EXECUTION" in environ
