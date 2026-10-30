"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

type ToolResult = {
  tool: string;
  status: string;
  latency_ms: number;
  data?: Record<string, unknown>;
};

type CallRecord = {
  call_id: string;
  merchant_id: string;
  merchant_name: string;
  business_name: string;
  scenario_label: string;
  started_at: string;
  ended_at?: string | null;
  duration_seconds: number;
  language?: string | null;
  outcome: string;
  ticket_id?: string | null;
  escalated: boolean;
  opt_out: boolean;
  attention_required: boolean;
  tool_calls: string[];
  tool_results: ToolResult[];
  intent_sequence: string[];
  turn_count: number;
  repeat_complaint_count: number;
  summary: string;
};

type Props = { apiBase: string };
type Filter = "all" | "open" | "closed" | "escalated" | "attention";

function isToolResult(value: unknown): value is ToolResult {
  if (!value || typeof value !== "object") return false;
  const tool = value as Record<string, unknown>;
  return typeof tool.tool === "string"
    && typeof tool.status === "string"
    && typeof tool.latency_ms === "number";
}

function isCallRecord(value: unknown): value is CallRecord {
  if (!value || typeof value !== "object") return false;
  const call = value as Record<string, unknown>;
  return typeof call.call_id === "string"
    && typeof call.merchant_id === "string"
    && typeof call.merchant_name === "string"
    && typeof call.business_name === "string"
    && typeof call.scenario_label === "string"
    && typeof call.started_at === "string"
    && (typeof call.ended_at === "string" || call.ended_at === null)
    && typeof call.duration_seconds === "number"
    && typeof call.outcome === "string"
    && typeof call.escalated === "boolean"
    && typeof call.opt_out === "boolean"
    && typeof call.attention_required === "boolean"
    && Array.isArray(call.tool_calls)
    && call.tool_calls.every((tool) => typeof tool === "string")
    && Array.isArray(call.tool_results)
    && call.tool_results.every(isToolResult)
    && Array.isArray(call.intent_sequence)
    && call.intent_sequence.every((intent) => typeof intent === "string")
    && typeof call.turn_count === "number"
    && typeof call.repeat_complaint_count === "number"
    && typeof call.summary === "string";
}

const FILTERS: Array<{ id: Filter; label: string }> = [
  { id: "all", label: "All" },
  { id: "open", label: "Open" },
  { id: "closed", label: "Closed" },
  { id: "escalated", label: "Escalated" },
  { id: "attention", label: "Needs attention" },
];

function durationLabel(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  return `${minutes}m ${String(seconds % 60).padStart(2, "0")}s`;
}

function outcomeClass(call: CallRecord) {
  if (call.escalated || call.attention_required) return "escalated";
  if (call.outcome.startsWith("resolved:")) return "resolved";
  if (call.outcome === "open") return "open";
  return "closed";
}

