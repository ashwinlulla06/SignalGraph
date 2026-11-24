import operator
from typing import Annotated, Literal, TypedDict

class AgentFinding(TypedDict):   # Conclusion returned by the specialist agent.
    agent_key : str
    summary : str
    confidence : float
    evidence_ids : list[str]

class EvidenceItem(TypedDict):   # Evidence that supports agent's conclusion
    evidence_id : str
    agent_key : str
    title : str
    source_name : str
    source_url : str | None
    summary : str
    published_at : str | None

class AgentHandoff(TypedDict):
    from_agent : str
    to_agent : str
    summary : str

class InvestigationState(TypedDict, total=False):
    investigation_id : str
    trigger : Literal['user_question', 'market_anomaly']
    question : str
    symbol : str

    investigation_date: str

    investigation_scope: Literal["live", "trading_day"]
    
    status : str

    selected_agents : list[str]

    market_context : dict

    anomaly_context : dict | None

    findings : Annotated[list[AgentFinding], operator.add]

    evidence : Annotated[list[EvidenceItem], operator.add]

    handoffs : Annotated[list[AgentHandoff], operator.add]

    errors : Annotated[list[str], operator.add]

    final_report : str

