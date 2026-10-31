"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import AdminDashboard from "@/components/dashboard/admindashboard";
import VoiceOrb from "@/components/voice/voiceorb";
import CallView from "@/components/ui/CallView";
import MerchantCard from "@/components/ui/MerchantCard";
import PaytmLogo from "@/components/ui/PaytmLogo";
import { useVoice } from "@/hooks/usevoice";
import { resolveApiUrl } from "@/lib/env";
import type { ConversationTurn, DemoMerchant, Provenance } from "@/lib/voice/types";

function isDemoMerchant(value: unknown): value is DemoMerchant {
  if (!value || typeof value !== "object") return false;
  const merchant = value as Record<string, unknown>;
  return typeof merchant.merchant_id === "string"
    && typeof merchant.name === "string"
    && typeof merchant.business_name === "string"
    && typeof merchant.city === "string"
    && typeof merchant.phone === "string"
    && typeof merchant.language === "string"
    && typeof merchant.language_display === "string"
    && typeof merchant.avatar === "string"
    && typeof merchant.scenario_id === "string"
    && typeof merchant.scenario_label === "string"
    && typeof merchant.scenario_description === "string"
    && typeof merchant.member_since === "string"
    && typeof merchant.total_transactions === "number"
    && typeof merchant.account_balance === "string"
    && typeof merchant.open_tickets === "number"
    && (merchant.recommended === undefined || typeof merchant.recommended === "boolean")
    && (merchant.opted_out === undefined || typeof merchant.opted_out === "boolean")
    && (merchant.transaction_id === undefined || typeof merchant.transaction_id === "string" || merchant.transaction_id === null)
    && (merchant.device_id === undefined || typeof merchant.device_id === "string" || merchant.device_id === null);
}

const provenanceLabel = (value?: Provenance) => {
  if (value === "document") return "Domain knowledge";
  if (value === "not_in_source") return "Not available in source";
  return "General knowledge";
};

