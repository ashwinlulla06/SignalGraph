const marketTimeFormatter = new Intl.DateTimeFormat(
    "en-US",
    {
        timeZone: "America/New_York",
        hour: "2-digit",
        minute: "2-digit"
    }
);

export function normalizeMarketCandle(rawCandle){
    const startTime = new Date(rawCandle.start_time).getTime();

    return {
        ...rawCandle,
        startTime,
        label: marketTimeFormatter.format(new Date(startTime))
    }
}

export function mergeCandleSeries(historicalCandles, liveCandles){
    const candlesByStartTime = new Map();

    for (const candle of historicalCandles){
        candlesByStartTime.set(candle.startTime, candle)
    }

    for (const candle of liveCandles){
        candlesByStartTime.set(candle.startTime, candle)
    }

    return Array.from(candlesByStartTime.values()).sort((first, second) => first.startTime - second.startTime)
}