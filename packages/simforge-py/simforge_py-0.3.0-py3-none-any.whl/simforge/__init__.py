"""Simforge client for provider-based API calls."""

from simforge.client import AllowedEnvVars, Simforge

# Only export SimforgeTracingProcessor if openai-agents is available
try:
    from simforge.tracing import (
        SimforgeOpenAITracingProcessor as SimforgeTracingProcessor,
    )

    __all__ = ["Simforge", "AllowedEnvVars", "SimforgeTracingProcessor"]
except ImportError:
    # openai-agents not installed, skip tracing processor export
    __all__ = ["Simforge", "AllowedEnvVars"]
