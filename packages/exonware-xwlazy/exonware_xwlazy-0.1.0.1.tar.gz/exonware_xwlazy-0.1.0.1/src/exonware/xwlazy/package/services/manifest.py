from __future__ import annotations

"""
xwlazy.common.utils.manifest
----------------------------

Centralized loader for per-package dependency manifests. A manifest can be
declared either as a JSON file located in the target project's root directory
or inline inside ``pyproject.toml`` under the ``[tool.xwlazy]`` namespace.

The loader consolidates the following pieces of information:

* Explicit import -> package mappings
* Serialization/watch prefixes that should be handled by the import hook
* Async installation preferences (queue enabled + worker count)

It also keeps lightweight caches with file-modification tracking so repeated
lookups do not hit the filesystem unnecessarily.
"""

from dataclasses import field
import importlib.util
import json
import os
from pathlib import Path
from threading import RLock
from typing import Any, Iterable, Optional

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except Exception:  # pragma: no cover - fallback for <=3.10
    try:
        import tomli as tomllib  # type: ignore[attr-defined]
    except ImportError:  # pragma: no cover
        tomllib = None  # type: ignore

DEFAULT_MANIFEST_FILENAMES: tuple[str, ...] = (
    "xwlazy.manifest.json",
    "lazy.manifest.json",
    ".xwlazy.manifest.json",
)

ENV_MANIFEST_PATH = "XWLAZY_MANIFEST_PATH"

def _normalize_package_name(package_name: Optional[str]) -> str:
    return (package_name or "global").strip().lower()

def _normalize_prefix(prefix: str) -> str:
    prefix = prefix.strip()
    if not prefix:
        return ""
    if not prefix.endswith("."):
        prefix = f"{prefix}."
    return prefix

def _normalize_wrap_hints(values: Iterable[Any]) -> list[str]:
    hints: list[str] = []
    for value in values:
        if value is None:
            continue
        hint = str(value).strip().lower()
        if hint:
            hints.append(hint)
    return hints

# PackageManifest moved to defs.py - import it from there
from ...defs import PackageManifest

