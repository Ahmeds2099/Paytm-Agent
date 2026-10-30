# Agent Implementation Prompt — Paytm Voice Teammate: Demo Layer + Admin Dashboard

> **Paste this entire document to a new agent session.**
> The agent should read `context.md`, `HANDOFF.md`, and `BUILD_LOG.md` first before making any changes.

---

## 0. Read these files FIRST before touching anything

```
G:\Coding\Projects\paytm-voice-teammate\context.md
G:\Coding\Projects\paytm-voice-teammate\HANDOFF.md
G:\Coding\Projects\paytm-voice-teammate\BUILD_LOG.md
```

Latest commit: `94cd620`. Tests: 157/157. tsc clean. Three servers must be running for live testing:
- Backend: `uvicorn app.main:app --host 127.0.0.1 --port 8100`  (from `backend/`, venv active)
- Mock API: `python -m mock_paytm` (from project root, backend venv)
- Frontend: `npm run dev` (from `frontend/`)

---

## 1. What you are building (overview)

Three interconnected features that together make this a complete, demo-ready product:

1. **Demo Scenarios** — Six fully-scripted merchant personas, each with a predefined issue, complete conversation flow, and outcome (ticket, resolution, escalation, or closure).
2. **Paytm-branded Landing + Merchant Login** — Replace the current generic landing page with a Paytm-coloured page where a user "logs in" by selecting a merchant persona, simulating an inbound call.
3. **Admin Dashboard** — Replace the Architecture tab with a live call-log panel for the sales team, showing every call's outcome, escalation status, and attention flags in real time.

Do all three in order. Run tests and TypeScript check after each. Never break the 157-test baseline.

---

## 2. Feature 1 — Demo Scenarios (backend + mock data)

### 2.1 Six merchant personas

Create these exactly in `mock_paytm/seed_data.py` and `backend/app/services/demo_scenarios.py`.

Each persona has:
- `merchant_id` — unique string
- `name`, `business_name`, `phone`, `language` — for display
- `scenario_id` — key that maps to a script
- `avatar_emoji` — for the frontend card
- Pre-loaded data in QR_STORE / SETTLEMENT_STORE / SOUNDBOX_STORE / REFUND_STORE

---

#### Persona 1 — Ravi Kumar (QR Not Working)
```
merchant_id: MID001
name: Ravi Kumar
business: Ravi General Store, Bengaluru
language: kn-IN
avatar: 🏪
scenario: qr_inactive
```
**Mock data:** QR status = `inactive`, issue = `QR not rendering`  
**Full conversation flow:**
1. Agent greets in Kannada (language pre-locked from persona).
2. Ravi says: "ನನ್ನ QR ಕೋಡ್ ಕೆಲಸ ಮಾಡ್ತಿಲ್ಲ" ("My QR code is not working").
3. Agent calls `lookup_qr(MID001)` → gets inactive status.
4. Agent says: "ನಿಮ್ಮ QR ಕೋಡ್ ಸಕ್ರಿಯವಾಗಿಲ್ಲ. ನಾವು ಈಗಾಗಲೇ ನಿಮ್ಮ ಸಮಸ್ಯೆಯನ್ನು ನೋಂದಾಯಿಸಿದ್ದೇವೆ." ("Your QR is not active. We have registered your issue.")
5. Agent calls `raise_ticket(MID001, "qr_inactive")` → returns `TICKET-001`.
6. Agent says: "ಟಿಕೆಟ್ #TICKET-001 ರಚಿಸಲಾಗಿದೆ. ತಂಡವು 4 ಗಂಟೆಗಳಲ್ಲಿ ಪರಿಹರಿಸುತ್ತದೆ." ("Ticket created. Team will resolve in 4 hours.")
7. Agent closes: "ಇನ್ನೇನಾದರೂ ಸಹಾಯ ಬೇಕೇ?" → Ravi says no → Agent says goodbye, logs call as `resolved:ticket_raised`.

