# Paytm Voice Teammate

Paytm Voice Teammate is a demo voice-support agent for fictional merchants. It
combines a Next.js web app, a FastAPI voice backend, and a local mock Paytm API
to demonstrate multilingual calls, transaction lookups, interruption handling,
support escalation, and an admin dashboard. It does not connect to real Paytm
accounts or payment systems.

## Requirements

- Python 3.11 or newer
- Node.js and npm
- Provider credentials for voice and AI features (Groq and Sarvam and/or
  Cartesia). Qdrant credentials are needed for document ingestion and retrieval.

## Run locally

From the repository root, create the backend environment, install dependencies,
and copy the sample configuration:

```powershell
python -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item .env.example backend\.env
```

Set the required provider credentials in `backend\.env`. Never commit `.env` or
put credentials in source files.

Start each service in its own terminal:

```powershell
# Terminal 1: from the repository root
.\backend\.venv\Scripts\Activate.ps1
python -m mock_paytm
```

```powershell
# Terminal 2
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8100 --log-level warning
```

```powershell
# Terminal 3
cd frontend
npm install
npm run dev
```

Open [http://localhost:3100](http://localhost:3100). The backend health check is
available at [http://127.0.0.1:8100/health](http://127.0.0.1:8100/health).

## Tests

Run the backend tests from the `backend` directory:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Run the frontend type check and lint from the `frontend` directory:

```powershell
npx tsc --noEmit
npm run lint
```
