"""Simulate a factory."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal, cast

import yaml

import gdsfactoryplus.models as m

if TYPE_CHECKING:
    import gdsfactory as gf
    import jax.numpy as jnp
    import sax

    import gdsfactoryplus.core.database as db
    from gdsfactoryplus.core.pdk import get_pdk, register_cells
    from gdsfactoryplus.logger import get_logger as log
else:
    from gdsfactoryplus.core.lazy import lazy_import

    sax = lazy_import("sax")
    jnp = lazy_import("jax.numpy")
    db = lazy_import("gdsfactoryplus.core.database")
    get_pdk = lazy_import("gdsfactoryplus.core.pdk", "get_pdk")
    register_cells = lazy_import("gdsfactoryplus.core.pdk", "register_cells")
    log = lazy_import("gdsfactoryplus.logger", "get_logger")


def get_schematic_recnet(name: str) -> dict:  # noqa: C901
    """Get a schematic record netlist.

    Args:
        name: name of the factory.

    Returns:
        recnet: recursive netlist.
    """
    recnet = {}
    pdk = get_pdk()
    register_cells()

    def _add_netlists(  # noqa: C901
        recnet: dict, prev_name: str, prev_inst_name: str, name: str, **kwargs: Any
    ) -> None:
        record = db.get_factories_by_name(name).get(name)
        if not record:
            msg = f"{name} not found in database!"
            raise ValueError(msg)
        source = record.absolute_source()
        if source is None:
            msg = f"Cell source for '{name}' not found in database."
            raise FileNotFoundError(msg)
        if str(source).endswith(".pic.yml"):
            recnet[name] = yaml.safe_load(source.read_text())
            nets = set()
            for p, q in recnet[name]["connections"].items():
                nets.add((p, q))
            for bundle in recnet[name]["routes"].values():
                for p, q in bundle.get("links", {}).items():
                    nets.add((p, q))
            recnet[name]["nets"] = recnet[name].get("nets", [])
            for p, q in nets:
                recnet[name]["nets"].append({"p1": p, "p2": q})
            recnet[name]["nets"] = tuple(recnet[name]["nets"])
            recnet[name] = {k: recnet[name][k] for k in ["nets", "instances", "ports"]}
        else:
            c = pdk.get_component(name, **kwargs)
            netlist = c.get_netlist()
            if not netlist["instances"]:
                return
            name = c.name
            recnet[name] = netlist
            recnet[prev_name]["instances"][prev_inst_name]["component"] = name

        for inst_name, inst in recnet[name]["instances"].items():
            if isinstance(inst, str):
                inst = {"component": inst}
            component = inst["component"]
            settings = cast(dict[str, Any], inst.get("settings", {}))
            _add_netlists(recnet, name, inst_name, component, **settings)

    _add_netlists(recnet, "", "", name)
    return recnet


def simulate(
    name: str,
    layout: dict[str, Any],
    model: dict[str, Any],
    how: Literal["from_layout", "from_netlist"] = "from_layout",
) -> sax.SType:
    """Simualate a factory.

    Args:
        name: Name of the cell to simulate.
        layout: Layout information for the cell.
        model: Model parameters for the simulation.
        how: Method to use for simulation, either "from_layout" or "from_netlist".

    Returns:
        sax.SType: The result of the simulation.
    """
    log().debug(f"{name=}\n{list(layout)=}\n{list(model)=}\n{how=}")
    sim = m.Simulation(name=name, layout=layout, model=model)

    record = db.get_factories_by_name(sim.name).get(sim.name)
    if not record or (src := record.absolute_source()) is None:
        msg = f"Cell '{sim.name}' not found in database."
        raise FileNotFoundError(msg)

    pdk = get_pdk()
    register_cells(paths=[src])
    if sim.name not in pdk.cells:
        msg = f"Cell '{sim.name}' not found in PDK."
        raise ValueError(msg)

    if how == "from_netlist":
        layout_info = sim.layout
    else:
        layout: gf.Component = pdk.get_component(sim.name, **sim.layout)
        layout_info = {
            **layout.info.model_dump(),
            **layout.settings.model_dump(),
        }

    model: Callable | None = pdk.models.get(sim.name)
    if model is not None:
        full_settings = {
            **layout_info,
            **sim.model,
        }
        settings = {
            k: v for k, v in full_settings.items() if k in sax.get_settings(model)
        }
        log().debug(
            f"{list(full_settings)=}\n{list(settings)=}\n{list(sax.get_settings(model))=}"
        )
        return model(**_arrayfy(settings))

    if how == "from_netlist":
        netlist = get_schematic_recnet(sim.name)
    else:
        netlist = layout.get_netlist(recursive=True)  # type: ignore[reportAttributeAccessIssue]

    if not netlist:
        msg = f"Cell '{sim.name}' is a base component (has no netlist) with no model."
        raise FileNotFoundError(msg)

    flat_net = next(iter(netlist.values()))
    if not flat_net.get("instances"):
        msg = f"Cell '{sim.name}' is a base component (has no instances) with no model."
        raise FileNotFoundError(msg)

    ports = flat_net.get("ports", {})
    if not ports:
        msg = f"Cell '{sim.name}' has no ports."
        raise ValueError(msg)
    if len(ports) < 2:
        msg = f"Cell '{sim.name}' has less than two ports."
        raise ValueError(msg)

    circuit, _ = sax.circuit(netlist, models=pdk.models)
    return circuit(**_arrayfy(sim.model))


def _arrayfy(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _arrayfy(v) for k, v in obj.items()}
    if isinstance(obj, list | float | int):
        return jnp.asarray(obj, dtype=float)
    return obj
