import { useRef, useState } from "react";
import { createMarketSeries } from "../data/prototypeData";

const WIDTH = 1000;
const HEIGHT = 500;
const LEFT = 68;
const RIGHT = 86;
const TOP = 28;
const BOTTOM = 64;
const ZOOM_LEVELS = [1, 1.35, 1.8, 2.5];

export default function MarketChart({ company, zoomIndex, liveCandles = [] }) {
  const svgRef = useRef(null);
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ left: 0, top: 0 });

  const prototypeData =
    createMarketSeries(company);

  const visibleLiveCandles =
    liveCandles.slice(-prototypeData.length);

  const prototypeCount =
    Math.max(
      0,
      prototypeData.length -
        visibleLiveCandles.length
    );

  const allData = [
    ...prototypeData.slice(0, prototypeCount),
    ...visibleLiveCandles,
  ];
  const visibleCount = Math.max(16, Math.round(allData.length / ZOOM_LEVELS[zoomIndex]));
  const data = allData.slice(-visibleCount);

  const plotWidth = WIDTH - LEFT - RIGHT;
  const plotHeight = HEIGHT - TOP - BOTTOM;
  const low = Math.min(...data.map((point) => point.low));
  const high = Math.max(...data.map((point) => point.high));
  const padding = (high - low) * 0.12;
  const yMin = low - padding;
  const yMax = high + padding;

  const x = (index) => LEFT + (index + 0.5) * (plotWidth / data.length);
  const y = (value) => TOP + ((yMax - value) / (yMax - yMin)) * plotHeight;
  const candleWidth = Math.max(7, Math.min(18, (plotWidth / data.length) * 0.58));
  const latest = data[data.length - 1];
  const baselinePoints = data
    .map((point, index) => `${x(index)},${y(point.close + Math.sin(index * 0.28) * (yMax - yMin) * 0.045)}`)
    .join(" ");

  function handlePointerMove(event) {
    const bounds = svgRef.current.getBoundingClientRect();
    const svgX = ((event.clientX - bounds.left) / bounds.width) * WIDTH;
    const nextIndex = Math.max(
      0,
      Math.min(data.length - 1, Math.floor((svgX - LEFT) / (plotWidth / data.length))),
    );
    setHoveredIndex(nextIndex);
    setTooltipPosition({
      left: Math.min(bounds.width - 175, Math.max(8, event.clientX - bounds.left)),
      top: Math.min(bounds.height - 45, Math.max(50, event.clientY - bounds.top)),
    });
  }

  const hoveredPoint = hoveredIndex === null ? null : data[hoveredIndex];

  return (
    <div className="chart-wrap">
      <svg
        ref={svgRef}
        id="marketChart"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label={`${company.ticker} price chart`}
        onPointerMove={handlePointerMove}
        onPointerLeave={() => setHoveredIndex(null)}
      >
        <g aria-hidden="true">
          {Array.from({ length: 7 }, (_, index) => {
            const lineY = TOP + index * (plotHeight / 6);
            const value = yMax - index * ((yMax - yMin) / 6);
            return (
              <g key={`y-${index}`}>
                <line x1={LEFT} y1={lineY} x2={WIDTH - RIGHT} y2={lineY} stroke="#282828" />
                <text x={WIDTH - RIGHT + 12} y={lineY + 5} fill="#858585" fontSize="13" fontFamily="Bahnschrift">{value.toFixed(2)}</text>
              </g>
            );
          })}

          {Array.from({ length: 8 }, (_, index) => {
            const lineX = LEFT + index * (plotWidth / 7);
            const pointIndex = Math.min(data.length - 1, Math.round(index * ((data.length - 1) / 7)));
            return (
              <g key={`x-${index}`}>
                <line x1={lineX} y1={TOP} x2={lineX} y2={HEIGHT - BOTTOM} stroke="#202020" />
                <text
                  x={lineX}
                  y={HEIGHT - 35}
                  fill="#858585"
                  fontSize="12"
                  textAnchor={index === 0 ? "start" : index === 7 ? "end" : "middle"}
                  fontFamily="Bahnschrift"
                >
                  {data[pointIndex].label}
                </text>
              </g>
            );
          })}

          <text x="20" y={HEIGHT / 2} fill="#999999" fontSize="12" fontFamily="Segoe UI" textAnchor="middle" transform={`rotate(-90 20 ${HEIGHT / 2})`}>Price (USD)</text>
          <text x={WIDTH / 2} y={HEIGHT - 9} fill="#999999" fontSize="12" fontFamily="Segoe UI" textAnchor="middle">Time (ET)</text>
        </g>

        <polyline points={baselinePoints} fill="none" stroke="#777777" strokeWidth="1" strokeDasharray="4 5" opacity=".58" />

        <g>
          {data.map((point, index) => {
            const rising = point.close >= point.open;
            const color = rising ? "#eeeeee" : "#777777";
            return (
              <g className="candle" style={{ animationDelay: `${index * 6}ms` }} key={point.startTime ??`${point.label}-${index}`}>
                <line x1={x(index)} y1={y(point.high)} x2={x(index)} y2={y(point.low)} stroke={color} strokeWidth="1.2" />
                <rect
                  x={x(index) - candleWidth / 2}
                  y={Math.min(y(point.open), y(point.close))}
                  width={candleWidth}
                  height={Math.max(3, Math.abs(y(point.open) - y(point.close)))}
                  rx="1"
                  fill={rising ? "#eeeeee" : "#222222"}
                  stroke={color}
                  strokeWidth="1.2"
                />
              </g>
            );
          })}
        </g>

        <line x1={LEFT} y1={y(latest.close)} x2={WIDTH - RIGHT} y2={y(latest.close)} stroke="#bcbcbc" strokeDasharray="2 4" opacity=".65" />
        <g>
          <rect x={WIDTH - RIGHT + 5} y={y(latest.close) - 12} width="66" height="24" rx="4" fill="#eeeeee" />
          <text x={WIDTH - RIGHT + 38} y={y(latest.close) + 5} textAnchor="middle" fill="#111111" fontSize="12" fontFamily="Bahnschrift">{latest.close.toFixed(2)}</text>
        </g>

        {hoveredPoint && (
          <g className="crosshair">
            <line x1={x(hoveredIndex)} y1={TOP} x2={x(hoveredIndex)} y2={HEIGHT - BOTTOM} stroke="#777777" strokeDasharray="3 4" />
            <line x1={LEFT} y1={y(hoveredPoint.close)} x2={WIDTH - RIGHT} y2={y(hoveredPoint.close)} stroke="#777777" strokeDasharray="3 4" />
          </g>
        )}
      </svg>

      {hoveredPoint && (
        <div className="chart-tooltip visible" style={tooltipPosition}>
          <div className="tooltip-title">{company.ticker} · {hoveredPoint.label}</div>
          O {hoveredPoint.open.toFixed(2)} &nbsp; H {hoveredPoint.high.toFixed(2)}<br />
          L {hoveredPoint.low.toFixed(2)} &nbsp; C {hoveredPoint.close.toFixed(2)}
        </div>
      )}
    </div>
  );
}

export { ZOOM_LEVELS };
