from os import cpu_count, environ
from pathlib import Path

CPU_CORES = cpu_count() or 1
STATE_FOLDER: str = str(Path("~/.blends").expanduser())
STATE_FOLDER_DEBUG = Path(STATE_FOLDER) / "debug"


def _get_artifact(env_var: str) -> str:
    if value := environ.get(env_var):
        return value
    exc_log = f"Expected environment variable: {env_var}"
    raise ValueError(exc_log)


def _get_optional_artifact(env_var: str) -> str | None:
    if value := environ.get(env_var):
        return value
    return None


# Side effects
TREE_SITTER_PARSERS = _get_artifact("BLENDS_TREE_SITTER_PARSERS_DIR")
TREE_SITTER_STATIC_NODE_FIELDS = _get_artifact("BLENDS_TREE_SITTER_STATIC_NODE_FIELDS")


Path(STATE_FOLDER).mkdir(mode=0o700, exist_ok=True, parents=True)
Path(STATE_FOLDER_DEBUG).mkdir(mode=0o700, exist_ok=True, parents=True)
