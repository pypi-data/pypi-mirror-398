from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _read_pyproject_version() -> str | None:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    if not pyproject.is_file():
        return None
    for line in pyproject.read_text().splitlines():
        if line.strip().startswith("version ="):
            return line.split("=", 1)[1].strip().strip('"')
    return None


def get_version() -> str:
    try:
        return version("viper-dev-kit")
    except PackageNotFoundError:
        return _read_pyproject_version() or "0.0.0"


__all__ = ["get_version"]
__version__ = get_version()
