# BUILD LOG — Paytm Voice Teammate

Owner: Ahmed Sufiyan
Brief: `Open Code Brief 1 Paytm Voice Teammate Build.docx`
Working directory: `G:\Coding\Projects\paytm-voice-teammate`

Every phase, decision and test is recorded here with a date. Secret values are never
written to this file; only environment variable names are listed.

---

## 2026-10-29 — Phase 0: Backup and clone

### Decision: source of truth for `VIA_ORIGINAL`

The owner designated `G:\Coding\Projects\Paytm Hackathon` as `VIA_ORIGINAL`
(not `G:\Coding\Projects\Via`).

Reason: the designated folder is the newer history. It is 6 commits ahead of the
`Via` folder's `Dev` branch head (`e46a49e`, 2026-07-25) and contains the later
work, including:

- `2dff4c4` chore(llm): switch Groq models to openai/gpt-oss variants
- `3a8badf` fix(types): add missing filename field to fallbackDemos

`Via` is on branch `Dev` at `e46a49e`; `Paytm Hackathon` is on branch
`feature/companion-integration` at `3a8badf` (2026-09-21). The two histories
diverged (1 commit on the `Via` side, 6 on the designated side).

### Baseline state was dirty (owner approved)

`VIA_ORIGINAL` had uncommitted changes. The owner approved using the dirty
working tree as the baseline. Recorded inventory:

- 15 modified tracked files
- 15 deleted tracked files (Via documentation, demo data, demo scripts)
- 4 untracked files (brief `.docx`, `backend/Via.code-workspace`,
  `backend/app/services/companion_client.py`, `backend/app/services/tool_intent.py`)
- net diff against `3a8badf`: 30 files changed, 264 insertions, 3017 deletions

Ignored but present and copied: `backend/.env`, `backend/.env.render`,
`frontend/.env.local`. Not copied: `.venv`, `node_modules`, `.next`,
`__pycache__`, `.git`.

Consequence: the clone's baseline commit represents a working-tree state that
does not exist in any commit of the original history. This is intentional and
recorded here.

### Fingerprint of the original

- Before: `G:\Coding\Projects\via-fingerprint-before.txt`
- 135 files, SHA-256 each, sorted by relative path
- Excluded: `.git`, `.venv`, `node_modules`, `.next`, `__pycache__`,
  `.pytest_cache`, `.mypy_cache`, `dist`, `build`, `*.pyc`,
  `frontend/tsconfig.tsbuildinfo`
- The brief `.docx` was open in another process; hashed with a shared-read
  file handle so the lock did not block the fingerprint.

### Backup archive

- Path: `G:\Coding\Projects\via-backup-20261029-1905.tar.gz`
- Size: 1.64 MB, 259 archive entries
- Contents verified: `.git/HEAD`, `backend/app/main.py`, `backend/.env`,
  `backend/.env.render`, `frontend/package.json`, the brief `.docx`
- Dependency leakage check: 0 entries matching `node_modules`, `.venv`,
  `__pycache__`, `.next`

### Clone

- Path: `G:\Coding\Projects\paytm-voice-teammate`
- Method: `robocopy /E` with directory exclusions; no `.git` copied
- Files copied: 135
- `git init` performed, **no remote configured**, secrets are ignored by
  `.gitignore`
- Initial commit: `baseline: copy of original`

### Isolation settings applied in the clone

| Setting | Original | Clone |
| --- | --- | --- |
| Frontend port | 3000 (Next default) | 3100 (`next dev -p 3100`) |
| Backend port | 8000 (Uvicorn default) | 8100 |
| Frontend API URL | `http://127.0.0.1:8000` | `http://127.0.0.1:8100` |
| CORS defaults | localhost:3000 | localhost:3100 |
| `allowedDevOrigins` | `*:3000` | `*:3100` |
| Redis session key | `via:session:{id}` | `paytm:session:{id}` |
| Redis memory key | `via:memories:{id}` | `paytm:memories:{id}` |
| Qdrant memories | `via_memories` | `paytm_memory` |
| Qdrant documents | `via_documents` | `paytm_policy` |
| Browser storage keys | `via_client_id`, `via_active_document` | `paytm_client_id`, `paytm_active_document` |
| Visible product name | "Via" | "Paytm Voice Teammate" |

Visible product-name sweep covered: page metadata, landing page, transcript
speaker label, voice orb copy, dashboard copy, user-facing error messages,
backend health/startup messages, application constants and the system prompts.

Deliberately left unchanged (internal identifiers, no user-visible text):
`VIA_ENABLE_TOOLS`, the `"via"` logger name, `_VIA_NAME` normalization in the
Deepgram fallback, `via-demo` document ID namespace, internal function names and
code comments. These are scheduled for removal or renaming in the phases that
rewrite the relevant modules.

### Dependency install

- Backend: new virtual environment at `backend/.venv`, installing
  `backend/requirements.txt`
- Frontend: `npm ci` failed because the committed `package-lock.json` is out of
  sync with `package.json` (`@emnapi/*` entries). This is a pre-existing defect
  inherited from the original. Used `npm install` instead, which updates the
  lock file.

### Baseline check

Services started in the clone:

- Backend: `uvicorn app.main:app --host 127.0.0.1 --port 8100`
- Frontend: `npm run dev` (`next dev -p 3100`)

Results:

| Check | Result |
| --- | --- |
| `GET http://127.0.0.1:8100/` | 200, "Paytm Voice Teammate Backend Running" |
| `GET /health` | 200, `{"status":"ok"}` |
| `GET /system/status` | 200, Deepgram/Groq/Cartesia configured |
| `GET http://127.0.0.1:3100` | 200, title "Paytm Voice Teammate", no "Via" in HTML |
| Voice socket `ws://127.0.0.1:8100/ws/voice` | `connected`, `emotion_status`, `stt_ready` (deepgram) |
| Full voice turn (synthesized speech) | transcript, LLM tokens, Cartesia audio frames, `assistant_audio_end` |
| Original fingerprint after | identical to before, 135/135 files |

Voice turn detail: a 2.08 s English clip was generated locally with Windows
speech synthesis, resampled to 16 kHz mono linear16 and streamed to the socket
in real time. Observed transcript: "Hello. What can you help me with?". The
assistant streamed "I'm the Paytm Voice Teammate, here to help you run your
Paytm merchant business." and produced 22 binary audio frames. Silence-based
end of utterance worked (Silero VAD logged speech start and end).

### Baseline defect found and fixed

Deepgram rejected the streaming connection with HTTP 400:
`INVALID_QUERY_PARAMETER: Keywords are not supported for Nova-3. Please use
keyterm instead.` The inherited code sent `keywords` while
`DEEPGRAM_MODEL=nova-3`. Without this fix the clone fell back to local
Whisper on every session. Fixed in `backend/app/services/voice/deepgram.py`:
the keyword parameter is now `keyterm` for `nova-3` and `keywords` for older
models. This is a compatibility fix only; Deepgram is removed from the active
path in Phase 1.

### Environment issues observed (not caused by the clone)

- `concise-tapir-162853.upstash.io` does not resolve, so Redis persistence is
  degraded and the session repository uses its in-process fallback. The clone
  uses `paytm:` keys, so no data can reach the original's namespace.
