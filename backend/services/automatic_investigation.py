import asyncio

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel

from backend.agents.graph import investigation_graph
from backend.connection_manager import ConnectionManager
from backend.models import MarketAnomalyResult


# Do not investigate weak anomalies.
# Lower scores indicate more unusual behaviour.
MINIMUM_ANOMALY_SCORE = -0.03

# Prevent repeated Gemini calls for the same company.
INVESTIGATION_COOLDOWN = timedelta(
    minutes=30
)

# Keep only the latest completed automatic investigations.
MAX_STORED_INVESTIGATIONS = 20


class AutomaticInvestigationEvent(BaseModel):
    """
    WebSocket message sent to React when an automatic
    investigation starts, completes, or fails.
    """

    type: Literal[
        "automatic_investigation_started",
        "automatic_investigation_completed",
        "automatic_investigation_failed",
    ]

    investigation_id: str
    symbol: str

    trigger: Literal[
        "market_anomaly"
    ] = "market_anomaly"

    result: dict | None = None
    error: str | None = None


def schedule_automatic_investigation(
    app: FastAPI,
    anomaly_result: MarketAnomalyResult,
    connection_manager: ConnectionManager,
) -> None:
    """
    Decide whether the anomaly should start an investigation.

    This function does not wait for Gemini. It creates a
    separate background task so the market feed can continue.
    """

    # Normal candles should not start investigations.
    if not anomaly_result.is_anomaly:
        return

    # Ignore anomalies that are only slightly below zero.
    if (
        anomaly_result.decision_score
        > MINIMUM_ANOMALY_SCORE
    ):
        return

    symbol = anomaly_result.symbol

    last_candle_time = (
        app.state
        .automatic_investigation_last_candle
        .get(symbol)
    )

    # Prevent the same candle from triggering twice.
    if (
        last_candle_time is not None
        and anomaly_result.start_time
        <= last_candle_time
    ):
        return

    now = datetime.now(timezone.utc)

    last_started_time = (
        app.state
        .automatic_investigation_last_started
        .get(symbol)
    )

    # Prevent several investigations for the same company
    # during a short period.
    if (
        last_started_time is not None
        and now - last_started_time
        < INVESTIGATION_COOLDOWN
    ):
        print(
            "Automatic investigation skipped: "
            f"{symbol} is still inside the cooldown"
        )
        return

    quote = app.state.market_quotes.get(symbol)

    # The agents need current market context.
    if quote is None:
        print(
            "Automatic investigation skipped: "
            f"no market quote is available for {symbol}"
        )
        return

    # Reserve this symbol and candle before creating the task.
    # This prevents another event from starting a duplicate.
    app.state.automatic_investigation_last_started[
        symbol
    ] = now

    app.state.automatic_investigation_last_candle[
        symbol
    ] = anomaly_result.start_time

    investigation_id = str(uuid4())

    task = asyncio.create_task(
        run_automatic_investigation(
            app=app,
            investigation_id=investigation_id,
            anomaly_result=anomaly_result,
            connection_manager=connection_manager,
        )
    )

    # Keep a reference to the task while it is running.
    app.state.automatic_investigation_tasks.add(
        task
    )

    # Remove the reference after the task finishes.
    task.add_done_callback(
        app.state
        .automatic_investigation_tasks
        .discard
    )


async def run_automatic_investigation(
    app: FastAPI,
    investigation_id: str,
    anomaly_result: MarketAnomalyResult,
    connection_manager: ConnectionManager,
) -> None:
    """
    Build the automatic question and run the LangGraph workflow.
    """

    symbol = anomaly_result.symbol

    quote = app.state.market_quotes.get(symbol)

    # The quote might disappear between scheduling and execution.
    if quote is None:
        return

    question = (
        f"Investigate the anomalous one-minute movement "
        f"detected for {symbol} at "
        f"{anomaly_result.start_time.isoformat()}. "
        f"Explain how unusual the movement was and "
        f"whether recent market or company evidence "
        f"provides a credible explanation."
    )

    initial_state = {
        "investigation_id": investigation_id,
        "trigger": "market_anomaly",
        "question": question,
        "symbol": symbol,
        "investigation_date": None,
        "investigation_scope": "live",
        "status": "created",
        "selected_agents": [],
        "market_context": (
            quote.model_dump(mode="json")
        ),
        "anomaly_context": (
            anomaly_result.model_dump(
                mode="json"
            )
        ),
        "findings": [],
        "evidence": [],
        "handoffs": [],
        "errors": [],
        "final_report": "",
    }

    started_event = AutomaticInvestigationEvent(
        type="automatic_investigation_started",
        investigation_id=investigation_id,
        symbol=symbol,
    )

    await connection_manager.broadcast(
        started_event
    )

    print(
        "Automatic investigation started: "
        f"{symbol} {investigation_id}"
    )

    try:
        result = await investigation_graph.ainvoke(
            initial_state,
            context={
                "finnhub_provider": (
                    app.state.finnhub_provider
                )
            },
        )

        # Store only a small recent history in memory.
        app.state.automatic_investigations.insert(
            0,
            result,
        )

        del app.state.automatic_investigations[
            MAX_STORED_INVESTIGATIONS:
        ]

        completed_event = (
            AutomaticInvestigationEvent(
                type=(
                    "automatic_investigation_completed"
                ),
                investigation_id=investigation_id,
                symbol=symbol,
                result=result,
            )
        )

        await connection_manager.broadcast(
            completed_event
        )

        print(
            "Automatic investigation completed: "
            f"{symbol} {investigation_id}"
        )

    except asyncio.CancelledError:
        # Allow FastAPI to shut down cleanly.
        raise

    except Exception as error:
        # Gemini or another agent can fail, but the market
        # feed must continue running.
        error_message = (
            f"{type(error).__name__}: {error}"
        )

        failed_event = AutomaticInvestigationEvent(
            type="automatic_investigation_failed",
            investigation_id=investigation_id,
            symbol=symbol,
            error=error_message,
        )

        await connection_manager.broadcast(
            failed_event
        )

        print(
            "Automatic investigation failed: "
            f"{symbol} {error_message}"
        )