---

#### Persona 2 — Sunita Devi (Settlement Delayed)
```
merchant_id: MID002
name: Sunita Devi
business: Sunita Sarees, Patna
language: hi-IN
avatar: 👗
scenario: settlement_pending
```
**Mock data:** TXN002 = pending ₹750, expected tomorrow  
**Full conversation flow:**
1. Agent greets in Hindi.
2. Sunita says: "मेरा पेमेंट अभी तक नहीं आया" ("My payment hasn't come yet").
3. Agent calls `settlement_status(TXN002)` → pending, expected tomorrow.
4. Agent says: "आपका ₹750 का सेटलमेंट कल तक आ जाएगा। अभी प्रोसेसिंग में है।" ("Your ₹750 settlement will arrive by tomorrow. Currently processing.")
5. Sunita: "लेकिन मुझे आज पैसे चाहिए" ("But I need money today").
6. Agent: "मैं समझती हूँ। मैं आपकी urgency नोट करती हूँ। क्या आप चाहेंगी कि मैं इसे escalate करूं?" 
7. Sunita: "हाँ" → Agent raises priority ticket `TICKET-002`, logs call as `resolved:ticket_raised_priority`.

---

#### Persona 3 — Mohammed Farooq (Soundbox Offline)
```
merchant_id: MID003
name: Mohammed Farooq
business: Farooq Electronics, Hyderabad
language: en-IN
avatar: 📱
scenario: soundbox_offline
```
**Mock data:** SB002 = offline, issue = `Check power and WiFi`  
**Full conversation flow:**
1. Agent greets in English.
2. Farooq says: "My soundbox is not making any sound when customers pay."
3. Agent calls `soundbox_health(SB002)` → offline.
4. Agent: "Your soundbox SB002 appears offline. Let's troubleshoot — can you check if it's plugged in and your WiFi is working?"
5. Farooq: "Yes it is plugged in."
6. Agent: "Please press the reset button on the back for 5 seconds. This usually fixes connectivity issues."
7. Farooq: "It beeped! It's working now."
8. Agent: "Great! Your soundbox is back online. I've logged this as resolved." → Call ends, logs as `resolved:self_service`.
9. *(Alternate ending if not fixed)*: Agent raises `TICKET-003`, logs as `resolved:ticket_raised`.

---

#### Persona 4 — Lakshmi Venkat (Refund Not Initiated)
```
merchant_id: MID004
name: Lakshmi Venkat
business: Lakshmi Textiles, Chennai
language: en-IN
avatar: 🧵
scenario: refund_pending
```
**Mock data:** TXN004 = completed ₹2,400, no refund yet  
**Full conversation flow:**
1. Agent greets.
2. Lakshmi: "My customer paid ₹2,400 by mistake and wants a refund but I don't know how to do it."
3. Agent: "I can initiate that refund for you right now. The transaction ID is TXN004 for ₹2,400 — is that correct?"
4. Lakshmi: "Yes."
5. Agent calls `trigger_refund(TXN004, 2400)` → returns `REF-TXN004-001, status: initiated`.
6. Agent: "The refund of ₹2,400 has been initiated. Refund ID is REF-TXN004-001. Your customer will receive it within 5-7 business days."
7. Agent: "Is there anything else?" → No → Call ends, logs as `resolved:refund_initiated`.

---

