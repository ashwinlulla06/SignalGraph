import { useEffect, useRef, useState } from "react";
import { normalizeMarketCandle } from "../utils/marketCandles";

const SNAPSHOT_URL =
  "http://127.0.0.1:8000/api/markets/snapshot";

const WEBSOCKET_URL =
  "ws://127.0.0.1:8000/ws/market";

const RECONNECT_DELAY = 2000;
const MAX_LIVE_CANDLES_PER_SYMBOL = 120;
const MAX_ANALYSIS_RESULTS_PER_SYMBOL = 120

function indexQuotesBySymbol(quotes){
  const indexedQuotes = {};

  for(const quote of quotes) {
    indexedQuotes[quote.symbol] = quote;
  }

  return indexedQuotes;
}

function applyTradeToQuotes(currentQuotes, trade){
  const currentQuote = currentQuotes[trade.symbol];

  if(!currentQuote) return currentQuotes;

  const tradeTime = new Date(trade.timestamp).getTime();

  const quoteTime = new Date(currentQuote.timestamp).getTime()

  if (tradeTime < quoteTime) return currentQuotes;

  const absoluteChange = trade.price - currentQuote.previous_close

  const changePercent = ( absoluteChange / currentQuote.previous_close ) * 100;

  const updatedQuote = {
    ...currentQuote,
    price: trade.price,
    absolute_change: absoluteChange,
    change_percent: changePercent,
    timestamp: trade.timestamp
  };

  return {
    ...currentQuotes,
    [trade.symbol]: updatedQuote
  }
}

function mergeLiveCandle(currentCandlesBySymbol, rawCandle){
  const candle = normalizeMarketCandle(rawCandle);

  const symbolCandles = currentCandlesBySymbol[candle.symbol] ?? []

  const existingIndex = symbolCandles.findIndex((existingCandle) => existingCandle.startTime === candle.startTime)

  let nextSymbolCandles;

  if(existingIndex >= 0){
    nextSymbolCandles = [...symbolCandles];

    nextSymbolCandles[existingIndex] = candle;

  } else {
    nextSymbolCandles = [...symbolCandles, candle]
  }

  nextSymbolCandles.sort((first, second) => first.startTime - second.startTime);

  return {
    ...currentCandlesBySymbol,
    [candle.symbol]: nextSymbolCandles.slice(-MAX_LIVE_CANDLES_PER_SYMBOL)

  }
}

function mergeAnalysisResult(currentResultsBySymbol, rawResult){
  const startTime = new Date(rawResult.start_time).getTime();

  if (!Number.isFinite(startTime)){
    return currentResultsBySymbol
  }

  const result = {
    ...rawResult,
    startTime
  }

  const symbolResults = currentResultsBySymbol[result.symbol] ?? []

  const existingIndex = symbolResults.findIndex((existingResult) => existingResult.startTime === result.startTime);

  let nextSymbolResults;

  if (existingIndex >= 0){
    nextSymbolResults = [...symbolResults];

    nextSymbolResults[existingIndex] = result;
  } else {
    nextSymbolResults = [...symbolResults, result]
  }

  nextSymbolResults.sort((first, second) => first.startTime - second.startTime);

  return {
    ...currentResultsBySymbol,
    [result.symbol] : nextSymbolResults.slice(-MAX_ANALYSIS_RESULTS_PER_SYMBOL)
  }
}

export default function useMarketData() {
  const [quotesBySymbol, setQuotesBySymbol] = useState({});
  const [connectionState, setConnectionState] = useState("connecting")
  const [error, setError] = useState("");
  const [liveCandlesBySymbol, setLiveCandlesBySymbol] = useState({});
  const [analysisResultsBySymbol, setAnalysisResultsBySymbol] = useState({});
  const [automaticInvestigation, setAutomaticInvestigation] = useState(null);

  const socketRef = useRef(null);
  const reconnectTimerRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    async function loadSnapshot() {
      try {
        const response = await fetch(SNAPSHOT_URL);

        if (!response.ok) {
          throw new Error(
            `Snapshot request failed: ${response.status}`
          );
        }

        const snapshot = await response.json();

        if (!Array.isArray(snapshot)){
          throw new Error("Snapshot response was not a list.")
        }

        if (cancelled) {
          return;
        }

        setQuotesBySymbol(indexQuotesBySymbol(snapshot))
        
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError.message);
        }
      }
    }

    function connectWebSocket() {
      if (cancelled) {
        return;
      }

      setConnectionState("connecting");

      const socket = new WebSocket(WEBSOCKET_URL);
      socketRef.current = socket;

      socket.onopen = function () {
        if (cancelled) {
          return;
        }

        setConnectionState("connected");
        setError("");

      };

      socket.onmessage = function (event) {
        if (cancelled) {
          return;
        }

        try {
          const message = JSON.parse(event.data);

          if (message.type === "pong"){
            return;
          }

          if (message.type === "market_trade") {
            setQuotesBySymbol((currentQuotes) => applyTradeToQuotes(currentQuotes, message));
            return;
          }

          if(message.type === "market_candle"){
            setLiveCandlesBySymbol((currentCandles) => mergeLiveCandle(currentCandles, message));
            return;
          }

          if(message.type === "market_anomaly_result"){
            setAnalysisResultsBySymbol((currentResults) => mergeAnalysisResult(currentResults, message));
            return;
          }

          if(message.type === "automatic_investigation_started"){
            setAutomaticInvestigation({
              status: "running",
              investigationId: message.investigation_id,
              symbol: message.symbol,
              result: null,
              error: ""
            });
            return;
          }

          if(message.type === "automatic_investigation_completed"){
            setAutomaticInvestigation({
              status: "complete",
              investigationId: message.investigation_id,
              symbol: message.symbol,
              result: message.result,
              error: ""
            });
            return;
          }

          if(message.type === "automatic_investigation_failed"){
            setAutomaticInvestigation({
              status: "failed",
              investigationId: message.investigation_id,
              symbol: message.symbol,
              result: null,
              error: message.error || "The automatic investigation failed"
            });
            return;
          }

        } catch {
          setError("The server sent an invalid message");
        }
      };

      socket.onerror = function () {
        if (cancelled) {
          return;
        }

        setError(
          "The market connection encountered an error"
        );

        socket.close();
      };

      socket.onclose = function () {
        if (cancelled) {
          return;
        }

        setConnectionState("reconnecting");

        reconnectTimerRef.current =
          window.setTimeout(
            connectWebSocket,
            RECONNECT_DELAY
          );
      };
    }

    loadSnapshot();
    connectWebSocket();

    return function cleanup() {
      cancelled = true;

      window.clearTimeout(
        reconnectTimerRef.current
      );

      const socket = socketRef.current;

      if (
        socket &&
        socket.readyState < WebSocket.CLOSING
      ) {
        socket.close();
      }

      socketRef.current = null;
      reconnectTimerRef.current = null;
    };
  }, []);

  return {
    quotesBySymbol,
    connectionState,
    error,
    liveCandlesBySymbol,
    analysisResultsBySymbol,
    automaticInvestigation
  };
}
