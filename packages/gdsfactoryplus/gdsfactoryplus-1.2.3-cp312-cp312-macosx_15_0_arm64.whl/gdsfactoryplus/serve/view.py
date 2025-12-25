"""GDS Viewer Additions to KWeb/DoWeb."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal

from fastapi import Request
from fastapi.responses import HTMLResponse

from .app import PDK, PROJECT_DIR, app

if TYPE_CHECKING:
    import doweb.api.viewer as doweb_viewer

    import gdsfactoryplus.core.pdk as gfp_pdk
else:
    from gdsfactoryplus.core.lazy import lazy_import

    doweb_viewer = lazy_import("doweb.api.viewer")
    gfp_pdk = lazy_import("gdsfactoryplus.core.pdk")


@app.get("/view2")
async def view2(
    request: Request,
    file: str,
    cell: str = "",
    theme: Literal["light", "dark"] = "dark",
    *,
    regen_lyp: bool = False,
    move_enabled: bool = True,
) -> HTMLResponse:
    """Alternative view specifically for GDSFactory+."""
    from fastapi.exceptions import HTTPException
    from fastapi.responses import HTMLResponse

    gds_path = Path(file).resolve()
    layer_props = PROJECT_DIR / "build" / "lyp" / f"{PDK}.lyp"
    if regen_lyp or not layer_props.is_file():
        _pdk = gfp_pdk.get_pdk()
        layer_views = _pdk.layer_views
        if layer_views is not None:
            if isinstance(layer_views, str | Path):
                layer_props = str(Path(layer_views).resolve())
            else:
                layer_views.to_lyp(filepath=layer_props)

    try:
        fv = doweb_viewer.FileView(
            file=gds_path,
            cell=cell or None,
            layer_props=str(layer_props),
            rdb=None,
        )
        resp = await doweb_viewer.file_view_static(request, fv)
    except HTTPException:
        color = "#f5f5f5" if theme == "light" else "#121317"
        return HTMLResponse(f'<body style="background-color: {color}"></body>')
    body = resp.body.decode()  # type: ignore[reportAttributeAccessIssue]
    body = _modify_body(body, theme, temp_rdb=False, move_enabled=move_enabled)
    return HTMLResponse(body)


def _modify_body(
    body: str,
    theme: str,
    *,
    temp_rdb: bool = False,
    move_enabled: bool = True,
) -> str:
    if theme == "light":
        body = body.replace('data-bs-theme="dark"', 'data-bs-theme="light"')
    body = body.replace(
        "</head>",
        """<style>
     [data-bs-theme=light] {{
       --bs-body-bg: #f5f5f5;
     }}
     [data-bs-theme=dark] {{
       --bs-body-bg: #121317;
     }}
   </style>
   <script src="/assets/js/view.js"></script>
   </head>""",
    ).replace(
        "</body>",
        f"""<script>
            // Initialize the GDS viewer with configuration
            if (window.gdsViewer) {{
                gdsViewer.initializeViewer(
                    {str(temp_rdb).lower()},
                    {str(move_enabled).lower()},
                    "{theme}"
                );
                gdsViewer.setupMessageListener();
            }} else {{
                console.error('GDS Viewer JavaScript not loaded');
            }}
        </script>
        </body>""",
    )
    return body.replace(" shadow ", " shadow-none ")
