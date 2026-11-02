export default function SharedEvidence({ handoffs }) {
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
          <div className="synthesis-label"><span>Current synthesis</span><span className="num">Confidence 78%</span></div>
          <h3>Demand appears broader, but visibility is uneven beyond the current reporting window.</h3>
          <p>Networking orders and power equipment lead times support deployment outside the largest buyers. Export restrictions and possible order pull-forward remain unresolved.</p>
          <div className="source-row">
            <span className="source">18 earnings calls</span>
            <span className="source">42 supply signals</span>
            <span className="source">11 filings</span>
            <span className="source">7 policy sources</span>
          </div>
          <div className="shared-memory">
            <span className="memory-avatars"><span>MK</span><span>FL</span><span>SC</span><span>RK</span></span>
            <span>4 agents contributed · 6 claims retain citations</span>
          </div>
        </article>
      </div>
    </section>
  );
}
