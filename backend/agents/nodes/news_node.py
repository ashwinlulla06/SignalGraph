from backend.agents.state import InvestigationState
from langchain_core.messages import HumanMessage, SystemMessage
from backend.agents.model import gemini_model
from langgraph.runtime import Runtime
from backend.agents.context import AgentRuntimeContext
from backend.agents.schemas import NewsAnalysis
from datetime import date
from backend.agents.tools.news_tool import fetch_company_news_for_date, fetch_recent_company_news


async def news_node(state: InvestigationState, runtime:Runtime[AgentRuntimeContext]) -> dict:
    symbol = state['symbol']
    scope = state['investigation_scope']

    try:
        if scope == "trading_day":
            target_date = date.fromisoformat(state['investigation_date'])

            articles = await fetch_company_news_for_date(
                provider=runtime.context.finnhub_provider,
                symbol=symbol,
                target_date=target_date,
                days_before=1,
                days_after=2,
                limit=20
            )

            news_period = f"The requested trading date {target_date}"

        else:
            articles = await fetch_recent_company_news(
                provider=runtime.context.finnhub_provider,
                symbol=symbol,
                lookback_days=5,
                limit=10
            )

            news_period = "The latest live movement"

    except Exception as error:
        summary = f"Company news could not be retrieved for {symbol}"

        return {
            "findings" : [
                {
                    "agent_key" : "news",
                    "summary" : summary,
                    "confidence" : 0.0,
                    "evidence_ids" : []
                }
            ],

            "handoffs" : [
                {
                    "from_agent" : "news",
                    "to_agent" : "review_gate",
                    "summary" : summary
                }
            ],

            "errors" : [
                f"News retrieval failed {type(error).__name__} : {error}"
            ]
        }

    if not articles:
        summary = f"No recent company-news articles were found for {symbol}"

        return {
            "findings" : [
                {
                    "agent_key" : "news",
                    "summary": summary,
                    "confidence": 0.0,
                    "evidence_ids": [],
                }
            ],

            "handoffs": [
                {
                    "from_agent": "news",
                    "to_agent": "review_gate",
                    "summary": summary,
                }
            ]
        }

    article_blocks = []

    for article in articles:
        article_blocks.append(
            (
                f"Article ID: "
                f"{article['article_id']}\n"
                f"Published: "
                f"{article['published_at']}\n"
                f"Source: "
                f"{article['source_name']}\n"
                f"Headline: "
                f"{article['headline']}\n"
                f"Summary: "
                f"{article['summary'][:700]}"
            )
        )

    articles_text = "\n\n".join(article_blocks)

    market_timestamp = state['market_context'].get("timestamp")

    structured_news_model = gemini_model.with_structured_output(NewsAnalysis)

    system_prompt = """
    You are the News specialist for SignalGraph.

    Examine only the supplied articles.

    The investigation may concern either a live
    one-minute movement or a completed historical
    trading day. Use the supplied investigation scope.

    For a historical investigation, compare article
    publication times with the requested date. An
    article published after the movement may provide
    a retrospective explanation, but it does not prove
    that traders knew the information earlier.

    Determine whether any article provides a
    plausible catalyst or useful context for
    the user's question.

    Distinguish between:
    - direct company-specific news,
    - sector or industry context,
    - broad market context,
    - irrelevant news.

    Do not claim that an article caused a price
    movement unless the supplied evidence clearly
    supports that claim.

    If no relevant catalyst is present, say so
    clearly.

    Return only article IDs that were supplied.
    Select at most five supporting articles.

    If you mention information from an article,
    return that article's ID. If you return no
    article IDs, do not mention any specific news
    event or explanation in the summary.
    """

    user_prompt = f"""
    Symbol: {symbol}

    Investigation scope: {scope}

    Investigation date: {state.get("investigation_date")}

    Question: 
    {state['question']}

    Latest market timestamp: {market_timestamp}

    Candidate articles:
    {articles_text}
    """

    analysis = await structured_news_model.ainvoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
    )

    articles_by_id = {
        article['article_id'] : article
        for article in articles
    }

    selected_article_ids = []

    for article_id in analysis.relevant_article_ids:
        if (article_id in articles_by_id and article_id not in selected_article_ids):
            selected_article_ids.append(article_id)

    if selected_article_ids:
        safe_summary = analysis.summary
        safe_confidence = analysis.confidence
    else:
        safe_summary = (
            f"No supplied company-news article was selected as "
            f"relevant evidence for {symbol}. No news catalyst "
            f"can be confirmed from the retrieved articles."
        )
        safe_confidence = 0.0

    evidence = []

    for article_id in selected_article_ids:
        article = articles_by_id[article_id]

        evidence.append(
            {
                "evidence_id": (
                    f"news-{article_id}"
                ),

                "agent_key": "news",

                "title": article[
                    "headline"
                ],

                "source_name": article[
                    "source_name"
                ],

                "source_url": article[
                    "source_url"
                ],

                "summary": article[
                    "summary"
                ],

                "published_at": (
                    article["published_at"]
                    .isoformat()
                ),
            }
        )

    evidence_ids = [
        item['evidence_id'] for item in evidence
    ]

    finding = {
        "agent_key": "news",
        "summary": safe_summary,
        "confidence": safe_confidence,
        "evidence_ids": evidence_ids,
    }

    return {
        "findings": [
            finding
        ],

        "evidence": evidence,

        "handoffs": [
            {
                "from_agent": "news",
                "to_agent": "review_gate",
                "summary": (
                    "Recent news analysis is ready."
                ),
            }
        ]
    }
