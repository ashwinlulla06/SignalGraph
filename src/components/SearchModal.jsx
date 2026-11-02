import { useState } from "react";

export default function SearchModal({ open, companies, onClose, onSelectCompany, showToast }) {
  const [query, setQuery] = useState("");
  if (!open) return null;

  const extraItems = [
    { title: "Market agent", detail: "Prices and estimates", type: "Agent" },
    { title: "Shared memory", detail: "Cross-agent research context", type: "System" },
    { title: "AI infrastructure demand", detail: "Active investigation", type: "Investigation" },
  ];

  const companyItems = companies.map((company) => ({
    title: company.ticker,
    detail: company.name,
    type: "Company",
    ticker: company.ticker,
  }));
  
  const cleanQuery = query.trim().toLowerCase();
  const results = [...companyItems, ...extraItems].filter((item) => (
    !cleanQuery || `${item.title} ${item.detail}`.toLowerCase().includes(cleanQuery)
  ));

  function choose(item) {
    if (item.ticker) onSelectCompany(item.ticker);
    else showToast(`${item.title}: ${item.detail}`);
    setQuery("");
    onClose();
  }

  return (
    <div className="command-backdrop open" role="dialog" aria-modal="true" aria-label="Search SignalGraph" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <div className="command">
        <input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search companies, agents, evidence…" autoComplete="off" />
        <div className="results">
          {results.map((item) => (
            <button className="result" key={`${item.type}-${item.title}`} onClick={() => choose(item)}>
              <b>{item.title}</b><span>{item.detail}</span><small>{item.type}</small>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
