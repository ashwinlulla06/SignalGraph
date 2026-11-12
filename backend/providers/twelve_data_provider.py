from datetime import datetime
from datetime import timezone

import httpx

from backend.models import MarketCandle

class TwelveDataProvider:
    BASE_URL = "https://api.twelvedata.com"

    def __init__(self, api_key: str):

        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=20.0,
            headers={
                "Authorization":
                    f"apikey {api_key}",
            },
        )

    async def get_recent_candles(self, symbol:str, output_size: int = 100) -> list[MarketCandle]:
        if output_size < 1:
            raise ValueError(
                "output_size must be atleast 1"
            )

        if output_size > 1000:
            raise ValueError(
                "output_size cannot exceed 1000"
            )

        response = await self._client.get(
            "/time_series",
            params={
                "symbol": symbol,
                "interval": "1min",
                "outputsize": output_size,
                "order": "asc",
                "format": "JSON",
                "dp": 8,
                "timezone": "UTC"
            }
        )

        response.raise_for_status()

        payload = response.json()

        if payload.get('status') == 'error':
            error_message = payload.get(
                "message",
                "Twelve Data returned an error"
            )

            raise RuntimeError(error_message)

        raw_values = payload.get('values')

        if not isinstance(raw_values, list):
            raise RuntimeError(
                "Twelve Data returned no candles"
            )

        candles = []

        for raw_candle in raw_values:
            start_time = datetime.strptime(
                raw_candle['datetime'],
                "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc)

            candle = MarketCandle(
                source="twelve_data",
                symbol=symbol,
                start_time=start_time,
                open=float(raw_candle["open"]),
                high=float(raw_candle["high"]),
                low=float(raw_candle["low"]),
                close=float(raw_candle["close"]),
                volume=float(
                    raw_candle["volume"]
                ),
            )

            candles.append(candle)

        candles.sort(key=lambda candle: candle.start_time)

        return candles

    async def close(self):
        await self._client.aclose()

