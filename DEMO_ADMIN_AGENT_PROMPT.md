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
2. **Paytm-branded Landing + Merchant Login** — Replace the current generic landing page with a Paytm-coloured page where a user selects a merchant persona to simulate a Paytm-initiated outbound call.
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

#### Persona 4 — Lakshmi Venkat (Refund Not Initiated) ⭐ HERO DEMO
```
merchant_id: MID004
name: Lakshmi Venkat
business: Lakshmi Textiles, Chennai
avatar: 🧵
scenario: refund_pending
```
**This is the hero demo scenario — make it the most polished, cleanest end-to-end flow.**  
**Mock data:** TXN004 = completed ₹2,400, no refund yet  
**Full conversation flow:**
1. Agent runs the normal language gate greeting: "Hello and welcome to Paytm. Would you be comfortable in English, Hindi or Kannada?"
2. Lakshmi chooses English.
3. Agent confirms in English and asks how it can help.
4. Lakshmi: "My customer paid ₹2,400 by mistake and wants a refund but I don't know how to do it."
5. Agent: "I can initiate that refund for you right now. The transaction ID is TXN004 for ₹2,400 — is that correct?"
6. Lakshmi: "Yes."
7. Agent calls `trigger_refund(TXN004, 2400)` → returns `REF-TXN004-001, status: initiated`.
8. Agent: "The refund of ₹2,400 has been initiated. Refund ID is REF-TXN004-001. Your customer will receive it within 5-7 business days."
9. Agent: "Is there anything else?" → Lakshmi: No → Agent closes warmly, logs as `resolved:refund_initiated`.

**Demo tip:** This scenario has the clearest outcome — money back, happy merchant. Lead with this one in every presentation.

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

#### Persona 6 — Priya Nair (Promotional Loan Offer — Opt Out)
```
merchant_id: MID006
name: Priya Nair
business: Priya Beauty Parlour, Kochi
language: en-IN
avatar: 💄
scenario: opt_out
```
**Full conversation flow:**
1. Paytm initiates the outbound call. The agent runs the normal language gate, then introduces the promotional loan offer; it does not imply Priya called Paytm.
2. Agent: "We're calling from Paytm with a promotional loan offer for your business. Would you be interested in hearing more?"
3. Priya: "No, I want to opt out of this loan offer. Please remove my number."
4. Agent classifies `opt_out` immediately (before treating "No" as a generic refusal), records the opt-out against this merchant, and stops all promotional discussion.
5. Agent acknowledges in Priya's chosen language that her number has been marked not to receive further promotional calls, then ends the call.
6. Logs as `closed:opt_out`. Admin shows an `OPT-OUT` badge and the recorded request on this call.

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

### 3.2 Landing page update (frontend/app/page.tsx)

**IMPORTANT: Do NOT change the existing page layout or component structure.** The current landing page has a hero section, a feature/stats strip, and a document cards section. Keep all of that exactly as it is. Only change:

1. **All copy text** — replace every reference to the generic voice assistant with Paytm-specific content:
   - Hero headline: `"Paytm Voice Teammate"` → subheadline: `"AI-powered outbound support for merchants. Speaks English, Hindi & Kannada."`
   - Feature strip: `"Real-time STT"` → `"Instant Transcription"`, `"Emotion Aware"` → `"3 Languages"`, etc. — keep the same strip layout, just update the label text to reflect Paytm agent features (QR support, settlement queries, soundbox help, multilingual)
   - Any `"Via"` branding → `"Paytm"`

2. **Document cards section** → **Demo Persona cards section**:
   - Replace the document upload cards / demo document cards with 6 merchant persona cards (same card grid layout as the existing document list)
   - Each card shows: avatar emoji, merchant name, business name, issue label
   - The "Upload Document" button becomes `"Start Demo Call"`
   - The card data comes from `GET /demo/merchants`

