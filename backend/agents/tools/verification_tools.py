import asyncio
from datetime import datetime, timedelta, timezone
from statistics import median

import httpx
from langchain_core.tools import tool

from backend.providers.finnhub_provider import FinnhubProvider


AI_SECTOR_SYMBOLS = [
    "NVDA",
    "AMD",
    "AVGO",
    "MSFT",
    "GOOGL",
    "META",
    "AMZN",
]


def create_verification_tools(
    finnhub_provider: FinnhubProvider,
) -> list:
    """Create verification tools that reuse the shared Finnhub provider."""

    @tool
    async def verify_current_market_quote(
        symbol: str,
    ) -> dict:
        """Fetch a fresh Finnhub quote to check a market-price claim."""
        normalized_symbol = symbol.upper()
        quote = await finnhub_provider.get_quote(
            normalized_symbol
        )

        summary = (
            f"{normalized_symbol} was {quote.price:.2f} "
            f"at {quote.timestamp.isoformat()}, with a "
            f"change of {quote.change_percent:.2f}% from "
            f"the previous close of {quote.previous_close:.2f}."
        )

        return {
            "check_type": "fresh_market_quote",
            "summary": summary,
            "evidence": [
                {
                    "evidence_id": (
                        "verification-quote-"
                        f"{normalized_symbol.lower()}"
                    ),
                    "agent_key": "verifier",
                    "title": (
                        f"Fresh {normalized_symbol} market quote"
                    ),
                    "source_name": "Finnhub",
                    "source_url": "https://finnhub.io/",
                    "summary": summary,
                    "published_at": quote.timestamp.isoformat(),
                }
            ],
        }

    @tool
    async def verify_recent_company_news(
        symbol: str,
        lookback_days: int = 5,
        limit: int = 5,
    ) -> dict:
        """Recheck recent company news and return source metadata."""
        if not 1 <= lookback_days <= 30:
            raise ValueError(
                "lookback_days must be between 1 and 30"
            )

        if not 1 <= limit <= 10:
            raise ValueError(
                "limit must be between 1 and 10"
            )

        normalized_symbol = symbol.upper()
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(
            days=lookback_days
        )

        articles = await finnhub_provider.get_company_news(
            symbol=normalized_symbol,
            from_date=start_date.isoformat(),
            to_date=end_date.isoformat(),
        )

        selected_articles = articles[:limit]
        evidence = []

        for article in selected_articles:
            evidence.append(
                {
                    "evidence_id": (
                        "verification-news-"
                        f"{article['article_id']}"
                    ),
                    "agent_key": "verifier",
                    "title": article["headline"],
                    "source_name": article["source_name"],
                    "source_url": article["source_url"],
                    "summary": article["summary"],
                    "published_at": (
                        article["published_at"].isoformat()
                    ),
                }
            )

        return {
            "check_type": "recent_company_news",
            "symbol": normalized_symbol,
            "articles_found": len(selected_articles),
            "evidence": evidence,
        }

    @tool
    async def verify_ai_sector_movement(
        target_symbol: str,
    ) -> dict:
        """Compare one stock with an AI-linked US equity basket."""
        normalized_target = target_symbol.upper()
        comparison_symbols = list(
            dict.fromkeys(
                [normalized_target, *AI_SECTOR_SYMBOLS]
            )
        )

        quote_results = await asyncio.gather(
            *[
                finnhub_provider.get_quote(symbol)
                for symbol in comparison_symbols
            ],
            return_exceptions=True,
        )

        movements = []
        failures = []

        for symbol, result in zip(
            comparison_symbols,
            quote_results,
        ):
            if isinstance(result, Exception):
                failures.append(symbol)
                continue

            movements.append(
                {
                    "symbol": symbol,
                    "price": result.price,
                    "change_percent": result.change_percent,
                    "timestamp": result.timestamp.isoformat(),
                }
            )

        if not movements:
            raise RuntimeError(
                "No AI-sector basket quotes were available"
            )

        changes = [
            item["change_percent"]
            for item in movements
        ]

        target_movement = next(
            (
                item
                for item in movements
                if item["symbol"] == normalized_target
            ),
            None,
        )

        peer_changes = [
            item["change_percent"]
            for item in movements
            if item["symbol"] != normalized_target
        ]

        if target_movement is None:
            raise RuntimeError(
                f"No quote was available for {normalized_target}"
            )

        if not peer_changes:
            raise RuntimeError(
                "No peer quotes were available for comparison"
            )

        peer_median_change = median(peer_changes)
        relative_difference = (
            target_movement["change_percent"]
            - peer_median_change
        )

        declining_count = sum(
            change < 0
            for change in changes
        )

        summary = (
            "AI-linked equity basket proxy: "
            f"{declining_count} of {len(movements)} symbols "
            f"were declining. {normalized_target} changed "
            f"{target_movement['change_percent']:.2f}%, while "
            f"the peer median was {peer_median_change:.2f}%. "
            f"The relative difference was "
            f"{relative_difference:.2f} percentage points. "
            "This is a comparison "
            "basket, not an official AI-sector index."
        )

        latest_timestamp = max(
            item["timestamp"]
            for item in movements
        )

        return {
            "check_type": "ai_sector_movement",
            "summary": summary,
            "target_symbol": normalized_target,
            "target_change_percent": (
                target_movement["change_percent"]
            ),
            "peer_median_change_percent": peer_median_change,
            "relative_difference_percentage_points": (
                relative_difference
            ),
            "constituents": movements,
            "failed_symbols": failures,
            "evidence": [
                {
                    "evidence_id": "verification-ai-sector-basket",
                    "agent_key": "verifier",
                    "title": "AI-linked equity basket movement",
                    "source_name": "Finnhub",
                    "source_url": "https://finnhub.io/",
                    "summary": summary,
                    "published_at": latest_timestamp,
                }
            ],
        }

    @tool
    async def search_government_policy_documents(
        query: str,
        lookback_days: int = 30,
        limit: int = 5,
    ) -> dict:
        """Search official US Federal Register documents for policy evidence."""
        if not 1 <= lookback_days <= 365:
            raise ValueError(
                "lookback_days must be between 1 and 365"
            )

        if not 1 <= limit <= 10:
            raise ValueError(
                "limit must be between 1 and 10"
            )

        start_date = (
            datetime.now(timezone.utc).date()
            - timedelta(days=lookback_days)
        )

        async with httpx.AsyncClient(
            timeout=20.0
        ) as client:
            response = await client.get(
                "https://www.federalregister.gov/api/v1/documents.json",
                params={
                    "per_page": limit,
                    "order": "newest",
                    "conditions[term]": query,
                    "conditions[publication_date][gte]": (
                        start_date.isoformat()
                    ),
                },
            )

            response.raise_for_status()
            payload = response.json()

        documents = payload.get("results", [])
        evidence = []

        for document in documents[:limit]:
            document_number = str(
                document.get("document_number", "unknown")
            )

            agencies = [
                agency.get("name", "")
                for agency in document.get("agencies", [])
                if agency.get("name")
            ]

            agency_text = (
                ", ".join(agencies)
                if agencies
                else "Unknown agency"
            )

            abstract = document.get("abstract") or (
                "No abstract was supplied."
            )

            summary = (
                f"Issued by {agency_text}. {abstract}"
            )

            evidence.append(
                {
                    "evidence_id": (
                        "verification-policy-"
                        f"{document_number.lower()}"
                    ),
                    "agent_key": "verifier",
                    "title": document.get(
                        "title",
                        "Federal Register document",
                    ),
                    "source_name": "Federal Register",
                    "source_url": document.get("html_url"),
                    "summary": summary,
                    "published_at": document.get(
                        "publication_date"
                    ),
                }
            )

        return {
            "check_type": "government_policy_documents",
            "query": query,
            "documents_found": len(evidence),
            "evidence": evidence,
        }

    return [
        verify_current_market_quote,
        verify_recent_company_news,
        verify_ai_sector_movement,
        search_government_policy_documents,
    ]
