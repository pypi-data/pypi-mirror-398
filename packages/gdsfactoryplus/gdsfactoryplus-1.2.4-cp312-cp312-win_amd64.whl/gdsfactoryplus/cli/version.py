"""Get the GDSFactory+ version."""

from __future__ import annotations

import sys

from .app import app

__all__ = ["version"]


@app.command()
def version() -> None:
    """Get the GDSFactory+ version."""
    import gdsfactoryplus.version as v

    sys.stdout.write(f"{v.__version__}\n")
