from __future__ import annotations

from typing import Callable

from wbal.environments.data_env import DataEnv
from wbal.helper import weaveTool

DEFAULT_CHAT_INSTRUCTIONS = (
    "You are a chat interface. Use the provided tools and ask clarifying questions when needed."
)


class ChatEnv(DataEnv):
    """Environment for interactive chat sessions."""

    chat_instructions: str = DEFAULT_CHAT_INSTRUCTIONS
    _waiting_for_input: bool = False
    _waiting_message: str = ""

    user_chat_input_handler: Callable[[str], str] = lambda prompt: input(prompt)
    output_handler: Callable[[str], None] = lambda x: print(x)

    def observe(self) -> str:
        base = self.chat_instructions.strip()
        rest = super().observe()
        return f"{base}\n\n{rest}" if base else rest

    def has_pending_input_request(self) -> bool:
        return self._waiting_for_input

    def get_pending_message(self) -> str:
        return self._waiting_message

    @weaveTool
    def chat(self, message_to_user: str, wait_for_user_input: bool = False) -> str:
        """Communicate with the user; optionally wait for input."""
        self.output_handler(message_to_user)
        if wait_for_user_input:
            self._waiting_for_input = True
            self._waiting_message = message_to_user
            user_response = self.user_chat_input_handler("\nUser: ")
            self._waiting_for_input = False
            self._waiting_message = ""
            return user_response
        return ""
