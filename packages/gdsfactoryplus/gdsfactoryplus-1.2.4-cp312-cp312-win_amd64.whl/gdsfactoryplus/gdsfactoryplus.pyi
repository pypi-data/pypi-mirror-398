# ruff: noqa: PYI021, D415

import builtins
import typing

def generate_call_graph(
    lib_paths: dict,
    function_filter: builtins.str | None = None,
    select_path: builtins.str | None = None,
) -> typing.Any:
    r"""Generate a call graph for Python libraries"""

def get_settings() -> dict[str, typing.Any]:
    r"""Get the merged settings from all sources"""

def get_ws_port() -> builtins.int:
    r"""Get the websocket port

    Returns the port set via `set_ws_port()`, or 7777 as default.
    """

def send_log_message(
    level: builtins.str, message: builtins.str, source: builtins.str = "python"
) -> None:
    r"""Send a log message to `VSCode` via WebSocket

    Convenience function to send a log message with the correct schema.

    # Arguments
    * `level` - Log level: "debug", "info", "warning", or "error"
    * `message` - The log message
    * `source` - Source identifier (default: "python")
    """

def send_message(message_json: builtins.str) -> None:
    r"""Send a JSON message to `VSCode` via WebSocket

    This function will silently ignore errors and implement a cooldown period
    to avoid spamming failed connection attempts.
    """

def serve(
    port: builtins.int = 8787,
    host: builtins.str = "127.0.0.1",
    workers: builtins.int = 1,
    reload: builtins.bool = False,
    ws_port: builtins.int | None = None,
) -> builtins.int:
    r"""Start the `GDSFactory+` background service

    This function starts a uvicorn server to serve the `GDSFactory+` API.
    It spawns the server process and exits with its exit code.

    # Arguments
    * `port` - Port on which to run the service (default: 8787)
    * `host` - Host on which to run the service (default: "127.0.0.1")
    * `workers` - Number of workers (0 = number of CPUs, default: 1)
    * `reload` - Run in reload mode for development (default: false)
    * `ws_port` - WebSocket port for communication with `VSCode` extension (default: None)
    """

def set_ws_port(port: builtins.int | None) -> None:
    r"""Set the websocket port (from CLI --ws-port argument)"""

def watch(
    server_port: builtins.int = 8787, ws_port: builtins.int | None = None
) -> None:
    r"""Watch for file changes in the current project

    This function will block and watch for file changes in the `GDSFactory+` project.
    It automatically finds the project root, reads configuration from settings,
    and notifies the `GDSFactory+` server when files change.

    The watcher uses Rust's native file system notification APIs for high performance.

    # Arguments
    * `server_port` - Port of the server to notify (default: 8787)
    * `ws_port` - WebSocket port for communication with `VSCode` extension (default: None)
    """
