"""Parse the GDSFactory+ settings."""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gdsfactoryplus import project as gfp_project
    from gdsfactoryplus.gdsfactoryplus import get_settings as _get_settings_rust
else:
    from gdsfactoryplus.core.lazy import lazy_import

    gfp_project = lazy_import("gdsfactoryplus.project")
    _get_settings_rust = lazy_import("gdsfactoryplus.gdsfactoryplus", "get_settings")


@cache
def get_settings() -> dict:
    """Get the gdsfactoryplus settings.

    Returns a dict with the merged settings from:
    1. Environment variables (GFP_*)
    2. pyproject.toml ([tool.gdsfactoryplus])
    3. ~/.gdsfactory/gdsfactoryplus.toml
    """
    return _get_settings_rust()


def get_wls() -> dict:
    """Get the wavelengths used in the project."""
    return get_settings()["sim"]["wls"]


def get_project_name() -> str:
    """Get the name of the project."""
    return get_settings()["name"]


def get_pdk_name() -> str:
    """Get the name of the pdk used in the project."""
    pdk_name = get_settings().get("pdk", {}).get("name", "")
    return pdk_name if pdk_name else "generic"


def is_a_pdk() -> bool:
    """Check if the settings are for a pdk or a project."""
    settings = get_settings()
    return settings["name"] == settings["pdk"]["name"]


def get_project_dir() -> Path:
    """Get the project root directory."""
    return Path(gfp_project.maybe_find_project_dir() or Path.cwd()).resolve()


def get_pics_dir() -> Path:
    """Get the PICs directory."""
    project_dir = get_project_dir()
    settings = get_settings()
    settings_parts = settings["name"].split(".")
    return project_dir / "/".join(settings_parts)


def get_build_dir() -> Path:
    """Get the build directory."""
    return get_project_dir() / "build"


def ignored_paths() -> list[Path]:
    """Get paths to ignore."""
    settings = get_settings()
    return [get_pics_dir() / path for path in settings["ignore"]]


def get_gds_dir() -> Path:
    """Get the output GDS directory."""
    path = get_build_dir() / "gds"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_db_path() -> Path:
    """Get the path to the database."""
    build_dir = get_build_dir()
    build_dir.mkdir(exist_ok=True)
    return build_dir / "gfp.db"


def get_log_dir() -> Path:
    """Get the log directory."""
    log_dir = get_build_dir() / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir
