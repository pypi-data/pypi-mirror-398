"""Simforge client for provider-based API calls."""

import asyncio
import logging
from typing import Any, Optional, TypedDict

import requests

from simforge.baml import run_function_with_baml
from simforge.tracing import SimforgeOpenAITracingProcessor

logger = logging.getLogger(__name__)

DEFAULT_SERVICE_URL = "https://simforge.goharvest.ai"


class AllowedEnvVars(TypedDict, total=False):
    """Allowed environment variables for LLM providers.

    Only these keys are permitted when passing environment variables
    to the Simforge client for local BAML execution.

    Attributes:
        OPENAI_API_KEY: OpenAI API key for GPT models
    """

    OPENAI_API_KEY: str


class Simforge:
    """Client for making provider-based API calls via BAML."""

    def __init__(
        self,
        api_key: str,
        service_url: Optional[str] = None,
        env_vars: Optional[AllowedEnvVars] = None,
        execute_locally: bool = True,
    ):
        """Initialize the Simforge client.

        Args:
            api_key: The API key for Simforge API authentication
            service_url: The base URL for the Simforge API (default: https://simforge.goharvest.ai)
            env_vars: Environment variables for LLM provider API keys (only OPENAI_API_KEY is supported)
            execute_locally: Whether to execute BAML locally on the client (default: True)
        """
        self.api_key = api_key
        self.service_url = service_url or DEFAULT_SERVICE_URL
        self.env_vars = env_vars or {}
        self.execute_locally = execute_locally

    def _fetch_function_version(self, method_name: str) -> dict:
        """Fetch the function with its current version and BAML prompt from the server.

        Args:
            method_name: The name of the method to fetch

        Returns:
            Function version data including BAML prompt and providers

        Raises:
            ValueError: If function not found or has no prompt
        """
        url = f"{self.service_url}/api/sdk/functions/lookup"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {"name": method_name}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()

            result = response.json()

            # Check if function was not found
            if result.get("id") is None:
                raise ValueError(
                    f'Function "{method_name}" not found. Create it at: {self.service_url}/functions'
                )

            # Check if function has no prompt
            if not result.get("prompt"):
                func_id = result.get("id")
                raise ValueError(
                    f'Function "{method_name}" has no prompt configured. '
                    f"Add one at: {self.service_url}/functions/{func_id}"
                )

            # Check for errors in the response
            if "error" in result:
                if "url" in result:
                    raise ValueError(
                        f"{result['error']} Configure it at: {self.service_url}{result['url']}"
                    )
                raise ValueError(result["error"])

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching function version: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text[:500]}")
            raise

    def call(self, method_name: str, **kwargs: Any) -> Any:
        """Call a method with the given named arguments via BAML execution.

        Args:
            method_name: The name of the method to call
            **kwargs: Named arguments to pass to the method

        Returns:
            The result of the BAML function execution

        Raises:
            ValueError: If no prompt is found or other API errors
        """
        logger.info(f"Calling {method_name} with inputs: {kwargs}")

        # If executeLocally is true, fetch the BAML and execute it locally
        if self.execute_locally:
            try:
                function_version = self._fetch_function_version(method_name)
                result = asyncio.run(
                    run_function_with_baml(
                        function_version["prompt"],
                        kwargs,
                        function_version["providers"],
                        self.env_vars,
                    )
                )
                return result
            except Exception as e:
                logger.error(f"Error during local execution: {e}")
                raise

        # Otherwise, fall back to server-side execution
        url = f"{self.service_url}/api/sdk/call"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "name": method_name,
            "inputs": kwargs,
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=120,  # Longer timeout for BAML execution
            )
            response.raise_for_status()

            result = response.json()
            logger.debug(f"Response: {result}")

            # Check for errors in the response
            if "error" in result:
                if "url" in result:
                    raise ValueError(
                        f"{result['error']} Configure it at: {self.service_url}{result['url']}"
                    )
                raise ValueError(result["error"])

            trace_id = result.get("traceId")
            if trace_id:
                logger.info(f"Trace created: {trace_id}")

            return result.get("result")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Simforge: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text[:500]}")
            raise

    def get_openai_tracing_processor(self) -> SimforgeOpenAITracingProcessor:
        """Get a tracing processor for OpenAI Agents SDK integration.

        The processor implements the TracingProcessor interface from the OpenAI
        Agents SDK and can be registered to automatically capture traces and
        spans from agent execution.

        Example:
            ```python
            from simforge import Simforge
            from agents import set_trace_processors

            simforge = Simforge(api_key="your-api-key")
            processor = simforge.get_openai_tracing_processor()

            # Register the processor with OpenAI Agents SDK
            set_trace_processors([processor])
            ```

        Returns:
            A SimforgeOpenAITracingProcessor instance configured for this client

        See:
            https://openai.github.io/openai-agents-python/ref/tracing/
        """
        return SimforgeOpenAITracingProcessor(
            api_key=self.api_key,
            service_url=self.service_url,
        )
