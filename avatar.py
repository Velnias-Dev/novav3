from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from emotion import EmotionState

logger = logging.getLogger(__name__)

EMOTION_TO_HOTKEY = {
    "happy": "NovaHappy",
    "thinking": "NovaThinking",
    "neutral": "NovaNeutral",
    "playful": "NovaPlayful",
    "serious": "NovaSerious",
}


class AvatarController:
    """
    Optional VTube Studio bridge.
    Uses pyvts if available and fails gracefully when VTube Studio is not running.
    """

    def __init__(self, enabled: bool, token_file: str = ".vts_token") -> None:
        self.enabled = enabled
        self.token_file = Path(token_file)
        self.connected = False
        self._pyvts = None
        self._vts = None
        self._executor: ThreadPoolExecutor | None = None

        if not self.enabled:
            return

        try:
            import pyvts

            self._pyvts = pyvts
            self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="nova_avatar")
        except Exception:
            logger.warning("pyvts is not installed. Avatar integration disabled.")
            self.enabled = False

    def connect(self) -> bool:
        """Try connecting to VTube Studio once at startup."""
        if not self.enabled or self._pyvts is None:
            return False
        try:
            self.connected = asyncio.run(self._connect_async())
            return self.connected
        except Exception:
            logger.exception("Avatar connection failed.")
            self.connected = False
            return False

    async def _connect_async(self) -> bool:
        assert self._pyvts is not None
        plugin_info = {
            "plugin_name": "NovaV2",
            "developer": "Nova Local",
            "authentication_token_path": str(self.token_file),
        }
        self._vts = self._pyvts.vts(plugin_info=plugin_info)
        await self._vts.connect()
        await self._vts.request_authenticate_token()
        await self._vts.request_authenticate()
        logger.info("Connected to VTube Studio.")
        return True

    async def _trigger_hotkey_async(self, hotkey_id: str) -> bool:
        if not self.connected or self._vts is None:
            return False
        try:
            request = self._pyvts.vts_request.requestTriggerHotKey(hotkeyID=hotkey_id)
            await self._vts.request(request)
            return True
        except Exception:
            logger.debug("Hotkey trigger failed or missing hotkey: %s", hotkey_id)
            return False

    def set_expression(self, emotion: EmotionState) -> bool:
        """Map emotion to a hotkey trigger. Missing hotkeys are ignored."""
        hotkey = EMOTION_TO_HOTKEY.get(emotion, EMOTION_TO_HOTKEY["neutral"])
        logger.debug("Setting avatar expression: emotion=%s hotkey=%s", emotion, hotkey)
        return self._trigger_hotkey(hotkey)

    def trigger_idle_animation(self) -> bool:
        """Trigger an optional idle animation hotkey."""
        logger.debug("Triggering avatar idle animation hotkey: NovaIdle")
        return self._trigger_hotkey("NovaIdle")

    def _trigger_hotkey(self, hotkey_id: str) -> bool:
        if not self.connected or self._executor is None:
            logger.debug("Skipping hotkey trigger because avatar is not connected: %s", hotkey_id)
            return False
        self._executor.submit(self._run_hotkey_task, hotkey_id)
        logger.debug("Queued avatar hotkey trigger: %s", hotkey_id)
        return True

    def _run_hotkey_task(self, hotkey_id: str) -> None:
        try:
            success = asyncio.run(self._trigger_hotkey_async(hotkey_id))
            if success:
                logger.info("Avatar hotkey trigger succeeded: %s", hotkey_id)
            else:
                logger.debug("Avatar hotkey trigger was ignored or failed: %s", hotkey_id)
        except Exception:
            logger.debug("Hotkey dispatch failed: %s", hotkey_id)

    def close(self) -> None:
        if self._executor is not None:
            self._executor.shutdown(wait=False)
        if self.connected and self._vts is not None:
            try:
                asyncio.run(self._vts.close())
            except Exception:
                logger.debug("Avatar close ignored due to runtime state.")
        self.connected = False