3. **"Start Agent" / "Connect" button behaviour change**:
   - Currently clicking Connect starts the agent immediately.
   - New behaviour: clicking Connect (or clicking a persona card) first opens a **persona picker modal** (a small overlay/sheet) that lists the 6 merchant cards.
   - The user selects one persona → modal closes → **then** the agent connects as normal.
   - The selected persona's `merchant_id` and `name` are stored in React state and shown in the session-signals panel ("Simulating: Lakshmi Venkat").
   - After connecting, `session_init` is sent with `client_id: merchant_id` and `merchant_profile` metadata — **do NOT pass `language`, `language_code`, or document IDs** (see Section 3.4).

```
Persona picker modal layout:
┌──────────────────────────────────────────────┐
│  Choose a merchant to call                 ✕  │
│  The agent will load this merchant's data     │
├──────────────────────────────────────────────┤
│  ┌────────┐ ┌────────┐ ┌────────┐           │
│  │  🧵   │ │  🏪   │ │  👗   │           │
│  │Lakshmi│ │  Ravi │ │Sunita │           │
│  │Refund ★│ │QR issue│ │Settle │           │
│  └────────┘ └────────┘ └────────┘           │
│  ┌────────┐ ┌────────┐ ┌────────┐           │
│  │  📱   │ │  🏬   │ │  💄   │           │
│  │Farooq │ │  Amit │ │ Priya │           │
│  │Soundbox│ │Escalate│ │Opt-out│           │
│  └────────┘ └────────┘ └────────┘           │
│                                              │
│  ★ = Recommended: start here for a demo     │
└──────────────────────────────────────────────┘
```

Lakshmi (Persona 4, refund ⭐) is highlighted as the recommended starting persona.

---

### 3.3 Active call view (after merchant selected)

After clicking a merchant card, the page transitions to a full-page call simulation:

