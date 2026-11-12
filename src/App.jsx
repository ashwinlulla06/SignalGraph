import { useEffect, useState } from "react";
import AgentWorkflow from "./components/AgentWorkflow";
import ContextHeader from "./components/ContextHeader";
import MarketPanel from "./components/MarketPanel";
import SearchModal from "./components/SearchModal";
import SharedEvidence from "./components/SharedEvidence";
import Sidebar from "./components/Sidebar";
import Toast from "./components/Toast";
import Topbar from "./components/Topbar";
import Watchlist from "./components/Watchlist";
import { companies, emptyHandoff } from "./data/prototypeData";
import useMarketData from "./hooks/useMarketData";

export default function App() {
  const [selectedTicker, setSelectedTicker] = useState("NVDA");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [activeQuestion, setActiveQuestion] = useState("");
  const [handoffs, setHandoffs] = useState([emptyHandoff]);
  const [workflowResetKey, setWorkflowResetKey] = useState(0);
  const [toast, setToast] = useState("");

  const {quotesBySymbol, connectionState, error} = useMarketData();

  const selectedCompany = companies.find((company) => company.ticker === selectedTicker) || companies[0];

  const selectedQuote = quotesBySymbol[selectedCompany.ticker];

  useEffect(() => {
    function handleKeyboard(event) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSearchOpen(true);
      }
      if (event.key === "Escape") {
        setSearchOpen(false);
        setSidebarOpen(false);
      }
    }

    window.addEventListener("keydown", handleKeyboard);
    return () => window.removeEventListener("keydown", handleKeyboard);
  }, []);

  useEffect(() => {
    if (!toast) return undefined;
    const timer = window.setTimeout(() => setToast(""), 2600);
    return () => window.clearTimeout(timer);
  }, [toast]);

  useEffect(() => {
    if(error){
      setToast(error);
    }
  }, [error])

  function selectCompany(ticker) {
    setSelectedTicker(ticker);
    setToast(`Market context switched to ${ticker}`);
  }

  function startNewInvestigation() {
    setWorkflowResetKey((current) => current + 1);
    setToast("Ready for a new research question");
  }

  return (
    <div className="app">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <main className="main">
        <Topbar
          onMenu={() => setSidebarOpen(true)}
          onSearch={() => setSearchOpen(true)}
          onNewInvestigation={startNewInvestigation}
          connectionState={connectionState}
        />

        <div className="workspace">
          <ContextHeader activeQuestion={activeQuestion} />

          <div className="primary-grid">
            <MarketPanel
              company={selectedCompany}
              companies={companies}
              onSelectCompany={selectCompany}
              quote={selectedQuote}
            />

            <AgentWorkflow
              company={selectedCompany}
              resetKey={workflowResetKey}
              onActiveQuestion={setActiveQuestion}
              onHandoffsChange={setHandoffs}
              showToast={setToast}
            />
          </div>

          <div className="secondary-grid">
            <Watchlist
              companies={companies}
              selectedTicker={selectedTicker}
              onSelect={selectCompany}
              quotesBySymbol={quotesBySymbol}
            />
            <SharedEvidence handoffs={handoffs} />
          </div>
        </div>
      </main>

      <SearchModal
        open={searchOpen}
        companies={companies}
        onClose={() => setSearchOpen(false)}
        onSelectCompany={selectCompany}
        showToast={setToast}
      />
      <Toast message={toast} />
    </div>
  );
}
