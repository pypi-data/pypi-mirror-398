from fastapi import FastAPI

from .router import router
from .settings import app_settings
from .lifespan import lifespan


def gpt_app() -> FastAPI:
    """
Creates and configures a FastAPI application instance.

Initializes the application with global settings (title, version, 
description), attaches the lifespan event handler, and registers 
the core routes.

The application is highly scalable and provides baseline GPT-related 
functionality. You can easily extend it by attaching your own 
endpoints as shown in the example below.

Returns:
    FastAPI: The configured application instance.

Example:
    ```python 
    from fastapi_helper.pj import gpt_app
    from fastapi import APIRouter

    router = APIRouter()

    @router.get('/')
    async def index_app() -> dict[str, bool]:
        return {"ok": True}

    main_app = gpt_app()
    main_app.include_router(router=router)
    ```
"""

    app = FastAPI(
        title=app_settings.title,
        version=app_settings.version,
        description=app_settings.description,
        lifespan=lifespan
    )
    
    app.include_router(router)
    return app