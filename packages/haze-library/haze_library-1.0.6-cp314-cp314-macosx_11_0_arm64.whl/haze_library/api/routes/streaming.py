"""WebSocket streaming API endpoints."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from haze_library.streaming import (
    CCXTStreamProcessor,
    IncrementalRSI,
    IncrementalSuperTrend,
    IncrementalMACD,
    IncrementalBollingerBands,
    IncrementalATR,
    IncrementalEMA,
    IncrementalSMA,
    create_indicator,
    get_available_streaming_indicators,
)

router = APIRouter(tags=["streaming"])


def _create_processor(indicators: list[str]) -> CCXTStreamProcessor:
    """Create a stream processor with the specified indicators."""
    processor = CCXTStreamProcessor()

    for ind_name in indicators:
        try:
            indicator = create_indicator(ind_name)
            processor.add_indicator(ind_name, indicator)
        except ValueError:
            # Try common abbreviations
            abbrev_map = {
                "rsi": ("rsi", {}),
                "macd": ("macd", {}),
                "supertrend": ("supertrend", {}),
                "bb": ("bb", {}),
                "atr": ("atr", {}),
                "ema": ("ema", {}),
                "sma": ("sma", {}),
            }
            if ind_name.lower() in abbrev_map:
                name, params = abbrev_map[ind_name.lower()]
                indicator = create_indicator(name, **params)
                processor.add_indicator(ind_name, indicator)
            else:
                raise ValueError(f"Unknown streaming indicator: {ind_name}")

    return processor


@router.websocket("/ws/{symbol}")
async def websocket_streaming(
    websocket: WebSocket,
    symbol: str,
    indicators: str = "rsi,supertrend",
) -> None:
    """WebSocket endpoint for real-time indicator streaming.

    Connect to receive real-time indicator updates for a symbol.

    Args:
        symbol: Trading symbol (e.g., "BTC-USDT")
        indicators: Comma-separated list of indicators to calculate

    Messages:
        - Outgoing: {"event": "update", "symbol": "...", "timestamp": ..., "data": {...}}
        - Incoming: {"action": "subscribe", "indicators": [...]} to update subscriptions
    """
    await websocket.accept()

    # Parse indicator list
    indicator_list = [i.strip() for i in indicators.split(",") if i.strip()]

    try:
        processor = _create_processor(indicator_list)
    except ValueError as e:
        await websocket.send_json({
            "event": "error",
            "timestamp": int(time.time() * 1000),
            "data": {"message": str(e)},
        })
        await websocket.close()
        return

    # Send subscription confirmation
    await websocket.send_json({
        "event": "subscribed",
        "symbol": symbol.replace("-", "/"),
        "timestamp": int(time.time() * 1000),
        "data": {
            "indicators": indicator_list,
            "status": processor.get_status(),
        },
    })

    try:
        while True:
            # Wait for incoming messages (candle data or control messages)
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=60.0,  # Heartbeat timeout
                )
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({
                    "event": "heartbeat",
                    "timestamp": int(time.time() * 1000),
                    "data": {},
                })
                continue

            # Handle different message types
            action = data.get("action", "update")

            if action == "candle":
                # Process a new candle
                candle = data.get("candle", [])
                if len(candle) >= 5:
                    try:
                        results = processor.process_candle(candle)
                        await websocket.send_json({
                            "event": "update",
                            "symbol": symbol.replace("-", "/"),
                            "timestamp": int(time.time() * 1000),
                            "data": {
                                "indicators": results,
                                "candle": {
                                    "open": candle[1] if len(candle) > 5 else candle[0],
                                    "high": candle[2] if len(candle) > 5 else candle[1],
                                    "low": candle[3] if len(candle) > 5 else candle[2],
                                    "close": candle[4] if len(candle) > 5 else candle[3],
                                },
                            },
                        })
                    except Exception as e:
                        await websocket.send_json({
                            "event": "error",
                            "timestamp": int(time.time() * 1000),
                            "data": {"message": str(e)},
                        })

            elif action == "subscribe":
                # Update indicator subscriptions
                new_indicators = data.get("indicators", [])
                try:
                    processor = _create_processor(new_indicators)
                    await websocket.send_json({
                        "event": "subscribed",
                        "symbol": symbol.replace("-", "/"),
                        "timestamp": int(time.time() * 1000),
                        "data": {
                            "indicators": new_indicators,
                            "status": processor.get_status(),
                        },
                    })
                except ValueError as e:
                    await websocket.send_json({
                        "event": "error",
                        "timestamp": int(time.time() * 1000),
                        "data": {"message": str(e)},
                    })

            elif action == "status":
                # Return current processor status
                await websocket.send_json({
                    "event": "status",
                    "timestamp": int(time.time() * 1000),
                    "data": processor.get_status(),
                })

            elif action == "reset":
                # Reset all indicators
                processor.reset_all()
                await websocket.send_json({
                    "event": "reset",
                    "timestamp": int(time.time() * 1000),
                    "data": {"message": "All indicators reset"},
                })

            elif action == "ping":
                # Respond to ping
                await websocket.send_json({
                    "event": "pong",
                    "timestamp": int(time.time() * 1000),
                    "data": {},
                })

    except WebSocketDisconnect:
        pass  # Client disconnected normally


@router.get(
    "/indicators",
    summary="List streaming indicators",
    description="Get list of available streaming indicators",
)
async def list_streaming_indicators() -> dict[str, Any]:
    """List all available streaming indicators."""
    indicators = get_available_streaming_indicators()
    return {
        "count": len(indicators),
        "indicators": indicators,
        "abbreviations": {
            "rsi": "IncrementalRSI",
            "macd": "IncrementalMACD",
            "supertrend": "IncrementalSuperTrend",
            "bb": "IncrementalBollingerBands",
            "atr": "IncrementalATR",
            "ema": "IncrementalEMA",
            "sma": "IncrementalSMA",
            "stochastic": "IncrementalStochastic",
            "ai_supertrend": "IncrementalAISuperTrend",
        },
    }
