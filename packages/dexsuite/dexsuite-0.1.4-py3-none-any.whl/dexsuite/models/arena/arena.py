"""Arena construction utilities.

This module builds a simple "arena" in a Genesis scene (plane, walls, and an
optional table) based on a YAML configuration. When a table is enabled, its MJCF
is materialized by recursively inlining MJCF <include file="..."> elements
and rewriting common file-bearing attributes (e.g. textures/meshes) to absolute
paths so the MJCF can be loaded robustly from any working directory.

The MJCF XML parsed here is expected to come from local, package-provided assets
or user-supplied files on disk (not from untrusted network inputs).
"""

from __future__ import annotations

import hashlib
import logging
import os
import tempfile
import xml.etree.ElementTree as element_tree
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import genesis as gs
import numpy as np
import yaml

from dexsuite.utils.models_utils import get_texture_paths

_THIS_DIR = Path(__file__).parent
_DEFAULT_YAML = _THIS_DIR / "arena.yaml"
_logger = logging.getLogger(__name__)


def _as_bool(x: object, *, ctx: str) -> bool:
    if isinstance(x, bool):
        return x
    if x is None:
        raise TypeError(f"{ctx} must be a bool, got None.")
    raise TypeError(f"{ctx} must be a bool, got {type(x).__name__}.")


def _as_float(x: object, *, ctx: str) -> float:
    if isinstance(x, bool):
        raise TypeError(f"{ctx} must be a float, got bool.")
    try:
        return float(x)  # type: ignore[arg-type]
    except (TypeError, ValueError) as e:
        raise TypeError(f"{ctx} must be a float, got {type(x).__name__}.") from e


def _as_str(x: object, *, ctx: str) -> str:
    if not isinstance(x, str):
        raise TypeError(f"{ctx} must be a string, got {type(x).__name__}.")
    return x


def _as_float_tuple(x: object, *, n: int, ctx: str) -> tuple[float, ...]:
    if not isinstance(x, (list, tuple)) or len(x) != n:
        raise TypeError(f"{ctx} must be a length-{n} list/tuple.")
    return tuple(_as_float(v, ctx=f"{ctx}[{i}]") for i, v in enumerate(x))


def _no_extra_keys(d: dict[str, Any], *, allowed: set[str], ctx: str) -> None:
    extra = set(d) - allowed
    if extra:
        extra_s = ", ".join(sorted(extra))
        allowed_s = ", ".join(sorted(allowed))
        raise ValueError(f"{ctx} has unknown key(s): {extra_s}. Allowed: {allowed_s}.")


def _parse_xml_root(path: Path) -> element_tree.Element:
    """Parse an XML file and return its root element.

    Args:
        path: Path to an XML file on disk.

    Returns:
        The parsed XML document root element.

    Raises:
        ValueError: If the XML cannot be parsed.
    """
    try:
        from defusedxml import (
            ElementTree as defused_element_tree,  # type: ignore[import-not-found]
        )
    except ImportError:
        try:
            return element_tree.parse(path).getroot()  # noqa: S314
        except element_tree.ParseError as exc:
            raise ValueError(f"Invalid MJCF XML: {path}") from exc

    try:
        return defused_element_tree.parse(path).getroot()
    except Exception as exc:  # defusedxml may raise multiple exception types
        raise ValueError(f"Invalid MJCF XML: {path}") from exc


@dataclass(slots=True)
class PlaneConfig:
    """Configuration for the ground plane."""

    enabled: bool = True
    pos: tuple[float, float, float] = (0.0, 0.0, 0.0)
    material: str = "wood"

    @classmethod
    def from_dict(cls, raw: dict[str, Any], *, ctx: str) -> PlaneConfig:
        """Parse a PlaneConfig from a YAML mapping."""
        _no_extra_keys(raw, allowed={"enabled", "pos", "material"}, ctx=ctx)
        enabled = _as_bool(raw.get("enabled", True), ctx=f"{ctx}.enabled")
        pos = _as_float_tuple(
            raw.get("pos", (0.0, 0.0, 0.0)),
            n=3,
            ctx=f"{ctx}.pos",
        )
        material = _as_str(raw.get("material", "wood"), ctx=f"{ctx}.material")
        return cls(enabled=enabled, pos=(pos[0], pos[1], pos[2]), material=material)


