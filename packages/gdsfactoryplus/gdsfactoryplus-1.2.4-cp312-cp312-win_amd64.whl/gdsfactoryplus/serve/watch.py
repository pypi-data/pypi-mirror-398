"""Server watcher handlers."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import BackgroundTasks

from .app import app, logger

if TYPE_CHECKING:
    import gdsfactoryplus.core.communication as comms
    import gdsfactoryplus.core.database as db
    import gdsfactoryplus.core.pdk as gfp_pdk
    import gdsfactoryplus.models as m
    import gdsfactoryplus.settings as gfp_settings
    from gdsfactoryplus.core import build, kcl
else:
    from gdsfactoryplus.core.lazy import lazy_import

    db = lazy_import("gdsfactoryplus.core.database")
    gfp_pdk = lazy_import("gdsfactoryplus.core.pdk")
    gfp_settings = lazy_import("gdsfactoryplus.settings")
    build = lazy_import("gdsfactoryplus.core.build")
    kcl = lazy_import("gdsfactoryplus.core.kcl")
    comms = lazy_import("gdsfactoryplus.core.communication")
    m = lazy_import("gdsfactoryplus.models")

_dedup: dict[Path, int] = {}
_skipped: set[Path] = set()


def _process_modified_file(p: Path) -> None:
    """Process a modified file in the background."""
    p = Path(p).resolve()
    t_prev = _dedup.get(p)
    t_curr = int(time.time())
    if t_prev is not None and t_curr - t_prev < 5:
        _skipped.add(p)
        return
    _dedup[p] = t_curr
    if p.name == "pyproject.toml":
        gfp_settings.get_settings.cache_clear()
        _, names = gfp_pdk.register_cells(reload=False)
        kcl.clear_cells_from_cache(*names)
        comms.send_message(m.ReloadFactoriesMessage())
        logger.info("pyproject.toml modified.")
        _dedup.pop(p, None)
        if p in _skipped:
            _skipped.remove(p)
            _process_modified_file(p)
        return

    removed_names = db.remove_factories_by_source(p)
    names, _ = gfp_pdk.register_cells(paths=[p])
    kcl.clear_cells_from_cache(*{*names, *removed_names})
    logger.info(f"registered / updated cells from {p}: {names}")

    build.build_by_names(*names, with_metadata=True)
    logger.info(f"build cells from {p}: {names}")
    _dedup.pop(p, None)
    if p in _skipped:
        _skipped.remove(p)
        _process_modified_file(p)


@app.get("/watch/on-modified")
def on_modified(path: str, background_tasks: BackgroundTasks) -> dict:
    """Handle an on-modified event."""
    p = Path(path).resolve()
    if not p.is_file():
        return {"detail": "not a file."}

    background_tasks.add_task(_process_modified_file, p)
    return {"detail": f"processing {p} in background."}


@app.get("/watch/on-deleted")
def on_deleted(path: str) -> dict:
    """Handle an on-deleted event."""
    p = Path(path).resolve()
    logger.info(f"on-deleted: {p}")

    if p.is_dir() and p.name == "build":
        # register_cells()
        return {"detail": "deleted build folder."}

    if (
        p.is_file()
        and p.name == gfp_settings.get_db_path().name
        and p.parent.name == "build"
    ):
        # register_cells()
        return {"detail": "deleted database."}

    if p.name.endswith(".pic.yml"):
        scm_path = p.parent / f"{p.name[:-8]}.scm.yml"
        logger.warning(f"deleting {scm_path} as well.")
        scm_path.unlink(missing_ok=True)

    # TODO: add pdk.unregister_cells for more targeted deletion
    _, names = gfp_pdk.register_cells(reload=False)
    kcl.clear_cells_from_cache(*names)
    logger.info(f"unregistered cells from {p}.")
    comms.send_message(m.ReloadFactoriesMessage())

    return {"detail": f"unregistered cells from {p}."}
