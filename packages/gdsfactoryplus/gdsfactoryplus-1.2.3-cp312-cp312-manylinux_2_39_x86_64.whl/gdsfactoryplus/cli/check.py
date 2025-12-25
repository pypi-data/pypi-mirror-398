"""DRC Checking."""

from __future__ import annotations

import json
import secrets
import sys
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Annotated

import typer

from .app import app

__all__ = ["check"]

check = typer.Typer()
app.add_typer(check, name="check")


@check.command()
def drc(
    path: Annotated[str, typer.Argument()],
    outpath: str = "stdout",
    pdk: str = "",
    process: str = "",
    timeout: int = 0,
    host: str = "",
    api_key: str = "",
    *,
    verbose: bool = True,
) -> None:
    """Check a GDS file for DRC errors.

    Args:
        path: path to the GDS file to run the check on.
        outpath: the output path to save the drc results to
        pdk: PDK to use for the check.
        process: the drc rules might be slightly different depending on the process
        timeout: timeout in seconds for the check (DRC only).
        host: api host (DRC only).
        api_key: the api key (DRC only).
        verbose: if True, print status messages to stderr.
    """
    from ..core.check import check_drc
    from ..core.shared import cli_environment, print_to_file
    from ..logger import get_logger
    from ..settings import get_settings

    settings = get_settings()
    logger = get_logger()
    logger.remove()

    if not pdk:
        pdk = settings["drc"]["pdk"] or settings["pdk"]["name"]
    if not process:
        process = settings["drc"]["process"]
    if not timeout:
        timeout = settings["drc"]["timeout"]
    if not host:
        host = settings["drc"]["host"]
    if not api_key:
        api_key = settings["api"]["key"]

    with cli_environment(no_stdout=True, no_stderr=True):
        result = check_drc(
            path=path,
            pdk=pdk,
            process=process,
            timeout=timeout,
            verbose=verbose,
            host=host,
            api_key=api_key,
        )

    sys.stderr.write("DONE!\n")
    print_to_file(outpath, result)


@check.command()
def conn(
    path: Annotated[str, typer.Argument()],
    pdk: str = "",
    outpath: str = "stdout",
    *,
    verbose: bool = True,
) -> None:
    """Check a GDS file for DRC errors.

    Args:
        path: path to the GDS file to run the check on.
        pdk: PDK to use for the check.
        outpath: the output path to save the drc results to
        verbose: if True, print status messages to stderr.
    """
    from ..core.check import check_conn
    from ..core.shared import cli_environment, print_to_file
    from ..settings import get_settings

    if not pdk:
        pdk = get_settings()["pdk"]["name"]

    with cli_environment(no_stdout=True, no_stderr=False):
        result = check_conn(
            path=path,
            verbose=verbose,
        )
    print_to_file(outpath, result)


LVS_INFO_TEMPLATE = """Running LVS on {cell!r}.
    - reference netlist path: {netpath!r}
    - output lyrdb path: {outpath!r}
    - pdk: {pdk!r}
"""


@check.command()
def lvs(
    cell: Annotated[str, typer.Argument()],
    netpath: Annotated[str, typer.Argument()],
    outpath: str = "stdout",
    pdk: str = "",
    cellargs: str = "",
) -> None:
    """Check a GDS file for LVS errors.

    Args:
        cell: the name of the cell to check
        netpath: the path to the reference netlist
        pdk: PDK to use for the check.
        cellargs: JSON encoded arguments to create the cell with.
        outpath: the output path to save the drc results to
    """
    from ..core.lvs import optical_lvs
    from ..core.pdk import get_pdk, register_cells
    from ..core.shared import cli_environment, print_to_file
    from ..logger import get_logger

    logger = get_logger()
    logger.remove()

    with cli_environment(no_stdout=True, no_stderr=True):
        _pdk = get_pdk()
        register_cells()
        if not outpath:
            outpath = f"{cell}.lyrdb"
        sys.stderr.write(
            LVS_INFO_TEMPLATE.format(
                cell=cell, netpath=netpath, outpath=outpath, pdk=pdk
            )
        )
        cell_func = _pdk.cells.get(cell, None)
        if cell_func is None:
            msg = f"Cell {cell!r} not in PDK {pdk!r}."
            raise ValueError(msg)
        if not cellargs:  # noqa: SIM108
            _cell = cell_func()
        else:
            _cell = cell_func(**json.loads(cellargs))
        rdb = optical_lvs(
            cell=_cell,
            ref=netpath,
        )
        temppath = Path(tempfile.gettempdir()) / "lvs" / f"{secrets.token_hex(8)}.lyrdb"
        temppath.parent.mkdir(parents=True, exist_ok=True)
        rdb.save(filename=str(temppath))

        content = temppath.read_text()
        with suppress(PermissionError):
            temppath.unlink()
    sys.stderr.write("DONE!\n")
    print_to_file(outpath, content)
