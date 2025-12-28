from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import Field

from wbal.agent import Agent
from wbal.environments.chat_env import ChatEnv
from wbal.helper import TOOL_CALL_TYPE, format_openai_tool_response, tool_timeout, weaveTool
from wbal.lm import GPT5Large, LM

DEFAULT_SYSTEM_PROMPT = "You are a capable assistant. Use tools when available, be brief and factual."


def extract_reasoning_summary(reasoning_item: Any) -> str | None:
    summary = getattr(reasoning_item, "summary", None)
    if not summary:
        return None
    if isinstance(summary, list):
        texts = []
        for item in summary:
            if hasattr(item, "text"):
                texts.append(item.text)
            elif isinstance(item, str):
                texts.append(item)
        if texts:
            return " ".join(texts)
    if isinstance(summary, str):
        return summary
    return None


def extract_message_text(message_item: Any) -> str | None:
    content = getattr(message_item, "content", [])
    if not content:
        return None
    parts: list[str] = []
    for part in content:
        if hasattr(part, "text"):
            parts.append(part.text)
        elif getattr(part, "type", None) == "output_text":
            text = getattr(part, "text", "")
            if text:
                parts.append(text)
    return "\n".join(parts) if parts else None


class OpenAIWBAgent(Agent):
    """Reference WBAL agent tuned for OpenAI Responses API."""

    lm: LM = Field(default_factory=GPT5Large)
    messages: list[dict[str, Any]] = Field(default_factory=list)
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    tool_timeout: int = 60
    _exit: bool = False

    @weaveTool
    def exit(self, exit_message: str) -> str:
        """Exit the run loop with a final message."""
        self._exit = True
        return exit_message

    def reset(self, reset_messages: bool = False) -> None:
        self._exit = False
        if reset_messages:
            self.messages = []
            self._last_response = None
        if isinstance(self.env, ChatEnv):
            self.env._waiting_for_input = False
            self.env._waiting_message = ""

    @property
    def stopCondition(self) -> bool:  # type: ignore[override]
        waiting = isinstance(self.env, ChatEnv) and self.env.has_pending_input_request()
        return self._exit or waiting

    def perceive(self) -> None:
        if self._step_count == 0:
            if not self.messages:
                today = datetime.now().strftime("%Y-%m-%d")
                self.messages.append({"role": "system", "content": f"{self.system_prompt}\n\nToday's date: {today}"})
                self.messages.append({"role": "system", "content": self.env.observe()})
            self.messages.append({"role": "user", "content": f"Task: {self.env.task}"})

    def invoke(self) -> Any:
        if not self.lm or not self.messages:
            return None
        tools = self._tool_definitions if self._tool_definitions else None
        response = self.lm.invoke(messages=self.messages, tools=tools)
        self._last_response = response
        if hasattr(response, "output"):
            self.messages.extend(response.output)
        return response

    def do(self) -> None:
        if self._last_response is None:
            return
        output = getattr(self._last_response, "output", None)
        if output is None:
            return

        reasoning_items = [o for o in output if getattr(o, "type", None) == "reasoning"]
        message_items = [o for o in output if getattr(o, "type", None) == "message"]
        tool_calls = [o for o in output if getattr(o, "type", None) == TOOL_CALL_TYPE]

        for reasoning in reasoning_items:
            text = extract_reasoning_summary(reasoning)
            if text:
                self.env.output_handler(f"💭 {text}\n")

        for msg in message_items:
            text = extract_message_text(msg)
            if text:
                self.env.output_handler(text)

        if not tool_calls:
            return

        for tc in tool_calls:
            name = getattr(tc, "name", "")
            raw_args = getattr(tc, "arguments", "{}")
            call_id = getattr(tc, "call_id", "")
            if isinstance(raw_args, str):
                try:
                    args = json.loads(raw_args)
                except json.JSONDecodeError:
                    args = {}
            else:
                args = raw_args or {}

            if name in self._tool_callables:
                try:
                    if name == "chat":
                        result = self._tool_callables[name](**args)
                    else:
                        with tool_timeout(self.tool_timeout, name):
                            result = self._tool_callables[name](**args)
                except Exception as e:  # noqa: BLE001
                    result = f"Error executing {name}: {e}"
            else:
                result = f"Unknown tool: {name}"

            self.messages.append(format_openai_tool_response(result, call_id))
