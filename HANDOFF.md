# Paytm Voice Teammate — Agent Handoff
**Last updated:** 2026-10-30  
**Latest commit:** `d2bcf48`  
**Tests:** 157 / 157 passing  
**TypeScript:** `tsc --noEmit` clean

---

## 1. Project in one paragraph

Paytm Voice Teammate is an outbound voice AI that calls merchant shopkeepers, asks which language they prefer (English / Hindi / Kannada), and then answers questions about their Paytm account using live tool calls to a mock (soon real) Paytm API. It runs as a FastAPI backend + Next.js frontend over a WebSocket audio pipeline: browser mic → PCM stream → Sarvam/Deepgram STT → intent classifier → Paytm tool OR Groq LLM → Sarvam/Cartesia TTS → browser speaker.

---

## 2. How to run (all three terminals)

```powershell
# Terminal 1 — Mock Paytm API (port 8200)
cd G:\Coding\Projects\paytm-voice-teammate\backend
.\.venv\Scripts\Activate.ps1
cd ..
python -m mock_paytm

# Terminal 2 — Backend (port 8100)
cd G:\Coding\Projects\paytm-voice-teammate\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8100 --log-level warning

# Terminal 3 — Frontend (port 3100)
cd G:\Coding\Projects\paytm-voice-teammate\frontend
npm run dev
```

Then open http://localhost:3100, click Connect, and speak.

**Health check:** GET http://127.0.0.1:8100/system/status

---

## 3. Run the tests

```powershell
cd G:\Coding\Projects\paytm-voice-teammate\backend
.\.venv\Scripts\Activate.ps1
python -m unittest discover -s tests
```

Expected: `Ran 157 tests in ~1.2s OK`

Warnings that are expected and NOT failures:
- `[audit_log] write failed: disk full` — audit test intentionally simulates disk failure
- `[paytm_tools] settlement_status failed: timeout` — timeout error path test
- `[paytm_tools] translation to hi-IN failed, using English` — translation fallback test
- ffmpeg not installed / Sarvam non-fatal — irrelevant to tests

---

## 4. Repository layout

```
paytm-voice-teammate/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py          ← All settings (env vars + defaults)
│   │   │   ├── prompts.py         ← System prompt + build_voice_prompt(language)
│   │   │   └── qdrant.py          ← QdrantClient singleton
│   │   ├── services/
│   │   │   ├── paytm_tools.py     ← Phase 4: 4 tools + spoken_summary_for_language()
│   │   │   ├── audit_log.py       ← Phase 4: JSONL audit trail per tool call
│   │   │   ├── intent.py          ← Intent classifier (rule→LLM, 11 labels)
│   │   │   ├── memory_service.py  ← Qdrant vector memory
│   │   │   ├── session_repository.py ← Upstash Redis REST persistence
│   │   │   ├── conversation_service.py ← In-process + Redis session history
│   │   │   ├── conversation_manager.py ← Main LLM pipeline (stream_voice)
│   │   │   ├── embedder.py        ← SentenceTransformer embeddings
│   │   │   └── voice/
│   │   │       ├── handlers/audio.py ← WS handler (ALL audio logic lives here)
│   │   │       ├── session.py      ← VoiceSession dataclass
│   │   │       ├── phrases.py      ← Fixed phrases + PHRASES dict
│   │   │       ├── language_gate.py ← Language detection + lock
│   │   │       └── prerender.py    ← PhraseCache (PCM clips)
│   │   └── main.py                ← FastAPI app + startup warmup
│   ├── tests/
│   │   ├── test_phase4.py         ← 19 Phase 4 tests (tools, audit, intent, language)
│   │   ├── test_language_selection.py ← 27 language gate tests
│   │   └── test_vf031.py          ← Interruption/async tests
│   └── .env                       ← Git-ignored; see .env.example
├── mock_paytm/
│   ├── __main__.py                ← FastAPI app on port 8200
│   ├── models.py                  ← Pydantic response types
│   ├── seed_data.py               ← Deterministic fixtures + idempotent refund store
│   └── routes/
│       ├── qr.py, settlement.py, refund.py, soundbox.py
├── frontend/
│   ├── app/page.tsx               ← Main UI page
│   ├── hooks/usevoice.ts          ← All voice state (toolCallLog, escalation, etc.)
│   ├── lib/voice/
│   │   ├── types.ts               ← VoiceState, ToolCall, EscalationEvent, etc.
│   │   └── websocket.ts           ← VoiceSocket class (all WS message handling)
│   └── components/
│       └── dashboard/architecturedashboard.tsx
├── BUILD_LOG.md                   ← Detailed change log per phase
├── context.md                     ← Session-by-session change notes
└── HANDOFF.md                     ← This file
```

