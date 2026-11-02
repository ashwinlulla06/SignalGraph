export const companies = [
  {
    ticker: "NVDA",
    name: "NVIDIA",
    exchange: "NASDAQ · USD",
    mark: "N",
    price: 197.92,
    change: -1.43,
    volume: "42.8M",
    evidence: 128,
    seed: 17,
  },
  {
    ticker: "AMD",
    name: "Advanced Micro Devices",
    exchange: "NASDAQ · USD",
    mark: "A",
    price: 173.34,
    change: 1.38,
    volume: "31.6M",
    evidence: 94,
    seed: 23,
  },
  {
    ticker: "MSFT",
    name: "Microsoft",
    exchange: "NASDAQ · USD",
    mark: "M",
    price: 532.11,
    change: 0.44,
    volume: "18.2M",
    evidence: 86,
    seed: 29,
  },
  {
    ticker: "GOOGL",
    name: "Alphabet",
    exchange: "NASDAQ · USD",
    mark: "G",
    price: 281.44,
    change: -0.56,
    volume: "22.4M",
    evidence: 73,
    seed: 31,
  },
  {
    ticker: "BABA",
    name: "Alibaba Group",
    exchange: "NYSE · USD",
    mark: "B",
    price: 102.38,
    change: 2.16,
    volume: "19.3M",
    evidence: 83,
    seed: 41,
  },
];

export const agentDefinitions = [
  {
    key: "market",
    initials: "MK",
    name: "Market agent",
    role: "Prices and estimates",
    task: "Comparing peer price response and estimate revisions",
  },
  {
    key: "filings",
    initials: "FL",
    name: "Filings agent",
    role: "Filings and transcripts",
    task: "Extracting capacity and capex language from recent filings",
  },
  {
    key: "supply",
    initials: "SC",
    name: "Supply agent",
    role: "Channel and supply chain",
    task: "Checking lead times, inventory, and supplier commentary",
  },
  {
    key: "risk",
    initials: "RK",
    name: "Risk agent",
    role: "Policy and counter-signals",
    task: "Testing export restrictions and demand pull-forward",
  },
];

export const workflowStages = [
  {
    key: "coordinator",
    progress: 8,
    state: "Planning tasks",
    copy: "Coordinator is planning the investigation",
    handoffTitle: "Question → Coordinator",
    handoffDetail: "Research objective received",
  },
  {
    key: "market",
    progress: 26,
    state: "Analyzing prices",
    copy: "Market agent is comparing prices and estimates",
    handoffTitle: "Coordinator → Market",
    handoffDetail: "Price and estimate comparison assigned",
  },
  {
    key: "filings",
    progress: 45,
    state: "Reading filings",
    copy: "Filings agent is extracting primary-source evidence",
    handoffTitle: "Coordinator → Filings",
    handoffDetail: "Filings and transcripts assigned",
  },
  {
    key: "supply",
    progress: 64,
    state: "Checking channels",
    copy: "Supply agent is mapping suppliers and lead times",
    handoffTitle: "Coordinator → Supply",
    handoffDetail: "Channel validation assigned",
  },
  {
    key: "risk",
    progress: 82,
    state: "Testing risks",
    copy: "Risk agent is challenging the emerging thesis",
    handoffTitle: "Coordinator → Risk",
    handoffDetail: "Counter-thesis validation assigned",
  },
  {
    key: "coordinator",
    progress: 94,
    state: "Synthesizing returns",
    copy: "Coordinator is reconciling agent findings",
    handoffTitle: "Agents → Coordinator",
    handoffDetail: "Specialist findings returned with citations",
  },
];

export const emptyHandoff = {
  time: "Waiting",
  title: "No active handoffs",
  detail: "Agent activity will appear after a question is submitted",
};

export function createMarketSeries(company) {
  let seed = company.seed;
  const random = () => {
    seed = (seed * 9301 + 49297) % 233280;
    return seed / 233280;
  };

  const count = 44;
  const start = company.price * (1 - (company.change / 100) * 0.75);
  let value = start;
  const data = [];

  for (let index = 0; index < count; index += 1) {
    const open = value;
    const drift = (company.price - start) / count;
    const close = open + drift + (random() - 0.48) * company.price * 0.0045;
    const high = Math.max(open, close) + random() * company.price * 0.0028;
    const low = Math.min(open, close) - random() * company.price * 0.0028;
    value = close;
    data.push({
      open,
      close,
      high,
      low,
      label: `${String(7 + Math.floor(index / 6)).padStart(2, "0")}:${String((index % 6) * 10).padStart(2, "0")}`,
    });
  }

  const correction = company.price - data[data.length - 1].close;
  return data.map((point, index) => {
    const adjustment = correction * (index / (count - 1));
    return {
      open: point.open + adjustment,
      close: point.close + adjustment,
      high: point.high + adjustment,
      low: point.low + adjustment,
      label: point.label,
    };
  });
}
