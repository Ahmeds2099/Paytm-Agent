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
