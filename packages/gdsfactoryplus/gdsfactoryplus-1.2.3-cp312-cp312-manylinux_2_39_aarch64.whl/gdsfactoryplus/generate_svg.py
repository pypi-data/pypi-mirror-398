"""Generate SVG from cell."""

from __future__ import annotations

import warnings
from collections.abc import Iterable
from functools import cache, partial
from inspect import signature
from typing import TYPE_CHECKING, Any, NamedTuple, cast

if TYPE_CHECKING:
    import gdsfactory as gf
    import numpy as np
    import shapely.geometry as sg

    from gdsfactoryplus.core.pdk import get_pdk
else:
    from gdsfactoryplus.core.lazy import lazy_import

    get_pdk = lazy_import("gdsfactoryplus.core.pdk", "get_pdk")
    gf = lazy_import("gdsfactory")
    np = lazy_import("numpy")
    sg = lazy_import("shapely.geometry")

__all__ = ["get_svg", "generate_svg", "generate_multipolygon"]


class _BBox(NamedTuple):
    north: float
    east: float
    south: float
    west: float

    def width(self) -> float:
        return self.east - self.west  # negative width allowed!

    def height(self) -> float:
        return self.north - self.south  # negative height allowed!


def generate_svg(
    comp: gf.Component,
    width: int,
    height: int,
    theme: str = "dark",
) -> str:
    """Generate the svg for a cell."""
    mp = generate_multipolygon(comp)
    mp = _simplify_multi_polygon(mp, eps=0.05)
    mp = _normalize_multi_polygon(mp, _get_bbox(mp), _BBox(0, width, height, 0))
    ds = _svg_strings_from_multi_polygon(mp)
    return _svg_from_svg_strings(ds, width, height, theme=theme)


@cache
def get_svg(
    comp: gf.Component,
    width: int,
    height: int,
    theme: str = "dark",
) -> str:
    """Get the (possible cached) svg for a cell."""
    return generate_svg(comp, width, height, theme)


def generate_multipolygon(
    comp: gf.Component,
) -> sg.MultiPolygon:
    """Generate a MultiPolygon from a component."""
    polys_dict = comp.get_polygons_points(by="tuple")
    layer = _get_main_pdk_layer()
    poly_arrays = polys_dict.get(layer, [])
    mp = sg.MultiPolygon([sg.Polygon(p) for p in poly_arrays]).buffer(0.01)
    if isinstance(mp, sg.Polygon):
        mp = sg.MultiPolygon([mp])
    return mp


def _simplify_multi_polygon(
    mp: sg.MultiPolygon,
    eps: float,
) -> sg.MultiPolygon:
    geoms = []
    for _poly in mp.geoms:
        if not isinstance(_poly, sg.Polygon):
            continue
        poly = _simplify_polygon(_poly, eps)
        geoms.append(poly)
    return sg.MultiPolygon(geoms)


def _normalize_multi_polygon(
    mp: sg.MultiPolygon,
    bbox_in: _BBox,
    bbox_out: _BBox,
) -> sg.MultiPolygon:
    geoms = []
    for _poly in mp.geoms:
        if not isinstance(_poly, sg.Polygon):
            continue
        poly = _normalize_polygon(_poly, bbox_in, bbox_out)
        geoms.append(poly)
    return sg.MultiPolygon(geoms)


def _simplify_polygon(
    poly: sg.Polygon,
    eps: float,
) -> sg.Polygon:
    boundary = poly.boundary
    if not isinstance(boundary, sg.MultiLineString):
        boundary = sg.MultiLineString([boundary])
    boundary = _simplify_multi_line_string(boundary, eps)
    geoms = list(boundary.geoms)
    return sg.Polygon(geoms[0], geoms[1:])


def _normalize_polygon(
    poly: sg.Polygon,
    bbox_in: _BBox,
    bbox_out: _BBox,
) -> sg.Polygon:
    boundary = poly.boundary
    if not isinstance(boundary, sg.MultiLineString):
        boundary = sg.MultiLineString([boundary])
    boundary = _normalize_multi_line_string(boundary, bbox_in, bbox_out)
    geoms = list(boundary.geoms)
    return sg.Polygon(geoms[0], geoms[1:])


def _simplify_multi_line_string(
    mls: sg.MultiLineString,
    eps: float,
) -> sg.MultiLineString:
    geoms = []
    for _ls in mls.geoms:
        if not isinstance(_ls, sg.LineString):
            continue
        ls = _simplify_line_string(_ls, eps)
        geoms.append(ls)
    return sg.MultiLineString(geoms)


def _normalize_multi_line_string(
    mls: sg.MultiLineString,
    bbox_in: _BBox,
    bbox_out: _BBox,
) -> sg.MultiLineString:
    geoms = []
    for _ls in mls.geoms:
        if not isinstance(_ls, sg.LineString):
            continue
        ls = _normalize_line_string(_ls, bbox_in, bbox_out)
        geoms.append(ls)
    return sg.MultiLineString(geoms)


def _simplify_line_string(
    ls: sg.LineString,
    eps: float,
) -> sg.LineString:
    arr = _simplify_array(np.array(list(ls.coords)), eps)
    return sg.LineString(arr)


def _normalize_line_string(
    ls: sg.LineString,
    bbox_in: _BBox,
    bbox_out: _BBox,
) -> sg.LineString:
    arr = _normalize_array(np.array(list(ls.coords)), bbox_in, bbox_out)
    return sg.LineString(arr)


def _simplify_array(
    arr: np.ndarray,
    eps: float,
) -> np.ndarray:
    return _rdp(arr, eps)