---

## 5. Key config variables (backend/.env)

| Variable | Purpose | Current status |
|---|---|---|
| `GROQ_API_KEY` | LLM (Llama 3.3 70B) + intent classification | ✅ Set |
| `SARVAM_API_KEY` | STT + TTS (primary) | ✅ Set |
| `DEEPGRAM_API_KEY` | STT fallback | ✅ Set |
| `CARTESIA_API_KEY` | TTS alternative | ✅ Set |
| `QDRANT_URL` / `QDRANT_API_KEY` | Vector memory | ✅ Set |
| `UPSTASH_REDIS_URL` | REST session persistence | ⚠️ URL fails DNS — needs correct Upstash REST URL from owner |
| `UPSTASH_REDIS_TOKEN` | Auth for Upstash | ✅ Set |
| `MOCK_PAYTM_URL` | Paytm tool target | Defaults to `http://127.0.0.1:8200` |
| `VOICE_ENABLE_TOOLS` | Master switch for Phase 4 dispatch | Defaults to `true` |
| `VOICE_MAX_TOKENS` | LLM reply length cap | `200` |
| `SARVAM_STT_SILENCE_MS` | End-of-speech silence threshold | `350` |

---

## 6. Phase completion status

| Phase | Description | Status |
|---|---|---|
| 1 | WebSocket voice pipeline (PCM → STT → LLM → TTS → PCM) | ✅ Complete |
| 2 | Emotion detection, barge-in, interruption recovery | ✅ Complete |
| 3 | Language gate (greeting → detect → lock en-IN/hi-IN/kn-IN) | ✅ Complete |
| 4 | Paytm tool layer (QR, settlement, refund, soundbox + audit) | ✅ Complete |
| 5 | Memory write-back, real Upstash, dedicated tool dashboard panel | 🔲 Next |

---

## 7. Phase 4 — what the agent can now answer

### QR Code ("My QR is not working")
| MID | Status | Spoken response |
|---|---|---|
| MID001 | Active | "Your QR is active. Last scan was ₹500." |
| MID002 | Inactive | "Your QR has an issue: QR code not rendering — contact support." |
| Unknown | Not found | "I couldn't find any QR registered to that ID." |

### Settlements ("When will my payment settle?")
| TXN | Status | Spoken response |
|---|---|---|
| TXN001 | Settled ₹1,200.50 | "Your settlement of ₹1,200 has been completed on [date]. UTR: UTR123456789." |
| TXN002 | Pending ₹750 | "Your settlement of ₹750 is pending, expected on [tomorrow]." |
| TXN003 | On hold ₹300 | "Your settlement of ₹300 is on hold, with no expected date yet." |

### Soundbox ("My soundbox is not working")
| Device | Status | Spoken response |
|---|---|---|
| SB001 | Online | "Your soundbox is online and working normally." |
| SB002 | Offline | "Your soundbox appears to be offline. Check power and WiFi." |
| Unknown | Not found | Error fallback |

### Refunds ("I need a refund")
- TXN001 → already processed, returns existing REF-TXN001-001
- Any new TXN → creates and stores a new refund with status `initiated`

### Escalation intents
- **"I want a human"** → session.escalated=True, speaks phrase in merchant's language, emits `escalation` WS event, amber banner on frontend
- **"Stop calling me"** → session.escalated=True, speaks opt_out phrase
- **Repeated complaint x2** → auto-escalates to human_request

---

## 8. Intent classifier labels

Defined in `backend/app/services/intent.py`:

