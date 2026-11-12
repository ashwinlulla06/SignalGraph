import { useEffect, useRef, useState } from "react";

const SNAPSHOT_URL =
  "http://127.0.0.1:8000/api/markets/snapshot";

const WEBSOCKET_URL =
  "ws://127.0.0.1:8000/ws/market";

const RECONNECT_DELAY = 2000;

function indexQuotesBySymbol(quotes){
  const indexedQuotes = {};

  for(const quote of quotes) {
    indexedQuotes[quote.symbol] = quote;
  }

  return indexedQuotes;
}



export default function useMarketData() {
  const [quotesBySymbol, setQuotesBySymbol] = useState({});
  const [connectionState, setConnectionState] = useState("connecting")
  const [error, setError] = useState("");

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

          if (message.type === "market_tick") {
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
    error
  };
}