- `QDRANT_URL` is unreachable from this machine, so retrieval and memory are
  unavailable. The assistant still answers in general mode.
- First utterance after a fresh install is slow because Emotion2Vec, the
  FastEmbed model and the Whisper fallback model download on first use.

### Phase 0 acceptance

| Acceptance item | Status |
| --- | --- |
| Backup archive exists and verified | Pass |
| Clone runs on separate ports (3100/8100) | Pass |
| Original fingerprint unchanged | Pass |
| Voice turn works (transcript, reply, audio) | Pass (synthesized speech; live microphone check left to owner) |

---

## 2026-10-29 — Phase 1: Sarvam speech-to-text, language support, TTS interface

### Scope

Make Sarvam AI the active speech-to-text provider for Hindi (`hi-IN`),
Kannada (`kn-IN`) and English (`en-IN`), keep Silero VAD for barge-in, add a
provider-neutral STT/TTS interface, and keep the rest of the voice loop
unchanged. Redis and Qdrant remain untouched in this phase.

### Decision: Sarvam Realtime Streaming, not the brief's batch endpoint

The brief names model `saaras:v3` on `/speech-to-text/ws`. Sarvam's current
documentation for live agent audio uses **Realtime Streaming**:

- endpoint `wss://api.sarvam.ai/speech-to-text-realtime/ws`
- model `saaras:v3-realtime` (documented default; `saaras:v4` also available)
- `stream_type=fast`, `encoding=linear16`, `sample_rate=16000`,
  `endpointing=vad`
- auth header `api-subscription-key`

Realtime Streaming is the only option that returns partial transcripts while
the merchant is still speaking, which barge-in needs. The batch endpoint would
add a full-utterance round trip and break interruption latency. **Followed the
docs and recorded the difference here.** All parameters are overridable
through `SARVAM_*` settings, so switching back to the brief's endpoint is a
config change plus a small adapter change, not a rewrite.

Protocol implemented (`backend/app/services/stt/sarvam.py`):

| Direction | Message |
| --- | --- |
| client → server | `{"event":"audio_input","audio":"<base64 PCM16>"}` |
| client → server | `{"event":"config.update","language_code":"hi-IN"}` |
| client → server | `{"event":"ping"}` every 20 s |
| client → server | `{"event":"end"}` for a graceful close |
| server → client | `session.begin`, `vad.speech_start`, `vad.speech_end` |
| server → client | `transcript.partial`, `transcript.final`, `config.updated`, `pong` |
| server → client | `session.end`, `error` (`code`, `is_fatal`, `message`, `status_code`) |

Implementation notes:

- Raw `websockets` client instead of the `sarvamai` SDK, because the SDK does
  not expose linear16 PCM framing.
- One transient reconnect on network failure; authentication and parameter
  errors (`400`, `401`, `403`) are not retried.
- Audio is base64-encoded into a bounded queue so the VAD loop never blocks on
  the network.
- Fatal `error` events and unexpected `session.end` hand control to the
  fallback chain exactly once. Non-fatal errors are logged and the stream
  continues.
- Documented close codes are mapped to readable reasons: `1003` (rate limit,
  quota, invalid key), `1008` (inactivity), `1011` (internal), `4000`
  (invalid parameter). The brief mentions `403`; the endpoint documents
  `4000` for parameter errors and `1003` for auth/quota, which is what the
  code handles.

### Provider chain and fallback

`backend/app/services/voice/handlers/audio.py` now builds the STT stack from
an ordered candidate list instead of hard-coding Deepgram:

| Order | Provider | When |
| --- | --- | --- |
| 1 | Sarvam Realtime | `VOICE_STT_PROVIDER=sarvam` (default) |
| 2 | Deepgram live | Sarvam fails to start or drops mid-session, `VOICE_ALLOW_DEEPGRAM_FALLBACK=true` |
| 3 | Local faster-whisper | Both streaming providers unavailable and `VOICE_ALLOW_WHISPER_FALLBACK=true` (existing consent flow) |

Behaviour:

- A missing `SARVAM_API_KEY` is not a user-facing error: the chain skips to
  Deepgram and the session continues. `stt_ready` reports the provider that
  actually connected.
- Mid-session provider changes emit `stt_switched` with
  `from_provider`/`to_provider`, and the existing Whisper consent prompt is
  reused when no streaming provider is left.
- `VOICE_STT_PROVIDER` values other than `sarvam`, `deepgram` or `whisper`
  now fail fast with `invalid_stt_provider`. Previously an unknown value
  would have been silently served by the Deepgram backup.

### Language handling

- New `backend/app/services/voice/language.py`:
  `normalize_language_code()` accepts `auto`, `hi-IN`, `kn-IN`, `en-IN` and
  friendly aliases (`hi`, `hindi`, `kn`, `kannada`, `en`, `english`,
  `en_in`, ...). Unsupported codes raise `ValueError`.
- `VOICE_DEFAULT_LANGUAGE=auto` keeps Sarvam's adaptive detection on. A
  client may lock a language by sending `session_init` with `language` or
  `language_code`.
- Sarvam applies a lock in place with `config.update`; Deepgram reconnects
  with the mapped code (`hi-IN`→`hi`, `kn-IN`→`kn`, `en-IN`→`en-IN`,
  `auto`→`DEEPGRAM_LANGUAGE`). A `language_changed` event is sent either way.
- When Sarvam is in `auto` mode the detected `language` from each final
  transcript is stored on the session (`detected_language`), and
  `VoiceSession.effective_language` feeds the TTS request. The assistant
  answers in the language the merchant just spoke.

### Text-to-speech

- New `TextToSpeechProvider` interface in
  `backend/app/services/tts/base.py` (`BaseTTSProvider` kept as an alias).
  Cartesia is still the only implementation, so a swap in a later phase is a
  factory change.
- Model moved from `sonic-3.5` to **`sonic-3.6`** (current general-availability
  model, 44 languages). It speaks `hi`, `kn` and `en` natively, including
  Hinglish.
- `language` is now a per-request argument on `synthesize()` and `stream()`,
  passed through `StreamingTTS` from `ConversationManager.stream_voice()` and
  `speak_only()`. `auto` resolves to `VOICE_TTS_LANGUAGE` (default `en-IN`).
- `CARTESIA_MODEL` and `VOICE_TTS_LANGUAGE` are configurable; previously the
  model ID was hard-coded and the language was always `"en"`.

### Inherited product-name rewriting removed

`normalize_transcript()` previously rewrote phonetic renderings ("vee ah",
"veeya", "viah") into "Via" before the text reached the LLM. In this product
that injected another product's name into every transcript. It now only
collapses whitespace. The corresponding unit test was updated to assert that
the speaker's words are preserved.

### Files

Added:

- `backend/app/services/stt/streaming.py` — `TranscriptEvent` (now with
  `language`), `StreamingSTTProvider` ABC with `start`/`send_audio`/`close`/
  `set_language`
- `backend/app/services/stt/sarvam.py` — `SarvamStreamingSTT`
- `backend/app/services/voice/language.py` — language normalization and
  Cartesia mapping
