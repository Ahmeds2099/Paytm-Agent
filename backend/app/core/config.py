import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME = "Paytm Voice Teammate Backend"
    VERSION = "0.1.0"

    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEMO_RESET_ENABLED = ENVIRONMENT == "development"
    IS_LITE_DEPLOYMENT = ENVIRONMENT == "production"

    CORS_ORIGINS: list[str] = [
        origin.strip().rstrip("/")
        for origin in os.getenv(
            "CORS_ORIGINS",
            (
                "http://localhost:3100,http://127.0.0.1:3100"
                if ENVIRONMENT == "development"
                else "https://paytm-agent.vercel.app"
            ),
        ).split(",")
        if origin.strip() and origin.strip() != "*"
    ]

    _DEFAULT_CORS_ORIGIN_REGEX = (
        r"^https?://(?:localhost|127\.0\.0\.1|"
        r"10(?:\.\d{1,3}){3}|"
        r"192\.168(?:\.\d{1,3}){2}|"
        r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})"
        r"(?::\d+)?$"
        if ENVIRONMENT == "development"
        else (
            r"^https://paytm-agent-[a-z0-9-]+-"
            r"ahmeds2099s-projects\.vercel\.app$"
        )
    )
    CORS_ORIGIN_REGEX: str | None = (
        os.getenv("CORS_ORIGIN_REGEX")
        or _DEFAULT_CORS_ORIGIN_REGEX
    )

    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    QDRANT_URL = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

    UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL", "")
    UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_TOKEN", "")

    UPSTASH_REDIS_REST_URL = os.getenv(
        "UPSTASH_REDIS_REST_URL",
        UPSTASH_REDIS_URL,
    )
    UPSTASH_REDIS_REST_TOKEN = os.getenv(
        "UPSTASH_REDIS_REST_TOKEN",
        UPSTASH_REDIS_TOKEN,
    )

    RAG_RELEVANCE_THRESHOLD: float = float(os.getenv(
        "RAG_RELEVANCE_THRESHOLD",
        "0.55",
    ))
    VOICE_ENABLE_RAG: bool = os.getenv(
        "VOICE_ENABLE_RAG",
        "false" if IS_LITE_DEPLOYMENT else "true",
    ).strip().lower() in {"1", "true", "yes", "on"}

    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")

    SENTRY_DSN = os.getenv("SENTRY_DSN", "")

    CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY", "")

    CARTESIA_VOICE_ID = os.getenv("CARTESIA_VOICE_ID", "")

    CARTESIA_MODEL: str = os.getenv(
        "CARTESIA_MODEL",
        "sonic-3.6",
    )

    VOICE_TTS_PROVIDER: str = os.getenv(
        "VOICE_TTS_PROVIDER",
        "cartesia",
    ).strip().lower()

    SARVAM_TTS_MODEL: str = os.getenv(
        "SARVAM_TTS_MODEL",
        "bulbul:v4-flash",
    ).strip()

    # Cartesia uses this when the session language is still ``auto``.
    VOICE_TTS_LANGUAGE: str = os.getenv(
        "VOICE_TTS_LANGUAGE",
        "en-IN",
    )

    VOICE_SAMPLE_RATE: int = 16000

    VOICE_CHUNK_SIZE: int = 1024

    VOICE_ENABLE_STREAMING: bool = True

    VOICE_ENABLE_INTERRUPTION: bool = True

    WHISPER_MODEL: str = "base"

    WHISPER_DEVICE: str = "cpu"

    WHISPER_COMPUTE_TYPE: str = "int8"

    VOICE_STT_PROVIDER: str = os.getenv(
        "VOICE_STT_PROVIDER",
        "sarvam",
    ).strip().lower()

    # Session language: ``auto`` keeps adaptive detection on. Callers may
    # lock ``hi-IN``, ``kn-IN`` or ``en-IN`` per session.
    VOICE_DEFAULT_LANGUAGE: str = os.getenv(
        "VOICE_DEFAULT_LANGUAGE",
        "auto",
    ).strip()

    # Phase 3: ask the merchant which language to use, then lock it. With this
    # off, the call keeps the old detect-as-you-go behaviour.
    VOICE_ASK_LANGUAGE: bool = os.getenv(
        "VOICE_ASK_LANGUAGE",
        "true",
    ).strip().lower() in {"1", "true", "yes", "on"}

    # Used when two answers do not resolve a language. The brief says English.
    VOICE_LANGUAGE_ON_FAILURE: str = os.getenv(
        "VOICE_LANGUAGE_ON_FAILURE",
        "en-IN",
    ).strip()

    # Where pre-rendered fixed phrases are cached. Relative paths resolve
    # against the backend directory.
    VOICE_PHRASE_CACHE_DIR: str = os.getenv(
        "VOICE_PHRASE_CACHE_DIR",
        "",
    ).strip()

    VOICE_ALLOW_WHISPER_FALLBACK: bool = os.getenv(
        "VOICE_ALLOW_WHISPER_FALLBACK",
        "false" if IS_LITE_DEPLOYMENT else "true",
    ).strip().lower() in {"1", "true", "yes", "on"}

    VOICE_VAD_PROVIDER: str = os.getenv(
        "VOICE_VAD_PROVIDER",
        "energy" if IS_LITE_DEPLOYMENT else "silero",
    ).strip().lower()

    VOICE_ALLOW_DEEPGRAM_FALLBACK: bool = os.getenv(
        "VOICE_ALLOW_DEEPGRAM_FALLBACK",
        "true",
    ).strip().lower() in {"1", "true", "yes", "on"}

    # Sarvam realtime streaming speech-to-text.
    SARVAM_API_KEY: str = os.getenv(
        "SARVAM_API_KEY",
        "",
    )

    SARVAM_STT_MODEL: str = os.getenv(
        "SARVAM_STT_MODEL",
        "saaras:v3-realtime",
    )

    # fast = lowest partial latency, best for barge-in.
    SARVAM_STT_STREAM_TYPE: str = os.getenv(
        "SARVAM_STT_STREAM_TYPE",
        "fast",
    )

    SARVAM_STT_ENDPOINTING: str = os.getenv(
        "SARVAM_STT_ENDPOINTING",
        "vad",
    )

    SARVAM_STT_SILENCE_MS: int = int(os.getenv(
        "SARVAM_STT_SILENCE_MS",
        "350",  # fix 10.3: was 500; shorter wait = faster end-of-speech detection
    ))

    SARVAM_STT_MIN_SPEECH_MS: int = int(os.getenv(
        "SARVAM_STT_MIN_SPEECH_MS",
        "250",
    ))

    SARVAM_STT_THRESHOLD: float = float(os.getenv(
        "SARVAM_STT_THRESHOLD",
        "0.3",
    ))

    # Optional terminology hint applied to final transcripts.
    SARVAM_STT_PROMPT: str = os.getenv(
        "SARVAM_STT_PROMPT",
        (
            "Paytm merchant payments, QR codes, settlements, "
            "refunds and soundbox"
        ),
    )

    VIA_ENABLE_TOOLS: bool = os.getenv(
        "VIA_ENABLE_TOOLS",
        "false" if IS_LITE_DEPLOYMENT else "true",
    ).strip().lower() in {"1", "true", "yes", "on"}

    # Phase 4: mock Paytm API server.
    MOCK_PAYTM_URL: str = os.getenv(
        "MOCK_PAYTM_URL",
        "http://127.0.0.1:8200",
    ).strip()

    # Phase 4: audit log location. Empty = default .audit/calls.jsonl in backend/.
    AUDIT_LOG_PATH: str = os.getenv(
        "AUDIT_LOG_PATH",
        "",
    ).strip()

    # Phase 4: enable Paytm tool dispatch on the voice path.
    VOICE_ENABLE_TOOLS: bool = os.getenv(
        "VOICE_ENABLE_TOOLS",
        "true",
    ).strip().lower() in {"1", "true", "yes", "on"}


    DEEPGRAM_API_KEY: str = os.getenv(
        "DEEPGRAM_API_KEY",
        "",
    )

    DEEPGRAM_MODEL: str = os.getenv(
        "DEEPGRAM_MODEL",
        "nova-3",
    )

    DEEPGRAM_LANGUAGE: str = os.getenv(
        "DEEPGRAM_LANGUAGE",
        "en-US",
    )

    DEEPGRAM_ENDPOINTING_MS: int = int(os.getenv(
        "DEEPGRAM_ENDPOINTING_MS",
        "300",
    ))

    DEEPGRAM_UTTERANCE_END_MS: int = int(os.getenv(
        "DEEPGRAM_UTTERANCE_END_MS",
        "1000",
    ))

    DEEPGRAM_KEYWORDS: str = os.getenv(
        "DEEPGRAM_KEYWORDS",
        "Paytm:3",
    )

    VOICE_MAX_TOKENS: int = int(os.getenv(
        "VOICE_MAX_TOKENS",
        "200",  # fix 10.3: was 320; shorter replies finish sooner, keep LLM_REASONING_EFFORT=low
    ))

    # Spoken replies: aim for the soft limit, allow one more sentence when it
    # carries a question, and never exceed the hard limit.
    VOICE_REPLY_SOFT_SENTENCES: int = int(os.getenv(
        "VOICE_REPLY_SOFT_SENTENCES",
        "3",
    ))

    VOICE_REPLY_MAX_SENTENCES: int = int(os.getenv(
        "VOICE_REPLY_MAX_SENTENCES",
        "5",
    ))

    LLM_MODEL: str = os.getenv(
        "LLM_MODEL",
        "openai/gpt-oss-120b",
    )

    LLM_CLASSIFIER_MODEL: str = os.getenv(
        "LLM_CLASSIFIER_MODEL",
        "openai/gpt-oss-120b",
    )

    LLM_TIMEOUT_SECONDS: float = float(os.getenv(
        "LLM_TIMEOUT_SECONDS",
        "12",
    ))

    LLM_MAX_RETRIES: int = int(os.getenv(
        "LLM_MAX_RETRIES",
        "1",
    ))

    # gpt-oss is a reasoning model and hidden reasoning tokens count against
    # max_tokens. Low effort keeps replies from being eaten by reasoning.
    LLM_REASONING_EFFORT: str = os.getenv(
        "LLM_REASONING_EFFORT",
        "low",
    )

    VOICE_INTERRUPTION_CONFIRM_TIMEOUT_SECONDS: float = float(os.getenv(
        "VOICE_INTERRUPTION_CONFIRM_TIMEOUT_SECONDS",
        "2.5",
    ))

    # Emotion analysis is parked. The module stays in place so it can be
    # switched back on, but nothing loads or waits while this is false.
    VOICE_ENABLE_EMOTION: bool = os.getenv(
        "VOICE_ENABLE_EMOTION",
        "false",
    ).strip().lower() in {"1", "true", "yes", "on"}

    EMOTION_DOUBT_THRESHOLD: float = float(os.getenv(
        "EMOTION_DOUBT_THRESHOLD",
        "0.70",
    ))

    EMOTION2VEC_MODEL: str = os.getenv(
        "EMOTION2VEC_MODEL",
        "iic/emotion2vec_plus_base",
    )

    EMOTION2VEC_HUB: str = os.getenv(
        "EMOTION2VEC_HUB",
        "hf",
    )

    EMOTION_WAIT_TIMEOUT_SECONDS: float = float(os.getenv(
        "EMOTION_WAIT_TIMEOUT_SECONDS",
        "0.30",
    ))

settings = Settings()
