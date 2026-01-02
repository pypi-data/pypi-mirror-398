import os
from pathlib import Path

APP_NAME = "artificer"
DIR_NAME = f".{APP_NAME}"
DEFAULT_ARTIFICER_HOME = Path.home() / DIR_NAME


def find_artificer_dir(start_dir: Path | None = None) -> Path | None:
    """Walk up from start_dir to find a .{APP_NAME}/ directory.

    Returns the directory path if found, None otherwise.
    """
    if start_dir is None:
        start_dir = Path.cwd()

    current = start_dir.resolve()

    # Walk up to root
    while current != current.parent:
        candidate = current / DIR_NAME
        if candidate.is_dir():
            return candidate
        current = current.parent

    # Check root as well
    candidate = current / DIR_NAME
    if candidate.is_dir():
        return candidate

    return None


def get_artificer_home() -> Path:
    """Get the global ARTIFICER_HOME directory.

    Uses ARTIFICER_HOME env var if set, otherwise ~/.artificer
    """
    env_home = os.getenv("ARTIFICER_HOME")
    if env_home:
        return Path(env_home).resolve()
    return DEFAULT_ARTIFICER_HOME


def get_workflows_dir() -> Path:
    """Get the workflows directory.

    Resolution order:
    1. Walk up from CWD to find .artificer/ directory
    2. Fall back to ARTIFICER_HOME (defaults to ~/.artificer)
    """
    # 1. Auto-discover project .artificer/
    artificer_dir = find_artificer_dir()
    if artificer_dir:
        return artificer_dir

    # 2. Fall back to global home
    return get_artificer_home()
