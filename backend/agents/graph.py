from langgraph.graph import START, END, StateGraph
from langgraph.types import Send
from backend.agents.nodes.creating_specialist_nodes import specialist_nodes
from backend.agents.nodes.supervisor_node import supervisor_node
from backend.agents.nodes.synthesis_node import synthesis_node
from backend.agents.nodes.skeptic_node import skeptic_node
from backend.agents.nodes.verifier_node import verifier_node
from backend.agents.state import InvestigationState
from backend.agents.context import AgentRuntimeContext


def route_to_selected_agents(state : InvestigationState):
    review_agents = {
        "verifier", "skeptic"
    }

    research_agents = [
        agent_key
        for agent_key in state['selected_agents']
        if agent_key not in review_agents
    ]

    if not research_agents:
        research_agents = ['market_data']

    return [
        Send(agent_key, state)
        for agent_key in research_agents
    ]

def review_gate_node(state: InvestigationState) -> dict:
    return {}

def route_after_research(state: InvestigationState) -> str:
    if "verifier" in state['selected_agents']:
        return "verifier"
    
    if "skeptic" in state['selected_agents']:
        return "skeptic"
    
    return "synthesis"

def route_after_verifier(state : InvestigationState) -> str:
    if "skeptic" in state['selected_agents']:
        return "skeptic"

    return "synthesis"

graph_builder = StateGraph(InvestigationState, context_schema=AgentRuntimeContext)

graph_builder.add_node("supervisor", supervisor_node)

for agent_key, agent_node in specialist_nodes.items():
    graph_builder.add_node(agent_key, agent_node)
    graph_builder.add_edge(agent_key, "review_gate")

graph_builder.add_node("review_gate", review_gate_node)
graph_builder.add_node("skeptic", skeptic_node)
graph_builder.add_node("verifier", verifier_node)
graph_builder.add_node("synthesis", synthesis_node)

graph_builder.add_edge(START, "supervisor")
graph_builder.add_conditional_edges("supervisor", route_to_selected_agents)
graph_builder.add_conditional_edges(
    "review_gate", 
    route_after_research,
    {
        "verifier" : "verifier",
        "skeptic" : "skeptic",
        "synthesis" : "synthesis"
    }
)
graph_builder.add_conditional_edges(
    "verifier",
    route_after_verifier,
    {
        "skeptic" : "skeptic",
        "synthesis" : "synthesis"
    }
)
graph_builder.add_edge("skeptic", "synthesis")
graph_builder.add_edge("synthesis", END)

investigation_graph = graph_builder.compile()


