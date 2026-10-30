# Context — Paytm Voice Teammate

Project change log and session notes. Read this at the start of every new session.

---

## Session 2026-10-30 — Three owner-requested fixes (pre-Phase 4)

**Agent:** Antigravity / Claude Sonnet 4.6 (Thinking)
**Starting commit:** `24b3ae7`
**Scope:** Implement the three fixes from HANDOFF.md section 10 before starting Phase 4.

---

### Fix 10.1 — Replace trilingual greeting with one English line

**Why:** The old greeting played three languages (~18 s total) before any interaction could happen.
The owner asked for a single natural English prompt.

**Files changed:**
- backend/app/services/voice/phrases.py
  - PHRASES["greeting"]: reduced from 3 languages to en-IN only:
    "Would you be comfortable in English, Hindi or Kannada?"
  - GREETING_ORDER: changed from ("hi-IN", "kn-IN", "en-IN") to ("en-IN",)
  - Docstring updated; retry phrases left trilingual per HANDOFF spec
- backend/tests/test_language_selection.py
  - Updated 3 stale tests to match single English greeting
  - Added test_retry_remains_trilingual
  - required_clips test now expects 1 clip not 3
- backend/.cache/voice_phrases/* -- deleted, will re-render on restart

**Accepted deviations recorded:**
- Recording notice intentionally dropped (owner explicit choice)
- Expected warm count after re-render: 17/17 (was 19/19)

---

### Fix 10.2 — Remove emotion from frontend UI, show knowledge

**Files changed:**
- frontend/app/page.tsx
  - Removed Emotion row from session-signals
  - Replaced "Adapt to the human signal" card with "Ground answers in your documents"
  - Knowledge row kept unchanged

**Verification:** npx tsc --noEmit clean.

---

### Fix 10.3 — Latency improvements

**Files changed:**
- backend/app/main.py
  - Added _groq_warmup_sync() via asyncio.to_thread at startup
  - Eliminates ~7s cold-start penalty on first merchant turn
- backend/app/core/config.py
  - SARVAM_STT_SILENCE_MS: 500 -> 350 (shorter end-of-speech wait)
  - VOICE_MAX_TOKENS: 320 -> 200 (shorter replies, keep reasoning_effort=low)

**Baseline (Phase 2):** first token 1.55-6.27s, first audio 1.86-6.86s, turn complete 2.95-7.98s
**Expected win:** greeting 18s -> ~4s (biggest), STT ~150ms faster, replies end sooner

---

### Test results

- python -m unittest discover -s tests -> 133/133 PASS
- npx tsc --noEmit -> clean

---

## Next Steps — Phase 4: Paytm Agent + Tools

See PHASE4_PLAN.md created this session for the full implementation plan.
Phase 4 must not start until owner gives go-ahead.
Key items: state machine, mock Paytm API on 8200, idempotent tools, intent wired into voice,
audit trail, escalation, memory integration, dashboard updates.

---

## Session 2026-10-30 (continued) — Phase 4: Paytm Agent + Tools

**Commit:** `82a324d`
**Tests:** 152/152 PASS (was 133, +19 new Phase 4 tests)
**TypeScript:** tsc --noEmit clean

---

### Step 1 — Mock Paytm API (mock_paytm/ on port 8200)

**Files created:**
- mock_paytm/__main__.py   FastAPI app, CORS for 127.0.0.1:8100
- mock_paytm/models.py     Pydantic response models
- mock_paytm/seed_data.py  Deterministic in-memory fixtures; idempotent refund store
- mock_paytm/routes/qr.py         GET /qr/{merchant_id}
- mock_paytm/routes/settlement.py GET /settlement/{txn_id}
- mock_paytm/routes/refund.py     POST /refund (idempotent by txn_id)
- mock_paytm/routes/soundbox.py   GET /soundbox/{device_id}
- mock_paytm/__init__.py, mock_paytm/routes/__init__.py

Run: python -m mock_paytm (from project root)
Health check: GET http://127.0.0.1:8200/health

---

### Step 2 — Tool layer (backend/app/services/paytm_tools.py)

- 4 tools: lookup_qr, settlement_status, trigger_refund, soundbox_health
- 3s httpx timeout on every call; never raises; returns typed ToolResult
- spoken_summary(): 1-2 sentence human-friendly result, no raw JSON
- config.py additions: MOCK_PAYTM_URL (default 127.0.0.1:8200), AUDIT_LOG_PATH, VOICE_ENABLE_TOOLS

---

### Step 3 — Intent wired into voice path (audio.py)

**Changes to backend/app/services/voice/handlers/audio.py:**
- New imports: classify, extract_slots, lookup_qr, settlement_status, trigger_refund, soundbox_health, spoken_summary, audit_tool_call, time
- New method _dispatch_intent(): called after language lock, before _schedule_response
  - Classifies transcript with classify() (rule -> LLM fallback)
  - Emits pipeline_stage intent event with label/topic/confidence for dashboard
  - Escalation intents (opt_out, human_request, 2x repeat_complaint): sets session.escalated=True, speaks phrase, emits escalation WS event
  - Tool intents: settlement_query->settlement_status, device_issue->soundbox_health, qr_code_issue->lookup_qr, refund_query->trigger_refund
  - Logs tool call to audit log
  - Emits tool_call WS event for dashboard
  - Returns True (handled) or False (fall through to LLM)

**Changes to backend/app/services/voice/session.py:**
- Added: escalated: bool = False
- Added: repeat_complaint_count: int = 0
- Added: last_intent: str | None = None

---

### Step 4 — Audit log (backend/app/services/audit_log.py)

- JSONL file appended per tool call
- Fields: ts, session_id, client_id, intent, tool, args, result_status, result_summary, latency_ms
- Default path: backend/.audit/calls.jsonl (git-ignored)
- Never raises on write failure (logs WARNING only)

---

### Steps 5-7 — Frontend

**types.ts:**
- PipelineStageName extended with "intent"
- New types: ToolCall, EscalationEvent

**websocket.ts:**
- Added onToolCall? and onEscalation? handlers
- Switch cases: tool_call, escalation

**usevoice.ts:**
- Imports: ToolCall, EscalationEvent
- New state: toolCallLog (last 10 calls), escalation (nullable)
- Socket handlers: socket.onToolCall, socket.onEscalation
- Exposed in return: toolCallLog, escalation, dismissEscalation

**page.tsx:**
- Tool call log (last 3) shown in session-signals section
- Escalation banner (yellow) with reason and dismiss button

---

### Test suite (backend/tests/test_phase4.py)

- ToolLayerHappyPathTests: 4 tests (one per tool, happy path)
- ToolLayerErrorPathTests: 3 tests (404, timeout, network error)
- SpokenSummaryTests: 6 tests (all tool types + error/not_found)
- AuditLogTests: 2 tests (writes JSONL, never raises on failure)
- IntentRoutingTests: 4 tests (settlement, human_request, opt_out, repeat_complaint)

Total new tests: 19. Total suite: 152.

---

## Next Steps — Phase 5 (if owner approves)

1. Dashboard: Add dedicated tool call panel and intent timeline to ArchitectureDashboard
2. Memory write-back: After every successful tool call, store result in MemoryService
3. Real slot extraction: Use Groq call for merchant_id/device_id extraction from transcript
4. Phrases: Add opt_out and human_request phrase keys to phrases.py with TTS rendering
5. End-to-end probe: language_gate_probe.py extended with settlement/soundbox scenarios
6. README update: Phase 4 section with architecture diagram and run instructions
