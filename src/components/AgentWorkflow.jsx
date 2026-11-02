import { useEffect, useState } from "react";
import { agentDefinitions, emptyHandoff, workflowStages } from "../data/prototypeData";

function currentTime() {
  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(new Date());
}

export default function AgentWorkflow({ company, resetKey, onActiveQuestion, onHandoffsChange, showToast }) {
  const [question, setQuestion] = useState("");
  const [running, setRunning] = useState(false);
  const [complete, setComplete] = useState(false);
  const [stageIndex, setStageIndex] = useState(-1);

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
    if (complete) return true;
    return workflowStages.slice(0, stageIndex).some((stage) => stage.key === key);
  }

  function statusFor(key) {
    const activeStage = workflowStages[stageIndex];
    if (running && activeStage?.key === key) return activeStage.state;
    if (complete) return key === "coordinator" ? "Synthesis ready" : "Returned";
    if (isCompleted(key)) return key === "coordinator" ? "Coordinating returns" : "Returned";
    return key === "coordinator" ? "Ready to plan" : "Ready";
  }

  function nodeClass(key, baseClass) {
    const active = running && workflowStages[stageIndex]?.key === key;
    return `${baseClass}${active ? " running" : ""}${!active && isCompleted(key) ? " completed" : ""}`;
  }

  function inspectAgent(agent) {
    if (!running) showToast(`${agent.name}: ${agent.task}`);
  }

  const activeStage = workflowStages[stageIndex];
  const progress = complete ? 100 : activeStage?.progress ?? 0;
  const progressLabel = complete ? "Complete" : running ? `${stageIndex + 1} of ${workflowStages.length} stages` : "Ready";
  const automaticCopy = complete ? "Completed automatically" : activeStage?.copy ?? "Starts automatically after a question";

  return (
    <section className="orchestration" aria-label="Agent orchestration">
      <div className="section-head">
        <div className="section-head-copy">
          <h2>Investigation workflow</h2>
          <p>The coordinator delegates the question and combines each specialist’s evidence.</p>
        </div>
        <span className={`run-state ${running ? "running" : ""}`}>
          {complete ? "Synthesis ready" : running ? "Agents running" : "Waiting for question"}
        </span>
      </div>

      <form className="question-composer" onSubmit={submitQuestion}>
        <input
          className="question-input"
          aria-label="Research question"
          placeholder={`Ask a research question about ${company.ticker}…`}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          disabled={running}
          autoComplete="off"
        />
        <button className="ask-button" type="submit" disabled={running}>Ask agents</button>
      </form>

      <div className="agent-map">
        <svg className="agent-lines" viewBox="0 0 1000 218" preserveAspectRatio="none" aria-hidden="true">
          <path className="active-line" d="M500 62V92M125 92H875M125 92V130M375 92V130M625 92V130M875 92V130" />
        </svg>

        <div className={nodeClass("coordinator", "coordinator")}>
          <span className="agent-avatar">CO</span>
          <span><strong>Coordinator</strong><small>Plans, delegates, resolves conflicts</small></span>
          <span className="node-state">{statusFor("coordinator")}</span>
        </div>

        <div className="specialists">
          {agentDefinitions.map((agent) => (
            <button key={agent.key} className={nodeClass(agent.key, "agent-node")} onClick={() => inspectAgent(agent)}>
              <span className="agent-avatar">{agent.initials}</span>
              <span><strong>{agent.name}</strong><small>{agent.role}</small></span>
              <span className="node-state">{statusFor(agent.key)}</span>
            </button>
          ))}
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
