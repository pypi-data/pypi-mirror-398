"""GDSFactory+ File Watcher."""

from __future__ import annotations

import typer

from .app import app

__all__ = ["watch"]


@app.command()
def watch(
    server_port: int = typer.Option(8787, help="Port of the server to notify"),
    ws_port: int | None = typer.Option(
        None, help="WebSocket port for VSCode communication"
    ),
) -> None:
    """Watch a folder for changes.

    Uses the high-performance Rust-based file watcher.
    All configuration is read from GDSFactory+ settings automatically.
    """
    from gdsfactoryplus.gdsfactoryplus import watch as rust_watch

    return rust_watch(server_port=server_port, ws_port=ws_port)
