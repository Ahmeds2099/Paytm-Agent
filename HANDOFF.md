# Handoff - Paytm Voice Teammate

Written 2026-10-30 at commit `24b3ae7`. This document is a complete handover to
the next agent. It is meant to be read top to bottom once, then used as a map.

---

## 0. Read these first, in this order

1. **The owner's build guide** (the document the owner will give you). It is the
   source of truth for requirements, phases and acceptance criteria.
2. **`BUILD_LOG.md`** in this repo. It contains the full history, the reasoning
   behind every decision, measured numbers, and the Phase 3 section at the end.
   This handoff summarises it; the log has the detail.
3. **This file.** Then look at the code paths named in section 5 before editing
   anything.

If this file and `BUILD_LOG.md` disagree, trust `BUILD_LOG.md` plus the code,
and fix the stale line.

---

## 1. What the project is

A voice teammate for Paytm merchants, built for hackathon Track 3. The agent
calls a merchant and talks about payments, QR codes, settlements, refunds and
soundboxes in **Hindi, Kannada and English**. Speech-to-text is Sarvam AI
streaming, the reply model is Groq `openai/gpt-oss-120b`, text-to-speech is
Cartesia `sonic-3.6`.

The deliverable is a working local demo: a Next.js frontend on port **3100**
and a FastAPI backend on port **8100**, plus live probes that prove the voice
path works without a human listening.

### Repos and isolation (non-negotiable)

| Item | Value |
| --- | --- |
| Working clone | `G:\Coding\Projects\paytm-voice-teammate` |
| Read-only original | `G:\Coding\Projects\Paytm Hackathon` - **never modify** |
| Branch | `master`, **no remote, never push** |
| Frontend | Next.js 16, dev server on **3100** |
| Backend | FastAPI, `127.0.0.1:8100` |
| Redis key prefix | `paytm:` |
| Qdrant collections | `paytm_memory`, `paytm_policy` |
| Secrets | only `backend/.env` (git-ignored) |

`BUILD_LOG.md` says the frontend is Vite in one older section. It is **Next.js
16**; `frontend/package.json` is correct.

---

## 2. Current state snapshot

Everything below was true at the handoff moment. Verify it, do not assume it.

- Phases **0, 1, 2 and 3** are complete, live-verified and committed.
- Working tree clean. Latest commits:
  - `24b3ae7` docs: record the phase 3 commit hash
  - `fb732e5` phase 3: ask-and-lock language selection at call start
  - `0096908` intent: reconcile taxonomy with brief section 5.3
- Tests: **133 passing** (`python -m unittest discover -s tests`). `BUILD_LOG.md`
  records 132 at the Phase 3 commit; 133 is the last verified count.
- Backend healthy on 8100:
  - `status=running`, `emotion_enabled=false`, `stt=sarvam/saaras:v3-realtime`,
    `tts=sonic-3.6`, `default_language=auto`.
  - `persistence=degraded` because hosted Redis/Qdrant are unreachable from this
    machine. The in-process fallback keeps voice working. **This is not a bug.**
- Phrase cache warm: **19/19** clips in `backend/.cache/voice_phrases`.
- `npx tsc --noEmit` clean, `compileall` clean, `app.main` imports.

### What is actually working end to end

- Sarvam realtime STT in hi/kn/en and auto, with Deepgram then local Whisper as
  fallbacks.
- Telecalling persona, short spoken replies enforced in code.
- 16-label intent classifier matching the brief, with the concrete merchant
  issue in a separate `topic` field. **Intent is not yet wired into the voice
  path** - that is Phase 4 work.
- Ask-and-lock language selection at the start of every call, with retry,
  English fallback, opt-out, human request, and explicit change-of-mind.
- Barge-in during the greeting and during replies.

---

## 3. Non-negotiables

These come from the owner or the brief. Do not silently revert them.

1. **Never modify the original repo.** Work only in the clone. No remote, no
   push.
