export default function Watchlist({ companies, selectedTicker, onSelect }) {
  return (
    <section className="watchlist" aria-label="Market watchlist">
      <header className="subhead">
        <h2>Market context</h2>
        <span>5 companies · prototype prices</span>
        <button>Manage</button>
      </header>
      <table>
        <thead><tr><th>Company</th><th>Price</th><th>Change</th><th>Volume</th><th>Evidence</th></tr></thead>
        <tbody>
          {companies.map((company) => (
            <tr key={company.ticker} className={selectedTicker === company.ticker ? "selected" : ""} onClick={() => onSelect(company.ticker)}>
              <td><span className="company-name">{company.name}</span><span className="company-ticker">{company.ticker}</span></td>
              <td>${company.price.toFixed(2)}</td>
              <td className={`movement ${company.change >= 0 ? "move-up" : "move-down"}`}>{Math.abs(company.change).toFixed(2)}%</td>
              <td>{company.volume}</td>
              <td>{company.evidence}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