#### Persona 5 — Amit Sharma (Escalation — Repeated Complaint)
```
merchant_id: MID005
name: Amit Sharma
business: Amit Kirana, Delhi
language: hi-IN
avatar: 🏬
scenario: repeated_escalation
```
**Mock data:** 2 prior tickets for same settlement issue (add to seed data)  
**Full conversation flow:**
1. Agent greets in Hindi.
2. Amit: "यह तीसरी बार है जब मैं call कर रहा हूँ! पैसे अभी तक नहीं आए!" ("This is the third time I'm calling! Money still hasn't come!")
3. Agent classifies as `repeat_complaint` → count = 1.
4. Agent: "मुझे खेद है, मैं समझता हूँ यह निराशाजनक है।" Shows empathy.
5. Amit: "आप लोगों से कुछ नहीं होता! मुझे senior से बात करनी है!" 
6. Agent classifies as `human_request` → session.escalated = True.
7. Agent: "ठीक है, मैं आपको अभी एक वरिष्ठ सहयोगी से जोड़ता हूँ।"
8. Escalation event fires → admin dashboard shows red "ATTENTION REQUIRED" flag.
9. Call logs as `escalated:human_requested`.

---

#### Persona 6 — Priya Nair (Opt Out — Do Not Call)
```
merchant_id: MID006
name: Priya Nair
business: Priya Beauty Parlour, Kochi
language: en-IN
avatar: 💄
scenario: opt_out
```
**Full conversation flow:**
1. Agent greets.
2. Priya: "Please remove my number. I don't want these calls."
3. Agent classifies `opt_out` immediately.
4. Agent: "Absolutely. I've noted your request and will ensure you receive no further calls from us. Thank you, Priya. Goodbye."
5. Call ends immediately. Logs as `closed:opt_out`. Admin sees `OPT-OUT` badge on this record.

---

### 2.2 Ticket system (mock_paytm/routes/tickets.py)

Add a new mock route:

```
POST /ticket
Body: { merchant_id, issue_type, description, priority }
Returns: { ticket_id, status: "open", eta_hours, created_at }
```

Ticket types and their ETAs:
- `qr_inactive` → 4 hours
- `settlement_delayed` → 24 hours  
- `soundbox_offline` → 8 hours
- `refund_failed` → 48 hours
- `escalation` → 1 hour (priority)

Add `raise_ticket(merchant_id, issue_type, description="", priority="normal")` to `paytm_tools.py`.
Add `ticket_summary(ticket_result)` to `spoken_summary_for_language`.

---

### 2.3 Call log backend (backend/app/services/call_log.py)

Create `backend/app/services/call_log.py`. This logs every call to `backend/.audit/call_log.jsonl`.

Each call record:
```json
{
  "call_id": "uuid",
  "merchant_id": "MID001",
  "merchant_name": "Ravi Kumar",
  "session_id": "...",
  "started_at": "ISO timestamp",
  "ended_at": "ISO timestamp or null",
  "duration_seconds": 45,
  "language": "kn-IN",
  "scenario": "qr_inactive",
  "outcome": "resolved:ticket_raised",
  "ticket_id": "TICKET-001",
  "escalated": false,
  "opt_out": false,
  "attention_required": false,
  "tool_calls": ["lookup_qr", "raise_ticket"],
  "intent_sequence": ["qr_code_issue", "out_of_scope"],
  "turn_count": 6,
  "summary": "Merchant QR was inactive. Ticket TICKET-001 raised. ETA 4 hours."
}
```

Outcome codes:
- `resolved:ticket_raised` — ticket created, problem handed off
- `resolved:ticket_raised_priority` — same but urgent
- `resolved:self_service` — merchant fixed it themselves during call
- `resolved:refund_initiated` — refund successfully triggered
- `resolved:info_provided` — agent answered question, no action needed
- `escalated:human_requested` — merchant asked for human
- `escalated:repeated_complaint` — auto-escalated after 2+ complaints
- `closed:opt_out` — merchant asked to not be called
- `closed:no_response` — merchant didn't respond / hung up
- `open` — call still in progress

Add REST endpoint `GET /admin/calls` and `GET /admin/calls/{call_id}` in `backend/app/routers/admin.py`.

Wire `call_log.py` into `audio.py`:
- On session_init with a known merchant persona → log call_start
- On session disconnect / escalation / opt_out / call close → log call_end with outcome

---

## 3. Feature 2 — Paytm-branded Frontend + Merchant Login

