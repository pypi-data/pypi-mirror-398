"""GDSFactory+ Pydantic models."""

from __future__ import annotations

import ast
import base64
import json
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    BinaryIO,
    Literal,
    Self,
    TypeAlias,
    cast,
)

import pydantic as pyd

if TYPE_CHECKING:
    import kfactory as kf
    import networkx as nx
    import numpy as np
    import sax.saxtypes.core as st

    from gdsfactoryplus.settings import get_project_dir
else:
    from gdsfactoryplus.core.lazy import lazy_import

    nx = lazy_import("networkx")
    st = lazy_import("sax.saxtypes.core")
    np = lazy_import("numpy")
    kf = lazy_import("kfactory")
    get_project_dir = lazy_import("gdsfactoryplus.settings", "get_project_dir")

__all__ = []

LogLevel: TypeAlias = Literal["debug", "info", "warning", "error"]

PdkType: TypeAlias = Literal["pdk", "base_pdk"]


class User(pyd.BaseModel):
    """A GDSFactory+ user."""

    user_name: str
    email: str
    organization_name: str | None
    organization_id: str | None
    pdks: list[str] | None
    is_superuser: bool


class SerializedComplexArray(pyd.BaseModel):
    """A serialized complex numpy array."""

    real: list[float]
    imag: list[float]

    def to_numpy(self) -> np.ndarray:
        """Convert to a complex number."""
        return np.array(self.real) + 1j * np.array(self.imag)

    @classmethod
    def from_numpy(cls, arr: st.ComplexArray) -> Self:
        """Create from a complex numpy array."""
        npa = np.atleast_1d(np.asarray(arr, dtype=np.complex128))
        if npa.ndim != 1:
            msg = "Input array must be one-dimensional."
            raise ValueError(msg)
        return cls(
            real=cast(list[float], np.real(npa).tolist()),
            imag=cast(list[float], np.imag(npa).tolist()),
        )


SimulationResult: TypeAlias = dict[str, dict[str, "st.ComplexArray"]]
SerializedSimulationResult: TypeAlias = dict[str, dict[str, SerializedComplexArray]]


def yaml_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return ast.literal_eval(value)
    except Exception:  # noqa: BLE001
        return value


def yaml_values(values: dict[str, Any]) -> dict[str, Any]:
    """Convert YAML values in a dictionary to their appropriate types."""
    return {k: yaml_value(v) for k, v in values.items()}


class Simulation(pyd.BaseModel):
    """A SAX simulation configuration."""

    name: str
    layout: Annotated[dict[str, Any], pyd.AfterValidator(yaml_values)]
    model: Annotated[dict[str, Any], pyd.AfterValidator(yaml_values)]


class ComponentRequest(pyd.BaseModel):
    """A request for port information."""

    name: str
    settings: dict[str, Any]


class ModelRecord(pyd.BaseModel):
    """A model record for the database."""

    factory: str
    settings: str
    source: str
    pdk_type: PdkType = "pdk"
    status: str = "UNKNOWN"
    message: str = ""

    def absolute_source(self) -> Path:
        """Return the absolute path to the source file."""
        if Path(self.source).is_absolute():
            return Path(self.source).resolve()

        return (get_project_dir() / self.source).resolve()

    def to_db_tuple(self) -> tuple:
        """Convert to tuple for database insertion."""
        return (
            self.factory,
            self.settings,
            self.source,
            self.pdk_type,
            self.status,
            self.message,
        )

    def __hash__(self) -> int:
        """Return hash of the model record for deduplication."""
        return hash(
            (
                self.factory,
                tuple(sorted(json.loads(self.settings).items())),
                self.source,
                self.pdk_type,
                self.status,
                self.message,
            )
        )

    def __eq__(self, other: object) -> bool:
        """Check equality for deduplication."""
        if not isinstance(other, ModelRecord):
            return False
        return hash(self) == hash(other)


