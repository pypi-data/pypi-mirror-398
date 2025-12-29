import importlib
import tomllib
from pathlib import Path
from typing import Type

from ..core.conf import DefaultSettings

_module_name = None
_settings_class_name = None
_settings = None


def find_project_root() -> Path:
    """Find and return project root directory."""
    path = Path.cwd()
    for parent in [path] + list(path.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError("Not inside a project directory.")


def read_pyproject(path: Path | None = None) -> dict:
    """Read and parse pyproject.toml file at `path`."""
    if path is None:
        root = find_project_root()
        path = root / "pyproject.toml"

    with path.open("rb") as f:
        return tomllib.load(f)


def settings_class_name() -> str:
    """Get settings class name from pyproject.toml."""
    global _settings_class_name

    if _settings_class_name is None:
        pyproject = read_pyproject()
        _settings_class_name = pyproject["tool"]["helicon"]["settings-class"]

    return _settings_class_name


def module_name() -> str:
    """Get module name from pyproject.toml."""
    global _module_name

    if _module_name is None:
        pyproject = read_pyproject()
        _module_name = pyproject["tool"]["helicon"]["module-name"]

    return _module_name


def get_settings(force_reload: bool = False) -> DefaultSettings:
    """Locate and instantiate the project's settings class defined in
    pyproject.toml.

    Reads the project's pyproject.toml to find the class path specified in
    [tool.helicon]["settings-class"], imports that class, and instantiates it
    and returns it.

    A cached version will be returned if not `force_reload` dictates
    otherwise.

    """
    global _settings

    if force_reload or _settings is None:
        settings_path = settings_class_name()
        module_path, class_name = settings_path.rsplit(".", 1)

        module = importlib.import_module(module_path)
        settings_cls: Type = getattr(module, class_name)

        _settings = settings_cls()

    return _settings
