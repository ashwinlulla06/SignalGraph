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

export const agentGroups = [
  {
    key: "market",
    name: "Market intelligence",
    description: "Price action and anomaly context",
  },
  {
    key: "context",
    name: "Market context",
    description: "Peers, sectors and macro conditions",
  },
  {
    key: "evidence",
    name: "External evidence",
    description: "Primary sources and current reporting",
  },
  {
    key: "review",
    name: "Review and control",
    description: "Risk, challenge and claim verification",
  },
];

export const agentDefinitions = [
  {
    key: "market_data",
    group: "market",
    initials: "MD",
    name: "Market data",
    role: "Quotes and candles",
    task: "Reconstructing price action around the investigation window",
  },
  {
    key: "technical",
    group: "market",
    initials: "TA",
    name: "Technical analysis",
    role: "Trend and volatility",
    task: "Measuring returns, volatility, drawdown, and recovery",
  },
  {
    key: "anomaly",
    group: "market",
    initials: "AF",
    name: "Anomaly forensics",
    role: "Signal inspection",
    task: "Checking whether the signal is persistent, transient, or a data issue",
  },
  {
    key: "cross_market",
    group: "context",
    initials: "CM",
    name: "Cross-market",
    role: "Market-wide comparison",
    task: "Comparing the event with other monitored companies and indices",
  },
  {
    key: "sector",
    group: "context",
    initials: "SE",
    name: "Sector research",
    role: "Peer and industry context",
    task: "Checking whether related companies show the same behaviour",
  },
  {
    key: "macro",
    group: "context",
    initials: "MA",
    name: "Macro research",
    role: "Economic context",
    task: "Checking rates, economic releases, and broad market catalysts",
  },
  {
    key: "filings",
    group: "evidence",
    initials: "CF",
    name: "Company filings",
    role: "Primary company sources",
    task: "Searching filings, investor relations, and company announcements",
  },
  {
    key: "news",
    group: "evidence",
    initials: "NW",
    name: "News research",
    role: "Current reporting",
    task: "Finding time-aligned reporting from trusted financial sources",
  },
  {
    key: "regulatory",
    group: "evidence",
    initials: "RX",
    name: "Regulatory search",
    role: "Exchange and regulator notices",
    task: "Checking trading halts, enforcement actions, and official notices",
  },
  {
    key: "risk",
    group: "review",
    initials: "RK",
    name: "Risk review",
    role: "Exposure and uncertainty",
    task: "Identifying liquidity, volatility, concentration, and evidence risks",
  },
  {
    key: "skeptic",
    group: "review",
    initials: "SK",
    name: "Skeptic",
    role: "Counter-thesis",
    task: "Challenging causal claims and testing alternative explanations",
  },
  {
    key: "verifier",
    group: "review",
    initials: "EV",
    name: "Evidence verifier",
    role: "Claim validation",
    task: "Marking claims as supported, partial, contradicted, or unverified",
  },
];

export const totalAgentCount = agentDefinitions.length + 2;

export const workflowStages = [
  {
    keys: ["supervisor"],
    progress: 10,
    state: "Planning routes",
    copy: "Supervisor is selecting the relevant specialists",
    handoffTitle: "Question → Supervisor",
    handoffDetail: "Investigation objective received",
  },
  {
    keys: ["market_data", "technical", "anomaly"],
    progress: 30,
    state: "Analyzing market data",
    copy: "Market specialists are reconstructing the event",
    handoffTitle: "Supervisor → Market intelligence",
    handoffDetail: "Price action and anomaly checks assigned",
  },
  {
    keys: ["cross_market", "sector", "macro"],
    progress: 50,
    state: "Comparing context",
    copy: "Context specialists are testing broader explanations",
    handoffTitle: "Supervisor → Market context",
    handoffDetail: "Peer, sector, and macro comparison assigned",
  },
  {
    keys: ["filings", "news", "regulatory"],
    progress: 70,
    state: "Gathering evidence",
    copy: "Evidence specialists are checking primary and current sources",
    handoffTitle: "Supervisor → External evidence",
    handoffDetail: "Filings, news, and official notices assigned",
  },
  {
    keys: ["risk", "skeptic", "verifier"],
    progress: 88,
    state: "Reviewing claims",
    copy: "Review agents are challenging and verifying the evidence",
    handoffTitle: "Specialists → Review",
    handoffDetail: "Findings returned for risk and evidence checks",
  },
  {
    keys: ["synthesis"],
    progress: 97,
    state: "Writing report",
    copy: "Synthesis agent is assembling the verified report",
    handoffTitle: "Verified evidence → Synthesis",
    handoffDetail: "Supported findings approved for the final report",
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
