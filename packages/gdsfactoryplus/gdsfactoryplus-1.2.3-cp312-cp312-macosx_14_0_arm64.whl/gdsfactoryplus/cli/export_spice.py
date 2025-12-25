"""Export a netlist to spice."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Literal, cast, get_args

import typer

from .app import app

__all__ = ["export_spice"]

FlavorType = Literal["spectre", "xyce", "ngspice"]


@app.command()
def export_spice(
    path: Annotated[str, typer.Argument()],
    outpath: str = "stdout",
    pdk: str = "",
    flavor: str = "spectre",
) -> None:
    """Export a .pic.yml netlist to spice.

    Args:
        path: the path to the .pic.yml file.
        outpath: where to save the spice file to
        pdk: the pdk context in which to parse the .pic.yml file
        flavor: the type of spice to export to
    """
    from ..core.export_spice import export_spice as _export_spice
    from ..core.pdk import register_cells
    from ..core.shared import cli_environment, print_to_file
    from ..logger import get_logger

    logger = get_logger()
    logger.remove()

    if pdk:
        sys.stderr.write("passing a pdk name is deprecated and will be ignored.\n")

    p = Path(path).expanduser().resolve()

    flavor = _validate_flavor(flavor)
    if not p.exists():
        msg = f"Path '{p}' does not exist.\n"
        sys.stderr.write(msg)
    if p.suffix not in (".gds", ".oas"):
        msg = f"Path '{p}' is not a GDS or OAS file.\n"
        sys.stderr.write(msg)
    if outpath != "stdout":
        outp = Path(outpath).expanduser().resolve()
        outp.parent.mkdir(parents=True, exist_ok=True)

    with cli_environment(no_stdout=False, no_stderr=False):
        register_cells()
        out = _export_spice(p, flavor)
    print_to_file(outpath, out)


def _validate_flavor(flavor: str) -> FlavorType:
    flavor = str(flavor).lower().strip()
    supported = get_args(FlavorType)
    if flavor not in supported:
        msg = f"Invalid flavor '{flavor}'. Supported export formats: {supported}.\n"
        sys.stderr.write(msg)
        raise typer.Exit(1)
    return cast("FlavorType", flavor)
