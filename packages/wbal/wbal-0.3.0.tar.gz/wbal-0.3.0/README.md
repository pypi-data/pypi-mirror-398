# WBAL

**W**eights & **B**iases **A**gent **L**ibrary - A minimal framework for building LLM agents.

## Overview

WBAL provides three core primitives:

- **Agent** - Orchestrates the perceive-invoke-do loop
- **Environment** - Provides tools and context
- **LM** - Language model interface

All components inherit from `WBALObject` (Pydantic BaseModel + `observe()` method).

## Quick Start

```python
import weave
from wbal import Agent, Environment, weaveTool, GPT5MiniTester

weave.init('my-project')

class MyEnv(Environment):
    system_prompt = "You are a helpful assistant."

    @weaveTool
    def greet(self, name: str) -> str:
        """Greet someone by name."""
        return f"Hello, {name}!"

agent = Agent(lm=GPT5MiniTester, env=MyEnv())
result = agent.run("Say hello to Alice")
```

## Installation

From PyPI:

```bash
pip install wbal
```

From source (for local development):

```bash
git clone https://github.com/wandb/CodeCurious.git
cd CodeCurious
uv sync
```

## Documentation

| Document | Description |
|----------|-------------|
| [USER.md](USER.md) | Usage guide, API reference, examples |
| [DEVELOPER.md](DEVELOPER.md) | Architecture, contributing, testing |
| [GRIFFIN_AGENT_INSTRUCTIONS.md](GRIFFIN_AGENT_INSTRUCTIONS.md) | Detailed framework guide |

## API

```python
from wbal import (
    # Core
    Agent, Environment, StatefulEnvironment, LM,

    # Models
    GPT5Large, GPT5MiniTester,

    # Decorators
    weaveTool, tool,

    # Mixins
    ExitableAgent,

    # Helpers
    tool_timeout, format_openai_tool_response,
)
```

## Examples

See [`examples/`](examples/) for complete implementations.

## Structure

```
wbal/
├── wbal/
│   ├── agent.py        # Agent class
│   ├── environment.py  # Environment, StatefulEnvironment
│   ├── lm.py           # LM, GPT5Large, GPT5MiniTester
│   ├── helper.py       # Tool decorators and utilities
│   └── mixins.py       # ExitableAgent
├── tests/
└── examples/
```
