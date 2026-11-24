from datetime import datetime
from datetime import timezone

from backend.models import (
    LiveCandleUpdate,
)
from backend.models import (
    ProviderTrade,
)


class LiveCandleAggregator:
    def __init__(self):
        self._current_candles: dict[
            str,
            LiveCandleUpdate,
        ] = {}

    @staticmethod
    def _get_minute_start(
        timestamp: datetime,
    ) -> datetime:
        utc_timestamp = (
            timestamp.astimezone(
                timezone.utc
            )
        )

        return utc_timestamp.replace(
            second=0,
            microsecond=0,
        )

    @staticmethod
    def _create_candle(
        trade: ProviderTrade,
        minute_start: datetime,
    ) -> LiveCandleUpdate:
        return LiveCandleUpdate(
            status="forming",
            symbol=trade.symbol,
            start_time=minute_start,
            open=trade.price,
            high=trade.price,
            low=trade.price,
            close=trade.price,
            volume=trade.size,
            trade_count=1,
            first_trade_time=(
                trade.timestamp
            ),
            last_trade_time=(
                trade.timestamp
            ),
        )

    def process_trade(
        self,
        trade: ProviderTrade,
    ) -> list[LiveCandleUpdate]:
        minute_start = (
            self._get_minute_start(
                trade.timestamp
            )
        )

        current_candle = (
            self._current_candles.get(
                trade.symbol
            )
        )

        if current_candle is None:
            new_candle = (
                self._create_candle(
                    trade=trade,
                    minute_start=(
                        minute_start
                    ),
                )
            )

            self._current_candles[
                trade.symbol
            ] = new_candle

            return [new_candle]

        if (
            minute_start <
            current_candle.start_time
        ):
            return []

        if (
            minute_start ==
            current_candle.start_time
        ):
            if (
                current_candle.status
                == "finalized"
            ):
                return []

            updated_candle = (
                self._update_candle(
                    current_candle=(
                        current_candle
                    ),
                    trade=trade,
                )
            )

            self._current_candles[
                trade.symbol
            ] = updated_candle

            return [updated_candle]

        updates = []

        if (
            current_candle.status
            == "forming"
        ):
            finalized_candle = (
                current_candle.model_copy(
                    update={
                        "status":
                            "finalized"
                    }
                )
            )

            updates.append(
                finalized_candle
            )

        new_candle = (
            self._create_candle(
                trade=trade,
                minute_start=minute_start,
            )
        )

        self._current_candles[
            trade.symbol
        ] = new_candle

        updates.append(new_candle)

        return updates

    @staticmethod
    def _update_candle(
        current_candle:
            LiveCandleUpdate,
        trade: ProviderTrade,
    ) -> LiveCandleUpdate:
        trade_is_first = (
            trade.timestamp <
            current_candle
            .first_trade_time
        )

        trade_is_latest = (
            trade.timestamp >=
            current_candle
            .last_trade_time
        )

        return (
            current_candle.model_copy(
                update={
                    "open": (
                        trade.price
                        if trade_is_first
                        else
                        current_candle.open
                    ),
                    "high": max(
                        current_candle.high,
                        trade.price,
                    ),
                    "low": min(
                        current_candle.low,
                        trade.price,
                    ),
                    "close": (
                        trade.price
                        if trade_is_latest
                        else
                        current_candle.close
                    ),
                    "volume": (
                        current_candle.volume
                        + trade.size
                    ),
                    "trade_count": (
                        current_candle
                        .trade_count
                        + 1
                    ),
                    "first_trade_time": min(
                        current_candle
                        .first_trade_time,
                        trade.timestamp,
                    ),
                    "last_trade_time": max(
                        current_candle
                        .last_trade_time,
                        trade.timestamp,
                    ),
                }
            )
        )

    def finalize_expired(
        self,
        now: datetime,
    ) -> list[LiveCandleUpdate]:
        current_minute = (
            self._get_minute_start(now)
        )

        finalized_updates = []

        for symbol, candle in (
            self._current_candles.items()
        ):
            candle_has_expired = (
                candle.start_time <
                current_minute
            )

            if (
                candle.status == "forming"
                and candle_has_expired
            ):
                finalized_candle = (
                    candle.model_copy(
                        update={
                            "status":
                                "finalized"
                        }
                    )
                )

                self._current_candles[
                    symbol
                ] = finalized_candle

                finalized_updates.append(
                    finalized_candle
                )

        return finalized_updates