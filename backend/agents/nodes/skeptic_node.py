from langchain_core.messages import HumanMessage, SystemMessage
from backend.agents.model import gemini_model
from backend.agents.schemas import SkepticAnalysis
from backend.agents.state import InvestigationState

async def skeptic_node(state:InvestigationState) -> dict:
    findings = state.get("findings", [])
    evidence = state.get("evidence", [])

    if not findings:
        summary = "There were no specialist findings available for skeptical review."

        return {
            "findings": [
                {
                    "agent_key" : "skeptic",
                    "summary" : summary,
                    "confidence" : 0.0,
                    "evidence_ids" : []
                }
            ],

            "handoffs" : [
                {
                    "from_agent": "skeptic",
                    "to_agent": "synthesis",
                    "summary": summary
                }
            ]
        }

    finding_blocks = []

    for finding in findings:
        finding_blocks.append(
            (
                f"Agent: "
                f"{finding['agent_key']}\n"
                f"Confidence: "
                f"{finding['confidence']}\n"
                f"Evidence IDs: "
                f"{finding['evidence_ids']}\n"
                f"Summary: "
                f"{finding['summary']}"
            )
        )

    findings_text = "\n\n".join(finding_blocks)

    evidence_blocks = []

    for item in evidence:
        evidence_blocks.append(
            (
                f"Evidence ID: "
                f"{item['evidence_id']}\n"
                f"Agent: "
                f"{item['agent_key']}\n"
                f"Title: "
                f"{item['title']}\n"
                f"Source: "
                f"{item['source_name']}\n"
                f"Published: "
                f"{item['published_at']}\n"
                f"Summary: "
                f"{item['summary']}"
            )
        )

    if evidence_blocks:
        evidence_text = "\n\n".join(evidence_blocks)
    else:
        evidence_text = "No supporting evidence items were provided"

    structured_skeptic_model = gemini_model.with_structured_output(SkepticAnalysis)

    system_prompt = """
    You are the Skeptic specialist for
    SignalGraph.

    Review the supplied specialist findings and
    evidence. Your job is to challenge weak or
    unsupported conclusions.

    Check for:
    - unsupported causal claims,
    - indirect or irrelevant evidence,
    - conflicting findings,
    - mismatched timestamps,
    - pre-market versus regular-session mismatch,
    - low-quality or missing sources,
    - conclusions that are stronger than the data,
    - alternative explanations that remain open.

    Do not introduce new external facts.
    Use only the supplied findings and evidence.

    Do not repeat a specific news event unless the
    finding cites an evidence ID and the matching
    evidence supports it. An empty evidence ID list
    means no cited news evidence was supplied.

    Do not reject a claim merely to sound
    skeptical. If a claim is properly supported,
    acknowledge that.

    Clearly distinguish:
    - what is supported,
    - what is uncertain,
    - what remains unexplained.

    Return only evidence IDs that were supplied.
    """

    user_prompt = f"""
    Symbol:
    {state['symbol']}

    Original question:
    {state['question']}

    Specialist findings:

    {findings_text}

    Available evidence:

    {evidence_text}
    """

    analysis = await structured_skeptic_model.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])

    valid_evidence_ids = {
        item["evidence_id"]
        for item in evidence
    }

    reviewed_evidence_ids = []

    for evidence_id in analysis.reviewed_evidence_ids:
        if (evidence_id in valid_evidence_ids) and (evidence_id not in reviewed_evidence_ids):
            reviewed_evidence_ids.append(evidence_id)

    skeptic_finding = {
        "agent_key" : "skeptic",
        "summary" : analysis.summary,
        "confidence" : analysis.confidence,
        "evidence_ids" : reviewed_evidence_ids
    }

    return {
        "findings" : [skeptic_finding],
        "handoffs" : [
            {
                "from_agent": "skeptic",
                "to_agent": "synthesis",
                "summary": (
                    "Skeptical review of the "
                    "findings is ready."
                )
            }
        ]
    }