def _normalize_array(
    arr: np.ndarray,
    bbox_in: _BBox,
    bbox_out: _BBox,
) -> np.ndarray:
    x0, y0 = arr.T
    x1 = (x0 - bbox_in.west) / bbox_in.width() * bbox_out.width() + bbox_out.west
    y1 = (y0 - bbox_in.south) / bbox_in.height() * bbox_out.height() + bbox_out.south
    return np.stack([x1, y1], axis=1)


def _rdp(
    poly: np.ndarray,
    eps: float,
) -> np.ndarray:
    poly = np.asarray(poly)
    if not poly.shape:
        return np.array([])
    if poly.shape[0] < 3:
        return poly
    start, end = poly[0], poly[-1]
    dists = _line_dists(poly, start, end)

    index = np.argmax(dists)
    dmax = dists[index]

    if dmax > eps:
        result1 = _rdp(poly[: index + 1], eps=eps)
        result2 = _rdp(poly[index:], eps=eps)
        result = np.vstack((result1[:-1], result2))
    else:
        result = np.array([start, end])

    return result


def _line_dists(
    points: np.ndarray,
    start: int,
    end: int,
) -> np.ndarray:
    if np.all(start == end):
        return np.linalg.norm(points - start, axis=1)
    vec = end - start
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        cross = np.cross(vec, start - points)
    return np.divide(abs(cross), np.linalg.norm(vec))


def _svg_string_from_line_string(
    ls: sg.LineString,
) -> str:
    iter_coords = iter(ls.coords)
    (x0, y0) = next(iter_coords)
    s = f"M {x0:.3f} {y0:.3f} "
    for x, y in iter_coords:
        s += f"L {x:.3f} {y:.3f} "
    s += "Z"
    return s


def _svg_string_from_multi_line_string(
    mls: sg.MultiLineString,
) -> str:
    s = ""
    for ls in mls.geoms:
        s += _svg_string_from_line_string(ls) + " "
    return s.strip()


def _svg_string_from_polygon(
    poly: sg.Polygon,
) -> str:
    boundary = poly.boundary
    if not isinstance(boundary, sg.MultiLineString):
        boundary = sg.MultiLineString([boundary])
    return _svg_string_from_multi_line_string(boundary)


def _svg_strings_from_multi_polygon(
    mp: sg.MultiPolygon,
) -> list[str]:
    return [_svg_string_from_polygon(poly) for poly in mp.geoms]


def _get_bbox(
    mp: sg.MultiPolygon,
    padding: float = 1.0,
) -> _BBox:
    west, south, east, north = mp.bounds
    return _BBox(
        north=max(north, south) + padding,
        east=max(east, west) + padding,
        south=min(north, south) - padding,
        west=min(east, west) - padding,
    )


def _path_from_svg_string(
    path_string: str,
    path_id: str,
    theme: str = "dark",
) -> str:
    stroke_color = "#ffffff" if theme == "dark" else "#000000"
    template = (
        '<path d="{path_string}" id="{path_id}" '
        'style="fill:none;fill-opacity:0;stroke:{stroke_color};'
        'stroke-dasharray:none;stroke-opacity:1" />'
    )
    return template.format(
        path_string=path_string, path_id=path_id, stroke_color=stroke_color
    )


def _svg_from_svg_strings(
    path_strings: list[str],
    width: int,
    height: int,
    theme: str = "dark",
) -> str:
    template = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   width="{width}"
   height="{height}"
   viewBox="0 0 {width} {height}"
   version="1.1"
   id="svg1"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:svg="http://www.w3.org/2000/svg">
  <defs
     id="defs1" />
  <g
     id="icon">
    <rect
       style="fill:none;fill-opacity:0;stroke:none;stroke-opacity:0.165761"
       id="frame"
       width="{width1}"
       height="{height1}"
       x="0.5"
       y="0.5" />
       {paths}
  </g>
</svg>"""
    paths = ""
    for i, path_string in enumerate(path_strings):
        paths += _path_from_svg_string(path_string, f"poly{i}", theme=theme) + r"\n"
    return template.format(
        paths=paths, width=width, height=height, width1=width - 1, height1=height - 1
    )


@cache
def _get_main_pdk_layer() -> tuple[int, int]:
    pdk = get_pdk()
    layers = {str(l).upper(): tuple(l) for l in (cast(Iterable, pdk.layers) or {})}
    layer = _get_main_cross_section_layer(pdk)
    if isinstance(layer, tuple):
        return layer[:2]
    layer = layers.get(str(layer).upper())
    if layer is not None:
        return layer
    layers_sel = {k: v for k, v in layers.items() if k.endswith("WG")}
    if layers_sel:
        return next(iter(layers_sel.values()))
    layers_sel = {k: v for k, v in layers.items() if "WG" in k}
    if layers_sel:
        return next(iter(layers_sel.values()))
    return (1, 0)


def _get_main_cross_section_layer(pdk: gf.Pdk) -> Any:
    cross_section = _get_main_cross_section(pdk)
    if cross_section is None:
        return None
    for section in cross_section.sections:
        if section.layer is None:
            continue
        return section.layer
    return None


def _get_main_cross_section(pdk: gf.Pdk) -> gf.CrossSection | None:
    cross_section_name = _get_main_cross_section_name(pdk)
    if not cross_section_name:
        return None
    return pdk.get_cross_section(cross_section_name)


def _get_main_cross_section_name(pdk: gf.Pdk) -> str:
    routing_strategies = pdk.routing_strategies or {}
    if "route_bundle" not in routing_strategies:
        route_bundle = next(iter(routing_strategies.values()))
    else:
        route_bundle = routing_strategies["route_bundle"]
    if not isinstance(route_bundle, partial):
        sig = signature(route_bundle)
        param = sig.parameters.get("cross_section", None)
        if param is None:
            return ""
        if isinstance(param.default, param.empty):
            return ""
        return param.default
    return route_bundle.keywords.get("cross_section", "")
