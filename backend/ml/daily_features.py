from statistics import pstdev

from backend.models import MarketCandle


ROLLING_WINDOW = 20

DAILY_FEATURE_NAMES = [
    "return_1",
    "range_percent",
    "body_percent",
    "gap_percent",
    "upper_wick_percent",
    "lower_wick_percent",
    "rolling_volatility_20",
    "volume_ratio_20",
    "drawdown_from_20_day_high",
    "distance_from_20_day_average",
]


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0

    return numerator / denominator


def build_daily_features(candles: list[MarketCandle]) -> list[dict]:
    ordered_candles = sorted(
        candles,
        key=lambda candle: candle.start_time,
    )

    feature_rows = []

    # We need 20 previous completed trading days.
    for index in range(
        ROLLING_WINDOW,
        len(ordered_candles),
    ):
        current_candle = ordered_candles[index]
        previous_candle = ordered_candles[index - 1]

        previous_window = ordered_candles[
            index - ROLLING_WINDOW:index
        ]

        return_1 = safe_ratio(
            current_candle.close - previous_candle.close,
            previous_candle.close,
        )

        range_percent = safe_ratio(
            current_candle.high
            - current_candle.low,
            current_candle.open,
        )

        body_percent = safe_ratio(
            current_candle.close
            - current_candle.open,
            current_candle.open,
        )

        gap_percent = safe_ratio(
            current_candle.open
            - previous_candle.close,
            previous_candle.close,
        )

        upper_wick = (
            current_candle.high
            - max(
                current_candle.open,
                current_candle.close,
            )
        )

        upper_wick_percent = safe_ratio(
            upper_wick,
            current_candle.open,
        )

        lower_wick = (
            min(
                current_candle.open,
                current_candle.close,
            )
            - current_candle.low
        )

        lower_wick_percent = safe_ratio(
            lower_wick,
            current_candle.open,
        )

        recent_returns = []

        # Create the latest 20 daily returns.
        for return_index in range(
            index - ROLLING_WINDOW + 1,
            index + 1,
        ):
            return_candle = ordered_candles[
                return_index
            ]

            return_previous_candle = (
                ordered_candles[
                    return_index - 1
                ]
            )

            daily_return = safe_ratio(
                return_candle.close
                - return_previous_candle.close,
                return_previous_candle.close,
            )

            recent_returns.append(
                daily_return
            )

        rolling_volatility_20 = pstdev(
            recent_returns
        )

        average_volume_20 = sum(
                candle.volume
                for candle in previous_window
            ) / len(previous_window)

        volume_ratio_20 = safe_ratio(
            current_candle.volume,
            average_volume_20,
        )

        previous_20_day_high = max(
            candle.high
            for candle in previous_window
        )

        drawdown_from_20_day_high = safe_ratio(
            current_candle.close
            - previous_20_day_high,
            previous_20_day_high,
        )

        previous_20_day_average = (
            sum(
                candle.close
                for candle in previous_window
            )
            / len(previous_window)
        )

        distance_from_20_day_average = safe_ratio(
            current_candle.close
            - previous_20_day_average,
            previous_20_day_average,
        )

        feature_rows.append(
            {
                "source": current_candle.source,
                "symbol": current_candle.symbol,
                "start_time": (
                    current_candle.start_time
                ),
                "open": current_candle.open,
                "high": current_candle.high,
                "low": current_candle.low,
                "close": current_candle.close,
                "volume": current_candle.volume,
                "return_1": return_1,
                "range_percent": range_percent,
                "body_percent": body_percent,
                "gap_percent": gap_percent,
                "upper_wick_percent": (
                    upper_wick_percent
                ),
                "lower_wick_percent": (
                    lower_wick_percent
                ),
                "rolling_volatility_20": (
                    rolling_volatility_20
                ),
                "volume_ratio_20": (
                    volume_ratio_20
                ),
                "drawdown_from_20_day_high": (
                    drawdown_from_20_day_high
                ),
                "distance_from_20_day_average": (
                    distance_from_20_day_average
                ),
            }
        )

    return feature_rows