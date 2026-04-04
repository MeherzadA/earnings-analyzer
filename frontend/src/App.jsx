import { useState, useMemo } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

const API_URL = "http://127.0.0.1:8000/analyze";

function currentQuarter(date) {
  const month = date.getMonth() + 1;
  if (month <= 3) return 1;
  if (month <= 6) return 2;
  if (month <= 9) return 3;
  return 4;
}

function SearchBar({ onSubmit, loading }) {
  const today = useMemo(() => new Date(), []);
  const [ticker, setTicker] = useState("");
  const [year, setYear] = useState(today.getFullYear());
  const [quarter, setQuarter] = useState(currentQuarter(today));

  function handleSubmit(e) {
    e.preventDefault();
    if (!ticker.trim()) return;
    onSubmit({ ticker: ticker.trim(), year: Number(year), quarter: Number(quarter) });
  }

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <div className="search-fields">
        <div className="search-field ticker-field">
          <label>Ticker</label>
          <input
            type="text"
            placeholder="AAPL"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            maxLength={10}
            required
          />
        </div>
        <div className="search-field">
          <label>Year</label>
          <input
            type="number"
            min="2000"
            max="2100"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            required
          />
        </div>
        <div className="search-field">
          <label>Quarter</label>
          <select value={quarter} onChange={(e) => setQuarter(e.target.value)}>
            <option value="1">Q1</option>
            <option value="2">Q2</option>
            <option value="3">Q3</option>
            <option value="4">Q4</option>
          </select>
        </div>
      </div>
      <button className="analyze-btn" disabled={loading}>
        {loading ? (
          <span className="btn-inner">
            <span className="spinner" /> Analyzing
          </span>
        ) : (
          <span className="btn-inner">Analyze</span>
        )}
      </button>
    </form>
  );
}

