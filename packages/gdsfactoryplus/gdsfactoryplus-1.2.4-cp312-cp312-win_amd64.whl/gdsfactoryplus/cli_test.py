"""Test Component Builds."""

from __future__ import annotations

import inspect
import sys
from collections.abc import Generator
from typing import TYPE_CHECKING

from .cli.app import app

if TYPE_CHECKING:
    import pytest
    import typer

    import gdsfactoryplus.core.pdk as gfp_pdk
    import gdsfactoryplus.core.shared as gfp_shared
    import gdsfactoryplus.settings as gfp_settings
else:
    from gdsfactoryplus.core.lazy import lazy_import

    pytest = lazy_import("pytest")
    typer = lazy_import("typer")
    gfp_shared = lazy_import("gdsfactoryplus.core.shared")
    gfp_settings = lazy_import("gdsfactoryplus.settings")
    gfp_pdk = lazy_import("gdsfactoryplus.core.pdk")

__all__ = []

# Module-level variable to store cells to skip
_CELLS_TO_SKIP: set[str] = set()


@app.command(name="test")
def do_test(
    *,
    verbose: bool = typer.Option(
        False,  # noqa: FBT003
        "-v",
        help="Verbose output",
    ),
    no_capture: bool = typer.Option(
        False,  # noqa: FBT003
        "-s",
        help="Disable output capturing",
    ),
    keyword: str = typer.Option("", "-k", help="Run tests matching expression"),
    exitfirst: bool = typer.Option(
        False,  # noqa: FBT003
        "-x",
        help="Stop after first failure",
    ),
    skip: str = typer.Option("", help="Comma-separated list of cell names to skip"),
) -> None:
    """Test if the cells in the project can be built."""
    global _CELLS_TO_SKIP  # noqa: PLW0603

    from gdsfactoryplus.project import maybe_find_project_dir

    project_dir = maybe_find_project_dir()
    if project_dir is None:
        print(  # noqa: T201
            "Could not start tests. Please run tests inside a GDSFactory+ project.",
            file=sys.stderr,
        )
        raise typer.Exit(1)

    gfp_pdk.register_cells()

    # Parse skip list
    if skip:
        _CELLS_TO_SKIP = {cell.strip() for cell in skip.split(",") if cell.strip()}

    # Build pytest arguments
    pytest_args = [__file__]
    if verbose:
        pytest_args.append("-v")
    if no_capture:
        pytest_args.append("-s")
    if keyword:
        pytest_args.extend(["-k", keyword])
    if exitfirst:
        pytest_args.append("-x")

    exit_code = pytest.main(pytest_args)
    if exit_code != 0:
        raise typer.Exit(exit_code)


def _iter_cells() -> Generator[str]:
    yield from gfp_pdk.get_pdk().cells


@pytest.mark.parametrize("cell_name", _iter_cells())
def test_build(cell_name: str) -> None:
    """Test if a cell can be built."""
    # Skip if in skip list
    if cell_name in _CELLS_TO_SKIP:
        pytest.skip(f"Skipping {cell_name}: in skip list")

    # print(cell_name)
    func = gfp_pdk.get_pdk().cells[cell_name]

    # Skip functions that require arguments
    sig = inspect.signature(func)
    required_params = [
        p
        for p in sig.parameters.values()
        if p.default is inspect.Parameter.empty
        and p.kind != inspect.Parameter.VAR_KEYWORD
    ]

    if required_params:
        pytest.skip(
            f"Skipping {cell_name}: requires arguments "
            f"{[p.name for p in required_params]}"
        )

    func()
