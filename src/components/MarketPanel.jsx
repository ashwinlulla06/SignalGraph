import { useState } from "react";
import MarketChart, { ZOOM_LEVELS } from "./MarketChart";


export default function MarketPanel({
  company,
  companies,
  onSelectCompany,
  quote,
  candles,
  historyLoading,
  analysisResults
}) {
  const [zoomIndex, setZoomIndex] = useState(0);

  const latestCandle = candles[candles.length - 1];

  const chartPrice =
    latestCandle?.symbol === company.ticker
      ? latestCandle.close
      : undefined;

  const price = chartPrice ?? quote?.price;
  const previousClose = quote?.previous_close;

  const change =
    Number.isFinite(price) &&
    Number.isFinite(previousClose)
      ? ((price - previousClose) / previousClose) * 100
      : quote?.change_percent;

  function selectNextCompany() {
    const currentIndex = companies.findIndex(
      (item) => item.ticker === company.ticker,
    );
    const nextCompany = companies[(currentIndex + 1) % companies.length];
    onSelectCompany(nextCompany.ticker);
  }

  return (
    <section className="market-card" aria-label="Market context">
      <header className="market-header">
        <button
          type="button"
          className="symbol-button"
          onClick={selectNextCompany}
          aria-label="Change company"
        >
          <span className="symbol-mark">{company.mark}</span>
          <span>
            <strong>{company.ticker}</strong>
            <small>{company.exchange}</small>
          </span>
          <span className="symbol-chevron">⌄</span>
        </button>

        <div className="market-metrics">
          <div>
            <div className="metric-label">Last price</div>
            <div className="metric-value primary">
              {price === undefined ? "—" : `$${price.toFixed(2)}`}
            </div>
          </div>

          <div>
            <div className="metric-label">Day change</div>
            <div
              className={`metric-value ${
                change === undefined
                  ? ""
                  : change >= 0
                    ? "move-up"
                    : "move-down"
              }`}
            >
              {change === undefined
                ? "—"
                : `${change >= 0 ? "+" : ""}${change.toFixed(2)}%`}
            </div>
          </div>

          <div>
            <div className="metric-label">Previous close</div>
            <div className="metric-value">
              {previousClose === undefined
                ? "—"
                : `$${previousClose.toFixed(2)}`}
            </div>
          </div>

          <div>
            <div className="metric-label">Linked evidence</div>
            <div className="metric-value">{company.evidence} sources</div>
          </div>
        </div>
      </header>

      <div className="chart-toolbar">

        <span className="chart-label">
          {company.ticker} · 1-minute history
        </span>
        <span className="chart-note">
          {historyLoading ? "Loading Candles..." : `${candles.length} candles`}
        </span>

        <div className="zoom-controls" aria-label="Chart zoom controls">
          <button
            type="button"
            className="zoom-button"
            aria-label="Zoom out"
            title="Zoom out"
            disabled={zoomIndex === 0}
            onClick={() => setZoomIndex(zoomIndex - 1)}
          >
            −
          </button>
          <span className="zoom-level">
            {Math.round(ZOOM_LEVELS[zoomIndex] * 100)}%
          </span>
          <button
            type="button"
            className="zoom-button"
            aria-label="Zoom in"
            title="Zoom in"
            disabled={zoomIndex === ZOOM_LEVELS.length - 1}
            onClick={() => setZoomIndex(zoomIndex + 1)}
          >
            +
          </button>
        </div>
      </div>

      <MarketChart 
        company={company} 
        zoomIndex={zoomIndex} 
        candles={candles} 
        loading={historyLoading}
        previousClose={previousClose}
        analysisResults={analysisResults}
      />
    </section>
  );
}
