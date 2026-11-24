import { useRef, useState } from "react";

const WIDTH = 1000;
const HEIGHT = 500;
const LEFT = 68;
const RIGHT = 86;
const TOP = 28;
const BOTTOM = 64;
const ZOOM_LEVELS = [1, 1.35, 1.8, 2.5];

export default function MarketChart({ company, zoomIndex, candles = [], loading, previousClose, analysisResults = [] }) {
  const svgRef = useRef(null);
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ left: 0, top: 0 });

  if(candles.length === 0)
    return (
      <div className="chart-wrap chart-empty">
        {loading ? "Loading historical candles..." : "No historical candles available"}
      </div>
    );

  const allData = candles;
  const visibleCount = Math.max(16, Math.round(allData.length / ZOOM_LEVELS[zoomIndex]));
  const data = allData.slice(-visibleCount);

  const analysisByStartTime = new Map(analysisResults.map((result) => [result.startTime, result]))

  const plotWidth = WIDTH - LEFT - RIGHT;
  const plotHeight = HEIGHT - TOP - BOTTOM;
  const hasPreviousClose = Number.isFinite(previousClose)
  const scaleValues = data.map((point) => point.close)
  if(hasPreviousClose){
    scaleValues.push(previousClose)
  }
  const low = Math.min(...scaleValues)
  const high = Math.max(...scaleValues)
  const priceRange = Math.max(high-low, high * 0.001, 0.01)
  const padding = priceRange * 0.12
  const yMin = low - padding;
  const yMax = high + padding;

  const x = (index) => {
    if (data.length === 1) {
      return ( LEFT + plotWidth/2 )
    }
    return ( LEFT + index * (plotWidth / (data.length - 1)) )
  }
  const y = (value) => TOP + ((yMax - value) / (yMax - yMin)) * plotHeight;

  const anomalyMarkers = data.map((point, index) => {
    const analysis = analysisByStartTime.get(point.startTime);

    if(!analysis?.is_anomaly){
      return null;
    }

    return {
      point, index, analysis
    }
  }).filter(Boolean)

  const latest = data[data.length - 1];
  const comparisonPrice = hasPreviousClose ? previousClose : data[0].close;
  const chartIsUp = latest.close >= comparisonPrice;
  const chartColor = chartIsUp ? "#35b779" : "#df5b5b";
  const linePoints = data.map((point, index) => `${x(index)},${y(point.close)}`).join(" ");
  const areaPoints = [`${x(0)},${HEIGHT - BOTTOM}`,
    linePoints,
    `${x(data.length - 1)},${
      HEIGHT - BOTTOM
    }`,
  ].join(" ");
  
  function handlePointerMove(event) {
    const bounds = svgRef.current.getBoundingClientRect();
    const svgX = ((event.clientX - bounds.left) / bounds.width) * WIDTH;
    const pointSpacing =
      data.length === 1
        ? plotWidth
        : plotWidth /
          (data.length - 1);

    const nextIndex = Math.max(
      0,
      Math.min(
        data.length - 1,
        Math.round(
          (svgX - LEFT) /
          pointSpacing
        )
      )
    );
    setHoveredIndex(nextIndex);
    setTooltipPosition({
      left: Math.min(bounds.width - 175, Math.max(8, event.clientX - bounds.left)),
      top: Math.min(bounds.height - 45, Math.max(50, event.clientY - bounds.top)),
    });
  }

  const hoveredPoint = hoveredIndex === null ? null : data[hoveredIndex];

  const hoveredAnalysis = hoveredPoint ? analysisByStartTime.get(hoveredPoint.startTime) : undefined;

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
        <title>{`${company.ticker} one-minute price history`}</title>
        <desc>
          {`Closing-price line for ${company.ticker}. The chart is ${chartIsUp ? "up" : "down"} relative to ${hasPreviousClose ? "the previous close" : "the first visible close"}.`}
        </desc>

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

        <polygon
          points={areaPoints}
          fill={chartColor}
          fillOpacity="0.12"
          pointerEvents="none"
        />

        <polyline
          points={linePoints}
          fill="none"
          stroke={chartColor}
          strokeWidth="2.5"
          strokeLinejoin="round"
          strokeLinecap="round"
          pointerEvents="none"
        />

        {anomalyMarkers.map(
          ({ point, index, analysis }) => {
            const pointY = y(point.close);

            const markerY = Math.max(
              TOP + 12,
              pointY - 18
            );

            return (
              <g
                key={`anomaly-${point.startTime}`}
                pointerEvents="none"
              >
                <line
                  x1={x(index)}
                  y1={pointY - 4}
                  x2={x(index)}
                  y2={markerY + 6}
                  stroke="#d5d5d5"
                  strokeWidth="1"
                />

                <circle
                  cx={x(index)}
                  cy={markerY}
                  r="7"
                  fill="#eeeeee"
                  stroke="#111111"
                  strokeWidth="2"
                />

                <text
                  x={x(index)}
                  y={markerY + 4}
                  fill="#111111"
                  fontSize="10"
                  fontWeight="700"
                  textAnchor="middle"
                >
                  !
                </text>

                <title>
                  {`Anomaly score ${analysis.decision_score.toFixed(4)}`}
                </title>
              </g>
            );
          }
        )}

        <circle
          cx={x(data.length - 1)}
          cy={y(latest.close)}
          r="4"
          fill={chartColor}
        />

        {hasPreviousClose && (
          <g>
            <line
              x1={LEFT}
              y1={y(previousClose)}
              x2={WIDTH - RIGHT}
              y2={y(previousClose)}
              stroke="#929292"
              strokeWidth="1"
              strokeDasharray="3 6"
            />

            <text
              x={WIDTH - RIGHT - 8}
              y={y(previousClose) - 8}
              textAnchor="end"
              fill="#a5a5a5"
              fontSize="12"
              fontFamily="Bahnschrift"
            >
              Previous close {previousClose.toFixed(2)}
            </text>
          </g>
        )}
        <line x1={LEFT} y1={y(latest.close)} x2={WIDTH - RIGHT} y2={y(latest.close)} stroke={chartColor} strokeDasharray="2 4" opacity=".65" />
        <g>
          <rect x={WIDTH - RIGHT + 5} y={y(latest.close) - 12} width="66" height="24" rx="4" fill={chartColor} />
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
          <div className="tooltip-title">
            {company.ticker} · {hoveredPoint.label}
            {hoveredPoint.status === "forming" ? " · Live" : ""}
          </div>
          O {hoveredPoint.open.toFixed(2)} &nbsp; H {hoveredPoint.high.toFixed(2)}<br />
          L {hoveredPoint.low.toFixed(2)} &nbsp; C {hoveredPoint.close.toFixed(2)}<br />
          Volume {hoveredPoint.volume.toLocaleString()}
        </div>
      )}

      {hoveredAnalysis && (
        <div
          className={`tooltip-analysis ${
            hoveredAnalysis.is_anomaly
              ? "anomaly"
              : ""
          }`}
        >
          ML analysis:{" "}
          {hoveredAnalysis.is_anomaly
            ? "Anomaly"
            : "Normal"}

          <br />

          Score{" "}
          {hoveredAnalysis.decision_score
            .toFixed(4)}
        </div>
      )}
    </div>
  );
}

export { ZOOM_LEVELS };
