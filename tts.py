from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class PiperTTS:
    """Minimal local TTS wrapper using Piper CLI."""

    def __init__(
        self,
        enabled: bool,
        model_path: Path,
        playback_enabled: bool = True,
        piper_binary: str = "piper",
    ) -> None:
        self.enabled = enabled
        self.model_path = model_path
        self.playback_enabled = playback_enabled
        self.piper_binary = piper_binary

    def is_ready(self) -> bool:
        if not self.enabled:
            return False
        if shutil.which(self.piper_binary) is None:
            logger.warning("Piper binary not found in PATH: %s", self.piper_binary)
            return False
        if not self.model_path.exists():
            logger.warning("Piper voice model not found: %s", self.model_path)
            return False
        return True

    def _synthesize_to_wav(self, text: str, output_path: Path) -> bool:
        cmd = [
            self.piper_binary,
            "--model",
            str(self.model_path),
            "--output_file",
            str(output_path),
        ]
        try:
            subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError as exc:
            logger.error("Piper synthesis failed: %s", exc.stderr.decode("utf-8", errors="ignore"))
            return False
        except OSError:
            logger.exception("Failed to execute Piper binary.")
            return False

    @staticmethod
    def _play_wav(wav_path: Path) -> bool:
        try:
            import simpleaudio  # Imported lazily to keep startup lightweight.
        except Exception:
            logger.exception("simpleaudio is not available for playback.")
            return False

        try:
            wave_obj = simpleaudio.WaveObject.from_wave_file(str(wav_path))
            playback = wave_obj.play()
            playback.wait_done()
            return True
        except Exception:
            logger.exception("Audio playback failed for %s", wav_path)
            return False

    def speak(self, text: str) -> bool:
        """Generate speech from text and optionally play it."""
        if not self.enabled:
            return False

        cleaned = text.strip()
        if not cleaned:
            return False

        if not self.is_ready():
            return False

        with tempfile.TemporaryDirectory(prefix="nova_tts_") as temp_dir:
            wav_path = Path(temp_dir) / "reply.wav"
            if not self._synthesize_to_wav(cleaned, wav_path):
                return False
            if not self.playback_enabled:
                return True
            return self._play_wav(wav_path)
