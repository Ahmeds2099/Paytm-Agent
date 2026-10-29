import httpx
from time import perf_counter

COMPANION_URL = "http://127.0.0.1:8420"

def ask_companion(task: str, timeout: float = 6.0) -> dict:
    """
    Synchronous client that sends a plain task string to Via Companion at 127.0.0.1:8420.
    Returns structured result dictionary.
    """
    start = perf_counter()
    try:
        resp = httpx.post(
            f"{COMPANION_URL}/chat",
            json={"text": task},
            headers={"Content-Type": "application/json"},
            timeout=httpx.Timeout(timeout, connect=2.0),
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "status": "executed",
            "summary": data.get("reply", ""),
            "action": data.get("action", None),
            "duration_ms": round((perf_counter() - start) * 1000),
        }

    except (httpx.RequestError, httpx.HTTPStatusError):
        return {"status": "unavailable", "summary": "", "action": None, "duration_ms": 0}
    except Exception:
        return {"status": "failed", "summary": "", "action": None, "duration_ms": 0}