class FactoryRecord(pyd.BaseModel):
    """A factory record for the database."""

    name: str
    source: str
    status: str
    message: str
    default_settings: str = "{}"
    pdk_type: PdkType = "pdk"
    parents: str = "[]"
    children: str = "[]"
    is_partial: bool = False
    has_model: bool = False
    tags: str = "[]"
    ignored_sources: str = "[]"
    last_updated: str = ""  # Will be set automatically by database

    @classmethod
    def from_callgraph(
        cls, G: nx.DiGraph, name: str, status: str = "UNKNOWN", message: str = ""
    ) -> Self:
        props = G.nodes[name]

        def _relpath(source: str | Path) -> str:
            return str(
                Path(source).resolve().relative_to(get_project_dir(), walk_up=True)
            )

        return cls(
            name=props["short_name"],
            source=_relpath(props["source"]),
            status=status,
            message=message,
            default_settings=json.dumps(props["default_settings"]),
            pdk_type=props["pdk_type"],
            parents=json.dumps(list(nx.ancestors(G, props["short_name"]))),
            children=json.dumps(list(nx.descendants(G, props["short_name"]))),
            is_partial=props["is_partial"],
            tags=json.dumps(props["tags"]),
            ignored_sources=json.dumps([_relpath(p) for p in props["other_sources"]]),
            has_model=False,
            last_updated="",
        )

    def absolute_source(self) -> Path:
        """Return the absolute path to the source file."""
        if Path(self.source).is_absolute():
            return Path(self.source).resolve()

        return (get_project_dir() / self.source).resolve()

    def absolute_ignored_sources_list(self) -> list[Path]:
        result = []
        for p in self.ignored_sources_list():
            if Path(p).is_absolute():
                result.append(Path(p).resolve())
            else:
                result.append((get_project_dir() / p).resolve())
        return result

    def default_settings_dict(self) -> dict[str, Any]:
        """Return the default settings as a dictionary."""
        return json.loads(self.default_settings)

    def parents_list(self) -> list[str]:
        """Return the parents as a list."""
        return json.loads(self.parents)

    def children_list(self) -> list[str]:
        """Return the children as a list."""
        return json.loads(self.children)

    def tags_list(self) -> list[str]:
        """Return the tags as a list."""
        return json.loads(self.tags)

    def ignored_sources_list(self) -> list[str]:
        """Return the ignored_sources as a list."""
        return json.loads(self.ignored_sources)

    def to_db_tuple(self) -> tuple:
        """Convert to tuple for database insertion, excl. has_model and last_updated."""
        return (
            self.name,
            self.source,
            self.status,
            self.message,
            self.default_settings,
            self.pdk_type,
            self.parents,
            self.children,
            self.is_partial,
            self.tags,
            self.ignored_sources,
        )

    def __hash__(self) -> int:
        """Return hash of the factory record for deduplication."""
        return hash(
            (
                self.name,
                self.source,
                self.status,
                self.message,
                tuple(sorted(json.loads(self.default_settings).items())),
                self.pdk_type,
                tuple(sorted(json.loads(self.parents))),
                tuple(sorted(json.loads(self.children))),
                self.is_partial,
                self.has_model,
                tuple(sorted(json.loads(self.tags))),
                tuple(sorted(json.loads(self.ignored_sources))),
            )
        )

    def __eq__(self, other: object) -> bool:
        """Check equality for deduplication."""
        if not isinstance(other, FactoryRecord):
            return False
        return hash(self) == hash(other)


