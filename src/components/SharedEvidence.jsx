export default function SharedEvidence({ handoffs, automaticInvestigation }) {
  const result = automaticInvestigation?.result;
  const findings = result?.findings || [];
  const evidence = result?.evidence || [];
  const selectedAgents = result?.selected_agents || [];

  const averageConfidence = findings.length
    ? Math.round(
        findings.reduce(
          (total, finding) => total + finding.confidence,
          0
        ) / findings.length * 100
      )
    : null;

  let title = "Monitoring finalized market candles";
  let summary = "SignalGraph will start an investigation when the anomaly model detects a meaningful event.";

  if (automaticInvestigation?.status === "running") {
    title = `Investigating ${automaticInvestigation.symbol}`;
    summary = "The supervisor is routing this anomaly through the relevant research and review agents.";
  }

  if (automaticInvestigation?.status === "failed") {
    title = `Investigation stopped for ${automaticInvestigation.symbol}`;
    summary = automaticInvestigation.error;
  }

  if (automaticInvestigation?.status === "complete") {
    title = `Investigation complete for ${automaticInvestigation.symbol}`;
    summary = result?.final_report || "The investigation completed without a final report.";
  }

  return (
    <section className="evidence-stream" aria-label="Shared evidence and synthesis">
      <header className="subhead">
        <h2>Shared evidence</h2>
        <span>Agent handoffs and current synthesis</span>
        <button>Open all</button>
      </header>

      <div className="evidence-body">
        <div className="handoffs">
          {handoffs.map((handoff, index) => (
            <div className="handoff" key={`${handoff.time}-${handoff.title}-${index}`}>
              <time>{handoff.time}</time>
              <strong>{handoff.title}</strong><br />
              {handoff.detail}
            </div>
          ))}
        </div>

        <article className="synthesis">
          <div className="synthesis-label">
            <span>Current synthesis</span>
            {averageConfidence !== null && (
              <span className="num">Confidence {averageConfidence}%</span>
            )}
          </div>
          <h3>{title}</h3>
          <p>{summary}</p>
          <div className="source-row">
            <span className="source">{findings.length} findings</span>
            <span className="source">{evidence.length} evidence items</span>
            <span className="source">{handoffs.length} recent handoffs</span>
          </div>
          <div className="shared-memory">
            <span>
              {selectedAgents.length
                ? `${selectedAgents.length} agents contributed: ${selectedAgents.join(", ")}`
                : "Waiting for an automatic investigation"}
            </span>
          </div>
        </article>
      </div>
    </section>
  );
}
