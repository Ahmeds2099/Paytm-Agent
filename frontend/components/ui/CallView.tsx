import type { ReactNode } from "react";
import type { DemoMerchant } from "@/lib/voice/types";

type Props = {
  merchant: DemoMerchant;
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
  return (
    <div className="call-layout">
      <aside className="merchant-profile-panel" aria-label="Merchant profile">
        <div className="call-status-line">
          <span className="status-dot" data-status={connected ? "ready" : connecting ? "connecting" : "idle"} />
          <span>{connecting ? "Connecting outbound call" : connected ? "Outbound call in progress" : "Call disconnected"}</span>
        </div>
        <div className="merchant-profile-heading">
          <span aria-hidden="true" className="merchant-profile-avatar">{merchant.avatar}</span>
          <h1>{merchant.name}</h1>
          <p>{merchant.business_name}</p>
        </div>
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
          {merchant.transaction_id && <p>Transaction: {merchant.transaction_id}</p>}
          {merchant.device_id && <p>Device: {merchant.device_id}</p>}
          {merchant.scenario_id === "opt_out" && (
            <p>Outbound promotional loan offer. Respect the request to remove this number from future demo offers.</p>
          )}
        </section>
        <div className="merchant-call-actions">
          <button className="quiet-action" disabled={!connected} onClick={onEscalate} type="button">
            Flag for human follow-up
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