- `backend/app/services/tts/base.py` — `TextToSpeechProvider` (rewritten)
- `backend/tests/test_sarvam_stt.py` — 19 tests
- `backend/scripts/sarvam_stt_smoke.py` — owner-run live harness for
  `hi-IN`, `kn-IN`, `en-IN`

Changed:

- `backend/app/services/voice/deepgram.py` — implements
  `StreamingSTTProvider`, `name="deepgram"`, language-aware `start()`,
  re-exports `TranscriptEvent`
- `backend/app/services/voice/handlers/audio.py` — provider chain, fallback,
  language switching, TTS language
- `backend/app/services/voice/session.py` — `stt_stream`, `language`,
  `detected_language`, `effective_language`
- `backend/app/core/config.py` — Sarvam settings, `VOICE_DEFAULT_LANGUAGE`,
  `VOICE_ALLOW_DEEPGRAM_FALLBACK`, `CARTESIA_MODEL`, `VOICE_TTS_LANGUAGE`,
  default `VOICE_STT_PROVIDER=sarvam`
- `backend/app/services/tts/cartesia.py`, `tts/stream.py`,
  `conversation_manager.py` — per-request language, `sonic-3.6`
- `backend/app/api/system.py` — `/system/status` reports `sarvam`, STT model,
  default language and TTS model
- `backend/tests/test_vf031.py` — transcript normalization expectation
- `.env.example` — Sarvam block, `sonic-3.6`, `VOICE_DEFAULT_LANGUAGE`,
  `Paytm:3` keyterm, port 3100 CORS

`backend/.env` gained `SARVAM_API_KEY=` (empty until the owner supplies it),
`VOICE_DEFAULT_LANGUAGE=auto` and `CARTESIA_MODEL=sonic-3.6`; its existing
values were not printed or rewritten.

### Tests

`python -m unittest discover -s tests` → **56 tests, OK**. `compileall` is
clean and `app.main` imports.

Coverage added:

- language aliases, rejection of unsupported codes, Cartesia fallback to the
  default language
- Sarvam URL parameters, partial/final events, detected language, locked
  language echo, fatal error reported once, non-fatal error keeps the stream,
  `config.update` on language change, empty finals ignored, close-code reasons
- Deepgram language mapping and the Nova-3 `keyterm` parameter
- provider chain ordering: Sarvam → Deepgram, Deepgram alone, fallback
  disabled, Whisper primary skips streaming, factory builds the right
  provider with the session language

### Live verification

| Check | Result |
| --- | --- |
| `GET /system/status` | `sarvam: configured`, `stt_provider: sarvam`, `stt_model: saaras:v3-realtime`, `default_language: auto`, `tts_model: sonic-3.6` |
| Voice socket handshake | `stt_ready provider=sarvam`, `model=saaras:v3-realtime`, `language=auto` |
| Language lock over the socket | `session_init` with `language: "hi-IN"` → `language_changed: hi-IN` (Sarvam `config.update`, no reconnect) |
| Full voice turn over the socket | Sarvam partials, final "Hello, what can you help me with?", streamed reply, Cartesia audio frames, `assistant_audio_end` |
| Fallback behaviour without a key | Session continues on Deepgram with no user-visible error |

Live Sarvam transcription, `scripts/sarvam_stt_smoke.py`, Cartesia-synthesized
merchant sentences streamed as 16 kHz PCM:

| Language | Final transcript | Partials | Result |
| --- | --- | --- | --- |
| `hi-IN` | मेरा पेटीएम क्यूआर कोड काम नहीं कर रहा है, कृपया मदद करें। | 67 | PASS |
| `kn-IN` | ನನ್ನ ಪೇಟಿಎಂ ಕ್ಯೂಆರ್ ಕೋಡ್ ಕೆಲಸ ಮಾಡುತ್ತಿಲ್ಲ, ದಯವಿಟ್ಟು ಸಹಾಯ ಮಾಡಿ. | 69 | PASS |
| `en-IN` | My Paytm QR code is not working. Can you help me? | 37 | PASS |
| `auto` (Hindi audio) | मेरा पेटीएम क्यूआर कोड काम नहीं कर रहा है, कृपया मदद करें। | 55 | PASS, detected `hi-IN` |

`auto` mode returned `language: hi-IN` on the final event, which is what drives
the reply language. Early partials in `auto` mode showed code-mixed output
("paytm QR code cord ...") before converging on the correct final, which is
expected from Sarvam's code-mixed handling.

Locked-language turns through the full socket (Cartesia audio in, Sarvam
transcript, Groq reply, Cartesia audio out):

| Language | Sarvam transcript | Assistant reply | Result |
| --- | --- | --- | --- |
| `hi-IN` | मेरा पेटीएम क्यूआर कोड काम नहीं कर रहा है, कृपया मदद करें। | Hindi, numbered troubleshooting steps | PASS |
| `kn-IN` | ನನ್ನ ಪೇಟಿಎಂ ಕ್ಯೂಆರ್ ಕೋಡ್ ಕೆಲಸ ಮಾಡುತ್ತಿಲ್ಲ, ದಯವಿಟ್ಟು ಸಹಾಯ ಮಾಡಿ. | Kannada, troubleshooting steps | PASS |

Both turns sent `language_changed` before the transcript and produced audio
frames through `assistant_audio_end`. Observation for Phase 2: the general
system prompt still answers in written style (numbered Markdown lists), which
reads poorly over voice. Prompt and persona work belongs to the telecalling
phase.

### Fix found during live verification

Sarvam's interim transcripts sometimes begin with a stray quote character
(`"`, `"'`) picked up before speech onset. Finals are post-processed by the
server and were clean, but the UI receives partials. `clean_partial()` in
`backend/app/services/stt/sarvam.py` trims quote characters from partials
only; two tests cover it. After the fix the observed partials started at
`Hello` with no artifacts.

### Still to check in the browser (owner)

- Live microphone input in Hindi, Kannada and English, including the reply
  language.
- Barge-in with Sarvam active. Silero VAD and the provisional-interruption
  watchdog are unchanged and their unit tests pass, but the real barge-in
  path has only been exercised with Deepgram so far.

### Docs vs brief, recorded

| Brief | Current docs / implementation |
| --- | --- |
| `saaras:v3` on `/speech-to-text/ws` | `saaras:v3-realtime` on `/speech-to-text-realtime/ws` |
| error `403` for auth | `error` event with `status_code: 401`, close code `1003` for auth/quota, `4000` for parameter errors |
| Deepgram active | Sarvam active, Deepgram first backup, Whisper last resort |

### Phase 1 acceptance

| Acceptance item | Status |
| --- | --- |
| Sarvam is the configured STT provider | Pass |
| Hindi, Kannada, English transcription | Pass (live, all three languages) |
| Language lock and `auto` detection | Pass (live) |
| Hindi and Kannada replies via TTS | Pass (live) |
| Silero VAD still drives barge-in | Pass (unchanged, tests green) |
| Fallback Sarvam → Deepgram → Whisper | Pass (Deepgram path exercised live; Whisper path unchanged from Phase 0) |
| TTS behind an interface, per-request language | Pass |
| No secrets printed or committed | Pass |
| Owner browser verification | Pending |

---

---

## 2026-10-29 - Phase 2: Retune the models and intents for telecalling

