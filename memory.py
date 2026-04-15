from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ChatMessage:
    role: str
    content: str


class ConversationMemory:
    """Maintains recent turns and compresses older context into a short summary."""

    def __init__(
        self,
        max_turns: int = 14,
        token_budget: int = 2800,
        summary_char_limit: int = 3200,
    ) -> None:
        self.max_turns = max(2, max_turns)
        self.token_budget = max(512, token_budget)
        self.summary_char_limit = max(400, summary_char_limit)
        self.messages: List[ChatMessage] = []
        self.summary: str = ""

    def clear(self) -> None:
        self.messages.clear()
        self.summary = ""

    def add_turn(self, user_text: str, assistant_text: str) -> None:
        """Add one full user->assistant turn, then summarize if needed."""
        self.messages.append(ChatMessage(role="user", content=user_text.strip()))
        self.messages.append(ChatMessage(role="assistant", content=assistant_text.strip()))
        self._maybe_summarize()

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        # Rough token estimate for context budgeting.
        return max(1, len(text) // 4)

    @staticmethod
    def _clip(text: str, max_len: int) -> str:
        if len(text) <= max_len:
            return text
        return text[: max_len - 3].rstrip() + "..."

    def _summarize_chunk(self, chunk: List[ChatMessage]) -> str:
        lines: List[str] = []
        for message in chunk:
            speaker = "User" if message.role == "user" else "Assistant"
            clean = " ".join(message.content.split())
            clean = self._clip(clean, 140)
            lines.append(f"- {speaker}: {clean}")
        return "Conversation notes:\n" + "\n".join(lines)

    def _maybe_summarize(self) -> None:
        max_messages = self.max_turns * 2
        if len(self.messages) <= max_messages:
            return

        # Move oldest overflow into summary.
        overflow = len(self.messages) - max_messages
        chunk = self.messages[:overflow]
        self.messages = self.messages[overflow:]

        new_summary = self._summarize_chunk(chunk)
        if self.summary:
            merged = f"{self.summary}\n{new_summary}"
        else:
            merged = new_summary
        self.summary = self._clip(merged, self.summary_char_limit)

    def build_context_messages(self) -> List[Dict[str, str]]:
        """Return summary + recent messages within token budget."""
        context: List[Dict[str, str]] = []
        used_tokens = 0

        if self.summary:
            summary_text = f"Memory summary from earlier chat:\n{self.summary}"
            context.append({"role": "system", "content": summary_text})
            used_tokens += self._estimate_tokens(summary_text)

        selected: List[ChatMessage] = []
        for message in reversed(self.messages):
            message_tokens = self._estimate_tokens(message.content)
            if used_tokens + message_tokens > self.token_budget:
                break
            selected.append(message)
            used_tokens += message_tokens

        selected.reverse()
        for message in selected:
            context.append({"role": message.role, "content": message.content})

        return context

    def stats(self) -> Dict[str, int]:
        return {
            "active_messages": len(self.messages),
            "estimated_turns": len(self.messages) // 2,
            "summary_chars": len(self.summary),
        }
