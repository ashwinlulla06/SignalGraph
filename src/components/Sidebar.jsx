export default function Sidebar({ open, onClose }) {
  return (
    <>
      {open && <button className="sidebar-scrim" onClick={onClose} aria-label="Close navigation" />}
      <aside className={`sidebar ${open ? "open" : ""}`} id="sidebar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 18V10l5 3 5-7 6 4v8" />
              <path d="M4 18h16" />
            </svg>
          </span>
          SignalGraph
        </div>

        <nav className="nav" aria-label="Primary navigation">
          <button className="nav-item active"><span className="nav-icon">◫</span>Workspace</button>
          <button className="nav-item"><span className="nav-icon">◇</span>Investigations <span className="count">4</span></button>
          <button className="nav-item"><span className="nav-icon">⌁</span>Agent runs <span className="count">3</span></button>
          <button className="nav-item"><span className="nav-icon">⌕</span>Evidence</button>
          <button className="nav-item"><span className="nav-icon">▤</span>Research notes</button>
          <div className="nav-label">System</div>
          <button className="nav-item"><span className="nav-icon">◎</span>Agent registry</button>
          <button className="nav-item"><span className="nav-icon">↔</span>Shared memory</button>
          <button className="nav-item"><span className="nav-icon">◌</span>Data sources</button>
        </nav>

        <div className="sidebar-footer">
          <div className="system-state">Orchestrator ready</div>
          <div className="user">
            <span className="avatar">AK</span>
            <span>Ashwin K.<small>Research analyst</small></span>
          </div>
        </div>
      </aside>
    </>
  );
}
