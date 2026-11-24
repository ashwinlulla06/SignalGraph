from backend.agents.state import (
    InvestigationState,
)


def unavailable_finding(
    state: InvestigationState,
) -> dict:
    symbol = state["symbol"]

    scope = state[
        "investigation_scope"
    ]

    if scope == "trading_day":
        period = (
            f"the trading day "
            f"{state['investigation_date']}"
        )
    else:
        period = (
            "the latest one-minute candle"
        )

    summary = (
        f"Technical features are currently "
        f"unavailable for {symbol} for "
        f"{period}."
    )

    return {
        "findings": [
            {
                "agent_key": "technical",
                "summary": summary,
                "confidence": 0.0,
                "evidence_ids": [],
            }
        ],
        "handoffs": [
            {
                "from_agent": "technical",
                "to_agent": "review_gate",
                "summary": summary,
            }
        ],
    }


def build_live_technical_finding(
    state: InvestigationState,
) -> dict:
    symbol = state["symbol"]

    context = state["anomaly_context"]

    features = context["features"]

    return_percent = features["return_1"] * 100

    range_percent = features["range_percent"] * 100

    body_percent = features["body_percent"] * 100

    rolling_volatility = (
        features["rolling_volatility"]
        * 100
    )

    start_time = context[
        "start_time"
    ]

    summary = (
        f"In the latest analyzed "
        f"one-minute candle, {symbol} "
        f"moved {return_percent:.3f}%. "
        f"The candle's high-to-low range "
        f"was {range_percent:.3f}%, its "
        f"body movement was "
        f"{body_percent:.3f}%, and rolling "
        f"volatility across the recent "
        f"20 one-minute returns was "
        f"{rolling_volatility:.3f}%."
    )

    evidence_id = (
        f"live-technical-"
        f"{symbol.lower()}"
    )

    evidence = {
        "evidence_id": evidence_id,
        "agent_key": "technical",
        "title": (
            f"{symbol} live technical "
            f"features"
        ),
        "source_name": (
            "SignalGraph Minute "
            "Feature Engine"
        ),
        "source_url": None,
        "summary": summary,
        "published_at": start_time,
    }

    return {
        "findings": [
            {
                "agent_key": "technical",
                "summary": summary,
                "confidence": 1.0,
                "evidence_ids": [
                    evidence_id
                ],
            }
        ],
        "evidence": [evidence],
        "handoffs": [
            {
                "from_agent": "technical",
                "to_agent": "review_gate",
                "summary": (
                    "Live technical analysis "
                    "is ready."
                ),
            }
        ],
    }


def build_daily_technical_finding(state: InvestigationState) -> dict:
    symbol = state["symbol"]

    trading_date = state[
        "investigation_date"
    ]

    context = state[
        "anomaly_context"
    ]

    features = context["features"]

    return_percent = (
        features["return_1"] * 100
    )

    range_percent = (
        features["range_percent"] * 100
    )

    gap_percent = (
        features["gap_percent"] * 100
    )

    rolling_volatility = (
        features[
            "rolling_volatility_20"
        ] * 100
    )

    volume_ratio = features[
        "volume_ratio_20"
    ]

    drawdown = (
        features[
            "drawdown_from_20_day_high"
        ] * 100
    )

    average_distance = (
        features[
            "distance_from_20_day_average"
        ] * 100
    )

    summary = (
        f"On {trading_date}, {symbol}'s "
        f"daily return was "
        f"{return_percent:.2f}%. "
        f"The day's range was "
        f"{range_percent:.2f}%, and its "
        f"opening gap was "
        f"{gap_percent:.2f}%. "
        f"Twenty-day rolling volatility "
        f"was {rolling_volatility:.2f}%. "
        f"Volume was {volume_ratio:.2f} "
        f"times its previous 20-day "
        f"average. The close was "
        f"{drawdown:.2f}% relative to the "
        f"previous 20-day high and "
        f"{average_distance:.2f}% relative "
        f"to the previous 20-day average."
    )

    evidence_id = (
        f"daily-technical-"
        f"{symbol.lower()}-"
        f"{trading_date}"
    )

    evidence = {
        "evidence_id": evidence_id,
        "agent_key": "technical",
        "title": (
            f"{symbol} daily technical "
            f"features for {trading_date}"
        ),
        "source_name": (
            "SignalGraph Daily "
            "Feature Engine"
        ),
        "source_url": None,
        "summary": summary,
        "published_at": trading_date,
    }

    return {
        "findings": [
            {
                "agent_key": "technical",
                "summary": summary,
                "confidence": 1.0,
                "evidence_ids": [
                    evidence_id
                ],
            }
        ],
        "evidence": [evidence],
        "handoffs": [
            {
                "from_agent": "technical",
                "to_agent": "review_gate",
                "summary": (
                    "Daily technical analysis "
                    "is ready."
                ),
            }
        ],
    }


def technical_node(state: InvestigationState) -> dict:
    if state.get("anomaly_context") is None:
        return unavailable_finding(state)

    if (
        state["investigation_scope"]
        == "trading_day"
    ):
        return (
            build_daily_technical_finding(
                state
            )
        )

    return build_live_technical_finding(
        state
    )