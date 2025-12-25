"""DoItForMe local server."""

from __future__ import annotations

import json
from collections.abc import Callable
from io import StringIO
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

from .app import SETTINGS, app, logger

if TYPE_CHECKING:
    import gdsfactory as gf
    import pandas as pd
    import pydantic as pyd
    import websockets
    from gdsfactory import schematic
    from gdsfactory.read.from_yaml import from_yaml

    import gdsfactoryplus.core.pdk as gfp_pdk
    import gdsfactoryplus.models as m
else:
    from gdsfactoryplus.core.lazy import lazy_import

    m = lazy_import("gdsfactoryplus.models")
    gf = lazy_import("gdsfactory")
    pd = lazy_import("pandas")
    pyd = lazy_import("pydantic")
    websockets = lazy_import("websockets")
    schematic = lazy_import("gdsfactory.schematic")
    from_yaml = lazy_import("gdsfactory.read.from_yaml", "from_yaml")
    gfp_pdk = lazy_import("gdsfactoryplus.core.pdk")


@app.post("/doitforme")
async def doitforme_post(data: m.DoItForMe):  # noqa: ANN201
    """Request a DoItForMe by posting an initial circuit."""
    logger.debug(f"Received DoItForMe request: {data}")
    return await websocket_client(
        prompt=data.prompt,
        initial_circuit=data.initial_circuit,
        url=data.url or _get_doitforme_wss(),
    )


@app.get("/doitforme")
async def doitforme_get(  # noqa: ANN201
    prompt: str = "", url: str = ""
):
    """Request a DoItForMe."""
    logger.debug(f"Received DoItForMe request: {prompt}")
    return await websocket_client(
        prompt=prompt,
        url=url or _get_doitforme_wss(),
    )


async def websocket_client(
    prompt: str = "",
    initial_circuit: str = "",
    api_key: str | None = None,
    pdk_name: str | None = None,
    url: str = "",
) -> dict[str, Any]:
    """Call into the websocket client."""
    logger.debug("Websocket client connected...")
    url = url or _get_doitforme_wss()
    api_key = api_key or SETTINGS["api"]["key"]
    pdk_name = pdk_name or SETTINGS["drc"]["pdk"] or SETTINGS["pdk"]["name"]

    pdk = gfp_pdk.get_pdk()
    logger.info(f"Using PDK: {pdk.name}")

    component_descriptions = {
        cell_name: _get_component_description(cell)
        for cell_name, cell in pdk.cells.items()
    }

    try:
        async with websockets.connect(
            url, ping_interval=20, ping_timeout=60
        ) as websocket:
            msg = {
                "type": "prompt",
                "api_key": api_key,
                "pdk_name": pdk_name,
                "prompt": prompt,
                "initial_circuit": initial_circuit,
                "descriptions": component_descriptions,
                "api_version": "v1",
            }
            await websocket.send(json.dumps(msg))

            while True:
                try:
                    raw = await websocket.recv()
                    msg = json.loads(raw)
                    msgtype = msg.get("type", "")

                    if msgtype == "validate":
                        validation_result = _validate_netlist(msg)
                        netlist = msg["netlist"]

                        await websocket.send(json.dumps(validation_result))

                    elif msgtype == "result":
                        netlist_json = msg["netlist"]
                        try:
                            netlist = schematic.Netlist.model_validate_json(
                                netlist_json
                            )
                            netlist_dict = netlist.model_dump(
                                exclude_defaults=True, exclude_unset=True
                            )
                        except pyd.ValidationError:
                            netlist_dict = json.loads(netlist_json)
                        return netlist_dict
                    else:
                        msg = f"Unexpected message type: {msgtype}"
                        raise RuntimeError(msg)

                except websockets.exceptions.ConnectionClosed as e:
                    msg = f"WebSocket connection closed: {e}"
                    logger.error(msg)
                    raise RuntimeError(msg) from e
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON message: {e}")
                    continue  # Skip malformed messages

    except websockets.exceptions.WebSocketException as e:
        msg = f"WebSocket error: {e}"
        logger.error(msg)
        raise RuntimeError(msg) from e
    except Exception as e:
        msg = f"Unexpected error: {e}"
        logger.error(msg)
        raise RuntimeError(msg) from e


def _get_component_description(
    cell: Callable[..., gf.Component], *, with_port_summary: bool = True
) -> dict[str, str]:
    description = cell.__doc__ or "No description provided."

    port_summary = ""
    if with_port_summary:
        try:
            c = cell()

            port_info = [_get_port_dict(p) for p in c.ports]
            csv_string = StringIO()
            pd.DataFrame.from_records(port_info).to_csv(csv_string, index=False)

            port_summary = csv_string.getvalue()
        except Exception:  # noqa: BLE001
            port_summary = "No port summary available."

    return {"description": description, "port_summary": port_summary}


def _validate_netlist(msg: dict[str, Any]) -> dict[str, Any]:
    netlist = msg["netlist"]

    is_valid = True
    error = ""
    try:
        from_yaml(netlist)
    except Exception as e:  # noqa: BLE001
        error = str(e)
        is_valid = False

    return {
        "type": "validated",
        "is_valid": is_valid,
        "error": error,
    }


def _get_port_dict(port: gf.Port) -> dict[str, Any]:
    return {
        "name": port.name,
        "x": port.dcenter[0],
        "y": port.dcenter[1],
        "angle": port.angle,
        "port_type": port.port_type,
        "width": port.dwidth,
    }


def _get_doitforme_https() -> str:
    return SETTINGS["gpt"]["host"]


def _get_doitforme_wss() -> str:
    return urljoin(_get_doitforme_https().replace("https://", "wss://"), "ws")
