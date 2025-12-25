# Simforge

Simforge client for provider-based API calls.

## Monorepo Structure

This package is part of the Harvest monorepo. While the TypeScript/JavaScript packages use a **pnpm workspace** for shared dependencies, this Python package uses Poetry for its dependency management.

**Note:** The pnpm workspace includes:
- `simforge-web` - Next.js web application
- `simforge-typescript-sdk` - TypeScript SDK
- `simforge-vscode` - VS Code extension
- `frontend` - Legacy frontend

From the root directory, you can run TypeScript tests and validation across all packages with `pnpm test` or `pnpm validate`.

## Installation

### Basic Installation

```bash
pip install simforge-py
```

### With OpenAI Tracing Support

If you want to use the OpenAI Agents SDK tracing integration:

```bash
pip install simforge-py[openai-tracing]
```

### Local Development

For local development:

```bash
cd simforge-python-sdk
poetry install
```

Or install as an editable package from the parent directory:

```bash
poetry add --editable ../simforge-python-sdk
```

## Usage

### Basic Usage

```python
from simforge import Simforge

client = Simforge(
    api_key="sf_your_api_key_here",
    service_url="https://simforge.goharvest.ai",  # Optional, defaults to production
    env_vars={"OPENAI_API_KEY": "sk-your-openai-key"},  # Optional, for local BAML execution
    execute_locally=True  # Optional, defaults to True
)

result = client.call("method_name", arg1="value1", arg2="value2")
```

### OpenAI Agents SDK Tracing

If you have the `openai-agents` package installed (via `pip install simforge-py[openai-tracing]`), you can use the tracing processor:

```python
from simforge import Simforge
from agents import set_trace_processors

simforge = Simforge(api_key="sf_your_api_key_here")
processor = simforge.get_openai_tracing_processor()

# Register the processor with OpenAI Agents SDK
set_trace_processors([processor])

# Now all your agent traces will be sent to Simforge
```

**Note:** If you try to use `get_openai_tracing_processor()` without installing the `openai-tracing` extra, you'll get a helpful error message telling you to install it.

## Configuration

- `api_key`: **Required** - Your Simforge API key (generate from your Simforge dashboard)
- `service_url`: Optional - The Simforge service URL (defaults to `https://simforge.goharvest.ai`)
- `env_vars`: Optional - Environment variables for LLM providers (e.g., `{"OPENAI_API_KEY": "..."}`)
- `execute_locally`: Optional - Whether to execute BAML locally (defaults to `True`)