| Label | Triggers tool? | Notes |
|---|---|---|
| `settlement_query` | ✅ settlement_status | Slot: transaction_id |
| `device_issue` | ✅ soundbox_health | Slot: device_id |
| `qr_code_issue` | ✅ lookup_qr | Slot: merchant_id |
| `refund_request` | ✅ trigger_refund | Slots: transaction_id, amount |
| `human_request` | ❌ escalates | session.escalated=True |
| `opt_out` | ❌ escalates | session.escalated=True |
| `repeat_complaint` | ❌ (2nd time escalates) | session.repeat_complaint_count++ |
| `greeting` | ❌ | Falls through to LLM |
| `out_of_scope` | ❌ | Falls through to LLM |

---

## 9. Session memory architecture

```
Client browser (localStorage: paytm_client_id)
    │ session_init {client_id, document_ids}
    ▼
audio.py session_init handler
    → ConversationService.bind(session_id, client_id)
        → session_repository.load(client_id)
            → Upstash Redis REST GET paytm:session:{client_id}
            → fallback: in-process dict if Redis unavailable
    → loads message history into ConversationService._sessions
    → loads memories into MemoryService (Qdrant)

Each turn:
    user message → ConversationService.add_message(session_id, "user", text)
    assistant reply → ConversationService.add_message(session_id, "assistant", text)
    → session_repository.save(client_id, state) → Upstash Redis SET

Memory extraction:
    MemoryExtractor.extract(query) → key facts
    → MemoryService.store_memory(fact, client_id) → Qdrant upsert + Redis
```

⚠️ **Upstash is currently degraded** (wrong hostname in .env). Session history survives browser refresh within the same process only. Owner must provide correct Upstash REST URL.

---

## 10. Known open items

| # | Item | Priority |
|---|---|---|
| 1 | Upstash Redis URL incorrect — owner to provide correct REST endpoint | 🔴 High |
| 2 | Phase 5: memory write-back after tool calls | 🟡 Medium |
| 3 | Phase 5: dedicated ArchitectureDashboard tool call panel | 🟡 Medium |
| 4 | Phase 5: Groq-based slot extraction for txn_id/device_id from transcript | 🟡 Medium |
| 5 | `VOICE_ENABLE_EMOTION=false` in .env — emotion disabled but code intact | 🟢 Low |
| 6 | Qdrant UserWarning on startup (version check) — non-breaking | 🟢 Low |

---

## 11. Owner-flagged UI items (still open)

1. **Landing orb "V" letter** — `frontend/app/page.tsx:209` — possibly leftover Via branding. Ask before changing.
2. **Lite-mode banner** — `frontend/app/layout.tsx:19` — mentions "Full emotional intelligence". Confirm before editing.

---

## 12. Credentials

- `backend/.env` — git-ignored. Keys: SARVAM, CARTESIA, GROQ, DEEPGRAM, QDRANT, UPSTASH, MOCK_PAYTM_URL
- `.env.example` — documents all keys with empty values; update when adding a new setting
- Frontend uses `NEXT_PUBLIC_API_URL` (defaults to `http://127.0.0.1:8100`) and `NEXT_PUBLIC_DEPLOYMENT_PROFILE=local`

---

## 13. Your first 30 minutes

1. Confirm latest commit is `d2bcf48` (`git log --oneline -3`).
2. Read `context.md` for session-by-session notes, then `BUILD_LOG.md` for detailed decisions.
3. Start all three servers (Section 2 above).
4. Run `python -m unittest discover -s tests` → expect 157 OK.
5. Run `npx tsc --noEmit` in `frontend/` → expect zero errors.
6. Hit `GET /system/status` and check `persistence.status` — if `degraded`, Upstash is not connected (expected until owner provides new URL).
7. Open browser, connect, choose a language, ask "when will my settlement come" → expect tool call response in chosen language.
8. Check `backend/.audit/calls.jsonl` grows with each tool call.
9. Proceed to Phase 5 items in Section 10.

---

## 14. Keeping the log useful

`BUILD_LOG.md` is the contract between agents and the owner. For each work item add a dated section with:
- objective and what the owner asked for (quoted where possible);
- what changed, file by file;
- measurements before/after (latency, test counts);
- exact commands and their results;
- decisions and deviations with reason;
- what remains open.
