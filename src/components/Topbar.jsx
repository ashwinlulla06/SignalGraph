function getConnectionLabel(connectionState) {
  if (connectionState === "connected") {
    return "Backend connected";
  }

  if (connectionState === "reconnecting") {
    return "Reconnecting";
  }

  if (connectionState === "connecting") {
    return "Connecting";
  }

  return "Offline";
}

export default function Topbar({
  onMenu,
  onSearch,
  onNewInvestigation,
  connectionState,
}) {
  return (
    <header className="topbar">
      <button
        type="button"
        className="mobile-menu"
        onClick={onMenu}
        aria-label="Open navigation"
      >
        ☰
      </button>

      <button
        type="button"
        className="search"
        onClick={onSearch}
        aria-label="Search workspace"
      >
        <span aria-hidden="true">⌕</span>
        <span>Search companies, agents, evidence…</span>
        <kbd>Ctrl K</kbd>
      </button>

      <div className="session-meta">
        <span
          className={`connection-status ${connectionState}`}
          title="Connection between this dashboard and the FastAPI backend"
        >
          <span className="connection-dot" />
          {getConnectionLabel(connectionState)}
        </span>

        <span className="dataset">Finnhub market snapshot</span>

        <div className="agents-online">
          <span className="agent-stack" aria-hidden="true">
            <span>CO</span>
            <span>MK</span>
            <span>FL</span>
            <span>NW</span>
          </span>
          <span>5 agents available</span>
        </div>

        <button
          type="button"
          className="new-run"
          onClick={onNewInvestigation}
        >
          New investigation
        </button>
      </div>
    </header>
  );
}