class LazyManifestLoader:
    """
    Loads and caches manifest data per package.

    Args:
        default_root: Optional fallback root directory used when a package
            root cannot be auto-detected.
        package_roots: Optional explicit mapping used mainly for tests.
    """

    def __init__(
        self,
        default_root: Optional[Path] = None,
        package_roots: Optional[dict[str, Path]] = None,
    ) -> None:
        self._default_root = default_root
        self._provided_roots = {
            _normalize_package_name(name): Path(path)
            for name, path in (package_roots or {}).items()
        }
        self._manifest_cache: dict[str, PackageManifest] = {}
        self._source_signatures: dict[str, tuple[str, float, float]] = {}
        self._pyproject_cache: dict[Path, tuple[float, dict[str, Any]]] = {}
        self._shared_dependency_maps: dict[
            tuple[str, float, float], dict[str, dict[str, str]]
        ] = {}
        self._lock = RLock()
        self._generation = 0

    @property
    def generation(self) -> int:
        """Incremented whenever any manifest content changes."""
        return self._generation

    def clear_cache(self) -> None:
        """Forcefully clear cached manifests."""
        with self._lock:
            self._manifest_cache.clear()
            self._source_signatures.clear()
            self._pyproject_cache.clear()
            self._shared_dependency_maps.clear()
            self._generation += 1

    def sync_manifest_configuration(self, package_name: str) -> None:
        """
        Sync configuration from manifest for a specific package.
        
        This method forces a reload of the manifest and clears caches
        to ensure the latest configuration is used.
        
        Args:
            package_name: The package name to sync configuration for
        """
        with self._lock:
            # Clear cache for this package
            package_key = _normalize_package_name(package_name)
            if package_key in self._manifest_cache:
                del self._manifest_cache[package_key]
            if package_key in self._source_signatures:
                del self._source_signatures[package_key]
            # Increment generation to invalidate shared caches
            self._generation += 1
            # Force reload by getting manifest
            self.get_manifest(package_key)

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def get_manifest(self, package_name: Optional[str]) -> Optional[PackageManifest]:
        """Return manifest for the provided package."""
        key = _normalize_package_name(package_name)
        with self._lock:
            signature = self._compute_signature(key)
            cached_signature = self._source_signatures.get(key)
            if (
                cached_signature is not None
                and signature is not None
                and cached_signature == signature
                and key in self._manifest_cache
            ):
                return self._manifest_cache[key]

            manifest = self._load_manifest(key)
            if manifest is None:
                # Cache miss is still tracked so we don't re-read files
                self._manifest_cache.pop(key, None)
                self._source_signatures[key] = signature or ("", 0.0, 0.0)
                return None

            self._manifest_cache[key] = manifest
            if signature is not None:
                self._source_signatures[key] = signature
                per_signature = self._shared_dependency_maps.setdefault(signature, {})
                per_signature[manifest.package] = manifest.dependencies.copy()
            self._generation += 1
            return manifest

    def get_manifest_signature(self, package_name: Optional[str]) -> Optional[tuple[str, float, float]]:
        key = _normalize_package_name(package_name)
        with self._lock:
            signature = self._source_signatures.get(key)
            if signature is not None:
                return signature
            signature = self._compute_signature(key)
            if signature is not None:
                self._source_signatures[key] = signature
            return signature
    
    def get_shared_dependencies(
        self,
        package_name: Optional[str],
        signature: Optional[tuple[str, float, float]],
    ) -> Optional[dict[str, str]]:
        if signature is None:
            return None
        with self._lock:
            package_maps = self._shared_dependency_maps.get(signature)
            if not package_maps:
                return None
            key = _normalize_package_name(package_name)
            return package_maps.get(key)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _load_manifest(self, package_key: str) -> Optional[PackageManifest]:
        root = self._resolve_project_root(package_key)
        pyproject_path = root / "pyproject.toml"
        pyproject_data = self._load_pyproject(pyproject_path)
        json_data, manifest_path = self._load_json_manifest(root, pyproject_data)

        data = self._merge_sources(package_key, pyproject_data, json_data)
        if not data["dependencies"] and not data["watched_prefixes"] and not data["async_installs"]:
            return None

        wrap_prefixes = tuple(data.get("wrap_class_prefixes", ()))

        manifest = PackageManifest(
            package=package_key,
            dependencies=data["dependencies"],
            watched_prefixes=tuple(
                _normalize_prefix(prefix)
                for prefix in data["watched_prefixes"]
                if _normalize_prefix(prefix)
            ),
            async_installs=bool(data.get("async_installs")),
            async_workers=max(1, int(data.get("async_workers", 1))),
            class_wrap_prefixes=wrap_prefixes,
            metadata={
                "root": str(root),
                "manifest_path": str(manifest_path) if manifest_path else None,
                "wrap_class_prefixes": wrap_prefixes,
            },
        )
        return manifest

    def _compute_signature(self, package_key: str) -> Optional[tuple[str, float, float]]:
        root = self._resolve_project_root(package_key)
        pyproject_path = root / "pyproject.toml"
        pyproject_mtime = pyproject_path.stat().st_mtime if pyproject_path.exists() else 0.0
        manifest_path = self._resolve_manifest_path(root, pyproject_path)
        json_mtime = manifest_path.stat().st_mtime if manifest_path and manifest_path.exists() else 0.0
        env_token = os.environ.get(ENV_MANIFEST_PATH, "")
        if not manifest_path and not pyproject_path.exists() and not env_token:
            return None
        return (env_token + str(manifest_path), pyproject_mtime, json_mtime)

    def _resolve_project_root(self, package_key: str) -> Path:
        if package_key in self._provided_roots:
            return self._provided_roots[package_key]

        module_candidates: Iterable[str]
        if package_key == "global":
            module_candidates = ()
        else:
            module_candidates = (f"exonware.{package_key}", package_key)

        for module_name in module_candidates:
            spec = importlib.util.find_spec(module_name)
            if spec and spec.origin:
                origin_path = Path(spec.origin).resolve()
                root = self._walk_to_project_root(origin_path.parent)
                if root:
                    self._provided_roots[package_key] = root
                    return root

        if self._default_root:
            return self._default_root
        return Path.cwd()

    @staticmethod
    def _walk_to_project_root(start: Path) -> Optional[Path]:
        """Walk up from start path to find project root."""
        from ...common.utils import find_project_root
        # Use utility function, but start from the provided path
        try:
            return find_project_root(start)
        except Exception:
            # Fallback: simple walk-up logic
            current = start
            while True:
                if (current / "pyproject.toml").exists():
                    return current
                parent = current.parent
                if parent == current:
                    break
                current = parent
            return None

    # ------------------------------- #
    # Pyproject helpers
    # ------------------------------- #
    def _load_pyproject(self, path: Path) -> dict[str, Any]:
        if not path.exists() or tomllib is None:
            return {}

        cached = self._pyproject_cache.get(path)
        current_mtime = path.stat().st_mtime
        if cached and cached[0] == current_mtime:
            return cached[1]

        try:
            with path.open("rb") as handle:
                data = tomllib.load(handle)
        except Exception:
            data = {}

        self._pyproject_cache[path] = (current_mtime, data)
        return data

    def _extract_pyproject_entry(
        self,
        pyproject_data: dict[str, Any],
        package_key: str,
    ) -> dict[str, Any]:
        tool_section = pyproject_data.get("tool", {})
        lazy_section = tool_section.get("xwlazy", {})
        packages = lazy_section.get("packages", {})
        entry = packages.get(package_key, {}) or packages.get(package_key.upper(), {})

        dependencies = {}
        watched = []
        async_installs = lazy_section.get("async_installs") or entry.get("async_installs")
        async_workers = entry.get("async_workers") or lazy_section.get("async_workers")
        wrap_hints = []

        global_deps = lazy_section.get("dependencies", {})
        if isinstance(global_deps, dict):
            dependencies.update({str(k): str(v) for k, v in global_deps.items()})

        if "dependencies" in entry and isinstance(entry["dependencies"], dict):
            dependencies.update({str(k): str(v) for k, v in entry["dependencies"].items()})

        for key in ("watched-prefixes", "watched_prefixes", "watch"):
            values = entry.get(key) or lazy_section.get(key)
            if isinstance(values, list):
                watched.extend(str(v) for v in values)

        global_wrap = lazy_section.get("wrap_class_prefixes") or lazy_section.get("wrap_classes")
        if isinstance(global_wrap, list):
            wrap_hints.extend(_normalize_wrap_hints(global_wrap))
        entry_wrap = entry.get("wrap_class_prefixes") or entry.get("wrap_classes")
        if isinstance(entry_wrap, list):
            wrap_hints.extend(_normalize_wrap_hints(entry_wrap))

        return {
            "dependencies": dependencies,
            "watched_prefixes": watched,
            "async_installs": bool(async_installs),
            "async_workers": async_workers or 1,
            "wrap_class_prefixes": wrap_hints,
        }

    # ------------------------------- #
    # Manifest helpers
    # ------------------------------- #
    def _resolve_manifest_path(self, root: Path, pyproject_path: Path) -> Optional[Path]:
        env_value = os.environ.get(ENV_MANIFEST_PATH)
        if env_value:
            for raw in env_value.split(os.pathsep):
                candidate = Path(raw).expanduser()
                if candidate.exists():
                    return candidate

        if pyproject_path.exists() and tomllib is not None:
            py_data = self._load_pyproject(pyproject_path)
            tool_section = py_data.get("tool", {}).get("xwlazy", {})
            manifest_path = tool_section.get("manifest") or tool_section.get("manifest_path")
            if manifest_path:
                candidate = (root / manifest_path).resolve()
                if candidate.exists():
                    return candidate

        for filename in DEFAULT_MANIFEST_FILENAMES:
            candidate = root / filename
            if candidate.exists():
                return candidate

        return None

    def _load_json_manifest(
        self,
        root: Path,
        pyproject_data: dict[str, Any],
    ) -> tuple[dict[str, Any], Optional[Path]]:
        manifest_path = self._resolve_manifest_path(root, root / "pyproject.toml")
        if not manifest_path:
            return {}, None

        try:
            with manifest_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
                if isinstance(data, dict):
                    return data, manifest_path
        except Exception:
            pass

        return {}, manifest_path

    def _merge_sources(
        self,
        package_key: str,
        pyproject_data: dict[str, Any],
        json_data: dict[str, Any],
    ) -> dict[str, Any]:
        merged_dependencies: dict[str, str] = {}
        merged_watched: list[str] = []
        merged_wrap_hints: list[str] = []

        # Pyproject first (acts as baseline)
        py_entry = self._extract_pyproject_entry(pyproject_data, package_key)
        merged_dependencies.update({k.lower(): v for k, v in py_entry["dependencies"].items()})
        merged_watched.extend(py_entry["watched_prefixes"])
        merged_wrap_hints.extend(_normalize_wrap_hints(py_entry.get("wrap_class_prefixes", [])))

        async_installs = py_entry.get("async_installs", False)
        async_workers = py_entry.get("async_workers", 1)

        # JSON global settings
        global_deps = json_data.get("dependencies", {})
        if isinstance(global_deps, dict):
            merged_dependencies.update({str(k).lower(): str(v) for k, v in global_deps.items()})

        global_watch = json_data.get("watch") or json_data.get("watched_prefixes")
        if isinstance(global_watch, list):
            merged_watched.extend(str(item) for item in global_watch)
        global_wrap = json_data.get("wrap_class_prefixes") or json_data.get("wrap_classes")
        if isinstance(global_wrap, list):
            merged_wrap_hints.extend(_normalize_wrap_hints(global_wrap))

        global_async = json_data.get("async_installs")
        if global_async is not None:
            async_installs = bool(global_async)
        global_workers = json_data.get("async_workers")
        if global_workers is not None:
            async_workers = global_workers

        packages_section = json_data.get("packages", {})
        if isinstance(packages_section, dict):
            entry = packages_section.get(package_key) or packages_section.get(package_key.upper())
            if isinstance(entry, dict):
                entry_deps = entry.get("dependencies", {})
                if isinstance(entry_deps, dict):
                    merged_dependencies.update({str(k).lower(): str(v) for k, v in entry_deps.items()})

                entry_watch = entry.get("watched_prefixes") or entry.get("watch")
                if isinstance(entry_watch, list):
                    merged_watched.extend(str(item) for item in entry_watch)
                entry_wrap = entry.get("wrap_class_prefixes") or entry.get("wrap_classes")
                if isinstance(entry_wrap, list):
                    merged_wrap_hints.extend(_normalize_wrap_hints(entry_wrap))

                if "async_installs" in entry:
                    async_installs = bool(entry["async_installs"])
                if "async_workers" in entry:
                    async_workers = entry.get("async_workers", async_workers)

        seen_wrap: set[str] = set()
        ordered_wrap_hints: list[str] = []
        for hint in merged_wrap_hints:
            if hint not in seen_wrap:
                seen_wrap.add(hint)
                ordered_wrap_hints.append(hint)

        return {
            "dependencies": merged_dependencies,
            "watched_prefixes": merged_watched,
            "async_installs": async_installs,
            "async_workers": async_workers,
            "wrap_class_prefixes": ordered_wrap_hints,
        }

_manifest_loader: Optional[LazyManifestLoader] = None
_manifest_loader_lock = RLock()

def get_manifest_loader() -> LazyManifestLoader:
    """
    Return the process-wide manifest loader instance.

    Calling this function does not force any manifest to be loaded, but the
    loader keeps shared caches that allow multiple subsystems (dependency mapper,
    installer, hook configuration) to observe manifest changes consistently.
    """
    global _manifest_loader
    with _manifest_loader_lock:
        if _manifest_loader is None:
            _manifest_loader = LazyManifestLoader()
        return _manifest_loader

def refresh_manifest_cache() -> None:
    """Forcefully clear the shared manifest loader cache."""
    loader = get_manifest_loader()
    loader.clear_cache()

def sync_manifest_configuration(package_name: str) -> None:
    """
    Sync configuration from manifest for a specific package.
    
    This is a convenience function that calls the manifest loader's
    sync_manifest_configuration method.
    
    Args:
        package_name: The package name to sync configuration for
    """
    loader = get_manifest_loader()
    loader.sync_manifest_configuration(package_name)

__all__ = [
    "PackageManifest",
    "LazyManifestLoader",
    "get_manifest_loader",
    "refresh_manifest_cache",
    "sync_manifest_configuration",
]

