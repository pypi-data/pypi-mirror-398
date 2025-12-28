from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Optional


_PACKAGE_DATA = "codexdem.data"


def data_root() -> Path:
    try:
        return Path(resources.files(_PACKAGE_DATA))
    except Exception:
        return Path(__file__).resolve().parent / "data"


def data_path(name: str) -> Path:
    return data_root() / name


def resolve_asset_path(path: Optional[str]) -> Optional[Path]:
    if not path:
        return None
    candidate = Path(path)
    if candidate.is_absolute() and candidate.exists():
        return candidate

    cwd_candidate = Path.cwd() / candidate
    if cwd_candidate.exists():
        return cwd_candidate

    package_candidate = data_path(candidate.name)
    if package_candidate.exists():
        return package_candidate

    return None


def default_dem_path() -> Path:
    return data_path("DEM_20m.npz")


def default_settings_store() -> Path:
    home_cfg = Path.home() / ".codexdem"
    home_cfg.mkdir(parents=True, exist_ok=True)
    return home_cfg / "viewer_settings.json"
