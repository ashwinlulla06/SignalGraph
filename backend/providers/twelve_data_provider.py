import asyncio
from datetime import date
from datetime import datetime
from datetime import timezone
from time import monotonic

import httpx

from backend.models import MarketCandle


class TwelveDataProvider:
    BASE_URL = "https://api.twelvedata.com"

    MINUTE_CACHE_SECONDS = 300
    DAILY_CACHE_SECONDS = 21600

    def __init__(self, api_key: str):
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=20.0,
            headers={
                "Authorization": (
                    f"apikey {api_key}"
                ),
            },
        )

        self._history_cache: dict[
            tuple,
            tuple[float, list[MarketCandle]],
        ] = {}

        self._cache_locks: dict[
            tuple,
            asyncio.Lock,
        ] = {}

    async def get_recent_candles(
        self,
        symbol: str,
        output_size: int = 100,
    ) -> list[MarketCandle]:
        """Return recent one-minute candles."""

        return await self._get_candles(
            symbol=symbol,
            interval="1min",
            output_size=output_size,
            cache_duration=(
                self.MINUTE_CACHE_SECONDS
            ),
        )

    async def get_daily_candles(
        self,
        symbol: str,
        output_size: int = 2500,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[MarketCandle]:
        """Return completed daily candles."""

        return await self._get_candles(
            symbol=symbol,
            interval="1day",
            output_size=output_size,
            cache_duration=(
                self.DAILY_CACHE_SECONDS
            ),
            start_date=start_date,
            end_date=end_date,
        )

    async def _get_candles(
        self,
        symbol: str,
        interval: str,
        output_size: int,
        cache_duration: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[MarketCandle]:
        if output_size < 1:
            raise ValueError(
                "output_size must be at least 1"
            )

        if output_size > 5000:
            raise ValueError(
                "output_size cannot exceed 5000"
            )

        normalized_symbol = symbol.upper()

        cache_key = (
            normalized_symbol,
            interval,
            output_size,
            (
                start_date.isoformat()
                if start_date
                else None
            ),
            (
                end_date.isoformat()
                if end_date
                else None
            ),
        )

        if cache_key not in self._cache_locks:
            self._cache_locks[
                cache_key
            ] = asyncio.Lock()

        async with self._cache_locks[
            cache_key
        ]:
            cache_entry = (
                self._history_cache.get(
                    cache_key
                )
            )

            if cache_entry is not None:
                fetched_at, cached_candles = (
                    cache_entry
                )

                cache_age = (
                    monotonic() - fetched_at
                )

                if cache_age < cache_duration:
                    print(
                        "Twelve Data cache hit:",
                        normalized_symbol,
                        interval,
                    )

                    return list(
                        cached_candles
                    )

            print(
                "Twelve Data cache miss:",
                normalized_symbol,
                interval,
            )

            candles = await self._fetch_candles(
                symbol=normalized_symbol,
                interval=interval,
                output_size=output_size,
                start_date=start_date,
                end_date=end_date,
            )

            self._history_cache[cache_key] = (
                monotonic(),
                candles,
            )

            return list(candles)

    async def _fetch_candles(
        self,
        symbol: str,
        interval: str,
        output_size: int,
        start_date: date | None,
        end_date: date | None,
    ) -> list[MarketCandle]:
        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": output_size,
            "order": "asc",
            "format": "JSON",
            "dp": 8,
            "timezone": "UTC",
        }

        if start_date is not None:
            params["start_date"] = (
                start_date.isoformat()
            )

        if end_date is not None:
            params["end_date"] = (
                end_date.isoformat()
            )

        response = await self._client.get(
            "/time_series",
            params=params,
        )

        response.raise_for_status()

        payload = response.json()

        if payload.get("status") == "error":
            raise RuntimeError(
                payload.get(
                    "message",
                    "Twelve Data returned an error",
                )
            )

        raw_values = payload.get("values")

        if not isinstance(raw_values, list):
            raise RuntimeError(
                "Twelve Data returned no candles"
            )

        candles = []

        for raw_candle in raw_values:
            start_time = datetime.fromisoformat(
                raw_candle["datetime"]
            )

            if start_time.tzinfo is None:
                start_time = start_time.replace(
                    tzinfo=timezone.utc
                )

            candles.append(
                MarketCandle(
                    source="twelve_data",
                    symbol=symbol,
                    start_time=start_time,
                    open=float(
                        raw_candle["open"]
                    ),
                    high=float(
                        raw_candle["high"]
                    ),
                    low=float(
                        raw_candle["low"]
                    ),
                    close=float(
                        raw_candle["close"]
                    ),
                    volume=float(
                        raw_candle["volume"]
                    ),
                )
            )

        candles.sort(
            key=lambda candle:
                candle.start_time
        )

        return candles

    async def close(self):
        await self._client.aclose()