from enum import Enum
from typing import Optional

from config.settings import settings


class MarketMode(str, Enum):
    LONG_ONLY = "LONG_ONLY"
    SHORT_ONLY = "SHORT_ONLY"
    BOTH = "BOTH"
    NO_TRADE = "NO_TRADE"


def normalize_market_mode(value: Optional[str]) -> MarketMode:
    if not value:
        return MarketMode.NO_TRADE
    normalized = value.strip().upper()
    aliases = {
        "LONG": "LONG_ONLY",
        "SHORT": "SHORT_ONLY",
        "NONE": "NO_TRADE",
        "OFF": "NO_TRADE",
        "AUTO": "AUTO",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized == "AUTO":
        return MarketMode.NO_TRADE
    try:
        return MarketMode(normalized)
    except ValueError:
        return MarketMode.NO_TRADE


def decide_market_mode(
    signal_mode: Optional[str] = None,
    trend_ema200: Optional[str] = None,
    volatility: Optional[str] = None,
) -> MarketMode:
    """Return the direction mode that should gate TradingView entry signals.

    Explicit signal_mode wins. If the global setting is AUTO, use the trend
    context supplied by TradingView. Missing context falls back to NO_TRADE so
    the bot does not invent a direction.
    """
    if signal_mode:
        requested = normalize_market_mode(signal_mode)
        if requested != MarketMode.NO_TRADE or signal_mode.strip().upper() in {"NO_TRADE", "NONE", "OFF"}:
            return requested

    configured = settings.MARKET_MODE.strip().upper()
    if configured != "AUTO":
        return normalize_market_mode(configured)

    if volatility and volatility.strip().upper() in {"LOW", "CHOP", "RANGE"}:
        return MarketMode.NO_TRADE

    trend = (trend_ema200 or "").strip().upper()
    if trend in {"UP", "BULL", "BULLISH", "LONG"}:
        return MarketMode.LONG_ONLY
    if trend in {"DOWN", "BEAR", "BEARISH", "SHORT"}:
        return MarketMode.SHORT_ONLY
    return MarketMode.NO_TRADE


def action_allowed_in_mode(action: str, mode: MarketMode) -> bool:
    action = action.upper()
    if mode == MarketMode.BOTH:
        return action in {"BUY", "SELL"}
    if mode == MarketMode.LONG_ONLY:
        return action == "BUY"
    if mode == MarketMode.SHORT_ONLY:
        return action == "SELL"
    return False

