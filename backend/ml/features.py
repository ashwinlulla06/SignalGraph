from statistics import pstdev
from backend.models import MarketCandle

ROLLING_WINDOW = 20

FEATURE_NAMES = [
    "return_1",
    "range_percent",
    "body_percent",
    "gap_percent",
    "upper_wick_percent",
    "lower_wick_percent",
    "rolling_volatility"
]

def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0

    return numerator / denominator

def build_candle_features(candles: list[MarketCandle]) -> list[dict]:
    ordered_candles = sorted(candles, key=lambda candle: candle.start_time)

    feature_rows = []
    returns = []

    for index in range(1, len(ordered_candles)):
        previous_candle = ordered_candles[index - 1]
        current_candle = ordered_candles[index]

        time_difference = current_candle.start_time - previous_candle.start_time

        candles_are_continuous = (time_difference.total_seconds() == 60)

        if not candles_are_continuous:
            returns = []
            continue

        return_1 = safe_ratio(current_candle.close - previous_candle.close, previous_candle.close)

        returns.append(return_1)

        if len(returns) < ROLLING_WINDOW:
            continue

        range_percent = safe_ratio(current_candle.high - current_candle.low, current_candle.open)

        body_percent = safe_ratio(current_candle.close - current_candle.open, current_candle.open)

        gap_percent = safe_ratio(current_candle.open - previous_candle.close, previous_candle.close)

        upper_wick = current_candle.high - max(current_candle.open, current_candle.close)

        upper_wick_percent = safe_ratio(upper_wick, current_candle.open)

        lower_wick = min(current_candle.open, current_candle.close) - current_candle.low

        lower_wick_percent = safe_ratio(lower_wick, current_candle.open)

        recent_returns = returns[-ROLLING_WINDOW : ]

        rolling_volatility = pstdev(recent_returns)

        feature_row = {
            "source": current_candle.source,
            "symbol" : current_candle.symbol,
            "start_time": current_candle.start_time,
            "open": current_candle.open,
            "high": current_candle.high,
            "low": current_candle.low,
            "close": current_candle.close,
            "volume": current_candle.volume,
            "return_1" : return_1,
            "range_percent": range_percent,
            "body_percent": body_percent,
            "gap_percent": gap_percent,
            "upper_wick_percent": upper_wick_percent,
            "lower_wick_percent": lower_wick_percent,
            "rolling_volatility": rolling_volatility
        }

        feature_rows.append(feature_row)

    return feature_rows