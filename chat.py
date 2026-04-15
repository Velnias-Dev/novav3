from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from avatar import AvatarController

from config import AppConfig
from emotion import EmotionState, detect_emotion
from memory import ConversationMemory
from model import LocalLlamaModel
from personality import build_system_prompt, detect_user_signal
from tts import PiperTTS

logger = logging.getLogger(__name__)

EXIT_COMMANDS = {"exit", "quit", "/exit", "/quit"}


class ChatSession:
    """Interactive CLI chat session with logging and local memory."""

    def __init__(
        self,
        config: AppConfig,
        model: LocalLlamaModel,
        memory: ConversationMemory,
        tts: PiperTTS,
        avatar: AvatarController,
    ) -> None:
        self.config = config
        self.model = model
        self.memory = memory
        self.tts = tts
        self.avatar = avatar

        self.config.log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_log_path = self.config.log_dir / f"session_{ts}.jsonl"

    def _append_log(self, role: str, content: str) -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "role": role,
            "content": content,
        }
        try:
            with self.session_log_path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except OSError:
            logger.exception("Failed to write session log.")

    @staticmethod
    def _print_help() -> None:
        print("Commands:")
        print("  /help   Show this help")
        print("  /reset  Clear conversation memory")
        print("  /status Show memory/runtime status")
        print("  /exit   Quit")

    def _print_status(self) -> None:
        stats = self.memory.stats()
        print(
            f"Status | gpu_layers={self.model.active_gpu_layers} | "
            f"active_messages={stats['active_messages']} | "
            f"summary_chars={stats['summary_chars']} | "
            f"tts={'on' if self.config.tts_enabled else 'off'} | "
            f"avatar={'on' if self.config.avatar_enabled else 'off'} | "
            f"emotion={'on' if self.config.emotion_enabled else 'off'}"
        )

    def _resolve_emotion(self, reply: str) -> EmotionState:
        if not self.config.emotion_enabled:
            return "neutral"
        return detect_emotion(reply)

    def _dispatch_reactions(self, reply: str, emotion: EmotionState) -> None:
        logger.info("Detected emotion: %s", emotion)
        print(f"[Emotion] {emotion}")

        if self.config.tts_enabled:
            self.tts.speak(reply)

        if self.config.avatar_enabled:
            self.avatar.set_expression(emotion)
            self.avatar.trigger_idle_animation()

    def run_cli(self) -> None:
        print(f"{self.config.app_name} ready.")
        print("Type /help for commands.")

        while True:
            try:
                user_text = input("You> ").strip()
            except (KeyboardInterrupt, EOFError):
                print(f"\n{self.config.character_name}> Session closed. Catch you later.")
                break

            if not user_text:
                continue

            lowered = user_text.lower()

            # Built-in CLI controls.
            if lowered in EXIT_COMMANDS:
                print(f"{self.config.character_name}> Later.")
                break
            if lowered == "/help":
                self._print_help()
                continue
            if lowered == "/reset":
                self.memory.clear()
                print(f"{self.config.character_name}> Memory cleared. Fresh slate.")
                continue
            if lowered == "/status":
                self._print_status()
                continue

            signal = detect_user_signal(user_text)
            system_prompt = build_system_prompt(self.config.character_name, signal)
            context = self.memory.build_context_messages()

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(context)
            messages.append({"role": "user", "content": user_text})

            try:
                reply = self.model.generate_response(messages)
            except Exception as exc:
                logger.exception("Generation failed: %s", exc)
                print(f"{self.config.character_name}> I hit a local runtime error. Check logs and try again.")
                continue

            print(f"{self.config.character_name}> {reply}")
            self.memory.add_turn(user_text=user_text, assistant_text=reply)
            self._append_log("user", user_text)
            self._append_log("assistant", reply)
            emotion = self._resolve_emotion(reply)
            self._append_log("emotion", emotion)
            self._dispatch_reactions(reply, emotion)


def run_smoke_test(model: LocalLlamaModel, character_name: str) -> str:
    """Simple runtime sanity check."""
    prompt = build_system_prompt(character_name, "neutral")
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": "Reply with exactly: NOVA_OK"},
    ]
    return model.generate_response(messages, temperature=0.0, top_p=1.0, max_tokens=16)
