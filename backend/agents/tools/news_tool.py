from datetime import date
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from backend.providers.finnhub_provider import (
    FinnhubProvider,
)


async def fetch_recent_company_news(
    provider: FinnhubProvider,
    symbol: str,
    lookback_days: int = 5,
    limit: int = 10,
) -> list[dict]:
    if lookback_days < 1:
        raise ValueError(
            "lookback_days must be at least 1"
        )

    if limit < 1:
        raise ValueError(
            "limit must be at least 1"
        )

    ending_date = (
        datetime.now(
            timezone.utc
        ).date()
    )

    starting_date = (
        ending_date
        - timedelta(days=lookback_days)
    )

    articles = await (
        provider.get_company_news(
            symbol=symbol,
            from_date=(
                starting_date.isoformat()
            ),
            to_date=(
                ending_date.isoformat()
            ),
        )
    )

    return articles[:limit]


async def fetch_company_news_for_date(
    provider: FinnhubProvider,
    symbol: str,
    target_date: date,
    days_before: int = 1,
    days_after: int = 2,
    limit: int = 10,
) -> list[dict]:
    if days_before < 0:
        raise ValueError(
            "days_before cannot be negative"
        )

    if days_after < 0:
        raise ValueError(
            "days_after cannot be negative"
        )

    if limit < 1:
        raise ValueError(
            "limit must be at least 1"
        )

    starting_date = (
        target_date
        - timedelta(days=days_before)
    )

    ending_date = (
        target_date
        + timedelta(days=days_after)
    )

    articles = await (
        provider.get_company_news(
            symbol=symbol,
            from_date=(
                starting_date.isoformat()
            ),
            to_date=(
                ending_date.isoformat()
            ),
        )
    )

    def historical_article_priority(
        article: dict,
    ) -> tuple:
        article_date = (
            article["published_at"].date()
        )

        distance_from_target = abs(
            (
                article_date
                - target_date
            ).days
        )

        published_after_target = (
            article_date > target_date
        )

        return (
            distance_from_target,
            published_after_target,
            article["published_at"],
        )

    ranked_articles = sorted(
        articles,
        key=historical_article_priority,
    )

    return ranked_articles[:limit]
