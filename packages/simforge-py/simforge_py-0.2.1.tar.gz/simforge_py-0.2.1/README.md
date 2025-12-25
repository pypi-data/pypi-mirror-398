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

```python
from simforge import Simforge

client = Simforge(
    provider="openAI",
    provider_model="gpt-4",
    api_key="sf_your_api_key_here",  # Required: Your Simforge API key
    service_url="https://your-simforge-instance.com",  # Optional, can use SIMFORGE_URL env var
    provider_api_key="sk-your-openai-key",  # Optional, can use OPENAI_API_KEY env var
)

result = client.call("method_name", arg1="value1", arg2="value2")
```

## Configuration

- `provider_model`: **Required** - The model name to use (e.g., 'gpt-4')
- `api_key` (Simforge API key): **Required** - Must be provided as a constructor argument
- `service_url`: Optional - Can be provided as a constructor argument or via the `SIMFORGE_URL` environment variable
- `provider_api_key`: Optional - The API key for the provider (e.g., OpenAI). If not provided, uses the `OPENAI_API_KEY` environment variable

You can generate a Simforge API key from your Simforge dashboard.
