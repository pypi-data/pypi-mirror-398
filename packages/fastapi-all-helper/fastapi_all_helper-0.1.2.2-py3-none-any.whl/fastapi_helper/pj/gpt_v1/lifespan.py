from contextlib import asynccontextmanager
from typing import AsyncGenerator


from fastapi import FastAPI

from .settings import lifespan_helper


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
Manages the application lifespan.

Performs resource initialization (such as database connections, etc.)
before the server starts and ensures a graceful shutdown when 
the server stops.

Args:
    app (FastAPI): The FastAPI application instance.

Yields:
    None: Yields control back to the application after initialization is complete.
"""

    await lifespan_helper.start_app()
    yield
    await lifespan_helper.close_app()