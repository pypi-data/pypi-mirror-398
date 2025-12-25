"""General Show function."""

from __future__ import annotations

import io
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import kfactory as kf
    import matplotlib.pyplot as plt

    import gdsfactoryplus.models as m
    from gdsfactoryplus.core.communication import send_message
    from gdsfactoryplus.core.show_cell import show_cell
else:
    from gdsfactoryplus.core.lazy import lazy_import

    kf = lazy_import("kfactory")
    plt = lazy_import("matplotlib.pyplot")
    send_message = lazy_import("gdsfactoryplus.core.communication", "send_message")
    show_cell = lazy_import("gdsfactoryplus.core.show_cell", "show_cell")
    m = lazy_import("gdsfactoryplus.models")


def show(obj: Any = None, /) -> None:
    """Show the object in a human-readable format."""
    match obj:
        case None:
            if plt.get_fignums():
                buf = io.BytesIO()
                plt.gcf().savefig(
                    buf,
                    format="png",
                    bbox_inches="tight",
                )
                msg = m.ShowBytesMessage.from_buf(buf)
                send_message(msg)
            else:
                sys.stderr.write("No object to show.\n")
        case kf.ProtoTKCell():
            from gdsfactoryplus.logger import get_logger

            get_logger().debug(f"{obj}")
            show_cell(obj)
