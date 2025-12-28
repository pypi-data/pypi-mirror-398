"""Functions to manage downloaded files location."""

from pathlib import Path
from comexdown.tables import TABLES


def ensure_path(path: Path | str) -> Path:
    """Ensure the input is a Path object."""
    return Path(path) if isinstance(path, str) else path


def path_aux(
    root: Path | str,
    name: str,
) -> Path | None:
    """
    Generate path for auxiliary table file.
    """
    root = ensure_path(root)
    file_info = TABLES.get(name)
    if not file_info:
        return None

    filename = file_info.get("file_ref")
    if not filename:
        return None

    return root / "auxiliary-tables" / filename


def path_trade(
    root: Path | str,
    direction: str,
    year: int,
    mun: bool = False,
) -> Path:
    """
    Generate path for trade data file (NCM).
    """
    root = ensure_path(root)
    direction = direction.lower()

    if direction not in ("exp", "imp"):
        raise ValueError(f"Invalid argument direction={direction}")

    prefix = f"{direction.upper()}_"
    suffix = "_MUN" if mun else ""
    dir_name = f"{direction}-mun" if mun else direction

    filename = f"{prefix}{year}{suffix}.csv"
    return root / dir_name / filename


def path_trade_nbm(
    root: Path | str,
    direction: str,
    year: int,
) -> Path:
    """
    Generate path for NBM trade data file.
    """
    root = ensure_path(root)
    direction = direction.lower()

    if direction not in ("exp", "imp"):
        raise ValueError(f"Invalid argument direction={direction}")

    prefix = f"{direction.upper()}_"
    dir_name = f"{direction}-nbm"

    filename = f"{prefix}{year}_NBM.csv"
    return root / dir_name / filename


def get_creation_time(path: Path) -> float:
    """Get the creation time of a file."""
    return path.stat().st_ctime