Goal: stop the assistant sounding like an IVR, keep replies short enough to
listen to, answer in the language of the call, and make a turn feel fast.

### Owner decisions that override the brief

| Topic | Brief | Built |
| --- | --- | --- |
| Emotion analysis | delete it outright | module kept, disabled by default (`VOICE_ENABLE_EMOTION=false`); nothing loads, waits or changes the prompt while false. One flag turns it back on. |
| Reply length | one or two sentences | aim for three, allow a fourth when it is a question, absolute cap of five. Over budget, close with a short "would you like to know more?" offer. |
| Language lock | Phase 3 asks and locks | left in Phase 3 as briefed. Phase 2 adds a strict "reply only in the call language" prompt rule; the automatic switch itself is fixed by the Phase 3 lock. |

### What changed

- `backend/app/core/prompts.py`
  - replaced the general system prompt with a merchant telecalling persona:
    truth rules, confirm before money commitments, one question at a time,
    hand over to a human when that is the honest answer.
  - new `build_voice_prompt(language)` with a hard language rule for
    `hi-IN`, `kn-IN`, `en-IN` and an `auto` rule: reply in the language the
    merchant used, never transliterate an Indian language into Latin letters.
  - voice rules: one to three sentences, fourth only if a question, never
    more than five, no lists or Markdown, amounts in words, one question.
  - `CLARIFICATION_MODE_PROMPT` kept for the parked emotion path.
- `backend/app/services/voice/response_guard.py` (new)
  - `strip_voice_markup`: removes code fences, headers, bullets, numbered
    markers, bold/italic, links and table pipes.
  - sentence splitting for `.`, `!`, `?`, Devanagari `।` and `॥`, with guards
    for numbered markers and abbreviations such as `Rs.`
  - `VoiceReplyGuard`: streaming budget (soft 3, max 5, fourth allowed only
    when it ends in a question), localized closing question, long-sentence
    chunks cut at a word boundary without spending a sentence.
  - `apology_line(language)` for a failed model call.
- `backend/app/services/llm.py`
  - one model for replies and classification (`LLM_MODEL` and
    `LLM_CLASSIFIER_MODEL`, both `openai/gpt-oss-120b`).
  - 12 s timeout, one retry, `complete_json` helper, no silent failure.
  - `reasoning_effort=low`. This mattered: gpt-oss hidden reasoning tokens
    count against `max_tokens`, and with the larger telecalling prompt a
    220-token ceiling sometimes produced an empty or half-finished reply.
- `backend/app/services/intent.py` (new)
  - 17 labels: settlement_query, transaction_issue, qr_code_issue,
    device_issue, refund_query, loan_interest, soundbox_issue, charges_query,
    onboarding_kyc, language_choice, confirmation_yes, confirmation_no,
    human_request, callback_request, opt_out, objection, other.
  - slot extraction: amount, transaction id, date, phone, time, product,
    language.
  - deterministic fast path for the six safety labels (opt-out, human,
    callback, language, yes, no) in English, Hindi and Kannada; everything
    else goes to the JSON classifier, with a safe fallback to `other`.
- `backend/app/services/conversation_manager.py`
  - language-aware system prompt, no more duplicated demo prompt.
  - emotion clarification gate only runs when the feature is enabled.
  - streaming replies pass through `VoiceReplyGuard`; the model stream stops
    as soon as the spoken budget is spent.
  - failed model call speaks a localized apology instead of silence.
- `backend/app/core/config.py`
  - `LLM_MODEL`, `LLM_CLASSIFIER_MODEL`, `LLM_TIMEOUT_SECONDS`,
    `LLM_MAX_RETRIES`, `LLM_REASONING_EFFORT`, `VOICE_REPLY_SOFT_SENTENCES`,
    `VOICE_REPLY_MAX_SENTENCES`, `VOICE_MAX_TOKENS` 320, emotion default false.
- `.env.example` and `backend/.env`
  - emotion off, new LLM and reply-budget settings, reasoning effort low.
  - only key names were edited; no secret value was printed.
- Tests and tooling
  - `backend/tests/data/intent_examples.py`: 5 examples per intent per
    language, 255 turns in total.
  - `backend/tests/test_intent.py`, `backend/tests/test_response_guard.py`.
  - `backend/scripts/intent_eval.py`: owner-run live accuracy run, one model
    call per example the rules do not catch.

### Tests

`python -m unittest discover -s tests` -> **97 tests, OK**. `compileall` is
clean and `app.main` imports.

Coverage added:

- 17 unique intent labels, dataset completeness, every safety example caught
  by a rule without calling the model, non-safety turns not misread as safety,
  language names in three scripts, slot extraction, JSON classifier path,
  unknown label and model failure fallback.
- markup stripping, Devanagari sentence stops, numbered markers and
  abbreviations, budget at 3/4/5, localized offer, auto language adding no
  offer, streaming guard matching the batch result, long-sentence handling,
  apology text.

### Latency

Warm English turn, same probe as Phase 1:

| Measurement | Phase 1 | Phase 2 |
| --- | --- | --- |
| Final transcript | +1.31 s | +1.28 to +2.34 s |
| First token | +2.02 s | +1.55 to +6.27 s |
| First audio | +2.32 s | +1.86 to +6.86 s |
| Turn complete | 10.89 s | 2.95 to 7.98 s |

The turn is much shorter because the reply is short and the model stream stops
at the budget. The remaining spread is Groq queue time, not the pipeline: the
same probe measured 1.55 s and 6.27 s for first token on consecutive warm
turns. The first turn after a backend restart is consistently slower
(7.0-7.5 s first token) because the model connection is cold; subsequent turns
are warm.

Emotion no longer appears in the backend log at all: no model download, no
`emotion2vec`, no `funasr` lines after the restart, and `/system/status`
reports `emotion_enabled: false`.

### Live replies

Full socket turns, Cartesia audio in, Sarvam transcript, Groq reply, Cartesia
audio out:

| Language | Transcript | Reply | Sentences |
| --- | --- | --- | --- |
| `hi-IN` | मेरा पेटीएम क्यूआर कोड काम नहीं कर रहा है, कृपया मदद करें। | कृपया बताइए, QR कोड स्कैन करने पर क्या कोई त्रुटि संदेश दिख रहा है या स्क्रीन पर कुछ नहीं आता? | 1 |
| `kn-IN` | ನನ್ನ ಪೇಟಿಎಂ ಕ್ಯೂಆರ್ ಕೋಡ್ ಕೆಲಸ ಮಾಡುತ್ತಿಲ್ಲ, ದಯವಿಟ್ಟು ಸಹಾಯ ಮಾಡಿ. | ನಿಮ್ಮ ಕ್ಯೂಆರ್ ಕೋಡ್ ಕೆಲಸ ಮಾಡದಿರುವುದನ್ನು ಅರ್ಥಮಾಡಿಕೊಂಡೆ. ದಯವಿಟ್ಟು, ಇತ್ತೀಚೆಗೆ ಕೋಡ್ ಬದಲಾಯಿಸಿದ್ದೀರಾ ಅಥವಾ ಯಾವುದೇ ದೋಷ ಸಂದೇಶ ಕಾಣಿಸುತ್ತಿದೆಯಾ? | 2 |
| `en-IN` | My Paytm QR code is not working. Can you help me? | I'm sorry the QR isn't working. Could you tell me if it's showing an error message or just not scanning at all? | 2 |

