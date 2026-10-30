import type { DemoMerchant } from "@/lib/voice/types";

type Props = {
  merchant: DemoMerchant;
  selected?: boolean;
  onSelect(merchant: DemoMerchant): void;
};

export default function MerchantCard({ merchant, selected = false, onSelect }: Props) {
  return (
    <button
      aria-label={`Start demo call with ${merchant.name}: ${merchant.scenario_label}`}
      className={`merchant-card ${selected ? "selected" : ""}`}
      onClick={() => onSelect(merchant)}
      type="button"
      disabled={merchant.opted_out}
    >
      <div className="merchant-card-top">
        <span aria-hidden="true" className="merchant-avatar">{merchant.avatar}</span>
        {merchant.recommended && <span className="merchant-badge">Recommended</span>}
      </div>
      <div className="merchant-card-body">
        <strong>{merchant.name}</strong>
        <small>{merchant.business_name}</small>
        <span>{merchant.scenario_label}</span>
      </div>
      <div className="merchant-card-footer">
        <span>{merchant.city}</span>
        <span>{merchant.opted_out ? "Promotional calls suppressed" : "Start demo call"}</span>
      </div>
    </button>
  );
}