class ComponentRecord(pyd.BaseModel):
    """A component record for the database."""

    name: str
    factory_name: str  # foreign key
    ports: str
    settings: str
    info: str

    def ports_list(self) -> list[str]:
        """Return the ports as a list."""
        return json.loads(self.ports)

    def settings_dict(self) -> dict[str, Any]:
        """Return the settings as a dictionary."""
        return json.loads(self.settings)

    def info_dict(self) -> dict[str, Any]:
        """Return the info as a dictionary."""
        return json.loads(self.info)

    def to_db_tuple(self) -> tuple:
        """Convert to tuple for database insertion."""
        return (
            self.name,
            self.factory_name,
            self.ports,
            self.settings,
            self.info,
        )

    def __hash__(self) -> int:
        """Return hash of the component record for deduplication."""
        return hash(
            (
                self.name,
                self.factory_name,
                tuple(sorted(json.loads(self.ports))),
                tuple(sorted(json.loads(self.settings).items())),
                tuple(sorted(json.loads(self.info).items())),
            )
        )

    def __eq__(self, other: object) -> bool:
        """Check equality for deduplication."""
        if not isinstance(other, ComponentRecord):
            return False
        return hash(self) == hash(other)

    @classmethod
    def from_tkcell(cls, tkcell: Any) -> Self:
        """Create a ComponentRecord from a TKCell object."""
        ports = object.__getattribute__(tkcell, "ports")
        port_names = json.dumps([str(p.name) for p in ports])
        factory_name = (
            getattr(tkcell, "basename", "")
            or getattr(tkcell, "function_name", "")
            or ""
        )
        default_settings = kf.KCellSettings()
        settings = getattr(tkcell, "settings", default_settings).model_dump_json()
        info = getattr(tkcell, "info", default_settings).model_dump_json()
        return cls(
            name=tkcell.name,
            factory_name=factory_name,
            ports=port_names,
            settings=settings,
            info=info,
        )


class Show3dMessage(pyd.BaseModel):
    """A message to vscode to show a 3D view."""

    what: Literal["show3D"] = "show3D"
    content: str

    def __hash__(self) -> int:
        """Return hash of the message for deduplication."""
        return hash((self.what, self.content))

    def __eq__(self, other: object) -> bool:
        """Check equality for deduplication."""
        if not isinstance(other, Show3dMessage):
            return False
        return self.what == other.what and self.content == other.content


class ReloadSchematicMessage(pyd.BaseModel):
    """A message to vscode to trigger a schematic reload."""

    what: Literal["reloadSchematic"] = "reloadSchematic"
    path: str

    def __hash__(self) -> int:
        """Return hash of the message for deduplication."""
        return hash((self.what, self.path))

    def __eq__(self, other: object) -> bool:
        """Check equality for deduplication."""
        if not isinstance(other, ReloadSchematicMessage):
            return False
        return self.what == other.what and self.path == other.path


class ReloadFactoriesMessage(pyd.BaseModel):
    """A message to vscode to trigger a pics tree reload."""

    what: Literal["reloadFactories"] = "reloadFactories"

    def __hash__(self) -> int:
        """Return hash of the message for deduplication."""
        return hash(self.what)

    def __eq__(self, other: object) -> bool:
        """Check equality for deduplication."""
        if not isinstance(other, ReloadFactoriesMessage):
            return False
        return self.what == other.what


class RestartServerMessage(pyd.BaseModel):
    """A message to vscode to trigger a server restart."""

    what: Literal["restartServer"] = "restartServer"

    def __hash__(self) -> int:
        """Return hash of the message for deduplication."""
        return hash(self.what)

    def __eq__(self, other: object) -> bool:
        """Check equality for deduplication."""
        if not isinstance(other, RestartServerMessage):
            return False
        return self.what == other.what


class ReloadLayoutMessage(pyd.BaseModel):
    """A message to vscode to trigger a gds viewer reload."""

    what: Literal["reloadLayout"] = "reloadLayout"
    cell: str

    def __hash__(self) -> int:
        """Return hash of the message for deduplication."""
        return hash((self.what, self.cell))

    def __eq__(self, other: object) -> bool:
        """Check equality for deduplication."""
        if not isinstance(other, ReloadLayoutMessage):
            return False
        return self.what == other.what and self.cell == other.cell


class LogMessage(pyd.BaseModel):
    """A message to vscode to log a message."""

    what: Literal["log"] = "log"
    level: LogLevel
    message: str
    source: str = "server"

    def __hash__(self) -> int:
        """Return hash of the message for deduplication."""
        return hash((self.what, self.level, self.message))

    def __eq__(self, other: object) -> bool:
        """Check equality for deduplication."""
        if not isinstance(other, LogMessage):
            return False
        return (
            self.what == other.what
            and self.level == other.level
            and self.message == other.message
        )


class ParseSpiceRequest(pyd.BaseModel):
    """Request model for parsing SPICE files."""

    path: str
    flavor: str = "oc"


class ExportSpiceRequest(pyd.BaseModel):
    """Request model for exporting GDS files to SPICE format."""

    path: str
    flavor: str = "spectre"


