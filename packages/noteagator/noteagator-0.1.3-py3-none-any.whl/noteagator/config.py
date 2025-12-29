import json
import os
import sys
from functools import cached_property
from pathlib import Path
from types import MappingProxyType
from typing import Any

CONFIG_DIR_NAME = ".noteagator"
DEFAULT_NOTEBOOK = "notebook"


class Config:
    def __init__(self, home_dir: str | None = None) -> None:
        self._home_dir = home_dir
        self.ensure_app_path()
        self.ensure_config_path()
        self._config_data: dict[str, Any] = self._get_config()
        self.ensure_config_keys()

    def _get_config(self) -> dict[str, Any]:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_config_file(self, config_data: dict[str, Any]) -> None:
        with open(self.config_path, "w", encoding="utf-8") as file:
            json.dump(config_data, file, indent=4, ensure_ascii=False)

    @cached_property
    def app_path(self) -> str:
        base = self._home_dir or os.path.expanduser("~")
        return os.path.join(base, CONFIG_DIR_NAME)

    @cached_property
    def config_path(self) -> str:
        return os.path.join(self.app_path, "config.json")

    @cached_property
    def default_notebook_path(self) -> str:
        path: str = os.path.join(self.app_path, DEFAULT_NOTEBOOK)
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def config_data(self) -> dict[str, Any]:
        return MappingProxyType(self._config_data)

    @config_data.setter
    def config_data(self, value: dict[str, Any]) -> None:
        data: dict = dict(value)
        self._config_data = data
        self._write_config_file(self._config_data)

    @property
    def notebook_base_dir(self) -> str:
        return self._config_data.get("base")

    @notebook_base_dir.setter
    def notebook_base_dir(self, value: str) -> None:
        self._config_data["base"] = value
        self._write_config_file(self._config_data)

    @property
    def display_index(self) -> dict[str, Any]:
        return self._config_data.get("display_index", {})

    @display_index.setter
    def display_index(self, value: dict[str, Any]) -> None:
        self._config_data["display_index"] = value
        self._write_config_file(self._config_data)

    @property
    def notebook_cwd(self) -> str:
        return self._config_data.get("cwd")

    @notebook_cwd.setter
    def notebook_cwd(self, value: str) -> None:
        self._config_data["cwd"] = value
        self._write_config_file(self._config_data)

    @property
    def print_mode(self) -> str:
        return self._config_data.get("print_mode")

    @print_mode.setter
    def print_mode(self, value: str) -> None:
        self._config_data["print_mode"] = value
        self._write_config_file(self._config_data)

    def ensure_app_path(self) -> None:
        os.makedirs(self.app_path, exist_ok=True)

    def ensure_config_path(self) -> None:
        if not os.path.exists(self.config_path):
            nb_home = self.default_notebook_path
            self._write_config_file({"base": nb_home, "cwd": nb_home})

    def ensure_config_keys(self) -> None:
        changed: bool = False
        if not self._config_data.get("base") or self._config_data["base"] is None:
            self._config_data["base"] = self.default_notebook_path
            changed = True
        if not self._config_data.get("cwd") or self._config_data["cwd"] is None:
            self._config_data["cwd"] = self.default_notebook_path
            changed = True
        cwd_path = Path(self._config_data.get("cwd"))
        if not cwd_path.is_dir():
            self._config_data["cwd"] = self._config_data.get("base")
            changed = True
        if (
            not self._config_data.get("print_mode")
            or self._config_data["print_mode"] is None
        ):
            self._config_data["print_mode"] = "markdown"
        if changed:
            self._write_config_file(self._config_data)

    def return_file_path(self, index) -> str:
        entry = (self.display_index or {}).get(index) or {}
        node_type = entry.get("type")
        path = entry.get("absolute_path")
        if node_type == "file":
            if os.path.exists(path):
                return path
            else:
                sys.exit(
                    (
                        f"That note no longer exists on disk (index #{index}).\n"
                        f"Previously at: {entry.get('absolute_path')}\n"
                        "Your display index is out of date.\n"
                        "Run `ngt ls` (or `ngt ls -R`) or use "
                        "`ngt search <term>` to rebuild the display index."
                    )
                )
        else:
            sys.exit("Invalid Selection")
