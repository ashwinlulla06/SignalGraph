import { useState } from "react";
import MarketChart, { ZOOM_LEVELS } from "./MarketChart";

const ranges = ["15m", "1h", "1D", "1W"];

export default function MarketPanel({ company, companies, onSelectCompany }) {
  const [range, setRange] = useState("1h");
  const [zoomIndex, setZoomIndex] = useState(0);

  function selectNextCompany() {
    const currentIndex = companies.findIndex((item) => item.ticker === company.ticker);
    onSelectCompany(companies[(currentIndex + 1) % companies.length].ticker);
  }

  return (
    <section className="market-card" aria-label="Market context">
      <header className="market-header">
        <button className="symbol-button" onClick={selectNextCompany} aria-label="Change company">
          <span className="symbol-mark">{company.mark}</span>
          <span><strong>{company.ticker}</strong><small>{company.exchange}</small></span>
          <span className="symbol-chevron">⌄</span>
        </button>

        <div className="market-metrics">
          <div><div className="metric-label">Last price</div><div className="metric-value primary">${company.price.toFixed(2)}</div></div>
          <div><div className="metric-label">Day change</div><div className={`metric-value ${company.change >= 0 ? "move-up" : "move-down"}`}>{Math.abs(company.change).toFixed(2)}%</div></div>
          <div><div className="metric-label">Volume</div><div className="metric-value">{company.volume}</div></div>
          <div><div className="metric-label">Linked evidence</div><div className="metric-value">{company.evidence} sources</div></div>
        </div>
      </header>

      <div className="chart-toolbar">
        {ranges.map((item) => (
          <button key={item} className={`range-button ${range === item ? "active" : ""}`} onClick={() => setRange(item)}>{item}</button>
        ))}
        <span className="chart-label">{company.ticker} market context</span>
        <span className="chart-note">Peer baseline</span>
        <div className="zoom-controls" aria-label="Chart zoom controls">
          <button className="zoom-button" aria-label="Zoom out" title="Zoom out" disabled={zoomIndex === 0} onClick={() => setZoomIndex(zoomIndex - 1)}>−</button>
          <span className="zoom-level">{Math.round(ZOOM_LEVELS[zoomIndex] * 100)}%</span>
          <button className="zoom-button" aria-label="Zoom in" title="Zoom in" disabled={zoomIndex === ZOOM_LEVELS.length - 1} onClick={() => setZoomIndex(zoomIndex + 1)}>+</button>
        </div>
      </div>

      <MarketChart company={company} zoomIndex={zoomIndex} />
    </section>
  );
}
