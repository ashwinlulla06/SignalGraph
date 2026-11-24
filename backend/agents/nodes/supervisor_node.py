from backend.agents.state import InvestigationState
from langchain_core.messages import HumanMessage, SystemMessage
from backend.agents.model import gemini_model
from backend.agents.schemas import SupervisorPlan


async def supervisor_node(state: InvestigationState) -> dict:

    structured_supervisor = gemini_model.with_structured_output(SupervisorPlan)

    system_prompt = """
    You are the Supervisor for SignalGraph,
    a financial market investigation system.

    The investigation scope is supplied by the backend.

    When the scope is "live", evaluate the latest
    available market movement and one-minute anomaly
    context.

    When the scope is "trading_day", evaluate the
    complete historical trading day identified by the
    investigation date.

    Do not replace historical information with current
    market information.

    Select only the specialist agents needed to investigate the question.
    Available agents:

    market_data:
    Quotes, candles and price movement.

    technical:
    Returns, volatility, drawdown and trend.

    anomaly:
    Anomaly score, persistence and data quality.

    cross_market:
    Comparision with other companies and indices.

    sector:
    Industry and peer-company context.

    macro:
    Economic releases, rates and broad catalysts.

    filings:
    SEC filings, investor relations and company annoucements.

    news:
    Time-aligned financial news research.

    regulatory:
    Trading halts, exchange notices and regulatory actions.

    risk:
    Liquidity, volatility and evidence risks.

    skeptic:
    The skeptic is a review agent.
    Select skeptic only when at least one other evidence-producing specialist is also selected.
    Never select skeptic by itself.

    verifier:
    Checks whether specialist claims are supported by the collected evidence.

    The verifier is a review agent.
    Select verifier only when at least one evidence-producing specialist is also selected.
    Never select verifier by itself.
    """

    user_prompt = f"""
    Trigger:
    {state["trigger"]}

    Symbol:
    {state["symbol"]}

    Investigation scope:
    {state["investigation_scope"]}

    Investigation date:
    {state.get("investigation_date")}

    Question:
    {state["question"]}
    """

    plan = await structured_supervisor.ainvoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
    )

    handoffs = [
        {
            "from_agent" : "supervisor",
            "to_agent" : agent_key,
            "summary" : plan.routing_summary
        }
        for agent_key in plan.selected_agents
    ]

    return {
        "status" : "running",
        "selected_agents" : plan.selected_agents,
        "handoffs" : handoffs
    }