2. **Isolation stays.** Ports 3100/8100, Redis prefix `paytm:`, Qdrant
   `paytm_memory` / `paytm_policy`.
3. **No "Via" in user-visible text.** The product is Paytm Voice Teammate.
   One suspected leftover is flagged in section 11.
4. **Secrets never printed or committed.** `backend/.env` only.
5. **Reply budget:** aim for 1-3 sentences, allow 4 only when the fourth is a
   question, absolute cap 5. Prefer closing with a localised "would you like to
   know more?".
6. **`reasoning_effort=low` must stay on every Groq call.** gpt-oss is a
   reasoning model and hidden reasoning tokens count against `max_tokens`.
   Without it replies intermittently come back empty or cut in half.
7. **Emotion stays disabled in the backend** (`VOICE_ENABLE_EMOTION=false`).
   The owner now also wants emotion **removed from the frontend UI**. Keep the
   backend module re-enablable unless the owner says otherwise.
8. **Log every significant step in `BUILD_LOG.md`**, including what is done and
   what remains. The owner relies on this to move between agents.
9. **Stop and report after each phase / work item.** Do not run ahead into
   Phase 4 without the owner's go-ahead.

---

## 4. How to run and verify

### Backend

```
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8100 --log-level warning
```

No `--reload`. Restart after code changes. Before restarting, kill **all**
`uvicorn app.main:app` python processes; a stale server causes port-bind errors.
Uvicorn normally shows two python processes, so kill both.

### Frontend

```
cd frontend
npm run dev
```

Open `http://localhost:3100`. Browser microphone access is required for a real
call.

### Health check

```
curl http://127.0.0.1:8100/system/status
```

Expect `status=running`, `emotion=false`, `stt=sarvam`, `tts=sonic-3.6`.

### Checks before every commit

```
cd backend
.venv\Scripts\python.exe -m unittest discover -s tests
.venv\Scripts\python.exe -m compileall -q app tests scripts
.venv\Scripts\python.exe -c "import app.main"

cd ..\frontend
npx tsc --noEmit
```

### Live probes

```
cd backend
.venv\Scripts\python.exe scripts\language_gate_probe.py     # 8 checks, spends STT/TTS credits
.venv\Scripts\python.exe scripts\voice_latency_probe.py en-IN
.venv\Scripts\python.exe scripts\voice_turn_probe.py hi-IN
.venv\Scripts\python.exe scripts\voice_turn_probe.py kn-IN
.venv\Scripts\python.exe scripts\voice_turn_probe.py en-IN
.venv\Scripts\python.exe scripts\intent_eval.py            # spends Groq credits
```

`language_gate_probe.py` is the acceptance probe for Phase 3. It synthesises
each answer with Cartesia and streams it into the microphone socket, so it
exercises the same path as the browser. Last result: **8/8 pass**.

`voice_turn_probe.py` sends a language in `session_init`, which locks the
language and **skips the greeting**. Use `language_gate_probe.py` when you need
the greeting/gate path.

---

## 5. Architecture map

