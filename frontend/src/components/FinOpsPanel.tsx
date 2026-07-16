import { useCallback, useEffect, useState } from "react";
import type { FinOpsSummary } from "../types";
import { apiUrl } from "../utils";

const POLL_MS = 5000;

// Editable defaults; token prices in USD per 1M tokens.
const DEFAULT_PRICE_IN = 2.5;
const DEFAULT_PRICE_OUT = 10.0;
const DEFAULT_REQUESTS_PER_DAY = 100_000;

export function fmtTokens(n: number): string {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(n >= 10_000_000_000 ? 0 : 1)}B`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(n >= 10_000_000 ? 0 : 1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(n >= 10_000 ? 0 : 1)}k`;
  return String(n);
}

function fmtUsd(n: number): string {
  if (n >= 1000) {
    return `$${n.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
  }
  return `$${n.toFixed(2)}`;
}

function fmtMs(ms: number): string {
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${ms}ms`;
}

function LatencyRow({
  label,
  p50,
  p95,
  maxMs,
  highlight,
}: {
  label: string;
  p50: number;
  p95: number;
  maxMs: number;
  highlight?: boolean;
}) {
  const width = maxMs > 0 ? Math.max((p50 / maxMs) * 100, 2) : 0;
  return (
    <div className="finops-lat-row">
      <span className="finops-lat-label">{label}</span>
      <div className="finops-lat-track">
        <div
          className={`finops-lat-bar ${highlight ? "fast" : ""}`}
          style={{ width: `${width}%` }}
        />
      </div>
      <span className="finops-lat-value">
        {fmtMs(p50)} <span className="finops-lat-p95">p95 {fmtMs(p95)}</span>
      </span>
    </div>
  );
}

export function FinOpsPanel() {
  const [summary, setSummary] = useState<FinOpsSummary | null>(null);
  const [priceIn, setPriceIn] = useState(DEFAULT_PRICE_IN);
  const [priceOut, setPriceOut] = useState(DEFAULT_PRICE_OUT);
  const [requestsPerDay, setRequestsPerDay] = useState(DEFAULT_REQUESTS_PER_DAY);

  const load = useCallback(async () => {
    try {
      const response = await fetch(apiUrl("/api/finops/summary"));
      if (response.ok) setSummary(await response.json());
    } catch {
      // panel is additive: keep last data on transient errors
    }
  }, []);

  useEffect(() => {
    void load();
    const timer = setInterval(() => void load(), POLL_MS);
    return () => clearInterval(timer);
  }, [load]);

  async function handleReset() {
    try {
      await fetch(apiUrl("/api/finops/reset"), { method: "POST" });
      void load();
    } catch {
      // ignore
    }
  }

  if (!summary) {
    return <div className="activity-empty">Loading FinOps metrics…</div>;
  }

  const answered = summary.cache_hits + summary.llm_turns;
  const hitRatePct = Math.round(summary.hit_rate * 100);
  const spent = summary.tokens_in + summary.tokens_out;
  const saved = summary.saved_in + summary.saved_out;
  const spentUsd = (summary.tokens_in / 1e6) * priceIn + (summary.tokens_out / 1e6) * priceOut;
  const savedUsd = (summary.saved_in / 1e6) * priceIn + (summary.saved_out / 1e6) * priceOut;
  const savedShare = spent + saved > 0 ? (saved / (spent + saved)) * 100 : 0;

  // Projection: at the observed hit rate and measured avg turn cost, what does
  // LangCache avoid per month at the given request volume?
  const avgTurnIn = summary.avg_tokens_in_per_llm_turn;
  const avgTurnOut = summary.avg_tokens_out_per_llm_turn;
  const monthlyHits = requestsPerDay * summary.hit_rate * 30;
  const monthlySavedIn = monthlyHits * avgTurnIn;
  const monthlySavedOut = monthlyHits * avgTurnOut;
  const monthlySavedUsd = (monthlySavedIn / 1e6) * priceIn + (monthlySavedOut / 1e6) * priceOut;

  const maxLat = Math.max(summary.latency_llm_ms.p50, summary.latency_hit_ms.p50, 1);

  const sliceEconomyPct =
    summary.slice_full_tokens > 0
      ? Math.round(
          ((summary.slice_full_tokens - summary.slice_served_tokens) / summary.slice_full_tokens) * 100
        )
      : 0;

  return (
    <div className="finops-content">
      {/* ── Session counters ── */}
      <section className="activity-section">
        <div className="activity-section-header">
          <span className="activity-section-title">
            <img src="/icons/langcache-64-duotone.svg" alt="" className="section-icon" />
            Semantic Cache · Session
          </span>
          <button className="finops-reset-btn" onClick={handleReset} type="button">
            Reset
          </button>
        </div>
        <div className="finops-stat-grid">
          <div className="finops-stat">
            <span className="finops-stat-value finops-accent">{hitRatePct}%</span>
            <span className="finops-stat-label">cache hit rate</span>
          </div>
          <div className="finops-stat">
            <span className="finops-stat-value">{summary.cache_hits}/{answered}</span>
            <span className="finops-stat-label">answered from cache</span>
          </div>
          <div className="finops-stat">
            <span className="finops-stat-value">{fmtTokens(spent)}</span>
            <span className="finops-stat-label">tokens spent · {fmtUsd(spentUsd)}</span>
          </div>
          <div className="finops-stat">
            <span className="finops-stat-value finops-accent">{fmtTokens(saved)}</span>
            <span className="finops-stat-label">tokens avoided · {fmtUsd(savedUsd)}</span>
          </div>
        </div>
        {spent + saved > 0 && (
          <div className="finops-share">
            <div className="finops-share-track">
              <div className="finops-share-bar" style={{ width: `${savedShare}%` }} />
            </div>
            <span className="finops-share-label">
              {Math.round(savedShare)}% of the session's token demand served by Redis, not the LLM
            </span>
          </div>
        )}
        {summary.blocked > 0 && (
          <div className="finops-footnote">
            +{summary.blocked} request{summary.blocked !== 1 ? "s" : ""} blocked by the semantic
            guardrail before reaching the LLM.
          </div>
        )}
      </section>

      {/* ── Latency ── */}
      <section className="activity-section">
        <div className="activity-section-header">
          <span className="activity-section-title">
            <img src="/icons/semantic-routing-64-duotone.svg" alt="" className="section-icon" />
            Latency · p50
          </span>
        </div>
        <div className="finops-lat-list">
          <LatencyRow
            label="Cache lookup (API)"
            p50={summary.latency_lookup_ms.p50}
            p95={summary.latency_lookup_ms.p95}
            maxMs={maxLat}
            highlight
          />
          <LatencyRow
            label="Cache hit (end-to-end)"
            p50={summary.latency_hit_ms.p50}
            p95={summary.latency_hit_ms.p95}
            maxMs={maxLat}
            highlight
          />
          <LatencyRow
            label="Full agent turn"
            p50={summary.latency_llm_ms.p50}
            p95={summary.latency_llm_ms.p95}
            maxMs={maxLat}
          />
        </div>
      </section>

      {/* ── KYC-360 context slicing (only once the journey ran) ── */}
      {summary.slice_calls > 0 && (
        <section className="activity-section">
          <div className="activity-section-header">
            <span className="activity-section-title">
              <img src="/icons/context-retriever-64-duotone.svg" alt="" className="section-icon" />
              Customer-360 Slicing
            </span>
            <span className="activity-section-count">{summary.slice_calls} calls</span>
          </div>
          <div className="finops-stat-grid">
            <div className="finops-stat">
              <span className="finops-stat-value">{fmtTokens(summary.slice_full_tokens)}</span>
              <span className="finops-stat-label">full-profile tokens</span>
            </div>
            <div className="finops-stat">
              <span className="finops-stat-value finops-accent">
                {fmtTokens(summary.slice_served_tokens)}
              </span>
              <span className="finops-stat-label">served after slicing · −{sliceEconomyPct}%</span>
            </div>
          </div>
        </section>
      )}

      {/* ── Projection ── */}
      <section className="activity-section">
        <div className="activity-section-header">
          <span className="activity-section-title">
            <img src="/icons/RDI-64-duotone.svg" alt="" className="section-icon" />
            Monthly Projection
          </span>
        </div>
        <div className="finops-inputs">
          <label className="finops-input">
            <span>Requests / day</span>
            <input
              type="number"
              min={0}
              value={requestsPerDay}
              onChange={(e) => setRequestsPerDay(Number(e.target.value) || 0)}
            />
          </label>
          <label className="finops-input">
            <span>$ / 1M input</span>
            <input
              type="number"
              min={0}
              step={0.1}
              value={priceIn}
              onChange={(e) => setPriceIn(Number(e.target.value) || 0)}
            />
          </label>
          <label className="finops-input">
            <span>$ / 1M output</span>
            <input
              type="number"
              min={0}
              step={0.1}
              value={priceOut}
              onChange={(e) => setPriceOut(Number(e.target.value) || 0)}
            />
          </label>
        </div>
        <div className="finops-projection">
          <div className="finops-stat">
            <span className="finops-stat-value finops-accent">
              {fmtTokens(monthlySavedIn + monthlySavedOut)}
            </span>
            <span className="finops-stat-label">tokens avoided / month</span>
          </div>
          <div className="finops-stat">
            <span className="finops-stat-value finops-accent">{fmtUsd(monthlySavedUsd)}</span>
            <span className="finops-stat-label">est. LLM cost avoided / month</span>
          </div>
        </div>
        <div className="finops-footnote">
          At the observed {hitRatePct}% hit rate and the measured average of {fmtTokens(avgTurnIn + avgTurnOut)} tokens
          per uncached agent turn ({summary.llm_turns} sample{summary.llm_turns !== 1 ? "s" : ""} in this environment).
        </div>
      </section>

      <div className="panel-footer-badge">Powered by Redis LangCache</div>
    </div>
  );
}