### 3.1 Color system (globals.css / index.css)

Replace ALL colors with the official Paytm palette:

```css
--paytm-blue: #00B9F1;        /* Primary brand blue */
--paytm-dark-blue: #002970;   /* Deep navy for headers */
--paytm-light-blue: #E8F8FD;  /* Backgrounds, cards */
--paytm-accent: #00D1FF;      /* Hover states, highlights */
--paytm-text: #1A1A2E;        /* Primary text */
--paytm-text-muted: #4A5568;  /* Secondary text */
--paytm-white: #FFFFFF;
--paytm-success: #00C48C;     /* Resolved / OK */
--paytm-warning: #FFB400;     /* Pending / Attention */
--paytm-danger: #FF4757;      /* Escalated / Error */
--paytm-surface: #F0FBFF;     /* Page background */
```

All gradients use blue tones. No purple, no generic grey. Remove all existing color tokens.

---

### 3.2 Landing page redesign (frontend/app/page.tsx)

**When no merchant is selected (initial state):**

Replace the current voice orb + connect button layout with:

```
┌─────────────────────────────────────────────────────────┐
│  [Paytm logo SVG]   Paytm Voice Teammate               │
│  AI-powered merchant support · 24/7 · 3 languages       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Choose who is calling:                                │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │  🏪      │ │  👗      │ │  📱      │               │
│  │ Ravi     │ │ Sunita   │ │ Farooq   │               │
│  │ Kumar    │ │ Devi     │ │          │               │
│  │ Kirana   │ │ Sarees   │ │Electricals│              │
│  │ 🇮🇳 kn   │ │ 🇮🇳 hi   │ │ 🇮🇳 en   │               │
│  │ QR issue │ │Settlement│ │ Soundbox │               │
│  └──────────┘ └──────────┘ └──────────┘               │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │  🧵      │ │  🏬      │ │  💄      │               │
│  │ Lakshmi  │ │ Amit     │ │ Priya    │               │
│  │ Textiles │ │ Sharma   │ │ Nair     │               │
│  │ 🇮🇳 en   │ │ 🇮🇳 hi   │ │ 🇮🇳 en   │               │
│  │ Refund   │ │Escalation│ │ Opt out  │               │
│  └──────────┘ └──────────┘ └──────────┘               │
│                                                         │
│        Simulate an inbound merchant call ↑              │
└─────────────────────────────────────────────────────────┘
```

Each card shows:
- Avatar emoji (large, centered)
- Merchant name (bold)
- Business name (muted)
- Language flag + language code
- Issue preview (e.g. "QR issue", "Settlement delay")
- Hover: card lifts, blue border glow, subtle scale
- Click: transitions to active call view

**Hero section above the cards:**
- Left: Paytm logo + product name + tagline
- Right: 3 stat pills → `3 Languages` · `6 Demo Scenarios` · `Live AI Agent`
- Background: soft gradient from `--paytm-light-blue` to white

---

### 3.3 Active call view (after merchant selected)

After clicking a merchant card, the page transitions to a full-page call simulation:

**Left panel (40%) — Merchant profile:**
```
┌──────────────────────────┐
│  📞 Call in progress...  │
│                          │
│     [Avatar Emoji]       │
│    Ravi Kumar            │
│    Ravi General Store    │
│    📍 Bengaluru          │
│    📱 +91 98xxx xxxx     │
│    🗣️  Language: Kannada │
│                          │
│  ─── Account Info ───    │
│  Merchant ID: MID001     │
│  Member since: Jan 2023  │
│  Total transactions: 847 │
│  Last transaction: Today │
│                          │
│  ─── Active Issue ───    │
│  QR Code Inactive        │
│  [View details]          │
│                          │
│  [End Call] [Escalate]   │
└──────────────────────────┘
```

**Right panel (60%) — Voice interface:**
- The existing voice orb (restyled in Paytm blue)
- Conversation transcript (scrollable)
- Session signals (language, connection, tools)
- Tool call log (live)

