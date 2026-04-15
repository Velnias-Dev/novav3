from __future__ import annotations

import argparse
import logging
from pathlib import Path
from avatar import AvatarController

from chat import ChatSession, run_smoke_test
from config import load_config
from memory import ConversationMemory
from model import LocalLlamaModel
from tts import PiperTTS


def setup_logging(log_dir: Path, verbose: bool) -> None:
    """Configure file and console logging."""
    log_dir.mkdir(parents=True, exist_ok=True)
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "nova.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Nova - local-first AI VTuber foundation (v2)"
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Load the model and run a minimal response check.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config()
    setup_logging(config.log_dir, config.verbose)

    if not config.model_path.exists():
        print(f"[ERROR] Model file not found: {config.model_path}")
        print("Set MODEL_PATH in .env to your local GGUF model file.")
        return 1

    model = LocalLlamaModel(config)

    try:
        model.load()
    except Exception as exc:
        logging.exception("Failed to load model.")
        print(f"[ERROR] Could not load model: {exc}")
        print("If GPU offload fails, set N_GPU_LAYERS=0 in .env and retry.")
        return 1

    if args.smoke_test:
        try:
            output = run_smoke_test(model, config.character_name)
        except Exception as exc:
            logging.exception("Smoke test failed.")
            print(f"[ERROR] Smoke test failed: {exc}")
            return 1

        print(f"Smoke test output: {output}")
        if "NOVA_OK" in output.upper():
            print("Smoke test passed.")
        else:
            print("Model responded, but not exact NOVA_OK (runtime still works).")
        return 0

    memory = ConversationMemory(
        max_turns=config.memory_max_turns,
        token_budget=config.memory_token_budget,
    )
    tts = PiperTTS(
        enabled=config.tts_enabled,
        model_path=config.tts_model_path,
        playback_enabled=config.tts_playback_enabled,
        piper_binary=config.piper_binary,
    )
    avatar = AvatarController(enabled=config.avatar_enabled)
    if config.avatar_enabled:
        avatar.connect()

    session = ChatSession(config=config, model=model, memory=memory, tts=tts, avatar=avatar)
    try:
        session.run_cli()
    finally:
        avatar.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
