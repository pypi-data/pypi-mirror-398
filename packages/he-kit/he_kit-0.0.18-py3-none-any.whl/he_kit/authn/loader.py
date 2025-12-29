import importlib

from ..core.conf import DefaultSettings
from .base import AuthProvider


def load_auth_provider(settings: DefaultSettings) -> AuthProvider:
    """Load an AuthProvider class from a full import path.

    Example: "he_kit.authn.dummy.DummyAuthProvider"

    """
    path = settings.AUTH_BACKEND
    if "." not in path:
        raise ValueError(f"Invalid AUTH_BACKEND: {path}")

    module_path, class_name = path.rsplit(".", 1)

    module = importlib.import_module(module_path)
    cls = getattr(module, class_name, None)

    if cls is None:
        raise ImportError(f"Class {class_name} not found in {module_path}")

    provider = cls(settings)

    if not isinstance(provider, AuthProvider):
        raise TypeError(f"{path} is not an AuthProvider")

    return provider