function MerchantChooser({
  merchants,
  selectedMerchantId,
  onSelect,
}: {
  merchants: DemoMerchant[];
  selectedMerchantId?: string;
  onSelect(merchant: DemoMerchant): void;
}) {
  if (!merchants.length) {
    return <div className="empty-state-box">Merchant scenarios are not available right now.</div>;
  }

  return (
    <div className="merchant-grid">
      {merchants.map((merchant) => (
        <MerchantCard
          key={merchant.merchant_id}
          merchant={merchant}
          selected={selectedMerchantId === merchant.merchant_id}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}

function ConversationTimeline({
  turns,
  interim,
}: {
  turns: ConversationTurn[];
  interim: string;
}) {
  const [historyExpanded, setHistoryExpanded] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const hiddenCount = Math.max(0, turns.length - 3);
  const visibleTurns = historyExpanded ? turns : turns.slice(-3);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [turns, interim]);

  return (
    <section className="conversation-panel" aria-labelledby="conversation-title">
      <div className="section-heading-row">
        <div>
          <p className="section-label">Live transcript</p>
          <h2 id="conversation-title">Conversation</h2>
        </div>
      </div>
      <div className="conversation-scroll" aria-live="polite" ref={scrollRef}>
        {hiddenCount > 0 && (
          <button className="history-toggle" onClick={() => setHistoryExpanded((value) => !value)} type="button">
            {historyExpanded ? "Show latest exchange" : `Show earlier conversation (${hiddenCount})`}
          </button>
        )}
        {visibleTurns.map((turn) => (
          <article className="conversation-turn" data-role={turn.role} key={turn.id}>
            <div className="turn-meta">
              <strong>{turn.role === "assistant" ? "Paytm teammate" : "Merchant"}</strong>
              <time>{new Date(turn.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time>
            </div>
            <p>{turn.text || <span className="response-skeleton">Preparing a response</span>}</p>
            {turn.role === "assistant" && turn.text && (
              <footer className="turn-evidence">
                <span className="provenance" data-type={turn.provenance ?? "general"}>{provenanceLabel(turn.provenance)}</span>
                {turn.interrupted && <span className="interrupted-tag">Interrupted</span>}
              </footer>
            )}
          </article>
        ))}
        {interim && (
          <article className="conversation-turn interim-turn" data-role="user">
            <div className="turn-meta"><strong>Merchant</strong><span>Listening</span></div>
            <p>{interim}</p>
          </article>
        )}
        {!turns.length && !interim && (
          <div className="teaching-empty conversation-empty">
            <span className="empty-mark">P</span>
            <strong>Your call transcript will appear here</strong>
            <p>The language gate runs first. Choose English, Hindi, or Kannada during the call.</p>
          </div>
        )}
      </div>
    </section>
  );
}

export default function HomePage() {
  const [entered, setEntered] = useState(false);
  const [workspace, setWorkspace] = useState<"session" | "admin">("session");
  const [merchantPickerOpen, setMerchantPickerOpen] = useState(false);
  const [documentUploadOpen, setDocumentUploadOpen] = useState(false);
  const [knowledgeFile, setKnowledgeFile] = useState<File | null>(null);
  const [merchants, setMerchants] = useState<DemoMerchant[]>([]);
  const [merchantLoadError, setMerchantLoadError] = useState("");
  const [selectedMerchant, setSelectedMerchant] = useState<DemoMerchant | null>(null);
  const apiBase = useMemo(() => resolveApiUrl().replace(/\/$/, ""), []);
  const voice = useVoice();
  const { callOutcome, selectMerchant } = voice;

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${apiBase}/demo/merchants`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Merchant list request failed (${response.status})`);
        return response.json();
      })
      .then((payload: unknown) => {
        if (!Array.isArray(payload) || !payload.every(isDemoMerchant)) {
          throw new Error("Merchant list response was invalid");
        }
        setMerchants(payload);
        setMerchantLoadError("");
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setMerchantLoadError(reason instanceof Error ? reason.message : "Could not load demo merchants.");
      });
    return () => controller.abort();
  }, [apiBase]);

  useEffect(() => {
    if (callOutcome !== "closed:opt_out") return;
    const controller = new AbortController();
    fetch(`${apiBase}/demo/merchants`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Merchant refresh failed (${response.status})`);
        return response.json();
      })
      .then((payload: unknown) => {
        if (!Array.isArray(payload) || !payload.every(isDemoMerchant)) {
          throw new Error("Merchant refresh response was invalid");
        }
        setMerchants(payload);
        const updated = payload.find((merchant) => merchant.merchant_id === selectedMerchant?.merchant_id);
        if (updated) {
          setSelectedMerchant(updated);
          selectMerchant(updated);
        }
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setMerchantLoadError(reason instanceof Error ? reason.message : "Could not refresh merchant opt-out status.");
      });
    return () => controller.abort();
  }, [apiBase, callOutcome, selectedMerchant?.merchant_id, selectMerchant]);

  const latestAssistant = useMemo(
    () => [...voice.conversation].reverse().find((turn) => turn.role === "assistant"),
    [voice.conversation],
  );

  const startVia = () => setMerchantPickerOpen(true);

  const chooseMerchant = (merchant: DemoMerchant) => {
    setSelectedMerchant(merchant);
    voice.selectMerchant(merchant);
    setMerchantPickerOpen(false);
    setWorkspace("session");
    setEntered(true);
    void voice.connect(merchant);
  };

  const returnHome = () => {
    voice.disconnect();
    voice.selectMerchant(null);
    setSelectedMerchant(null);
    setEntered(false);
    setWorkspace("session");
  };

  const startGeneralCall = () => {
    setSelectedMerchant(null);
    voice.selectMerchant(null);
    setWorkspace("session");
    setEntered(true);
    void voice.connect(null);
  };

  const callMerchantFromAdmin = (merchant: DemoMerchant) => {
    setSelectedMerchant(merchant);
    setWorkspace("session");
    setEntered(true);
    voice.switchMerchant(merchant);
  };

  return (
    <main className="app-shell">
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <header className="site-header">
        <button aria-label="Paytm Voice Teammate home" className="brand" onClick={returnHome} type="button">
          <PaytmLogo />
          <span><strong>Voice Teammate</strong><small>Merchant support demo</small></span>
        </button>
        {entered ? (
          <div className="header-actions">
            <div aria-label="Workspace" className="workspace-switch" role="tablist">
              <button aria-selected={workspace === "session"} onClick={() => setWorkspace("session")} role="tab" type="button">Call</button>
              <button aria-selected={workspace === "admin"} onClick={() => setWorkspace("admin")} role="tab" type="button">Admin</button>
            </div>
            {selectedMerchant ? (
              <div className="session-identity">
                <span className="status-dot" data-status={voice.connected ? "ready" : "idle"} />
                <span>Simulating: <strong>{selectedMerchant.name}</strong></span>
              </div>
            ) : workspace !== "session" || voice.systemStatus?.settings?.rag_enabled === false ? null : (
              <button className="source-trigger" onClick={() => setDocumentUploadOpen(true)} type="button">
                <span className="status-dot" data-status={voice.connected ? "ready" : "idle"} />
                Upload document
              </button>
            )}
          </div>
        ) : (
          <div className="header-proof"><span className="status-dot" data-status={voice.systemStatus ? "ready" : "degraded"} />AI-powered outbound support for merchants</div>
        )}
      </header>

      {merchantPickerOpen && (
        <div className="merchant-modal-backdrop" onClick={() => setMerchantPickerOpen(false)}>
          <section
            aria-labelledby="merchant-picker-title"
            aria-modal="true"
            className="merchant-modal"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
          >
            <div className="merchant-modal-header">
              <div>
                <p className="section-label">Outbound demo call</p>
                <h2 id="merchant-picker-title">Choose a merchant to call</h2>
                <p>The scenario provides account context. The merchant chooses a language live on the call.</p>
              </div>
              <button aria-label="Close merchant picker" className="icon-text-button" onClick={() => setMerchantPickerOpen(false)} type="button">Close</button>
            </div>
            {merchantLoadError && <div className="inline-error" role="alert">{merchantLoadError}</div>}
            <MerchantChooser
              merchants={merchants}
              selectedMerchantId={selectedMerchant?.merchant_id}
              onSelect={chooseMerchant}
            />
            <p className="recommended-note">Lakshmi is recommended for the refund demo. No persona language is preselected.</p>
          </section>
        </div>
      )}

      {documentUploadOpen && (
        <div className="merchant-modal-backdrop" onClick={() => setDocumentUploadOpen(false)}>
          <section
            aria-labelledby="document-upload-title"
            aria-modal="true"
            className="document-upload-modal"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
          >
            <div className="merchant-modal-header">
              <div>
                <p className="section-label">General merchant call</p>
                <h2 id="document-upload-title">Upload a support document</h2>
                <p>Upload a PDF, CSV, or JSON file to ground this call with the knowledge source.</p>
              </div>
              <button aria-label="Close document upload" className="icon-text-button" onClick={() => setDocumentUploadOpen(false)} type="button">Close</button>
            </div>
            {voice.activeDocument && (
              <p className="active-knowledge">Active source: <strong>{voice.activeDocument.filename}</strong> · {voice.activeDocument.chunks} indexed chunks</p>
            )}
            <label className="knowledge-upload document-upload-picker">
              <span>Browse files</span>
              <input accept=".pdf,.csv,.json" onChange={(event) => setKnowledgeFile(event.target.files?.[0] ?? null)} type="file" />
            </label>
            {knowledgeFile && <p className="active-knowledge">Selected: <strong>{knowledgeFile.name}</strong></p>}
            <div className="document-upload-actions">
              <button
                className="primary-action compact"
                disabled={!knowledgeFile || voice.uploading}
                onClick={() => {
                  if (!knowledgeFile) return;
                  void voice.uploadDocument(knowledgeFile);
                  setKnowledgeFile(null);
                }}
                type="button"
              >
                {voice.uploading ? "Uploading…" : "Upload and index"}
              </button>
              <button className="quiet-action" disabled={voice.uploading} onClick={() => setDocumentUploadOpen(false)} type="button">Done</button>
            </div>
            {voice.uploadError && <p className="inline-error" role="alert">{voice.uploadError}</p>}
          </section>
        </div>
      )}

      {!entered ? (
        <div className="landing-view" id="main-content">
          <section className="hero-copy">
            <p className="section-label">Paytm Voice Teammate</p>
            <h1>Support that speaks<br /><span>your merchant&apos;s language.</span></h1>
            <p className="hero-lede">
              AI-powered outbound support for merchants. Speaks English, Hindi, and Kannada while helping with QR issues, settlements, refunds, and soundbox support.
            </p>
            <div className="hero-actions">
              <button className="primary-action large" onClick={startVia} type="button">
                <span className="button-status-dot" />Start demo call
              </button>
              <button className="quiet-action large" onClick={() => document.getElementById("demo-merchants")?.scrollIntoView({ behavior: "smooth" })} type="button">
                Explore scenarios
              </button>
            </div>
            <p className="no-source-note">Every demo starts with the live language gate. No language is preloaded.</p>
          </section>

          <section aria-label="Paytm voice agent" className="hero-orb">
            <div aria-hidden="true" className="landing-orb"><span className="landing-orb-letter">P</span></div>
            <div className="hero-status"><span>Instant transcription</span><span>3 languages</span><span>Merchant support</span></div>
          </section>

          <section aria-label="Paytm agent features" className="landing-proof">
            <div><strong>QR support</strong><p>Check merchant QR status and create a support ticket when needed.</p></div>
            <div><strong>Settlement queries</strong><p>Explain pending payments and recognize when an issue needs escalation.</p></div>
            <div><strong>Soundbox and refunds</strong><p>Troubleshoot devices, request human-approved refund follow-up, or honor an opt-out request.</p></div>
          </section>

          <section className="demo-section" id="demo-merchants">
            <div className="demo-intro">
              <p className="section-label">Merchant scenarios</p>
              <h2>Choose a merchant to call.</h2>
              <p>Each card opens the persona picker. Lakshmi&apos;s refund flow is the recommended demo starting point.</p>
              <div className="general-mode-entry">
                <strong>Test without a persona</strong>
                <p>Ask a merchant-support question without loading one of the scripted scenarios.</p>
                <button className="quiet-action" onClick={startGeneralCall} type="button">Start general call</button>
              </div>
            </div>
            {merchantLoadError && <div className="inline-error" role="alert">{merchantLoadError}</div>}
            <MerchantChooser
              merchants={merchants}
              selectedMerchantId={selectedMerchant?.merchant_id}
              onSelect={() => setMerchantPickerOpen(true)}
            />
          </section>
        </div>
      ) : (
        <div className="workspace-view" id="main-content">
          {workspace === "admin" ? (
            <AdminDashboard apiBase={apiBase} onCallMerchant={callMerchantFromAdmin} />
          ) : (
            <CallView
              connected={voice.connected}
              connecting={voice.connecting}
              language={voice.callLanguage.locked ? voice.callLanguage.display : ""}
              merchant={selectedMerchant}
              onEndCall={voice.disconnect}
              onEscalate={voice.requestEscalation}
            >
              <section className="session-main">
                <VoiceOrb
                  connected={voice.connected}
                  connecting={voice.connecting}
                  listening={voice.listening}
                  onConnect={() => void voice.connect(selectedMerchant)}
                  onDisconnect={voice.disconnect}
                  onStartListening={() => void voice.startListening()}
                  onStopListening={voice.stopListening}
                  state={voice.voiceState}
                />
                <div className="live-answer" aria-live="polite">
                  <p className="section-label">Paytm teammate</p>
                  <p>{voice.assistantResponse || latestAssistant?.text || "The call will begin with a language choice."}</p>
                </div>
                <div className="session-signals">
                  <div><span className="status-dot" data-status={voice.connected ? "ready" : "idle"} /><span>Connection</span><strong>{voice.connected ? "Live" : "Offline"}</strong></div>
                  <div><span className="status-dot" data-status={voice.callLanguage.locked ? "ready" : "degraded"} /><span>Language</span><strong>{voice.callLanguage.display}</strong></div>
                  <div><span className="status-dot" data-status={voice.sttProvider === "deepgram" ? "ready" : "degraded"} /><span>Transcription</span><strong>{voice.sttProvider}</strong></div>
                  <div><span className="status-dot" data-status={selectedMerchant ? "ready" : "idle"} /><span>Merchant</span><strong>{selectedMerchant ? `${selectedMerchant.name} · ${selectedMerchant.merchant_id}` : "No persona"}</strong></div>
                </div>
                <div className="tts-provider-row">
                  <label htmlFor="tts-provider">Speech output</label>
                  <select
                    disabled={voice.ttsUpdating || !voice.systemStatus}
                    id="tts-provider"
                    onChange={(event) => {
                      const provider = event.target.value;
                      if (provider === "cartesia" || provider === "sarvam") {
                        void voice.updateSystemSettings({ tts_provider: provider });
                      }
                    }}
                    value={voice.systemStatus?.settings?.tts_provider ?? "cartesia"}
                  >
                    <option value="cartesia">Cartesia</option>
                    <option value="sarvam">Sarvam</option>
                  </select>
                  <span>{voice.ttsUpdating ? "Switching…" : "Applies to the next speech segment"}</span>
                </div>
                {voice.toolCallLog.length > 0 && (
                  <section className="tool-call-panel" aria-label="Recent tool calls">
                    <p className="section-label">Tool calls</p>
                    {voice.toolCallLog.slice(0, 5).map((call, index) => (
                      <div className="tool-call-row" key={`${call.tool}-${call.ts}-${index}`}>
                        <span className="status-dot" data-status={call.status === "ok" ? "ready" : "degraded"} />
                        <strong>{call.tool}</strong><span>{call.status}</span><small>{call.latency_ms} ms</small>
                      </div>
                    ))}
                  </section>
                )}
              </section>
              <ConversationTimeline interim={voice.interimTranscript} turns={voice.conversation} />
              {(voice.voiceError || voice.systemError) && (
                <div className="error-banner" role="alert">
                  <div><strong>The voice session needs attention</strong><p>{voice.voiceError || voice.systemError}</p></div>
                  <div className="error-actions">
                    <button className="quiet-action" onClick={() => void voice.checkSystem()} type="button">Check again</button>
                    <button aria-label="Dismiss error" className="close-error" onClick={() => { voice.dismissVoiceError(); voice.dismissSystemError(); }} type="button">×</button>
                  </div>
                </div>
              )}
              {voice.fallbackRequired && (
                <section className="fallback-banner" aria-labelledby="fallback-title">
                  <div><p className="section-label">Transcription fallback</p><h2 id="fallback-title">Continue with the local model?</h2><p>{voice.fallbackMessage}</p></div>
                  <div>
                    <button className="primary-action compact" onClick={() => voice.chooseWhisperFallback("continue")} type="button">Continue with Whisper</button>
                    <button className="quiet-action" onClick={() => voice.chooseWhisperFallback("stop")} type="button">Stop and check</button>
                  </div>
                </section>
              )}
              {voice.escalation && (
                <div className="escalation-banner" role="status">
                  <strong>Human follow-up requested</strong>
                  <span>{voice.escalation.reason === "merchant_requested_human" ? "The merchant asked to speak with a senior colleague." : "This call has been flagged for human follow-up."}</span>
                </div>
              )}
            </CallView>
          )}
        </div>
      )}
    </main>
  );
}