function StockPriceChart({ dailyPrices, ticker }) {
  if (!dailyPrices || dailyPrices.length === 0) {
    return null;
  }

  // Transform for Recharts: needs {label, price}
  const chartData = dailyPrices.map((item) => ({
    label: item.label || item.date,
    price: item.price,
  }));

  const minPrice = Math.min(...chartData.map(d => d.price));
  const maxPrice = Math.max(...chartData.map(d => d.price));
  const range = maxPrice - minPrice;
  const padding = range * 0.1; // 10% padding

  return (
    <div className="card chart-card">
      <p className="card-label">Stock Price Movement</p>
      <p className="chart-title">{ticker} Post-Earnings</p>
      
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e4e7ec" />
          <XAxis
            dataKey="label"
            stroke="#6b7280"
            style={{ fontSize: "12px" }}
          />
          <YAxis
            stroke="#6b7280"
            style={{ fontSize: "12px" }}
            domain={[minPrice - padding, maxPrice + padding]}
          />
          <Tooltip
            contentStyle={{
              background: "rgba(255,255,255,0.95)",
              border: "1px solid #e4e7ec",
              borderRadius: "8px",
              padding: "8px",
            }}
            formatter={(value) => `$${value.toFixed(2)}`}
            labelStyle={{ color: "#0f1117" }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="price"
            stroke="#0f62fe"
            dot={{ fill: "#0f62fe", r: 5 }}
            activeDot={{ r: 7 }}
            isAnimationActive={true}
            name="Close Price"
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="chart-stats">
        <div className="stat">
          <span className="label">Earnings Date</span>
          <span className="value">${chartData[0]?.price.toFixed(2)}</span>
        </div>
        <div className="stat">
          <span className="label">Day 1</span>
          <span className="value">${chartData[1]?.price.toFixed(2)}</span>
        </div>
        <div className="stat">
          <span className="label">Day 5</span>
          <span className="value">${chartData[5]?.price.toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
}

function SentimentCard({ sentiment, score }) {
  const colors = {
    positive: { bg: "#f0faf4", border: "#a3d9b6", text: "#1a6b3c", label: "#2d9e5f" },
    negative: { bg: "#fff4f4", border: "#f5b8b8", text: "#8b1a1a", label: "#d44" },
    neutral:  { bg: "#f5f5f5", border: "#d0d0d0", text: "#444",    label: "#777" },
  };
  const c = colors[sentiment?.toLowerCase()] || colors.neutral;
  const pct = ((score + 1) / 2) * 100;

  const barColor =
    score > 0.2 ? "#2d9e5f" : score < -0.2 ? "#d44444" : "#999";

  return (
    <div className="card sentiment-card" style={{ background: c.bg, borderColor: c.border }}>
      <p className="card-label">Sentiment</p>
      <p className="sentiment-label" style={{ color: c.label }}>
        {sentiment ? sentiment.charAt(0).toUpperCase() + sentiment.slice(1) : "—"}
      </p>
      <div className="score-row">
        <span className="score-val" style={{ color: c.text }}>
          {score != null ? score.toFixed(2) : "—"}
        </span>
        <div className="score-track">
          <div
            className="score-fill"
            style={{ width: `${pct}%`, background: barColor }}
          />
          <div className="score-midline" />
        </div>
      </div>
      <div className="score-axis">
        <span>−1</span>
        <span>0</span>
        <span>+1</span>
      </div>
    </div>
  );
}

function SummaryCard({ summary, ticker, year, quarter, cached }) {
  return (
    <div className="card summary-card">
      <div className="summary-header">
        <div>
          <p className="card-label">Summary</p>
          <p className="summary-meta">
            {ticker} · Q{quarter} {year}
            {cached && <span className="cached-badge">Cached</span>}
          </p>
        </div>
      </div>
      <p className="summary-text">{summary}</p>
    </div>
  );
}

function TabsSection({ keyClaims, redFlags, opportunities }) {
  const [active, setActive] = useState("claims");

  const tabs = [
    { id: "claims",       label: "Key Claims",    data: keyClaims,    color: "#2563eb" },
    { id: "flags",        label: "Red Flags",     data: redFlags,     color: "#dc2626" },
    { id: "opportunities",label: "Opportunities", data: opportunities, color: "#16a34a" },
  ];

  const current = tabs.find((t) => t.id === active);

  return (
    <div className="card tabs-card">
      <div className="tabs-header">
        {tabs.map((t) => (
          <button
            key={t.id}
            className={`tab-btn ${active === t.id ? "tab-active" : ""}`}
            style={active === t.id ? { borderBottomColor: t.color, color: t.color } : {}}
            onClick={() => setActive(t.id)}
          >
            {t.label}
            <span className="tab-count">{t.data?.length ?? 0}</span>
          </button>
        ))}
      </div>
      <div className="tab-content">
        {current?.data?.length ? (
          current.data.map((item, i) => (
            <div className="list-item" key={i}>
              <span
                className="list-dot"
                style={{ background: current.color }}
              />
              <p>{item}</p>
            </div>
          ))
        ) : (
          <p className="empty-tab">None reported for this period.</p>
        )}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="empty-state">
      <div className="empty-icon">📊</div>
      <p className="empty-title">Enter a ticker to begin</p>
      <p className="empty-sub">
        Fetch and analyze earnings call transcripts powered by Gemini AI.
      </p>
    </div>
  );
}

export default function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function handleSubmit({ ticker, year, quarter }) {
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker, year, quarter }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "Request failed");
      setResult(data);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-inner">
          <div className="brand">
            <span className="brand-mark">EA</span>
            <span className="brand-name">Earnings Analyzer</span>
          </div>
        </div>
      </header>

      <main className="main">
        <div className="search-section">
          <h1 className="hero-title">Earnings Call Intelligence</h1>
          <p className="hero-sub">
            AI-powered analysis of earnings transcripts — sentiment, key claims, risks, and opportunities.
          </p>
          <SearchBar onSubmit={handleSubmit} loading={loading} />
          {error && <div className="error-banner">{error}</div>}
        </div>

        {!result && !loading && <EmptyState />}

        {loading && (
          <div className="loading-state">
            <div className="loading-bar">
              <div className="loading-fill" />
            </div>
            <p className="loading-text">Fetching transcript and running analysis…</p>
          </div>
        )}

        {result && (
          <div className="results">
            <div className="top-row">
              <SentimentCard
                sentiment={result.analysis?.sentiment}
                score={result.analysis?.sentiment_score}
              />
              <SummaryCard
                summary={result.analysis?.summary}
                ticker={result.ticker}
                year={result.year}
                quarter={result.quarter}
                cached={result.cached}
              />
            </div>
            {result.daily_prices && result.daily_prices.length > 0 && (
              <StockPriceChart
                dailyPrices={result.daily_prices}
                ticker={result.ticker}
              />
            )}
            <TabsSection
              keyClaims={result.analysis?.key_claims}
              redFlags={result.analysis?.red_flags}
              opportunities={result.analysis?.opportunities}
            />
          </div>
        )}
      </main>
    </div>
  );
}