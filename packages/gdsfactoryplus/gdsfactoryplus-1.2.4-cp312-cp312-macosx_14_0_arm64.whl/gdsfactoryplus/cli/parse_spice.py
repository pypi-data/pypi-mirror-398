"""Parse spice into a yaml netlist."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer

from .app import app

__all__ = ["parse_spice"]


@app.command()
def parse_spice(
    path: Annotated[str, typer.Argument()],
    outpath: str = "stdout",
    pdk: str = "",
    flavor: str = "oc",
) -> None:
    """Convert a spice netlist [.sp] to a GDSFactory netlist [.pic.yml].

    Args:
        path: path to convert
        outpath: the output path to output the converted netlist to
        pdk: PDK to use for the conversion.
        flavor: The spice flavor to use. Currently only 'oc' is supported.
    """
    from ..core.shared import cli_environment
    from ..logger import get_logger

    logger = get_logger()
    logger.remove()

    if pdk:
        sys.stderr.write("passing a pdk name is deprecated and will be ignored.\n")

    with cli_environment(no_stdout=True, no_stderr=True):
        import yaml

        from ..core.parse_spice import parse_oc_spice
        from ..core.pdk import register_cells
        from ..core.shared import cli_environment, print_to_file

        if flavor.lower().strip() != "oc":
            msg = (
                "Invalid spice flavor. "
                f"Currently only 'oc' is supported. Got: {flavor}.\n"
            )
            sys.stderr.write(msg)
            raise typer.Exit(1)
        if outpath.lower().strip() != "stdout":
            msg = "We can currently only output to stdout.\n"
            sys.stderr.write(msg)
            raise typer.Exit(1)
        p = Path(path).resolve()
        if not p.exists():
            sys.stderr.write(f"File {p} does not exist.\n")
            raise typer.Exit(1)
        register_cells()
        recnet = parse_oc_spice(p)
    yaml_str = yaml.safe_dump(recnet, sort_keys=False)
    print_to_file(outpath, yaml_str)