```
backend/
  app/
    main.py                     FastAPI app, startup phrase-cache warm
    core/
      config.py                 every setting/environment variable
      prompts.py                voice persona + build_voice_prompt(language)
    services/
      conversation_manager.py   stream_voice(), speak_only(), TTS streaming
      llm.py                    Groq client, streaming, retries
      intent.py                 rule fast path + model classifier, language aliases
      response_guard.py         VoiceReplyGuard, sentence budget
      voice/
        handlers/audio.py       session init, greeting trigger, gate wiring, replies
        session.py              VoiceSession: language, language_locked, attempts
        language_gate.py        pure gate decisions (lock/retry/default/opt-out/human)
        language.py             language normalisation
        phrases.py              every fixed spoken line + GREETING_ORDER
        prerender.py            WAV strip + PCM disk cache + warm()
        stt_pipeline.py         streaming STT provider chain
        streaming_stt.py        Sarvam realtime client
        deepgram.py             Deepgram fallback
        vad.py, silero.py, energy.py
        response_guard / resume_intent / state / session_store
  scripts/
    language_gate_probe.py      live 8-check acceptance probe
    voice_latency_probe.py      first token / first audio / turn complete
    voice_turn_probe.py         per-language reply probe
    intent_eval.py              intent accuracy, spends credits
  tests/                        unittest suite
  .cache/voice_phrases/         pre-rendered PCM clips (git-ignored)

frontend/
  app/page.tsx                  landing + live call UI
  app/layout.tsx                metadata + lite-mode banner
  app/globals.css
  hooks/usevoice.ts             WebSocket state, events, emotion/language state
  lib/voice/websocket.ts        typed socket events
  lib/voice/recorder.ts         mic capture and PCM frames
  lib/voice/pcm.ts              Float32 conversion
  lib/voice/types.ts            event types
```

---

## 6. What happens on a call now

1. Browser opens `/ws/voice` and sends `session_init` with no language.
2. Backend plays the pre-rendered greeting: one clip each in Hindi, Kannada,
   English (18.0 s total if the merchant stays silent).
3. Until the merchant answers, `session.language` stays `auto`, so Sarvam can
   understand any of the three. Every final transcript goes to the **language
   gate**, not the reply model.
4. A clear language answer locks the language, switches the Sarvam stream, sends
   `language_changed` with `locked: true`, and speaks a confirmation in that
   language. The confirmation invites the first question.
5. After the lock, every turn goes to the normal reply path using
   `session.effective_language` for the prompt and Cartesia.
6. An explicit later request for another language changes it and speaks the
   short "changed" line. Nothing else can move the call off the locked language.
7. Two unclear answers default to English and offer a human colleague.
8. Barge-in interrupts greeting/confirmation/reply in about 100 ms.

Gate logic lives in `app/services/voice/language_gate.py`; the handler wiring is
in `app/services/voice/handlers/audio.py` (`_handle_language_gate`,
`_apply_language`, `_set_session_language`, `_schedule_phrases`).

---

## 7. Phase status

| Phase | Status | Commit | Evidence |
| --- | --- | --- | --- |
| 0 clone + isolate | done | `c6c5529` | fingerprint identical (135 files), ports/prefixes isolated, Nova-3 `keyterm` fixed |
| 1 Sarvam STT, hi/kn/en, TTS | done | `45cdcc9` | 56 tests, live hi/kn/en/auto smoke pass |
| 2 telecalling retune | done | `6b00ed0` | 97 tests, live hi/kn/en replies, latency measured, emotion absent from logs |
| intent reconciliation | done | `0096908` | brief's exact 16 labels, `topic` field, 240-example dataset |
| 3 ask-and-lock language | done | `fb732e5` | 133 tests, live probe 8/8, greeting cache 19/19 |
| 4 Paytm agent + tools | **not started** | - | brief: states, sub-agent delegation, `mock_paytm/` on 8200, idempotent tools, audit, escalation, memory, dashboard |
| 5 hackathon readiness | **not started** | - | brief sections 8 and 9 |

Phase 4 is the next brief phase, but **three owner-requested fixes come first**
(section 10). Do not start Phase 4 until the owner says so.

---

## 8. Decisions taken, and why

1. **Emotion parked, not deleted (backend).** The brief says remove it; the
   owner asked to keep it re-enablable. While `VOICE_ENABLE_EMOTION=false`, no
   model loads and nothing waits on it. Caveat:
   `app/services/emotion/provider.py` still imports `funasr` at module import
   time, so the module is imported (cheap) but the model is never constructed.
2. **Reply length 3 soft / 4 if a question / 5 hard.** The brief says 1-2; the
   owner allowed a little more room. Enforced in `VoiceReplyGuard`.