Remove the demo document selector — it's not relevant for the merchant agent.

---

### 3.4 Session init on merchant select

When a merchant card is clicked:
1. Send `session_init` with:
   - `client_id`: merchant's `merchant_id`
   - `language`: merchant's language code (this locks the language immediately, skipping the greeting gate — the agent already knows who is calling)
   - `merchant_profile`: JSON with name, business, scenario, phone
2. Frontend stores selected merchant in React state.
3. Transition animation: card expands/fades into call view.
4. Agent speaks a language-specific opening (different from the language-selection greeting):
   - en-IN: "Hello Ravi! This is Paytm support calling. I can see you've been having an issue with your QR code. Can you tell me more about what's happening?"
   - hi-IN: "नमस्ते! यह Paytm support से call है..."
   - kn-IN: "ನಮಸ್ಕಾರ! ಇದು Paytm support..."
   - These are pre-scripted opening phrases, not from the language gate.

Add these phrases to `phrases.py`:
```python
"demo_open_qr": { "en-IN": "...", "hi-IN": "...", "kn-IN": "..." }
"demo_open_settlement": { "en-IN": "...", ... }
"demo_open_soundbox": { "en-IN": "...", ... }
"demo_open_refund": { "en-IN": "...", ... }
"demo_open_general": { "en-IN": "...", ... }
```

---

### 3.5 Merchant data endpoint

Add `GET /demo/merchants` to `backend/app/routers/demo.py`:

```json
[
  {
    "merchant_id": "MID001",
    "name": "Ravi Kumar",
    "business_name": "Ravi General Store",
    "city": "Bengaluru",
    "phone": "+91 98441 12345",
    "language": "kn-IN",
    "language_display": "Kannada",
    "avatar": "🏪",
    "scenario_id": "qr_inactive",
    "scenario_label": "QR Not Working",
    "member_since": "Jan 2023",
    "total_transactions": 847,
    "account_balance": "₹12,450",
    "open_tickets": 1
  },
  ... (all 6)
]
```

Frontend fetches this on load and renders the cards.

---

## 4. Feature 3 — Admin Dashboard (replace Architecture tab)

### 4.1 Tab rename

In `frontend/app/page.tsx`, rename the "Architecture" tab to "Admin". Remove `<ArchitectureDashboard />`. Replace with `<AdminDashboard />`.

---

### 4.2 AdminDashboard component (frontend/components/dashboard/admindashboard.tsx)

Layout:

```
┌─────────────────────────────────────────────────────────────┐
│  Admin Dashboard                        [🔴 Live] [Refresh] │
│  Paytm Voice Agent · Call Monitoring Panel                  │
├──────┬──────┬────────┬───────────┬────────────────────────  │
│ ALL  │ OPEN │ CLOSED │ ESCALATED │ NEEDS ATTENTION (badge)  │
├──────┴──────┴────────┴───────────┴────────────────────────  │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🟢 Ravi Kumar        QR Fixed     kn  2m 14s  RESOLVED  │ │
│ │    Ravi General Store · MID001     Ticket #TICKET-001   │ │
│ │    Tools: lookup_qr, raise_ticket  4 turns              │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ 🟡 Sunita Devi       Settlement   hi  1m 42s  TICKET↑   │ │
│ │    Sunita Sarees · MID002          Priority ticket       │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ 🔴 Amit Sharma       Escalated    hi  3m 02s  HUMAN ⚠️   │ │
│ │    Amit Kirana · MID005            ATTENTION REQUIRED   │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ ⚫ Priya Nair         Opt-out     en  0m 28s  OPT-OUT   │ │
│ │    Priya Beauty · MID006           DNC registered       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [Click any row to expand full call detail]                  │
└─────────────────────────────────────────────────────────────┘
```

