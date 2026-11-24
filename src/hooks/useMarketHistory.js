import { useState, useRef, useEffect } from "react";
import { normalizeMarketCandle } from "../utils/marketCandles";

const HISTORY_BASE_URL = "http://127.0.0.1:8000/api/markets"
const HISTORY_SIZE = 100
const CACHE_DURATION_MS = 60_000;


export default function useMarketHistory(symbol) {
    const [candles, setCandles] = useState([]);

    const [loading, setLoading] = useState(false);

    const [error, setError] = useState("")

    const cacheRef = useRef(new Map());

    useEffect(() => {
        let cancelled = false;

        async function loadHistory() {
            const cacheKey = `${symbol}:${HISTORY_SIZE}`

            const cachedEntry = cacheRef.current.get(cacheKey)

            const cacheAge = cachedEntry ? Date.now() - cachedEntry.fetchedAt : Infinity

            const cacheIsFresh = cacheAge < CACHE_DURATION_MS;

            if(cachedEntry)
            {
                setCandles(cachedEntry.candles)
            }

            if(cacheIsFresh){
                setLoading(false)
                setError("");
                return;
            }

            if(!cachedEntry)
                setCandles([])

            setLoading(true)
            setError("");

            try{
                const encodedSymbol = encodeURIComponent(symbol);
                const url = `${HISTORY_BASE_URL}/${encodedSymbol}/history?output_size=${HISTORY_SIZE}`;

                const response = await fetch(url)

                if (!response.ok)
                    throw new Error(`History request failed: ${response.status}`)

                const rawCandles = await response.json();

                if (!Array.isArray(rawCandles))
                    throw new Error("History response was not a list.")

                const normalizedCandles = rawCandles.map(normalizeMarketCandle).sort((first, second) => first.startTime - second.startTime)

                cacheRef.current.set(cacheKey, {candles: normalizedCandles, fetchedAt: Date.now()});

                if (cancelled)
                    return;

                setCandles(normalizedCandles)
            } catch(requestError){
                if (cancelled)
                    return;

                setError(requestError.message)

                if(!cachedEntry)
                    setCandles([]);
            } finally {
                if(!cancelled)
                    setLoading(false)
            }
        }

        if (symbol)
            loadHistory();

        return function cleanup(){
            cancelled = true;
        }

    }, [symbol])

    return {candles, loading, error}
}