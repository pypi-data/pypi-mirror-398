from pathlib import Path

from .types import PathType


def norm_path(path: PathType) -> Path:
    """Normalize path/str (expanduser +resolve). Return Path type."""
    if isinstance(path, str):
        path = Path(path)
    return path.expanduser().resolve()


def strf_path(path: PathType) -> str:
    """Normalize path/str (expanduser +resolve). Return str type."""
    return str(norm_path(path))
