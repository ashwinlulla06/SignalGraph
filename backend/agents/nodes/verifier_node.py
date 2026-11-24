import json

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.runtime import Runtime

from backend.agents.context import AgentRuntimeContext
from backend.agents.model import gemini_model
from backend.agents.schemas import VerificationPlan
from backend.agents.schemas import VerifierAnalysis
from backend.agents.state import InvestigationState
from backend.agents.tools.verification_tools import (
    create_verification_tools,
)


def format_findings(findings: list[dict]) -> str:
    blocks = []

    for finding in findings:
        blocks.append(
            (
                f"Agent: {finding['agent_key']}\n"
                f"Claim: {finding['summary']}\n"
                f"Confidence: {finding['confidence']}\n"
                f"Evidence IDs: {finding['evidence_ids']}"
            )
        )

    return "\n\n".join(blocks)


def format_evidence(evidence: list[dict]) -> str:
    blocks = []

    for item in evidence:
        blocks.append(
            (
                f"Evidence ID: {item['evidence_id']}\n"
                f"Title: {item['title']}\n"
                f"Source: {item['source_name']}\n"
                f"Published: {item['published_at']}\n"
                f"Summary: {item['summary']}"
            )
        )

    if not blocks:
        return "No evidence was supplied."

    return "\n\n".join(blocks)


