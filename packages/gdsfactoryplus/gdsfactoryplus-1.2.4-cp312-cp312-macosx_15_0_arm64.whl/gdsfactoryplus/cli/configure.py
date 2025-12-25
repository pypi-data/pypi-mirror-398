"""Configure GDSFactory+."""

from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path
from urllib.parse import urlparse

import typer

from .app import app

__all__ = ["configure"]


@app.command()
def configure(
    api_key: str = "",
    organization: str = "",
    *,
    uv: bool = False,
    force: bool = False,
) -> None:
    """Configure a GDSFactory+ API key.

    Args:
        api_key: the api key to set
        organization: the name of your organization as registered with gdsfactoryplus
        uv: configure uv to use your gdsfactoryplus pypi index for proprietary packages
        force: force overwriting the api key if an existing key was found
    """
    import toml

    gdsfactory_dir = Path("~/.gdsfactory").expanduser().resolve()
    gdsfactory_dir.mkdir(parents=True, exist_ok=True)
    config_path = gdsfactory_dir / "gdsfactoryplus.toml"
    if config_path.is_dir():
        sys.stderr.write(f"{config_path} is a directory and should be a file.\n")
        raise typer.Exit(2)
    if config_path.is_file():
        try:
            with config_path.open("r") as f:
                config = toml.load(f)
        except Exception as e:
            sys.stderr.write(
                f"could not parse {config_path}. Please delete or fix it manually.\n"
            )
            raise typer.Exit(1) from e
    else:
        config = {}
    tool_config = config["tool"] = config.get("tool", {})
    gfp_config = tool_config["gdsfactoryplus"] = tool_config.get("gdsfactoryplus", {})

    api_config = gfp_config["api"] = gfp_config.get("api", {})
    if api_key:
        if not uv:
            _check_existing(config, "tool.gdsfactoryplus.api.key", force=force)
        api_config["key"] = api_key.strip()
    if organization:
        if not uv:
            _check_existing(config, "tool.gdsfactoryplus.api.nickname", force=force)
        api_config["nickname"] = organization.strip()

    if uv:
        configure_uv(api_config["key"], force=force)

    with config_path.open("w") as file:
        toml.dump(config, file)


def configure_uv(api_key: str, *, force: bool) -> None:
    import toml
    from httpx import get

    from gdsfactoryplus import settings

    api_host = settings.get_settings()["api"]["host"]
    parsed_url = urlparse(api_host)
    base_host = str(parsed_url.hostname)
    allowed_hosts = (
        "prod.gdsfactory.com",
        "dev.gdsfactory.com",
        "demo.gdsfactory.com",
        "trial.gdsfactory.com",
    )
    if base_host not in allowed_hosts:
        msg = (
            f"trying to validate access against the invalid host {base_host!r}. "
            "validating against 'prod.gdsfactory.com' instead."
        )
        warnings.warn(msg, stacklevel=1, category=RuntimeWarning)
        base_host = "prod.gdsfactory.com"

    uv_config_path = _get_uv_config_path()
    uv_config = toml.load(uv_config_path)
    uv_config["native-tls"] = True
    uv_config["allow-insecure-host"] = list(allowed_hosts)

    index_config = [
        c
        for c in uv_config.get("index", [])
        if c.get("url", "") != "https://pypi.org/simple"
    ]

    new_index_config = [{"name": "pypi", "url": "https://pypi.org/simple"}]

    dpd_config = None
    for i in range(len(index_config)):
        if index_config[i].get("name", "") == "dpd":
            dpd_config = index_config[i]
            index_config = [c for c in index_config if c.get("name", "") != "dpd"]
            break

    if force or (dpd_config is None) or (base_host not in dpd_config.get("url", "")):
        resp = get(f"https://{base_host}/api/verify-api-key?api_key={api_key}")
        data = resp.json()
        uuid = (
            data.get("organization_id", None)
            or "01660aaf-92f9-42a7-bd2d-0df7de79ce8b"  # "doplaydo"
        )
        dpd_config = {
            "name": "dpd",
            "url": f"https://user:{api_key}@devpi.{base_host}/{uuid}/private",
        }

    if dpd_config is not None:
        new_index_config.append(dpd_config)

    new_index_config.extend(index_config)

    if len(new_index_config) > 0:
        uv_config["index"] = new_index_config

    with uv_config_path.open("w") as file:
        toml.dump(uv_config, file)


def _check_existing(config: dict, full_key: str, *, force: bool) -> None:
    if force:
        return

    parts = full_key.split(".")

    try:
        # Navigate through the nested dictionary
        for part in parts[:-1]:
            config = config[part]

        existing = config.get(parts[-1], None)

        if existing is not None:
            existing_short = _format_api_key_short(existing)
            msg = (
                f"An existing configuration for '{full_key}' "
                f"was found: '{existing_short}'.\n Do you want to overwrite it? "
                "Choosing 'n' (no) will cancel all changes. [Y/n]: "
            )
            answer = input(msg)

            if answer.lower().strip() not in ("yes", "y", ""):
                sys.stdout.write("Aborted.\n")
                raise typer.Exit(0)
    except KeyError as e:
        msg = f"Error: The key '{full_key}' does not exist in the configuration.\n"
        sys.stdout.write(msg)
        raise typer.Exit(1) from e


def _get_uv_config_path() -> Path:
    if os.name == "nt":  # windows
        config_dir = (
            Path(os.environ.get("APPDATA", r"~\AppData\Roaming")).expanduser().resolve()
        )
    else:  # Mac Linux
        config_dir = (
            Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser().resolve()
        )
    config_path = config_dir / "uv" / "uv.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if not config_path.is_file():
        config_path.write_text("")
    return config_path


def _format_api_key_short(api_key: str, length: int = 10) -> str:
    return api_key if len(str(api_key)) < length else f"{str(api_key)[: length - 3]}..."
