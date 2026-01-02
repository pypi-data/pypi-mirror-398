from __future__ import annotations

from typing import Any, Sequence


def is_available() -> bool:
    try:
        import torch  # noqa: F401
    except Exception:
        return False
    return True


def get_available_functions() -> list[str]:
    return [
        "sma",
        "ema",
        "rsi",
        "macd",
        "bollinger_bands",
        "atr",
        "supertrend",
        "obv",
        "vwap",
    ]


def _require_torch():
    try:
        import torch
    except Exception as exc:  # pragma: no cover
        raise ImportError("torch is required for torch_ta") from exc
    return torch


def _tensor_to_float_list(tensor: Any) -> list[float]:
    torch = _require_torch()
    return tensor.detach().to(device="cpu", dtype=torch.float64).tolist()


def _to_tensor(values: Sequence[float], *, like: Any) -> Any:
    torch = _require_torch()
    return torch.tensor(list(values), device=like.device, dtype=torch.float64)


def sma(close: Any, period: int) -> Any:
    from . import haze_library as _ext
    close_list = _tensor_to_float_list(close)
    result = _ext.py_sma(close_list, period)
    return _to_tensor(result, like=close)


def ema(close: Any, period: int) -> Any:
    from . import haze_library as _ext
    close_list = _tensor_to_float_list(close)
    result = _ext.py_ema(close_list, period)
    return _to_tensor(result, like=close)


def rsi(close: Any, period: int = 14) -> Any:
    from . import haze_library as _ext
    close_list = _tensor_to_float_list(close)
    result = _ext.py_rsi(close_list, period)
    return _to_tensor(result, like=close)


def macd(close: Any, *, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> tuple[Any, Any, Any]:
    from . import haze_library as _ext
    close_list = _tensor_to_float_list(close)
    macd_line, signal_line, histogram = _ext.py_macd(close_list, fast_period, slow_period, signal_period)
    return (
        _to_tensor(macd_line, like=close),
        _to_tensor(signal_line, like=close),
        _to_tensor(histogram, like=close),
    )


def bollinger_bands(close: Any, *, period: int = 20, std_multiplier: float = 2.0) -> tuple[Any, Any, Any]:
    from . import haze_library as _ext
    close_list = _tensor_to_float_list(close)
    upper, middle, lower = _ext.py_bollinger_bands(close_list, period, std_multiplier)
    return (
        _to_tensor(upper, like=close),
        _to_tensor(middle, like=close),
        _to_tensor(lower, like=close),
    )


def atr(high: Any, low: Any, close: Any, *, period: int = 14) -> Any:
    from . import haze_library as _ext
    high_list = _tensor_to_float_list(high)
    low_list = _tensor_to_float_list(low)
    close_list = _tensor_to_float_list(close)
    result = _ext.py_atr(high_list, low_list, close_list, period)
    return _to_tensor(result, like=close)


def supertrend(
    high: Any,
    low: Any,
    close: Any,
    *,
    period: int = 10,
    multiplier: float = 3.0,
) -> tuple[Any, Any]:
    from . import haze_library as _ext
    high_list = _tensor_to_float_list(high)
    low_list = _tensor_to_float_list(low)
    close_list = _tensor_to_float_list(close)
    trend, direction, _upper, _lower = _ext.py_supertrend(high_list, low_list, close_list, period, multiplier)
    return _to_tensor(trend, like=close), _to_tensor(direction, like=close)


def obv(close: Any, volume: Any) -> Any:
    from . import haze_library as _ext
    close_list = _tensor_to_float_list(close)
    volume_list = _tensor_to_float_list(volume)
    result = _ext.py_obv(close_list, volume_list)
    return _to_tensor(result, like=close)


def vwap(high: Any, low: Any, close: Any, volume: Any, *, period: int = 0) -> Any:
    from . import haze_library as _ext
    high_list = _tensor_to_float_list(high)
    low_list = _tensor_to_float_list(low)
    close_list = _tensor_to_float_list(close)
    volume_list = _tensor_to_float_list(volume)
    result = _ext.py_vwap(high_list, low_list, close_list, volume_list, period)
    return _to_tensor(result, like=close)

