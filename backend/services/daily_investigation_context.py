from datetime import date
from datetime import timedelta

from fastapi import FastAPI


HISTORY_LOOKBACK_DAYS = 120


async def build_daily_investigation_context(
    app: FastAPI,
    symbol: str,
    investigation_date: date,
) -> tuple[dict, dict | None]:
    start_date = (
        investigation_date
        - timedelta(
            days=HISTORY_LOOKBACK_DAYS
        )
    )

    # Add one day because some APIs treat
    # end_date as an exclusive boundary.
    end_date = (
        investigation_date
        + timedelta(days=1)
    )

    candles = await (
        app.state.twelve_data_provider
        .get_daily_candles(
            symbol=symbol,
            output_size=150,
            start_date=start_date,
            end_date=end_date,
        )
    )

    target_index = next(
        (
            index
            for index, candle
            in enumerate(candles)
            if candle.start_time.date()
            == investigation_date
        ),
        None,
    )

    if target_index is None:
        raise ValueError(
            "No completed trading candle was "
            f"found for {symbol} on "
            f"{investigation_date}. The date may "
            "be a weekend, holiday, or unavailable."
        )

    if target_index == 0:
        raise ValueError(
            "The previous trading day's candle "
            "is unavailable."
        )

    target_candle = candles[
        target_index
    ]

    previous_candle = candles[
        target_index - 1
    ]

    absolute_change = (
        target_candle.close
        - previous_candle.close
    )

    change_percent = (
        absolute_change
        / previous_candle.close
        * 100
    )

    market_context = {
        "type": "daily_market_context",
        "source": target_candle.source,
        "symbol": symbol,
        "trading_date": (
            investigation_date.isoformat()
        ),
        "previous_close": (
            previous_candle.close
        ),
        "open": target_candle.open,
        "high": target_candle.high,
        "low": target_candle.low,
        "close": target_candle.close,
        "volume": target_candle.volume,
        "absolute_change": absolute_change,
        "change_percent": change_percent,
        "timestamp": (
            target_candle.start_time
            .isoformat()
        ),
        "session": "regular",
        "timeframe": "1day",
    }

    anomaly_result = (
        app.state.daily_anomaly_detector
        .analyze_day(
            symbol=symbol,
            trading_date=investigation_date,
            candles=candles,
        )
    )

    anomaly_context = (
        anomaly_result.model_dump(
            mode="json"
        )
        if anomaly_result is not None
        else None
    )

    return (
        market_context,
        anomaly_context,
    )