import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.config import FINNHUB_API_TOKEN
from backend.config import TWELVE_DATA_API_KEY
from backend.connection_manager import (
    ConnectionManager,
)

from backend.models import MarketCandle
from backend.models import MarketQuote
from backend.models import SymbolInfo
from backend.providers.finnhub_provider import (
    FinnhubProvider,
)
from backend.providers.twelve_data_provider import (
    TwelveDataProvider,
)
from backend.symbol_data import SYMBOLS

connection_manager = ConnectionManager()

known_symbols = {
    symbol_info.symbol
    for symbol_info in SYMBOLS
}


def validate_symbol(symbol: str) -> str:
    normalized_symbol = symbol.upper()

    if normalized_symbol not in known_symbols:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Unknown symbol: "
                f"{normalized_symbol}"
            ),
        )

    return normalized_symbol


async def run_market_feed(app: FastAPI):
    while True:
        try: 
            subscribed_symbols = list(
                app.state.market_quotes.keys()
            )

            async for trade in app.state.finnhub_provider.stream_trades(symbols=subscribed_symbols):
                print(
                    f"Real Finnhub trade: "
                    f"{trade.symbol} "
                    f"price={trade.price} "
                    f"size={trade.size} "
                    f"time={trade.timestamp}"
                )

                await connection_manager.broadcast(trade)

        except asyncio.CancelledError:
            raise
        
        except Exception as error:
            print(
                "Finnhub stream disconnted: ", type(error).__name__
            )

            print("Trying again in 5 seconds...")

            await asyncio.sleep(5)


async def load_initial_quotes(
    finnhub_provider: FinnhubProvider,
) -> dict[str, MarketQuote]:
    quote_requests = [
        finnhub_provider.get_quote(
            symbol=symbol_info.symbol
        )
        for symbol_info in SYMBOLS
    ]

    results = await asyncio.gather(
        *quote_requests,
        return_exceptions=True,
    )

    quotes_by_symbol = {}

    for symbol_info, result in zip(
        SYMBOLS,
        results,
    ):
        if isinstance(result, Exception):
            print(
                f"Could not load quote for "
                f"{symbol_info.symbol}: "
                f"{type(result).__name__}"
            )
            continue

        quotes_by_symbol[symbol_info.symbol] = (
            result
        )

    return quotes_by_symbol

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting SignalGraph")

    app.state.finnhub_provider = (
        FinnhubProvider(
            api_token=FINNHUB_API_TOKEN
        )
    )

    app.state.twelve_data_provider = (
        TwelveDataProvider(
            api_key=TWELVE_DATA_API_KEY
        )
    )

    app.state.market_quotes = (
        await load_initial_quotes(
            finnhub_provider=app.state.finnhub_provider
        )
    )

    print("Initial Finnhub quotes loaded: ", len(app.state.market_quotes))

    market_feed_task = asyncio.create_task(
        run_market_feed(app)
    )

    try:
        yield

    finally:
        print("Stopping SignalGraph")

        market_feed_task.cancel()

        try:
            await market_feed_task
        except asyncio.CancelledError:
            pass

        await (
            app.state.finnhub_provider.close()
        )

        await (
            app.state
            .twelve_data_provider
            .close()
        )


app = FastAPI(
    title="SignalGraph API",
    version="0.1.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "signalgraph-api",
    }


@app.get(
    "/api/symbols",
    response_model=list[SymbolInfo],
)
async def get_symbols():
    return SYMBOLS


@app.get(
    "/api/markets/snapshot",
    response_model=list[MarketQuote],
)
async def get_market_snapshot(request: Request):
    return list(request.app.state.market_quotes.values())


@app.get(
    "/api/markets/{symbol}/quote",
    response_model=MarketQuote,
)
async def get_market_quote(symbol: str, request: Request):
    normalized_symbol = validate_symbol(symbol)

    quote = await (
        request.app.state
        .finnhub_provider
        .get_quote(
            symbol=normalized_symbol
        )
    )

    return quote


@app.get(
    "/api/markets/{symbol}/history",
    response_model=list[MarketCandle],
)
async def get_market_history(
    symbol: str,
    request: Request,
    output_size: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
):
    normalized_symbol = validate_symbol(
        symbol
    )

    candles = await (
        request.app.state
        .twelve_data_provider
        .get_recent_candles(
            symbol=normalized_symbol,
            output_size=output_size,
        )
    )

    return candles


@app.websocket("/ws/market")
async def market_websocket(
    websocket: WebSocket,
):
    await connection_manager.connect(
        websocket
    )

    try:
        while True:
            message = (
                await websocket.receive_text()
            )

            if message == "ping":
                await websocket.send_json(
                    {
                        "type": "pong"
                    }
                )

    except WebSocketDisconnect:
        connection_manager.disconnect(
            websocket
        )