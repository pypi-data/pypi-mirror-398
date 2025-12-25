"""Freeze a python cell as schematic netlist."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import Body
from fastapi.responses import JSONResponse, PlainTextResponse

from .app import app, logger

if TYPE_CHECKING:
    import orjson

    from gdsfactoryplus.core.freeze import freeze
else:
    from gdsfactoryplus.core.lazy import lazy_import

    orjson = lazy_import("orjson")
    freeze = lazy_import("gdsfactoryplus.core.freeze", "freeze")


@app.post("/freeze/{cell_name}", response_model=None)
def freeze_post(
    cell_name: str,
    body: Annotated[str, Body()],
) -> PlainTextResponse | JSONResponse:
    """Freeze a python cell as schematic netlist.

    Args:
        cell_name: name of the cell to freeze.
        body: the keyword arguments to create the cell with.
    """
    kwargs = orjson.loads(body)
    try:
        netlist = freeze(cell_name, **kwargs)
    except FileNotFoundError as e:
        return PlainTextResponse(str(e), status_code=400)
    except RuntimeError as e:
        return PlainTextResponse(str(e), status_code=422)
    except Exception as e:  # noqa: BLE001
        return PlainTextResponse(f"Unexpected error: {e}", status_code=500)

    logger.debug(str(netlist))

    return JSONResponse(netlist, status_code=200)


@app.get("/freeze/{cell_name}", response_model=None)
def freeze_get(cell_name: str) -> PlainTextResponse | JSONResponse:
    """Freeze a python cell as schematic netlist.

    Args:
        cell_name: name of the cell to freeze.
    """
    return freeze_post(cell_name, body="{}")
