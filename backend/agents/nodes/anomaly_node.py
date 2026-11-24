from backend.agents.state import (
    InvestigationState,
)


def anomaly_node(
    state: InvestigationState,
) -> dict:
    symbol = state["symbol"]

    scope = state[
        "investigation_scope"
    ]

    context = state.get(
        "anomaly_context"
    )

    if context is None:
        period = (
            state["investigation_date"]
            if scope == "trading_day"
            else "the latest minute"
        )

        summary = (
            "No anomaly analysis is "
            f"currently available for "
            f"{symbol} for {period}."
        )

        return {
            "findings": [
                {
                    "agent_key": "anomaly",
                    "summary": summary,
                    "confidence": 0.0,
                    "evidence_ids": [],
                }
            ],
            "handoffs": [
                {
                    "from_agent": "anomaly",
                    "to_agent": "review_gate",
                    "summary": summary,
                }
            ],
        }

    is_anomaly = context[
        "is_anomaly"
    ]

    decision_score = context[
        "decision_score"
    ]

    analyzed_at = context[
        "analyzed_at"
    ]

    classification = (
        "was classified as anomalous"
        if is_anomaly
        else "was not classified as anomalous"
    )

    if scope == "trading_day":
        trading_date = context[
            "trading_date"
        ]

        summary = (
            f"The complete trading day "
            f"for {symbol} on "
            f"{trading_date} "
            f"{classification} by the "
            f"daily Isolation Forest. "
            f"The decision score was "
            f"{decision_score:.6f}. Lower "
            f"and negative scores indicate "
            f"more unusual daily behaviour."
        )

        evidence_id = (
            f"daily-anomaly-"
            f"{symbol.lower()}-"
            f"{trading_date}"
        )

        title = (
            f"{symbol} daily anomaly "
            f"analysis for {trading_date}"
        )

        source_name = (
            "SignalGraph Daily "
            "Isolation Forest"
        )

    else:
        start_time = context[
            "start_time"
        ]

        summary = (
            f"The latest analyzed "
            f"one-minute candle for "
            f"{symbol} at {start_time} "
            f"{classification}. "
            f"The decision score was "
            f"{decision_score:.6f}. Lower "
            f"and negative scores indicate "
            f"more unusual one-minute "
            f"behaviour."
        )

        evidence_id = (
            f"live-anomaly-"
            f"{symbol.lower()}"
        )

        title = (
            f"{symbol} latest one-minute "
            f"anomaly analysis"
        )

        source_name = (
            "SignalGraph Minute "
            "Isolation Forest"
        )

    evidence = {
        "evidence_id": evidence_id,
        "agent_key": "anomaly",
        "title": title,
        "source_name": source_name,
        "source_url": None,
        "summary": summary,
        "published_at": analyzed_at,
    }

    return {
        "findings": [
            {
                "agent_key": "anomaly",
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
                "from_agent": "anomaly",
                "to_agent": "review_gate",
                "summary": (
                    "Anomaly analysis "
                    "is ready."
                ),
            }
        ],
    }