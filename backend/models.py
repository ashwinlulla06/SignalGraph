from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

class SymbolInfo(BaseModel):
    company_id: str
    company_name: str
    symbol: str
    listing_venue: str
    market: Literal["US", "CN", "HK"]
    currency: Literal["USD", "CNY", "HKD"]


class MarketTick(BaseModel):
    type: Literal["market_tick"] = "market_tick"

    company_id: str
    symbol: str
    market: Literal["US", "CN", "HK"]
    currency: Literal["USD", "CNY", "HKD"]

    price: float = Field(gt=0)
    previous_close: float = Field(gt=0)
    absolute_change: float
    change_percent: float
    volume: int = Field(ge=0)

    timestamp: datetime
    sequence: int = Field(ge=0)


class ProviderTrade(BaseModel):
    type: Literal['market_trade'] = "market_trade"
    source: Literal['finnhub'] = 'finnhub'
    symbol: str
    price : float = Field(gt=0)
    size: float = Field(gt=0)

    timestamp : datetime

class MarketCandle(BaseModel):
    source: Literal['twelve_data', 'finnhub']

    symbol: str
    start_time: datetime

    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)

    volume: float = Field(gt=0)


class MarketQuote(BaseModel):
    source: Literal['finnhub'] = 'finnhub'

    symbol: str

    price: float = Field(gt=0)
    previous_close: float = Field(gt=0)

    absolute_change : float
    change_percent : float

    day_open : float = Field(gt=0)
    day_high : float = Field(gt=0)
    day_low : float = Field(gt=0)

    timestamp : datetime

