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
