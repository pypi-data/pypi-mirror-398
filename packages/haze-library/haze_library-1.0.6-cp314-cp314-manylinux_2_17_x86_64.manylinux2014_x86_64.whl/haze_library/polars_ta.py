from __future__ import annotations

from typing import Any, Iterable


def is_available() -> bool:
    try:
        import polars  # noqa: F401
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


def _require_polars():
    try:
        import polars as pl
    except Exception as exc:  # pragma: no cover
        raise ImportError("polars is required for polars_ta") from exc
    return pl


def _series_to_float_list(values: Iterable[Any]) -> list[float]:
    out: list[float] = []
    for v in values:
        if v is None:
            out.append(float("nan"))
        else:
            out.append(float(v))
    return out


def _get_column(df: Any, name: str) -> list[float]:
    return _series_to_float_list(df[name].to_list())


def sma(df: Any, close_column: str, period: int, *, result_column: str = "sma") -> Any:
    pl = _require_polars()
    from . import haze_library as _ext

    close = _get_column(df, close_column)
    result = list(_ext.py_sma(close, period))
    return df.with_columns(pl.Series(result_column, result))


def ema(df: Any, close_column: str, period: int, *, result_column: str = "ema") -> Any:
    pl = _require_polars()
    from . import haze_library as _ext

    close = _get_column(df, close_column)
    result = list(_ext.py_ema(close, period))
    return df.with_columns(pl.Series(result_column, result))


def rsi(df: Any, close_column: str, period: int, *, result_column: str = "rsi") -> Any:
    pl = _require_polars()
    from . import haze_library as _ext

    close = _get_column(df, close_column)
    result = list(_ext.py_rsi(close, period))
    return df.with_columns(pl.Series(result_column, result))


def macd(
    df: Any,
    close_column: str,
    *,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Any:
    pl = _require_polars()
    from . import haze_library as _ext

    close = _get_column(df, close_column)
    macd_line, signal_line, histogram = _ext.py_macd(close, fast_period, slow_period, signal_period)
    return df.with_columns(
        [
            pl.Series("macd", list(macd_line)),
            pl.Series("macd_signal", list(signal_line)),
            pl.Series("macd_histogram", list(histogram)),
        ]
    )


def bollinger_bands(
    df: Any,
    close_column: str,
    *,
    period: int = 20,
    std_multiplier: float = 2.0,
) -> Any:
    pl = _require_polars()
    from . import haze_library as _ext

    close = _get_column(df, close_column)
    upper, middle, lower = _ext.py_bollinger_bands(close, period, std_multiplier)
    return df.with_columns(
        [
            pl.Series("bb_upper", list(upper)),
            pl.Series("bb_middle", list(middle)),
            pl.Series("bb_lower", list(lower)),
        ]
    )


def atr(
    df: Any,
    *,
    high_column: str = "high",
    low_column: str = "low",
    close_column: str = "close",
    period: int = 14,
    result_column: str = "atr",
) -> Any:
    pl = _require_polars()
    from . import haze_library as _ext

    high = _get_column(df, high_column)
    low = _get_column(df, low_column)
    close = _get_column(df, close_column)
    result = list(_ext.py_atr(high, low, close, period))
    return df.with_columns(pl.Series(result_column, result))


def supertrend(
    df: Any,
    *,
    high_column: str = "high",
    low_column: str = "low",
    close_column: str = "close",
    period: int = 10,
    multiplier: float = 3.0,
    trend_column: str = "supertrend",
    direction_column: str = "supertrend_direction",
) -> Any:
    pl = _require_polars()
    from . import haze_library as _ext

    high = _get_column(df, high_column)
    low = _get_column(df, low_column)
    close = _get_column(df, close_column)

    trend, direction, _upper, _lower = _ext.py_supertrend(high, low, close, period, multiplier)
    return df.with_columns(
        [
            pl.Series(trend_column, list(trend)),
            pl.Series(direction_column, list(direction)),
        ]
    )


def obv(
    df: Any,
    *,
    close_column: str = "close",
    volume_column: str = "volume",
    result_column: str = "obv",
) -> Any:
    pl = _require_polars()
    from . import haze_library as _ext

    close = _get_column(df, close_column)
    volume = _get_column(df, volume_column)
    result = list(_ext.py_obv(close, volume))
    return df.with_columns(pl.Series(result_column, result))


def vwap(
    df: Any,
    *,
    high_column: str = "high",
    low_column: str = "low",
    close_column: str = "close",
    volume_column: str = "volume",
    period: int = 0,
    result_column: str = "vwap",
) -> Any:
    pl = _require_polars()
    from . import haze_library as _ext

    high = _get_column(df, high_column)
    low = _get_column(df, low_column)
    close = _get_column(df, close_column)
    volume = _get_column(df, volume_column)

    result = list(_ext.py_vwap(high, low, close, volume, period))
    return df.with_columns(pl.Series(result_column, result))