class BboxRequest(pyd.BaseModel):
    """Request model for generating bounding box GDS files."""

    path: str
    outpath: str = ""
    layers_to_keep: list[str] = []
    bbox_layer: tuple[int, int] = (99, 0)
    ignore_ports: bool = False


class ShowBytesMessage(pyd.BaseModel):
    """A message to send raw bytes to the client."""

    what: Literal["showBytes"] = "showBytes"
    content: str  # base64 encoded content
    name: str | None = None

    def __hash__(self) -> int:
        """Return hash of the message for deduplication."""
        return hash((self.what, self.content, self.name))

    def __eq__(self, other: object) -> bool:
        """Check equality for deduplication."""
        if not isinstance(other, ShowBytesMessage):
            return False
        return (
            self.what == other.what
            and self.content == other.content
            and self.name == other.name
        )

    @classmethod
    def from_bytes(cls, content: bytes, name: str | None = None) -> Self:
        """Create a ShowBytesMessage from raw bytes."""
        encoded_content = base64.b64encode(content).decode()
        return cls(content=encoded_content, name=name)

    @classmethod
    def from_buf(cls, buf: BinaryIO, name: str | None = None) -> Self:
        """Create a ShowBytesMessage from a BytesIO buffer."""
        buf.seek(0)
        content = buf.read()
        return cls.from_bytes(content, name)


class ShowGdsMessage(pyd.BaseModel):
    """A message to vscode to show a GDS file."""

    what: Literal["showGds"] = "showGds"
    gds: str
    lyrdb: str | None = None

    def __hash__(self) -> int:
        """Return hash of the message for deduplication."""
        return hash((self.what, self.gds, self.lyrdb))

    def __eq__(self, other: object) -> bool:
        """Check equality for deduplication."""
        if not isinstance(other, ShowGdsMessage):
            return False
        self_path = str(Path(self.gds).resolve())
        other_path = str(Path(other.gds).resolve())
        self_lyrdb = None if self.lyrdb is None else str(Path(self.lyrdb).resolve())
        other_lyrdb = None if other.lyrdb is None else str(Path(other.lyrdb).resolve())
        return (
            self.what == other.what
            and self_path == other_path
            and self_lyrdb == other_lyrdb
        )


class StartupStatusMessage(pyd.BaseModel):
    """A message to vscode to update startup status in factories view."""

    what: Literal["startupStatus"] = "startupStatus"
    message: str

    def __hash__(self) -> int:
        """Return hash of the message for deduplication."""
        return hash((self.what, self.message))

    def __eq__(self, other: object) -> bool:
        """Check equality for deduplication."""
        if not isinstance(other, StartupStatusMessage):
            return False
        return self.what == other.what and self.message == other.message


class ShutdownStatusMessage(pyd.BaseModel):
    """A message to vscode to update shutdown status in factories view."""

    what: Literal["shutdownStatus"] = "shutdownStatus"
    message: str

    def __hash__(self) -> int:
        """Return hash of the message for deduplication."""
        return hash((self.what, self.message))

    def __eq__(self, other: object) -> bool:
        """Check equality for deduplication."""
        if not isinstance(other, ShutdownStatusMessage):
            return False
        return self.what == other.what and self.message == other.message


class DoItForMe(pyd.BaseModel):
    """DoItForMe Data."""

    prompt: str = ""
    initial_circuit: str = ""
    url: str = ""

    def __hash__(self) -> int:
        """Return hash of the DoItForMe message for deduplication."""
        return hash((self.prompt, self.initial_circuit, self.url))

    def __eq__(self, other: object) -> bool:
        """Check equality for deduplication."""
        if not isinstance(other, DoItForMe):
            return False
        return (
            self.prompt == other.prompt
            and self.initial_circuit == other.initial_circuit
            and self.url == other.url
        )


Message: TypeAlias = (
    LogMessage
    | ReloadFactoriesMessage
    | ReloadLayoutMessage
    | ReloadSchematicMessage
    | RestartServerMessage
    | Show3dMessage
    | ShowBytesMessage
    | ShowGdsMessage
    | StartupStatusMessage
    | ShutdownStatusMessage
)
