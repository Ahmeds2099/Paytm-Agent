import { useState } from "react";
import type { ReactNode } from "react";
import type { DemoMerchant } from "@/lib/voice/types";

type Props = {
  merchant: DemoMerchant | null;
  language: string;
  connected: boolean;
  connecting: boolean;
  onEndCall(): void;
  onEscalate(): void;
  children: ReactNode;
};

export default function CallView({
  merchant,
  language,
  connected,
  connecting,
  onEndCall,
  onEscalate,
  children,
}: Props) {
  const [profileExpanded, setProfileExpanded] = useState(false);

  return (
    <div className="call-layout">
      <aside className="merchant-profile-panel" aria-label="Merchant profile">
        <div className="merchant-profile-topline">
          <div className="call-status-line">
            <span className="status-dot" data-status={connected ? "ready" : connecting ? "connecting" : "idle"} />
            <span>{connecting ? "Connecting outbound call" : connected ? "Outbound call in progress" : "Call disconnected"}</span>
          </div>
          <button
            aria-controls="merchant-profile-content"
            aria-expanded={profileExpanded}
            className="profile-collapse-button"
            onClick={() => setProfileExpanded((expanded) => !expanded)}
            type="button"
          >
            {profileExpanded ? "Collapse profile" : "Expand profile"}
          </button>
        </div>
        {!profileExpanded && (
          <div className="merchant-profile-summary">
            <span className="merchant-profile-summary-avatar" aria-hidden="true">{merchant?.avatar ?? "💬"}</span>
            <span>
              <strong>{merchant?.name ?? "Paytm Merchant Support"}</strong>
              <small>{merchant?.business_name ?? "General assistance · no demo scenario"}</small>
            </span>
          </div>
        )}
        {profileExpanded && (
          <div id="merchant-profile-content">
            <div className="merchant-profile-heading">
              <span className="merchant-profile-avatar">
                {merchant?.avatar ?? "💬"}
              </span>
              <h1>{merchant?.name ?? "Paytm Merchant Support"}</h1>
              <p>{merchant?.business_name ?? "General assistance · no demo scenario"}</p>
            </div>
            {merchant ? (
              <>
                <dl className="merchant-profile-details">
                  <div><dt>Location</dt><dd>{merchant.city}</dd></div>
                  <div><dt>Phone</dt><dd>{merchant.phone}</dd></div>
                  <div><dt>Language</dt><dd>{language || "Chosen live during call"}</dd></div>
                </dl>
                <section className="merchant-account" aria-labelledby="merchant-account-title">
                  <h2 id="merchant-account-title">Account information</h2>
                  <dl>
                    <div><dt>Merchant ID</dt><dd>{merchant.merchant_id}</dd></div>
                    <div><dt>Member since</dt><dd>{merchant.member_since}</dd></div>
                    <div><dt>Transactions</dt><dd>{merchant.total_transactions.toLocaleString()}</dd></div>
                    <div><dt>Account balance</dt><dd>{merchant.account_balance}</dd></div>
                  </dl>
                </section>
                <section className="merchant-issue" aria-labelledby="merchant-issue-title">
                  <h2 id="merchant-issue-title">Active demo scenario</h2>
                  <strong>{merchant.scenario_label}</strong>
                  <p>{merchant.scenario_description}</p>
                  {merchant.transaction_id && <p>Transaction: {merchant.transaction_id} · {merchant.transaction_status}</p>}
                  {merchant.transaction_amount != null && <p>Amount: ₹{merchant.transaction_amount.toLocaleString("en-IN")}</p>}
                  {merchant.transaction_date && <p>Transaction date: {merchant.transaction_date}</p>}
                  {merchant.expected_date && <p>Expected date: {merchant.expected_date}</p>}
                  {merchant.device_id && <p>Device: {merchant.device_id}</p>}
                  {merchant.scenario_id === "opt_out" && (
                    <p>Outbound promotional loan offer. Respect the request to remove this number from future demo offers.</p>
                  )}
                </section>
              </>
            ) : (
              <section className="merchant-issue">
                <h2>General call</h2>
                <p>Ask what happened. For transaction lookups, the agent will request a transaction ID before checking it.</p>
              </section>
            )}
          </div>
        )}
        <div className="merchant-call-actions">
          <button className="quiet-action" disabled={!connected} onClick={onEscalate} type="button">
            Request human follow-up
          </button>
          <button className="danger-call-action" disabled={!connected && !connecting} onClick={onEndCall} type="button">
            End call
          </button>
        </div>
      </aside>
      <div className="call-content">{children}</div>
    </div>
  );
}