@dataclass(slots=True)
class WallItem:
    """Single wall panel specification."""

    name: str
    pos: tuple[float, float, float]
    quat: tuple[float, float, float, float]
    size: tuple[float, float, float]

    @classmethod
    def from_dict(cls, raw: dict[str, Any], *, ctx: str) -> WallItem:
        """Parse a WallItem from a YAML mapping."""
        _no_extra_keys(raw, allowed={"name", "pos", "quat", "size"}, ctx=ctx)
        name = _as_str(raw.get("name"), ctx=f"{ctx}.name")
        pos = _as_float_tuple(raw.get("pos"), n=3, ctx=f"{ctx}.pos")
        quat = _as_float_tuple(raw.get("quat"), n=4, ctx=f"{ctx}.quat")
        size = _as_float_tuple(raw.get("size"), n=3, ctx=f"{ctx}.size")
        return cls(
            name=name,
            pos=(pos[0], pos[1], pos[2]),
            quat=(quat[0], quat[1], quat[2], quat[3]),
            size=(size[0], size[1], size[2]),
        )


@dataclass(slots=True)
class WallsConfig:
    """Configuration for optional wall panels."""

    enabled: bool = True
    default_rgba: tuple[float, float, float, float] = (0.82, 0.86, 0.90, 1.0)
    items: tuple[WallItem, ...] = ()

    @classmethod
    def from_dict(cls, raw: dict[str, Any], *, ctx: str) -> WallsConfig:
        """Parse a WallsConfig from a YAML mapping."""
        _no_extra_keys(raw, allowed={"enabled", "default_rgba", "items"}, ctx=ctx)
        enabled = _as_bool(raw.get("enabled", True), ctx=f"{ctx}.enabled")
        default_rgba = _as_float_tuple(
            raw.get("default_rgba", (0.82, 0.86, 0.90, 1.0)),
            n=4,
            ctx=f"{ctx}.default_rgba",
        )
        items_raw = raw.get("items", [])
        if items_raw is None:
            items_raw = []
        if not isinstance(items_raw, list):
            raise TypeError(f"{ctx}.items must be a list of mappings.")
        items = tuple(
            WallItem.from_dict(item, ctx=f"{ctx}.items[{i}]")
            for i, item in enumerate(items_raw)
        )
        return cls(enabled=enabled, default_rgba=default_rgba, items=items)


@dataclass(slots=True)
class TableConfig:
    """Configuration for the optional MJCF table."""

    enabled: bool = True
    file: str = "assets/vention_table/ventionTable.xml"
    height: float = 0.0
    pos: tuple[float, float, float] = (0.40, 0.0, 0.0)
    euler_deg: tuple[float, float, float] = (0.0, 0.0, 90.0)

    @classmethod
    def from_dict(cls, raw: dict[str, Any], *, ctx: str) -> TableConfig:
        """Parse a TableConfig from a YAML mapping."""
        _no_extra_keys(
            raw,
            allowed={"enabled", "file", "height", "pos", "euler_deg"},
            ctx=ctx,
        )
        enabled = _as_bool(raw.get("enabled", True), ctx=f"{ctx}.enabled")
        file = _as_str(raw.get("file", cls.file), ctx=f"{ctx}.file")
        height = _as_float(raw.get("height", 0.0), ctx=f"{ctx}.height")
        pos = _as_float_tuple(raw.get("pos", cls.pos), n=3, ctx=f"{ctx}.pos")
        euler = _as_float_tuple(
            raw.get("euler_deg", cls.euler_deg),
            n=3,
            ctx=f"{ctx}.euler_deg",
        )
        return cls(
            enabled=enabled,
            file=file,
            height=height,
            pos=(pos[0], pos[1], pos[2]),
            euler_deg=(euler[0], euler[1], euler[2]),
        )


@dataclass(slots=True)
class ArenaConfig:
    """Top-level arena configuration parsed from YAML."""

    plane: PlaneConfig = field(default_factory=PlaneConfig)
    walls: WallsConfig = field(default_factory=WallsConfig)
    table: TableConfig = field(default_factory=TableConfig)

    @classmethod
    def from_dict(cls, raw: dict[str, Any], *, ctx: str) -> ArenaConfig:
        """Parse an ArenaConfig from a YAML mapping."""
        _no_extra_keys(raw, allowed={"plane", "walls", "table"}, ctx=ctx)
        plane = PlaneConfig.from_dict(raw.get("plane", {}) or {}, ctx=f"{ctx}.plane")
        walls = WallsConfig.from_dict(raw.get("walls", {}) or {}, ctx=f"{ctx}.walls")
        table = TableConfig.from_dict(raw.get("table", {}) or {}, ctx=f"{ctx}.table")
        return cls(plane=plane, walls=walls, table=table)


def _mjcf_cache_dir() -> Path:
    override = os.environ.get("DEXSUITE_MJCF_CACHE_DIR")
    d = (
        Path(override).expanduser().resolve()
        if override
        else (Path(tempfile.gettempdir()) / "dexsuite_mjcf").resolve()
    )
    d.mkdir(parents=True, exist_ok=True)
    return d