3. **Intent taxonomy matches the brief exactly.** `intent` is the brief's 16
   labels; merchant-issue detail is in `topic`. Rules handle `opt_out`,
   `human_request`, `ticket_request`, `repeat_complaint`, `callback_request`,
   `language_choice`, `confirmation_yes`, `confirmation_no` in all three
   languages; everything else asks the model for JSON.
4. **One model, low reasoning effort.** `openai/gpt-oss-120b` for replies and
   classification, 12 s timeout, 1 retry, `reasoning_effort=low`.
5. **Language is locked, not auto-detected.** `VOICE_ASK_LANGUAGE=true` and
   `VOICE_LANGUAGE_ON_FAILURE=en-IN`. `auto` is rejected as a fallback because
   it would reintroduce self-switching.
6. **Phrase audio is pre-rendered and cached as raw PCM.** Cartesia returns WAV;
   `strip_wav` keeps the `data` chunk because the browser does
   `new Float32Array(buffer)` and would play a header as noise. Cache key covers
   text + language + model + voice id, so edits re-render automatically.
7. **Greeting order hi -> kn -> en.** Hindi and Kannada first signals both are
   real options; English closes as the fallback. **This is being changed now**
   (section 10).

### Deviations from the brief you should know about

- The greeting currently includes a recording notice. The owner's new
  one-line English greeting (section 10) **drops the intro and the recording
  notice**. That is the owner's explicit choice ("in english thats enough for
  now"); record it as a conscious deviation, do not "fix" it back silently.
- Emotion is disabled rather than deleted (backend). The owner now wants it
  gone from the UI.

---

## 9. Gotchas

- **First Groq call after a restart is cold (~7 s to first token).** Warm turns
  are much faster: 2.95-7.98 s turn completion. Do not read the first
  measurement as a regression.
- **Windows PowerShell mangles non-ASCII** with `Add-Content` and in the
  console. Write Hindi/Kannada text with the editor tool or Python, and verify
  with `repr()` / byte checks rather than trusting console output.
- **Qdrant and Redis are unreachable here.** Standalone scripts that call
  `QdrantService` raise `ResponseHandlingException`. Use the running backend or
  avoid retrieval. `persistence: degraded` is expected.
- **`SARVAM_STT_SILENCE_MS` is 500** (config default and `.env.example`). It
  directly controls how long the agent waits after speech before finalising a
  transcript - a latency lever.
- **`VOICE_MAX_TOKENS` is 320** and is not set in `backend/.env`.
- **`VOICE_ENABLE_TOOLS=true`** internally; the `VIA_ENABLE_TOOLS` name is
  internal and is not user-visible text, so leave it.
- **Voice sessions are keyed by `client_id`.** Probes use their own ids so they
  do not disturb a browser session.
- **Git warns LF -> CRLF on every commit.** `core.autocrlf` noise, not a file
  problem.
- **Phrase cache is content-hashed.** After editing `phrases.py`, simply restart
  the backend; `warm()` renders any missing clip. To force a clean re-render,
  delete `backend/.cache/voice_phrases/*` first. The clip count will drop from
  19 to 17 once the greeting exists only in English.
- **`backend/.env` is the only place secrets exist.** `.env.example` documents
  names with empty values.

---

## 10. Pending work: three owner-requested fixes (do these first)

The owner's exact asks:

> "it still takes a long time to process and also from the frontend remove the
> emotion disabled instead just show knowledge in its place ... see the greeting
> too its like robotic change it to would you be comfortable in english, hindi
> or kannada in english thats enough for now"

Implement in this order. The greeting is the biggest perceived win and is also
part of the latency fix.

### 10.1 Replace the trilingual greeting with one English line

**Target files**

- `backend/app/services/voice/phrases.py`
  - `PHRASES["greeting"]`: keep only `"en-IN"` with the single line
    `"Would you be comfortable in English, Hindi or Kannada?"`.
  - `GREETING_ORDER`: `("en-IN",)`.
  - Update the module docstring (it currently says the greeting is deliberately
    trilingual).