async def verifier_node(
    state: InvestigationState,
    runtime: Runtime[AgentRuntimeContext],
) -> dict:
    findings = state.get("findings", [])
    original_evidence = state.get("evidence", [])

    if not findings:
        return {
            "findings": [
                {
                    "agent_key": "verifier",
                    "summary": (
                        "No specialist findings were available "
                        "for verification."
                    ),
                    "confidence": 1.0,
                    "evidence_ids": [],
                }
            ],
            "handoffs": [
                {
                    "from_agent": "verifier",
                    "to_agent": "synthesis",
                    "summary": "No findings required verification.",
                }
            ],
        }

    findings_text = format_findings(findings)

    # Step 1: Gemini creates a small verification checklist.
    planner = gemini_model.with_structured_output(
        VerificationPlan
    )

    plan = await planner.ainvoke(
        [
            SystemMessage(
                content="""
                You plan evidence checks for a financial
                investigation.

                Select every check needed to verify the
                material claims. Return the smallest complete
                set, not merely one convenient check.

                Available checks:

                market_quote:
                Check a price or daily-movement claim.

                company_news:
                Recheck recent company-news claims.

                ai_sector:
                Compare the target stock with AI-linked peers
                when a finding uses sector, industry, technology
                or AI-market conditions as an explanation.

                government_policy:
                Search official policy documents when a finding
                mentions regulation, government action, tariffs,
                sanctions, antitrust or export controls.

                Do not produce a verdict. Only plan the checks.
                """
            ),
            HumanMessage(
                content=(
                    f"Symbol: {state['symbol']}\n\n"
                    f"Question: {state['question']}\n\n"
                    f"Findings:\n{findings_text}"
                )
            ),
        ]
    )

    # Step 2: Python executes every check in the plan.
    verification_tools = create_verification_tools(
        runtime.context.finnhub_provider
    )

    tools_by_name = {
        tool.name: tool
        for tool in verification_tools
    }

    check_configuration = {
        "market_quote": (
            "verify_current_market_quote",
            {"symbol": state["symbol"]},
        ),
        "company_news": (
            "verify_recent_company_news",
            {
                "symbol": state["symbol"],
                "lookback_days": 5,
                "limit": 5,
            },
        ),
        "ai_sector": (
            "verify_ai_sector_movement",
            {"target_symbol": state["symbol"]},
        ),
        "government_policy": (
            "search_government_policy_documents",
            {
                "query": (
                    f"{state['symbol']} artificial intelligence "
                    "semiconductor regulation export control"
                ),
                "lookback_days": 30,
                "limit": 5,
            },
        ),
    }

    tool_results = []
    tool_evidence = []
    tool_errors = []

    planned_checks = list(
        dict.fromkeys(plan.required_checks)
    )

    if state['investigation_scope'] == "trading_day":
        current_data_checks = {
            "market_quote",
            "company_news",
            "ai_sector",
            "government_policy"
        }

        planned_checks = [
            check_name
            for check_name in planned_checks
            if check_name not in current_data_checks
        ]

    print(
        "Verifier plan:",
        planned_checks,
        "Reason:",
        plan.reasoning,
    )

    for check_name in planned_checks:
        print(
            "Verifier running check:",
            check_name,
        )

        tool_name, arguments = check_configuration[
            check_name
        ]

        try:
            result = await tools_by_name[tool_name].ainvoke(
                arguments
            )
        except Exception as error:
            error_text = (
                f"Verification check {check_name} failed: "
                f"{type(error).__name__}: {error}"
            )
            tool_errors.append(error_text)
            result = {"error": error_text}

        tool_results.append(
            {
                "check": check_name,
                "result": result,
            }
        )

        if isinstance(result, dict):
            tool_evidence.extend(
                result.get("evidence", [])
            )

    # Step 3: Gemini evaluates the original and checked data.
    all_evidence = [
        *original_evidence,
        *tool_evidence,
    ]

    evidence_by_id = {
        item["evidence_id"]: item
        for item in all_evidence
    }

    verifier = gemini_model.with_structured_output(
        VerifierAnalysis
    )

    analysis = await verifier.ainvoke(
        [
            SystemMessage(
                content="""
                You are the Verifier for SignalGraph.

                Evaluate whether the findings are supported by
                the supplied evidence and completed checks.

                Rules:

                - A quote confirms price facts, not causation.
                - Sector weakness may support a contribution,
                  but does not prove an exact or sole cause.
                - Compare the target movement with the peer
                  median. Large underperformance means sector
                  weakness does not explain the full movement.
                - A later article may describe an earlier event.
                  Separate event time from publication time.
                - Analyst opinion is not causal proof.
                - Use supported only when every material part of
                  the explanation is supported.
                - Use partially_supported when facts or context
                  are supported but the full explanation is not.
                - Use insufficient_evidence when the checks cannot
                  establish the explanation.
                - Never claim an exact or sole market cause.
                - A finding with no evidence IDs does not support
                  a specific news event or explanation.
                - Do not repeat news details that do not appear in
                  the supplied evidence.
                - Return only supplied evidence IDs.
                """
            ),
            HumanMessage(
                content=(
                    f"Symbol: {state['symbol']}\n\n"
                    f"Question: {state['question']}\n\n"
                    f"Market timestamp: "
                    f"{state.get('market_context', {}).get('timestamp')}"
                    f"\n\nFindings:\n{findings_text}"
                    f"\n\nEvidence:\n{format_evidence(all_evidence)}"
                    f"\n\nVerification plan:\n"
                    f"{plan.model_dump_json(indent=2)}"
                    f"\n\nTool results:\n"
                    f"{json.dumps(tool_results, default=str, indent=2)}"
                )
            ),
        ]
    )

    reviewed_evidence_ids = []

    for evidence_id in analysis.reviewed_evidence_ids:
        if (
            evidence_id in evidence_by_id
            and evidence_id not in reviewed_evidence_ids
        ):
            reviewed_evidence_ids.append(evidence_id)

    verdict = analysis.verdict.replace(
        "_",
        " ",
    ).capitalize()

    result = {
        "findings": [
            {
                "agent_key": "verifier",
                "summary": (
                    f"Verification verdict: {verdict}.\n"
                    f"{analysis.summary}"
                ),
                "confidence": analysis.confidence,
                "evidence_ids": reviewed_evidence_ids,
            }
        ],
        "evidence": tool_evidence,
        "handoffs": [
            {
                "from_agent": "verifier",
                "to_agent": (
                    "skeptic"
                    if "skeptic" in state["selected_agents"]
                    else "synthesis"
                ),
                "summary": (
                    "Planned verification checks are complete."
                ),
            }
        ],
    }

    if tool_errors:
        result["errors"] = tool_errors

    return result
