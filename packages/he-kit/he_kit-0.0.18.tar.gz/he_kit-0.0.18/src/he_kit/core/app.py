from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from starlette.middleware.cors import CORSMiddleware

from ..authn.loader import load_auth_provider
from ..utils.project import read_pyproject
from .conf import DefaultSettings
from .db import db_lifespan
from .lifespan import compose_lifespans
from .logging import configure_logging, get_logger

logger = get_logger(__name__)


class App(FastAPI):
    settings = DefaultSettings()
    lifespans = [
        db_lifespan,
    ]

    def __init__(
        self,
        title=None,
        description=None,
        version=None,
        settings=None,
        lifespan=None,
        *args,
        **kwargs,
    ):
        pyproject = read_pyproject()

        title = title if title is not None else pyproject["project"]["name"]
        description = (
            description
            if description is not None
            else pyproject["project"]["description"]
        )
        version = version if version is not None else pyproject["project"]["version"]

        if settings is not None:
            self.settings = settings

        self.configure_logger()

        lifespan = compose_lifespans(*self.lifespans, lifespan)

        super().__init__(
            lifespan=lifespan,
            title=title,
            description=description,
            version=version,
            *args,
            **kwargs,
        )

        self.state.settings = self.settings
        self.state.auth_provider = load_auth_provider(self.settings)

        self.add_cors_middleware()

    def add_cors_middleware(self):
        """Register CORS middleware based on configuration."""
        self.add_middleware(
            CORSMiddleware,  # ty: ignore[invalid-argument-type]
            allow_origins=self.settings.CORS_ALLOWED_ORIGINS,
            allow_credentials=self.settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=self.settings.CORS_ALLOWED_METHODS,
            allow_headers=self.settings.CORS_ALLOWED_HEADERS,
        )

    def get_lifespans(self):
        """Return a list of all core lifespan context managers."""

    def openapi(self) -> dict[str, Any]:
        """Generate or return cached OpenAPI schema."""
        if getattr(self, "_openapi_schema", None) is not None:
            return self._openapi_schema

        schema = get_openapi(
            title=self.title,
            version=self.version,
            description=self.description,
            routes=self.routes,
            tags=getattr(self, "openapi_tags", None),
            servers=[{"url": self.settings.BASE_URL}],
            contact=getattr(self, "contact", None),
            license_info=getattr(self, "license_info", None),
        )

        self._openapi_schema = schema
        return schema

    def configure_logger(self):
        """Set up logging behavior."""
        configure_logging(
            level=self.settings.LOG_LEVEL,
            json_format=self.settings.LOG_JSON_FORMAT,
        )