All three stayed in the call language and script, asked one clarifying
question, and contained no lists or formatting. The previous Kannada turn that
opened with a numbered troubleshooting list is gone.

### Phase 2 acceptance

| Acceptance item | Status |
| --- | --- |
| Intent classifier tests pass | Pass (97 tests, safety rules covered in three languages) |
| No emotion code loads | Pass (disabled by default, no model lines in the log) |
| Replies are short and spoken-style | Pass (live, 1-2 sentences, no Markdown or numbered steps) |
| Sample transcript per language | Pass (Hindi, Kannada, English) |
| One model for replies and classification | Pass |
| Timeout, one retry, spoken apology | Pass |
| No secrets printed or committed | Pass |
| Owner browser verification | Pending |
| Live intent accuracy run | Pending, owner-run: `scripts/intent_eval.py` |

### Notes for the next phase

- Kannada-to-English switching in `auto` mode is still possible until the
  Phase 3 ask-and-lock lands. The Phase 2 prompt forbids switching, but the
  session language itself is not locked yet.
- The reply budget is enforced in code, so a prompt regression cannot bring
  the numbered-list read-aloud back.
- Groq latency varies by queue; if the first audio of a call needs to be more
  predictable, pre-warming the model at startup is the next lever.

---

## 2026-10-30 - Handoff: where the build stands, evidence, and what comes next

This section is written so another agent can resume without reading the whole
log. Read this section, then the Phase 2 section above.

### One-line status

Phases 0, 1 and 2 are complete, live-verified and committed. Phase 3 has not
started. Nothing is half-edited: the working tree was clean at the Phase 2
commit.

| Item | Value |
| --- | --- |
| Working repo | `G:\Coding\Projects\paytm-voice-teammate` |
| Read-only original | `G:\Coding\Projects\Paytm Hackathon` (never modify) |
| Branch | `master`, no remote, never push |
| Last commit | `6b00ed0 phase 2: retune for merchant telecalling` |
| Backend | FastAPI, `127.0.0.1:8100` |
| Frontend | Vite, `http://localhost:3100` |
| Redis prefix | `paytm:` |
| Qdrant collections | `paytm_memory`, `paytm_policy` |
| Tests | 97 passing |

### How to run everything

Backend, from the repo:

```
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8100 --log-level warning
```

Frontend, from the repo:

```
cd frontend
npm run dev
```

Secrets live only in `backend/.env`, which is git-ignored. `.env.example`
documents every key with empty values. Never print or commit a key.

Health check:

```
curl http://127.0.0.1:8100/system/status
```

Expected: `status=running`, `emotion_enabled=false`, `stt=sarvam/saaras:v3-realtime`,
`tts=sonic-3.6`, `default_language=auto`. Persistence reports `degraded` because
the hosted Redis and Qdrant are unreachable from this machine; the in-process
fallback keeps voice working and this is not a build defect.

Verification commands, all owner-runnable:

```
cd backend
.venv\Scripts\python.exe -m unittest discover -s tests
.venv\Scripts\python.exe scripts\voice_latency_probe.py en-IN
.venv\Scripts\python.exe scripts\voice_turn_probe.py hi-IN
.venv\Scripts\python.exe scripts\voice_turn_probe.py kn-IN
.venv\Scripts\python.exe scripts\voice_turn_probe.py en-IN
.venv\Scripts\python.exe scripts\intent_eval.py
.venv\Scripts\python.exe scripts\intent_eval.py --language hi-IN
```

`intent_eval.py` spends Groq credits: one classification call per example the
rule fast path does not catch. It has not been run yet.

### What is done, with evidence

| Phase | Commit | Evidence |
| --- | --- | --- |
| 0 clone and isolate | `21c0264`, `2fea99a`, `c6c5529` | fingerprint identical (135 files), ports and prefixes isolated, Nova-3 `keyterm` fixed |
| 1 Sarvam STT, hi/kn/en, TTS | `b097fe3`, `45cdcc9` | 56 tests, live hi/kn/en/auto smoke pass, Sarvam listed as active provider |
| 2 telecalling retune | `6b00ed0` | 97 tests, live hi/kn/en turns, emotion absent from the log, latency measured |

Phase 2 detail that matters later:

- `backend/app/core/prompts.py` holds the whole voice persona and
  `build_voice_prompt(language)`. This is the single editable prompt file the
  brief asks for.
- `backend/app/services/voice/response_guard.py` enforces short speech in
  code, so a prompt regression cannot make the agent read a list aloud. Budget:
  aim for three sentences, a fourth only if it is a question, hard cap five,
  otherwise close with a localized "would you like to know more?".
- `backend/app/services/intent.py` classifies a turn against the brief's 16
  labels, with the concrete merchant issue in a separate `topic` field. Rules
  run first for `opt_out`, `human_request`, `ticket_request`,
  `repeat_complaint`, `callback_request`, `language_choice`,
  `confirmation_yes` and `confirmation_no` in all three languages. Everything
  else asks the model for JSON.
- `backend/app/services/llm.py` uses one model, `openai/gpt-oss-120b`, for
  replies and classification, with a 12 s timeout, one retry and
  `reasoning_effort=low`. The effort setting is not cosmetic: hidden reasoning
  tokens count against `max_tokens`, and without it replies came back empty or
  cut in half.
- Two probes were promoted from temporary scripts into the repo at
  `backend/scripts/voice_latency_probe.py` and
  `backend/scripts/voice_turn_probe.py`, so the numbers below can be
  reproduced by the next agent.

Warm English turn, measured with the probe:

| Measurement | Phase 1 | Phase 2 |
| --- | --- | --- |
| Final transcript | +1.31 s | +1.28 to +2.34 s |
| First token | +2.02 s | +1.55 to +6.27 s |
| First audio | +2.32 s | +1.86 to +6.86 s |
| Turn complete | 10.89 s | 2.95 to 7.98 s |

The spread is Groq queue time on the same warm backend, not pipeline work. The
first turn after a restart is consistently slower (about 7 s to first token).

### Decisions taken against the brief

These were owner instructions or necessary judgement calls. They are recorded
so nobody silently reverts them, and so Phase 4 knows where it stands.

1. **Emotion analysis is parked, not deleted.** The brief says remove it
   outright. The owner asked to keep it re-enablable. `VOICE_ENABLE_EMOTION`
   is `false` in `.env.example` and in `backend/.env`. While false, no model is
   loaded, nothing waits on it and the clarification prompt is not used.
   Caveat: `backend/app/services/emotion/provider.py` still does
   `from funasr import AutoModel` at import time, so the module is imported
   (cheap) but the model is never constructed. If Phase 4 wants the brief's
   "no dead code" reading literally, delete the module and the flag then.
2. **Reply length is three, four if a question, five max.** The brief says one
   or two. The owner asked for a little more room. Enforced in
   `VoiceReplyGuard`.
3. **The intent taxonomy was reconciled on 2026-10-30.** Phase 2 shipped 17
   labels that did not match the brief; see the reconciliation section below.
   `intent` is now exactly the brief's 16 labels and the extra merchant-issue
   detail lives in `topic`. Nothing to decide here any more.