function prettyOutcome(outcome: string) {
  return outcome.replace(/[:_]/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default function AdminDashboard({ apiBase }: Props) {
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [filter, setFilter] = useState<Filter>("all");
  const [expandedCall, setExpandedCall] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const refresh = useCallback(async () => {
    try {
      const response = await fetch(`${apiBase}/admin/calls`, { cache: "no-store" });
      if (!response.ok) throw new Error(`Call log request failed (${response.status})`);
      const payload: unknown = await response.json();
      if (!Array.isArray(payload) || !payload.every(isCallRecord)) {
        throw new Error("Call log response was invalid");
      }
      setCalls(payload);
      setLastUpdated(new Date());
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load call records.");
    }
  }, [apiBase]);

  useEffect(() => {
    const initialRequest = window.setTimeout(() => void refresh(), 0);
    const timer = window.setInterval(() => void refresh(), 5000);
    return () => {
      window.clearTimeout(initialRequest);
      window.clearInterval(timer);
    };
  }, [refresh]);

  const counts = useMemo(() => ({
    all: calls.length,
    open: calls.filter((call) => call.outcome === "open").length,
    closed: calls.filter((call) => call.ended_at && !call.escalated && !call.attention_required).length,
    escalated: calls.filter((call) => call.escalated).length,
    attention: calls.filter((call) => call.attention_required).length,
    resolved: calls.filter((call) => call.outcome.startsWith("resolved:")).length,
    optOut: calls.filter((call) => call.opt_out).length,
  }), [calls]);

  const visibleCalls = calls.filter((call) => {
    if (filter === "open") return call.outcome === "open";
    if (filter === "closed") return Boolean(call.ended_at) && !call.escalated;
    if (filter === "escalated") return call.escalated;
    if (filter === "attention") return call.attention_required;
    return true;
  });

  return (
    <section className="admin-dashboard" aria-labelledby="admin-title">
      <div className="admin-dashboard-heading">
        <div>
          <p className="section-label">Call operations</p>
          <h1 id="admin-title">Admin dashboard</h1>
          <p>Paytm Voice Teammate · Call monitoring panel</p>
        </div>
        <div className="admin-live-controls">
          <span className="admin-live-indicator"><span className="status-dot" data-status="ready" />Live · refreshes every 5 seconds</span>
          <button className="quiet-action" onClick={() => void refresh()} type="button">Refresh</button>
        </div>
      </div>

      <dl className="admin-stats">
        <div><dt>Total calls</dt><dd>{counts.all}</dd></div>
        <div><dt>Resolved</dt><dd>{counts.resolved}</dd></div>
        <div><dt>Escalated</dt><dd>{counts.escalated}</dd></div>
        <div><dt>Open</dt><dd>{counts.open}</dd></div>
        <div><dt>Opt-out</dt><dd>{counts.optOut}</dd></div>
      </dl>

      <div className="admin-filters" role="tablist" aria-label="Filter calls">
        {FILTERS.map((item) => (
          <button
            aria-selected={filter === item.id}
            className={filter === item.id ? "active" : ""}
            key={item.id}
            onClick={() => setFilter(item.id)}
            role="tab"
            type="button"
          >
            {item.label}{item.id === "attention" && counts.attention > 0 && <span className="attention-count">{counts.attention}</span>}
          </button>
        ))}
      </div>

      {error && <div className="admin-error" role="alert">{error}</div>}
      <p className="admin-updated">Last updated: {lastUpdated?.toLocaleTimeString() ?? "Loading…"}</p>

      <div className="admin-call-list">
        {!calls.length && !error ? (
          <div className="empty-state-box">No call records yet. Start a merchant demo call to populate this dashboard.</div>
        ) : visibleCalls.length ? visibleCalls.map((call) => {
          const expanded = expandedCall === call.call_id;
          return (
            <article className="admin-call-card" data-status={outcomeClass(call)} key={call.call_id}>
              <button
                aria-expanded={expanded}
                className="admin-call-summary"
                onClick={() => setExpandedCall(expanded ? null : call.call_id)}
                type="button"
              >
                <span className={`call-status-dot ${outcomeClass(call)}`} aria-hidden="true" />
                <span className="admin-call-merchant">
                  <strong>{call.merchant_name}</strong>
                  <small>{call.business_name} · {call.merchant_id}</small>
                </span>
                <span className="admin-call-scenario">{call.scenario_label}</span>
                <span className="admin-call-language">{call.language ?? "—"}</span>
                <span className="admin-call-duration">{call.outcome === "open" ? `LIVE · ${call.turn_count} turns` : durationLabel(call.duration_seconds)}</span>
                <span className="admin-call-outcome">{prettyOutcome(call.outcome)}</span>
                {call.attention_required && <span className="attention-flag">Attention required</span>}
              </button>
              {expanded && (
                <div className="admin-call-detail">
                  <div className="admin-detail-grid">
                    <div><span>Started</span><strong>{new Date(call.started_at).toLocaleString()}</strong></div>
                    <div><span>Ended</span><strong>{call.ended_at ? new Date(call.ended_at).toLocaleString() : "Call in progress"}</strong></div>
                    <div><span>Ticket</span><strong>{call.ticket_id ?? "None"}</strong></div>
                    <div><span>Turns</span><strong>{call.turn_count}</strong></div>
                    <div><span>Escalated</span><strong>{call.escalated ? "Yes" : "No"}</strong></div>
                    <div><span>Opt-out</span><strong>{call.opt_out ? "DNC recorded" : "No"}</strong></div>
                  </div>
                  <div><h3>Intent sequence</h3><p>{call.intent_sequence.length ? call.intent_sequence.join(" → ") : "No intents recorded"}</p></div>
                  <div>
                    <h3>Tool calls</h3>
                    {call.tool_results.length ? (
                      <ul className="admin-tool-list">
                        {call.tool_results.map((tool, index) => (
                          <li key={`${tool.tool}-${index}`}><code>{tool.tool}</code><span>{tool.status}</span><span>{tool.latency_ms} ms</span></li>
                        ))}
                      </ul>
                    ) : <p>No tool calls recorded</p>}
                  </div>
                  <div><h3>Summary</h3><p>{call.summary}</p></div>
                </div>
              )}
            </article>
          );
        }) : <div className="empty-state-box">No calls match this filter.</div>}
      </div>
    </section>
  );
}