def _collect_mjcf_includes(path: Path) -> tuple[Path, ...]:
    """Collect MJCF <include file="..."> dependencies recursively."""
    seen: set[Path] = set()
    out: list[Path] = []

    def _walk(p: Path) -> None:
        p = p.resolve()
        if p in seen:
            return
        seen.add(p)
        out.append(p)
        root = _parse_xml_root(p)
        for inc in root.iter("include"):
            rel = inc.attrib.get("file")
            if not rel:
                raise ValueError(f"MJCF include missing 'file' attribute in {p}")
            inc_path = (p.parent / rel).resolve()
            if inc_path.exists():
                _walk(inc_path)

    _walk(path)
    return tuple(out)


def _expand_includes_inplace(root: element_tree.Element, *, base_dir: Path) -> None:
    """Inline <include file="..."> tags into their parent element."""
    i = 0
    while i < len(root):
        child = root[i]
        if child.tag != "include":
            _expand_includes_inplace(child, base_dir=base_dir)
            i += 1
            continue

        rel = child.attrib.get("file")
        if not rel:
            raise ValueError("MJCF include tag is missing a 'file' attribute.")
        inc_path = _resolve_mjcf_path(rel, base_dir=base_dir)
        if inc_path is None:
            raise FileNotFoundError(
                f"MJCF include file not found: '{rel}' (base_dir={base_dir})",
            )

        inc_root = _parse_xml_root(inc_path)
        if inc_root.tag != "mujocoinclude":
            raise ValueError(
                f"Expected <mujocoinclude> root in {inc_path}, got <{inc_root.tag}>.",
            )

        root.remove(child)
        insert_at = i
        inserted = 0
        for inc_child in list(inc_root):
            root.insert(insert_at, inc_child)
            _expand_includes_inplace(inc_child, base_dir=inc_path.parent)
            insert_at += 1
            inserted += 1
        i += inserted


def _merge_compilers_inplace(root: element_tree.Element) -> None:
    compilers = [c for c in list(root) if c.tag == "compiler"]
    if len(compilers) <= 1:
        return
    merged: dict[str, str] = {}
    for comp in compilers:
        for k, v in comp.attrib.items():
            if k not in merged or merged[k] == "":
                merged[k] = v
    for comp in compilers:
        root.remove(comp)
    root.insert(0, element_tree.Element("compiler", attrib=merged))


def _rewrite_file_attribs_to_abs(root: element_tree.Element, *, base_dir: Path) -> None:
    """Rewrite common file-bearing attributes to absolute paths."""
    for el in root.iter():
        raw = el.attrib.get("file")
        if not raw:
            continue
        resolved = _resolve_mjcf_path(raw, base_dir=base_dir)
        if resolved is not None:
            el.attrib["file"] = str(resolved)


def _resolve_mjcf_path(raw: str, *, base_dir: Path) -> Path | None:
    """Resolve an MJCF path string to an existing absolute path.

    This supports:
    - normal relative paths (relative to the referring XML's directory),
    - absolute paths,
    - repo/package-prefixed paths like dexsuite/... (resolved relative to the
      installed dexsuite package directory).
    """
    s = str(raw).strip()
    p = Path(s)
    if p.is_absolute():
        return p if p.exists() else None

    cand = (base_dir / p).resolve()
    if cand.exists():
        return cand

    # Handle legacy references like "dexsuite/models/...".
    # In an installed package, the "dexsuite" directory is the package root.
    if s.startswith("dexsuite/") or s.startswith("dexsuite\\"):
        pkg_root = Path(__file__).resolve().parents[2]  # .../dexsuite
        suffix = s.split("/", 1)[1] if "/" in s else s.split("\\", 1)[1]
        cand2 = (pkg_root / suffix).resolve()
        if cand2.exists():
            return cand2

    return None


def materialize_mjcf(root_xml: Path) -> Path:
    """Return a merged MJCF file with includes inlined and file paths absolutized."""
    deps = _collect_mjcf_includes(root_xml)
    h = hashlib.sha256()
    for p in deps:
        h.update(p.read_bytes())
    out = _mjcf_cache_dir() / f"{h.hexdigest()}.xml"
    if out.exists():
        return out

    mj = _parse_xml_root(root_xml)
    _expand_includes_inplace(mj, base_dir=root_xml.parent)
    _merge_compilers_inplace(mj)
    _rewrite_file_attribs_to_abs(mj, base_dir=root_xml.parent)
    element_tree.ElementTree(mj).write(out, encoding="utf-8", xml_declaration=True)
    return out


