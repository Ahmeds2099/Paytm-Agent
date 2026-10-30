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
- `backend/app/services/intent.py` classifies a turn. Rules run first for
  `opt_out`, `human_request`, `callback_request`, `language_choice`,
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
3. **The intent taxonomy does not match brief section 5.3.** This is the
   biggest thing to reconcile before Phase 4. Built labels:

   | Brief label | Built? | Built equivalent |
   | --- | --- | --- |
   | language_choice | yes | same |
   | settlement_query | yes | same |
   | device_issue | yes | same |
   | ticket_request | **no** | not modelled |
   | loan_interest | yes | same |
   | device_offer_interest | **no** | not modelled |
   | policy_question | **no** | not modelled |
   | callback_request | yes | same |
   | human_request | yes | same |
   | repeat_complaint | **no** | not modelled |
   | objection | yes | same |
   | opt_out | yes | same |
   | confirmation_yes / confirmation_no | yes | same |
   | smalltalk | **no** | folded into `other` |
   | out_of_scope | **no** | folded into `other` |

   Built labels with no brief counterpart: `transaction_issue`,
   `qr_code_issue`, `refund_query`, `soundbox_issue`, `charges_query`,
   `onboarding_kyc`. They were added because they are the questions merchants
   actually ask on a Paytm call, but Phase 4 escalation rules in the brief key
   off the brief's labels. Recommendation: extend the taxonomy at the start of
   Phase 4, keep the existing labels as sub-labels or aliases, and update
   `backend/tests/data/intent_examples.py` plus `INTENTS` together.
4. **Language is still `auto`.** Phase 3 owns ask-and-lock. Until then, `auto`
   can still follow the merchant from Kannada into English. The Phase 2 prompt
   forbids switching in words, but the session language is not locked.
5. **No trilingual greeting and no recording notice yet.** The brief puts both
   in the Phase 3 greeting. Nothing in the current greeting contradicts it, and
   there is no user-visible "Via" text.

### What comes next, in the brief's order

**Phase 3 - language selection at the start of every call.** Not started.
Checklist from brief section 6:

- [ ] Greeting: one short line in Hindi, Kannada and English that introduces
      the assistant, says the call may be recorded, and asks which language the
      merchant is comfortable in.
- [ ] Classifier returns `language_choice` with a value in `{hi, kn, en}` for
      the language name in any of the three scripts and for common spellings.
      A single-word answer must work. The rule fast path in
      `backend/app/services/intent.py` already extracts all of this; Phase 3
      needs to consume `slots["language"]` and act on it.
- [ ] Confirm once in the chosen language ("Okay, we will continue in
      Kannada"), then persist `session.language`.
- [ ] Use the locked language for speech to text, the system prompt and the TTS
      language field for the rest of the call. The three inputs already exist:
      `session.effective_language`, `build_voice_prompt(language)` and the
      Cartesia `language=` argument.
- [ ] Unclear answer: ask once more, slowly and simply. If still unclear,
      default to English and offer a human.
- [ ] Change of mind: if the merchant explicitly names another language later,
      update the language. Never switch on its own. Explicit requests already
      classify as `language_choice`, so this is a wiring job, not a new model.
- [ ] Pre-generate the greeting and fixed phrases once per language and cache
      them as audio files, per brief section 9. Nothing is cached yet; every
      turn currently synthesizes fresh audio.
- [ ] Acceptance: all three languages end to end, the unclear path works, and
      the language never changes by itself.

Likely files: `backend/app/services/voice/session.py` (a `language_locked`
flag), `backend/app/services/voice/handlers/audio.py` (greeting, gate,
`language_changed`), `backend/app/services/voice/language.py` (accept
single-word and cross-script language names), `backend/app/core/prompts.py`
(trilingual greeting + confirmation line), a new
`backend/app/services/voice/prerender.py` for the audio cache, and the frontend
language control so the demo can also select manually.

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
      credits, which is why it was left to the owner.
- [ ] Confirm whether the Phase 4 taxonomy should be reconciled to the brief's
      label list, or whether the built list stays.

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
