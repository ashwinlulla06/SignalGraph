from dataclasses import dataclass
from backend.providers.finnhub_provider import FinnhubProvider

@dataclass
class AgentRuntimeContext:
    finnhub_provider : FinnhubProvider

