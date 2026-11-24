from backend.agents.state import InvestigationState
from backend.agents.nodes.news_node import news_node
from backend.agents.nodes.anomaly_node import anomaly_node
from backend.agents.nodes.market_data_node import market_data_node
# from backend.agents.nodes.skeptic_node import skeptic_node
from backend.agents.nodes.technical_node import technical_node
# from backend.agents.nodes.verifier_node import verifier_node

def create_test_specialist_node(agent_key : str):
    def specialist_node(state : InvestigationState) -> dict:
        symbol = state['symbol']

        return {
            "findings" : [
                {
                    "agent_key" : agent_key,
                    "summary" : f"Test finding from {agent_key} for {symbol}",
                    "confidence" : 1.0,
                    "evidence_ids" : []
                }
            ],

            "handoffs" : [
                {
                    "from_agent" : agent_key,
                    "to_agent": "synthesis",
                    "summary": f"{agent_key} test finding is ready."
                }
            ]
        }

    return specialist_node

specialist_nodes = {
    "market_data": market_data_node,

    "technical": technical_node,

    "anomaly": anomaly_node,

    "cross_market":
        create_test_specialist_node(
            "cross_market"
        ),

    "sector":
        create_test_specialist_node(
            "sector"
        ),

    "macro":
        create_test_specialist_node(
            "macro"
        ),

    "filings":
        create_test_specialist_node(
            "filings"
        ),

    "news": news_node,

    "regulatory":
        create_test_specialist_node(
            "regulatory"
        ),

    "risk":
        create_test_specialist_node(
            "risk"
        ),

    # "skeptic": skeptic_node,

    # "verifier": verifier_node,
}
