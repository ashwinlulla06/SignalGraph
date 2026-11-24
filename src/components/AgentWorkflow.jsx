import { useEffect, useState } from "react";
import { agentDefinitions, agentGroups, emptyHandoff, workflowStages } from "../data/prototypeData";

function currentTime() {
  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(new Date());
}

export default function AgentWorkflow({
  company,
  resetKey,
  onActiveQuestion,
  onHandoffsChange,
  showToast,
  automaticInvestigation
}) {
  const [question, setQuestion] = useState("");
  const [running, setRunning] = useState(false);
  const [complete, setComplete] = useState(false);
  const [stageIndex, setStageIndex] = useState(-1);

  const automaticRunning = automaticInvestigation?.status === "running";
  const automaticComplete = automaticInvestigation?.status === "complete";
  const automaticFailed = automaticInvestigation?.status === "failed";

  useEffect(() => {
    setQuestion("");
    setRunning(false);
    setComplete(false);
    setStageIndex(-1);
    onActiveQuestion("");
    onHandoffsChange([emptyHandoff]);
  }, [resetKey, onActiveQuestion, onHandoffsChange]);

  useEffect(() => {
    if (!running || stageIndex < 0) return undefined;

    if (stageIndex >= workflowStages.length) {
      setRunning(false);
      setComplete(true);
      showToast("Investigation complete · synthesis is ready");
      return undefined;
    }

    const timer = window.setTimeout(() => {
      const nextIndex = stageIndex + 1;
      if (nextIndex < workflowStages.length) {
        const nextStage = workflowStages[nextIndex];
        onHandoffsChange((current) => [
          {
            time: currentTime(),
            title: nextStage.handoffTitle,
            detail: nextStage.handoffDetail,
          },
          ...current,
        ].slice(0, 4));
      }
      setStageIndex(nextIndex);
    }, 1500);

    return () => window.clearTimeout(timer);
  }, [running, stageIndex, onHandoffsChange, showToast]);

  useEffect(() => {
    if (!automaticInvestigation) return;

    const { status, symbol, result, error } = automaticInvestigation;

    if (status === "running") {
      onActiveQuestion(`Automatic anomaly investigation for ${symbol}`);
      onHandoffsChange([{
        time: currentTime(),
        title: "Anomaly monitor → Supervisor",
        detail: `A live anomaly triggered an investigation for ${symbol}`
      }]);
      showToast(`Automatic investigation started for ${symbol}`);
      return;
    }

    if (status === "complete") {
      onActiveQuestion(
        result?.question || `Automatic anomaly investigation for ${symbol}`
      );

      const backendHandoffs = (result?.handoffs || [])
        .map((handoff) => ({
          time: currentTime(),
          title: `${handoff.from_agent} → ${handoff.to_agent}`,
          detail: handoff.summary
        }))
        .reverse()
        .slice(0, 4);

      onHandoffsChange(
        backendHandoffs.length ? backendHandoffs : [emptyHandoff]
      );
      showToast(`Automatic investigation completed for ${symbol}`);
      return;
    }

    if (status === "failed") {
      onActiveQuestion(`Automatic anomaly investigation for ${symbol}`);
      onHandoffsChange([{
        time: currentTime(),
        title: "Investigation stopped",
        detail: error
      }]);
      showToast(`Automatic investigation failed for ${symbol}`);
    }
  }, [automaticInvestigation, onActiveQuestion, onHandoffsChange, showToast]);

  function submitQuestion(event) {
    event.preventDefault();
    const cleanQuestion = question.trim();
    if (!cleanQuestion) {
      showToast("Enter a research question to start the agents");
      return;
    }

    const firstStage = workflowStages[0];
    setRunning(true);
    setComplete(false);
    setStageIndex(0);
    onActiveQuestion(cleanQuestion);
    onHandoffsChange([{
      time: currentTime(),
      title: firstStage.handoffTitle,
      detail: firstStage.handoffDetail,
    }]);
  }

  function isCompleted(key) {
    if (automaticComplete) {
      const selectedAgents = automaticInvestigation.result?.selected_agents || [];
      return key === "supervisor" || key === "synthesis" || selectedAgents.includes(key);
    }

    if (complete) return true;
    if (stageIndex <= 0) return false;
    return workflowStages
      .slice(0, stageIndex)
      .some((stage) => stage.keys.includes(key));
  }

  function statusFor(key) {
    if (automaticRunning && key === "supervisor") return "Routing anomaly";
    if (automaticComplete && key === "synthesis") return "Report ready";
    if (automaticComplete && isCompleted(key)) return "Complete";

    const activeStage = workflowStages[stageIndex];
    if (running && activeStage?.keys.includes(key)) return activeStage.state;
    if (complete) return key === "synthesis" ? "Report ready" : "Complete";
    if (isCompleted(key)) return "Returned";
    if (key === "supervisor") return "Ready to route";
    if (key === "synthesis") return "Waiting for evidence";
    return "Available";
  }

  function nodeClass(key, baseClass) {
    const automaticActive = automaticRunning && key === "supervisor";
    const active = automaticActive || (running && workflowStages[stageIndex]?.keys.includes(key));
    return `${baseClass}${active ? " running" : ""}${!active && isCompleted(key) ? " completed" : ""}`;
  }

  function inspectAgent(agent) {
    if (!running) showToast(`${agent.name}: ${agent.task}`);
  }

  const activeStage = workflowStages[stageIndex];
  const progress = automaticComplete ? 100 : automaticRunning ? 10 : complete ? 100 : activeStage?.progress ?? 0;
  const progressLabel = automaticFailed
    ? "Failed"
    : automaticComplete || complete
      ? "Complete"
      : automaticRunning
        ? "Running automatically"
        : running
          ? `${stageIndex + 1} of ${workflowStages.length} phases`
          : "Ready";
  const automaticCopy = automaticFailed
    ? automaticInvestigation.error
    : automaticRunning
      ? "Triggered by the live anomaly monitor"
      : automaticComplete
        ? "Completed automatically"
        : activeStage?.copy ?? "Starts automatically after a question";

  return (
    <section className="orchestration" aria-label="Agent orchestration">
      <div className="section-head">
        <div className="section-head-copy">
          <h2>Investigation workflow</h2>
          <p>The supervisor routes each investigation through the relevant market, evidence, and review specialists.</p>
        </div>
        <span className={`run-state ${running || automaticRunning ? "running" : ""}`}>
          {automaticFailed
            ? "Investigation failed"
            : automaticComplete || complete
              ? "Synthesis ready"
              : automaticRunning
                ? "Automatic investigation"
                : running
                  ? "Agents running"
                  : "Monitoring for anomalies"}
        </span>
      </div>

      <form className="question-composer" onSubmit={submitQuestion}>
        <input
          className="question-input"
          aria-label="Research question"
          placeholder={`Ask a research question about ${company.ticker}…`}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          disabled={running || automaticRunning}
          autoComplete="off"
        />
        <button className="ask-button" type="submit" disabled={running || automaticRunning}>Ask agents</button>
      </form>

      <div className="agent-map">
        <div className={nodeClass("supervisor", "workflow-anchor")}>
          <span className="agent-avatar">SV</span>
          <span><strong>Supervisor</strong><small>Plans the investigation and selects specialists</small></span>
          <span className="node-state">{statusFor("supervisor")}</span>
        </div>

        <div className="workflow-connector" aria-hidden="true" />

        <div className="agent-groups">
          {agentGroups.map((group) => (
            <section className="agent-group" key={group.key}>
              <header className="agent-group-head">
                <h3>{group.name}</h3>
                <p>{group.description}</p>
              </header>

              <div className="agent-group-nodes">
                {agentDefinitions
                  .filter((agent) => agent.group === group.key)
                  .map((agent) => (
                    <button
                      type="button"
                      key={agent.key}
                      className={nodeClass(agent.key, "agent-node")}
                      onClick={() => inspectAgent(agent)}
                    >
                      <span className="agent-avatar">{agent.initials}</span>
                      <span><strong>{agent.name}</strong><small>{agent.role}</small></span>
                      <span className="node-state">{statusFor(agent.key)}</span>
                    </button>
                  ))}
              </div>
            </section>
          ))}
        </div>

        <div className="workflow-connector" aria-hidden="true" />

        <div className={nodeClass("synthesis", "workflow-anchor synthesis-agent")}>
          <span className="agent-avatar">SY</span>
          <span><strong>Synthesis</strong><small>Builds the final report from verified evidence</small></span>
          <span className="node-state">{statusFor("synthesis")}</span>
        </div>
      </div>

      <div className="run-footer">
        <div className="run-progress"><span style={{ width: `${progress}%` }} /></div>
        <span className="progress-copy">{progressLabel}</span>
        <span className="auto-copy">{automaticCopy}</span>
      </div>
    </section>
  );
}
