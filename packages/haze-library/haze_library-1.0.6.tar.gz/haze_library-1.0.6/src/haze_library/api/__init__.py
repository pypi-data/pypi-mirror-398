"""
Haze Library REST API

Provides HTTP endpoints for technical analysis indicators and trading execution.

Usage:
    uvicorn haze_library.api.main:app --host 0.0.0.0 --port 8000

Or programmatically:
    from haze_library.api.main import app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

from __future__ import annotations

from .main import app, create_app

__all__ = ["app", "create_app"]