**Left panel (40%) — Merchant profile:**
```
┌──────────────────────────┐
│  📞 Outbound call in progress... │
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

### 3.4 Session init on merchant select — LANGUAGE GATE MUST STILL RUN

**CRITICAL: Do NOT pass `language` in session_init when a persona is selected.**  
The language gate greeting must run as normal for every persona — the whole point is to demonstrate the multilingual capability. The merchant (person demoing) chooses the language live during the call, just like a real merchant would.

When a merchant persona is selected and Connect is pressed:
1. Send `session_init` with ONLY:
   - `client_id`: the merchant's `merchant_id` (e.g. `"MID004"`)
   - `merchant_profile`: JSON metadata `{ name, business_name, scenario_id, avatar }` — for context injection only
   - **Do NOT include `language` or `language_code`**
2. The agent runs the normal language gate: speaks the greeting "Hello and welcome to Paytm. Would you be comfortable in English, Hindi or Kannada?"
3. The demo user (acting as the merchant) responds with a language.
4. After the language locks, the agent knows the persona context (from `merchant_profile` in session metadata) and proceeds to ask how it can help.
5. Frontend stores selected persona in React state and shows it in the session-signals panel: `"Simulating: Lakshmi Venkat · MID004"`.

This means the language shown on the persona cards is a **hint** ("this persona typically calls in English/Hindi/Kannada") not a constraint. Remove any `language_code` badge from the persona cards — replace with `"Tip: try Hindi"` or just remove the language hint entirely to keep it clean.

**The scenario-specific system prompt context IS injected** (so the AI knows this merchant's issue) but the language is always chosen live by the demo participant.

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
8. **Landing page copy + persona cards** — Keep existing layout. Update all copy. Replace document cards with 6 persona cards fetched from `GET /demo/merchants`.
9. **Persona picker modal** — Wire Connect button to open modal. On persona select: store in state, close modal, connect, send `session_init` with ONLY `client_id` + `merchant_profile`. Do NOT pass `language`.
10. **Session-signals panel** — Show "Simulating: [Name] · [MID]" after persona is selected.
11. **AdminDashboard component** — Build with mock data first, then wire to /admin/calls polling every 5s.
12. **TypeScript check** — `npx tsc --noEmit` must be clean.
13. **Full demo run** — Start with Lakshmi (hero ⭐). Persona picker → select Lakshmi → agent greets in English/Hindi/Kannada (your choice) → mention refund → confirm outcome → verify Admin row shows `resolved:refund_initiated`.
14. **Update docs** — BUILD_LOG.md entry, context.md session notes, HANDOFF.md.
15. **Commit** — Single commit: `feat: demo scenarios + merchant persona picker + admin dashboard`.

---

## 8. Acceptance criteria (how to know it’s done)

- [ ] Existing landing page layout preserved — only copy text and the cards section changed.
- [ ] All 6 persona cards appear in the persona picker modal with avatars, names, and issue labels.
- [ ] Lakshmi Venkat (Persona 4) is visually highlighted as the recommended (⭐) starting persona.
- [ ] Pressing Connect opens the persona picker modal — selecting a persona closes it and starts the call.
- [ ] `session_init` sent with `client_id` and `merchant_profile` only — NO `language`, `language_code`, or document IDs — for every persona.
- [ ] Agent always runs the language gate greeting first ("Hello and welcome to Paytm...") regardless of which persona is selected.
- [ ] Lakshmi hero demo: choose English → mention refund → agent calls trigger_refund → speaks confirmation → Admin shows `resolved:refund_initiated`.
- [ ] Amit escalation demo: choose Hindi → complain twice → escalation banner fires → Admin shows ⚠️ ATTENTION.
- [ ] Priya opt-out demo: after the language gate, the Paytm agent offers a promotional loan; Priya says “No, I want to opt out of this loan offer. Please remove my number.” The request is recorded, promotional discussion stops, the call closes promptly, and Admin shows the OPT-OUT badge.
- [ ] Admin tab shows all calls with correct status dot colours and outcome labels.
- [ ] Session signals panel shows “Simulating: [Name] · [MID]” after persona is selected.
- [ ] `tsc --noEmit` is clean.
- [ ] All tests pass (new count ≥ 170).
- [ ] No browser console errors. Page uses ONLY Paytm blue / navy / white — zero purple or generic grey.

---

## 9. Do NOT change

- The WebSocket audio pipeline internals (PCM encoding, barge-in, interruption logic).
- The STT/TTS provider code (`sarvam.py`, `deepgram.py`, `cartesia.py`).
- The language gate logic (`language_gate.py`) — it must run for every call including demo personas.
- The 157 existing tests — all must still pass.
- `backend/.env` — never commit secrets.

---

## 10. Notes on demo scenario behavior

- The demo scenarios define the **expected happy path**. The AI is not strictly scripted — it responds naturally. The seed data ensures tool calls return the right fixture so the AI can articulate the correct outcome.
- The `demo_scenarios.py` module provides a lookup: `get_scenario(merchant_id)` → scenario metadata. Audio.py uses this on session_init to inject scenario context into the system prompt AFTER the language gate locks.
- System prompt injection after language lock: `"You are calling {merchant_name} from {business_name}. Their registered concern is: {scenario_label}. Use available tools to look up their account and resolve their issue. After resolving, confirm the resolution warmly and close the call."`
- **Language is NEVER pre-loaded from the persona** — the greeting runs first, the merchant picks their language, then the scenario context is used to guide the conversation in that language.
- For Persona 5 (Amit — escalation): seed data includes `prior_complaint_count: 2` so the intent classifier immediately treats the first complaint as `repeat_complaint` and auto-escalates on the second message.
- For Persona 6 (Priya — opt-out): after the language gate locks, the agent must introduce the Paytm-initiated promotional loan offer. Priya's opt-out utterance must trigger the existing high-priority `opt_out` classifier, record the request, stop the offer flow immediately, and close the call. Do not frame this as an inbound support call or merely as a generic "not interested" objection.
- **Hero demo (Persona 4, Lakshmi)**: make this the default pre-selected persona in the picker modal. The ⭐ star badge draws attention to it. During any demo presentation, lead with this scenario first — it shows the complete happy path: greeting → language choice → problem stated → tool called → refund initiated → confirmation → warm close.
