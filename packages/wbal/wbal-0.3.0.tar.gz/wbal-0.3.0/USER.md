# WBAL User Guide

WBAL (**W**eights & **B**iases **A**gent **L**ibrary) is a minimal framework for building LLM agents. It provides three core primitives: Agent, Environment, and LM.

## Installation

Install from PyPI:

```bash
pip install wbal
```

For local development from source:

```bash
git clone https://github.com/wandb/CodeCurious.git
cd CodeCurious
uv sync
```

## Quick Start

```python
import weave
from wbal import Agent, Environment, weaveTool, GPT5MiniTester

weave.init('my-project')

# Define an environment with tools
class MyEnv(Environment):
    system_prompt = "You are a helpful assistant."

    @weaveTool
    def greet(self, name: str) -> str:
        """Greet someone by name."""
        return f"Hello, {name}!"

# Create and run an agent
agent = Agent(lm=GPT5MiniTester, env=MyEnv())
result = agent.run("Say hello to Alice")
print(result)
```

## Core Concepts

### Agent

The `Agent` orchestrates the perceive-invoke-do loop:

1. **perceive()** - Gather observations, update state
2. **invoke()** - Call the LLM with messages and tools
3. **do()** - Execute tool calls from the LLM response

```python
from wbal import Agent, GPT5MiniTester

agent = Agent(
    lm=GPT5MiniTester,      # Language model
    env=MyEnv(),            # Environment with tools
    maxSteps=20,            # Max loop iterations
)
result = agent.run("Your task here")
```

### Environment

The `Environment` provides tools and context:

```python
from wbal import Environment, weaveTool

class MyEnv(Environment):
    system_prompt = "You are a helpful assistant."

    # Instance variables become context
    task: str = "Default task description"

    @weaveTool
    def my_tool(self, query: str) -> str:
        """Tool description (shown to LLM)."""
        return f"Result for: {query}"
```

### Tools

Use `@weaveTool` to expose methods to the LLM:

```python
from wbal import weaveTool

@weaveTool
def search(query: str, limit: int = 10) -> str:
    """Search for information.

    Args:
        query: The search query
        limit: Maximum results to return
    """
    # Implementation
    return results
```

The docstring becomes the tool description. Type hints define the schema.

### Language Models

```python
from wbal import GPT5Large, GPT5MiniTester

# Production model
agent = Agent(lm=GPT5Large, env=env)

# Testing/development model (faster, cheaper)
agent = Agent(lm=GPT5MiniTester, env=env)
```

## Stateful Environments

For persistent state across agent runs:

```python
from wbal import StatefulEnvironment

class MyStatefulEnv(StatefulEnvironment):
    observations: list[str] = []

    @weaveTool
    def add_observation(self, obs: str) -> str:
        """Record an observation."""
        self.observations.append(obs)
        self.save()  # Persist to disk
        return f"Recorded: {obs}"

# Load from disk or create new
env = MyStatefulEnv.load_or_create("/path/to/state")
```

## Exitable Agents

For agents that can decide when to stop:

```python
from wbal import ExitableAgent

class MyAgent(ExitableAgent):
    # Inherits exit() tool automatically
    pass

agent = MyAgent(env=env, maxSteps=50)
result = agent.run("Task that agent can exit from")
```

## Observability

All tool calls are traced with [Weave](https://wandb.ai/site/weave):

```python
import weave
weave.init('my-project')

# Now all agent runs are traced
agent.run("...")
```

View traces at: `https://wandb.ai/<entity>/<project>/weave`

## API Reference

### Exports

```python
from wbal import (
    # Core classes
    Agent,
    Environment,
    StatefulEnvironment,
    ExitableAgent,
    LM,
    GPT5Large,
    GPT5MiniTester,

    # Decorators
    weaveTool,
    tool,

    # Helpers
    tool_timeout,
    ToolTimeoutError,
    format_openai_tool_response,
    to_openai_tool,
    to_anthropic_tool,
)
```

### Agent Methods

| Method | Description |
|--------|-------------|
| `run(task)` | Run the agent loop until completion |
| `step()` | Execute one perceive-invoke-do cycle |
| `perceive()` | Override to customize observation gathering |
| `invoke()` | Override to customize LLM calls |
| `do()` | Override to customize tool execution |

### Environment Methods

| Method | Description |
|--------|-------------|
| `observe()` | Returns string representation of environment state |
| `save()` | (StatefulEnvironment) Persist state to disk |
| `load_or_create(path)` | (StatefulEnvironment) Load or create new instance |