- `backend/app/services/voice/handlers/audio.py`
  - Greeting trigger in `handle_control` -> `session_init` (around line 1767)
    schedules `[("greeting", language) for language in GREETING_ORDER]`. With
    `GREETING_ORDER` reduced this works unchanged - verify it does.
- `backend/tests/test_language_selection.py`
  - Greeting tests assert three clips / three languages. Update to one English
    clip.
- `backend/.cache/voice_phrases/*`
  - Delete and restart so the new clip renders. Expected warm count becomes
    17/17 (greeting loses two languages).

**Notes**

- `retry` stays trilingual on purpose: a merchant who did not answer the first
  question may not have understood English. Do not reduce it.
- `confirm`, `changed`, `default_english`, `opt_out`, `human_request` are
  unchanged.
- Expected greeting audio: roughly 3-4 s (the old English clip was 5.84 s but
  contained two extra sentences).

**Acceptance**

- New call: exactly one English clip, then the gate.
- `language_gate_probe.py` still 8/8 (it exercises greeting, retry, fallback,
  change-of-mind, no-auto-switch).
- Unit tests pass; no stale 19-clip reference in docs.

### 10.2 Remove emotion from the frontend UI, show knowledge in its place

**Target files**

- `frontend/app/page.tsx`
  - Line ~302: delete the **Emotion** row in `session-signals`.
  - Line ~303: the **Knowledge** row already exists; keep it.
  - Line ~217: replace the card
    `<strong>Adapt to the human signal</strong>` /
    "Local emotional cues make explanations calmer, clearer, and better timed."
    with knowledge-oriented copy, e.g.
    `<strong>Ground answers in your documents</strong>` /
    "Add a price list, policy or FAQ and the assistant answers from it."
    **Confirm the exact wording with the owner.**
- `frontend/hooks/usevoice.ts`
  - Emotion state and the `onEmotionUpdate` handler can stay (harmless, backend
    emits nothing while disabled), but nothing should render it. Removing the
    dead state is optional cleanup; do not break the event types.
- `frontend/app/layout.tsx`
  - Line ~19 lite-mode banner says "Full emotional intelligence ...". **Ask the
    owner** whether to reword it (it is only shown when
    `NEXT_PUBLIC_DEPLOYMENT_PROFILE=lite`). The first character is mangled
    (a replacement-character artifact from a PowerShell write); fix that if you
    touch the line.

**Acceptance**

- No "Emotion" text anywhere in the rendered UI. Search the frontend for
  `Emotion` / `emotion` and confirm only non-rendered state remains.
- `npx tsc --noEmit` clean; page renders; Knowledge row still shows the active
  document.

### 10.3 Improve perceived and measured latency

The owner says a call/response "still takes a long time to process". This is
both real and perceived. Fix the perceived part first, then measure.

**Measure first** (warm backend, two runs, note the first run is cold):

```
cd backend
.venv\Scripts\python.exe scripts\voice_latency_probe.py en-IN
.venv\Scripts\python.exe scripts\voice_turn_probe.py en-IN
```

Record: final transcript time, first token, first audio, turn complete. Baseline
from Phase 2 is first token 1.55-6.27 s, first audio 1.86-6.86 s, turn complete
2.95-7.98 s, with the spread being Groq queue time.

**Candidate fixes, in expected impact order**

1. **Greeting 18 s -> ~4 s.** Covered by 10.1. This is the single biggest
   perceived win: the merchant currently waits through three languages before
   anything else can happen.
2. **Pre-warm the first Groq call on startup.** The first call after a restart
   costs ~7 s to first token. A tiny warm-up completion at startup (or on
   `session_init`) removes the cold-start penalty from the first real turn.
3. **Reduce `SARVAM_STT_SILENCE_MS` 500 -> ~350.** Shorter end-of-speech wait.
   Validate against the live probes; too low causes cut-off transcripts,
   especially for Kannada.
