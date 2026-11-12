export default function Watchlist({
  companies,
  selectedTicker,
  onSelect,
  quotesBySymbol = {},
}) {
  return (
    <section className="watchlist" aria-label="Market watchlist">
      <header className="subhead">
        <h2>Market context</h2>
        <span>{companies.length} companies · Finnhub snapshot</span>
        <button type="button">Manage</button>
      </header>

      <table className="watchlist-table">
        <colgroup>
          <col className="company-column" />
          <col className="price-column" />
          <col className="change-column" />
          <col className="volume-column" />
          <col className="evidence-column" />
        </colgroup>

        <thead>
          <tr>
            <th>Company</th>
            <th>Price</th>
            <th>Day change</th>
            <th>Previous close</th>
            <th>Evidence</th>
          </tr>
        </thead>

        <tbody>
          {companies.map((company) => {
            const quote = quotesBySymbol[company.ticker];
            const price = quote?.price;
            const change = quote?.change_percent;
            const previousClose = quote?.previous_close;

            const movementClass =
              change === undefined
                ? ""
                : change >= 0
                  ? "move-up"
                  : "move-down";

            return (
              <tr
                key={company.ticker}
                className={
                  selectedTicker === company.ticker ? "selected" : ""
                }
                onClick={() => onSelect(company.ticker)}
              >
                <td>
                  <span className="company-name">{company.name}</span>
                  <span className="company-ticker">{company.ticker}</span>
                </td>

                <td>
                  {price === undefined ? "—" : `$${price.toFixed(2)}`}
                </td>

                <td className={`movement ${movementClass}`}>
                  {change === undefined
                    ? "—"
                    : `${change >= 0 ? "+" : ""}${change.toFixed(2)}%`}
                </td>

                <td>
                  {previousClose === undefined
                    ? "—"
                    : `$${previousClose.toFixed(2)}`}
                </td>

                <td>{company.evidence}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
