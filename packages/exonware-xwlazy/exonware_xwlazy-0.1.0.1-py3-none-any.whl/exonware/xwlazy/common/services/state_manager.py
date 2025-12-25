from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

def _get_base_config_dir() -> Path:
    """Determine a cross-platform directory for storing lazy configuration."""
    if os.name == "nt":
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / "exonware" / "lazy"
        return Path.home() / "AppData" / "Roaming" / "exonware" / "lazy"

    # POSIX-style
    xdg_config = os.getenv("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "exonware" / "lazy"
    return Path.home() / ".config" / "exonware" / "lazy"

class LazyStateManager:
    """Persist and retrieve lazy installation state."""

    def __init__(self, package_name: str) -> None:
        self._package = package_name.lower()
        self._state_path = _get_base_config_dir() / "state.json"
        self._state: dict[str, dict[str, bool]] = self._load_state()

    # --------------------------------------------------------------------- #
    # Persistence helpers
    # --------------------------------------------------------------------- #
    def _load_state(self) -> dict[str, dict[str, bool]]:
        if not self._state_path.exists():
            return {}
        try:
            with self._state_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
        return {}

    def _save_state(self) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        with self._state_path.open("w", encoding="utf-8") as fh:
            json.dump(self._state, fh, indent=2, sort_keys=True)

    def _ensure_entry(self) -> dict[str, bool]:
        return self._state.setdefault(self._package, {})

    # --------------------------------------------------------------------- #
    # Manual state management
    # --------------------------------------------------------------------- #
    def get_manual_state(self) -> Optional[bool]:
        entry = self._state.get(self._package, {})
        value = entry.get("manual")
        return bool(value) if isinstance(value, bool) else None

    def set_manual_state(self, value: Optional[bool]) -> None:
        entry = self._ensure_entry()
        if value is None:
            entry.pop("manual", None)
        else:
            entry["manual"] = bool(value)
        self._save_state()

    # --------------------------------------------------------------------- #
    # Auto detection cache
    # --------------------------------------------------------------------- #
    def get_cached_auto_state(self) -> Optional[bool]:
        entry = self._state.get(self._package, {})
        value = entry.get("auto")
        return bool(value) if isinstance(value, bool) else None

    def set_auto_state(self, value: Optional[bool]) -> None:
        entry = self._ensure_entry()
        if value is None:
            entry.pop("auto", None)
        else:
            entry["auto"] = bool(value)
        self._save_state()

