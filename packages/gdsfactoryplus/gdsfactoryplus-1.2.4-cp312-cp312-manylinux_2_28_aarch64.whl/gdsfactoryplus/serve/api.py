"""API module for the application."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

from fastapi import BackgroundTasks
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse

from .app import app, logger

if TYPE_CHECKING:
    import sax
    import yaml

    import gdsfactoryplus.core.bbox as bb
    import gdsfactoryplus.core.database as db
    import gdsfactoryplus.core.export_spice as spe
    import gdsfactoryplus.core.parse_spice as spp
    import gdsfactoryplus.core.pdk as gfp_pdk
    import gdsfactoryplus.models as m
    import gdsfactoryplus.simulate as s
    from gdsfactoryplus import settings
    from gdsfactoryplus.core import build, kcl
else:
    from gdsfactoryplus.core.lazy import lazy_import

    sax = lazy_import("sax")
    yaml = lazy_import("yaml")

    bb = lazy_import("gdsfactoryplus.core.bbox")
    db = lazy_import("gdsfactoryplus.core.database")
    spe = lazy_import("gdsfactoryplus.core.export_spice")
    spp = lazy_import("gdsfactoryplus.core.parse_spice")
    gfp_pdk = lazy_import("gdsfactoryplus.core.pdk")
    m = lazy_import("gdsfactoryplus.models")
    settings = lazy_import("gdsfactoryplus.settings")
    s = lazy_import("gdsfactoryplus.simulate")
    build = lazy_import("gdsfactoryplus.core.build")
    kcl = lazy_import("gdsfactoryplus.core.kcl")


@app.get("/tree")
def tree() -> dict:
    """Tree is used as health check."""
    return {}


def _build_cell(
    name: str, *, with_metadata: bool = True, register: bool = True
) -> None:
    """Build a GDS cell by name (background task).

    Args:
        name: Name of the cell to build.
        with_metadata: Whether to include metadata in the GDS file.
        register: Whether to re-register the cell in the KLayout cache.
    """
    paths = db.get_factory_sources_by_name(name)
    if register and paths:
        names, _ = gfp_pdk.register_cells(paths=paths.values())
        kcl.clear_cells_from_cache(*names)
    else:
        kcl.clear_cells_from_cache(name)
    build.build_by_names(name, with_metadata=with_metadata)


@app.get("/api/build-cell")
def build_cell(
    name: str,
    background_tasks: BackgroundTasks,
    *,
    with_metadata: bool = True,
    register: bool = True,
) -> dict:
    """Build a GDS cell by name.

    Args:
        name: Name of the cell to build.
        background_tasks: Fastapi background tasks
        with_metadata: Whether to include metadata in the GDS file.
        register: Whether to re-register the cell in the KLayout cache.
    """
    background_tasks.add_task(
        _build_cell, name, with_metadata=with_metadata, register=register
    )
    return {"detail": f"building {name} in background."}


def _build_cells(
    names: list[str],
    *,
    with_metadata: bool = True,
    register: bool = True,
) -> None:
    """Build multiple GDS cells by names (background task).

    Args:
        names: List of cell names to build.
        with_metadata: Whether to include metadata in the GDS files.
        register: Whether to re-register the cells in the KLayout cache.
    """
    logger.debug(f"{names}")
    paths = db.get_factory_sources_by_name(*names)
    if register and paths:
        registered_names, _ = gfp_pdk.register_cells(paths=paths.values())
        kcl.clear_cells_from_cache(*registered_names)
        names = list({*names, *registered_names})
    else:
        kcl.clear_cells_from_cache(*names)
    build.build_by_names(*names, with_metadata=with_metadata)


@app.post("/api/build-cells")
def build_cells(
    names: list[str],
    background_tasks: BackgroundTasks,
    *,
    with_metadata: bool = True,
    register: bool = True,
) -> dict:
    """Build multiple GDS cells by names.

    Args:
        names: List of cell names to build.
        background_tasks: Fastapi background tasks
        with_metadata: Whether to include metadata in the GDS files.
        register: Whether to re-register the cells in the KLayout cache.
    """
    background_tasks.add_task(
        _build_cells, names, with_metadata=with_metadata, register=register
    )
    return {"detail": f"building {len(names)} cells in background."}


@app.post("/api/simulate")
def simulate(
    sim: m.Simulation,
    how: Literal["from_layout", "from_netlist"] = "from_layout",
) -> m.SerializedSimulationResult | dict[str, str]:
    """Simulate a factory.

    Args:
        sim: Simulation object containing the name, layout, and model.
        how: Method to use for simulation, either "from_layout" or "from_netlist".

    Returns:
        SerializedSimulationResult: The result of the simulation, serialized.
    """
    try:
        sdict = sax.sdict(
            s.simulate(sim.name, layout=sim.layout, model=sim.model, how=how)
        )
        result: m.SerializedSimulationResult = {}
        for (p, q), v in sdict.items():
            if (abs(v) < 1e-7).all():
                continue
            if p not in result:
                result[p] = {}
            result[p][q] = m.SerializedComplexArray.from_numpy(v)
    except Exception as e:  # noqa: BLE001
        return {"detail": str(e)}
    return result


@app.get("/api/simulate")
def simulate_get(
    name: str,
) -> m.SerializedSimulationResult | dict[str, str]:
    """Simulate a factory.

    Args:
        name: name of the factory to simulate with default arguments.

    Returns:
        SerializedSimulationResult: The result of the simulation, serialized.
    """
    return simulate(m.Simulation(name=name, layout={}, model={}))


@app.post("/api/parse-spice")
def parse_spice_api(request: m.ParseSpiceRequest) -> dict[str, str]:
    """Parse a SPICE file to YAML format.

    Args:
        request: ParseSpiceRequest containing path and flavor.

    Returns:
        dict: Either {'content': yaml_string} on success
            or {'detail': error_message} on error.
    """
    try:
        logger.info(
            f"Parse SPICE API called with path: {request.path}, "
            f"flavor: {request.flavor}"
        )

        if request.flavor.lower().strip() != "oc":
            error_msg = (
                f"Invalid spice flavor. Currently only 'oc' is supported."
                f" Got: {request.flavor}."
            )
            logger.warning(error_msg)
            return {"detail": error_msg}

        file_path = Path(request.path).expanduser().resolve()
        logger.info(f"Resolved file path: {file_path}")

        if not file_path.exists():
            error_msg = f"File {file_path} does not exist."
            logger.error(error_msg)
            return {"detail": error_msg}

        if file_path.suffix.lower() not in (".sp", ".spice"):
            error_msg = f"File {file_path} is not a SPICE file (.sp or .spice)."
            logger.error(error_msg)
            return {"detail": error_msg}

        logger.info("Registering cells...")
        # Register cells before parsing
        gfp_pdk.register_cells()

        logger.info("Parsing SPICE file...")
        # Parse the SPICE file
        recnet = spp.parse_oc_spice(file_path)

        logger.info(f"Parsed netlist type: {type(recnet)}")
        logger.info(
            f"Parsed netlist keys: {
                list(recnet.keys()) if isinstance(recnet, dict) else 'Not a dict'
            }"
        )

        logger.info("Converting to YAML...")
        yaml_str = yaml.safe_dump(recnet, sort_keys=False)
        logger.info(f"Generated YAML length: {len(yaml_str)}")

    except Exception as e:  # noqa: BLE001
        error_msg = f"SPICE parsing failed: {e!s}"
        logger.error(error_msg)
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception args: {e.args}")
        return {"detail": error_msg}

    else:
        return {"content": yaml_str}


@app.post("/api/export-spice")
def export_spice_api(request: m.ExportSpiceRequest) -> dict[str, str]:
    """Export a GDS file to SPICE format.

    Args:
        request: ExportSpiceRequest containing path and flavor.

    Returns:
        dict: Either {'content': spice_string} on success
            or {'detail': error_message} on error.
    """
    try:
        # Validate flavor
        supported_flavors = ["spectre", "xyce", "ngspice"]
        flavor = request.flavor.lower().strip()
        if flavor not in supported_flavors:
            return {
                "detail": f"Invalid flavor '{flavor}'. "
                f"Supported export formats: {supported_flavors}."
            }

        file_path = Path(request.path).expanduser().resolve()
        if not file_path.exists():
            return {"detail": f"File {file_path} does not exist."}

        if file_path.suffix.lower() not in (".gds", ".oas"):
            return {"detail": f"File {file_path} is not a GDS or OAS file."}

        # Register cells before exporting
        gfp_pdk.register_cells()

        # Export to SPICE
        spice_content = spe.export_spice(file_path, cast(spe.SpiceFlavor, flavor))

    except Exception as e:  # noqa: BLE001
        logger.error(f"SPICE export failed: {e}")
        return {"detail": f"SPICE export failed: {e!s}"}

    else:
        return {"content": spice_content}


@app.get("/api/port-center")
def port_center(netlist: str, instance: str, port: str) -> dict[str, float]:
    """Get the center coordinates of a port in a netlist."""
    c = gfp_pdk.get_pdk().get_component(netlist)
    x, y = c.insts[instance].ports[port].center
    return {"x": x, "y": y}


@app.post("/api/bbox")
def bbox_api(request: m.BboxRequest) -> dict[str, str]:
    """Generate a bounding box GDS file from an input GDS.

    Args:
        request: BboxRequest containing path and bbox parameters.

    Returns:
        dict: Either {'outpath': output_file_path} on success
            or {'detail': error_message} on error.
    """
    try:
        file_path = Path(request.path).expanduser().resolve()
        if not file_path.exists():
            return {"detail": f"File {file_path} does not exist."}

        if file_path.suffix.lower() not in (".gds", ".oas"):
            return {"detail": f"File {file_path} is not a GDS or OAS file."}

        # Register cells before processing
        gfp_pdk.register_cells()

        # Call the bbox function
        bb.bbox(
            str(file_path),
            request.outpath,
            request.layers_to_keep,
            request.bbox_layer,
            ignore_ports=request.ignore_ports,
        )

        # Return the output path (bbox function handles default naming if outpath empty)
        if request.outpath:
            outpath = Path(request.outpath).expanduser().resolve()
        else:
            # Use the same logic as in bbox._validate_args for default naming
            ext = "gds" if file_path.suffix.lower() == ".gds" else "oas"
            outpath = file_path.with_suffix(f"-bbox.{ext}")

    except Exception as e:  # noqa: BLE001
        logger.error(f"Bbox generation failed: {e}")
        return {"detail": f"Bbox generation failed: {e!s}"}

    else:
        return {"outpath": str(outpath)}


@app.get("/api/download/{path:path}.gds")
def download_gds(path: str, background_tasks: BackgroundTasks) -> FileResponse:
    """Download a GDS file from the project directory.

    Args:
        path: Relative path to the GDS file (without .gds extension).
        background_tasks: FastAPI background tasks for async operations.

    Returns:
        FileResponse: The GDS file as an octet-stream download.
    """
    parts = Path(path).parts
    is_build_path = (parts[0] == "build") and (parts[1] == "gds")
    with_metadata = parts[2] != "no-meta"

    project_dir = settings.get_project_dir()
    file_path = (project_dir / f"{path}.gds").resolve()
    if not file_path.is_relative_to(project_dir):
        logger.error(f"Path traversal attempt: {path}")
        raise HTTPException(status_code=403, detail="Forbidden: Invalid file path.")

    if not file_path.exists() and is_build_path:
        cell_name = parts[-1]
        build_cell(
            cell_name, background_tasks, with_metadata=with_metadata, register=False
        )

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"File {file_path} not found.")

    if file_path.suffix.lower() != ".gds":
        logger.error(f"Not a GDS file: {file_path}")
        raise HTTPException(
            status_code=400, detail=f"File {file_path} is not a GDS file."
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/octet-stream",
        filename=file_path.name,
    )
