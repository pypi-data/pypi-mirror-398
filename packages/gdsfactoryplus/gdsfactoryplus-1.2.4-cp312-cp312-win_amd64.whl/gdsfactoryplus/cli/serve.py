"""Serve the GDSFactory+ server."""

from __future__ import annotations

import os
import subprocess
import sys

import typer

from .app import app

__all__ = ["serve"]


@app.command()
def serve(
    port: int = 8787,
    host: str = "localhost",
    workers: int = 1,
    *,
    reload: bool = False,
    ws_port: int | None = None,
) -> None:
    """Start the GDSFactory+ background service.

    Args:
        port: the port on which to run the background service
        host: the host on which to run the background service
        workers: the number of workers of the background service
        reload: run the background service in debug mode (not recommended)
        ws_port: the websocket port for VSCode communication
    """
    from gdsfactoryplus.gdsfactoryplus import get_ws_port as rust_get_ws_port
    from gdsfactoryplus.gdsfactoryplus import set_ws_port as rust_set_ws_port

    if ws_port is not None:
        rust_set_ws_port(ws_port)
        ws_port = rust_get_ws_port()

    from gdsfactoryplus.logger import get_logger as log

    log().info(f"Server start requested.\n{port=}\n{host=}\n{workers=}\n{ws_port=}")
    log().debug("Importing communication modules...")
    from gdsfactoryplus.core.communication import send_message
    from gdsfactoryplus.models import StartupStatusMessage

    log().debug("Communication modules imported.")
    send_message(
        StartupStatusMessage(message="Server starting. Just a moment please...")
    )
    if host == "localhost":
        host = "127.0.0.1"

    # Calculate actual workers (0 means use all CPUs)
    num_cpus = os.cpu_count() or 1
    actual_workers = num_cpus if workers == 0 else min(workers, num_cpus)

    # Build uvicorn command
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "gdsfactoryplus.serve.app:get_app",
        "--host",
        host,
        "--port",
        str(port),
        "--workers",
        str(actual_workers),
        "--factory",
        "--forwarded-allow-ips=*",
        "--proxy-headers",
        "--use-colors",
    ]

    if reload:
        cmd.append("--reload")

    # Set up environment with ws_port if provided
    env = os.environ.copy()
    if ws_port is not None:
        env["GFP_WS_PORT"] = str(ws_port)

    log().debug("Starting uvicorn subprocess...")
    result = subprocess.run(cmd, check=False, env=env)
    raise typer.Exit(result.returncode)
