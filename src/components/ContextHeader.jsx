export default function ContextHeader({ activeQuestion }) {
  return (
    <div className="context-row">
      <div className="context-title">
        <h1>{activeQuestion ? "Active investigation" : "Research workspace"}</h1>
        <p>{activeQuestion || "Review market context, then ask the agent team to investigate."}</p>
      </div>
      <div className="context-actions">
        <button className="quiet-button">Export brief</button>
        <button className="quiet-button">View run history</button>
      </div>
    </div>
  );
}
