# Agent Instructions

This guide explains how to build agents with the WBAL stack (`DataEnv`, `ChatEnv`, `PollEnv`, `OpenAIWBAgent`).

## Core pieces
- **Environments**: Provide tools and context. `DataEnv` holds shared state (notes/observations) and read-only tools. `PollEnv` adds write tools for notes/observations. `ChatEnv` adds a chat tool and chat instructions.
- **Agent**: `OpenAIWBAgent` runs the perceive → invoke → do loop with OpenAI Responses-compatible behavior.
- **Tools**: Real tool functions live directly on env/agent methods; no wrappers needed so annotations/docstrings are captured once.

## Creating tools
1. Define a method on your env or agent.
2. Add type hints and a clear docstring.
3. Decorate with `@weaveTool` (or `@tool`).

Example (env tool):
```python
from wbal import weaveTool
from wbal.environments.data_env import DataEnv

class MyDataEnv(DataEnv):
    @weaveTool
    def fetch_user(self, user_id: str) -> dict[str, str]:
        """Return user info from your service."""
        return {"id": user_id}
```

Example (agent tool):
```python
from wbal import weaveTool
from wbal.agents.openai_agent import OpenAIWBAgent

class MyAgent(OpenAIWBAgent):
    @weaveTool
    def jot(self, note: str) -> str:
        """Keep a local note during reasoning."""
        return f"Noted: {note}"
```

**Tip:** Put helper functions in a `tools/` module if you like, but bind them directly as class methods so annotations/docstrings are picked up once. Avoid wrapper functions that duplicate docs.

## Running an agent
```python
from wbal.agents.openai_agent import OpenAIWBAgent
from wbal.environments.chat_env import ChatEnv

env = ChatEnv(task="help the user", working_directory="/tmp/state")
agent = OpenAIWBAgent(env=env)
agent.run(task="Find recent deploys", max_steps=20)
```
- First turn: agent injects system prompt, `env.observe()` (tools + state summary), then `Task: ...` as a user message.
- Stop condition: exit tool called, or (in `ChatEnv`) waiting for user input.
- `wbal-chat` / `wbal-poll` provide runnable examples.

## Output and timeouts
- Agent prints assistant messages and reasoning summaries via `env.output_handler` (defaults to `print`).
- Tool calls are executed sequentially with a timeout (skips timeout for `chat`).

## Persistence
- Set `working_directory` on your env to persist notes/observations in `environment_state.json`.
- `DataEnv` exposes read-only tools (`get_notes`, `get_observations`). `PollEnv` adds write tools (`store_note`, `delete_note`, `add_observation`).

## Extending
- Swap LMs by passing a different `lm` to `OpenAIWBAgent`.
- Add custom stop logic by overriding `stopCondition` or `perceive` in a subclass.
- Add more tools directly to your env/agent with docstrings and annotations.

## Building your own bot (example: PersonBot)
1) **Pick envs**
   - Interactive only: subclass `ChatEnv`.
   - Add headless monitoring: subclass `PollEnv` too (share `working_directory` to share state).

2) **Add tools directly (no wrappers)**
```python
from wbal import weaveTool
from wbal.environments.chat_env import ChatEnv

class PersonChatEnv(ChatEnv):
    @weaveTool
    def fetch_profile(self, user_id: str) -> dict[str, str]:
        """Return a user profile from your service."""
        return {"id": user_id}
```
For polling writes:
```python
from wbal.environments.poll_env import PollEnv

class PersonPollEnv(PollEnv):
    @weaveTool
    def check_health(self) -> dict[str, str]:
        """Run a health check."""
        return {"status": "ok"}
```

3) **Run with the reference agent**
```python
from wbal.agents.openai_agent import OpenAIWBAgent
env = PersonChatEnv(task="help the user", working_directory="/tmp/state")
agent = OpenAIWBAgent(env=env)
agent.run(task="Assist the user", max_steps=20)
```

4) **Use scripts**
- Chat: `uv run wbal-chat --project myproj --task "Assist the user" --working-dir /tmp/state`
- Poll: `uv run wbal-poll --project myproj --task "Monitor health" --working-dir /tmp/state --interval 300`
Both share state if `working_directory` matches.
