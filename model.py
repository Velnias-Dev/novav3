from __future__ import annotations

import logging
from typing import Dict, List, Optional

from llama_cpp import Llama

from config import AppConfig

logger = logging.getLogger(__name__)


class LocalLlamaModel:
    """Thin wrapper around llama-cpp-python with optional GPU->CPU fallback."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.llm: Optional[Llama] = None
        self.active_gpu_layers = 0

    def _build_llm(self, n_gpu_layers: int) -> Llama:
        kwargs = {
            "model_path": str(self.config.model_path),
            "n_ctx": self.config.n_ctx,
            "n_threads": self.config.n_threads,
            "n_batch": self.config.n_batch,
            "n_gpu_layers": n_gpu_layers,
            "verbose": self.config.verbose,
        }

        # Keep chat formatting configurable for easier model swaps.
        if self.config.chat_format.lower() != "auto":
            kwargs["chat_format"] = self.config.chat_format

        return Llama(**kwargs)

    def load(self) -> None:
        """Load the model and optionally retry in CPU mode if GPU offload fails."""
        try:
            self.llm = self._build_llm(self.config.n_gpu_layers)
            self.active_gpu_layers = self.config.n_gpu_layers
            logger.info("Model loaded. n_gpu_layers=%s", self.active_gpu_layers)
            return
        except Exception as exc:
            if not self.config.allow_cpu_fallback or self.config.n_gpu_layers == 0:
                raise RuntimeError(f"Model load failed: {exc}") from exc
            logger.warning("GPU load failed (%s). Retrying with CPU fallback.", exc)

        self.llm = self._build_llm(0)
        self.active_gpu_layers = 0
        logger.info("Model loaded in CPU mode.")

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate one assistant response from chat-style messages."""
        if self.llm is None:
            raise RuntimeError("Model is not loaded.")

        response = self.llm.create_chat_completion(
            messages=messages,
            temperature=self.config.temperature if temperature is None else temperature,
            top_p=self.config.top_p if top_p is None else top_p,
            max_tokens=self.config.max_tokens if max_tokens is None else max_tokens,
            repeat_penalty=self.config.repeat_penalty,
        )

        content = response["choices"][0]["message"]["content"]
        if content is None:
            raise RuntimeError("Model returned an empty response.")
        return str(content).strip()
