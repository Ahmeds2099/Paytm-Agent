"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { DemoMerchant } from "@/lib/voice/types";

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
  attention_reason?: string | null;
  requires_human_approval?: boolean;
  refund_request?: {
    approval_id?: string;
    txn_id?: string;
    amount?: number;
    transaction_date?: string | null;
    status?: string;
  } | null;
  phone?: string;
  city?: string;
  member_since?: string;
  total_transactions?: number;
  account_balance?: string;
  transaction_id?: string | null;
  transaction_amount?: number | null;
  transaction_status?: string | null;
  transaction_date?: string | null;
  expected_date?: string | null;
  tool_calls: string[];
  tool_results: ToolResult[];
  intent_sequence: string[];
  turn_count: number;
  repeat_complaint_count: number;
  summary: string;
};

type Props = {
  apiBase: string;
  onCallMerchant(merchant: DemoMerchant): void;
};
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
    && (call.attention_reason === undefined || call.attention_reason === null || typeof call.attention_reason === "string")
    && (call.requires_human_approval === undefined || typeof call.requires_human_approval === "boolean")
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

export default function AdminDashboard({ apiBase, onCallMerchant }: Props) {
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [merchants, setMerchants] = useState<DemoMerchant[]>([]);
  const [filter, setFilter] = useState<Filter>("all");
  const [expandedCall, setExpandedCall] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [profileCall, setProfileCall] = useState<CallRecord | null>(null);
  const [resetPending, setResetPending] = useState(false);

  const loadMerchants = useCallback(async () => {
    const response = await fetch(`${apiBase}/demo/merchants`, { cache: "no-store" });
    if (!response.ok) throw new Error(`Merchant list request failed (${response.status})`);
    const payload: unknown = await response.json();
    if (!Array.isArray(payload)) throw new Error("Merchant list response was invalid");
    setMerchants(payload as DemoMerchant[]);
  }, [apiBase]);

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
    const initialMerchants = window.setTimeout(() => {
      void loadMerchants().catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Could not load merchant profiles.");
      });
    }, 0);
    const timer = window.setInterval(() => void refresh(), 5000);
    return () => {
      window.clearTimeout(initialRequest);
      window.clearTimeout(initialMerchants);
      window.clearInterval(timer);
    };
  }, [loadMerchants, refresh]);

  const resetDemo = async () => {
    if (!window.confirm("Reset demo calls, opt-outs, tickets, refunds, and pending approvals? This cannot be undone.")) return;
    setResetPending(true);
    try {
      const response = await fetch(`${apiBase}/demo/reset`, { method: "POST" });
      if (!response.ok) throw new Error(`Demo reset failed (${response.status})`);
      setProfileCall(null);
      await Promise.all([refresh(), loadMerchants()]);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not reset the demo.");
    } finally {
      setResetPending(false);
    }
  };

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
          <button className="danger-quiet admin-reset-button" disabled={resetPending} onClick={() => void resetDemo()} type="button">
            {resetPending ? "Resetting…" : "Reset demo data"}
          </button>
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
              <div className="admin-call-summary">
                <span className={`call-status-dot ${outcomeClass(call)}`} aria-hidden="true" />
                <span className="admin-call-merchant">
                  <button className="admin-merchant-name" onClick={() => { setProfileCall(call); setExpandedCall(call.call_id); }} type="button">{call.merchant_name}</button>
                  <small>{call.business_name} · {call.merchant_id}</small>
                </span>
                <span className="admin-call-scenario">{call.scenario_label}</span>
                <span className="admin-call-language">{call.language ?? "—"}</span>
                <span className="admin-call-duration">{call.outcome === "open" ? `LIVE · ${call.turn_count} turns` : durationLabel(call.duration_seconds)}</span>
                <span className="admin-call-outcome">{prettyOutcome(call.outcome)}</span>
                {call.attention_required && (
                  <span className="attention-flag">
                    {call.requires_human_approval ? "Attention needed · Human approval required" : "Attention needed"}
                  </span>
                )}
                <button
                  aria-expanded={expanded}
                  className="admin-expand-button"
                  onClick={() => setExpandedCall(expanded ? null : call.call_id)}
                  type="button"
                >
                  {expanded ? "Hide details" : "Details"}
                </button>
              </div>
              {expanded && (
                <div className="admin-call-detail">
                  {call.attention_required && (
                    <section className="attention-detail">
                      <h3>Why attention is needed</h3>
                      <p>{call.attention_reason || "This call needs a sales or support team review."}</p>
                      {call.requires_human_approval && <strong>Human approval required before refund action.</strong>}
                    </section>
                  )}
                  <div className="admin-detail-grid">
                    <div><span>Started</span><strong>{new Date(call.started_at).toLocaleString()}</strong></div>
                    <div><span>Ended</span><strong>{call.ended_at ? new Date(call.ended_at).toLocaleString() : "Call in progress"}</strong></div>
                    <div><span>Ticket</span><strong>{call.ticket_id ?? "None"}</strong></div>
                    <div><span>Turns</span><strong>{call.turn_count}</strong></div>
                    <div><span>Escalated</span><strong>{call.escalated ? "Yes" : "No"}</strong></div>
                    <div><span>Opt-out</span><strong>{call.opt_out ? "DNC recorded" : "No"}</strong></div>
                    <div><span>Transaction</span><strong>{call.refund_request?.txn_id ?? call.transaction_id ?? "—"}</strong></div>
                    <div><span>Amount</span><strong>{call.refund_request?.amount != null ? `₹${call.refund_request.amount.toLocaleString("en-IN")}` : call.transaction_amount != null ? `₹${call.transaction_amount.toLocaleString("en-IN")}` : "—"}</strong></div>
                    <div><span>Transaction date</span><strong>{call.refund_request?.transaction_date ?? call.transaction_date ?? "—"}</strong></div>
                    <div><span>Expected date</span><strong>{call.expected_date ?? "—"}</strong></div>
                    <div><span>Refund approval</span><strong>{call.refund_request?.status ?? "Not requested"}</strong></div>
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
                  {profileCall && (() => {
                    const merchant = merchants.find((item) => item.merchant_id === profileCall.merchant_id);
                    const latestTransaction = [...profileCall.tool_results].reverse().find((item) => {
                      const data = item.data ?? {};
                      return typeof data.txn_id === "string" || typeof data.transaction_id === "string";
                    })?.data;
                    const txnAmount = profileCall.refund_request?.amount
                      ?? profileCall.transaction_amount
                      ?? (typeof latestTransaction?.amount === "number" ? latestTransaction.amount : undefined);
                    const txnId = profileCall.refund_request?.txn_id
                      ?? profileCall.transaction_id
                      ?? (typeof latestTransaction?.txn_id === "string" ? latestTransaction.txn_id : undefined);
                    const txnDate = profileCall.refund_request?.transaction_date
                      ?? profileCall.transaction_date
                      ?? (typeof latestTransaction?.settled_date === "string" ? latestTransaction.settled_date : undefined)
                      ?? (typeof latestTransaction?.expected_date === "string" ? latestTransaction.expected_date : undefined);
                    return (
                      <div className="profile-modal-backdrop" onClick={() => setProfileCall(null)}>
                        <section aria-labelledby="merchant-profile-title" aria-modal="true" className="profile-modal" onClick={(event) => event.stopPropagation()} role="dialog">
                          <div className="profile-modal-heading">
                            <div><p className="section-label">Sales profile</p><h2 id="merchant-profile-title">{profileCall.merchant_name}</h2><p>{profileCall.business_name} · {profileCall.merchant_id}</p></div>
                            <button aria-label="Close merchant profile" className="icon-text-button" onClick={() => setProfileCall(null)} type="button">Close</button>
                          </div>
                          <dl className="profile-modal-details">
                            <div><dt>Location</dt><dd>{merchant?.city ?? profileCall.city ?? "—"}</dd></div>
                            <div><dt>Phone</dt><dd>{merchant?.phone ?? profileCall.phone ?? "—"}</dd></div>
                            <div><dt>Member since</dt><dd>{merchant?.member_since ?? profileCall.member_since ?? "—"}</dd></div>
                            <div><dt>Transactions</dt><dd>{merchant?.total_transactions ?? profileCall.total_transactions ?? "—"}</dd></div>
                            <div><dt>Account balance</dt><dd>{merchant?.account_balance ?? profileCall.account_balance ?? "—"}</dd></div>
                            <div><dt>Active scenario</dt><dd>{profileCall.scenario_label}</dd></div>
                            <div><dt>Transaction</dt><dd>{txnId ?? "—"}</dd></div>
                            <div><dt>Amount</dt><dd>{txnAmount != null ? `₹${txnAmount.toLocaleString("en-IN")}` : "—"}</dd></div>
                            <div><dt>Transaction date</dt><dd>{txnDate ?? "—"}</dd></div>
                            <div><dt>Next expected date</dt><dd>{merchant?.expected_date ?? profileCall.expected_date ?? "—"}</dd></div>
                          </dl>
                          {profileCall.attention_required && <div className="attention-detail"><h3>Attention needed</h3><p>{profileCall.attention_reason || "Review this call with the merchant."}</p>{profileCall.requires_human_approval && <strong>Human approval required before refund action.</strong>}</div>}
                          <div className="profile-modal-actions">
                            {merchant && !merchant.opted_out && (
                              <button className="primary-action" onClick={() => { setProfileCall(null); onCallMerchant(merchant); }} type="button">Start demo call</button>
                            )}
                            <button className="quiet-action" onClick={() => setProfileCall(null)} type="button">Close profile</button>
                          </div>
                        </section>
                      </div>
                    );
                  })()}
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
