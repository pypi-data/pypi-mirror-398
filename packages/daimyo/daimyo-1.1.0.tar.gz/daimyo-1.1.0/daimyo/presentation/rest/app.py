"""FastAPI application setup."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from daimyo import __version__
from daimyo.infrastructure.logging import get_logger, setup_logging
from daimyo.presentation.rest.routers import scopes

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager.

    Handles startup and shutdown events using modern FastAPI pattern.

    :param app: FastAPI application instance
    :type app: FastAPI
    :yields: None during application lifetime
    :rtype: AsyncIterator[None]
    """
    logger.info("Daimyo Rules Server starting up...")
    logger.info("REST API endpoints available at /docs")
    yield
    logger.info("Daimyo Rules Server shutting down...")


app = FastAPI(
    title="Daimyo Rules Server",
    description=(
        "Rules server for agents with REST and MCP interfaces. "
        "Supports scope-based rules with inheritance, categories for filtering, "
        "and server federation for distributed rule management."
    ),
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.include_router(scopes.router)


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    """Root endpoint - health check.

    :returns: Status information
    :rtype: dict[str, str]
    """
    return {"status": "ok", "service": "Daimyo Rules Server", "version": __version__}


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Health check endpoint.

    :returns: Health status
    :rtype: dict[str, str]
    """
    return {"status": "healthy"}


@app.exception_handler(404)
async def not_found_handler(request: object, exc: object) -> JSONResponse:
    """Handle 404 errors.

    :param request: The request object
    :type request: object
    :param exc: The exception object
    :type exc: object
    :returns: JSON response with error detail
    :rtype: JSONResponse
    """
    return JSONResponse(status_code=404, content={"detail": "Resource not found"})


@app.exception_handler(500)
async def internal_error_handler(request: object, exc: object) -> JSONResponse:
    """Handle 500 errors.

    :param request: The request object
    :type request: object
    :param exc: The exception object
    :type exc: object
    :returns: JSON response with error detail
    :rtype: JSONResponse
    """
    logger.exception("Internal server error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


__all__ = ["app"]