class Arena:
    """Arena builder that adds plane, walls, and table to a scene."""

    def __init__(self, scene: gs.Scene, yaml_path: str | Path | None = None):
        """Build the environment arena (plane, walls, and optional table).

        Args:
            scene: The Genesis scene to add arena components to.
            yaml_path: Optional path to a custom arena YAML. If omitted, loads
                dexsuite/models/arena/arena.yaml.

        Raises:
            FileNotFoundError: If the YAML file cannot be found.
            TypeError: If the YAML does not contain mappings where expected.
            ValueError: If the YAML contains unknown keys or invalid values.
        """
        self.scene = scene
        self.plane_ent = None
        self.wall_ents: list[Any] = []
        self.table_ent = None

        yaml_file = Path(yaml_path) if yaml_path else _DEFAULT_YAML

        try:
            raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or {}
        except FileNotFoundError as err:
            raise FileNotFoundError(f"Arena YAML not found: {yaml_file}") from err
        except Exception as e:
            raise ValueError(f"Error loading or parsing {yaml_file}: {e}") from e

        if not isinstance(raw, dict):
            raise TypeError(f"Arena YAML must be a mapping at top-level: {yaml_file}")

        self.cfg = raw
        self.config = ArenaConfig.from_dict(raw, ctx=f"{yaml_file}")

        # Get table height for global z-shift. Default to 0 if no table.
        self._table_h = (
            float(self.config.table.height) if self.config.table.enabled else 0.0
        )

        self._build_plane()
        self._build_walls()
        self._build_table()

    def _shift_z(self, z: float) -> float:
        """Apply global negative offset so table-top sits at z = 0."""
        return z - self._table_h

    def _build_plane(self):
        """Builds the ground plane."""
        cfg = self.config.plane
        if not cfg.enabled:
            return

        pos = np.asarray(cfg.pos, dtype=float)
        pos[2] = self._shift_z(pos[2])

        material = cfg.material
        try:
            texture = get_texture_paths(f"floor/{material}")
            diffuse = texture.get("diffuse")
            roughness = texture.get("roughness")
            surface = gs.surfaces.Default(
                diffuse_texture=(
                    None
                    if diffuse is None
                    else gs.textures.ImageTexture(image_path=diffuse)
                ),
                roughness_texture=(
                    None
                    if roughness is None
                    else gs.textures.ImageTexture(image_path=roughness)
                ),
                vis_mode="visual",
            )
        except FileNotFoundError as err:
            _logger.warning(
                f"Could not find floor material '{material}'. "
                f"Falling back to grey plane. Error: {err}",
            )
            surface = gs.surfaces.Default(color=(0.5, 0.5, 0.5, 1.0))

        self.plane_ent = self.scene.add_entity(
            morph=gs.morphs.Plane(
                pos=tuple(pos),
                normal=(0, 0, 1),
            ),
            surface=surface,
        )

    def _build_walls(self) -> None:
        """Instantiate the six visual wall panels declared in arena.yaml."""
        cfg = self.config.walls
        if not cfg.enabled:
            return

        # Get the final Z position of the plane to build walls on top of it
        plane_base_z = (
            float(self.config.plane.pos[2]) if self.config.plane.enabled else 0.0
        )
        final_plane_z = self._shift_z(plane_base_z)

        rgba = tuple(cfg.default_rgba)
        surface = gs.surfaces.Default(color=rgba)

        for item in cfg.items:
            pos = list(item.pos)
            quat = tuple(item.quat)
            size = list(item.size)

            # size[1] is the wall height.
            half_height = float(size[1]) / 2

            # Center the wall vertically so its bottom is flush with the plane
            pos[2] = final_plane_z + half_height

            morph = gs.morphs.Box(
                pos=tuple(pos),
                quat=quat,
                size=tuple(size),
                visualization=True,  # Visual-only, no collision
                fixed=True,
            )
            self.wall_ents.append(self.scene.add_entity(morph, surface=surface))

    def _build_table(self):
        """Builds the vention table from its MJCF file."""
        cfg = self.config.table
        if not cfg.enabled:
            return

        # Path to the MuJoCo XML (can be overridden in arena.yaml)
        table_path = Path(cfg.file)

        # Resolve path relative to this file (arena.py)
        if not table_path.is_absolute():
            table_path = (_THIS_DIR / table_path).resolve()

        if not table_path.exists():
            _logger.error(f"Table XML file not found: {table_path}")
            return

        merged = materialize_mjcf(table_path)
        pos = (cfg.pos[0], cfg.pos[1], self._shift_z(cfg.pos[2]))
        try:
            self.table_ent = self.scene.add_entity(
                gs.morphs.MJCF(file=str(merged), pos=pos, euler=tuple(cfg.euler_deg)),
            )
            self.table = self.table_ent
        except Exception:
            _logger.exception("Failed to load table MJCF from %s", table_path)
