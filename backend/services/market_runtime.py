import asyncio
from datetime import datetime, timezone

from fastapi import FastAPI

from backend.connection_manager import ConnectionManager
from backend.models import LiveCandleUpdate, MarketQuote
from backend.providers.finnhub_provider import FinnhubProvider
from backend.symbol_data import SYMBOLS
from backend.services.automatic_investigation import schedule_automatic_investigation


# The same manager is shared by the market service and WebSocket route.
connection_manager = ConnectionManager()


async def run_market_feed(app: FastAPI) -> None:
    """Receive Finnhub trades and turn them into dashboard updates."""
    while True:
        try:
            subscribed_symbols = list(
                app.state.market_quotes.keys()
            )

            async for trade in (
                app.state.finnhub_provider.stream_trades(
                    symbols=subscribed_symbols
                )
            ):
                print(
                    f"Real Finnhub trade: "
                    f"{trade.symbol} "
                    f"price={trade.price} "
                    f"size={trade.size} "
                    f"time={trade.timestamp}"
                )

                # Keep the server's latest quote in sync with live trades.
                current_quote = (
                    app.state.market_quotes.get(
                        trade.symbol
                    )
                )

                if current_quote is not None:
                    absolute_change = (
                        trade.price
                        - current_quote.previous_close
                    )

                    change_percent = (
                        absolute_change
                        / current_quote.previous_close
                        * 100
                    )

                    app.state.market_quotes[
                        trade.symbol
                    ] = current_quote.model_copy(
                        update={
                            "price": trade.price,
                            "absolute_change": absolute_change,
                            "change_percent": change_percent,
                            "day_high": max(
                                current_quote.day_high,
                                trade.price,
                            ),
                            "day_low": min(
                                current_quote.day_low,
                                trade.price,
                            ),
                            "timestamp": trade.timestamp,
                        }
                    )

                candle_updates = (
                    app.state.candle_aggregator
                    .process_trade(trade)
                )

                # React uses the raw trade to update displayed prices.
                await connection_manager.broadcast(
                    trade
                )

                for candle_update in candle_updates:
                    await publish_candle_update(
                        app=app,
                        candle=candle_update,
                    )

        except asyncio.CancelledError:
            # Allow FastAPI to stop this background task cleanly.
            raise

        except Exception as error:
            print(
                "Finnhub stream disconnected: ",
                type(error).__name__,
            )
            print("Trying again in 5 seconds...")
            await asyncio.sleep(5)


async def publish_candle_update(
    app: FastAPI,
    candle: LiveCandleUpdate,
) -> None:
    """Send a candle to React and analyse it when it is finalized."""
    await connection_manager.broadcast(candle)

    # Forming candles are still changing, so ML only sees final candles.
    if candle.status != "finalized":
        return

    anomaly_result = (
        app.state.anomaly_detector
        .analyze_finalized_candle(candle)
    )

    if anomaly_result is None:
        return

    # Agents can later read the latest result for the selected symbol.
    app.state.latest_anomaly_results[
        anomaly_result.symbol
    ] = anomaly_result

    print(
        "Anomaly analysis: "
        f"{anomaly_result.symbol} "
        f"{anomaly_result.start_time} "
        f"anomaly={anomaly_result.is_anomaly} "
        f"score={anomaly_result.decision_score:.6f}"
    )

    await connection_manager.broadcast(
        anomaly_result
    )

    schedule_automatic_investigation(app = app,
                                     anomaly_result=anomaly_result,
                                     connection_manager=connection_manager)


async def run_candle_finalizer(
    app: FastAPI,
) -> None:
    """Finalize expired candles even when no new trade arrives."""
    while True:
        await asyncio.sleep(1)

        finalized_candles = (
            app.state.candle_aggregator
            .finalize_expired(
                now=datetime.now(timezone.utc)
            )
        )

        for candle in finalized_candles:
            print(
                "Finalized candle: "
                f"{candle.symbol} "
                f"{candle.start_time} "
                f"close={candle.close}"
            )

            await publish_candle_update(
                app=app,
                candle=candle,
            )


async def load_initial_quotes(
    finnhub_provider: FinnhubProvider,
) -> dict[str, MarketQuote]:
    """Load one starting quote for every configured symbol."""
    quote_requests = [
        finnhub_provider.get_quote(
            symbol=symbol_info.symbol
        )
        for symbol_info in SYMBOLS
    ]

    results = await asyncio.gather(
        *quote_requests,
        return_exceptions=True,
    )

    quotes_by_symbol = {}

    for symbol_info, result in zip(
        SYMBOLS,
        results,
    ):
        if isinstance(result, Exception):
            print(
                f"Could not load quote for "
                f"{symbol_info.symbol}: "
                f"{type(result).__name__}"
            )
            continue

        quotes_by_symbol[
            symbol_info.symbol
        ] = result

    return quotes_by_symbol


async def seed_anomaly_detector(
    app: FastAPI,
) -> None:
    """Give each ML model enough historical candles for its features."""
    model_symbols = (
        app.state.anomaly_detector.model_symbols
    )

    history_requests = [
        app.state.twelve_data_provider
        .get_recent_candles(
            symbol=symbol,
            output_size=100,
        )
        for symbol in model_symbols
    ]

    results = await asyncio.gather(
        *history_requests,
        return_exceptions=True,
    )

    for symbol, result in zip(
        model_symbols,
        results,
    ):
        if isinstance(result, Exception):
            print(
                "Could not seed anomaly history "
                f"for {symbol}: "
                f"{type(result).__name__}"
            )
            continue

        app.state.anomaly_detector.seed_candles(
            symbol=symbol,
            candles=result,
        )

        print(
            "Anomaly history seeded: "
            f"{symbol} {len(result)} candles"
        )

        # This provides a latest result even while the market is closed.
        if result:
            latest_result = app.state.anomaly_detector.analyze_finalized_candle(result[-1])

            if latest_result is not None:
                app.state.latest_anomaly_results[symbol] = latest_result
                print(
                    "Latest anomaly result stored: "
                    f"{symbol} "
                    f"anomaly={latest_result.is_anomaly} "
                    f"score={latest_result.decision_score:.6f}"
                )
            else:
                print(
                    "No anomaly result created for "
                    f"{symbol}"
                )