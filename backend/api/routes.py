from uuid import uuid4
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from backend.agents.graph import investigation_graph
from backend.agents.schemas import InvestigationRequest
from backend.models import MarketCandle
from backend.models import MarketQuote
from backend.models import SymbolInfo
from backend.services.market_runtime import connection_manager
from backend.symbol_data import SYMBOLS
from backend.services.daily_investigation_context import build_daily_investigation_context


router = APIRouter()

known_symbols = {
    symbol_info.symbol
    for symbol_info in SYMBOLS
}


def validate_symbol(symbol: str) -> str:
    """Normalize a symbol and reject unsupported companies."""
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


@router.get("/api/health")
async def health_check():
    """Confirm that FastAPI is running."""
    return {
        "status": "ok",
        "service": "signalgraph-api",
    }


@router.get(
    "/api/symbols",
    response_model=list[SymbolInfo],
)
async def get_symbols():
    """Return the companies configured in SignalGraph."""
    return SYMBOLS


@router.get(
    "/api/markets/snapshot",
    response_model=list[MarketQuote],
)
async def get_market_snapshot(
    request: Request,
):
    """Return the latest in-memory quote for every company."""
    return list(
        request.app.state
        .market_quotes.values()
    )


@router.get(
    "/api/markets/{symbol}/quote",
    response_model=MarketQuote,
)
async def get_market_quote(
    symbol: str,
    request: Request,
):
    """Request a fresh quote for one company from Finnhub."""
    normalized_symbol = validate_symbol(symbol)

    quote = await (
        request.app.state
        .finnhub_provider
        .get_quote(
            symbol=normalized_symbol
        )
    )

    return quote


@router.get(
    "/api/markets/{symbol}/history",
    response_model=list[MarketCandle],
)
async def get_market_history(
    symbol: str,
    request: Request,
    output_size: int = Query(
        default=100,
        ge=1,
        le=5000,
    ),
):
    """Return recent one-minute candles from Twelve Data."""
    normalized_symbol = validate_symbol(symbol)

    candles = await (
        request.app.state
        .twelve_data_provider
        .get_recent_candles(
            symbol=normalized_symbol,
            output_size=output_size,
        )
    )

    return candles


@router.websocket("/ws/market")
async def market_websocket(
    websocket: WebSocket,
):
    """Keep the browser connected for live market messages."""
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
                    {"type": "pong"}
                )

    except WebSocketDisconnect:
        connection_manager.disconnect(
            websocket
        )


@router.post("/api/investigations")
async def create_investigation(
    investigation_request: InvestigationRequest,
    request: Request,
):
    """Run either a live one-minute investigation or a completed-day investigation"""

    symbol = validate_symbol(
        investigation_request.symbol
    )

    investigation_date = (
        investigation_request
        .investigation_date
    )

    if investigation_date is None:
        investigation_scope = "live"

        quote = request.app.state.market_quotes.get(symbol)

        if quote is None:
            raise HTTPException(status_code=503, detail=f"Live market data is unavailable for {symbol}")

        minute_anomaly_result = request.app.state.latest_anomaly_results.get(symbol)

        market_context = quote.model_dump(mode="json")

        anomaly_context = minute_anomaly_result.model_dump(mode="json") if minute_anomaly_result is not None else None

        investigation_date_value = None

    else:
        investigation_scope = "trading_day"

        current_new_york_date = (
            datetime.now(
                ZoneInfo("America/New_York")
            ).date()
        )
    
        if (
            investigation_date
            >= current_new_york_date
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Daily investigations currently "
                    "support only completed past "
                    "trading days."
                ),
            )
    
        try:
            (
                market_context,
                anomaly_context,
            ) = await (
                build_daily_investigation_context(
                    app=request.app,
                    symbol=symbol,
                    investigation_date=(
                        investigation_date
                    ),
                )
            )
    
        except ValueError as error:
            raise HTTPException(
                status_code=422,
                detail=str(error),
            ) from error

        investigation_date_value = investigation_date.isoformat()
        
    initial_state = {
            "investigation_id": str(uuid4()),
            "trigger": "user_question",
            "question": (
                investigation_request.question
            ),
            "symbol": symbol,
            "investigation_date": (
                investigation_date_value
            ),
            "investigation_scope": (
                investigation_scope
            ),
            "status": "created",
            "selected_agents": [],
            "market_context": (
                market_context
            ),
            "anomaly_context": (
                anomaly_context
            ),
            "findings": [],
            "evidence": [],
            "handoffs": [],
            "errors": [],
            "final_report": "",
        }
    
    result = await (
            investigation_graph.ainvoke(
                initial_state,
                context={
                    "finnhub_provider": (
                        request.app.state
                        .finnhub_provider
                    )
                },
            )
        )
    
    return result
    
