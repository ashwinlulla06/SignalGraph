import { TextAlignCenter } from "lucide-react";

export default function Topbar({ onMenu, onSearch, onNewInvestigation }) {
  return (
    <header className="topbar">
      <button className="mobile-menu" onClick={onMenu} aria-label="Open navigation">☰</button>
      <button className="search" onClick={onSearch} aria-label="Search workspace">
        <span style={{textAlign: "center", fontWeight: 400, color: "white"}}>⌕</span>
        <span>Search companies, agents, evidence…</span>
        <kbd>Ctrl K</kbd>
      </button>

      <div className="session-meta">
        <span className="dataset">Prototype dataset · Oct 31</span>
        <div className="agents-online">
          <span className="agent-stack"><span>CO</span><span>MK</span><span>FL</span><span>NW</span></span>
          <span>5 agents available</span>
        </div>
        <button className="new-run" onClick={onNewInvestigation}>New investigation</button>
      </div>
    </header>
  );
}
