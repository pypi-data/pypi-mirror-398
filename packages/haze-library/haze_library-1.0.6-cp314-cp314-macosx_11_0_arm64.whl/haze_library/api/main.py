"""FastAPI application entry point for Haze Library API."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from haze_library import __version__
from haze_library import numpy_compat as np_ta
from haze_library.streaming import get_available_streaming_indicators

from .routes import indicators_router, execution_router, streaming_router
from .models.responses import HealthResponse, ErrorResponse

# Track server start time
_start_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    global _start_time
    _start_time = time.time()
    yield


def create_app(
    *,
    title: str = "Haze Library API",
    version: str | None = None,
    cors_origins: list[str] | None = None,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        title: API title for documentation
        version: API version (defaults to library version)
        cors_origins: List of allowed CORS origins (defaults to ["*"])

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=title,
        version=version or __version__,
        description=(
            "High-performance technical analysis indicators and trading execution API. "
            "Powered by Rust backend with Python bindings."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(indicators_router, prefix="/api/v1/indicators")
    app.include_router(execution_router, prefix="/api/v1/execution")
    app.include_router(streaming_router, prefix="/api/v1/streaming")

    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "service": "Haze Library API",
            "version": __version__,
            "docs": "/docs",
        }

    # Health check
    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["health"],
        summary="Health check",
    )
    async def health_check() -> HealthResponse:
        """Check service health and get basic info."""
        execution_available = False
        try:
            from haze_library.execution.llm_tools import get_default_engine

            get_default_engine()
            execution_available = True
        except Exception:
            pass

        return HealthResponse(
            status="healthy",
            version=__version__,
            indicators_available=len(np_ta.__all__),
            streaming_indicators=len(get_available_streaming_indicators()),
            execution_enabled=execution_available,
            uptime_seconds=round(time.time() - _start_time, 2),
        )

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=str(exc),
                error_code="INTERNAL_ERROR",
                details={"path": str(request.url.path)},
            ).model_dump(),
        )

    return app


# Default application instance
app = create_app()


def run(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    workers: int = 1,
) -> None:
    """Run the API server.

    Args:
        host: Bind address
        port: Bind port
        reload: Enable auto-reload for development
        workers: Number of worker processes
    """
    import uvicorn

    uvicorn.run(
        "haze_library.api.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
    )


if __name__ == "__main__":
    run()
