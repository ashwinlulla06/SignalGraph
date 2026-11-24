from backend.agents.state import (
    InvestigationState,
)


def build_live_market_finding(
    state: InvestigationState,
) -> dict:
    context = state["market_context"]

    symbol = context["symbol"]
    price = context["price"]

    previous_close = context[
        "previous_close"
    ]

    absolute_change = context[
        "absolute_change"
    ]

    change_percent = context[
        "change_percent"
    ]

    day_open = context["day_open"]
    day_high = context["day_high"]
    day_low = context["day_low"]

    timestamp = context["timestamp"]

    if change_percent > 0:
        direction = "up"
    elif change_percent < 0:
        direction = "down"
    else:
        direction = "unchanged"

    summary = (
        f"{symbol} is currently {direction} "
        f"{abs(change_percent):.2f}% at "
        f"${price:.2f}. The price moved "
        f"${abs(absolute_change):.2f} from "
        f"the previous close of "
        f"${previous_close:.2f}. "
        f"The current session range is "
        f"${day_low:.2f} to "
        f"${day_high:.2f}, with an opening "
        f"price of ${day_open:.2f}."
    )

    evidence_id = (
        f"live-market-"
        f"{symbol.lower()}"
    )

    evidence = {
        "evidence_id": evidence_id,
        "agent_key": "market_data",
        "title": (
            f"{symbol} live market quote"
        ),
        "source_name": "Finnhub",
        "source_url": (
            "https://finnhub.io/"
        ),
        "summary": summary,
        "published_at": timestamp,
    }

    return {
        "findings": [
            {
                "agent_key": "market_data",
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
                "from_agent": "market_data",
                "to_agent": "review_gate",
                "summary": (
                    "Live market analysis "
                    "is ready."
                ),
            }
        ],
    }


def build_daily_market_finding(
    state: InvestigationState,
) -> dict:
    context = state["market_context"]

    symbol = context["symbol"]

    trading_date = context["trading_date"]

    previous_close = context["previous_close"]

    day_open = context["open"]
    day_high = context["high"]
    day_low = context["low"]
    day_close = context["close"]
    volume = context["volume"]

    absolute_change = context[
        "absolute_change"
    ]

    change_percent = context[
        "change_percent"
    ]

    if change_percent > 0:
        direction = "gained"
    elif change_percent < 0:
        direction = "declined"
    else:
        direction = "was unchanged"

    if change_percent == 0:
        movement_text = (
            f"{symbol} was unchanged"
        )
    else:
        movement_text = (
            f"{symbol} {direction} "
            f"{abs(change_percent):.2f}%"
        )

    summary = (
        f"On {trading_date}, "
        f"{movement_text}, closing at "
        f"${day_close:.2f}. "
        f"The previous close was "
        f"${previous_close:.2f}, and the "
        f"absolute movement was "
        f"${abs(absolute_change):.2f}. "
        f"The stock opened at "
        f"${day_open:.2f}, traded between "
        f"${day_low:.2f} and "
        f"${day_high:.2f}, and recorded "
        f"volume of {volume:,.0f} shares."
    )

    evidence_id = (
        f"daily-market-"
        f"{symbol.lower()}-"
        f"{trading_date}"
    )

    evidence = {
        "evidence_id": evidence_id,
        "agent_key": "market_data",
        "title": (
            f"{symbol} daily market data "
            f"for {trading_date}"
        ),
        "source_name": "Twelve Data",
        "source_url": (
            "https://twelvedata.com/"
        ),
        "summary": summary,
        "published_at": context[
            "timestamp"
        ],
    }

    return {
        "findings": [
            {
                "agent_key": "market_data",
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
                "from_agent": "market_data",
                "to_agent": "review_gate",
                "summary": (
                    "Daily market analysis "
                    "is ready."
                ),
            }
        ],
    }


def market_data_node(
    state: InvestigationState,
) -> dict:
    scope = state["investigation_scope"]

    if scope == "trading_day":
        return build_daily_market_finding(state)

    return build_live_market_finding(state)