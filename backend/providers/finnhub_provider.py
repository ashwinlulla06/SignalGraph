import json
from collections.abc import AsyncIterator
from datetime import datetime
from datetime import timezone

import httpx
from websockets.asyncio.client import connect

from backend.models import MarketQuote
from backend.models import ProviderTrade


class FinnhubProvider:
    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self, api_token: str):
        self._api_token = api_token
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=20.0,
            headers={
                "X-Finnhub-Token": api_token
            }
        )

    async def get_quote(self, symbol: str) -> MarketQuote:
        response = await self._client.get(
            "/quote",
            params={
                "symbol": symbol
            }
        )

        response.raise_for_status()

        payload = response.json()

        if "error" in payload:
            raise RuntimeError(payload['error'])

        current_price = payload.get('c')
        provider_timestamp = payload.get('t')

        if (not current_price or not provider_timestamp):
            raise RuntimeError(
                f"Finnhub returned no quote for {symbol}"
            )

        timestamp = datetime.fromtimestamp(provider_timestamp, tz=timezone.utc)

        return MarketQuote(
            source = 'finnhub',
            symbol = symbol,
            price = float(current_price),
            previous_close = float(payload.get('pc')),
            absolute_change = float(payload.get('d')),
            change_percent = float(payload["dp"]),
            day_open = float(payload["o"]),
            day_high = float(payload["h"]),
            day_low = float(payload["l"]),
            timestamp = timestamp
        )

    async def stream_trades(self, symbols: list[str]) -> AsyncIterator[ProviderTrade]:
        websocket_url = (
            f"wss://ws.finnhub.io?token={self._api_token}"
        )

        async with connect(websocket_url) as websocket:
            for symbol in symbols:
                subscription = {
                    "type" : "subscribe",
                    "symbol" : symbol
                }

                await websocket.send(
                    json.dumps(subscription)
                )

                print(f"Finnhub subscription sent: {symbol}")

            async for raw_message in websocket:
                message = json.loads(raw_message)

                message_type = message.get("type")

                if message_type == "ping":
                    continue

                if message_type == "error":
                    raise RuntimeError(
                        message.get("message", "Finnhub websocket error")
                    )

                if message_type !="trade":
                    continue

                raw_trades = message.get("data", [])

                for raw_trade in raw_trades:
                    trade = ProviderTrade(
                        symbol=raw_trade['s'],
                        price=float(raw_trade['p']),
                        size=float(raw_trade['v']),
                        timestamp=(datetime.fromtimestamp(raw_trade['t'] / 1000, tz = timezone.utc))
                    )

                    yield trade

    async def get_company_news(self, symbol : str, from_date : str, to_date : str) -> list[dict]:
        response = await self._client.get(
            "/company-news", 
            params={
                "symbol" : symbol.upper(),
                "from" : from_date,
                "to" : to_date
            }
        )

        response.raise_for_status()

        payload = response.json()

        if isinstance(payload, dict):
            if "error" in payload:
                raise RuntimeError(
                    payload['error']
                )
            raise RuntimeError(
                "Finnhub returned an invalid company-news response"
            )

        if not isinstance(payload, list):
            raise RuntimeError("Finnhub returned no news list.")

        articles = []

        for raw_article in payload:
            headline = raw_article.get("headline", "")
            source_url = raw_article.get("url", "")
            published_timestamp = raw_article.get("datetime", "")

            if ( not headline or not source_url or not published_timestamp):
                continue

            published_at = datetime.fromtimestamp(published_timestamp, tz=timezone.utc)

            article = {
                "article_id" : str(raw_article.get("id", "")),
                "headline" : headline,
                "summary" : raw_article.get("summary", ""),
                "source_name" : raw_article.get("source", "Unknown source"),
                "source_url" : source_url,
                "published_at" : published_at,
                "related_symbol" : raw_article.get("related", symbol.upper())
            }

            articles.append(article)

        articles.sort(key = lambda article: article['published_at'], reverse=True)

        return articles

    async def close(self):
        await self._client.aclose()

        
