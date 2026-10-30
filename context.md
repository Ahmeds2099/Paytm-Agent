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

---

## Session 2026-10-30 (evening) — Language Fixes, Greeting, Memory Debug

**Commits:** d2bcf48
**Tests:** 157/157 PASS (was 152, +5 new tests)
**TypeScript:** clean

### Changes made

#### 1. Greeting phrase updated (phrases.py)
- Old: "Would you be comfortable in English, Hindi or Kannada?"
- New: "Hello and welcome to Paytm. Would you be comfortable in English, Hindi or Kannada?"
- Cleared .cache/voice_phrases/* so new clip is rendered on next startup

#### 2. Tool call responses translated into merchant language (paytm_tools.py)
- Added spoken_summary_for_language(result, language, llm) function
- For en-IN: returns English summary, no LLM call
- For hi-IN / kn-IN: calls llm.complete_json() with JSON schema {"translation": "..."}
- On LLM failure / None: falls back to English silently with WARNING log
- audio.py _dispatch_intent now calls spoken_summary_for_language instead of spoken_summary

#### 3. Resume + false-interruption prefixes now language-aware (audio.py)
- Removed RESUME_PREFIX = "Returning to that thought - " (was always English)
- Removed FALSE_INTERRUPTION_RESUME_PREFIX = "I didn't catch that..." (was always English)
- Added _RESUME_PREFIX dict: hi-IN, kn-IN, en-IN translations
- Added _FALSE_RESUME_PREFIX dict: matching translations
- Added helper functions: _resume_prefix(lang), _false_resume_prefix(lang)
- _schedule_resume() default prefix now reads from _resume_prefix(session.effective_language)
- Interruption watchdog now calls _false_resume_prefix(session.effective_language)

#### 4. Upstash Redis URL bug fixed (.env)
- Was: UPSTASH_REDIS_URL= https://concise-tapir-162853.upstash.io (leading space)
- Fixed: UPSTASH_REDIS_URL=https://concise-tapir-162853.upstash.io (no space)
- BUT: hostname still fails DNS (getaddrinfo failed). Owner needs to provide correct Upstash REST URL.
- Current behavior: in-process dict fallback (session history lives within process only)

#### 5. Tests updated
- test_language_selection.py: added test_greeting_has_paytm_welcome
- test_phase4.py: +4 tests for spoken_summary_for_language:
  - test_english_passthrough_no_translation
  - test_no_llm_falls_back_to_english
  - test_hindi_translation_called_with_llm
  - test_translation_failure_returns_english
- BUILD_LOG.md and HANDOFF.md fully updated

### What the mock data tells merchants

QR: MID001=active/500, MID002=inactive/error
Settlement: TXN001=settled 1200.50, TXN002=pending 750, TXN003=on_hold 300
Soundbox: SB001=online, SB002=offline/error
Refund: TXN001=already processed; others create new refund

### Next steps (Phase 5)

1. Owner provides correct Upstash REST URL → Redis persistence restored
2. Memory write-back: after tool calls, store result summary in MemoryService
3. Phase 5 frontend: dedicated tool call panel in ArchitectureDashboard
4. Groq-based slot extraction for txn_id/device_id from transcript
5. End-to-end probe: extend language_gate_probe.py with settlement/soundbox scenarios
6. README.md creation for the repository