**Status colour coding:**
- 🟢 Green dot = Resolved (any resolved: outcome)
- 🟡 Yellow dot = Open / In progress / Ticket raised
- 🔴 Red dot = Escalated or Needs attention
- ⚫ Grey dot = Closed with no resolution (opt-out, no response)

**Row expanded view (click to expand):**
```
┌────────────────────────────────────────────────────────────┐
│  📞 Ravi Kumar  ·  MID001  ·  kn-IN  ·  2m 14s            │
│  Started: 10:32:04  Ended: 10:34:18  2026-10-30            │
│                                                             │
│  Outcome: resolved:ticket_raised                           │
│  Ticket:  #TICKET-001 · QR Inactive · ETA 4 hours         │
│                                                             │
│  Intent sequence:  qr_code_issue → out_of_scope            │
│  Tool calls:       lookup_qr (ok, 212ms)                   │
│                    raise_ticket (ok, 88ms)                  │
│                                                             │
│  Turns: 6  ·  Interruptions: 0  ·  Escalated: No          │
│  Attention required: No                                     │
│                                                             │
│  Summary: Merchant QR MID001 was inactive. Ticket          │
│  TICKET-001 raised. Team will resolve within 4 hours.      │
└────────────────────────────────────────────────────────────┘
```

**Stats strip at the top (above the tab bar):**
```
 Total Calls: 12  │  Resolved: 8  │  Escalated: 2  │  Open: 1  │  Opt-out: 1
```

---

### 4.3 Live updates (WebSocket or polling)

- Admin dashboard polls `GET /admin/calls?since=<timestamp>` every 5 seconds.
- For the active call (if any), the row shows `🟡 LIVE · X turns` and updates in real time.
- When a call ends, the row transitions from yellow to the final outcome colour with a brief animation.

---

### 4.4 Attention Required logic

A call is flagged `attention_required: true` and gets the ⚠️ badge when:
- `escalated: true` AND outcome is `escalated:human_requested`
- `repeat_complaint_count >= 2` at end of call
- Call ended with `closed:no_response` after the agent spoke for > 30 seconds
- A tool call returned `status: error` and the call ended without resolution

These flags are set by `call_log.py` when `log_call_end()` is called.

---

## 5. Paytm logo SVG

Use this inline SVG for the Paytm wordmark (simplified, correct colors):

```svg
<svg viewBox="0 0 120 32" xmlns="http://www.w3.org/2000/svg">
  <rect width="120" height="32" rx="4" fill="#00B9F1"/>
  <text x="8" y="23" font-family="Arial Black, sans-serif" 
        font-size="18" font-weight="900" fill="white">paytm</text>
</svg>
```

Place this in `frontend/components/ui/PaytmLogo.tsx` as a React component.

---

## 6. Exact file changes required

### New files to create:
```
mock_paytm/routes/tickets.py
backend/app/services/call_log.py
backend/app/services/demo_scenarios.py
backend/app/routers/admin.py
backend/app/routers/demo.py
frontend/components/dashboard/admindashboard.tsx
frontend/components/ui/PaytmLogo.tsx
frontend/components/ui/MerchantCard.tsx
frontend/components/ui/CallView.tsx
```

### Files to modify:
```
mock_paytm/seed_data.py          — add Personas 3-6 data
mock_paytm/__main__.py           — register tickets router, demo router
backend/app/services/paytm_tools.py  — add raise_ticket(), extend spoken_summary_for_language
backend/app/services/voice/phrases.py — add demo_open_* phrases
backend/app/services/voice/handlers/audio.py — wire call_log, demo persona opening
backend/app/main.py              — register admin router, demo router
frontend/app/page.tsx            — merchant selector landing, active call view, Admin tab
frontend/app/globals.css         — Paytm color system, full retheme
frontend/hooks/usevoice.ts       — merchant profile state, call log state
frontend/lib/voice/types.ts      — MerchantProfile, CallLogEntry types
frontend/lib/voice/websocket.ts  — no changes needed (tool_call, escalation already handled)
```

