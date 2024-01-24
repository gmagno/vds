from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware

from vidoso.config import Settings
from vidoso.deps import get_settings_dep
from vidoso.routes.v1 import routers


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings_dep()

    middlewares = [
        Middleware(
            CORSMiddleware,
            **dict(
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            ),
        )
    ]

    app = FastAPI(
        title=settings.title,
        description=settings.description,
        version=settings.version,
        docs_url=settings.docs_url,
        openapi_url=settings.openapi_url,
        middleware=middlewares,
    )

    app.include_router(
        routers.router,
        prefix=settings.base_url,
        tags=["vidoso"],
    )
    return app
