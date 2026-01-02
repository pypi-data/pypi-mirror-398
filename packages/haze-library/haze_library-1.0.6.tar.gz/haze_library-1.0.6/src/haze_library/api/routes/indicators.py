"""Indicator calculation REST API endpoints."""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException

from haze_library import numpy_compat as np_ta
from haze_library.api.models.requests import CalculateIndicatorsRequest
from haze_library.api.models.responses import CalculateIndicatorsResponse

router = APIRouter(tags=["indicators"])

# Semantic key names for multi-output indicators
_TUPLE_OUTPUT_NAMES: dict[str, list[str]] = {
    "macd": ["macd", "signal", "histogram"],
    "bbands": ["upper", "middle", "lower"],
    "stoch": ["slowk", "slowd"],
    "stochrsi": ["fastk", "fastd"],
    "aroon": ["aroon_down", "aroon_up"],
    "ai_supertrend_ml": ["supertrend", "direction", "trend_offset", "buy_signal", "sell_signal", "stop_loss"],
    "atr2_signals_ml": ["atr_band", "rsi_smooth", "direction", "volatility", "buy_signal", "sell_signal", "stop_loss", "take_profit"],
    "ai_momentum_index_ml": ["momentum", "signal", "trend_strength", "direction", "buy_signal", "sell_signal"],
    "dynamic_macd": ["macd", "signal", "histogram", "ha_open", "ha_close"],
}


def _convert_result(
    result: Any, indicator_name: str | None = None
) -> list[float | None] | dict[str, list[float | None]]:
    """Convert indicator result to JSON-serializable format."""
    if isinstance(result, np.ndarray):
        # Replace NaN with None for JSON serialization
        return [None if np.isnan(x) else float(x) for x in result]
    elif isinstance(result, tuple):
        # Multi-output indicator - use semantic names if available
        names = _TUPLE_OUTPUT_NAMES.get(indicator_name or "", [])
        if len(names) >= len(result):
            return {names[i]: _convert_result(arr) for i, arr in enumerate(result)}
        else:
            return {f"output_{i}": _convert_result(arr) for i, arr in enumerate(result)}
    elif isinstance(result, dict):
        return {k: _convert_result(v) for k, v in result.items()}
    elif isinstance(result, list):
        return [None if (isinstance(x, float) and np.isnan(x)) else x for x in result]
    else:
        return result


def _get_indicator_function(name: str) -> Any:
    """Get indicator function by name."""
    if not hasattr(np_ta, name):
        raise ValueError(f"Unknown indicator: {name}")
    return getattr(np_ta, name)


@router.post(
    "/calculate",
    response_model=CalculateIndicatorsResponse,
    summary="Calculate multiple indicators",
    description="Batch calculate technical indicators on provided OHLCV data",
)
async def calculate_indicators(
    request: CalculateIndicatorsRequest,
) -> CalculateIndicatorsResponse:
    """Calculate multiple technical indicators in a single request.

    Args:
        request: Contains indicators list, OHLCV data, and optional parameters

    Returns:
        Calculated indicator values for each requested indicator

    Example:
        POST /api/v1/indicators/calculate
        {
            "indicators": ["sma", "rsi"],
            "data": {"close": [100, 101, 102, ...]},
            "params": {"sma": {"period": 20}, "rsi": {"period": 14}}
        }
    """
    start_time = time.perf_counter()
    results: dict[str, Any] = {}
    errors: dict[str, str] = {}

    # Convert data to numpy arrays
    data_arrays = {k: np.array(v, dtype=np.float64) for k, v in request.data.items()}

    for indicator_name in request.indicators:
        try:
            func = _get_indicator_function(indicator_name)
            params = request.params.get(indicator_name, {})

            # Build kwargs from data + params
            kwargs: dict[str, Any] = {}

            # Map function parameter names -> possible source data keys
            # e.g., if function expects "data", try to use "close" from input
            param_to_data_mapping = {
                "data": ["close", "data", "c", "price", "values", "series"],
                "close": ["close", "c", "price"],
                "high": ["high", "h"],
                "low": ["low", "l"],
                "open_": ["open", "o", "open_"],
                "volume": ["volume", "v", "vol"],
            }

            # Try to auto-map data arrays to function parameters
            import inspect

            sig = inspect.signature(func)
            for param in sig.parameters.values():
                if param.name in params:
                    # Explicit parameter from request
                    kwargs[param.name] = params[param.name]
                elif param.name in data_arrays:
                    # Direct match in data
                    kwargs[param.name] = data_arrays[param.name]
                elif param.name in param_to_data_mapping:
                    # Try mapped aliases
                    for alias in param_to_data_mapping[param.name]:
                        if alias in data_arrays:
                            kwargs[param.name] = data_arrays[alias]
                            break

            # Add remaining explicit params
            for k, v in params.items():
                if k not in kwargs:
                    kwargs[k] = v

            # Call the indicator function
            result = func(**kwargs)
            results[indicator_name] = _convert_result(result, indicator_name)

        except Exception as e:
            errors[indicator_name] = str(e)

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    return CalculateIndicatorsResponse(
        success=len(errors) == 0,
        results=results,
        errors=errors,
        metadata={
            "elapsed_ms": round(elapsed_ms, 2),
            "data_length": len(next(iter(request.data.values()), [])),
            "indicators_requested": len(request.indicators),
            "indicators_succeeded": len(results),
        },
    )


@router.get(
    "/available",
    summary="List available indicators",
    description="Get list of all available indicator functions",
)
async def list_available_indicators() -> dict[str, Any]:
    """List all available indicator functions."""
    indicators = list(np_ta.__all__)
    return {
        "count": len(indicators),
        "indicators": sorted(indicators),
    }


@router.get(
    "/{indicator_name}/info",
    summary="Get indicator info",
    description="Get detailed information about a specific indicator",
)
async def get_indicator_info(indicator_name: str) -> dict[str, Any]:
    """Get information about a specific indicator."""
    try:
        func = _get_indicator_function(indicator_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    import inspect

    sig = inspect.signature(func)
    params = []
    for name, param in sig.parameters.items():
        param_info = {
            "name": name,
            "required": param.default is inspect.Parameter.empty,
        }
        if param.default is not inspect.Parameter.empty:
            param_info["default"] = param.default
        if param.annotation is not inspect.Parameter.empty:
            param_info["type"] = str(param.annotation)
        params.append(param_info)

    return {
        "name": indicator_name,
        "docstring": func.__doc__ or "No documentation available",
        "parameters": params,
    }