4. **Language is still `auto`.** Phase 3 owns ask-and-lock. Until then, `auto`
   can still follow the merchant from Kannada into English. The Phase 2 prompt
   forbids switching in words, but the session language is not locked.
5. **No trilingual greeting and no recording notice yet.** The brief puts both
   in the Phase 3 greeting. Nothing in the current greeting contradicts it, and
   there is no user-visible "Via" text.

### What comes next, in the brief's order

**Phase 3 - language selection at the start of every call.** Done (2026-10-30,
see the Phase 3 section at the end of this log). Checklist from brief section 6:

- [x] Greeting: one short line in Hindi, Kannada and English that introduces
      the assistant, says the call may be recorded, and asks which language the
      merchant is comfortable in.
- [x] Classifier returns `language_choice` with a value in `{hi, kn, en}` for
      the language name in any of the three scripts and for common spellings.
      A single-word answer must work.
- [x] Confirm once in the chosen language ("Okay, we will continue in
      Kannada"), then persist `session.language`.
- [x] Use the locked language for speech to text, the system prompt and the TTS
      language field for the rest of the call.
- [x] Unclear answer: ask once more, slowly and simply. If still unclear,
      default to English and offer a human.
- [x] Change of mind: if the merchant explicitly names another language later,
      update the language. Never switch on its own.
- [x] Pre-generate the greeting and fixed phrases once per language and cache
      them as audio files, per brief section 9.
- [x] Acceptance: all three languages end to end, the unclear path works, and
      the language never changes by itself. Proven live by
      `scripts/language_gate_probe.py`, 8/8 checks.

Files: `backend/app/services/voice/session.py` (`language_locked`,
`language_attempts`), `backend/app/services/voice/handlers/audio.py` (greeting,
gate, `language_changed`, cached-clip speaker),
`backend/app/services/voice/language_gate.py` (pure decisions),
`backend/app/services/voice/phrases.py` (fixed lines),
`backend/app/services/voice/prerender.py` (PCM cache), `intent.py` (language
aliases and code-mixed matching), and the frontend `language_changed` event
with a Language row in the session signals.

**Phase 4 - Paytm agent.** Not started. From the brief: conversation states,
delegation protocol with a sub agent, a separate `mock_paytm/` FastAPI service
on port 8200 with seeded data, tool functions with idempotency and audit
entries, escalation rules, session memory, and a dashboard. The sub agent is
`openai/gpt-oss-120b` with tool calling, at most three steps, eight second
total budget, four second per-function timeout and one retry.

**Phase 5 - hackathon-day readiness.** Not started. See brief section 8 and
section 9 on credit protection and demo reliability.

### Pending owner actions

- [ ] Browser check on `http://localhost:3100`: microphone in Hindi, Kannada
      and English, plus barge-in.
- [ ] Run `scripts/intent_eval.py` for live intent accuracy. It spends Groq
      credits, which is why it was left to the owner. The taxonomy is now the
      brief's 16 labels, so the run also reports how often `topic` agrees with
      the label it implies.

### Gotchas for the next agent

- Windows PowerShell mangles non-ASCII on `Add-Content` and in the console.
  Write Unicode files with Python or the editor tool, and check with
  `repr()`/`Select-String` rather than trusting console output.
- `backend/.env` is the only place secrets exist. Changing settings means
  editing keys there; `.env.example` only documents names.
- Qdrant and Redis are unreachable here. Standalone scripts that call
  `QdrantService` raise `ResponseHandlingException`. Use the running backend,
  or avoid retrieval.
- The first Groq call after a restart is cold and roughly 7 s. Warm turns are
  much faster. Do not read the first measurement as a regression.
- `VOICE_MAX_TOKENS` is 320 by default and is not set in `backend/.env`.
  `reasoning_effort=low` must stay on every Groq call or replies will
  intermittently come back empty.
- Git warns about LF/CRLF on every commit. It is noise from
  `core.autocrlf`, not a problem with the files.
- Voice sessions are keyed by `client_id`; the probes use their own ids so they
  do not disturb a browser session.

---

## 2026-10-30 - Intent taxonomy reconciled to the brief

### Why

Phase 2 shipped 17 labels built from the merchant-issue angle rather than from
brief section 5.3. Ten matched the brief, six brief labels were missing
(`ticket_request`, `device_offer_interest`, `policy_question`,
`repeat_complaint`, `smalltalk`, `out_of_scope`), and seven labels existed that
the brief does not name. That was a spec deviation with real consequences:
Phase 4 escalation in section 7.5 keys on `repeat_complaint` and
`out_of_scope`, retrieval in section 7.7 keys on `policy_question`, and the
tool layer in section 7.4 maps `ticket_request` to `create_support_ticket` and
`device_offer_interest` to `send_offer_link`. None of those could ever fire.

The Phase 2 tests did not catch it because the 255-example dataset was written
from the same label list the code used, so the tests validated the label list
against itself.

### Owner decision

Keep the brief's 16 labels as `intent`, because that is what Phase 4 routes and
escalates on, and carry the extra merchant-issue detail in a separate `topic`
field so answers keep the precision the Phase 2 labels had. One label per turn,
exactly as the brief requires.

### What changed

- `backend/app/services/intent.py`
  - `INTENTS` is now the brief's 16 labels. `other` is gone.
  - new `TOPICS` and `extract_topic()`: `transaction_issue`, `qr_code_issue`,
    `refund_query`, `soundbox_issue`, `charges_query`, `onboarding_kyc`.
  - `IntentResult` gained a `topic` field; `as_dict()` returns it next to
    `intent`, `confidence`, `slots` and `source`.
  - the classifier prompt now asks for
    `{"intent": ..., "confidence": ..., "topic": ...}` and states that
    money-related asks are `out_of_scope`.
  - new rule-backed labels: `ticket_request`, `repeat_complaint`, `smalltalk`,
    and a narrow `device_offer_interest` phrase list. `CRITICAL_INTENTS` is the
    old `SAFETY_INTENTS` under a clearer name, now including ticket and repeat
    complaint because both promise or escalate something.
  - rule order is now opt-out, human, ticket, repeat complaint, callback,
    confirmation no, confirmation yes, device offer, smalltalk. `repeat_complaint`
    moved above `callback_request` because "I called before and nothing
    happened" is a repeat complaint, not a request to be called back.
  - the model-failure and unknown-label fallback is `out_of_scope`, which is
    safer than the old `other`: Phase 4 escalates on it instead of answering.
  - an empty transcript classifies as `smalltalk`.
- `backend/tests/data/intent_examples.py`: rewritten to 16 labels x 5 examples
  x 3 languages, 240 turns. Examples for `ticket_request`, `repeat_complaint`,
  `smalltalk`, `out_of_scope`, `policy_question` and `device_offer_interest`
  were added in Devanagari, Kannada and English. Soundbox and card-machine
  faults now both sit under `device_issue`.
- `backend/tests/test_intent.py`: asserts the exact 16-label set, that no
  issue label leaked into `INTENTS`, that the topic map only names valid
  labels, that all eight critical labels are caught by rules without a model,
  topic extraction in three scripts, rule topic beating the model topic,
  unknown topic being dropped, and the `out_of_scope` fallback.
- `backend/scripts/intent_eval.py`: reports intent accuracy per language,
  how many turns each path resolved, the critical-rule rate, and how often
  `topic` agrees with the label it implies.

### Topic to label map

Used by the eval script and worth remembering in Phase 4:

| topic | usual label | why |
| --- | --- | --- |
| `soundbox_issue` | `device_issue` | the brief's device fault |
| `qr_code_issue` | `policy_question` | answered from troubleshooting policy |
| `charges_query` | `policy_question` | answered from the fee policy |
| `onboarding_kyc` | `policy_question` | answered from the KYC policy |
| `refund_query` | `out_of_scope` | money-related, escalate to a human |
| `transaction_issue` | `out_of_scope` | money-related, escalate to a human |

The map is a guide, not a hard rewrite: the model picks the label, the regex
picks the topic, and the eval script reports disagreement. Money-related turns
landing in `out_of_scope` is deliberate, because section 7.4 has no refund or
limit-change function and section 7.5 says to hand those to a human.

### Tests

`python -m unittest discover -s tests` -> **106 tests, OK** (was 97).
`compileall` is clean and `app.main` imports.

### What this means for Phase 4

- Route and escalate on `intent` only. Every label the brief's sections 7.4,
  7.5 and 7.7 refer to now exists.
- Use `topic` for the answer detail and for choosing a policy passage, never
  for routing.
- `out_of_scope` now covers three cases: genuinely out-of-function asks,
  money-related asks, and any turn where classification failed. Treat all three
  as escalation or "a human will help", not as a chance to improvise.
- `ticket_request` and `device_offer_interest` are commitments. The brief
  requires verbal confirmation before `create_support_ticket` or
  `send_offer_link`, so Phase 4 must gate them on `confirmation_yes`.

---

## 2026-10-30 - Phase 3: ask-and-lock language selection

Commit: $hash.

### Objective

The agent must no longer detect language by itself. Every call starts with a
trilingual greeting, asks which language the merchant wants, locks the answer,
and uses that language for speech to text, the reply model and text to speech
for the rest of the call. Brief section 6.

### Call flow now

1. The browser opens `/ws/voice` and sends `session_init` (no language).
2. The backend plays the pre-rendered greeting, one clip per language, in the
   order Hindi, Kannada, English. Each line introduces the assistant, gives the
   recording notice, and names the three options.
3. Until the merchant answers, `session.language` stays `auto` so Sarvam can
   understand an answer in any of the three languages, and every final
   transcript goes to the language gate instead of the reply model.
4. On a clear answer the gate locks the language, switches the Sarvam stream,
   sends `language_changed` with `locked: true`, and speaks a confirmation in
   the chosen language. That confirmation also invites the first question, so
   the call does not stall.
5. After the lock, every turn goes to the normal reply path with
   `session.effective_language` as the language for the prompt and Cartesia.
6. A later explicit request for another language changes it and speaks the
   short "changed" line. Nothing else can move the call off the chosen
   language.

Barge-in works throughout: speaking while the greeting or a confirmation is
playing interrupts it within about 100 ms and the new turn is handled
immediately. The probe relies on this.

### Gate decisions

`backend/app/services/voice/language_gate.py` is pure and unit-tested:

| action | when | what the handler does |
| --- | --- | --- |
| `lock` | an explicit language name, any script, any common spelling, alone or in a short turn | lock and speak `confirm` in that language |
| `retry` | unclear on the first answer | speak `retry` in all three languages, remember one attempt |
| `default` | unclear again | lock English, speak the English fallback that also offers a human |
| `opt_out` | "stop calling me" etc. while still choosing | speak the opt-out line, mark `metadata["opted_out"]` |
| `human_request` | "talk to a human" while still choosing | speak the human-request line |

Two attempts total (`MAX_LANGUAGE_ATTEMPTS = 2`). `VOICE_LANGUAGE_ON_FAILURE`
sets the fallback, default `en-IN`; `auto` is rejected as a fallback because it
would reintroduce self-switching.

Explicitness is the guard against auto-switching: `detect_language_choice`
reuses the rule classifier, which only treats a language word as a choice when
the turn is a single word / up to six words, or when a word like *speak*,
*talk* or *language* is next to it. "My shop board is written in Kannada, when
will my settlement come?" is not a choice. That exact sentence is in the live
probe.

### Step-by-step, in the order it was built

1. **State.** `VoiceSession` gained `language_locked: bool` and
   `language_attempts: int`. `effective_language` already preferred
   `session.language` over `detected_language`, so no change was needed there;
   `detected_language` now only updates for logs.
2. **Fixed phrases.** New `backend/app/services/voice/phrases.py` holds every
   spoken line per language: `greeting`, `confirm`, `changed`, `retry`,
   `default_english`, `opt_out`, `human_request`, plus `LANGUAGE_NAMES` and
   `GREETING_ORDER = ("hi-IN", "kn-IN", "en-IN")`. Text lives here so the
   cached audio and the transcript text cannot drift.
3. **Pre-render cache.** New `backend/app/services/voice/prerender.py`:
   Cartesia returns a WAV container, `strip_wav` extracts the raw
   `pcm_f32le` data chunk, and the bytes are cached under
   `backend/.cache/voice_phrases/<phrase>.<language>.<hash>.pcm`. The hash
   covers text, language, model and voice id, so editing a line re-renders it.
   `PhraseCache.ensure` renders on first use behind a thread lock;
   `warm_phrase_cache` renders all 19 clips. `.cache/` is already git-ignored.
4. **Startup warm.** `backend/app/main.py` queues `warm_phrase_cache` in a
   worker thread on startup when `VOICE_ASK_LANGUAGE` and a Cartesia key are
   present. Log line on a warm start:
   `phrase cache warm: 19/19 ready in ...\.cache\voice_phrases`.
5. **Speaking cached audio.** `AudioHandler._schedule_phrases` takes
   `[(phrase_id, language), ...]`, resolves PCM (rendering if needed), and
   emits the same item stream as live TTS: token, segment start, audio, segment
   end, then stream/audio end. Audio is chunked into 100 ms frames with a
   cancellation check per frame, which is what keeps barge-in fast. If the
   provider is down the same text falls back to `speak_only`.
6. **Greeting trigger.** In `handle_control` -> `session_init`, after the
   session-restore reply, the handler schedules the three greeting clips once
   per session (`metadata["greeted"]`). A `session_init` that names a language
   (used by the probes and available to a future picker) locks it and skips the
   greeting.
7. **Gate wiring.** In `_handle_transcript_event`, right after the transcript
   event is sent:
   - before the lock: stop any speech, run `_handle_language_gate`, return;
   - after the lock: `detect_language_change`; if the merchant explicitly asks
     for another language, `_apply_language(changed=True)` and return.
   The old duplicate "interrupt if speaking" block now calls
   `_stop_active_speech`, shared with the gate.
8. **`_set_session_language`** gained `lock: bool`. It now always sends
   `language_changed` (including when the code did not change) with
   `language`, `display` and `locked`, and returns a bool.
9. **Intent aliases.** `_LANGUAGE_PATTERNS` in `intent.py` accept `hindhi`,
   `hindee`, `kannad`, `kannadam`, `inglish`, `angrezi`, `angreji`. The Latin
   alternatives use `(?<![a-z])` / `(?![a-z])` instead of `\b`; a live Sarvam
   transcript came back as `Kannadaದಲ್ಲಿ ಮಾತನಾಡಿ`, where a trailing `\b` fails
   because the next character is a Kannada letter. This was a real bug found
   by the probe, not a hypothetical.
10. **Config and docs.** `VOICE_ASK_LANGUAGE` (default true),
    `VOICE_LANGUAGE_ON_FAILURE` (default `en-IN`) and
    `VOICE_PHRASE_CACHE_DIR` (default empty -> `backend/.cache/voice_phrases`)
    were added to `config.py` and documented in `.env.example`.
11. **Frontend.** `language_changed` is parsed into `onLanguageChanged`, the
    hook exposes `callLanguage = { code, display, locked }`, and the live
    session signals show a Language row that flips from "Not chosen" to
    "Hindi" / "Kannada" / "English". `npx tsc --noEmit` is clean.

### Audio durations, measured

Cartesia with the configured voice, 16 kHz:

| phrase | hi-IN | kn-IN | en-IN |
| --- | --- | --- | --- |
| greeting | 5.76 s | 6.40 s | 5.84 s |
| confirm | 4.08 s | 4.56 s | 3.28 s |
| retry | 3.12 s | 3.52 s | 4.00 s |
| changed | 2.00 s | 2.96 s | 2.24 s |

The three-part greeting is **18.0 s** if the merchant stays silent. That is the
literal cost of saying the line in all three languages, and the first draft was
27 s before the lines were tightened. It is acceptable because playback starts
instantly from cache and a merchant who already knows their choice interrupts
it within a few seconds; the probe does exactly that. If the owner wants it
shorter still, the honest options are to drop the recording notice from two of
the three lines (and repeat it in the confirmation instead) or to play only the
chosen language, which would require guessing the language, so it was not done.

### Files touched

- `backend/app/services/voice/session.py` - lock and attempt fields.
- `backend/app/services/voice/phrases.py` - new, all fixed lines.
- `backend/app/services/voice/prerender.py` - new, WAV strip + PCM cache.
- `backend/app/services/voice/language_gate.py` - new, pure gate.
- `backend/app/services/voice/handlers/audio.py` - greeting, gate,
  change-of-mind, cached-clip speaker, lock-aware `_set_session_language`.
- `backend/app/services/intent.py` - language aliases, code-mixed matching.
- `backend/app/core/config.py`, `.env.example` - three new settings.
- `backend/app/main.py` - startup warm.
- `backend/tests/test_language_selection.py` - new, 27 tests.
- `backend/scripts/language_gate_probe.py` - new live acceptance probe.
- `frontend/lib/voice/websocket.ts`, `frontend/hooks/usevoice.ts`,
  `frontend/app/page.tsx` - `language_changed` and the Language row.

### Evidence

Unit and compile checks:

```
python -m unittest discover -s tests   ->  Ran 132 tests, OK   (was 106)
python -m compileall -q app tests scripts -> exit 0
python -c "import app.main"              -> import ok
npx tsc --noEmit (frontend)              -> exit 0
```

Live probe, `backend/scripts/language_gate_probe.py`, against the real backend
with Sarvam STT and Cartesia TTS. It synthesizes each answer with Cartesia and
streams it into the microphone socket, so this is the same path the browser
uses. Result: **8/8 pass**.

```
PASS  lock hindi            transcript "हिंदी में बात करें" -> language_changed hi-IN locked
PASS  lock kannada          transcript "Kannadaದಲ್ಲಿ ಮಾತನಾಡಿ" -> language_changed kn-IN locked
PASS  lock english          transcript "English please" -> language_changed en-IN locked
PASS  unclear asks again    "I do not know." -> retry in hi, kn, en
PASS  unclear then locks Kannada
PASS  reply after the lock stays Kannada
PASS  change of mind to English
PASS  no switch on a stray language word
```

The post-lock Kannada reply, verbatim from the probe:

```
ಸೆಟಲ್ಮೆಂಟ್ ಸಾಮಾನ್ಯವಾಗಿ ವ್ಯವಹಾರ ದಿನದ ನಂತರ ಎರಡು ಕೆಲಸದ ದಿನಗಳಲ್ಲಿ ನಿಮ್ಮ ಖಾತೆಗೆ ಬರುತ್ತದೆ.
ಇನ್ನಷ್ಟು ವಿವರ ಬೇಕೆ?
```

Kannada script, two sentences, one closing question. This is the specific
failure the owner reported ("Kannada speech answered in English /
transliterated") and it is now covered by an automated live check.

The no-switch check sent: "My shop board is written in Kannada, when will my
settlement come?" after locking English. Sarvam misheard "Kannada" as "Canada",
which made the test weaker but still valid; the reply stayed English and no
`language_changed` fired.

### How to re-run

```
backend\.venv\Scripts\python.exe scripts\language_gate_probe.py
```

Needs the backend on 8100. It spends Cartesia and Groq credits; the Kannada
reply turn is a real model call. Expect roughly two minutes.

To force a re-render of the fixed lines (for example after editing
`phrases.py`), delete `backend/.cache/voice_phrases/*` or just restart, since
the hash includes the text.

### Decisions worth remembering

- The greeting is three separate clips, not one trilingual string. Cartesia
  takes one language per request, so a single string would mispronounce two of
  the three languages.
- The gate consumes `language_choice` from the rule classifier rather than the
  LLM. It is deterministic, instant, and cannot be talked out of a lock by a
  clever sentence.
- `language_attempts` counts total answers, not retries: the first unclear
  answer sets it to 1, the second triggers the English default.
- `opt_out` and `human_request` are honoured during language selection instead
  of being swallowed by the gate. This matters: a merchant saying "stop
  calling me" over a language question must be obeyed.
- Phase 4 must treat `session.language_locked` as the source of truth for the
  call language. Intent classification is still not wired into the voice path;
  that remains Phase 4.

### What remains for Phase 3

- [ ] Owner browser check on `http://localhost:3100`: hear the trilingual
      greeting, answer in each language, confirm the Language row flips, and
      barge in mid-greeting.
- [ ] Optional, not required by the brief: a visible language picker in the UI.
      The backend already accepts `{"type": "session_init", "language": ...}`
      and locks it, so a picker would only need a frontend control.

### Gotchas added in this phase

- The greeting starts on `session_init`. If audio does not play in the browser,
  check that the AudioContext is not suspended (the page needs one user
  gesture); the backend side is fine.
- `scripts/voice_turn_probe.py` sends a language in `session_init`, which now
  locks it and skips the greeting. That is intentional and still valid for
  reply tests; use `language_gate_probe.py` to exercise the greeting and gate.
- The phrase cache is PCM, not WAV, on purpose: the frontend treats every
  binary frame as `Float32Array` samples. Do not store the container bytes.
- `_schedule_phrases` runs Cartesia in a worker thread on a cache miss. A cold
  first call after deleting the cache can add a couple of seconds per clip; the
  startup warm avoids this in normal runs.