---

## 7. Implementation order (do exactly this order)

1. **Seed data + ticket route** — Add personas 3-6 to seed_data.py, create tickets.py route, test `POST /ticket` manually.
2. **Demo scenarios** — Create demo_scenarios.py with all 6 persona definitions + scenario scripts.
3. **raise_ticket tool** — Add to paytm_tools.py, add ticket_summary(), add to _dispatch_intent in audio.py.
4. **call_log.py** — Create the call log service, wire into audio.py session lifecycle, create /admin/calls endpoint.
5. **Backend tests** — Add tests for raise_ticket, ticket spoken summaries, and call log writes. Run all 157+ tests.
6. **Paytm CSS** — Replace color system in globals.css, verify no broken styles.
7. **PaytmLogo + MerchantCard components** — Create isolated components first.
8. **Landing page** — Fetch /demo/merchants, render cards, wire click → session_init with merchant profile.
9. **Active call view** — Left panel (merchant profile) + right panel (existing voice UI).
10. **Demo opening phrases** — Wire scenario-specific opening phrase on session_init.
11. **AdminDashboard component** — Build with mock data first, then wire to /admin/calls polling.
12. **TypeScript check** — `npx tsc --noEmit` must be clean.
13. **Full demo run** — Walk through all 6 scenarios end-to-end in the browser. Confirm each reaches its expected outcome.
14. **Update docs** — BUILD_LOG.md entry, context.md session notes, HANDOFF.md.
15. **Commit** — Single commit: `feat: demo scenarios + merchant login + admin dashboard`.

---

## 8. Acceptance criteria (how to know it's done)

- [ ] All 6 merchant cards appear on the landing page with correct colors and labels.
- [ ] Clicking Ravi Kumar starts a call in Kannada, greets him by name, and eventually speaks a tool result in Kannada.
- [ ] Clicking Amit Sharma ends with an escalation banner and an ⚠️ row in the Admin tab.
- [ ] Clicking Priya Nair ends the call in < 30 seconds and logs OPT-OUT in Admin.
- [ ] Admin tab shows all completed calls with correct outcome colors and no attention badge for resolved calls.
- [ ] `tsc --noEmit` is clean.
- [ ] `python -m unittest discover -s tests` passes all tests (new count ≥ 170).
- [ ] No console errors in the browser.
- [ ] Page uses ONLY Paytm blue / navy / white — zero purple, orange, or generic grey.

---

## 9. Do NOT change

- The WebSocket audio pipeline internals (PCM encoding, barge-in, interruption logic).
- The STT/TTS provider code (`sarvam.py`, `deepgram.py`, `cartesia.py`).
- The language gate logic (`language_gate.py`) — though the demo skips it by pre-locking via session_init.
- The 157 existing tests — all must still pass.
- `backend/.env` — never commit secrets.

---

## 10. Notes on demo scenario behavior

- The demo scenarios define the **expected happy path**. The AI is not strictly scripted — it will respond naturally. The seed data ensures the tool calls return the right fixture so the AI can articulate the correct outcome.
- The `demo_scenarios.py` module provides a lookup: `get_scenario(merchant_id)` → scenario metadata. Audio.py uses this on session_init to speak the correct opening phrase and inject scenario context into the system prompt.
- The system prompt for demo calls should include: `"You are assisting {merchant_name} from {business_name}. Their registered issue is {scenario_label}. Use the tools available to look up their account and resolve the issue. After resolving, confirm the resolution and close the call warmly."`
- For Persona 5 (Amit — escalation), the conversation must reach escalation naturally. The seed data can include `prior_complaint_count: 2` so the intent classifier immediately treats the first complaint as a `repeat_complaint`.
- For Persona 6 (Priya — opt-out), the opening phrase should NOT mention her issue — just a neutral greeting. Her first utterance triggers opt_out classification.
