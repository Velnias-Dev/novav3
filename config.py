from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class AppConfig:
    app_name: str
    character_name: str
    model_path: Path
    chat_format: str
    n_ctx: int
    n_threads: int
    n_batch: int
    n_gpu_layers: int
    temperature: float
    top_p: float
    max_tokens: int
    repeat_penalty: float
    memory_max_turns: int
    memory_token_budget: int
    log_dir: Path
    allow_cpu_fallback: bool
    verbose: bool
    emotion_enabled: bool
    tts_enabled: bool
    tts_model_path: Path
    tts_playback_enabled: bool
    piper_binary: str
    avatar_enabled: bool


def load_config() -> AppConfig:
    """Load application configuration from environment variables."""
    load_dotenv(override=False)

    project_root = Path(__file__).resolve().parent
    default_threads = max(1, (os.cpu_count() or 4) - 2)

    # Keep model path easy to configure with relative paths.
    raw_model_path = os.getenv("MODEL_PATH", "models/Qwen2.5-3B-Instruct-Q4_K_M.gguf")
    model_path = Path(raw_model_path).expanduser()
    if not model_path.is_absolute():
        model_path = (project_root / model_path).resolve()

    raw_log_dir = os.getenv("LOG_DIR", "logs")
    log_dir = Path(raw_log_dir).expanduser()
    if not log_dir.is_absolute():
        log_dir = (project_root / log_dir).resolve()
    raw_tts_model_path = os.getenv("TTS_MODEL_PATH", "voices/en_US-lessac-medium.onnx")
    tts_model_path = Path(raw_tts_model_path).expanduser()
    if not tts_model_path.is_absolute():
        tts_model_path = (project_root / tts_model_path).resolve()

    return AppConfig(
        app_name=os.getenv("APP_NAME", "Nova Local Chat"),
        character_name=os.getenv("CHARACTER_NAME", "Nova"),
        model_path=model_path,
        chat_format=os.getenv("CHAT_FORMAT", "chatml"),
        n_ctx=_get_int("N_CTX", 4096),
        n_threads=_get_int("N_THREADS", default_threads),
        n_batch=_get_int("N_BATCH", 512),
        n_gpu_layers=_get_int("N_GPU_LAYERS", 0),
        temperature=_get_float("TEMPERATURE", 0.85),
        top_p=_get_float("TOP_P", 0.9),
        max_tokens=_get_int("MAX_TOKENS", 220),
        repeat_penalty=_get_float("REPEAT_PENALTY", 1.1),
        memory_max_turns=_get_int("MEMORY_MAX_TURNS", 14),
        memory_token_budget=_get_int("MEMORY_TOKEN_BUDGET", 2800),
        log_dir=log_dir,
        allow_cpu_fallback=_get_bool("ALLOW_CPU_FALLBACK", True),
        verbose=_get_bool("VERBOSE", False),
        emotion_enabled=_get_bool("EMOTION_ENABLED", True),
        tts_enabled=_get_bool("TTS_ENABLED", False),
        tts_model_path=tts_model_path,
        tts_playback_enabled=_get_bool("TTS_PLAYBACK_ENABLED", True),
        piper_binary=os.getenv("PIPER_BINARY", "piper"),
        avatar_enabled=_get_bool("AVATAR_ENABLED", False),
    )
