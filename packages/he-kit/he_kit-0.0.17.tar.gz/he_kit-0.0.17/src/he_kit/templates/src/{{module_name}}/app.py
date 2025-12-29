from he_kit.core.app import App

from .conf import settings


def create_app():
    app = App(settings=settings)

    # Register routers etc here

    return app


app = create_app()
