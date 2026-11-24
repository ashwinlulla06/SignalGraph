import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from backend.candle_aggregator import LiveCandleAggregator
from backend.config import FINNHUB_API_TOKEN
from backend.config import TWELVE_DATA_API_KEY
from backend.ml.anomaly_detector import AnomalyDetector
from backend.providers.finnhub_provider import FinnhubProvider
from backend.providers.twelve_data_provider import TwelveDataProvider
from backend.services.market_runtime import load_initial_quotes
from backend.services.market_runtime import run_candle_finalizer
from backend.services.market_runtime import run_market_feed
from backend.services.market_runtime import seed_anomaly_detector
from backend.ml.daily_anomaly_detector import DailyAnomalyDetector


MODEL_ARTIFACT_DIRECTORY = (
    Path(__file__).resolve().parent
    / "ml"
    / "artifacts"
)

DAILY_MODEL_ARTIFACT_DIRECTORY = Path(__file__).resolve().parent/"ml"/"daily_artifacts"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create shared services at startup and close them at shutdown."""
    print("Starting SignalGraph")

    # Providers are shared by routes and background tasks through app.state.
    app.state.finnhub_provider = (
        FinnhubProvider(
            api_token=FINNHUB_API_TOKEN
        )
    )

    app.state.twelve_data_provider = (
        TwelveDataProvider(
            api_key=TWELVE_DATA_API_KEY
        )
    )

    # Load the first dashboard values before accepting requests.
    app.state.market_quotes = (
        await load_initial_quotes(
            finnhub_provider=(
                app.state.finnhub_provider
            )
        )
    )

    print(
        "Initial Finnhub quotes loaded:",
        len(app.state.market_quotes),
    )

    app.state.candle_aggregator = (
        LiveCandleAggregator()
    )

    app.state.anomaly_detector = (
        AnomalyDetector(
            artifact_directory=(
                MODEL_ARTIFACT_DIRECTORY
            )
        )
    )

    app.state.daily_anomaly_detector = DailyAnomalyDetector(
        artifact_directory=DAILY_MODEL_ARTIFACT_DIRECTORY
    )

    app.state.latest_anomaly_results = {}

    # Historical candles prepare the ML models for live analysis.
    await seed_anomaly_detector(app)

    # These tasks continue running while FastAPI serves requests.
    market_feed_task = asyncio.create_task(
        run_market_feed(app)
    )

    candle_finalizer_task = (
        asyncio.create_task(
            run_candle_finalizer(app)
        )
    )

    try:
        # FastAPI handles requests while execution is paused here.
        yield

    finally:
        print("Stopping SignalGraph")

        background_tasks = [
            market_feed_task,
            candle_finalizer_task,
        ]

        # Stop both infinite background loops cleanly.
        for task in background_tasks:
            task.cancel()

        for task in background_tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Close the reusable HTTP clients owned by the providers.
        await (
            app.state.finnhub_provider.close()
        )

        await (
            app.state.twelve_data_provider.close()
        )
