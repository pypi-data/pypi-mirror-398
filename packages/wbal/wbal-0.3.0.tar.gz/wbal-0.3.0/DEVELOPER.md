# WBAL Developer Guide

Guide for developing and contributing to the WBAL framework.

## Architecture

WBAL is built on three primitives, all inheriting from `WBALObject`:

```
WBALObject (Pydantic BaseModel + observe())
├── LM - Language model interface
├── Environment - Tools and context
│   └── StatefulEnvironment - Persistent state
└── Agent - Perceive-invoke-do loop
    └── ExitableAgent - With exit() tool
```

### File Structure

```
lib/wbal/
├── wbal/
│   ├── __init__.py      # Public exports
│   ├── object.py        # WBALObject base class
│   ├── lm.py            # LM, GPT5Large, GPT5MiniTester
│   ├── environment.py   # Environment, StatefulEnvironment
│   ├── agent.py         # Agent class
│   ├── mixins.py        # ExitableAgent mixin
│   └── helper.py        # Tool decorators, schema utilities
├── tests/
├── examples/
├── pyproject.toml
└── GRIFFIN_AGENT_INSTRUCTIONS.md  # Detailed framework guide
```

## Development Setup

```bash
cd CodeCurious
uv sync

# Run tests
cd lib/wbal
uv run pytest tests/

# Run specific test
uv run pytest tests/test_agent.py -v
```

## Core Components

### WBALObject (`object.py`)

Base class providing:
- Pydantic model validation
- `observe()` method for state representation
- Serialization support

```python
class WBALObject(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def observe(self) -> str:
        """Return string representation of object state."""
        return str(self.model_dump())
```

### LM (`lm.py`)

Language model interface:

```python
class LM(WBALObject):
    def invoke(self, messages: list[dict], tools: list[dict] | None = None) -> Response:
        """Call the LLM and return response."""
        pass
```

Built-in implementations:
- `GPT5Large` - Production model (gpt-4o)
- `GPT5MiniTester` - Testing model (gpt-4o-mini)

### Environment (`environment.py`)

Provides tools and context:

```python
class Environment(WBALObject):
    system_prompt: str = ""

    @property
    def tools(self) -> list[Callable]:
        """Override to provide tools."""
        return []
```

`StatefulEnvironment` adds persistence:

```python
class StatefulEnvironment(Environment):
    _state_path: str | None = None

    def save(self) -> None:
        """Persist state to disk."""

    @classmethod
    def load_or_create(cls, path: str) -> Self:
        """Load from disk or create new."""
```

### Agent (`agent.py`)

Orchestrates the loop:

```python
class Agent(WBALObject):
    lm: LM
    env: Environment
    maxSteps: int = 20
    messages: list[dict] = []

    def run(self, task: str | None = None) -> str:
        """Run until stopCondition or maxSteps."""
        while not self.stopCondition and self._step_count < self.maxSteps:
            self.step()
        return self._last_response

    def step(self) -> None:
        self.perceive()
        self.invoke()
        self.do()

    @property
    def stopCondition(self) -> bool:
        """Override to customize stop logic."""
        return False
```

### Helper (`helper.py`)

Tool utilities:

```python
# Decorators
@weaveTool      # Traced with Weave
@tool           # Basic tool decorator

# Schema extraction
extract_tool_schema(fn)     # Get JSON schema from function
to_openai_tool(fn)          # Convert to OpenAI tool format
to_anthropic_tool(fn)       # Convert to Anthropic tool format

# Response formatting
format_openai_tool_response(tool_call_id, result)

# Timeout handling
@tool_timeout(seconds=30)
def slow_tool(): ...
```

## Adding Features

### Adding a New LM

```python
# In lm.py
class MyLM(LM):
    model: str = "my-model"
    client: Any = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = MyClient()

    def invoke(self, messages, tools=None):
        response = self.client.chat(messages, tools)
        return self._format_response(response)
```

### Adding a New Mixin

```python
# In mixins.py
class MyMixin(Agent):
    @weaveTool
    def my_capability(self, arg: str) -> str:
        """Add this capability to agents."""
        return result
```

Usage:
```python
class MyAgent(MyMixin, Agent):
    pass
```

## Testing

```bash
# All tests
uv run pytest tests/

# With coverage
uv run pytest tests/ --cov=wbal

# Specific test file
uv run pytest tests/test_agent.py -v

# Run single test
uv run pytest tests/test_agent.py::test_agent_run -v
```

### Writing Tests

```python
# tests/test_my_feature.py
import pytest
from wbal import Agent, Environment, weaveTool

def test_my_feature():
    class TestEnv(Environment):
        @weaveTool
        def test_tool(self) -> str:
            return "ok"

    agent = Agent(env=TestEnv(), maxSteps=1)
    # assertions...
```

## Examples

See `examples/` for complete implementations:

- `simple_example.py` - Basic agent setup
- `story_summarizer.py` - Multi-step agent with file I/O
- `regioned_claude_code/` - Complex agent with sandboxing

## Guidelines

1. **Keep it minimal** - WBAL is intentionally small (~740 lines)
2. **Use Pydantic** - All classes should be Pydantic models
3. **Trace with Weave** - Use `@weaveTool` for observability
4. **Document tools** - Docstrings become LLM tool descriptions
5. **Type hints** - Required for tool schema generation