4. **Check when TTS actually starts.** `conversation_manager.stream_voice`
   feeds tokens through `VoiceReplyGuard.feed()` and emits a sentence at a time
   via `_sentence_items`, which should start audio on the first sentence. Verify
   there is no buffering in `VoiceHandler._stream_items` / `_emit_stream` or in
   `response_guard` that holds short replies until stream end. If a 2-sentence
   reply waits for `flush()`, emit the first clause/sentence earlier.
5. **Lower `VOICE_MAX_TOKENS` 320 -> ~200.** Shorter replies finish sooner.
   Keep `LLM_REASONING_EFFORT=low`; lowering tokens without it causes empty
   replies.
6. **Confirm intent classification does not run on the voice path.** It should
   not yet (Phase 4 wires it). If it sneaks in, it adds a second model call per
   turn.

Do not add speculative caching or model swaps without measurement. Re-run the
same probes after each change and put before/after numbers in `BUILD_LOG.md`.

**Acceptance**

- Greeting starts instantly from cache and is one English line.
- Measured first audio improves over baseline on a warm backend, with the
  cold-start case no worse.
- No response-guard regressions: replies still 1-3 sentences (4 if a question,
  max 5) and still end with the "would you like to know more?" offer where
  appropriate.

---

## 11. Flagged, needs an owner decision

1. **Landing orb still shows a "V"**:
   `frontend/app/page.tsx:209` ->
   `<span className="landing-orb-letter">V</span>`. That is likely a leftover
   "Via" brand mark and conflicts with the no-"Via" rule if it reads as
   branding. Ask before changing; a "P" or a neutral mark may be wanted.
2. **Lite-mode banner wording** in `frontend/app/layout.tsx:19` mentions "Full
   emotional intelligence" and has a mangled leading character. Reword/remove
   only with owner approval (see 10.2).
3. **Recording notice.** The new one-line greeting drops it. If the brief's
   recording-notice requirement matters for the demo, the owner may want it
   added back to the confirmation instead. Record whichever choice is made.
4. **`intent_eval.py` has not been run** (spends Groq credits). The owner was
   asked to run it. It is optional for the three fixes above.

---

## 12. Credentials and environment

- `backend/.env` holds `SARVAM_API_KEY`, `CARTESIA_API_KEY`, `GROQ_API_KEY` (and
  optionally others). It is git-ignored. Never print or commit it.
- `.env.example` documents every key with empty values; update it when adding a
  setting.
- `frontend` uses `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_DEPLOYMENT_PROFILE`.
  For local work the profile is `local`.

---

## 13. Your first 30 minutes

1. Read the owner's guide, then `BUILD_LOG.md`, then this file.
2. Confirm the tree is clean (`git status`) and the latest commit is `24b3ae7`.
3. Start the backend and frontend; hit `/system/status`; confirm warm 19/19.
4. Run the test suite once to establish your own baseline.
5. Open the three target areas so you know them before editing:
   `phrases.py`, `handlers/audio.py` (greeting + `_schedule_phrases`),
   `frontend/app/page.tsx` (lines 209/217/302/303), and
   `conversation_manager.stream_voice`.
6. Measure latency once with the probes; write the numbers down.
7. Confirm the open UI wording questions with the owner (sections 10.2 and 11).
8. Implement in order: greeting -> emotion UI -> latency. After each: tests,
   live probe, `BUILD_LOG.md` entry, commit. Stop and report.

---

## 14. Keeping the log useful

`BUILD_LOG.md` is the contract between agents and the owner. For each work item
add a dated section with:

- objective and what the owner asked for, quoted where possible;
- what changed, file by file;
- measurements before/after (latency, clip durations, test counts);
- exact commands and their result;
- decisions and deviations, with the reason;
- what remains.

Never edit the original repo's log. Only this clone's.
